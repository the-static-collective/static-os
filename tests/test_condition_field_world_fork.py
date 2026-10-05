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


residual_fixture = load_module(
    "static_os_residual_fixture_for_condition_field",
    "tests/test_residual_witness_discriminator.py",
)
condition = load_module(
    "static_os_condition_field_test",
    "scripts/condition_field.py",
)


def root():
    specimen = residual_fixture.make_residual(second_relation="contradicts")
    return specimen["first"]["field"], specimen["update"]


def mineral_want(seed="a", kind="mineral.parameter-sweep/v0"):
    return {
        "request_sha256": seed * 64,
        "mineral_kind": kind,
        "status": "requested",
        "authorization": "none",
    }


def branches():
    field, update = root()
    return field, update, [
        condition.make_branch(
            field, update, "alpha", "cedar",
            "ambient_temperature", "20C", "25C",
            accept_branch=True,
        ),
        condition.make_branch(
            field, update, "beta", "river",
            "sampling_interval", "10s", "1s",
            accept_branch=True,
            mineral_want=mineral_want(),
        ),
        condition.make_branch(
            field, update, "gamma", "ember",
            "observer_blinding", "single_blind", "double_blind",
            accept_branch=True,
        ),
    ]


def complete_results(branch_list):
    return [
        condition.make_result(
            branch_list[0],
            "contacted",
            "corroborates",
            "Alpha reproduced the prior-supported path under the temperature change.",
            "Alpha leaves no unresolved execution residue beyond the recorded observation.",
        ),
        condition.make_result(
            branch_list[1],
            "contacted",
            "contradicts",
            "Beta reproduced the challenged path under the sampling change.",
            "Beta returns one verified-compute artifact address plus the local observation.",
            mineral_artifact_sha256="b" * 64,
        ),
        condition.make_result(
            branch_list[2],
            "contacted",
            "corrects",
            "Gamma exposed a narrower correction under stronger blinding.",
            "Gamma preserves the original witness disagreement plus the narrower correction.",
        ),
    ]


def full_specimen():
    field, update, branch_list = branches()
    result_list = complete_results(branch_list)
    postbag = condition.make_postbag(branch_list, result_list)
    association = condition.make_association(postbag, branch_list, result_list)
    frontier = condition.make_frontier(postbag, association, result_list)
    return field, update, branch_list, result_list, postbag, association, frontier


class ConditionFieldWorldForkTests(unittest.TestCase):
    def test_three_sovereign_worlds_change_one_distinct_condition_each(self):
        _, _, branch_list, _, _, _, _ = full_specimen()
        self.assertEqual(len({b["owner"] for b in branch_list}), 3)
        self.assertEqual(
            len({b["changed_condition"]["name"] for b in branch_list}),
            3,
        )
        for branch in branch_list:
            self.assertEqual(branch["admission_status"], "admitted")
            self.assertNotEqual(
                branch["changed_condition"]["before"],
                branch["changed_condition"]["after"],
            )

    def test_explicit_branch_admission_is_required(self):
        field, update = root()
        with self.assertRaisesRegex(ValueError, "explicit local branch admission"):
            condition.make_branch(
                field, update, "alpha", "cedar",
                "temperature", "20C", "25C",
                accept_branch=False,
            )

    def test_noop_condition_change_is_refused(self):
        field, update = root()
        with self.assertRaisesRegex(ValueError, "actually change one condition"):
            condition.make_branch(
                field, update, "alpha", "cedar",
                "temperature", "20C", "20C",
                accept_branch=True,
            )

    def test_postbag_holds_all_and_ranks_none(self):
        _, _, branch_list, result_list, postbag, _, _ = full_specimen()
        self.assertEqual(len(postbag["returns"]), 3)
        self.assertTrue(postbag["all_returns_held"])
        self.assertFalse(postbag["return_order_ranked"])
        self.assertEqual(
            {item["branch_sha256"] for item in postbag["returns"]},
            {condition.digest(b) for b in branch_list},
        )
        self.assertEqual(
            {item["result_sha256"] for item in postbag["returns"]},
            {condition.digest(r) for r in result_list},
        )

    def test_postbag_is_order_invariant(self):
        _, _, branch_list, result_list, postbag, _, _ = full_specimen()
        reversed_bag = condition.make_postbag(
            list(reversed(branch_list)),
            list(reversed(result_list)),
        )
        self.assertEqual(condition.digest(postbag), condition.digest(reversed_bag))

    def test_distinct_sovereign_owners_are_required(self):
        _, _, branch_list = branches()
        result_list = complete_results(branch_list)
        bad = copy.deepcopy(branch_list)
        bad[2]["owner"] = bad[0]["owner"]
        result_list[2] = condition.make_result(
            bad[2],
            "contacted",
            "corrects",
            "Gamma-like result.",
            "Residue preserved.",
        )
        with self.assertRaisesRegex(ValueError, "distinct sovereign owners"):
            condition.make_postbag(bad, result_list)

    def test_distinct_condition_names_are_required(self):
        _, _, branch_list = branches()
        bad = copy.deepcopy(branch_list)
        bad[2]["changed_condition"]["name"] = bad[0]["changed_condition"]["name"]
        result_list = complete_results(bad)
        with self.assertRaisesRegex(ValueError, "distinct named condition"):
            condition.make_postbag(bad, result_list)

    def test_mineral_want_carries_no_execution_authority(self):
        _, _, branch_list = branches()
        want = branch_list[1]["mineral_want"]
        self.assertIsNotNone(want)
        self.assertEqual(want["status"], "requested")
        self.assertEqual(want["authorization"], "none")

    def test_branch_without_want_cannot_return_mineral_artifact(self):
        _, _, branch_list = branches()
        with self.assertRaisesRegex(ValueError, "without Mineral WANT"):
            condition.make_result(
                branch_list[0],
                "contacted",
                "corroborates",
                "Observation.",
                "Residue.",
                mineral_artifact_sha256="f" * 64,
            )

    def test_dogram_reports_split_without_causal_claim(self):
        *_, association, frontier = full_specimen()
        self.assertEqual(association["status"], "complete")
        self.assertEqual(
            set(association["distinct_outcomes"]),
            {"corroborates", "contradicts", "corrects"},
        )
        self.assertTrue(association["split_detected"])
        self.assertFalse(association["causal_claimed"])
        self.assertFalse(association["ranking_used"])

        inspection = condition.inspect(frontier, association)
        self.assertTrue(inspection["split_detected"])
        self.assertFalse(inspection["causal_claimed"])
        self.assertFalse(inspection["ranking_used"])

    def test_causality_cannot_be_laundered_into_association(self):
        *_, association, _ = full_specimen()
        bad = copy.deepcopy(association)
        bad["causal_claimed"] = True
        with self.assertRaisesRegex(ValueError, "cannot claim causality"):
            condition.validate_association(bad)

    def test_refusal_is_preserved_as_incomplete_not_failure_or_rank(self):
        field, update, branch_list = branches()
        result_list = complete_results(branch_list)
        result_list[2] = condition.make_result(
            branch_list[2],
            "refused",
            None,
            "",
            "Gamma refused the second contact; the unopened condition path remains residue.",
        )
        postbag = condition.make_postbag(branch_list, result_list)
        association = condition.make_association(postbag, branch_list, result_list)
        frontier = condition.make_frontier(postbag, association, result_list)

        self.assertEqual(association["status"], "incomplete")
        self.assertFalse(association["ranking_used"])
        self.assertEqual(len(postbag["returns"]), 3)
        self.assertEqual(frontier["parent_count"], 3)
        self.assertEqual(frontier["status"], "held")

    def test_recombinant_frontier_has_three_parents_and_no_canonical_parent(self):
        _, _, _, result_list, postbag, association, frontier = full_specimen()
        self.assertEqual(frontier["parent_count"], 3)
        self.assertEqual(
            set(frontier["parent_result_sha256s"]),
            {condition.digest(r) for r in result_list},
        )
        self.assertFalse(frontier["parent_bodies_embedded"])
        self.assertFalse(frontier["canonical_parent_selected"])
        self.assertEqual(frontier["status"], "held")
        self.assertEqual(frontier["postbag_sha256"], condition.digest(postbag))
        self.assertEqual(
            frontier["association_sha256"],
            condition.digest(association),
        )

    def test_frontier_is_order_invariant(self):
        _, _, branch_list, result_list, _, _, frontier = full_specimen()
        postbag = condition.make_postbag(
            [branch_list[2], branch_list[0], branch_list[1]],
            [result_list[1], result_list[2], result_list[0]],
        )
        association = condition.make_association(
            postbag,
            list(reversed(branch_list)),
            [result_list[2], result_list[0], result_list[1]],
        )
        reordered = condition.make_frontier(
            postbag,
            association,
            list(reversed(result_list)),
        )
        self.assertEqual(
            frontier["frontier_root_sha256"],
            reordered["frontier_root_sha256"],
        )

    def test_missing_world_return_is_refused(self):
        _, _, branch_list = branches()
        result_list = complete_results(branch_list)
        with self.assertRaisesRegex(ValueError, "exactly three results"):
            condition.make_postbag(branch_list, result_list[:2])

    def test_result_cannot_point_at_unknown_branch(self):
        _, _, branch_list = branches()
        result_list = complete_results(branch_list)
        bad = copy.deepcopy(result_list)
        bad[0]["branch_sha256"] = "e" * 64
        with self.assertRaisesRegex(ValueError, "unknown branch"):
            condition.make_postbag(branch_list, bad)

    def test_frontier_cannot_select_canonical_parent(self):
        *_, frontier = full_specimen()
        bad = copy.deepcopy(frontier)
        bad["canonical_parent_selected"] = True
        with self.assertRaisesRegex(ValueError, "may not select a canonical parent"):
            condition.validate_frontier(bad)

    def test_frontier_cannot_embed_parent_bodies(self):
        *_, frontier = full_specimen()
        bad = copy.deepcopy(frontier)
        bad["parent_bodies_embedded"] = True
        with self.assertRaisesRegex(ValueError, "may not embed parent bodies"):
            condition.validate_frontier(bad)

    def test_association_cannot_smuggle_hidden_ranking_field(self):
        *_, association, _ = full_specimen()
        bad = copy.deepcopy(association)
        bad["preferred_world"] = "beta"
        with self.assertRaisesRegex(ValueError, "shape drifted"):
            condition.validate_association(bad)

    def test_frontier_cannot_smuggle_preferred_parent(self):
        *_, frontier = full_specimen()
        bad = copy.deepcopy(frontier)
        bad["preferred_parent_sha256"] = bad["parent_result_sha256s"][0]
        with self.assertRaisesRegex(ValueError, "shape drifted"):
            condition.validate_frontier(bad)


if __name__ == "__main__":
    unittest.main()
