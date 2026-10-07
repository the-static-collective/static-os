import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-whole-body.py"
SPEC = importlib.util.spec_from_file_location("whole_body_validator", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

BASE = json.loads((ROOT / "manifest" / "whole-body-001.json").read_text(encoding="utf-8"))


def clone():
    return json.loads(json.dumps(BASE))


class WholeBodyManifestTests(unittest.TestCase):
    def test_accepts_checked_in_candidate(self):
        self.assertEqual(MODULE.validate(clone())["id"], "WHOLE-BODY-001")

    def test_refuses_mutable_source_ref(self):
        value = clone()
        value["organs"][0]["commit"] = "main"
        with self.assertRaisesRegex(ValueError, "40-hex"):
            MODULE.validate(value)

    def test_refuses_supabardo_as_canon(self):
        value = clone()
        value["supabardo"]["canonical"] = True
        with self.assertRaisesRegex(ValueError, "canon"):
            MODULE.validate(value)

    def test_refuses_supabardo_as_durable_memory_owner(self):
        value = clone()
        value["supabardo"]["durable_memory_owner"] = True
        with self.assertRaisesRegex(ValueError, "durable"):
            MODULE.validate(value)

    def test_refuses_automatic_admission(self):
        value = clone()
        value["supabardo"]["automatic_admission"] = True
        with self.assertRaisesRegex(ValueError, "admit"):
            MODULE.validate(value)

    def test_refuses_auto_start_foreign_organs(self):
        value = clone()
        value["deployment"]["auto_start_foreign_organs"] = True
        with self.assertRaisesRegex(ValueError, "automatic"):
            MODULE.validate(value)

    def test_refuses_runtime_claim_promotion(self):
        value = clone()
        value["claims"]["runtime_composition"] = "verified"
        with self.assertRaisesRegex(ValueError, "promoted"):
            MODULE.validate(value)

    def test_refuses_cross_boot_claim_promotion(self):
        value = clone()
        value["claims"]["cross_boot_continuity"] = "proven"
        with self.assertRaisesRegex(ValueError, "promoted"):
            MODULE.validate(value)

    def test_refuses_sb001_evidence_substitution(self):
        value = clone()
        value["supabardo"]["proof"]["evidence_set_id"] = "sb001-evidence-v0:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "evidence"):
            MODULE.validate(value)

    def test_refuses_relattes_before_proven_sb001_head(self):
        value = clone()
        relatte = next(row for row in value["organs"] if row["id"] == "relatte")
        relatte["commit"] = "87006f3265103a8abe387d81597c58aeb39b0beb"
        with self.assertRaisesRegex(ValueError, "SB-001"):
            MODULE.validate(value)

    def test_refuses_live_membrane_as_reconstruction_dependency(self):
        value = clone()
        value["supabardo"]["proof"]["live_membrane_required_for_reconstruction"] = True
        with self.assertRaisesRegex(ValueError, "live Bardo"):
            MODULE.validate(value)


if __name__ == "__main__":
    unittest.main()
