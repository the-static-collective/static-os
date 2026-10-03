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
GROUND = json.loads(
    (ROOT / "examples" / "make-ground.receipt.json").read_text(encoding="utf-8")
)
ARTIFACT = json.loads(
    (ROOT / "examples" / "reproduction-run.evidence.json").read_text(encoding="utf-8")
)
EXPECTED_REENTRY = json.loads(
    (ROOT / "examples" / "make-ground-to-witness.reentry.json").read_text(
        encoding="utf-8"
    )
)


class WitnessReentryTests(unittest.TestCase):
    def test_packet_declares_reentry(self):
        packet = witness.validate_packet(copy.deepcopy(PACKET))
        self.assertIn("static.ground-receipt/v0", packet["crossings"]["accepts"])
        self.assertIn("static.evidence-artifact/v0", packet["crossings"]["accepts"])
        self.assertIn("static.witness-reentry/v0", packet["crossings"]["emits"])

    def test_generated_reentry_matches_durable_fixture(self):
        self.assertEqual(
            witness.reenter_ground(
                copy.deepcopy(GROUND),
                copy.deepcopy(ARTIFACT),
            ),
            EXPECTED_REENTRY,
        )

    def test_reentry_preserves_full_ancestry_bundle(self):
        reentry = witness.reenter_ground(
            copy.deepcopy(GROUND),
            copy.deepcopy(ARTIFACT),
        )
        ancestry = reentry["source_bundle"]["ancestry"]
        self.assertEqual(
            ancestry["ground_plan_sha256"],
            GROUND["plan_sha256"],
        )
        self.assertEqual(
            ancestry["world_primary_source_sha256"],
            GROUND["ancestry"]["world_primary_source_sha256"],
        )
        self.assertEqual(
            ancestry["world_candidate_source_sha256"],
            GROUND["ancestry"]["world_candidate_source_sha256"],
        )
        self.assertEqual(
            reentry["source_bundle"]["evidence_artifact"]["artifact_id"],
            ARTIFACT["artifact_id"],
        )

    def test_observation_and_interpretation_do_not_collapse(self):
        reentry = witness.reenter_ground(
            copy.deepcopy(GROUND),
            copy.deepcopy(ARTIFACT),
        )
        classes = [record["claim_class"] for record in reentry["records"]]
        self.assertEqual(
            classes,
            [
                "source_record",
                "source_artifact",
                "derivative_interpretation",
                "derivative_interpretation",
                "intervention_record",
                "source_limit",
            ],
        )
        self.assertEqual(
            reentry["records"][0]["value"],
            GROUND["observed"],
        )
        self.assertEqual(
            reentry["records"][2]["value"],
            GROUND["observation_relation"],
        )

    def test_refuse_artifact_not_declared_by_ground_receipt(self):
        artifact = copy.deepcopy(ARTIFACT)
        artifact["artifact_id"] = "unlisted.json"
        with self.assertRaisesRegex(ValueError, "not declared"):
            witness.reenter_ground(copy.deepcopy(GROUND), artifact)

    def test_refuse_ground_ancestry_mismatch(self):
        receipt = copy.deepcopy(GROUND)
        receipt["ancestry"]["ground_plan_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ancestry mismatch"):
            witness.reenter_ground(receipt, copy.deepcopy(ARTIFACT))

    def test_source_fingerprints_change_when_sources_change(self):
        first = witness.reenter_ground(
            copy.deepcopy(GROUND),
            copy.deepcopy(ARTIFACT),
        )

        changed_artifact = copy.deepcopy(ARTIFACT)
        changed_artifact["content"]["raw_result_summary"] += " changed"
        second = witness.reenter_ground(
            copy.deepcopy(GROUND),
            changed_artifact,
        )
        self.assertNotEqual(
            first["source_bundle"]["evidence_artifact"]["sha256"],
            second["source_bundle"]["evidence_artifact"]["sha256"],
        )

        changed_ground = copy.deepcopy(GROUND)
        changed_ground["observed"] += " changed"
        third = witness.reenter_ground(
            changed_ground,
            copy.deepcopy(ARTIFACT),
        )
        self.assertNotEqual(
            first["source_bundle"]["ground_receipt"]["sha256"],
            third["source_bundle"]["ground_receipt"]["sha256"],
        )

    def test_reentry_does_not_upgrade_new_artifact(self):
        reentry = witness.reenter_ground(
            copy.deepcopy(GROUND),
            copy.deepcopy(ARTIFACT),
        )
        limits = " ".join(reentry["does_not_establish"]).lower()
        self.assertIn("independently verifies", limits)
        self.assertIn("resolves the upstream contradiction", limits)

        inspection = witness.inspect_reentry(reentry)
        self.assertFalse(inspection["independent_verification_claimed"])
        self.assertTrue(inspection["loop_closed"])
        self.assertTrue(inspection["upstream_world_sources_preserved"])

    def test_reentry_returns_as_new_source_not_final_story(self):
        reentry = witness.reenter_ground(
            copy.deepcopy(GROUND),
            copy.deepcopy(ARTIFACT),
        )
        self.assertIn("new source material", reentry["next_door"])
        inspection = witness.inspect_any(reentry)
        self.assertEqual(
            inspection["schema"],
            "static.witness-reentry-inspection/v0",
        )


if __name__ == "__main__":
    unittest.main()
