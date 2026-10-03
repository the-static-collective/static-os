import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


source_fixture = load_module(
    "static_os_composed_world_fixture_for_measurement",
    "tests/test_composed_witness_to_world.py",
)
audit = load_module(
    "static_os_world_measurement_audit_test",
    "scripts/world_measurement_audit.py",
)


def passing_audit(source_sha):
    return {
        "schema": "static.measurement-path-audit/v0",
        "audit_id": "measurement-audit-001",
        "candidate_source_sha256": source_sha,
        "criteria": {
            "channel_origin": {
                "status": "preexisting_or_external",
                "evidence_sha256": "a" * 64,
            },
            "capture_control": {
                "status": "not_controlled_by_orientation",
                "evidence_sha256": "b" * 64,
            },
            "result_selection": {
                "status": "result_blind_capture",
                "evidence_sha256": "c" * 64,
            },
            "operator_relation": {
                "status": "independent_or_automatic",
                "evidence_sha256": "d" * 64,
            },
        },
        "claim_limit": (
            "This contract fixture declares evidence-addressed audit criteria. "
            "It does not externally authenticate the supporting evidence artifacts."
        ),
    }


def make_source():
    *_, candidate, _ = source_fixture.make_source()
    return candidate


class MeasurementPathAuditTests(unittest.TestCase):
    def test_passing_audit_upgrades_only_measurement_axis(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))

        self.assertEqual(
            receipt["selection_independence"],
            "not_independent_of_orientation",
        )
        self.assertEqual(
            receipt["measurement_independence"],
            "independent_candidate",
        )
        self.assertEqual(
            receipt["evidence_role"],
            "selection_dependent_measurement_independent_candidate",
        )
        self.assertFalse(receipt["counts_as_independent_confirmation"])

    def test_all_four_criteria_are_required_for_independent_candidate(self):
        candidate = make_source()
        specimen = passing_audit(candidate["source_sha256"])
        specimen["criteria"]["operator_relation"]["status"] = "unknown"

        receipt = audit.classify(candidate, specimen)

        self.assertEqual(receipt["measurement_independence"], "unknown")
        self.assertEqual(
            receipt["evidence_role"],
            "selection_dependent_measurement_unknown",
        )
        self.assertIn("operator_relation", receipt["criteria_summary"]["unknown"])
        self.assertFalse(receipt["counts_as_independent_confirmation"])

    def test_failed_criterion_marks_measurement_not_independent(self):
        candidate = make_source()
        specimen = passing_audit(candidate["source_sha256"])
        specimen["criteria"]["capture_control"]["status"] = (
            "controlled_by_orientation"
        )

        receipt = audit.classify(candidate, specimen)

        self.assertEqual(receipt["measurement_independence"], "not_independent")
        self.assertEqual(
            receipt["evidence_role"],
            "selection_and_measurement_dependent",
        )
        self.assertIn("capture_control", receipt["criteria_summary"]["failed"])

    def test_audit_cannot_change_known_selection_dependence(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))
        inspection = audit.inspect(receipt)

        self.assertFalse(inspection["selection_axis_upgraded"])
        self.assertTrue(inspection["measurement_axis_audited"])
        self.assertEqual(
            inspection["selection_independence"],
            "not_independent_of_orientation",
        )

    def test_source_hash_must_match_candidate(self):
        candidate = make_source()
        specimen = passing_audit("f" * 64)

        with self.assertRaisesRegex(ValueError, "source does not match candidate"):
            audit.classify(candidate, specimen)

    def test_candidate_source_cannot_self_certify_audit(self):
        candidate = make_source()
        specimen = passing_audit(candidate["source_sha256"])
        specimen["criteria"]["channel_origin"]["evidence_sha256"] = (
            candidate["source_sha256"]
        )

        with self.assertRaisesRegex(ValueError, "own audit evidence"):
            audit.classify(candidate, specimen)

    def test_orientation_ancestry_cannot_impersonate_audit_evidence(self):
        candidate = make_source()
        specimen = passing_audit(candidate["source_sha256"])
        specimen["criteria"]["channel_origin"]["evidence_sha256"] = (
            candidate["orientation_ancestry"]["source_generation_sha256"]
        )

        with self.assertRaisesRegex(ValueError, "impersonate orientation ancestry"):
            audit.classify(candidate, specimen)

    def test_measurement_independent_candidate_is_not_full_confirmation(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))

        limits = " ".join(receipt["does_not_establish"]).lower()
        self.assertIn("fully independent evidence", limits)
        self.assertIn("selected the question or experiment", limits)
        self.assertFalse(receipt["counts_as_independent_confirmation"])

    def test_receipt_requires_consistent_role(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))
        bad = copy.deepcopy(receipt)
        bad["evidence_role"] = "selection_and_measurement_dependent"

        with self.assertRaisesRegex(ValueError, "contradicts independence"):
            audit.validate_receipt(bad)

    def test_independent_candidate_requires_all_passes(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))
        bad = copy.deepcopy(receipt)
        bad["criteria_summary"]["unknown"] = ["operator_relation"]
        bad["criteria_summary"]["passed"].remove("operator_relation")

        with self.assertRaisesRegex(ValueError, "requires all criteria to pass"):
            audit.validate_receipt(bad)

    def test_unknown_cannot_be_promoted_to_independent_by_relabel(self):
        candidate = make_source()
        specimen = passing_audit(candidate["source_sha256"])
        specimen["criteria"]["result_selection"]["status"] = "unknown"
        receipt = audit.classify(candidate, specimen)

        bad = copy.deepcopy(receipt)
        bad["measurement_independence"] = "independent_candidate"
        bad["evidence_role"] = (
            "selection_dependent_measurement_independent_candidate"
        )

        with self.assertRaisesRegex(ValueError, "requires all criteria to pass"):
            audit.validate_receipt(bad)

    def test_inspection_preserves_typed_origin_and_no_truth_claim(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))
        inspection = audit.inspect(receipt)

        self.assertTrue(inspection["typed_origin_preserved"])
        self.assertFalse(inspection["truth_claimed"])
        self.assertFalse(inspection["counts_as_independent_confirmation"])

    def test_next_door_requests_independent_selection_for_stronger_role(self):
        candidate = make_source()
        receipt = audit.classify(candidate, passing_audit(candidate["source_sha256"]))
        next_door = receipt["next_door"].lower()

        self.assertIn("selection-dependent", next_door)
        self.assertIn("selection path is also independent", next_door)


if __name__ == "__main__":
    unittest.main()
