import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_os_world", ROOT / "scripts" / "world.py"
)
world = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(world)

PACKET = json.loads(
    (ROOT / "bridge" / "world.packet.json").read_text(encoding="utf-8")
)
INTAKE = json.loads(
    (ROOT / "examples" / "nav-to-witness.intake.json").read_text(encoding="utf-8")
)
DERIVED = json.loads(
    (ROOT / "examples" / "world-candidate.derived-corroboration.json").read_text(encoding="utf-8")
)
INDEPENDENT = json.loads(
    (ROOT / "examples" / "world-candidate.independent-contradiction.json").read_text(encoding="utf-8")
)


class WorldCrossingTests(unittest.TestCase):
    def test_packet_contract(self):
        self.assertEqual(
            world.validate_packet(copy.deepcopy(PACKET))["id"],
            "world-001",
        )

    def test_refuse_invariant_drift(self):
        bad = copy.deepcopy(PACKET)
        bad["core_distinction"] = "AGREEMENT IS WORLD"
        with self.assertRaisesRegex(ValueError, "invariant"):
            world.validate_packet(bad)

    def test_derived_corroboration_is_not_second_witness(self):
        receipt = world.compare(
            copy.deepcopy(INTAKE),
            copy.deepcopy(DERIVED),
        )
        self.assertEqual(receipt["lineage_class"], "derived_retelling")
        self.assertEqual(receipt["claim_relation"], "corroborates")
        self.assertEqual(receipt["independence_status"], "not_independent")
        self.assertFalse(receipt["independence_claim_accepted"])

    def test_independent_candidate_can_contradict(self):
        receipt = world.compare(
            copy.deepcopy(INTAKE),
            copy.deepcopy(INDEPENDENT),
        )
        self.assertEqual(receipt["lineage_class"], "independent_candidate")
        self.assertEqual(receipt["claim_relation"], "contradicts")
        self.assertEqual(receipt["independence_status"], "independent_candidate")
        self.assertTrue(receipt["independence_claim_accepted"])

    def test_contradiction_does_not_create_independence(self):
        candidate = copy.deepcopy(DERIVED)
        candidate["claim_relation"] = "contradicts"
        receipt = world.compare(copy.deepcopy(INTAKE), candidate)
        self.assertEqual(receipt["claim_relation"], "contradicts")
        self.assertEqual(receipt["lineage_class"], "derived_retelling")
        self.assertFalse(receipt["independence_claim_accepted"])

    def test_correction_does_not_create_independence(self):
        candidate = copy.deepcopy(DERIVED)
        candidate["claim_relation"] = "corrects"
        receipt = world.compare(copy.deepcopy(INTAKE), candidate)
        self.assertEqual(receipt["claim_relation"], "corrects")
        self.assertEqual(receipt["independence_status"], "not_independent")

    def test_refuse_false_independence_claim(self):
        candidate = copy.deepcopy(DERIVED)
        candidate["independence_claim"] = True
        with self.assertRaisesRegex(ValueError, "claims independence"):
            world.compare(copy.deepcopy(INTAKE), candidate)

    def test_same_artifact_is_not_independent(self):
        candidate = copy.deepcopy(DERIVED)
        candidate["source_sha256"] = INTAKE["source"]["sha256"]
        candidate["derives_from"] = []
        candidate["ancestry_roots"] = ["same-artifact-root"]
        receipt = world.compare(copy.deepcopy(INTAKE), candidate)
        self.assertEqual(receipt["lineage_class"], "same_artifact")
        self.assertFalse(receipt["independence_claim_accepted"])

    def test_unknown_lineage_remains_unknown(self):
        candidate = copy.deepcopy(DERIVED)
        candidate["channel"] = "document"
        candidate["derives_from"] = []
        candidate["ancestry_roots"] = ["unverified-document-root"]
        receipt = world.compare(copy.deepcopy(INTAKE), candidate)
        self.assertEqual(receipt["lineage_class"], "lineage_unknown")
        self.assertEqual(receipt["independence_status"], "unknown")
        self.assertFalse(receipt["independence_claim_accepted"])

    def test_inspection_keeps_truth_unclaimed(self):
        receipt = world.compare(
            copy.deepcopy(INTAKE),
            copy.deepcopy(INDEPENDENT),
        )
        inspection = world.inspect_receipt(receipt)
        self.assertTrue(inspection["counts_as_second_witness"])
        self.assertFalse(inspection["truth_claimed"])


if __name__ == "__main__":
    unittest.main()
