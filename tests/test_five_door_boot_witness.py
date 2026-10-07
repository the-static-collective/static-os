import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-five-door-boot-witness.py"
SPEC = importlib.util.spec_from_file_location("validate_fdbw001", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
CONTRACT = MODULE.load(ROOT / "manifest" / "five-door-boot-witness-001.json")
SESSION = MODULE.load(ROOT / "fixtures" / "five-door-boot-witness-001" / "session.json")


class FiveDoorBootWitnessTests(unittest.TestCase):
    def validate(self, contract=None, session=None):
        return MODULE.validate(
            copy.deepcopy(CONTRACT if contract is None else contract),
            copy.deepcopy(SESSION if session is None else session),
        )

    def test_committed_synthetic_constellation_validates(self):
        result = self.validate()
        self.assertEqual(result["doors"], ["MOTION", "PRESENT", "PRINT", "SOUND", "VOICE"])
        self.assertEqual(result["unfinished"], ["life:sound:001"])
        self.assertEqual(result["causal_result"], "comparison-ready-only")

    def test_refuses_real_adapter_claim_promotion(self):
        contract = copy.deepcopy(CONTRACT)
        contract["claims"]["real_adapters_bound"] = True
        with self.assertRaisesRegex(ValueError, "claims silently promoted"):
            self.validate(contract=contract)

    def test_refuses_visible_card_auto_execution(self):
        contract = copy.deepcopy(CONTRACT)
        contract["doors"][0]["automatic_execution"] = True
        with self.assertRaisesRegex(ValueError, "visibility must not execute"):
            self.validate(contract=contract)

    def test_refuses_parent_drift_between_siblings(self):
        session = copy.deepcopy(SESSION)
        session["branches"][1]["parent"] = "synthetic:other-parent"
        with self.assertRaisesRegex(ValueError, "sibling parent drift"):
            self.validate(session=session)

    def test_refuses_branch_intent_drift(self):
        session = copy.deepcopy(SESSION)
        session["branches"][2]["intent"] = "different intent"
        with self.assertRaisesRegex(ValueError, "branch intent drift"):
            self.validate(session=session)

    def test_refuses_sibling_mutation_authority(self):
        session = copy.deepcopy(SESSION)
        session["branches"][3]["may_mutate_sibling"] = True
        with self.assertRaisesRegex(ValueError, "may not mutate"):
            self.validate(session=session)

    def test_refuses_return_without_local_disposition(self):
        session = copy.deepcopy(SESSION)
        session["branches"][0]["disposition"] = None
        with self.assertRaisesRegex(ValueError, "requires explicit local disposition"):
            self.validate(session=session)

    def test_refuses_in_flight_pre_admission(self):
        session = copy.deepcopy(SESSION)
        session["branches"][2]["disposition"] = "ADMIT"
        with self.assertRaisesRegex(ValueError, "in-flight branch cannot"):
            self.validate(session=session)

    def test_refuses_tranchnose_authority_promotion(self):
        contract = copy.deepcopy(CONTRACT)
        contract["causal_observer"]["authority"] = "session-controller"
        with self.assertRaisesRegex(ValueError, "observer cannot acquire"):
            self.validate(contract=contract)

    def test_refuses_causal_proof_from_comparison_only_fixture(self):
        contract = copy.deepcopy(CONTRACT)
        contract["causal_observer"]["causal_attribution_proven"] = True
        with self.assertRaisesRegex(ValueError, "causal proof"):
            self.validate(contract=contract)

    def test_refuses_synthetic_replay_as_actual_reboot(self):
        session = copy.deepcopy(SESSION)
        session["reboot_expectation"]["actual_reboot_executed"] = True
        with self.assertRaisesRegex(ValueError, "promoted to executed reboot"):
            self.validate(session=session)

    def test_refuses_erasing_unfinished_branch_at_shutdown(self):
        session = copy.deepcopy(SESSION)
        session["shutdown_snapshot"]["unfinished_branch_ids"] = []
        with self.assertRaisesRegex(ValueError, "unfinished LIFE branches were erased"):
            self.validate(session=session)


if __name__ == "__main__":
    unittest.main()
