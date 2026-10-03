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
REENTRY = json.loads(
    (ROOT / "examples" / "make-ground-to-witness.reentry.json").read_text(
        encoding="utf-8"
    )
)
EXPECTED_CANDIDATE = json.loads(
    (ROOT / "examples" / "world-recursive-candidate.from-reentry.json").read_text(
        encoding="utf-8"
    )
)
EXPECTED_RECEIPT = json.loads(
    (ROOT / "examples" / "world-recursion-receipt.generated-downstream.json").read_text(
        encoding="utf-8"
    )
)


class WorldRecursiveEvidenceTests(unittest.TestCase):
    def test_packet_declares_recursive_world_path(self):
        packet = world.validate_packet(copy.deepcopy(PACKET))
        self.assertIn(
            "static.witness-reentry/v0",
            packet["crossings"]["accepts"],
        )
        self.assertIn(
            "static.world-recursive-candidate/v0",
            packet["crossings"]["emits"],
        )
        self.assertIn(
            "static.world-recursion-receipt/v0",
            packet["crossings"]["emits"],
        )

    def test_reentry_becomes_exact_recursive_candidate_fixture(self):
        candidate = world.candidate_from_reentry(copy.deepcopy(REENTRY))
        self.assertEqual(candidate, EXPECTED_CANDIDATE)

    def test_candidate_preserves_generation_ancestry(self):
        candidate = world.candidate_from_reentry(copy.deepcopy(REENTRY))
        ancestry = candidate["generation_ancestry"]
        reentry_ancestry = REENTRY["source_bundle"]["ancestry"]
        self.assertEqual(
            ancestry["ground_receipt_sha256"],
            REENTRY["source_bundle"]["ground_receipt"]["sha256"],
        )
        self.assertEqual(
            ancestry["ground_plan_sha256"],
            reentry_ancestry["ground_plan_sha256"],
        )
        self.assertEqual(
            ancestry["world_primary_source_sha256"],
            reentry_ancestry["world_primary_source_sha256"],
        )
        self.assertEqual(
            ancestry["world_candidate_source_sha256"],
            reentry_ancestry["world_candidate_source_sha256"],
        )

    def test_new_artifact_is_not_independent_by_generation(self):
        candidate = world.candidate_from_reentry(copy.deepcopy(REENTRY))
        self.assertEqual(candidate["novelty_status"], "new_artifact")
        self.assertEqual(candidate["observation_status"], "fresh_capture")
        self.assertEqual(
            candidate["independence_status"],
            "not_independent_by_generation",
        )
        self.assertFalse(candidate["independence_claim"])
        self.assertNotEqual(
            candidate["source_sha256"],
            candidate["generation_ancestry"]["world_primary_source_sha256"],
        )
        self.assertNotEqual(
            candidate["source_sha256"],
            candidate["generation_ancestry"]["world_candidate_source_sha256"],
        )

    def test_recursive_classification_matches_durable_fixture(self):
        receipt = world.classify_recursive(copy.deepcopy(EXPECTED_CANDIDATE))
        self.assertEqual(receipt, EXPECTED_RECEIPT)

    def test_fresh_capture_does_not_count_as_second_witness(self):
        receipt = world.classify_recursive(copy.deepcopy(EXPECTED_CANDIDATE))
        self.assertEqual(receipt["lineage_class"], "generated_downstream")
        self.assertEqual(receipt["novelty_status"], "new_artifact")
        self.assertEqual(receipt["observation_status"], "fresh_capture")
        self.assertFalse(receipt["counts_as_second_witness"])
        self.assertTrue(receipt["upstream_ancestry_preserved"])

    def test_mixed_relation_survives_reentry_to_world(self):
        candidate = world.candidate_from_reentry(copy.deepcopy(REENTRY))
        self.assertEqual(candidate["relation_to_upstream"], "mixed")
        receipt = world.classify_recursive(candidate)
        self.assertEqual(receipt["relation_to_upstream"], "mixed")

    def test_refuse_recursive_independence_claim(self):
        candidate = copy.deepcopy(EXPECTED_CANDIDATE)
        candidate["independence_claim"] = True
        with self.assertRaisesRegex(ValueError, "must not claim independence"):
            world.validate_recursive_candidate(candidate)

    def test_refuse_collapsed_upstream_ancestry(self):
        candidate = copy.deepcopy(EXPECTED_CANDIDATE)
        candidate["generation_ancestry"]["world_candidate_source_sha256"] = (
            candidate["generation_ancestry"]["world_primary_source_sha256"]
        )
        with self.assertRaisesRegex(ValueError, "collapsed upstream"):
            world.classify_recursive(candidate)

    def test_inspection_keeps_novelty_and_independence_separate(self):
        inspection = world.inspect_any(copy.deepcopy(EXPECTED_RECEIPT))
        self.assertEqual(inspection["novelty_axis"], "new_artifact")
        self.assertEqual(inspection["lineage_axis"], "generated_downstream")
        self.assertEqual(
            inspection["independence_status"],
            "not_independent_by_generation",
        )
        self.assertFalse(inspection["counts_as_second_witness"])
        self.assertTrue(inspection["upstream_ancestry_preserved"])
        self.assertFalse(inspection["truth_claimed"])

    def test_reentry_missing_intervention_lineage_is_refused(self):
        bad = copy.deepcopy(REENTRY)
        bad["records"] = [
            record
            for record in bad["records"]
            if record["kind"] != "intervention_lineage"
        ]
        with self.assertRaisesRegex(ValueError, "record set"):
            world.candidate_from_reentry(bad)


if __name__ == "__main__":
    unittest.main()
