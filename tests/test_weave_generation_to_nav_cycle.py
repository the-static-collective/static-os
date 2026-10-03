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
    "static_os_weave_admission_fixture_for_cycle",
    "tests/test_weave_to_nav_admission.py",
)
weave_cycle = load_module(
    "static_os_weave_cycle",
    "scripts/weave_cycle.py",
)

NEXT_HEADING = (
    "Use the composed comparison to choose one bounded test that can distinguish "
    "external confirmation from environment-dependent reproduction."
)


def make_source():
    fixture, admission, generation = fixture_mod.make_admission_and_generation()
    origin = weave_cycle.make_origin(
        *fixture,
        admission,
        generation,
    )
    orientation = weave_cycle.start_cycle(
        origin,
        generation,
        preserve=[
            "typed parent provenance",
            "the still-open branch",
            "the distinction between continuation and open branch",
        ],
        aperture=[
            "one bounded result capable of disagreeing with the composed heading"
        ],
        bounded_move=(
            "Compare one external observation against one second-environment "
            "reproduction without widening the claim."
        ),
        stop_condition=(
            "Stop after one comparable result is captured or if either source "
            "cannot be preserved independently."
        ),
        claim_limit=(
            "Starting from composed history does not make the composition correct."
        ),
    )
    ledger = weave_cycle.contact_cycle(
        generation,
        origin,
        orientation,
        observed=(
            "The fresh NAV cycle produced a new bounded comparison result from the "
            "admitted composed heading."
        ),
        delta=(
            "Composed history functioned as a usable starting orientation while its "
            "typed parents remained outside the local NAV receipt."
        ),
        next_heading=NEXT_HEADING,
    )
    return fixture, admission, generation, origin, orientation, ledger


class WeaveGenerationToNavCycleTests(unittest.TestCase):
    def test_composed_generation_becomes_fresh_nav_origin(self):
        fixture, _, generation, origin, orientation, ledger = make_source()
        result = weave_cycle.verify_cycle_ledger(ledger)

        self.assertEqual(result["status"], "complete")
        self.assertEqual(
            result["from_heading"],
            generation["admitted_heading"],
        )
        self.assertEqual(
            orientation["heading"],
            fixture[5]["proposed_heading"],
        )
        self.assertEqual(result["next_heading"], NEXT_HEADING)

    def test_ordinary_nav_receipt_stays_ordinary(self):
        _, _, _, _, orientation, ledger = make_source()
        contact = next(iter(ledger["contacts"].values()))

        for receipt in (orientation, contact):
            self.assertEqual(receipt["schema"], "static.nav-receipt/v0")
            self.assertNotIn("parent_set_sha256", receipt)
            self.assertNotIn("weave_ledger_sha256", receipt)
            self.assertNotIn("relation_kinds", receipt)
            self.assertNotIn("parents", receipt)

    def test_cycle_capsule_is_bounded_and_addressable(self):
        _, _, _, _, _, ledger = make_source()
        cycle = next(iter(ledger["cycles"].values()))

        self.assertEqual(set(cycle), weave_cycle.CYCLE_KEYS)
        self.assertEqual(cycle["provenance_mode"], "addressable")
        self.assertEqual(
            set(cycle["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        for forbidden in (
            "generation",
            "origin",
            "orientation",
            "contact",
            "parents",
            "parent_set",
            "weave",
            "history",
        ):
            self.assertNotIn(forbidden, cycle)

    def test_source_generation_is_stored_once(self):
        _, _, generation, _, _, ledger = make_source()
        digest = weave_cycle.canonical_digest(generation)
        self.assertEqual(set(ledger["generations"]), {digest})
        self.assertEqual(
            ledger["source_generation_sha256"],
            digest,
        )

    def test_missing_generation_is_incomplete(self):
        _, _, _, _, _, ledger = make_source()
        ledger["generations"].clear()

        result = weave_cycle.verify_cycle_ledger(ledger)
        self.assertEqual(result["status"], "incomplete")
        self.assertEqual(result["reason"], "missing_generation")

    def test_mutated_generation_is_invalid(self):
        _, _, _, _, _, ledger = make_source()
        digest = ledger["source_generation_sha256"]
        ledger["generations"][digest]["admitted_heading"] += " mutated"

        result = weave_cycle.verify_cycle_ledger(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "generation_digest_mismatch")

    def test_origin_cannot_rewrite_admitted_heading(self):
        _, _, generation, origin, _, _ = make_source()
        bad = copy.deepcopy(origin)
        bad["admitted_heading"] = "A different composed origin"

        with self.assertRaisesRegex(ValueError, "heading differs"):
            weave_cycle.verify_origin_against_generation(bad, generation)

    def test_fresh_cycle_cannot_start_from_another_heading(self):
        _, _, generation, origin, orientation, _ = make_source()
        bad = copy.deepcopy(orientation)
        bad["heading"] = "Not the admitted composed heading"

        with self.assertRaisesRegex(ValueError, "does not begin"):
            weave_cycle.contact_cycle(
                generation,
                origin,
                bad,
                observed="A result",
                delta="A delta",
                next_heading="A next heading",
            )

    def test_cycle_cannot_drop_typed_relation_kind(self):
        _, _, _, _, _, ledger = make_source()
        cycle_digest = ledger["cycle_sha256"]
        cycle = ledger["cycles"].pop(cycle_digest)
        cycle["relation_kinds"] = ["branch_continuation"]
        new_digest = weave_cycle.canonical_digest(cycle)
        ledger["cycles"][new_digest] = cycle
        ledger["cycle_sha256"] = new_digest

        result = weave_cycle.verify_cycle_ledger(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertIn("relation_kinds", result["reason"])

    def test_origin_provenance_addresses_match_generation(self):
        _, _, generation, origin, _, _ = make_source()
        for key in (
            "admission_sha256",
            "weave_capsule_sha256",
            "parent_set_sha256",
            "weave_ledger_sha256",
            "root_cycle_digest",
        ):
            self.assertEqual(origin[key], generation[key])

    def test_inspection_marks_composed_history_as_new_ground(self):
        _, _, _, _, _, ledger = make_source()
        inspection = weave_cycle.inspect(ledger)

        self.assertTrue(inspection["composed_history_is_new_ground"])
        self.assertTrue(inspection["typed_provenance_preserved"])
        self.assertFalse(inspection["open_branch_closed"])
        self.assertFalse(inspection["automatic_authority_claimed"])
        self.assertFalse(inspection["generation_embedded_in_cycle"])
        self.assertFalse(inspection["typed_parents_embedded_in_cycle"])

    def test_contact_mutation_is_detected(self):
        _, _, _, _, _, ledger = make_source()
        cycle = next(iter(ledger["cycles"].values()))
        digest = cycle["contact_sha256"]
        ledger["contacts"][digest]["observed"] += " mutated"

        result = weave_cycle.verify_cycle_ledger(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "contact_digest_mismatch")

    def test_undeclared_cycle_material_is_invalid(self):
        _, _, _, _, _, ledger = make_source()
        fake = copy.deepcopy(next(iter(ledger["cycles"].values())))
        fake["cycle_id"] = "hidden-cycle"
        ledger["cycles"][weave_cycle.canonical_digest(fake)] = fake

        result = weave_cycle.verify_cycle_ledger(ledger)
        self.assertEqual(result["status"], "invalid")
        self.assertEqual(result["reason"], "undeclared_cycle_present")


if __name__ == "__main__":
    unittest.main()
