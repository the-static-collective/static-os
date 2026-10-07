import copy
import json
import unittest
from pathlib import Path

from crank.runtime import Refuse, digest, execute_turn, list_capabilities

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = json.loads((ROOT / "fixtures" / "cranknode-001" / "capabilities.json").read_text(encoding="utf-8"))
REQUEST = json.loads((ROOT / "fixtures" / "cranknode-001" / "turn.json").read_text(encoding="utf-8"))


class CrankNode001Tests(unittest.TestCase):
    def test_listing_is_inert(self):
        cards = list_capabilities(copy.deepcopy(REGISTRY))
        self.assertEqual([card["id"] for card in cards], ["AI.PROPOSE", "TEXT.HASH", "TEXT.UPPERCASE"])
        self.assertTrue(all("receipt" not in card for card in cards))

    def test_founding_turn_executes_exactly_one_bounded_capability(self):
        bundle = execute_turn(copy.deepcopy(REGISTRY), copy.deepcopy(REQUEST))
        self.assertEqual(bundle["result"]["capability_id"], "AI.PROPOSE")
        self.assertTrue(bundle["result"]["proposal_only"])
        self.assertFalse(bundle["result"]["automatic_next_turn"])
        self.assertEqual(bundle["receipt"]["authority_effect"], "none")
        self.assertEqual(bundle["receipt"]["admission_effect"], "none")
        self.assertEqual(bundle["receipt"]["transport_effect"], "none")
        self.assertEqual(bundle["receipt"]["budget"]["remaining_units"], 1)

    def test_receipt_binds_exact_request_and_result(self):
        bundle = execute_turn(copy.deepcopy(REGISTRY), copy.deepcopy(REQUEST))
        self.assertEqual(bundle["receipt"]["request_sha256"], digest(REQUEST))
        self.assertEqual(bundle["receipt"]["result_sha256"], digest(bundle["result"]))
        receipt = copy.deepcopy(bundle["receipt"])
        receipt_hash = receipt.pop("receipt_sha256")
        self.assertEqual(receipt_hash, digest(receipt))

    def test_payload_mutation_changes_receipt_address(self):
        first = execute_turn(copy.deepcopy(REGISTRY), copy.deepcopy(REQUEST))
        changed = copy.deepcopy(REQUEST)
        changed["payload"]["prompt"] += " Changed."
        second = execute_turn(copy.deepcopy(REGISTRY), changed)
        self.assertNotEqual(first["receipt"]["request_sha256"], second["receipt"]["request_sha256"])
        self.assertNotEqual(first["receipt"]["receipt_sha256"], second["receipt"]["receipt_sha256"])

    def test_refuses_hidden_next_turn(self):
        request = copy.deepcopy(REQUEST)
        request["payload"]["next_turn"] = {"selected_capability": "TEXT.HASH"}
        with self.assertRaisesRegex(Refuse, "hidden chaining key"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_refuses_pipeline_disguised_as_payload(self):
        request = copy.deepcopy(REQUEST)
        request["payload"]["pipeline"] = [{"capability": "TEXT.HASH"}, {"capability": "TEXT.UPPERCASE"}]
        with self.assertRaisesRegex(Refuse, "hidden chaining key"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_refuses_multiple_selected_capabilities(self):
        request = copy.deepcopy(REQUEST)
        request["selected_capability"] = ["TEXT.HASH", "TEXT.UPPERCASE"]
        with self.assertRaisesRegex(Refuse, "exactly one"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_refuses_insufficient_budget(self):
        request = copy.deepcopy(REQUEST)
        request["budget_units"] = 1
        with self.assertRaisesRegex(Refuse, "insufficient"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_budget_cannot_buy_authority(self):
        request = copy.deepcopy(REQUEST)
        request["budget_units"] = 999999
        request["authority_request"] = "ADMIT"
        with self.assertRaisesRegex(Refuse, "cannot request authority"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_computation_cannot_request_admission(self):
        request = copy.deepcopy(REQUEST)
        request["admission_request"] = "ADMIT"
        with self.assertRaisesRegex(Refuse, "cannot request admission"):
            execute_turn(copy.deepcopy(REGISTRY), request)

    def test_physical_input_is_a_turn_source_not_authority(self):
        request = copy.deepcopy(REQUEST)
        request["source"] = {"kind": "physical-input", "id": "rotary-encoder:test-001"}
        bundle = execute_turn(copy.deepcopy(REGISTRY), request)
        self.assertEqual(bundle["receipt"]["source"]["kind"], "physical-input")
        self.assertEqual(bundle["receipt"]["authority_effect"], "none")

    def test_refuses_unregistered_handler(self):
        registry = copy.deepcopy(REGISTRY)
        registry["capabilities"][0]["handler"] = "shell-anything"
        with self.assertRaisesRegex(Refuse, "unknown handler"):
            list_capabilities(registry)

    def test_ai_seam_is_explicitly_not_a_live_model_claim(self):
        bundle = execute_turn(copy.deepcopy(REGISTRY), copy.deepcopy(REQUEST))
        self.assertEqual(bundle["result"]["output"]["model_execution"], "not-performed-placeholder-seam")
        self.assertTrue(bundle["result"]["output"]["proposal_only"])


if __name__ == "__main__":
    unittest.main()
