"""FIELD-CELL-001: purely synthetic deterministic measurement parser tests."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "field_cell_analysis", ROOT / "scripts" / "field-cell-analyze.py"
)
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
RAW = (ROOT / "fixtures" / "field-cell-001" / "synthetic-rc.csv").read_bytes()


def rows(raw: bytes = RAW) -> list[str]:
    return raw.decode("utf-8").splitlines()


def edited(lines: list[str]) -> bytes:
    return ("\n".join(lines) + "\n").encode("utf-8")


class FieldCellAnalysisTests(unittest.TestCase):
    def test_synthetic_15_trials_five_conditions_105_rows(self):
        r = mod.analyze_bytes(RAW, "SYNTHETIC")
        self.assertEqual(r["trial_count"], 15)
        self.assertEqual(r["rows_analyzed"], 105)
        self.assertEqual(set(r["condition_counts"].values()), {3})
        self.assertEqual(r["flags"], [])
        self.assertFalse(r["physical_processor_proven"])
        self.assertFalse(r["physical_measurement_independently_verified"])

    def test_open_path_censored_control_does_not_invent_threshold(self):
        r = mod.analyze_bytes(RAW, "SYNTHETIC")
        opened = [x for x in r["trials"] if x["condition"] == "open"]
        self.assertEqual(len(opened), 3)
        self.assertTrue(all(x["rise_to_63_percent_s"] is None for x in opened))
        self.assertTrue(all(x["right_censored_63_percent"] for x in opened))

    def test_wet_damp_dry_order_is_synthetic_model_not_field_claim(self):
        r = mod.analyze_bytes(RAW, "SYNTHETIC")
        def avg(condition):
            vals = [x["normalized_voltage_at_10s"] for x in r["trials"] if x["condition"] == condition]
            return sum(vals) / len(vals)
        self.assertGreater(avg("wet"), avg("damp"))
        self.assertGreater(avg("damp"), avg("dry"))
        self.assertNotIn("HARDWARE_INSTRUMENT_VERIFICATION", r["claims"])

    def test_t63_finite_vs_right_censored(self):
        r = mod.analyze_bytes(RAW, "SYNTHETIC")
        fixed = [x for x in r["trials"] if x["condition"] == "fixed"]
        self.assertTrue(all(x["rise_to_63_percent_s"] is not None for x in fixed))
        self.assertTrue(all(12 < x["rise_to_63_percent_s"] < 18 for x in fixed))

    def test_replay_exact_and_source_digest_content_sensitive(self):
        a = mod.analyze_bytes(RAW, "SYNTHETIC")
        self.assertEqual(a, mod.analyze_bytes(RAW, "SYNTHETIC"))
        lines = rows()
        lines[-1] = lines[-1].replace(",3.0500", ",3.0400")
        b = mod.analyze_bytes(edited(lines), "SYNTHETIC")
        self.assertNotEqual(a["source_sha256"], b["source_sha256"])

    def test_user_reported_does_not_become_hardware_verification(self):
        r = mod.analyze_bytes(RAW)
        self.assertEqual(r["evidence_classification"], "USER_REPORTED_UNVERIFIED")
        self.assertFalse(r["physical_processor_proven"])
        self.assertFalse(r["physical_measurement_independently_verified"])

    def test_header_injection_and_extra_column_refused(self):
        lines = rows()
        lines[0] += ",gps"
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_wrong_phase_refused(self):
        lines = rows()
        lines[1] = lines[1].replace(",charge,", ",discharge,")
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_nonfinite_numbers_refused(self):
        lines = rows()
        columns = lines[2].split(",")
        columns[-1] = "nan"
        lines[2] = ",".join(columns)
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_out_of_range_supply_and_node_refused(self):
        lines = rows()
        cols = lines[1].split(",")
        cols[-2] = "5.0"
        lines[1] = ",".join(cols)
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")
        lines = rows()
        cols = lines[2].split(",")
        cols[-1] = "3.5"
        lines[2] = ",".join(cols)
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_duplicate_sample_time_refused(self):
        lines = rows()
        cols = lines[2].split(",")
        cols[3] = "0"
        lines[2] = ",".join(cols)
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_source_size_limit_refused(self):
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(b"x" * 131073, "SYNTHETIC")

    def test_battery_drift_refused(self):
        lines = rows()
        cols = lines[3].split(",")
        cols[-2] = "3.25"
        lines[3] = ",".join(cols)
        with self.assertRaises(mod.Refuse):
            mod.analyze_bytes(edited(lines), "SYNTHETIC")

    def test_initial_not_reset_flag_not_falsified(self):
        lines = rows()
        cols = lines[1].split(",")
        cols[-1] = "0.3000"
        lines[1] = ",".join(cols)
        r = mod.analyze_bytes(edited(lines), "SYNTHETIC")
        self.assertIn("INITIAL_VOLTAGE_NOT_RESET", r["trials"][0]["flags"])
        self.assertIn("REVIEW_TRIAL_WARNINGS", r["flags"])

    def test_missing_control_flagged_not_inferred(self):
        lines = [x for x in rows() if ",open," not in x]
        r = mod.analyze_bytes(edited(lines), "SYNTHETIC")
        self.assertIn("MISSING_OPEN_CONDITION", r["flags"])
        self.assertEqual(r["condition_counts"]["open"], 0)

    def test_too_few_replications_flagged(self):
        lines = [x for x in rows() if not x.startswith("fixed-2,") and not x.startswith("fixed-3,")]
        r = mod.analyze_bytes(edited(lines), "SYNTHETIC")
        self.assertIn("INSUFFICIENT_REPLICATION_FIXED", r["flags"])

    def test_no_external_authority_or_actuation_in_result(self):
        result = mod.analyze_bytes(RAW, "SYNTHETIC")
        self.assertEqual(result["operation"], "READ_ONLY_OFFLINE_ANALYSIS")
        self.assertNotIn("transmit", result)
        self.assertNotIn("actuate", result)
        self.assertNotIn("admit", result)


if __name__ == "__main__":
    unittest.main()
