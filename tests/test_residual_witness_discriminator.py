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


first_fixture = load_module(
    "static_os_first_discrimination_fixture_for_residual",
    "tests/test_witness_field_discrimination_cycle.py",
)
residual = load_module(
    "static_os_residual_witness_cycle_test",
    "scripts/residual_witness_cycle.py",
)


def residual_candidate(first, candidate_id, changed_variables, external_dependencies):
    update = first["update"]
    prior = update["contact_supported_relations"][0]
    target = update["contact_challenged_relations"][0]
    return {
        "schema": "static.residual-witness-discriminator-candidate/v0",
        "candidate_id": candidate_id,
        "original_field_sha256": residual.digest(first["field"]),
        "first_update_sha256": residual.digest(update),
        "first_contact_sha256": residual.digest(first["contact_capsule"]),
        "prior_supported_relation": prior,
        "target_challenged_relation": target,
        "proposed_heading": (
            "Run one differently conditioned blinded replay targeted at whether the "
            "challenged witness path can reproduce."
        ),
        "bounded_move": (
            "Change one condition not changed in contact #1 and run one blinded replay "
            "with outcomes predeclared for the prior-supported and challenged paths."
        ),
        "paths": [
            {
                "relation": prior,
                "discriminating_observation": (
                    "The second replay again matches the relation supported by contact #1."
                ),
            },
            {
                "relation": target,
                "discriminating_observation": (
                    "The second replay matches the relation challenged by contact #1."
                ),
            },
        ],
        "preserve": [
            "contact #1 as immutable history",
            "every original witness source",
            "the challenged relation as a live test target",
        ],
        "aperture": [
            "one second-contact result that can disagree with contact #1"
        ],
        "stop_condition": "Stop after one second replay is captured.",
        "cost_vector": {
            "irreversible_steps": 0,
            "changed_variables": changed_variables,
            "world_contacts": 1,
            "external_dependencies": external_dependencies,
        },
        "claim_limit": (
            "This residual candidate targets a challenged path but does not assume "
            "that path is true, false, or less authoritative."
        ),
    }


def make_residual(
    relations=("corroborates", "corroborates", "contradicts"),
    second_relation="contradicts",
):
    first = first_fixture.make_source(
        relations=relations,
        observed_relation="corroborates",
    )
    candidates = [
        residual_candidate(first, "larger-residual", 2, 0),
        residual_candidate(first, "smallest-residual", 1, 0),
        residual_candidate(first, "dependency-heavy-residual", 1, 2),
    ]
    transition = residual.select_transition(
        first["field"],
        first["field_receipt"],
        first["update"],
        first["contact_capsule"],
        candidates,
    )
    selected = next(
        item for item in candidates
        if residual.digest(item) == transition["candidate_sha256"]
    )
    reorientation = residual.make_reorientation(transition)
    admission = residual.make_admission(
        selected,
        transition,
        reorientation,
        admitted_by="residual-local-authority",
        accept_proposal=True,
    )
    orientation = residual.start_orientation(admission, selected)
    observation = next(
        path["discriminating_observation"]
        for path in selected["paths"]
        if path["relation"] == second_relation
    )
    second_capsule, second_contact = residual.perform_contact(
        admission,
        selected,
        orientation,
        second_relation,
        observation,
        "Preserve both contacts and navigate from the remaining conditional tension.",
    )
    update = residual.update_history(
        first["field"],
        first["update"],
        first["contact_capsule"],
        selected,
        admission,
        orientation,
        second_capsule,
        second_contact,
    )
    return {
        "first": first,
        "candidates": candidates,
        "selected": selected,
        "transition": transition,
        "reorientation": reorientation,
        "admission": admission,
        "orientation": orientation,
        "second_capsule": second_capsule,
        "second_contact": second_contact,
        "update": update,
    }


class ResidualWitnessDiscriminatorTests(unittest.TestCase):
    def test_smallest_residual_candidate_is_selected(self):
        source = make_residual()
        self.assertEqual(source["selected"]["candidate_id"], "smallest-residual")
        self.assertEqual(source["transition"]["cost_vector"]["changed_variables"], 1)
        self.assertEqual(source["transition"]["cost_vector"]["external_dependencies"], 0)

    def test_residual_candidate_targets_challenged_not_supported_relation(self):
        source = make_residual()
        first_update = source["first"]["update"]
        self.assertEqual(
            source["selected"]["prior_supported_relation"],
            first_update["contact_supported_relations"][0],
        )
        self.assertIn(
            source["selected"]["target_challenged_relation"],
            first_update["contact_challenged_relations"],
        )
        self.assertNotEqual(
            source["selected"]["prior_supported_relation"],
            source["selected"]["target_challenged_relation"],
        )

    def test_candidate_cannot_target_non_challenged_relation(self):
        first = first_fixture.make_source(observed_relation="corroborates")
        candidate = residual_candidate(first, "bad-target", 1, 0)
        candidate["target_challenged_relation"] = candidate["prior_supported_relation"]
        candidate["paths"][1]["relation"] = candidate["prior_supported_relation"]

        with self.assertRaisesRegex(
            ValueError,
            "relation pair invalid|paths must cover prior and challenged",
        ):
            residual.select_transition(
                first["field"],
                first["field_receipt"],
                first["update"],
                first["contact_capsule"],
                [candidate],
            )

    def test_first_contact_is_preserved_by_address_through_second_transition(self):
        source = make_residual()
        first_contact_sha = residual.digest(source["first"]["contact_capsule"])
        self.assertEqual(source["transition"]["first_contact_sha256"], first_contact_sha)
        self.assertEqual(source["admission"]["first_contact_sha256"], first_contact_sha)
        self.assertEqual(source["second_capsule"]["first_contact_sha256"], first_contact_sha)
        self.assertEqual(
            source["update"]["contact_history_sha256s"][0],
            first_contact_sha,
        )

    def test_explicit_second_admission_required(self):
        first = first_fixture.make_source(observed_relation="corroborates")
        candidate = residual_candidate(first, "residual", 1, 0)
        transition = residual.select_transition(
            first["field"],
            first["field_receipt"],
            first["update"],
            first["contact_capsule"],
            [candidate],
        )
        reorientation = residual.make_reorientation(transition)
        with self.assertRaisesRegex(ValueError, "explicit local acceptance"):
            residual.make_admission(
                candidate,
                transition,
                reorientation,
                admitted_by="residual-local-authority",
                accept_proposal=False,
            )

    def test_second_observation_must_be_predeclared(self):
        source = make_residual()
        with self.assertRaisesRegex(ValueError, "does not match predeclared"):
            residual.perform_contact(
                source["admission"],
                source["selected"],
                source["orientation"],
                source["selected"]["target_challenged_relation"],
                "An observation invented after seeing the second result.",
                "A next heading",
            )

    def test_challenged_path_can_survive_second_contact(self):
        source = make_residual(second_relation="contradicts")
        update = source["update"]

        self.assertEqual(
            update["residual_tension_status"],
            "challenged_path_survives_second_contact",
        )
        self.assertEqual(
            set(update["historical_supported_relations"]),
            {"corroborates", "contradicts"},
        )
        self.assertEqual(len(update["contact_history_sha256s"]), 2)
        self.assertFalse(update["first_contact_promoted_to_verdict"])
        self.assertEqual(update["verdict_status"], "withheld")

    def test_challenged_path_can_be_challenged_again_without_erasure(self):
        source = make_residual(second_relation="corroborates")
        update = source["update"]

        self.assertEqual(
            update["residual_tension_status"],
            "challenged_path_challenged_again",
        )
        self.assertEqual(update["historical_supported_relations"], ["corroborates"])
        self.assertTrue(update["all_witnesses_retained"])
        self.assertEqual(
            update["witness_count_before"],
            update["witness_count_after"],
        )

        target = source["selected"]["target_challenged_relation"]
        target_states = [
            item for item in update["witness_history"]
            if item["original_relation"] == target
        ]
        self.assertTrue(target_states)
        for item in target_states:
            self.assertEqual(item["first_contact_state"], "challenged_by_contact")
            self.assertEqual(item["second_contact_state"], "challenged_by_contact")

    def test_second_contact_can_reverse_first_without_rewriting_it(self):
        source = make_residual(second_relation="contradicts")
        update = source["update"]

        self.assertEqual(
            source["first"]["update"]["observed_relation"],
            "corroborates",
        )
        self.assertEqual(update["second_observed_relation"], "contradicts")
        self.assertEqual(
            set(update["historical_supported_relations"]),
            {"corroborates", "contradicts"},
        )
        self.assertFalse(update["first_contact_promoted_to_verdict"])

    def test_original_field_and_first_update_remain_unchanged(self):
        source = make_residual()
        field_before = copy.deepcopy(source["first"]["field"])
        update_before = copy.deepcopy(source["first"]["update"])

        residual.update_history(
            source["first"]["field"],
            source["first"]["update"],
            source["first"]["contact_capsule"],
            source["selected"],
            source["admission"],
            source["orientation"],
            source["second_capsule"],
            source["second_contact"],
        )

        self.assertEqual(source["first"]["field"], field_before)
        self.assertEqual(source["first"]["update"], update_before)

    def test_witness_count_never_changes(self):
        source = make_residual(second_relation="contradicts")
        update = source["update"]
        self.assertEqual(
            update["witness_count_before"],
            len(source["first"]["field"]["witnesses"]),
        )
        self.assertEqual(update["witness_count_after"], update["witness_count_before"])
        self.assertTrue(update["all_witnesses_retained"])

    def test_majority_flip_does_not_change_residual_status_for_same_contacts(self):
        majority_first = make_residual(
            ("corroborates", "corroborates", "contradicts"),
            second_relation="contradicts",
        )
        minority_first = make_residual(
            ("corroborates", "contradicts", "contradicts"),
            second_relation="contradicts",
        )

        self.assertEqual(
            majority_first["update"]["residual_tension_status"],
            "challenged_path_survives_second_contact",
        )
        self.assertEqual(
            minority_first["update"]["residual_tension_status"],
            "challenged_path_survives_second_contact",
        )
        self.assertFalse(majority_first["update"]["majority_rule_used"])
        self.assertFalse(minority_first["update"]["majority_rule_used"])

    def test_first_contact_cannot_be_promoted_to_verdict(self):
        source = make_residual()
        bad = copy.deepcopy(source["update"])
        bad["first_contact_promoted_to_verdict"] = True
        with self.assertRaisesRegex(ValueError, "cannot be promoted to verdict"):
            residual.validate_update(bad)

    def test_residual_update_cannot_delete_witness(self):
        source = make_residual()
        bad = copy.deepcopy(source["update"])
        bad["witness_history"].pop()
        bad["witness_count_after"] -= 1
        with self.assertRaisesRegex(ValueError, "before count mismatch|deleted a witness"):
            residual.validate_update(bad)

    def test_contact_history_cannot_drop_first_contact(self):
        source = make_residual()
        bad = copy.deepcopy(source["update"])
        bad["contact_history_sha256s"] = [bad["contact_history_sha256s"][1]]
        with self.assertRaisesRegex(ValueError, "exactly two distinct contacts"):
            residual.validate_update(bad)

    def test_second_contact_mutation_breaks_history_chain(self):
        source = make_residual()
        bad_contact = copy.deepcopy(source["second_contact"])
        bad_contact["observed"] += " mutated"
        with self.assertRaisesRegex(ValueError, "second contact receipt mismatch"):
            residual.update_history(
                source["first"]["field"],
                source["first"]["update"],
                source["first"]["contact_capsule"],
                source["selected"],
                source["admission"],
                source["orientation"],
                source["second_capsule"],
                bad_contact,
            )

    def test_inspection_preserves_history_without_truth_claim(self):
        source = make_residual(second_relation="contradicts")
        inspection = residual.inspect(source["update"])
        self.assertEqual(inspection["contact_count"], 2)
        self.assertTrue(inspection["all_witnesses_retained"])
        self.assertFalse(inspection["first_contact_promoted_to_verdict"])
        self.assertFalse(inspection["majority_rule_used"])
        self.assertEqual(inspection["verdict_status"], "withheld")
        self.assertFalse(inspection["history_rewritten"])
        self.assertFalse(inspection["truth_claimed"])


if __name__ == "__main__":
    unittest.main()
