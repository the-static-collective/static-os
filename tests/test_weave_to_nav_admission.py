import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fixture_mod = load_module(
    "static_os_navigation_weave_fixture",
    "tests/test_navigation_weave.py",
)
weave_nav = load_module(
    "static_os_weave_nav",
    "scripts/weave_nav.py",
)
weave = load_module(
    "static_os_navigation_weave_for_admission",
    "scripts/navigation_weave.py",
)


def make_fixture():
    (
        base,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
        _,
    ) = fixture_mod.make_weave_fixture()
    return (
        base,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
    )


def make_admission_and_generation():
    fixture = make_fixture()
    admission = weave_nav.make_admission(
        *fixture,
        admitted_by="test-local-weave-authority",
        accept_proposal=True,
    )
    generation = weave_nav.make_generation(
        admission,
        fixture[3],
        fixture[4],
        fixture[5],
    )
    return fixture, admission, generation


class WeaveToNavAdmissionTests(unittest.TestCase):
    def test_explicit_acceptance_required(self):
        fixture = make_fixture()
        with self.assertRaisesRegex(ValueError, "explicit local acceptance"):
            weave_nav.make_admission(
                *fixture,
                admitted_by="test-local-weave-authority",
                accept_proposal=False,
            )

    def test_admission_actor_required(self):
        fixture = make_fixture()
        with self.assertRaisesRegex(ValueError, "actor missing"):
            weave_nav.make_admission(
                *fixture,
                admitted_by="",
                accept_proposal=True,
            )

    def test_admitted_heading_exactly_matches_weave_proposal(self):
        fixture, admission, _ = make_admission_and_generation()
        self.assertEqual(
            admission["heading"],
            fixture[5]["proposed_heading"],
        )
        self.assertEqual(admission["status"], "admitted")

    def test_admission_preserves_typed_provenance_addresses(self):
        fixture, admission, _ = make_admission_and_generation()
        weave_ledger = fixture[3]
        parent_set = fixture[4]
        weave_capsule = fixture[5]

        self.assertEqual(
            admission["weave_capsule_sha256"],
            weave_nav.canonical_digest(weave_capsule),
        )
        self.assertEqual(
            admission["parent_set_sha256"],
            weave_nav.canonical_digest(parent_set),
        )
        self.assertEqual(
            admission["weave_ledger_sha256"],
            weave_nav.canonical_digest(weave_ledger),
        )
        self.assertEqual(
            set(admission["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )

    def test_generation_is_bounded_and_typed(self):
        _, admission, generation = make_admission_and_generation()
        self.assertEqual(set(generation), weave_nav.GENERATION_KEYS)
        self.assertEqual(generation["status"], "admitted")
        self.assertEqual(
            generation["admission_sha256"],
            weave_nav.canonical_digest(admission),
        )
        self.assertEqual(
            set(generation["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        for forbidden in (
            "parents",
            "parent_set",
            "weave_ledger",
            "braid",
            "history",
            "continuation",
            "open_branch",
        ):
            self.assertNotIn(forbidden, generation)

    def test_generation_verifies_complete(self):
        fixture, admission, generation = make_admission_and_generation()
        result = weave_nav.verify_generation(
            *fixture,
            admission,
            generation,
        )
        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            set(result["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        self.assertEqual(
            result["admitted_heading"],
            fixture[5]["proposed_heading"],
        )

    def test_inspection_keeps_open_branch_open(self):
        fixture, admission, generation = make_admission_and_generation()
        inspection = weave_nav.inspect(
            *fixture,
            admission,
            generation,
        )
        self.assertTrue(inspection["typed_provenance_preserved"])
        self.assertFalse(inspection["open_branch_closed"])
        self.assertFalse(inspection["parent_ranking_claimed"])
        self.assertFalse(inspection["automatic_admission_used"])
        self.assertFalse(inspection["parents_recursively_embedded"])

    def test_relation_kind_collapse_is_refused_before_admission(self):
        fixture = list(make_fixture())
        bad_capsule = copy.deepcopy(fixture[5])
        bad_capsule["relation_kinds"] = ["branch_continuation"]
        fixture[5] = bad_capsule

        with self.assertRaisesRegex(ValueError, "weave is not admissible"):
            weave_nav.make_admission(
                *fixture,
                admitted_by="test-local-weave-authority",
                accept_proposal=True,
            )

    def test_rehashed_wrong_parent_set_breaks_admission_chain(self):
        fixture, admission, generation = make_admission_and_generation()
        bad_parent_set = copy.deepcopy(fixture[4])
        bad_parent_set["parents"][0]["heading"] += " rewritten"

        result = weave_nav.verify_generation(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            bad_parent_set,
            fixture[5],
            admission,
            generation,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertIn(
            result["reason"],
            {"weave_invalid", "admission_parent_set_sha256_mismatch"},
        )

    def test_admission_cannot_rewrite_heading_after_weave_verification(self):
        fixture, admission, generation = make_admission_and_generation()
        bad_admission = copy.deepcopy(admission)
        bad_admission["heading"] = "A different admitted heading"
        bad_generation = copy.deepcopy(generation)
        bad_generation["admission_sha256"] = weave_nav.canonical_digest(
            bad_admission
        )
        bad_generation["admitted_heading"] = bad_admission["heading"]

        result = weave_nav.verify_generation(
            *fixture,
            bad_admission,
            bad_generation,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "admission_heading_mismatch")

    def test_generation_cannot_drop_one_relation_kind(self):
        fixture, admission, generation = make_admission_and_generation()
        bad_generation = copy.deepcopy(generation)
        bad_generation["relation_kinds"] = ["branch_continuation"]

        result = weave_nav.verify_generation(
            *fixture,
            admission,
            bad_generation,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertIn("relation_kinds", result["reason"])

    def test_weave_mutation_after_admission_is_detected(self):
        fixture, admission, generation = make_admission_and_generation()
        bad_weave = copy.deepcopy(fixture[5])
        bad_weave["proposed_heading"] += " changed"

        result = weave_nav.verify_generation(
            fixture[0],
            fixture[1],
            fixture[2],
            fixture[3],
            fixture[4],
            bad_weave,
            admission,
            generation,
        )
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "weave_invalid")

    def test_generation_can_recover_typed_parent_set_by_digest(self):
        fixture, _, generation = make_admission_and_generation()
        parent_set = fixture[4]
        self.assertEqual(
            generation["parent_set_sha256"],
            weave_nav.canonical_digest(parent_set),
        )
        self.assertEqual(
            {parent["kind"] for parent in parent_set["parents"]},
            set(generation["relation_kinds"]),
        )


if __name__ == "__main__":
    unittest.main()
