import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

DOGRAM_SPEC = importlib.util.spec_from_file_location(
    "static_os_dogram_nav", ROOT / "scripts" / "dogram_nav.py"
)
dogram_nav = importlib.util.module_from_spec(DOGRAM_SPEC)
DOGRAM_SPEC.loader.exec_module(dogram_nav)

NAV_SPEC = importlib.util.spec_from_file_location(
    "static_os_nav", ROOT / "scripts" / "nav.py"
)
nav = importlib.util.module_from_spec(NAV_SPEC)
NAV_SPEC.loader.exec_module(nav)

PATHS = [
    "examples/nav-contacted.local-test.json",
    "examples/nav-to-witness.intake.json",
    "examples/world-receipt.independent-contradiction.json",
    "examples/make-ground.receipt.json",
    "examples/make-ground-to-witness.reentry.json",
    "examples/world-recursion-receipt.generated-downstream.json",
]
ARTIFACTS = [
    json.loads((ROOT / path).read_text(encoding="utf-8"))
    for path in PATHS
]


class DogramNavReorientationTests(unittest.TestCase):
    def test_trace_verifies_complete(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        result = dogram_nav.verify_trace(ledger)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["positions"], list(range(6)))
        self.assertEqual(
            ledger["artifacts"][ledger["root_digest"]]["schema"],
            "static.nav-receipt/v0",
        )
        self.assertEqual(
            ledger["artifacts"][ledger["head_digest"]]["schema"],
            "static.world-recursion-receipt/v0",
        )

    def test_missing_witness_is_incomplete_not_invalid(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        missing_digest = ledger["entries"][3]["artifact_digest"]
        del ledger["artifacts"][missing_digest]
        result = dogram_nav.verify_trace(ledger)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"], "missing_artifact")

    def test_mutated_witness_is_invalid(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        digest = ledger["entries"][2]["artifact_digest"]
        ledger["artifacts"][digest]["next_door"] += " changed"
        result = dogram_nav.verify_trace(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "artifact_digest_mismatch")

    def test_transition_preserves_path_without_embedding_it(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        transition = dogram_nav.make_transition(
            ledger,
            "Repeat the disputed behavior under captured conditions before widening the claim.",
            "The recursive artifact is new but generated downstream, so it changes what should be tested next without counting as external confirmation.",
            [
                "the upstream contradiction",
                "the generated-downstream classification",
                "the claim that the new artifact is not a second witness",
            ],
        )
        self.assertEqual(transition["status"], "proposed")
        self.assertEqual(
            transition["from_heading"],
            ARTIFACTS[0]["next_heading"],
        )
        self.assertEqual(
            transition["to_heading"],
            "Repeat the disputed behavior under captured conditions before widening the claim.",
        )
        self.assertNotIn("artifacts", transition)
        self.assertNotIn("entries", transition)

    def test_same_destination_can_be_different_navigation(self):
        first_ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        first = dogram_nav.make_transition(
            first_ledger,
            "Repeat the disputed behavior under captured conditions before widening the claim.",
            "Path A",
            ["preserve A"],
        )

        alternate = copy.deepcopy(ARTIFACTS)
        alternate[1]["establishes"][0] += " alternate-path"
        second_ledger = dogram_nav.build_trace(alternate)
        second = dogram_nav.make_transition(
            second_ledger,
            "Repeat the disputed behavior under captured conditions before widening the claim.",
            "Path B",
            ["preserve B"],
        )

        comparison = dogram_nav.compare_destination(first, second)
        self.assertTrue(comparison["same_destination"])
        self.assertFalse(comparison["same_trace"])
        self.assertFalse(comparison["same_navigation"])

    def test_identical_path_and_destination_is_same_navigation(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        first = dogram_nav.make_transition(
            ledger,
            "Repeat the disputed behavior under captured conditions before widening the claim.",
            "Same delta",
            ["same preserve"],
        )
        second = copy.deepcopy(first)
        comparison = dogram_nav.compare_destination(first, second)
        self.assertTrue(comparison["same_navigation"])

    def test_nav_reorientation_is_proposal_not_replacement(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        transition = dogram_nav.make_transition(
            ledger,
            "Repeat the disputed behavior under captured conditions before widening the claim.",
            "The path changed the next useful question.",
            ["upstream source distinction", "reversibility"],
        )
        proposal = nav.make_reorientation(transition)
        self.assertEqual(proposal["schema"], "static.nav-reorientation/v0")
        self.assertEqual(proposal["status"], "proposed")
        self.assertEqual(
            proposal["proposed_heading"],
            transition["to_heading"],
        )
        self.assertEqual(
            proposal["trace_ledger_sha256"],
            transition["trace_ledger_sha256"],
        )
        self.assertNotEqual(
            proposal["from_heading"],
            proposal["proposed_heading"],
        )
        self.assertIn("does not activate", proposal["claim_limit"])

    def test_nav_refuses_activated_dogram_transition(self):
        ledger = dogram_nav.build_trace(copy.deepcopy(ARTIFACTS))
        transition = dogram_nav.make_transition(
            ledger,
            "A heading",
            "A delta",
            ["a preserve"],
        )
        transition["status"] = "activated"
        with self.assertRaisesRegex(ValueError, "must remain proposed"):
            nav.make_reorientation(transition)

    def test_trace_rejects_repeated_artifact(self):
        bad = copy.deepcopy(ARTIFACTS)
        bad[4] = copy.deepcopy(bad[3])
        with self.assertRaisesRegex(ValueError, "repeated"):
            dogram_nav.build_trace(bad)


if __name__ == "__main__":
    unittest.main()
