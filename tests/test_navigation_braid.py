import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dogram_nav = load_module("static_os_dogram_nav", "scripts/dogram_nav.py")
nav = load_module("static_os_nav", "scripts/nav.py")
history = load_module("static_os_navigation_history", "scripts/navigation_history.py")
braid = load_module("static_os_navigation_braid", "scripts/navigation_braid.py")

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
BRANCH_ONE = "Seek one genuinely external observation before widening the claim."
BRANCH_TWO = "Hold the claim narrow and reproduce the condition split in a second environment."


def make_admission(reorientation, actor):
    return {
        "schema": "static.nav-heading-admission/v0",
        "status": "admitted",
        "heading": reorientation["proposed_heading"],
        "transition_sha256": reorientation["transition_sha256"],
        "reorientation_sha256": history.canonical_digest(reorientation),
        "admitted_by": actor,
        "claim_limit": (
            "This fixture records explicit local branch admission. "
            "Admission does not prove the branch is correct or preferred."
        ),
    }


def make_base_history():
    artifacts = copy.deepcopy(BASE)
    trace = dogram_nav.build_trace(artifacts)
    transition = dogram_nav.make_transition(
        trace,
        HEADING_B,
        "Cycle 1 preserves that the recursive artifact is new but generated downstream.",
        [
            "upstream contradiction",
            "generated-downstream classification",
            "no fake second witness",
        ],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, "base-history-local-authority")

    ledger = history.make_ledger()
    ledger = history.append_cycle(
        ledger, trace, transition, reorientation, admission
    )
    return ledger


def make_branch_trace():
    artifacts = copy.deepcopy(BASE)
    artifacts[0]["heading"] = HEADING_B
    artifacts[0]["next_heading"] = HEADING_B
    artifacts[0]["observed"] = (
        "The admitted parent heading exposed two bounded next moves that preserve "
        "the current uncertainty differently."
    )
    artifacts[0]["delta"] = (
        "The field supports more than one lawful next experiment without ranking "
        "either as the uniquely correct continuation."
    )

    artifacts[1]["records"][0]["value"] = artifacts[0]["observed"]
    artifacts[1]["records"][1]["value"] = artifacts[0]["delta"]
    artifacts[1]["records"][2]["value"] = HEADING_B
    artifacts[1]["establishes"][0] = "Branching NAV source was ingested."

    artifacts[5]["relation_to_upstream"] = "inconclusive"
    artifacts[5]["establishes"][-1] = (
        "Relation to the upstream disagreement is preserved as: inconclusive."
    )
    artifacts[5]["next_door"] = (
        "Preserve plural lawful next moves without collapsing them into a ranking."
    )

    return dogram_nav.build_trace(artifacts)


def make_bundle(branch_id, destination, reason):
    trace = make_branch_trace()
    transition = dogram_nav.make_transition(
        trace,
        destination,
        reason,
        [
            "the admitted parent heading",
            "the unresolved evidence boundary",
            "branch plurality without ranking",
        ],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(
        reorientation, f"local-authority-{branch_id}"
    )
    return {
        "branch_id": branch_id,
        "trace": trace,
        "transition": transition,
        "reorientation": reorientation,
        "admission": admission,
    }


def make_two_branches():
    return [
        make_bundle(
            "external-observation",
            BRANCH_ONE,
            "One lawful continuation seeks an evidence path outside the generated-downstream loop.",
        ),
        make_bundle(
            "second-environment",
            BRANCH_TWO,
            "Another lawful continuation pressure-tests whether the condition split reproduces elsewhere.",
        ),
    ]


class NavigationBraidTests(unittest.TestCase):
    def test_two_branches_verify_complete(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        result = braid.verify_braid(base, ledger, branch_set)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["verified_branches"], 2)
        self.assertEqual(result["parent_heading"], HEADING_B)
        self.assertEqual(set(result["branch_headings"]), {BRANCH_ONE, BRANCH_TWO})
        self.assertEqual(result["branch_capsule_key_counts"], [10, 10])

    def test_base_spine_is_not_rewritten_by_branching(self):
        base = make_base_history()
        before = copy.deepcopy(base)
        before_digest = braid.canonical_digest(base)

        ledger, branch_set = braid.build_braid(base, make_two_branches())

        self.assertEqual(base, before)
        self.assertEqual(braid.canonical_digest(base), before_digest)
        inspection = braid.inspect(base, ledger, branch_set)
        self.assertTrue(inspection["base_history_unchanged"])
        self.assertFalse(inspection["branch_histories_recursively_embedded"])

    def test_branches_share_parent_and_root_but_not_heading(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        capsules = list(ledger["branches"].values())

        self.assertEqual(
            len({c["parent_cycle_digest"] for c in capsules}),
            1,
        )
        self.assertEqual(
            len({c["root_cycle_digest"] for c in capsules}),
            1,
        )
        self.assertEqual(
            len({c["admitted_heading"] for c in capsules}),
            2,
        )

    def test_duplicate_heading_is_not_plural_navigation(self):
        base = make_base_history()
        bundles = make_two_branches()
        bundles[1] = make_bundle(
            "fake-second-branch",
            BRANCH_ONE,
            "Different prose but same admitted destination.",
        )
        with self.assertRaisesRegex(ValueError, "branch headings collapsed"):
            braid.build_braid(base, bundles)

    def test_branch_must_descend_from_admitted_parent_heading(self):
        base = make_base_history()
        bundle = make_two_branches()[0]
        bad_transition = copy.deepcopy(bundle["transition"])
        bad_transition["from_heading"] = "Not the admitted parent"
        bad_reorientation = nav.make_reorientation(bad_transition)
        bad_admission = make_admission(
            bad_reorientation, "bad-local-authority"
        )

        with self.assertRaisesRegex(ValueError, "does not descend"):
            braid.make_branch_capsule(
                base,
                "bad-branch",
                bundle["trace"],
                bad_transition,
                bad_reorientation,
                bad_admission,
            )

    def test_missing_branch_witness_is_incomplete(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        descriptor = branch_set["branches"][0]
        capsule = ledger["branches"][descriptor["branch_digest"]]
        del ledger["admissions"][capsule["admission_sha256"]]

        result = braid.verify_braid(base, ledger, branch_set)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"], "missing_admission")

    def test_mutated_branch_transition_is_invalid(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        descriptor = branch_set["branches"][0]
        capsule = ledger["branches"][descriptor["branch_digest"]]
        transition = ledger["transitions"][capsule["transition_sha256"]]
        transition["delta_summary"] += " mutated"

        result = braid.verify_braid(base, ledger, branch_set)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "transition_digest_mismatch")

    def test_undeclared_branch_is_invalid(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        fake = copy.deepcopy(next(iter(ledger["branches"].values())))
        fake["branch_id"] = "hidden-third-branch"
        fake["admitted_heading"] = "Hidden destination"
        ledger["branches"][braid.canonical_digest(fake)] = fake

        result = braid.verify_braid(base, ledger, branch_set)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "undeclared_branch_present")

    def test_branch_set_is_canonical_not_ranked(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, list(reversed(make_two_branches())))
        digests = [item["branch_digest"] for item in branch_set["branches"]]
        self.assertEqual(digests, sorted(digests))

        inspection = braid.inspect(base, ledger, branch_set)
        self.assertFalse(inspection["branch_ranking_claimed"])

    def test_branch_capsules_keep_fixed_shape(self):
        base = make_base_history()
        ledger, branch_set = braid.build_braid(base, make_two_branches())
        for capsule in ledger["branches"].values():
            self.assertEqual(set(capsule), braid.BRANCH_KEYS)
            self.assertNotIn("parent", capsule)
            self.assertNotIn("history", capsule)
            self.assertNotIn("ancestry", capsule)
            self.assertNotIn("branch_set", capsule)

        inspection = braid.inspect(base, ledger, branch_set)
        self.assertTrue(inspection["local_branches_fixed_shape"])

    def test_branch_set_cannot_mix_different_parent_spines(self):
        base = make_base_history()
        bundles = make_two_branches()
        first = braid.make_branch_capsule(base, **{
            "branch_id": bundles[0]["branch_id"],
            "trace": bundles[0]["trace"],
            "transition": bundles[0]["transition"],
            "reorientation": bundles[0]["reorientation"],
            "admission": bundles[0]["admission"],
        })
        second = copy.deepcopy(first)
        second["branch_id"] = "other-parent"
        second["admitted_heading"] = BRANCH_TWO
        second["parent_cycle_digest"] = "9" * 64
        with self.assertRaisesRegex(ValueError, "share one parent"):
            braid.make_branch_set([first, second])


if __name__ == "__main__":
    unittest.main()
