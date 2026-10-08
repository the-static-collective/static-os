"""Hostile question-first session proof, with genuine GHoT native signed dispatch.

The external GHoT checkout is optional for ordinary local unittest runs, but
REQUIRED by the dedicated PR CI job (GHOT_SRC pinned to a precise commit).
"""
from __future__ import annotations

import copy
import json
import os
import tempfile
import unittest
from pathlib import Path

from question_first.gear_donor import FORWARD, INVERSE, run as gear_run
from question_first.session import (
    SOURCE, Hold, _sealed, _state, _state_path, _write_new,
    compile_question, discover_ghot, execute_selected, native_packet_verify,
    replay_state, validate_seed, validate_selection,
)

ROOT = Path(__file__).resolve().parents[1]
SEED = json.loads((ROOT / "fixtures/question-first-001/gear-seed.json").read_text())
MANIFEST = ROOT / "integrations/question-first-001/adapter-manifest.json"


class QuestionFirstTests(unittest.TestCase):
    def test_ideal_mechanism_exact_math_and_nonhistorical_source(self):
        request = {
            "schema": "static-os.gear-simulation-request/v0",
            "operation": "forward", "driver_teeth": 12,
            "driven_teeth": 36, "input_turns": 6,
        }
        a = gear_run(request, FORWARD)
        self.assertEqual(a["value"], {"numerator": -2, "denominator": 1})
        self.assertFalse(a["physical_measurement"])
        self.assertFalse(a["historical_reconstruction_verified"])
        b = gear_run({**request, "operation": "inverse", "input_turns": -2}, INVERSE)
        self.assertEqual(b["value"], {"numerator": 6, "denominator": 1})

    def test_donor_rejects_unselected_operation_and_unsafe_types(self):
        req = {"schema": "static-os.gear-simulation-request/v0", "operation": "forward",
               "driver_teeth": 12, "driven_teeth": 36, "input_turns": 6}
        for modified in [
            {**req, "operation": "transmit"},
            {**req, "operation": "inverse"},
            {**req, "driver_teeth": True},
            {**req, "driver_teeth": 0},
            {**req, "input_turns": 10**30},
            {**req, "shell": "exec"},
        ]:
            with self.subTest(modified=modified), self.assertRaises(ValueError):
                gear_run(modified, FORWARD)

    def test_source_must_not_pretend_a_folio_is_verified(self):
        for modified in [
            {**SEED, "source": "LEONARDO_AUTHENTIC_FOLIO"},
            {**SEED, "driver_teeth": False},
            {**SEED, "driver_turns": 10000},
            {**SEED, "execution": "auto"},
        ]:
            with self.subTest(modified=modified), self.assertRaises(Hold):
                validate_seed(modified)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="static-question-first-")
        self.root = Path(self.temp.name)
        self.ghot = Path(os.environ["GHOT_SRC"]) if os.environ.get("GHOT_SRC") else None
        self.previous = {key: os.environ.get(key)
                         for key in ("GHOT_HOME", "GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"] = str(self.root / "ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"] = str(MANIFEST)

    def tearDown(self):
        for key, value in self.previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.temp.cleanup()

    def need_ghot(self):
        if self.ghot is None:
            self.skipTest("native GHoT checkout not supplied; dedicated CI requires GHOT_SRC")
        self.assertTrue((self.ghot / "ghot/instrument_rack.py").exists())

    def selection(self, question, candidate_id="simulate-forward", approved=True):
        candidate = next(c for c in question["candidate_experiments"]
                         if c["candidate_id"] == candidate_id)
        return {"schema": "static-os.question-selection/v0",
                "question_id": question["question_id"],
                "candidate_id": candidate_id, "card_id": candidate["card_id"],
                "approved": approved, "owner_id": "test-human"}

    def test_generate_two_candidates_from_actual_native_ghot_offers(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        q1 = compile_question(SEED, rack)
        q2 = compile_question(copy.deepcopy(SEED), rack)
        self.assertEqual(q1, q2)
        self.assertEqual(q1["status"], "QUESTION_OPEN")
        self.assertEqual(len(q1["candidate_experiments"]), 2)
        self.assertEqual({x["capability"] for x in q1["candidate_experiments"]},
                         {FORWARD, INVERSE})
        self.assertEqual(q1["historical_source"], "NO_VERIFIED_FOLIO_ATTACHED")
        self.assertFalse(q1["automatic_execution"])
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())

    def test_refuse_missing_instrument_and_invented_authority(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        q = compile_question(SEED, rack)
        modified = copy.deepcopy(rack)
        modified["cards"].pop()
        with self.assertRaises(Hold):
            compile_question(SEED, modified)
        modified = copy.deepcopy(rack)
        modified["cards"][0]["limits"]["transmit"] = True
        with self.assertRaises(Hold):
            compile_question(SEED, modified)
        for changed in [
            {**self.selection(q), "approved": False},
            {**self.selection(q), "owner_id": "hacker;rm"},
            {**self.selection(q), "card_id": "different"},
            {**self.selection(q), "authority": "ADMIT"},
            {**self.selection(q), "question_id": "other"},
        ]:
            with self.subTest(changed=changed), self.assertRaises(Hold):
                validate_selection(q, changed)
        self.assertFalse((self.root / "ghot" / "instrument-rack").exists())

    def test_prepared_execution_survives_as_hold_not_automatic_retry(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        question = compile_question(SEED, rack)
        selected = self.selection(question)
        candidate = validate_selection(question, selected)
        state_dir = self.root / "prepared-only"
        _write_new(_state_path(state_dir, question), _state({
            "schema": "static-os.question-session-state/v0",
            "stage": "PREPARED", "question": question, "selection": selected,
            "candidate": candidate, "operation": "GHOT_SIGNED_INSTRUMENT_DISPATCH",
            "auto_retry": False,
        }))
        with self.assertRaisesRegex(Hold, "NO_AUTORETRY"):
            execute_selected(SEED, rack, selected,
                             ghot_root=self.ghot, state_dir=state_dir)
        with self.assertRaisesRegex(Hold, "COLD_REPLAY_REFUSES_PREPARED"):
            replay_state(_state_path(state_dir, question), ghot_root=self.ghot)
        self.assertFalse((self.root / "ghot" / "instrument-rack" / "dispatches").exists())

    def test_real_native_signed_ghot_dispatch_and_read_only_cold_replay(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        question = compile_question(SEED, rack)
        chosen = self.selection(question)
        state_dir = self.root / "selected"
        actual = execute_selected(SEED, rack, chosen,
                                  ghot_root=self.ghot, state_dir=state_dir)
        self.assertFalse(actual["replayed"])
        s = actual["state"]
        self.assertEqual(s["stage"], "COMPLETED")
        self.assertEqual(s["observation"]["result"], "MATCHES_DECLARED_CLAIM")
        self.assertEqual(s["observation"]["value"], {"numerator": -2, "denominator": 1})
        self.assertFalse(s["observation"]["physical_observation"])
        self.assertFalse(s["automatic_next_turn"])
        self.assertEqual(s["next_question"]["status"], "PROPOSAL_ONLY")
        self.assertEqual(s["next_question"]["proposed_other_candidate_id"], "simulate-inverse")
        packet = s["native_ghot_result"]["packet"]
        self.assertEqual(native_packet_verify(self.ghot, packet)["packet_id"], packet["packet_id"])
        self.assertEqual(packet["status"], "PORTABLE_NOT_ADMITTED")
        dispatch_dir = self.root / "ghot" / "instrument-rack" / "dispatches"
        before = sorted(dispatch_dir.iterdir())
        self.assertEqual(len(before), 1)
        replayed = execute_selected(SEED, rack, chosen,
                                    ghot_root=self.ghot, state_dir=state_dir)
        self.assertTrue(replayed["replayed"])
        self.assertEqual(replayed["state"], s)
        self.assertEqual(sorted(dispatch_dir.iterdir()), before)
        self.assertEqual(replay_state(_state_path(state_dir, question),
                                      ghot_root=self.ghot), s)
        self.assertEqual(sorted(dispatch_dir.iterdir()), before)

    def test_inverse_proposal_and_contradictory_claim_both_execute_as_simulations(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        q = compile_question(SEED, rack)
        inv = execute_selected(SEED, rack, self.selection(q, "simulate-inverse"),
                               ghot_root=self.ghot, state_dir=self.root / "inverse")
        self.assertEqual(inv["state"]["observation"]["value"],
                         {"numerator": 6, "denominator": 1})
        wrong = {**SEED, "claimed_driven_turns": -3}
        q_wrong = compile_question(wrong, rack)
        contradiction = execute_selected(
            wrong, rack, self.selection(q_wrong),
            ghot_root=self.ghot, state_dir=self.root / "contradictory",
        )
        self.assertEqual(contradiction["state"]["observation"]["result"],
                         "CONTRADICTS_DECLARED_CLAIM")
        self.assertIn("contradiction", contradiction["state"]["next_question"]["question"].lower())
        self.assertFalse(contradiction["state"]["observation"]["physical_observation"])

    def test_native_signature_refuses_tampered_packet_even_with_state_rehash(self):
        self.need_ghot()
        rack = discover_ghot(self.ghot)
        q = compile_question(SEED, rack)
        data = execute_selected(SEED, rack, self.selection(q),
                                ghot_root=self.ghot, state_dir=self.root / "tamper")
        path = _state_path(self.root / "tamper", q)
        rewritten = copy.deepcopy(data["state"])
        rewritten["native_ghot_result"]["packet"]["donor_result"]["result"]["value"]["numerator"] = 999
        new_state = _state({k: v for k, v in rewritten.items() if k != "state_id"})
        path.write_text(json.dumps(new_state), encoding="utf-8")
        with self.assertRaises(Hold):
            replay_state(path, ghot_root=self.ghot)


if __name__ == "__main__":
    unittest.main()
