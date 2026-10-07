import copy
import json
import unittest
from pathlib import Path

from crank.relatte_candidate import RELATTE_OWNER, make_relatte_candidate
from crank.runtime import Refuse, execute_turn

ROOT = Path(__file__).resolve().parents[1]
ALPHA = json.loads((ROOT / "fixtures" / "cranknode-002" / "capabilities-alpha.json").read_text())
BETA = json.loads((ROOT / "fixtures" / "cranknode-002" / "capabilities-beta.json").read_text())
TURN = json.loads((ROOT / "fixtures" / "cranknode-002" / "turn.json").read_text())


class CrankNode002Tests(unittest.TestCase):
    def test_external_provider_process_executes_one_proposal(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        output = bundle["result"]["output"]
        self.assertEqual(output["provider"]["provider_id"], "fixture-alpha")
        self.assertEqual(output["provider"]["model_id"], "fixture-alpha-v1")
        self.assertTrue(output["proposal"].startswith("ALPHA proposes"))
        self.assertTrue(output["proposal_only"])
        self.assertFalse(bundle["result"]["automatic_next_turn"])

    def test_provider_is_replaceable_without_changing_turn_contract(self):
        alpha = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        beta = execute_turn(copy.deepcopy(BETA), copy.deepcopy(TURN))
        self.assertEqual(alpha["result"]["capability_id"], "AI.PROPOSE")
        self.assertEqual(beta["result"]["capability_id"], "AI.PROPOSE")
        self.assertNotEqual(alpha["result"]["output"]["provider"]["provider_id"], beta["result"]["output"]["provider"]["provider_id"])
        self.assertNotEqual(alpha["result"]["output"]["proposal"], beta["result"]["output"]["proposal"])
        self.assertEqual(alpha["result"]["authority_effect"], "none")
        self.assertEqual(beta["result"]["authority_effect"], "none")

    def test_turn_payload_cannot_replace_provider_command(self):
        turn = copy.deepcopy(TURN)
        turn["payload"]["provider_command"] = ["python3", "somewhere-else.py"]
        bundle = execute_turn(copy.deepcopy(ALPHA), turn)
        self.assertEqual(bundle["result"]["output"]["provider"]["provider_id"], "fixture-alpha")

    def test_provider_identity_mismatch_is_refused(self):
        registry = copy.deepcopy(ALPHA)
        registry["capabilities"][0]["provider"]["provider_id"] = "not-alpha"
        with self.assertRaisesRegex(Refuse, "provider identity mismatch"):
            execute_turn(registry, copy.deepcopy(TURN))

    def test_hostile_provider_cannot_smuggle_next_turn(self):
        registry = copy.deepcopy(ALPHA)
        provider = registry["capabilities"][0]["provider"]
        provider["provider_id"] = "fixture-hostile"
        provider["model_id"] = "fixture-hostile-v1"
        provider["command"] = ["python3", "fixtures/cranknode-002/provider_hostile.py"]
        with self.assertRaisesRegex(Refuse, "hidden chaining key"):
            execute_turn(registry, copy.deepcopy(TURN))

    def test_fixture_provider_claim_is_not_independently_verified(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        provider = bundle["result"]["output"]["provider"]
        self.assertEqual(provider["provider_attestation"], "fixture-provider-executed-not-a-live-model")
        self.assertFalse(provider["provider_attestation_independently_verified"])

    def test_relatte_candidate_has_exact_opaque_organ_shape(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        candidate = make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00Z")
        spec = candidate["spec"]
        self.assertEqual(spec["schema"], "relatte.opaque-organ-spec/v0")
        self.assertEqual(
            set(spec),
            {
                "schema", "family_ref", "donor_contract_ref", "artifact_kind",
                "source_world", "source_particular", "source_history_head",
                "payload_refs", "donor_claims", "requested_effect",
                "return_address", "created_at",
            },
        )
        self.assertEqual(spec["artifact_kind"], "CRANK_TURN_PROPOSAL")
        self.assertEqual(spec["requested_effect"]["kind"], "PRESENT_FOR_LOCAL_REVIEW")
        self.assertFalse(spec["requested_effect"]["automatic_admission"])

    def test_candidate_is_explicitly_not_a_signed_crossing(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        candidate = make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00Z")
        self.assertFalse(candidate["claims"]["signed_crossing_created"])
        self.assertFalse(candidate["claims"]["transport_executed"])
        self.assertFalse(candidate["claims"]["destination_received"])
        self.assertIsNone(candidate["claims"]["destination_disposition"])
        self.assertFalse(candidate["claims"]["candidate_is_authority"])

    def test_candidate_pins_current_merged_relatte_owner(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        candidate = make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00Z")
        self.assertEqual(candidate["owner"], RELATTE_OWNER)
        self.assertEqual(RELATTE_OWNER["commit"], "dcc8cdca84c440aa4294134f020fb7095bf87f24")
        self.assertEqual(RELATTE_OWNER["organ_blob_sha"], "f53e3b8bb2cb2770ad6803ed0ff4287b103ae0ca")

    def test_mutated_result_is_refused_before_candidate(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        bundle["result"]["output"]["proposal"] = "mutated after receipt"
        with self.assertRaisesRegex(Refuse, "does not bind exact turn result"):
            make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00Z")

    def test_mutated_receipt_is_refused_before_candidate(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        bundle["receipt"]["authority_effect"] = "ADMIT"
        with self.assertRaises(Refuse):
            make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00Z")

    def test_non_proposal_result_cannot_become_proposal_crossing_candidate(self):
        registry = {
            "schema": "static-os.crank-capability-registry/v0",
            "node_id": "test-node",
            "capabilities": [{
                "id": "TEXT.HASH",
                "description": "hash",
                "handler": "hash-text",
                "cost_units": 1,
                "proposal_only": False,
                "authority": "none",
            }],
        }
        request = {
            "schema": "static-os.crank-turn-request/v0",
            "turn_id": "HASH-001",
            "source": {"kind": "human", "id": "test"},
            "selected_capability": "TEXT.HASH",
            "budget_units": 1,
            "authority_request": "none",
            "admission_request": "none",
            "payload": {"text": "hello"},
        }
        bundle = execute_turn(registry, request)
        with self.assertRaisesRegex(Refuse, "proposal-only"):
            make_relatte_candidate(registry, bundle, "2026-10-07T21:55:00Z")

    def test_candidate_timestamp_requires_timezone(self):
        bundle = execute_turn(copy.deepcopy(ALPHA), copy.deepcopy(TURN))
        with self.assertRaisesRegex(Refuse, "include timezone"):
            make_relatte_candidate(ALPHA, bundle, "2026-10-07T21:55:00")


if __name__ == "__main__":
    unittest.main()
