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


field_fixture = load_module(
    "static_os_external_witness_field_fixture_for_nav",
    "tests/test_external_witness_field.py",
)
field_nav = load_module(
    "static_os_field_dogram_nav_test",
    "scripts/field_dogram_nav.py",
)


def make_field(relations=("corroborates", "corroborates", "contradicts")):
    _, receipts, pairs, witness_field, receipt = field_fixture.make_three(relations)
    return receipts, pairs, witness_field, receipt


def candidate(field_sha, candidate_id, changed_variables, external_dependencies, heading):
    return {
        "schema": "static.field-discriminator-candidate/v0",
        "candidate_id": candidate_id,
        "field_sha256": field_sha,
        "proposed_heading": heading,
        "bounded_move": (
            "Run one blinded replay under a single changed condition and record the "
            "observable that differs between the live witness relation paths."
        ),
        "paths": [
            {
                "relation": "corroborates",
                "discriminating_observation": "The target condition reproduces under the blinded replay.",
            },
            {
                "relation": "contradicts",
                "discriminating_observation": "The target condition fails to reproduce under the blinded replay.",
            },
        ],
        "preserve": [
            "all witness source receipts",
            "pairwise independence audits",
            "claim relation without verdict",
        ],
        "aperture": [
            "one result capable of disagreeing with either live witness path",
        ],
        "stop_condition": "Stop after the one blinded replay is captured.",
        "cost_vector": {
            "irreversible_steps": 0,
            "changed_variables": changed_variables,
            "world_contacts": 1,
            "external_dependencies": external_dependencies,
        },
        "claim_limit": (
            "This candidate declares a structural discriminator. It does not prove "
            "the proposed contact will discriminate the witness claims in reality."
        ),
    }


def make_candidates(field_sha):
    return [
        candidate(
            field_sha,
            "larger-discriminator",
            2,
            0,
            "Change two conditions in one reversible contact.",
        ),
        candidate(
            field_sha,
            "smallest-discriminator",
            1,
            0,
            "Change one condition in one reversible contact and capture the split.",
        ),
        candidate(
            field_sha,
            "dependency-heavy-discriminator",
            1,
            2,
            "Change one condition using two additional external dependencies.",
        ),
    ]


class WitnessFieldToNavTests(unittest.TestCase):
    def test_smallest_structural_candidate_is_selected(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        candidates = make_candidates(digest)

        transition = field_nav.select_transition(
            witness_field,
            receipt,
            candidates,
        )

        selected = next(
            item for item in candidates
            if field_nav.canonical_digest(item) == transition["candidate_sha256"]
        )
        self.assertEqual(selected["candidate_id"], "smallest-discriminator")
        self.assertEqual(transition["cost_vector"]["changed_variables"], 1)
        self.assertEqual(transition["cost_vector"]["external_dependencies"], 0)
        self.assertEqual(
            transition["selection_basis"],
            "minimum_declared_structural_cost",
        )

    def test_candidate_order_does_not_change_selection(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        candidates = make_candidates(digest)

        first = field_nav.select_transition(witness_field, receipt, candidates)
        second = field_nav.select_transition(
            witness_field,
            receipt,
            list(reversed(candidates)),
        )
        self.assertEqual(first["candidate_sha256"], second["candidate_sha256"])
        self.assertEqual(first["to_heading"], second["to_heading"])

    def test_majority_flip_does_not_change_structural_choice(self):
        _, _, field_a, receipt_a = make_field(
            ("corroborates", "corroborates", "contradicts")
        )
        _, _, field_b, receipt_b = make_field(
            ("corroborates", "contradicts", "contradicts")
        )

        candidates_a = make_candidates(field_nav.canonical_digest(field_a))
        candidates_b = make_candidates(field_nav.canonical_digest(field_b))

        transition_a = field_nav.select_transition(field_a, receipt_a, candidates_a)
        transition_b = field_nav.select_transition(field_b, receipt_b, candidates_b)

        selected_a = next(
            item for item in candidates_a
            if field_nav.canonical_digest(item) == transition_a["candidate_sha256"]
        )
        selected_b = next(
            item for item in candidates_b
            if field_nav.canonical_digest(item) == transition_b["candidate_sha256"]
        )

        self.assertEqual(selected_a["candidate_id"], "smallest-discriminator")
        self.assertEqual(selected_b["candidate_id"], "smallest-discriminator")
        self.assertEqual(
            transition_a["selection_basis"],
            transition_b["selection_basis"],
        )
        self.assertEqual(
            set(transition_a["live_relations"]),
            {"corroborates", "contradicts"},
        )
        self.assertEqual(
            set(transition_b["live_relations"]),
            {"corroborates", "contradicts"},
        )

    def test_candidate_must_cover_every_live_relevant_relation(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        bad = candidate(
            digest,
            "one-sided",
            1,
            0,
            "Only test the corroborating path.",
        )
        bad["paths"] = bad["paths"][:1]

        with self.assertRaisesRegex(ValueError, "at least two relation paths"):
            field_nav.select_transition(witness_field, receipt, [bad])

    def test_duplicate_observation_does_not_discriminate(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        bad = candidate(
            digest,
            "fake-discriminator",
            1,
            0,
            "Pretend one observation distinguishes both paths.",
        )
        bad["paths"][1]["discriminating_observation"] = (
            bad["paths"][0]["discriminating_observation"]
        )

        with self.assertRaisesRegex(ValueError, "do not distinguish paths"):
            field_nav.select_transition(witness_field, receipt, [bad])

    def test_convergence_is_not_sent_to_disagreement_discriminator(self):
        _, _, witness_field, receipt = make_field(
            ("corroborates", "corroborates", "corroborates")
        )
        digest = field_nav.canonical_digest(witness_field)

        with self.assertRaisesRegex(ValueError, "requires unresolved independent disagreement"):
            field_nav.select_transition(
                witness_field,
                receipt,
                make_candidates(digest),
            )

    def test_unresolved_pairwise_independence_is_refused(self):
        candidate_base, receipts, pairs, witness_field, _ = field_fixture.make_three()
        bad_pairs = copy.deepcopy(pairs)
        bad_pairs[0]["criteria"]["shared_source_ancestry"]["status"] = "unknown"
        unresolved_field = field_fixture.field.build_field(
            candidate_base["source_sha256"],
            receipts,
            bad_pairs,
        )
        unresolved_receipt = field_fixture.field.classify(
            unresolved_field,
            receipts,
            bad_pairs,
        )
        digest = field_nav.canonical_digest(unresolved_field)

        with self.assertRaisesRegex(ValueError, "independently qualified witness plurality"):
            field_nav.select_transition(
                unresolved_field,
                unresolved_receipt,
                make_candidates(digest),
            )

    def test_candidate_cannot_smuggle_majority_weight(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        bad = candidate(
            digest,
            "weighted",
            1,
            0,
            "Use a weighted majority move.",
        )
        bad["majority_weight"] = 2

        with self.assertRaisesRegex(ValueError, "shape drifted"):
            field_nav.select_transition(witness_field, receipt, [bad])

    def test_transition_preserves_no_verdict_laws(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        transition = field_nav.select_transition(
            witness_field,
            receipt,
            make_candidates(digest),
        )

        self.assertEqual(transition["status"], "proposed")
        self.assertIn("majority rule remains unused", transition["preserved"])
        self.assertIn("WORLD verdict remains withheld", transition["preserved"])
        inspection = field_nav.inspect(transition)
        self.assertFalse(inspection["majority_rule_used"])
        self.assertFalse(inspection["verdict_claimed"])
        self.assertFalse(inspection["authority_claimed"])

    def test_nav_reorientation_is_proposal_only(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        transition = field_nav.select_transition(
            witness_field,
            receipt,
            make_candidates(digest),
        )
        nav = field_nav.make_nav_reorientation(transition)

        self.assertEqual(nav["schema"], "static.nav-field-reorientation/v0")
        self.assertEqual(nav["packet_id"], "nav-001")
        self.assertEqual(nav["status"], "proposed")
        self.assertEqual(nav["field_sha256"], receipt["field_sha256"])
        self.assertEqual(nav["proposed_heading"], transition["to_heading"])
        self.assertEqual(
            nav["transition_sha256"],
            field_nav.canonical_digest(transition),
        )

        inspection = field_nav.inspect(nav)
        self.assertFalse(inspection["majority_rule_used"])
        self.assertFalse(inspection["verdict_claimed"])
        self.assertFalse(inspection["heading_admitted"])

    def test_candidate_must_address_exact_field(self):
        _, _, witness_field, receipt = make_field()
        candidates = make_candidates("f" * 64)
        with self.assertRaisesRegex(ValueError, "addresses another field"):
            field_nav.select_transition(witness_field, receipt, candidates)

    def test_irreversible_candidate_is_refused(self):
        _, _, witness_field, receipt = make_field()
        digest = field_nav.canonical_digest(witness_field)
        bad = candidate(
            digest,
            "irreversible",
            1,
            0,
            "Irreversible contact.",
        )
        bad["cost_vector"]["irreversible_steps"] = 1
        with self.assertRaisesRegex(ValueError, "must remain reversible"):
            field_nav.select_transition(witness_field, receipt, [bad])


if __name__ == "__main__":
    unittest.main()
