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


cycle_fixture = load_module(
    "static_os_composed_cycle_fixture_for_witness",
    "tests/test_weave_generation_to_nav_cycle.py",
)
witness = load_module(
    "static_os_witness_for_composed_contact_test",
    "scripts/witness.py",
)
witness_composed = load_module(
    "static_os_witness_composed_test",
    "scripts/witness_composed.py",
)
weave_cycle = load_module(
    "static_os_weave_cycle_for_composed_witness_test",
    "scripts/weave_cycle.py",
)


class ComposedNavContactToWitnessTests(unittest.TestCase):
    def make_source(self):
        fixture, admission, generation, origin, orientation, ledger = (
            cycle_fixture.make_source()
        )
        composed = witness_composed.intake_cycle(copy.deepcopy(ledger))
        return (
            fixture,
            admission,
            generation,
            origin,
            orientation,
            ledger,
            composed,
        )

    def test_fresh_contact_enters_witness_as_ordinary_source(self):
        _, _, _, _, _, ledger, composed = self.make_source()
        cycle = ledger["cycles"][ledger["cycle_sha256"]]
        contact = ledger["contacts"][cycle["contact_sha256"]]
        ordinary = witness.intake_nav(contact)

        self.assertEqual(composed["source"]["sha256"], cycle["contact_sha256"])
        self.assertEqual(
            composed["source"]["intake_sha256"],
            witness_composed.canonical_digest(ordinary),
        )
        self.assertEqual(composed["records"], ordinary["records"])

    def test_ordinary_claim_classes_survive_exactly(self):
        *_, composed = self.make_source()
        self.assertEqual(
            [record["claim_class"] for record in composed["records"]],
            [
                "source_record",
                "derivative_interpretation",
                "orientation_proposal",
                "source_limit",
            ],
        )

    def test_origin_provenance_survives_as_sidecar(self):
        _, _, generation, origin, _, ledger, composed = self.make_source()
        provenance = composed["origin_provenance"]

        self.assertEqual(provenance["cycle_sha256"], ledger["cycle_sha256"])
        self.assertEqual(provenance["origin_sha256"], ledger["origin_sha256"])
        self.assertEqual(
            provenance["source_generation_sha256"],
            ledger["source_generation_sha256"],
        )
        self.assertEqual(
            provenance["admission_sha256"],
            generation["admission_sha256"],
        )
        self.assertEqual(
            provenance["weave_capsule_sha256"],
            generation["weave_capsule_sha256"],
        )
        self.assertEqual(
            provenance["parent_set_sha256"],
            generation["parent_set_sha256"],
        )
        self.assertEqual(
            provenance["weave_ledger_sha256"],
            generation["weave_ledger_sha256"],
        )
        self.assertEqual(
            provenance["root_cycle_digest"],
            generation["root_cycle_digest"],
        )
        self.assertEqual(
            set(provenance["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        self.assertEqual(
            set(origin["relation_kinds"]),
            set(provenance["relation_kinds"]),
        )

    def test_origin_is_not_embedded_in_observation_text(self):
        _, _, _, _, _, _, composed = self.make_source()
        observation = composed["records"][0]["value"]
        provenance = composed["origin_provenance"]

        for digest in provenance.values():
            if isinstance(digest, str) and len(digest) == 64:
                self.assertNotIn(digest, observation)
        self.assertNotIn("branch_continuation", observation)
        self.assertNotIn("open_branch", observation)

    def test_fresh_source_hash_is_distinct_from_generation_hash(self):
        _, _, _, _, _, _, composed = self.make_source()
        self.assertNotEqual(
            composed["source"]["sha256"],
            composed["origin_provenance"]["source_generation_sha256"],
        )

    def test_incomplete_cycle_is_refused_before_witness(self):
        _, _, _, _, _, ledger, _ = self.make_source()
        bad = copy.deepcopy(ledger)
        bad["origins"].clear()

        with self.assertRaisesRegex(ValueError, "not complete: missing_origin"):
            witness_composed.intake_cycle(bad)

    def test_mutated_contact_is_refused_before_witness(self):
        _, _, _, _, _, ledger, _ = self.make_source()
        bad = copy.deepcopy(ledger)
        cycle = bad["cycles"][bad["cycle_sha256"]]
        digest = cycle["contact_sha256"]
        bad["contacts"][digest]["observed"] += " mutated"

        with self.assertRaisesRegex(ValueError, "not complete: contact_digest_mismatch"):
            witness_composed.intake_cycle(bad)

    def test_origin_generation_mismatch_is_refused(self):
        _, _, _, _, _, ledger, _ = self.make_source()
        bad = copy.deepcopy(ledger)
        origin_digest = bad["origin_sha256"]
        origin = bad["origins"].pop(origin_digest)
        origin["source_generation_sha256"] = "9" * 64
        new_origin_digest = weave_cycle.canonical_digest(origin)
        bad["origins"][new_origin_digest] = origin
        bad["origin_sha256"] = new_origin_digest
        cycle = bad["cycles"].pop(bad["cycle_sha256"])
        cycle["origin_sha256"] = new_origin_digest
        new_cycle_digest = weave_cycle.canonical_digest(cycle)
        bad["cycles"][new_cycle_digest] = cycle
        bad["cycle_sha256"] = new_cycle_digest

        with self.assertRaisesRegex(ValueError, "not complete: origin_generation_digest_mismatch"):
            witness_composed.intake_cycle(bad)

    def test_witness_does_not_claim_independent_verification(self):
        *_, composed = self.make_source()
        inspection = witness_composed.inspect(composed)

        self.assertFalse(inspection["independent_verification_claimed"])
        self.assertTrue(inspection["typed_provenance_preserved"])
        self.assertTrue(inspection["ordinary_claim_classes_preserved"])
        self.assertFalse(inspection["open_branch_closed"])
        self.assertFalse(inspection["origin_embedded_in_observation"])

    def test_does_not_establish_keeps_orientation_separate_from_contact(self):
        *_, composed = self.make_source()
        limits = " ".join(composed["does_not_establish"]).lower()
        self.assertIn("independently verifies the composed history", limits)
        self.assertIn("still-open branch", limits)
        self.assertIn("delta or next-heading proposal is correct", limits)

    def test_next_door_requires_world_to_distinguish_contact_from_history(self):
        *_, composed = self.make_source()
        self.assertIn("WORLD", composed["next_door"])
        self.assertIn("distinguish", composed["next_door"])
        self.assertIn("history that oriented the move", composed["next_door"])

    def test_sidecar_mutation_breaks_validation(self):
        *_, composed = self.make_source()
        bad = copy.deepcopy(composed)
        bad["origin_provenance"]["relation_kinds"] = ["branch_continuation"]

        with self.assertRaisesRegex(ValueError, "relation kinds invalid"):
            witness_composed.validate_composed_intake(bad)


if __name__ == "__main__":
    unittest.main()
