import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_os_witness", ROOT / "scripts" / "witness.py"
)
witness = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(witness)

PACKET = json.loads(
    (ROOT / "bridge" / "witness.packet.json").read_text(encoding="utf-8")
)
NAV_RECEIPT = json.loads(
    (ROOT / "examples" / "nav-contacted.local-test.json").read_text(encoding="utf-8")
)


class WitnessCrossingTests(unittest.TestCase):
    def test_packet_contract(self):
        self.assertEqual(
            witness.validate_packet(copy.deepcopy(PACKET))["id"],
            "witness-001",
        )

    def test_refuse_invariant_drift(self):
        bad = copy.deepcopy(PACKET)
        bad["core_distinction"] = "STORY IS SOURCE"
        with self.assertRaisesRegex(ValueError, "invariant"):
            witness.validate_packet(bad)

    def test_refuse_oriented_nav_receipt(self):
        bad = copy.deepcopy(NAV_RECEIPT)
        bad["status"] = "oriented"
        bad["observed"] = None
        bad["delta"] = None
        bad["next_heading"] = None
        with self.assertRaisesRegex(ValueError, "requires a contacted"):
            witness.intake_nav(bad)

    def test_nav_to_witness_preserves_claim_classes(self):
        intake = witness.intake_nav(copy.deepcopy(NAV_RECEIPT))
        self.assertEqual(intake["schema"], "static.witness-intake/v0")
        self.assertEqual(
            [record["claim_class"] for record in intake["records"]],
            [
                "source_record",
                "derivative_interpretation",
                "orientation_proposal",
                "source_limit",
            ],
        )
        self.assertEqual(intake["records"][0]["value"], NAV_RECEIPT["observed"])
        self.assertEqual(intake["records"][1]["value"], NAV_RECEIPT["delta"])
        self.assertEqual(intake["records"][2]["value"], NAV_RECEIPT["next_heading"])

    def test_intake_does_not_upgrade_world_contact(self):
        intake = witness.intake_nav(copy.deepcopy(NAV_RECEIPT))
        joined = " ".join(intake["does_not_establish"]).lower()
        self.assertIn("independently verified", joined)
        self.assertIn("independently reproduced", joined)
        inspection = witness.inspect_intake(intake)
        self.assertFalse(inspection["independent_verification_claimed"])

    def test_source_digest_is_stable_and_sensitive(self):
        first = witness.intake_nav(copy.deepcopy(NAV_RECEIPT))
        second = witness.intake_nav(copy.deepcopy(NAV_RECEIPT))
        self.assertEqual(first["source"]["sha256"], second["source"]["sha256"])

        changed = copy.deepcopy(NAV_RECEIPT)
        changed["observed"] += " changed"
        third = witness.intake_nav(changed)
        self.assertNotEqual(first["source"]["sha256"], third["source"]["sha256"])

    def test_refuse_collapsed_claim_classes(self):
        intake = witness.intake_nav(copy.deepcopy(NAV_RECEIPT))
        bad = copy.deepcopy(intake)
        bad["records"][1]["claim_class"] = "source_record"
        with self.assertRaisesRegex(ValueError, "claim classes"):
            witness.validate_intake(bad)


if __name__ == "__main__":
    unittest.main()
