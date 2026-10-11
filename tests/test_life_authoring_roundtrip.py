import copy
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from validate_life_authoring_roundtrip import load, validate


class LifeAuthoringRoundtripTests(unittest.TestCase):
    def test_roundtrip_passes(self):
        self.assertEqual(validate()["status"], "PASS")

    def test_door_cannot_become_an_automatic_action(self):
        door = copy.deepcopy(load()["door"])
        door["status"] = "EXECUTED"
        with self.assertRaisesRegex(ValueError, "door gained"):
            validate({"door": door})

    def test_human_selection_cannot_be_replaced_by_agent(self):
        choice = copy.deepcopy(load()["choice"])
        choice["authority"] = "agent"
        with self.assertRaisesRegex(ValueError, "human selection absent"):
            validate({"choice": choice})

    def test_choice_cannot_select_an_unrelated_door(self):
        choice = copy.deepcopy(load()["choice"])
        choice["door_id"] = "open-page-001:door:someone-else"
        with self.assertRaisesRegex(ValueError, "proposed door"):
            validate({"choice": choice})

    def test_unobserved_external_consequence_refuses(self):
        occurrence = copy.deepcopy(load()["occurrence"])
        occurrence["external_world_consequence"] = "LIFE_CHANGED"
        with self.assertRaisesRegex(ValueError, "unwitnessed life consequence"):
            validate({"occurrence": occurrence})

    def test_expected_is_not_silently_promoted_to_observed(self):
        comparison = copy.deepcopy(load()["comparison"])
        row = next(row for row in comparison["comparisons"]
                   if row["dimension"] == "full-verification")
        row["status"] = "MATCH"
        row["observed"] = "PASS"
        with self.assertRaisesRegex(ValueError, "backdated"):
            validate({"comparison": comparison})

    def test_mythic_echo_cannot_become_historical_claim(self):
        comparison = copy.deepcopy(load()["comparison"])
        comparison["mythic_echo"]["historical_claim"] = True
        with self.assertRaisesRegex(ValueError, "promoted to history"):
            validate({"comparison": comparison})

    def test_source_manifest_stays_historically_open(self):
        manifest = copy.deepcopy(load()["manifest"])
        manifest["consequence"]["state"] = "CLOSED"
        with self.assertRaisesRegex(ValueError, "retconned"):
            validate({"manifest": manifest})


if __name__ == "__main__":
    unittest.main()
