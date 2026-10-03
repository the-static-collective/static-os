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
weave = load_module("static_os_navigation_weave", "scripts/navigation_weave.py")

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
CONTINUED = "Use the external observation to test whether the captured condition split generalizes."
WEAVE_HEADING = (
    "Compare the continued external-observation path with the still-open "
    "second-environment path before choosing another move."
)


def make_admission(reorientation, actor):
    return {
        "schema": "static.nav-heading-admission/v0",
        "status": "admitted",
        "heading": reorientation["proposed_heading"],
        "transition_sha256": reorientation["transition_sha256"],
        "reorientation_sha256": history.canonical_digest(reorientation),
        "admitted_by": actor,
        "claim_limit": (
            "This fixture records explicit local admission. "
            "Admission does not prove the heading is correct."
        ),
    }


def make_base_history():
    trace = dogram_nav.build_trace(copy.deepcopy(BASE))
    transition = dogram_nav.make_transition(
        trace,
        HEADING_B,
        "The first cycle preserves new evidence without fake independence.",
        ["upstream contradiction", "generated-downstream classification"],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, "weave-base-authority")
    ledger = history.make_ledger()
    return history.append_cycle(
        ledger, trace, transition, reorientation, admission
    )


def make_branch_trace():
    artifacts = copy.deepcopy(BASE)
    artifacts[0]["heading"] = HEADING_B
    artifacts[0]["next_heading"] = HEADING_B
    artifacts[0]["observed"] = "The admitted heading exposed plural lawful continuations."
    artifacts[0]["delta"] = "Two bounded next moves remain live without ranking."

    artifacts[1]["records"][0]["value"] = artifacts[0]["observed"]
    artifacts[1]["records"][1]["value"] = artifacts[0]["delta"]
    artifacts[1]["records"][2]["value"] = HEADING_B
    artifacts[1]["establishes"][0] = "Weave branch source was ingested."

    artifacts[5]["relation_to_upstream"] = "inconclusive"
    artifacts[5]["establishes"][-1] = (
        "Relation to the upstream disagreement is preserved as: inconclusive."
    )
    artifacts[5]["next_door"] = "Keep plural next moves addressable without ranking."
    return dogram_nav.build_trace(artifacts)


def make_branch_bundle(branch_id, destination):
    trace = make_branch_trace()
    transition = dogram_nav.make_transition(
        trace,
        destination,
        f"Branch {branch_id} preserves a distinct lawful continuation.",
        ["shared parent", "unresolved evidence", "branch plurality"],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, f"authority-{branch_id}")
    return {
        "branch_id": branch_id,
        "trace": trace,
        "transition": transition,
        "reorientation": reorientation,
        "admission": admission,
    }


def make_braid():
    base = make_base_history()
    bundles = [
        make_branch_bundle("external-observation", BRANCH_ONE),
        make_branch_bundle("second-environment", BRANCH_TWO),
    ]
    braid_ledger, branch_set = braid.build_braid(base, bundles)
    by_heading = {
        capsule["admitted_heading"]: digest
        for digest, capsule in braid_ledger["branches"].items()
    }
    return base, braid_ledger, branch_set, by_heading


def make_continuation_trace():
    artifacts = copy.deepcopy(BASE)
    artifacts[0]["heading"] = BRANCH_ONE
    artifacts[0]["next_heading"] = BRANCH_ONE
    artifacts[0]["observed"] = (
        "The external-observation branch returned a bounded observation that can be "
        "compared with the still-open environment-reproduction branch."
    )
    artifacts[0]["delta"] = (
        "The continued branch now carries information unavailable at the original "
        "branch point, while its sibling remains lawfully open."
    )
    artifacts[1]["records"][0]["value"] = artifacts[0]["observed"]
    artifacts[1]["records"][1]["value"] = artifacts[0]["delta"]
    artifacts[1]["records"][2]["value"] = BRANCH_ONE
    artifacts[1]["establishes"][0] = "Continued branch source was ingested."
    artifacts[5]["relation_to_upstream"] = "inconclusive"
    artifacts[5]["establishes"][-1] = (
        "Relation to the upstream disagreement is preserved as: inconclusive."
    )
    artifacts[5]["next_door"] = (
        "Compose this continued path with the still-open sibling without erasing relation kind."
    )
    return dogram_nav.build_trace(artifacts)


def make_continuation_bundle(parent_branch_digest):
    trace = make_continuation_trace()
    transition = dogram_nav.make_transition(
        trace,
        CONTINUED,
        "The external-observation branch continued one generation while its sibling stayed open.",
        [
            "the original branch point",
            "the still-open sibling",
            "typed relation history",
        ],
    )
    reorientation = nav.make_reorientation(transition)
    admission = make_admission(reorientation, "continuation-authority")
    return {
        "parent_branch_digest": parent_branch_digest,
        "continuation_id": "external-observation-continuation-001",
        "trace": trace,
        "transition": transition,
        "reorientation": reorientation,
        "admission": admission,
    }


def make_weave_fixture():
    base, braid_ledger, branch_set, by_heading = make_braid()
    continuation_bundle = make_continuation_bundle(by_heading[BRANCH_ONE])
    weave_ledger, parent_set, weave_capsule = weave.build_weave(
        base,
        braid_ledger,
        branch_set,
        continuation_bundle,
        by_heading[BRANCH_TWO],
        WEAVE_HEADING,
    )
    return (
        base,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
        by_heading,
    )


class NavigationWeaveTests(unittest.TestCase):
    def test_typed_weave_verifies_complete(self):
        fixture = make_weave_fixture()
        result = weave.verify_weave(*fixture[:6])

        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["verified_parents"], 2)
        self.assertEqual(
            set(result["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        self.assertEqual(result["proposed_heading"], WEAVE_HEADING)

    def test_weave_preserves_relation_kinds(self):
        fixture = make_weave_fixture()
        inspection = weave.inspect(*fixture[:6])
        self.assertTrue(inspection["relation_kinds_preserved"])
        self.assertFalse(inspection["branch_ranking_claimed"])
        self.assertFalse(inspection["branch_merge_claimed"])
        self.assertFalse(inspection["weave_activated"])

    def test_base_spine_and_braid_remain_unchanged(self):
        base, braid_ledger, branch_set, *_ = make_weave_fixture()
        base_snapshot = copy.deepcopy(base)
        braid_snapshot = copy.deepcopy(braid_ledger)
        branch_snapshot = copy.deepcopy(branch_set)

        parent_branch = next(
            digest
            for digest, capsule in braid_ledger["branches"].items()
            if capsule["admitted_heading"] == BRANCH_ONE
        )
        open_branch = next(
            digest
            for digest, capsule in braid_ledger["branches"].items()
            if capsule["admitted_heading"] == BRANCH_TWO
        )
        weave.build_weave(
            base,
            braid_ledger,
            branch_set,
            make_continuation_bundle(parent_branch),
            open_branch,
            WEAVE_HEADING,
        )

        self.assertEqual(base, base_snapshot)
        self.assertEqual(braid_ledger, braid_snapshot)
        self.assertEqual(branch_set, branch_snapshot)

    def test_kind_substitution_fails_even_after_rehash(self):
        (
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
            _,
        ) = make_weave_fixture()

        altered_parent_set = copy.deepcopy(parent_set)
        for descriptor in altered_parent_set["parents"]:
            descriptor["kind"] = (
                "open_branch"
                if descriptor["kind"] == "branch_continuation"
                else "branch_continuation"
            )
        altered_parent_set["parents"].sort(
            key=lambda item: (item["kind"], item["head_digest"])
        )

        altered_capsule = copy.deepcopy(weave_capsule)
        altered_capsule["parent_set_sha256"] = weave.canonical_digest(
            altered_parent_set
        )

        altered_ledger = copy.deepcopy(weave_ledger)
        altered_ledger["parent_set_sha256"] = weave.canonical_digest(
            altered_parent_set
        )
        altered_ledger["weave_capsule_sha256"] = weave.canonical_digest(
            altered_capsule
        )

        result = weave.verify_weave(
            base,
            braid_ledger,
            branch_set,
            altered_ledger,
            altered_parent_set,
            altered_capsule,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "parent_kind_mismatch")

    def test_missing_continuation_witness_is_incomplete(self):
        (
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
            _,
        ) = make_weave_fixture()
        weave_ledger["continuations"].clear()

        result = weave.verify_weave(
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
        )
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"], "missing_continuation")

    def test_mutated_continuation_is_invalid(self):
        (
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
            _,
        ) = make_weave_fixture()
        digest = next(iter(weave_ledger["continuations"]))
        weave_ledger["continuations"][digest]["admitted_heading"] += " mutated"

        result = weave.verify_weave(
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "continuation_digest_mismatch")

    def test_continued_branch_cannot_also_be_open_parent(self):
        base, braid_ledger, branch_set, by_heading = make_braid()
        continuation = weave.make_continuation(
            base,
            braid_ledger,
            branch_set,
            by_heading[BRANCH_ONE],
            "continuation-001",
            **{
                key: value
                for key, value in make_continuation_bundle(by_heading[BRANCH_ONE]).items()
                if key in {"trace", "transition", "reorientation", "admission"}
            },
        )
        same_branch = braid_ledger["branches"][by_heading[BRANCH_ONE]]
        with self.assertRaisesRegex(ValueError, "cannot also be the open sibling"):
            weave.make_parent_set(continuation, same_branch)

    def test_parent_set_is_canonical_and_typed(self):
        fixture = make_weave_fixture()
        parent_set = fixture[4]
        self.assertEqual(
            parent_set["parents"],
            sorted(
                parent_set["parents"],
                key=lambda item: (item["kind"], item["head_digest"]),
            ),
        )
        identities = {
            (p["kind"], p["head_digest"]) for p in parent_set["parents"]
        }
        self.assertEqual(len(identities), 2)

    def test_weave_capsule_stays_bounded(self):
        fixture = make_weave_fixture()
        weave_capsule = fixture[5]
        self.assertEqual(set(weave_capsule), weave.WEAVE_KEYS)
        for forbidden in ("parents", "history", "braid", "continuation", "ancestry"):
            self.assertNotIn(forbidden, weave_capsule)

    def test_weave_is_proposal_not_admission(self):
        fixture = make_weave_fixture()
        weave_capsule = fixture[5]
        self.assertEqual(weave_capsule["status"], "proposed")
        self.assertIn("does not rank", weave_capsule["claim_limit"])
        self.assertIn("activate", weave_capsule["claim_limit"])

    def test_relation_kind_collapse_is_invalid(self):
        (
            base,
            braid_ledger,
            branch_set,
            weave_ledger,
            parent_set,
            weave_capsule,
            _,
        ) = make_weave_fixture()
        bad = copy.deepcopy(parent_set)
        bad["parents"][1]["kind"] = bad["parents"][0]["kind"]
        bad["parents"].sort(key=lambda item: (item["kind"], item["head_digest"]))
        bad_capsule = copy.deepcopy(weave_capsule)
        bad_capsule["parent_set_sha256"] = weave.canonical_digest(bad)
        bad_ledger = copy.deepcopy(weave_ledger)
        bad_ledger["parent_set_sha256"] = weave.canonical_digest(bad)
        bad_ledger["weave_capsule_sha256"] = weave.canonical_digest(bad_capsule)

        result = weave.verify_weave(
            base,
            braid_ledger,
            branch_set,
            bad_ledger,
            bad,
            bad_capsule,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "relation_kind_collapse")


if __name__ == "__main__":
    unittest.main()
