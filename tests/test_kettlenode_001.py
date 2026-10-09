"""KETTLENODE-001 hostile tests. No physical-energy claim is made."""
import copy
import json
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from crank.runtime import Refuse
from crank.thermal import observe, inspect, reserve, attempt_turn

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "fixtures" / "kettlenode-001"


def fixture(name):
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


class KettleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ledger = Path(self.tmp.name) / "ledger.json"
        self.policy = fixture("policy.json")
        self.baseline = fixture("baseline.json")
        self.warm = fixture("warm.json")
        self.request = fixture("turn.json")
        self.registry = json.loads(
            (ROOT / "fixtures/cranknode-001/capabilities.json").read_text()
        )

    def prime(self):
        observe(self.baseline, self.ledger, self.policy)

    def warmup(self):
        self.prime()
        observe(self.warm, self.ledger, self.policy)

    def test_no_observation_no_work(self):
        with self.assertRaisesRegex(Refuse, "no energy baseline"):
            reserve(self.ledger, self.policy, self.request)
        self.assertIsNone(inspect(self.ledger, self.policy))

    def test_zero_baseline_is_not_power(self):
        self.prime()
        with self.assertRaisesRegex(Refuse, "insufficient"):
            reserve(self.ledger, self.policy, self.request)
        self.assertEqual(inspect(self.ledger, self.policy)["turns"], [])

    def test_one_warm_sample_one_selected_turn_and_receipts(self):
        self.warmup()
        state = inspect(self.ledger, self.policy)
        self.assertEqual(state["available_mj"], 9000)
        self.assertEqual(state["turns"], [])
        outcome = attempt_turn(self.ledger, self.policy, self.registry, self.request)
        self.assertEqual(outcome["crank"]["result"]["capability_id"], "TEXT.HASH")
        self.assertEqual(outcome["crank"]["receipt"]["authority_effect"], "none")
        self.assertFalse(outcome["claims"]["actual_consumption_metered"])
        self.assertFalse(outcome["claims"]["heat_source_physically_observed"])
        self.assertFalse(outcome["claims"]["automatic_next_turn"])
        self.assertEqual(inspect(self.ledger, self.policy)["available_mj"], 4000)
        self.assertEqual(len(inspect(self.ledger, self.policy)["turns"]), 1)

    def test_duplicate_turn_fails_even_when_more_energy_arrives(self):
        self.warmup()
        attempt_turn(self.ledger, self.policy, self.registry, self.request)
        later = copy.deepcopy(self.warm)
        later.update(sequence=2, cumulative_millijoules=17000)
        observe(later, self.ledger, self.policy)
        with self.assertRaisesRegex(Refuse, "already reserved"):
            attempt_turn(self.ledger, self.policy, self.registry, self.request)
        self.assertEqual(inspect(self.ledger, self.policy)["available_mj"], 12000)

    def test_energy_not_automatic_second_turn(self):
        self.warmup()
        attempt_turn(self.ledger, self.policy, self.registry, self.request)
        new_request = copy.deepcopy(self.request)
        new_request["turn_id"] = "KETTLE-TURN-002"
        with self.assertRaisesRegex(Refuse, "insufficient"):
            attempt_turn(self.ledger, self.policy, self.registry, new_request)
        self.assertEqual(len(inspect(self.ledger, self.policy)["turns"]), 1)

    def test_sample_replay_gap_and_decreasing_cumulative_refused(self):
        self.warmup()
        with self.assertRaisesRegex(Refuse, "replay, gap"):
            observe(self.warm, self.ledger, self.policy)
        gap = copy.deepcopy(self.warm)
        gap.update(sequence=3, cumulative_millijoules=12000)
        with self.assertRaisesRegex(Refuse, "replay, gap"):
            observe(gap, self.ledger, self.policy)
        decreasing = copy.deepcopy(self.warm)
        decreasing.update(sequence=2, cumulative_millijoules=8000)
        with self.assertRaisesRegex(Refuse, "decreased"):
            observe(decreasing, self.ledger, self.policy)

    def test_sample_must_not_select_capability_or_authority(self):
        self.prime()
        hostile = dict(self.warm, selected_capability="AI.PROPOSE")
        with self.assertRaisesRegex(Refuse, "fields changed"):
            observe(hostile, self.ledger, self.policy)
        hostile = dict(self.warm, admission_request="ADMIT")
        with self.assertRaisesRegex(Refuse, "fields changed"):
            observe(hostile, self.ledger, self.policy)

    def test_fake_hardware_and_session_spoof_refused(self):
        self.prime()
        for field, value in (
            ("source_id", "other-device"),
            ("session_id", "reset-001"),
            ("observation_kind", "meter-reported-unverified"),
        ):
            bogus = dict(self.warm, **{field: value})
            with self.assertRaisesRegex(Refuse, "mismatch"):
                observe(bogus, self.ledger, self.policy)

    def test_limits_booleans_floats_and_giant_jump(self):
        self.prime()
        for value in (-1, True, 1.5):
            bogus = dict(self.warm, cumulative_millijoules=value)
            with self.assertRaises(Refuse):
                observe(bogus, self.ledger, self.policy)
        giant = dict(self.warm, cumulative_millijoules=100000)
        with self.assertRaisesRegex(Refuse, "increment exceeds"):
            observe(giant, self.ledger, self.policy)

    def test_policy_change_does_not_reprice_reserved_work(self):
        self.warmup()
        hostile = copy.deepcopy(self.policy)
        hostile["capability_allowances_mj"]["TEXT.HASH"] = 1
        with self.assertRaisesRegex(Refuse, "policy changed"):
            attempt_turn(self.ledger, hostile, self.registry, self.request)

    def test_corrupt_ledger_fails_closed(self):
        self.warmup()
        self.ledger.write_text("{garbage", encoding="utf-8")
        with self.assertRaisesRegex(Refuse, "unreadable"):
            observe(dict(self.warm, sequence=2), self.ledger, self.policy)

    def test_tampered_balance_detected(self):
        self.warmup()
        state = json.loads(self.ledger.read_text())
        state["available_mj"] = 99999
        self.ledger.write_text(json.dumps(state))
        with self.assertRaisesRegex(Refuse, "hash mismatch"):
            inspect(self.ledger, self.policy)

    def test_nonhuman_turn_refused(self):
        self.warmup()
        for kind in ("timer", "peer-node", "physical-input"):
            hostile = copy.deepcopy(self.request)
            hostile["source"]["kind"] = kind
            with self.assertRaisesRegex(Refuse, "human-selected"):
                attempt_turn(self.ledger, self.policy, self.registry, hostile)
        self.assertEqual(inspect(self.ledger, self.policy)["turns"], [])

    def test_crash_spends_reservation_without_forging_success(self):
        self.warmup()
        with patch("crank.thermal.execute_turn", side_effect=RuntimeError("provider crashed")):
            with self.assertRaisesRegex(RuntimeError, "crashed"):
                attempt_turn(self.ledger, self.policy, self.registry, self.request)
        state = inspect(self.ledger, self.policy)
        self.assertEqual(state["available_mj"], 4000)
        self.assertEqual(len(state["turns"]), 1)
        self.assertFalse(state["turns"][0]["execution_proven"])
        with self.assertRaisesRegex(Refuse, "already reserved"):
            attempt_turn(self.ledger, self.policy, self.registry, self.request)

    def test_competing_same_turn_claims_only_one_wins(self):
        self.warmup()
        outcomes = []
        lock = threading.Lock()
        def run():
            try:
                value = attempt_turn(self.ledger, self.policy, self.registry, self.request)
            except Refuse:
                value = "REFUSE"
            with lock:
                outcomes.append(value)
        a = threading.Thread(target=run)
        b = threading.Thread(target=run)
        a.start()
        b.start()
        a.join()
        b.join()
        self.assertEqual(len([x for x in outcomes if isinstance(x, dict)]), 1)
        self.assertEqual(outcomes.count("REFUSE"), 1)
        self.assertEqual(len(inspect(self.ledger, self.policy)["turns"]), 1)


if __name__ == "__main__":
    unittest.main()
