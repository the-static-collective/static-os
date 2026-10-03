import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_os_make_ground", ROOT / "scripts" / "make_ground.py"
)
ground = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ground)

PACKET = json.loads(
    (ROOT / "bridge" / "make-ground.packet.json").read_text(encoding="utf-8")
)
WORLD = json.loads(
    (ROOT / "examples" / "world-receipt.independent-contradiction.json").read_text(
        encoding="utf-8"
    )
)
FIELD = json.loads(
    (ROOT / "examples" / "make-ground.field-profile.json").read_text(encoding="utf-8")
)


class MakeGroundCrossingTests(unittest.TestCase):
    def test_packet_contract(self):
        self.assertEqual(
            ground.validate_packet(copy.deepcopy(PACKET))["id"],
            "make-ground-001",
        )

    def test_refuse_invariant_drift(self):
        bad = copy.deepcopy(PACKET)
        bad["core_distinction"] = "BUILD THE WHOLE THING"
        with self.assertRaisesRegex(ValueError, "invariant"):
            ground.validate_packet(bad)

    def test_requires_unresolved_independent_contact(self):
        bad = copy.deepcopy(WORLD)
        bad["lineage_class"] = "derived_retelling"
        bad["independence_status"] = "not_independent"
        bad["independence_claim_accepted"] = False
        with self.assertRaisesRegex(ValueError, "independent candidate"):
            ground.make_plan(bad, copy.deepcopy(FIELD))

    def test_refuse_non_disagreement_relation(self):
        bad = copy.deepcopy(WORLD)
        bad["claim_relation"] = "corroborates"
        with self.assertRaisesRegex(ValueError, "contradiction or correction"):
            ground.make_plan(bad, copy.deepcopy(FIELD))

    def test_selected_lever_must_exist(self):
        bad = copy.deepcopy(FIELD)
        bad["selected_lever_id"] = "missing"
        with self.assertRaisesRegex(ValueError, "selected reversible lever"):
            ground.make_plan(copy.deepcopy(WORLD), bad)

    def test_plan_is_reversible_and_not_a_verdict(self):
        plan = ground.make_plan(copy.deepcopy(WORLD), copy.deepcopy(FIELD))
        self.assertEqual(plan["status"], "proposed")
        self.assertEqual(plan["world_source"]["claim_relation"], "contradicts")
        self.assertTrue(plan["intervention"]["rollback"])
        self.assertFalse(plan["truth_claimed"])
        self.assertIn("does not establish", plan["claim_limit"].lower())
        self.assertIn("without requiring either source", plan["success_condition"])

    def test_observation_records_fertility_not_truth(self):
        plan = ground.make_plan(copy.deepcopy(WORLD), copy.deepcopy(FIELD))
        receipt = ground.observe_plan(
            plan,
            "mixed",
            "The fresh fixture reproduced part of each report under different captured conditions.",
            ["raw-run-001.json", "environment-001.json"],
            [
                "repeat the disputed behavior with an environment manifest",
                "compare raw outputs across declared environments",
            ],
            True,
            True,
            "The fixture adds a small test-only maintenance burden.",
            False,
        )
        self.assertEqual(receipt["observation_relation"], "mixed")
        self.assertFalse(receipt["truth_claimed"])
        self.assertGreaterEqual(
            len(receipt["fertility_delta"]["new_capabilities"]),
            2,
        )
        self.assertIn("does not establish", receipt["claim_limit"].lower())

    def test_observation_requires_evidence_artifact(self):
        plan = ground.make_plan(copy.deepcopy(WORLD), copy.deepcopy(FIELD))
        with self.assertRaisesRegex(ValueError, "evidence artifact"):
            ground.observe_plan(
                plan,
                "inconclusive",
                "No stable difference was observed.",
                [],
                ["capture the environment consistently"],
                False,
                True,
                "No added ongoing maintenance.",
                False,
            )

    def test_plan_hash_changes_when_plan_changes(self):
        plan = ground.make_plan(copy.deepcopy(WORLD), copy.deepcopy(FIELD))
        first = ground._sha256(plan)
        changed = copy.deepcopy(plan)
        changed["intervention"]["change"] += " extra"
        second = ground._sha256(changed)
        self.assertNotEqual(first, second)

    def test_inspection_returns_to_witness(self):
        plan = ground.make_plan(copy.deepcopy(WORLD), copy.deepcopy(FIELD))
        receipt = ground.observe_plan(
            plan,
            "inconclusive",
            "The intervention produced a reusable artifact but did not settle the disagreement.",
            ["fresh-run.json"],
            ["produce a repeatable capture of the disputed behavior"],
            True,
            True,
            "One fixture must be maintained while the question remains live.",
            False,
        )
        inspection = ground.inspect_receipt(receipt)
        self.assertEqual(inspection["reentry_target"], "WITNESS")
        self.assertFalse(inspection["truth_claimed"])


if __name__ == "__main__":
    unittest.main()
