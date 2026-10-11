"""FIELD-PROCESSOR-001: no hardware, no person, no matchmaking backend."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from instruments.contract import Refuse
from instruments.field_processor import FieldProcessorAdapter
from instruments.host import InstrumentHost


FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/field-processor-001/three-rooms.json"


class FieldProcessorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "synthetic.json"
        self.source = json.loads(FIXTURE.read_text())
        self.save()
        self.adapter = FieldProcessorAdapter(self.path)

    def save(self):
        self.path.write_text(json.dumps(self.source, sort_keys=True) + "\n")

    def candidates(self):
        return self.adapter.observe()["items"]

    def test_native_contract_and_no_transmission(self):
        desc = self.adapter.describe()
        desc.validate()
        self.assertEqual(desc.to_dict()["transmission"], "DISABLED")
        self.assertEqual(set(desc.capabilities), {"observe", "select", "attend", "record"})
        self.assertTrue(desc.calibration["synthetic_only"])

    def test_three_rooms_two_candidates_one_decline(self):
        candidates = self.candidates()
        self.assertEqual([(c["mode"],c["left"],c["right"],c["status"]) for c in candidates], [
            ("ROOM_RHYME","A","C","HOLD"),
            ("SONG_SEAT","A","B","REFUSED")
        ])
        self.assertNotIn('"D"', json.dumps(candidates))
        self.assertTrue(all(c["authority"] == "NONE" and c["consequence"] == "NONE" for c in candidates))

    def test_offline_replay_preserves_exact_result(self):
        self.assertEqual(self.adapter.observe(), self.adapter.observe())

    def test_nonparticipant_even_if_identical_song(self):
        self.source["offers"][3]["song_ref"] = self.source["offers"][0]["song_ref"]
        self.save()
        self.assertNotIn('"D"', json.dumps(self.candidates()))

    def test_revocation_and_expiry_refuse_match(self):
        self.source["offers"][1]["revoked"] = True
        self.save()
        self.assertTrue(all(c["mode"] != "SONG_SEAT" for c in self.candidates()))
        self.source["offers"][1]["revoked"] = False
        self.source["offers"][1]["expires_at"] = self.source["now"]
        self.save()
        self.assertTrue(all(c["mode"] != "SONG_SEAT" for c in self.candidates()))

    def test_withheld_attribute_refuses_room_rhyme(self):
        self.source["offers"][0]["share"] = ["song_ref","weather"]
        self.save()
        self.assertTrue(all(c["mode"] != "ROOM_RHYME" for c in self.candidates()))

    def test_unknown_weather_and_different_basis_refuse(self):
        self.source["offers"][2]["weather"] = None
        self.save()
        self.assertTrue(all(c["mode"] != "ROOM_RHYME" for c in self.candidates()))
        self.source["offers"][2]["weather"] = "rain"
        self.source["offers"][2]["weather_basis"] = "UNVERIFIED_SENSOR"
        self.save()
        self.assertTrue(all(c["mode"] != "ROOM_RHYME" for c in self.candidates()))

    def test_equal_title_different_recording_ref_refuses(self):
        self.source["offers"][1]["song_ref"] = "recording:rosemary-roses-alt-take"
        self.save()
        self.assertTrue(all(c["mode"] != "SONG_SEAT" for c in self.candidates()))

    def test_mutual_accept_is_only_simulated_readiness(self):
        self.source["decisions"]["C"] = "ACCEPT"
        self.save()
        c = self.candidates()[0]
        self.assertEqual(c["status"], "MUTUAL_READY_SIMULATED")
        self.assertEqual(c["consequence"], "NONE")

    def test_ground_echo_is_only_typed_synthetic_hypothesis(self):
        for o in self.source["offers"][:2]:
            o["modes"].append("GROUND_ECHO")
            o["share"].append("ground_event")
            o["ground_event"] = "event-class:truck-like-rumble"
            o["ground_basis"] = "SYNTHETIC_SENSOR"
        self.save()
        pairs = [c for c in self.candidates() if c["mode"] == "GROUND_ECHO"]
        self.assertEqual(len(pairs), 1)
        self.assertIn("SAME_VEHICLE_UNPROVEN", pairs[0]["evidence"])
        self.source["offers"][1]["ground_basis"] = "REAL_GEOPHONE"
        self.save()
        self.assertFalse([c for c in self.candidates() if c["mode"] == "GROUND_ECHO"])

    def test_single_declared_condition_perturbation_changes_only_room_rhyme(self):
        before = self.candidates()
        before_song = [x for x in before if x["mode"] == "SONG_SEAT"]
        self.source["offers"][2]["weather"] = "dry"
        self.save()
        after = self.candidates()
        self.assertEqual([x for x in after if x["mode"] == "SONG_SEAT"], before_song)
        self.assertFalse([x for x in after if x["mode"] == "ROOM_RHYME"])

    def test_roomtone_source_hash_changes_with_one_perturbation(self):
        before = self.adapter.describe().source["sha256"]
        self.source["offers"][2]["texture"] = "irregular-metal-hum"
        self.save()
        after = self.adapter.describe().source["sha256"]
        self.assertNotEqual(before, after)

    def test_no_ground_identity_when_classification_is_unknown(self):
        for o in self.source["offers"][:2]:
            o["modes"].append("GROUND_ECHO")
            o["share"].append("ground_event")
            o["ground_event"] = "same-vibration-tag"
            o["ground_basis"] = None
        self.save()
        self.assertFalse([x for x in self.candidates() if x["mode"] == "GROUND_ECHO"])

    def test_unknown_fields_and_control_smuggling_refused(self):
        for key in ("raw_audio", "gps", "connect", "transmit", "secret"):
            original = copy.deepcopy(self.source)
            self.source["offers"][0][key] = True
            self.save()
            with self.subTest(key=key), self.assertRaises(Refuse):
                self.adapter.observe()
            self.source = original

    def test_invalid_classification_and_duplicates_refused(self):
        self.source["classification"] = "LIVE_SENSOR"
        self.save()
        with self.assertRaises(Refuse):
            self.adapter.describe()
        self.source["classification"] = "SYNTHETIC_ONLY"
        self.source["offers"][1]["id"] = "A"
        self.save()
        with self.assertRaises(Refuse):
            self.adapter.describe()

    def test_oversized_and_missing_source_refused(self):
        self.path.write_bytes(b"x" * 65537)
        with self.assertRaises(Refuse):
            self.adapter.describe()
        self.path.unlink()
        with self.assertRaises(Refuse):
            self.adapter.describe()

    def test_empty_eligible_field_returns_sentinel_not_person(self):
        for o in self.source["offers"]:
            o["opted_in"] = False
        self.save()
        items = self.candidates()
        self.assertEqual(items[0]["type"], "NO_CANDIDATE")
        self.assertNotIn('"A"', json.dumps(items))

    def test_actual_native_host_can_observe_and_select_but_not_execute(self):
        host = InstrumentHost(Path(self.tmp.name) / "host")
        self.addCleanup(host.close)
        descriptor = host.install(self.adapter)
        self.assertEqual(descriptor["transmission"], "DISABLED")
        observed = host.observe(self.adapter.instrument_id)
        self.assertEqual(len(observed["items"]), 2)
        host.set_positions(self.adapter.instrument_id, [1])
        selected = host.select(self.adapter.instrument_id)
        self.assertEqual(selected["type"], "FieldCandidateSelection")
        self.assertFalse(selected["may_connect"])
        self.assertFalse(selected["may_actuate"])
        request = host.propose_operation(self.adapter.instrument_id)
        with self.assertRaises(Refuse):
            host.execute(request)

    def test_changed_source_withdraws_host_capability(self):
        host = InstrumentHost(Path(self.tmp.name) / "host")
        self.addCleanup(host.close)
        host.install(self.adapter)
        host.observe(self.adapter.instrument_id)
        self.source["offers"][1]["song_ref"] = "recording:changed"
        self.save()
        with self.assertRaisesRegex(Refuse, "source withdrawn"):
            host.select(self.adapter.instrument_id)
        self.assertEqual(host.discover()["instruments"][0]["lifecycle"], "withdrawn")


if __name__ == "__main__":
    unittest.main()
