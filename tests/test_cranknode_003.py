import copy
import json
import os
import pty
import tempfile
import threading
import time
import unittest
from pathlib import Path

from crank.physical import (
    claim_edge,
    decode_edge_frame,
    edge_id,
    edge_to_turn,
    normalize_edge,
    read_one_tty_frame,
)
from crank.relatte_candidate import make_relatte_candidate
from crank.runtime import Refuse, execute_turn

ROOT = Path(__file__).resolve().parents[1]
EDGE = json.loads((ROOT / "fixtures" / "cranknode-003" / "edge-001.jsonl").read_text())
PAYLOAD = json.loads((ROOT / "fixtures" / "cranknode-003" / "payload.json").read_text())
ALPHA = json.loads((ROOT / "fixtures" / "cranknode-002" / "capabilities-alpha.json").read_text())


class CrankNode003Tests(unittest.TestCase):
    def test_edge_identity_is_stable(self):
        self.assertEqual(edge_id(EDGE), edge_id(copy.deepcopy(EDGE)))

    def test_refuses_multi_tick_frame(self):
        edge = copy.deepcopy(EDGE)
        edge["ticks"] = 2
        with self.assertRaisesRegex(Refuse, "exactly one tick"):
            normalize_edge(edge)

    def test_refuses_extra_semantic_fields_from_hardware(self):
        edge = copy.deepcopy(EDGE)
        edge["admit"] = True
        with self.assertRaisesRegex(Refuse, "fields changed"):
            normalize_edge(edge)

    def test_claim_is_durable_and_duplicate_is_refused(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "edges.jsonl"
            receipt = claim_edge(copy.deepcopy(EDGE), ledger)
            self.assertTrue(receipt["consumed"])
            self.assertEqual(receipt["semantic_authority"], "none")
            self.assertEqual(receipt["admission_authority"], "none")
            self.assertFalse(receipt["automatic_retry"])
            self.assertTrue(ledger.read_text().strip())
            with self.assertRaisesRegex(Refuse, "already consumed"):
                claim_edge(copy.deepcopy(EDGE), ledger)

    def test_same_sequence_in_new_device_session_is_a_new_edge(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "edges.jsonl"
            claim_edge(copy.deepcopy(EDGE), ledger)
            fresh = copy.deepcopy(EDGE)
            fresh["session_id"] = "fixture-boot-B"
            second = claim_edge(fresh, ledger)
            self.assertNotEqual(second["edge_id"], edge_id(EDGE))

    def test_edge_becomes_one_plain_physical_turn_request(self):
        request = edge_to_turn(EDGE, "AI.PROPOSE", PAYLOAD, 3)
        self.assertEqual(request["source"]["kind"], "physical-input")
        self.assertEqual(request["source"]["id"], edge_id(EDGE))
        self.assertEqual(request["selected_capability"], "AI.PROPOSE")
        self.assertEqual(request["authority_request"], "none")
        self.assertEqual(request["admission_request"], "none")

    def test_physical_edge_composes_through_provider_to_unsigned_candidate(self):
        with tempfile.TemporaryDirectory() as td:
            gate = claim_edge(copy.deepcopy(EDGE), Path(td) / "edges.jsonl")
            request = edge_to_turn(EDGE, "AI.PROPOSE", PAYLOAD, 3)
            bundle = execute_turn(copy.deepcopy(ALPHA), request)
            candidate = make_relatte_candidate(ALPHA, bundle, "2026-10-07T22:10:00Z")

        self.assertTrue(gate["consumed"])
        self.assertTrue(bundle["result"]["proposal_only"])
        self.assertFalse(bundle["result"]["automatic_next_turn"])
        self.assertEqual(candidate["spec"]["schema"], "relatte.opaque-organ-spec/v0")
        self.assertFalse(candidate["claims"]["signed_crossing_created"])
        self.assertIsNone(candidate["claims"]["destination_disposition"])

    def test_json_line_decoder_requires_newline(self):
        frame = json.dumps(EDGE, sort_keys=True).encode()
        with self.assertRaisesRegex(Refuse, "end with newline"):
            decode_edge_frame(frame)

    def test_posix_tty_path_reads_exactly_one_edge(self):
        master_fd, slave_fd = pty.openpty()
        slave_path = os.ttyname(slave_fd)
        first = json.dumps(EDGE, sort_keys=True).encode() + b"\n"
        second_edge = copy.deepcopy(EDGE)
        second_edge["sequence"] = 2
        second = json.dumps(second_edge, sort_keys=True).encode() + b"\n"

        def writer():
            time.sleep(0.05)
            os.write(master_fd, first + second)

        thread = threading.Thread(target=writer)
        thread.start()
        try:
            observed = read_one_tty_frame(slave_path, baud=115200, timeout_seconds=2.0)
        finally:
            thread.join(timeout=2.0)
            os.close(master_fd)
            os.close(slave_fd)

        self.assertEqual(observed, normalize_edge(EDGE))
        self.assertEqual(observed["sequence"], 1)

    def test_invalid_ledger_refuses_instead_of_repairing_history(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = Path(td) / "edges.jsonl"
            ledger.write_text("not-json\n")
            with self.assertRaisesRegex(Refuse, "ledger contains invalid JSON"):
                claim_edge(copy.deepcopy(EDGE), ledger)


if __name__ == "__main__":
    unittest.main()
