import copy
import json
import unittest
from pathlib import Path

from v1.vehicle_ecm import Refuse, digest, ingest_observation

ROOT = Path(__file__).resolve().parents[1]
OBS = json.loads((ROOT / "fixtures" / "v1" / "vehicle-ecm-observation-001.json").read_text())


class V1VehicleECMTests(unittest.TestCase):
    def test_fixture_observation_yields_readonly_receipt(self):
        receipt = ingest_observation(copy.deepcopy(OBS))
        self.assertEqual(receipt["mode"], "observation-only")
        self.assertEqual(receipt["vehicle_control_authority"], "none")
        self.assertEqual(receipt["diagnostic_write_authority"], "none")
        self.assertEqual(receipt["safety_critical_actuation"], "forbidden")
        self.assertFalse(receipt["automatic_next_turn"])

    def test_observation_hash_is_content_bound(self):
        first = ingest_observation(copy.deepcopy(OBS))
        changed = copy.deepcopy(OBS)
        changed["signals"]["engine_rpm"]["value"] = 813
        second = ingest_observation(changed)
        self.assertNotEqual(first["observation_sha256"], second["observation_sha256"])
        self.assertNotEqual(first["receipt_sha256"], second["receipt_sha256"])

    def test_refuses_control_command_field(self):
        hostile = copy.deepcopy(OBS)
        hostile["command"] = "anything"
        with self.assertRaisesRegex(Refuse, "vehicle control field refused"):
            ingest_observation(hostile)

    def test_refuses_throttle_field_even_when_nested(self):
        hostile = copy.deepcopy(OBS)
        hostile["signals"]["engine_rpm"]["throttle"] = 20
        with self.assertRaisesRegex(Refuse, "vehicle control field refused"):
            ingest_observation(hostile)

    def test_refuses_reflash_request(self):
        hostile = copy.deepcopy(OBS)
        hostile["reflash"] = True
        with self.assertRaisesRegex(Refuse, "vehicle control field refused"):
            ingest_observation(hostile)

    def test_refuses_non_allowlisted_signal(self):
        hostile = copy.deepcopy(OBS)
        hostile["signals"]["steering_angle"] = {"value": 0, "unit": "deg"}
        with self.assertRaisesRegex(Refuse, "not allowlisted"):
            ingest_observation(hostile)

    def test_refuses_unit_laundering(self):
        hostile = copy.deepcopy(OBS)
        hostile["signals"]["vehicle_speed"]["unit"] = "mph"
        with self.assertRaisesRegex(Refuse, "unit mismatch"):
            ingest_observation(hostile)

    def test_receipt_self_address_is_stable(self):
        receipt = ingest_observation(copy.deepcopy(OBS))
        body = dict(receipt)
        stored = body.pop("receipt_sha256")
        self.assertEqual(stored, digest(body))


if __name__ == "__main__":
    unittest.main()
