import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

dogram_nav = load_module("static_os_dogram_nav", "scripts/dogram_nav.py")
nav = load_module("static_os_nav", "scripts/nav.py")
history = load_module("static_os_navigation_history", "scripts/navigation_history.py")

BASE_PATHS = [
    "examples/nav-contacted.local-test.json",
    "examples/nav-to-witness.intake.json",
    "examples/world-receipt.independent-contradiction.json",
    "examples/make-ground.receipt.json",
    "examples/make-ground-to-witness.reentry.json",
    "examples/world-recursion-receipt.generated-downstream.json",
]
BASE = [
    json.loads((ROOT / path).read_text(encoding="utf-8"))
    for path in BASE_PATHS
]

HEADING_B = "Repeat the disputed behavior under captured conditions before widening the claim."
HEADING_C = "Compare the captured condition split with one genuinely external observation before widening the claim."


def make_admission(reorientation, actor):
    return {
        "schema": "static.nav-heading-admission/v0",
        "status": "admitted",
        "heading": reorientation["proposed_heading"],
        "transition_sha256": reorientation["transition_sha256"],
        "reorientation_sha256": history.canonical_digest(reorientation),
        "admitted_by": actor,
        "claim_limit": (
            "This fixture records explicit local admission for the navigation-history "
            "contract test. Admission does not prove the heading is correct."
        ),
    }


def cycle_one():
    artifacts = copy.deepcopy(BASE)
    trace = dogram_nav.build_trace(artifacts)
    transition = dogram_nav.make_transition(
        trace,
        HEADING_B,
        "Cycle 1 preserves that the new artifact is fresh but generated downstream.",
        [
            "upstream contradiction",
            "generated-downstream classification",
            "no fake second witness",
        ],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, "test-local-authority-cycle-1")
    return artifacts, trace, transition, reorientation, admission


def second_cycle_artifacts():
    artifacts = copy.deepcopy(BASE)

    nav_receipt = artifacts[0]
    nav_receipt["heading"] = HEADING_B
    nav_receipt["observed"] = (
        "A second bounded cycle compared the captured condition split with a fresh "
        "declared observation channel."
    )
    nav_receipt["delta"] = (
        "The useful question moved from reproducing the split to distinguishing "
        "condition dependence from genuinely external confirmation."
    )
    nav_receipt["next_heading"] = HEADING_B

    witness = artifacts[1]
    witness["source"]["sha256"] = "2" * 64
    witness["records"][0]["value"] = nav_receipt["observed"]
    witness["records"][1]["value"] = nav_receipt["delta"]
    witness["records"][2]["value"] = HEADING_B
    witness["establishes"][0] = "Cycle 2 contacted NAV receipt was ingested."

    world = artifacts[2]
    world["primary_source_sha256"] = "2" * 64
    world["candidate_source_sha256"] = "3" * 64
    world["claim_relation"] = "corrects"
    world["next_door"] = "Preserve the condition split while seeking an external observation."

    ground = artifacts[3]
    ground["plan_sha256"] = "4" * 64
    ground["ancestry"]["ground_plan_sha256"] = "4" * 64
    ground["ancestry"]["world_primary_source_sha256"] = "2" * 64
    ground["ancestry"]["world_candidate_source_sha256"] = "3" * 64
    ground["field_id"] = "nav-reproduction-field-002"
    ground["observed"] = (
        "The second-cycle field pass preserved the condition split and produced a "
        "separate comparison artifact."
    )
    ground["observation_relation"] = "inconclusive"
    ground["evidence_artifacts"] = ["cycle-002-raw.json"]

    reentry = artifacts[4]
    reentry["source_bundle"]["ground_receipt"]["sha256"] = "5" * 64
    reentry["source_bundle"]["evidence_artifact"]["artifact_id"] = "cycle-002-raw.json"
    reentry["source_bundle"]["evidence_artifact"]["sha256"] = "6" * 64
    reentry["source_bundle"]["ancestry"]["ground_plan_sha256"] = "4" * 64
    reentry["source_bundle"]["ancestry"]["world_primary_source_sha256"] = "2" * 64
    reentry["source_bundle"]["ancestry"]["world_candidate_source_sha256"] = "3" * 64
    reentry["records"][0]["value"] = ground["observed"]
    reentry["records"][2]["value"] = "inconclusive"
    reentry["next_door"] = "Carry cycle 2 source material into recursive WORLD classification."

    recursion = artifacts[5]
    recursion["candidate_source_sha256"] = "6" * 64
    recursion["relation_to_upstream"] = "inconclusive"
    recursion["establishes"][-1] = (
        "Relation to the upstream disagreement is preserved as: inconclusive."
    )
    recursion["next_door"] = (
        "Use the cycle 2 artifact as generated-downstream source material and seek "
        "one genuinely external observation before widening the claim."
    )

    return artifacts


def cycle_two():
    artifacts = second_cycle_artifacts()
    trace = dogram_nav.build_trace(artifacts)
    transition = dogram_nav.make_transition(
        trace,
        HEADING_C,
        "Cycle 2 leaves the condition split unresolved and changes the next useful move toward external comparison.",
        [
            "cycle 1 heading",
            "condition split",
            "generated-downstream ancestry",
        ],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, "test-local-authority-cycle-2")
    return artifacts, trace, transition, reorientation, admission


class TwoCycleNavigationHistoryTests(unittest.TestCase):
    def test_two_cycles_verify_complete(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        ledger = history.append_cycle(
            ledger, trace2, transition2, reorientation2, admission2
        )

        result = history.verify_history(ledger)
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["cycle_indices"], [0, 1])
        self.assertEqual(
            result["heading_path"],
            [transition1["from_heading"], HEADING_B, HEADING_C],
        )
        self.assertEqual(result["capsule_key_counts"], [10, 10])

    def test_cycle_capsules_do_not_embed_prior_history(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        ledger = history.append_cycle(
            ledger, trace2, transition2, reorientation2, admission2
        )

        capsules = list(ledger["cycles"].values())
        self.assertEqual(len(capsules), 2)
        for capsule in capsules:
            self.assertEqual(set(capsule), history.CYCLE_KEYS)
            self.assertNotIn("history", capsule)
            self.assertNotIn("trace", capsule)
            self.assertNotIn("transition", capsule)
            self.assertNotIn("parent", capsule)

        inspection = history.inspect(ledger)
        self.assertTrue(inspection["local_capsules_fixed_shape"])
        self.assertFalse(inspection["history_recursively_embedded"])

    def test_cycle_two_must_begin_at_admitted_cycle_one_heading(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )

        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        bad_transition = copy.deepcopy(transition2)
        bad_transition["from_heading"] = "A different origin"
        bad_reorientation = nav.make_reorientation(bad_transition)
        bad_admission = make_admission(
            bad_reorientation, "test-local-authority-bad-cycle"
        )

        with self.assertRaisesRegex(ValueError, "does not begin at admitted prior heading"):
            history.append_cycle(
                ledger,
                trace2,
                bad_transition,
                bad_reorientation,
                bad_admission,
            )

    def test_proposal_without_explicit_admission_cannot_be_appended(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, _ = cycle_one()
        bad_admission = {
            "schema": "static.nav-heading-admission/v0",
            "status": "proposed",
            "heading": HEADING_B,
            "transition_sha256": reorientation1["transition_sha256"],
            "reorientation_sha256": history.canonical_digest(reorientation1),
            "admitted_by": "nobody",
            "claim_limit": "not admitted",
        }
        with self.assertRaisesRegex(ValueError, "must be explicit"):
            history.append_cycle(
                ledger, trace1, transition1, reorientation1, bad_admission
            )

    def test_admission_cannot_change_proposed_heading(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        bad = copy.deepcopy(admission1)
        bad["heading"] = "Secretly different heading"
        with self.assertRaisesRegex(ValueError, "does not match proposal"):
            history.append_cycle(
                ledger, trace1, transition1, reorientation1, bad
            )

    def test_missing_parent_cycle_is_incomplete(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        ledger = history.append_cycle(
            ledger, trace2, transition2, reorientation2, admission2
        )

        head = ledger["cycles"][ledger["head_cycle_digest"]]
        parent = head["parent_cycle_digest"]
        del ledger["cycles"][parent]
        result = history.verify_history(ledger)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"], "missing_cycle_capsule")

    def test_mutated_transition_is_invalid(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        transition_digest = next(iter(ledger["transitions"]))
        ledger["transitions"][transition_digest]["delta_summary"] += " mutated"
        result = history.verify_history(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "transition_digest_mismatch")

    def test_cycle_two_trace_is_distinct_but_history_root_is_stable(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        root_digest = ledger["head_cycle_digest"]

        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        self.assertNotEqual(
            history.canonical_digest(trace1),
            history.canonical_digest(trace2),
        )
        ledger = history.append_cycle(
            ledger, trace2, transition2, reorientation2, admission2
        )
        head = ledger["cycles"][ledger["head_cycle_digest"]]
        self.assertEqual(head["root_cycle_digest"], root_digest)

    def test_adding_cycle_two_does_not_rewrite_cycle_one(self):
        ledger = history.make_ledger()
        _, trace1, transition1, reorientation1, admission1 = cycle_one()
        ledger = history.append_cycle(
            ledger, trace1, transition1, reorientation1, admission1
        )
        first_snapshot = copy.deepcopy(ledger)

        _, trace2, transition2, reorientation2, admission2 = cycle_two()
        ledger2 = history.append_cycle(
            ledger, trace2, transition2, reorientation2, admission2
        )

        first_digest = first_snapshot["head_cycle_digest"]
        self.assertEqual(
            ledger2["cycles"][first_digest],
            first_snapshot["cycles"][first_digest],
        )
        self.assertEqual(
            ledger2["transitions"][
                first_snapshot["cycles"][first_digest]["transition_sha256"]
            ],
            first_snapshot["transitions"][
                first_snapshot["cycles"][first_digest]["transition_sha256"]
            ],
        )


if __name__ == "__main__":
    unittest.main()
