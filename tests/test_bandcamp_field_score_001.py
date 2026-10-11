"""BANDCAMP-FIELD-SCORE-001 — an album is not executable code."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest

from instruments.bandcamp_field_score import BandcampFieldScoreAdapter
from instruments.contract import Refuse
from instruments.host import InstrumentHost

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures/bandcamp-field-score-001/three-cues.json"


class BandcampScoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "field-score.json"
        self.source = json.loads(FIXTURE.read_text())
        self.save()
        self.adapter = BandcampFieldScoreAdapter(self.path)

    def save(self):
        self.path.write_text(json.dumps(self.source, sort_keys=True) + "\n")

    def items(self):
        return self.adapter.observe()["items"]

    def test_native_adapter_is_read_only(self):
        desc = self.adapter.describe()
        desc.validate()
        self.assertEqual(desc.to_dict()["transmission"], "DISABLED")
        self.assertEqual(set(desc.capabilities), {"observe", "select", "attend", "record"})

    def test_distinct_occurrences_share_one_referent_without_authority(self):
        pair, sequence = self.items()
        self.assertEqual(pair["match"], "SYNTHETIC_SAME_REFERENT")
        self.assertEqual(pair["observation_ids"], ["q1", "a1"])
        self.assertIn("q1-replay", pair["all_matching_occurrence_ids"])
        self.assertEqual(pair["independence_claim"], "NONE")
        self.assertEqual(pair["consequence"], "NONE")
        self.assertEqual(sequence["evaluation"], "DECLARED_SYNTHETIC_ORDER")
        self.assertIn("ACTUAL_PLAYBACK", sequence["not_proved"])

    def test_wrong_referent_stays_outside_pair(self):
        pair, _ = self.items()
        self.assertEqual(pair["rejected_or_ambiguous_ids"], ["optical-other"])
        self.assertNotIn("optical-other", pair["all_matching_occurrence_ids"])

    def test_deterministic_replay(self):
        self.assertEqual(self.adapter.observe(), self.adapter.observe())

    def test_mutated_source_withdraws_old_digest(self):
        before = self.adapter.describe().source["sha256"]
        self.source["observations"][1]["referent"] = "artifact:wrong"
        self.save()
        self.assertNotEqual(before, self.adapter.describe().source["sha256"])

    def test_missing_audio_channel_makes_pair_missing(self):
        self.source["observations"] = [
            o for o in self.source["observations"] if o["channel"] != "AUDIO"
        ]
        self.save()
        self.assertEqual(self.items()[0]["match"], "MISSING_CHANNEL_HOLD")
        self.assertEqual(self.items()[1]["evaluation"], "MISSING_CUE_HOLD")

    def test_corrupt_and_ambiguous_audio_do_not_match(self):
        for state in ("FAIL", "AMBIGUOUS"):
            self.source = json.loads(FIXTURE.read_text())
            self.source["observations"][1]["integrity"] = state
            self.save()
            pair, sequence = self.items()
            self.assertEqual(pair["observation_ids"][1], "a2")
            self.assertEqual(sequence["evaluation"], "MISSING_CUE_HOLD")
            self.assertIn("a1", pair["rejected_or_ambiguous_ids"])

    def test_out_of_order_stays_out_of_order(self):
        self.source["observations"][3]["sequence"] = 1
        self.save()
        self.assertEqual(self.items()[1]["evaluation"], "OUT_OF_ORDER_HOLD")

    def test_cross_clock_order_not_inferred(self):
        self.source["observations"][3]["clock_domain"] = "other-device"
        self.save()
        self.assertEqual(self.items()[1]["evaluation"], "UNCOMPARABLE_CLOCK_HOLD")

    def test_repeat_audio_kept_but_not_automatically_trusted(self):
        new = copy.deepcopy(self.source["observations"][1])
        new["id"] = "a1-replay"
        new["sequence"] = 7
        self.source["observations"].append(new)
        self.save()
        self.assertEqual(self.items()[1]["evaluation"], "REPEATED_CUE_HOLD")

    def test_declined_offer_remains_visible(self):
        self.source["decision"] = "DECLINE"
        self.save()
        self.assertEqual([x["status"] for x in self.items()], ["REFUSED", "REFUSED"])
        self.assertTrue(all(x["consequence"] == "NONE" for x in self.items()))

    def test_authority_smuggling_through_source_refused(self):
        for extra in ("run", "url", "permissions", "download", "connect", "location"):
            self.source = json.loads(FIXTURE.read_text())
            self.source["observations"][0][extra] = "auto"
            self.save()
            with self.subTest(extra=extra), self.assertRaises(Refuse):
                self.items()

    def test_duplicate_occurrences_and_unknown_cue_refused(self):
        self.source["observations"][1]["id"] = "q1"
        self.save()
        with self.assertRaises(Refuse):
            self.items()
        self.source["observations"][1]["id"] = "a1"
        self.source["observations"][1]["cue_id"] = "imaginary-song"
        self.save()
        with self.assertRaises(Refuse):
            self.items()

    def test_real_capture_claim_refused(self):
        self.source["observations"][0]["capture_kind"] = "PHYSICAL"
        self.save()
        with self.assertRaises(Refuse):
            self.items()

    def test_wrong_source_and_recording_digest_refused(self):
        self.source["edition"]["evidence_level"] = "VERIFIED_MASTER"
        self.save()
        with self.assertRaises(Refuse):
            self.items()
        self.source["edition"]["evidence_level"] = "LYRIC_EXPORT_ONLY"
        self.source["cues"][0]["recording_sha256"] = "sha256:example"
        self.save()
        with self.assertRaises(Refuse):
            self.items()

    def test_empty_missing_or_oversized_file_refused(self):
        self.path.write_bytes(b"x" * 65537)
        with self.assertRaises(Refuse):
            self.adapter.describe()
        self.path.unlink()
        with self.assertRaises(Refuse):
            self.adapter.describe()

    def test_duplicate_json_key_refused(self):
        self.path.write_text('{"schema":"a","schema":"b"}')
        with self.assertRaises(Refuse):
            self.adapter.describe()

    def test_native_host_select_cannot_execute(self):
        host = InstrumentHost(Path(self.temp.name) / "host")
        self.addCleanup(host.close)
        descriptor = host.install(self.adapter)
        self.assertEqual(descriptor["transmission"], "DISABLED")
        observed = host.observe(self.adapter.instrument_id)
        self.assertEqual(len(observed["items"]), 2)
        host.set_positions(self.adapter.instrument_id, [1])
        selected = host.select(self.adapter.instrument_id)
        self.assertEqual(selected["type"], "BandcampFieldScoreSelection")
        self.assertFalse(selected["may_execute"])
        self.assertFalse(selected["may_open_url"])
        proposal = host.propose_operation(self.adapter.instrument_id)
        with self.assertRaises(Refuse):
            host.execute(proposal)

    def test_host_withdraws_source_after_change(self):
        host = InstrumentHost(Path(self.temp.name) / "host")
        self.addCleanup(host.close)
        host.install(self.adapter)
        host.observe(self.adapter.instrument_id)
        self.source["observations"][1]["referent"] = "artifact:changed"
        self.save()
        with self.assertRaisesRegex(Refuse, "source withdrawn"):
            host.select(self.adapter.instrument_id)


if __name__ == "__main__":
    unittest.main()
