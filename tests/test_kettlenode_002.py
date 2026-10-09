"""Hostile tests: Heat Commons thermal routes are simulations, not pumps."""
import copy
import json
import unittest
from pathlib import Path

from crank.heat_commons import evaluate, simulate_route, temperature_centi_c, validate_world
from crank.runtime import Refuse

ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "kettlenode-002"


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class HeatCommonsTests(unittest.TestCase):
    def setUp(self):
        self.world = load("world.json")
        self.route = load("route.json")

    def test_inert_evaluation_does_not_mutate(self):
        original = copy.deepcopy(self.world)
        check = evaluate(self.world, self.route)
        self.assertTrue(check["feasible"])
        self.assertFalse(check["physical_actuation"])
        self.assertEqual(original, self.world)

    def test_simulated_transfer_conserves_exact_heat(self):
        total = sum(n["thermal_energy_j"] for n in self.world["nodes"].values())
        result = simulate_route(self.world, self.route)
        updated = result["world"]
        self.assertEqual(total, sum(n["thermal_energy_j"] for n in updated["nodes"].values()))
        self.assertEqual(self.world["spent_request_ids"], [])
        self.assertEqual(len(updated["spent_request_ids"]), 1)
        self.assertEqual(updated["nodes"]["solar-bank"]["thermal_energy_j"],
                         self.world["nodes"]["solar-bank"]["thermal_energy_j"] - 100000)
        self.assertEqual(updated["nodes"]["fish-tank"]["thermal_energy_j"],
                         self.world["nodes"]["fish-tank"]["thermal_energy_j"] + 100000)
        self.assertGreater(temperature_centi_c(updated["nodes"]["fish-tank"]), 2200)
        self.assertLess(temperature_centi_c(updated["nodes"]["solar-bank"]), 5000)

    def test_no_actual_transfer_or_electric_claim(self):
        result = simulate_route(self.world, self.route)
        receipt = result["receipt"]
        for key in ("actual_heat_moved", "fluid_interconnection",
                    "electrical_energy_generated", "actuator_command_emitted"):
            self.assertFalse(receipt[key])
        self.assertEqual(receipt["authority_effect"], "none")
        self.assertEqual(receipt["signature_status"], "unsigned-simulation")

    def test_replay_cannot_execute_again_with_same_world_snapshot(self):
        updated = simulate_route(self.world, self.route)["world"]
        with self.assertRaisesRegex(Refuse, "already spent"):
            simulate_route(updated, self.route)

    def test_uphill_thermal_route_refused(self):
        self.route.update(source="computer-coolant", destination="solar-bank",
                          exchanger_id=None)
        with self.assertRaisesRegex(Refuse, "uphill"):
            evaluate(self.world, self.route)

    def test_overheating_fish_refused(self):
        self.route["transfer_j"] = 13000000
        with self.assertRaisesRegex(Refuse, "overheat"):
            evaluate(self.world, self.route)

    def test_undercooling_source_refused(self):
        self.world["nodes"]["solar-bank"]["min_centi_c"] = 4800
        self.route["transfer_j"] = 2100000
        with self.assertRaisesRegex(Refuse, "undercool"):
            evaluate(self.world, self.route)

    def test_inverting_thermal_gradient_refused(self):
        self.route["transfer_j"] = 19000000
        with self.assertRaisesRegex(Refuse, "invert thermal gradient"):
            evaluate(self.world, self.route)

    def test_no_mixing_fish_and_heat_bank_without_exchanger(self):
        self.route["exchanger_id"] = None
        with self.assertRaisesRegex(Refuse, "isolating exchanger"):
            evaluate(self.world, self.route)

    def test_wrong_exchanger_refused(self):
        self.route["exchanger_id"] = "hx-roots"
        with self.assertRaisesRegex(Refuse, "incompatible"):
            evaluate(self.world, self.route)

    def test_throughput_exceeded(self):
        self.world["exchangers"]["hx-fish"]["max_transfer_j"] = 10
        with self.assertRaisesRegex(Refuse, "throughput exceeded"):
            evaluate(self.world, self.route)

    def test_no_direct_biological_fluid_routing(self):
        self.route.update(source="fish-tank", destination="root-zone",
                          exchanger_id=None)
        # fish at 22C, roots at 20C; potential heat exists, fluid mixing prohibited
        with self.assertRaisesRegex(Refuse, "isolating exchanger"):
            evaluate(self.world, self.route)

    def test_loss_of_circulation_fails_closed(self):
        self.world["nodes"]["fish-tank"]["circulation_ok"] = False
        with self.assertRaisesRegex(Refuse, "circulation unavailable"):
            evaluate(self.world, self.route)

    def test_missing_fish_oxygen_refuses_routing(self):
        self.world["nodes"]["fish-tank"]["oxygen_ok"] = False
        with self.assertRaisesRegex(Refuse, "fish life-support"):
            evaluate(self.world, self.route)

    def test_meter_claim_promotion_refused(self):
        self.world["evidence_kind"] = "calibrated-live-hardware"
        with self.assertRaisesRegex(Refuse, "unearned measurement"):
            evaluate(self.world, self.route)

    def test_perpetual_heat_or_power_claim_refused(self):
        self.route["electrical_energy_generated"] = True
        with self.assertRaisesRegex(Refuse, "fields changed"):
            evaluate(self.world, self.route)

    def test_automated_command_and_admission_refused(self):
        for field, value in (("selection", "timer"), ("authority_request", "grant"),
                             ("admission_request", "ADMIT")):
            bad = copy.deepcopy(self.route)
            bad[field] = value
            with self.assertRaisesRegex(Refuse, "cannot gain authority"):
                evaluate(self.world, bad)

    def test_bad_numbers_refused(self):
        for value in (0, -1, True, 1.0, 10**16):
            bad = copy.deepcopy(self.route)
            bad["transfer_j"] = value
            with self.assertRaises(Refuse):
                evaluate(self.world, bad)

    def test_tampered_receipt_detected(self):
        new_world = simulate_route(self.world, self.route)["world"]
        new_world["receipts"][0]["actual_heat_moved"] = True
        with self.assertRaises(Refuse):
            validate_world(new_world)

    def test_tampered_balance_refuses_invalid_temperature(self):
        self.world["nodes"]["fish-tank"]["thermal_energy_j"] = 999999999
        with self.assertRaisesRegex(Refuse, "exceeds temperature limits"):
            validate_world(self.world)

    def test_compost_lacks_direct_fluid_connection(self):
        self.route.update(source="compost-hx", destination="solar-bank",
                          transfer_j=50000, exchanger_id=None)
        with self.assertRaisesRegex(Refuse, "isolating exchanger"):
            evaluate(self.world, self.route)
        self.route["exchanger_id"] = "hx-compost"
        self.assertTrue(evaluate(self.world, self.route)["feasible"])

    def test_heat_into_root_zone_is_independent_from_fish_water(self):
        self.route.update(destination="root-zone", exchanger_id="hx-roots")
        result = simulate_route(self.world, self.route)
        self.assertEqual(result["world"]["nodes"]["fish-tank"],
                         self.world["nodes"]["fish-tank"])
        self.assertGreater(result["world"]["nodes"]["root-zone"]["thermal_energy_j"],
                           self.world["nodes"]["root-zone"]["thermal_energy_j"])


if __name__ == "__main__":
    unittest.main()
