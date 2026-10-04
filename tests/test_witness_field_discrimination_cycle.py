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


nav_fixture = load_module(
    "static_os_witness_field_to_nav_fixture_for_cycle",
    "tests/test_witness_field_to_nav.py",
)
field_nav = load_module(
    "static_os_field_dogram_nav_for_cycle_test",
    "scripts/field_dogram_nav.py",
)
cycle = load_module(
    "static_os_field_discrimination_cycle_test",
    "scripts/field_discrimination_cycle.py",
)


def make_source(relations=("corroborates", "corroborates", "contradicts"), observed_relation="corroborates"):
    _, _, witness_field, field_receipt = nav_fixture.make_field(relations)
    field_digest = cycle.canonical_digest(witness_field)
    candidates = nav_fixture.make_candidates(field_digest)
    transition = field_nav.select_transition(
        witness_field,
        field_receipt,
        candidates,
    )
    selected = next(
        item
        for item in candidates
        if cycle.canonical_digest(item) == transition["candidate_sha256"]
    )
    reorientation = field_nav.make_nav_reorientation(transition)
    admission = cycle.make_admission(
        witness_field,
        field_receipt,
        selected,
        transition,
        reorientation,
        admitted_by="field-cycle-local-authority",
        accept_proposal=True,
    )
    orientation = cycle.start_orientation(admission, selected)
    observation = next(
        path["discriminating_observation"]
        for path in selected["paths"]
        if path["relation"] == observed_relation
    )
    contact_capsule, contact = cycle.perform_contact(
        admission,
        selected,
        orientation,
        observed_relation,
        observation,
        (
            "Preserve every witness and test whether the residual challenged path "
            "survives one more bounded contact."
        ),
    )
    update = cycle.update_field(
        witness_field,
        field_receipt,
        selected,
        admission,
        orientation,
        contact_capsule,
        contact,
    )
    return {
        "field": witness_field,
        "field_receipt": field_receipt,
        "candidates": candidates,
        "selected": selected,
        "transition": transition,
        "reorientation": reorientation,
        "admission": admission,
        "orientation": orientation,
        "contact_capsule": contact_capsule,
        "contact": contact,
        "update": update,
    }


class WitnessFieldDiscriminationCycleTests(unittest.TestCase):
    def test_explicit_acceptance_is_required(self):
        _, _, witness_field, field_receipt = nav_fixture.make_field()
        digest = cycle.canonical_digest(witness_field)
        candidates = nav_fixture.make_candidates(digest)
        transition = field_nav.select_transition(witness_field, field_receipt, candidates)
        selected = next(
            item for item in candidates
            if cycle.canonical_digest(item) == transition["candidate_sha256"]
        )
        reorientation = field_nav.make_nav_reorientation(transition)

        with self.assertRaisesRegex(ValueError, "explicit local acceptance"):
            cycle.make_admission(
                witness_field,
                field_receipt,
                selected,
                transition,
                reorientation,
                admitted_by="field-cycle-local-authority",
                accept_proposal=False,
            )

    def test_admission_exactly_binds_selected_proposal(self):
        source = make_source()
        admission = source["admission"]

        self.assertEqual(admission["status"], "admitted")
        self.assertEqual(
            admission["heading"],
            source["selected"]["proposed_heading"],
        )
        self.assertEqual(
            admission["candidate_sha256"],
            cycle.canonical_digest(source["selected"]),
        )
        self.assertEqual(
            admission["transition_sha256"],
            cycle.canonical_digest(source["transition"]),
        )
        self.assertEqual(
            admission["reorientation_sha256"],
            cycle.canonical_digest(source["reorientation"]),
        )

    def test_execution_uses_ordinary_nav_receipts(self):
        source = make_source()

        self.assertEqual(source["orientation"]["schema"], "static.nav-receipt/v0")
        self.assertEqual(source["orientation"]["status"], "oriented")
        self.assertEqual(source["contact"]["schema"], "static.nav-receipt/v0")
        self.assertEqual(source["contact"]["status"], "contacted")
        self.assertEqual(
            source["orientation"]["bounded_move"],
            source["selected"]["bounded_move"],
        )

    def test_contact_must_match_predeclared_observation(self):
        source = make_source()
        with self.assertRaisesRegex(ValueError, "does not match predeclared"):
            cycle.perform_contact(
                source["admission"],
                source["selected"],
                source["orientation"],
                "corroborates",
                "A convenient observation invented after contact.",
                "A next heading",
            )

    def test_contact_cannot_claim_undeclared_relation(self):
        source = make_source()
        with self.assertRaisesRegex(ValueError, "observed relation invalid"):
            cycle.perform_contact(
                source["admission"],
                source["selected"],
                source["orientation"],
                "unrelated",
                "Something unrelated.",
                "A next heading",
            )

    def test_field_ambiguity_reduces_without_witness_deletion(self):
        source = make_source()
        update = source["update"]

        self.assertEqual(update["ambiguity_before"], 2)
        self.assertEqual(update["ambiguity_after"], 1)
        self.assertEqual(
            update["witness_count_before"],
            update["witness_count_after"],
        )
        self.assertEqual(
            update["witness_count_after"],
            len(source["field"]["witnesses"]),
        )
        self.assertTrue(update["all_witnesses_retained"])

    def test_challenged_witnesses_remain_addressable(self):
        source = make_source()
        original_sources = {
            item["source_sha256"] for item in source["field"]["witnesses"]
        }
        returned_sources = {
            item["source_sha256"] for item in source["update"]["witness_states"]
        }
        self.assertEqual(original_sources, returned_sources)

        challenged = [
            item for item in source["update"]["witness_states"]
            if item["contact_state"] == "challenged_by_contact"
        ]
        self.assertTrue(challenged)
        for item in challenged:
            self.assertIn(item["source_sha256"], original_sources)

    def test_alignment_is_relation_based_not_count_based(self):
        majority_corrob = make_source(
            ("corroborates", "corroborates", "contradicts"),
            observed_relation="contradicts",
        )
        majority_contra = make_source(
            ("corroborates", "contradicts", "contradicts"),
            observed_relation="contradicts",
        )

        self.assertEqual(
            majority_corrob["update"]["contact_supported_relations"],
            ["contradicts"],
        )
        self.assertEqual(
            majority_contra["update"]["contact_supported_relations"],
            ["contradicts"],
        )
        self.assertEqual(majority_corrob["update"]["ambiguity_after"], 1)
        self.assertEqual(majority_contra["update"]["ambiguity_after"], 1)
        self.assertFalse(majority_corrob["update"]["majority_rule_used"])
        self.assertFalse(majority_contra["update"]["majority_rule_used"])

    def test_original_field_is_not_rewritten(self):
        source = make_source()
        field_snapshot = copy.deepcopy(source["field"])
        receipt_snapshot = copy.deepcopy(source["field_receipt"])

        cycle.update_field(
            source["field"],
            source["field_receipt"],
            source["selected"],
            source["admission"],
            source["orientation"],
            source["contact_capsule"],
            source["contact"],
        )

        self.assertEqual(source["field"], field_snapshot)
        self.assertEqual(source["field_receipt"], receipt_snapshot)

    def test_update_cannot_delete_a_witness(self):
        source = make_source()
        bad = copy.deepcopy(source["update"])
        bad["witness_states"].pop()
        bad["witness_count_after"] -= 1

        with self.assertRaisesRegex(ValueError, "before count mismatch|deleted a witness"):
            cycle.validate_update(bad)

    def test_update_cannot_turn_challenge_into_verdict(self):
        source = make_source()
        bad = copy.deepcopy(source["update"])
        bad["verdict_status"] = "corroborated"

        with self.assertRaisesRegex(ValueError, "verdict must remain withheld"):
            cycle.validate_update(bad)

    def test_update_cannot_enable_majority_rule(self):
        source = make_source()
        bad = copy.deepcopy(source["update"])
        bad["majority_rule_used"] = True

        with self.assertRaisesRegex(ValueError, "cannot use majority rule"):
            cycle.validate_update(bad)

    def test_contact_mutation_breaks_return_chain(self):
        source = make_source()
        bad_contact = copy.deepcopy(source["contact"])
        bad_contact["observed"] += " mutated"

        with self.assertRaisesRegex(ValueError, "contact receipt mismatch"):
            cycle.update_field(
                source["field"],
                source["field_receipt"],
                source["selected"],
                source["admission"],
                source["orientation"],
                source["contact_capsule"],
                bad_contact,
            )

    def test_challenged_does_not_mean_false(self):
        source = make_source()
        limits = " ".join(source["update"]["does_not_establish"]).lower()
        self.assertIn("challenged witnesses are false", limits)
        self.assertIn("deleted from history", limits)
        self.assertIn("final verdict", limits)

    def test_inspection_reports_reduced_ambiguity_and_zero_deletion(self):
        source = make_source()
        inspection = cycle.inspect(source["update"])

        self.assertTrue(inspection["ambiguity_reduced"])
        self.assertEqual(inspection["ambiguity_before"], 2)
        self.assertEqual(inspection["ambiguity_after"], 1)
        self.assertTrue(inspection["all_witnesses_retained"])
        self.assertFalse(inspection["witness_deletion_used"])
        self.assertFalse(inspection["majority_rule_used"])
        self.assertEqual(inspection["verdict_status"], "withheld")
        self.assertFalse(inspection["truth_claimed"])


if __name__ == "__main__":
    unittest.main()
