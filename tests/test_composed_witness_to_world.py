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
    "static_os_composed_cycle_fixture_for_world",
    "tests/test_weave_generation_to_nav_cycle.py",
)
witness_composed = load_module(
    "static_os_witness_composed_for_world_test",
    "scripts/witness_composed.py",
)
world_composed = load_module(
    "static_os_world_composed_test",
    "scripts/world_composed.py",
)


def make_source():
    fixture, admission, generation, origin, orientation, ledger = (
        cycle_fixture.make_source()
    )
    witness_intake = witness_composed.intake_cycle(copy.deepcopy(ledger))
    candidate = world_composed.candidate_from_witness(
        copy.deepcopy(witness_intake)
    )
    receipt = world_composed.classify(copy.deepcopy(candidate))
    return (
        fixture,
        admission,
        generation,
        origin,
        orientation,
        ledger,
        witness_intake,
        candidate,
        receipt,
    )


class ComposedWitnessToWorldTests(unittest.TestCase):
    def test_fresh_contact_is_new_but_not_independent_confirmation(self):
        *_, candidate, receipt = make_source()

        self.assertEqual(candidate["novelty_status"], "new_source_artifact")
        self.assertEqual(candidate["observation_status"], "fresh_world_contact")
        self.assertEqual(
            candidate["selection_independence"],
            "not_independent_of_orientation",
        )
        self.assertEqual(candidate["measurement_independence"], "unknown")
        self.assertEqual(
            candidate["confirmation_status"],
            "independent_confirmation_not_established",
        )

        self.assertEqual(receipt["lineage_class"], "oriented_downstream")
        self.assertFalse(receipt["counts_as_independent_confirmation"])

    def test_world_preserves_typed_orientation_ancestry(self):
        (
            _,
            _,
            generation,
            _,
            _,
            ledger,
            witness_intake,
            candidate,
            receipt,
        ) = make_source()
        ancestry = candidate["orientation_ancestry"]
        provenance = witness_intake["origin_provenance"]

        self.assertEqual(ancestry, provenance)
        self.assertEqual(
            ancestry["source_generation_sha256"],
            ledger["source_generation_sha256"],
        )
        self.assertEqual(
            ancestry["parent_set_sha256"],
            generation["parent_set_sha256"],
        )
        self.assertEqual(
            set(ancestry["relation_kinds"]),
            {"branch_continuation", "open_branch"},
        )
        self.assertTrue(receipt["typed_origin_preserved"])

    def test_fresh_source_is_distinct_from_orienting_generation(self):
        *_, witness_intake, candidate, _ = make_source()

        self.assertEqual(
            candidate["source_sha256"],
            witness_intake["source"]["sha256"],
        )
        self.assertNotEqual(
            candidate["source_sha256"],
            candidate["orientation_ancestry"]["source_generation_sha256"],
        )

    def test_freshness_does_not_upgrade_measurement_independence(self):
        *_, candidate, _ = make_source()
        bad = copy.deepcopy(candidate)
        bad["measurement_independence"] = "independent_candidate"
        bad["confirmation_status"] = "independent_confirmation_candidate"

        with self.assertRaisesRegex(
            ValueError,
            "measurement independence cannot be inferred",
        ):
            world_composed.validate_candidate(bad)

    def test_selection_independence_cannot_be_claimed(self):
        *_, candidate, _ = make_source()
        bad = copy.deepcopy(candidate)
        bad["selection_independence"] = "independent"

        with self.assertRaisesRegex(
            ValueError,
            "selection independence drifted",
        ):
            world_composed.validate_candidate(bad)

    def test_relation_kind_collapse_is_refused(self):
        *_, candidate, _ = make_source()
        bad = copy.deepcopy(candidate)
        bad["orientation_ancestry"]["relation_kinds"] = ["branch_continuation"]

        with self.assertRaisesRegex(ValueError, "relation kinds invalid"):
            world_composed.validate_candidate(bad)

    def test_unknown_measurement_independence_does_not_count_as_confirmation(self):
        *_, _, receipt = make_source()
        self.assertEqual(receipt["measurement_independence"], "unknown")
        self.assertEqual(
            receipt["confirmation_status"],
            "independent_confirmation_not_established",
        )
        self.assertFalse(receipt["counts_as_independent_confirmation"])

    def test_world_claim_limits_are_explicit(self):
        *_, _, receipt = make_source()
        limits = " ".join(receipt["does_not_establish"]).lower()

        self.assertIn("fresh contact is an independent confirmation", limits)
        self.assertIn("new source hash proves epistemic independence", limits)
        self.assertIn("unknown measurement independence", limits)
        self.assertIn("still-open branch is closed", limits)

    def test_inspection_keeps_axes_separate(self):
        *_, _, receipt = make_source()
        inspection = world_composed.inspect(receipt)

        self.assertEqual(
            inspection["novelty_axis"],
            "new_source_artifact",
        )
        self.assertEqual(
            inspection["observation_axis"],
            "fresh_world_contact",
        )
        self.assertEqual(
            inspection["selection_independence"],
            "not_independent_of_orientation",
        )
        self.assertEqual(
            inspection["measurement_independence"],
            "unknown",
        )
        self.assertFalse(
            inspection["counts_as_independent_confirmation"]
        )
        self.assertFalse(
            inspection["freshness_collapsed_into_independence"]
        )
        self.assertFalse(inspection["truth_claimed"])

    def test_mutated_witness_sidecar_is_refused_before_world(self):
        *_, witness_intake, _, _ = make_source()
        bad = copy.deepcopy(witness_intake)
        bad["origin_provenance"]["relation_kinds"] = ["open_branch"]

        with self.assertRaisesRegex(ValueError, "relation kinds invalid"):
            world_composed.candidate_from_witness(bad)

    def test_next_door_requires_separate_independence_audit(self):
        *_, _, receipt = make_source()
        next_door = receipt["next_door"].lower()

        self.assertIn("audit the measurement path separately", next_door)
        self.assertIn("selection and measurement path", next_door)

    def test_world_does_not_rewrite_witness_source_records(self):
        *_, witness_intake, candidate, _ = make_source()

        observation = witness_intake["records"][0]["value"]
        self.assertNotIn(
            candidate["orientation_ancestry"]["source_generation_sha256"],
            observation,
        )
        self.assertNotIn("branch_continuation", observation)
        self.assertNotIn("open_branch", observation)


if __name__ == "__main__":
    unittest.main()
