"""Build a reLATTE opaque-organ donor spec from one verified CRANKNODE turn.

This module does not sign, transport, receive, HOLD, ADMIT, REFUSE, or RETURN.
It emits the exact donor-side relatte.opaque-organ-spec/v0 structure owned by
reLATTE R14 so the canonical reLATTE implementation can perform those acts.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .runtime import (
    RECEIPT_SCHEMA,
    RESULT_SCHEMA,
    Refuse,
    digest,
)

CANDIDATE_SCHEMA = "static-os.relatte-crossing-candidate/v0"
RELATTE_SPEC_SCHEMA = "relatte.opaque-organ-spec/v0"

RELATTE_OWNER = {
    "repository": "the-static-collective/reLATTE",
    "commit": "dcc8cdca84c440aa4294134f020fb7095bf87f24",
    "organ_path": "src/organ.ts",
    "organ_blob_sha": "f53e3b8bb2cb2770ad6803ed0ff4287b103ae0ca",
    "roundtrip_path": "src/roundtrip.ts",
    "roundtrip_blob_sha": "c459106d60f0760dd065bf1d158834b8cab20238",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Refuse(message)


def _timestamp(value: str) -> str:
    _require(isinstance(value, str) and value, "candidate created_at required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise Refuse("candidate created_at must be ISO-8601") from exc
    _require(parsed.tzinfo is not None, "candidate created_at must include timezone")
    return value


def _verify_turn_bundle(bundle: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(isinstance(bundle, dict), "turn bundle must be an object")
    _require(set(bundle) == {"result", "receipt"}, "turn bundle fields changed")
    result = bundle.get("result")
    receipt = bundle.get("receipt")
    _require(isinstance(result, dict), "turn result required")
    _require(isinstance(receipt, dict), "turn receipt required")
    _require(result.get("schema") == RESULT_SCHEMA, "unsupported turn result schema")
    _require(receipt.get("schema") == RECEIPT_SCHEMA, "unsupported turn receipt schema")
    _require(result.get("turn_id") == receipt.get("turn_id"), "turn id mismatch")
    _require(
        result.get("capability_id") == receipt.get("capability_id"),
        "capability mismatch",
    )
    _require(
        receipt.get("result_sha256") == digest(result),
        "receipt does not bind exact turn result",
    )
    receipt_without_hash = dict(receipt)
    stored_receipt_hash = receipt_without_hash.pop("receipt_sha256", None)
    _require(
        stored_receipt_hash == digest(receipt_without_hash),
        "receipt self-address mismatch",
    )
    _require(result.get("proposal_only") is True, "crossing candidate requires proposal-only result")
    _require(receipt.get("proposal_only") is True, "crossing candidate requires proposal-only receipt")
    _require(result.get("authority_effect") == "none", "result authority effect must remain none")
    _require(receipt.get("authority_effect") == "none", "receipt authority effect must remain none")
    _require(result.get("admission_effect") == "none", "result admission effect must remain none")
    _require(receipt.get("admission_effect") == "none", "receipt admission effect must remain none")
    _require(
        result.get("automatic_next_turn") is False
        and receipt.get("automatic_next_turn") is False,
        "candidate cannot arise from automatic continuation",
    )
    output = result.get("output")
    _require(isinstance(output, dict), "proposal output required")
    _require(isinstance(output.get("proposal"), str) and output["proposal"], "proposal text required")
    _require(output.get("proposal_only") is True, "provider proposal must remain proposal-only")
    return result, receipt


def make_relatte_candidate(
    registry: dict[str, Any],
    bundle: dict[str, Any],
    created_at: str,
) -> dict[str, Any]:
    result, receipt = _verify_turn_bundle(bundle)
    _require(isinstance(registry, dict), "registry required")
    node_id = registry.get("node_id")
    _require(isinstance(node_id, str) and node_id, "registry node_id required")

    result_hash = digest(result)
    receipt_bytes_hash = digest(receipt)
    receipt_id = receipt["receipt_sha256"]
    output = result["output"]
    provider = output.get("provider")
    provider_claims = {
        "provider_process_executed": isinstance(provider, dict),
        "provider_attestation_independently_verified": (
            provider.get("provider_attestation_independently_verified", False)
            if isinstance(provider, dict)
            else False
        ),
        "model_inference_independently_verified": False,
    }

    spec = {
        "schema": RELATTE_SPEC_SCHEMA,
        "family_ref": "static-os.cranknode/v0",
        "donor_contract_ref": "static-os:CRANKNODE-002",
        "artifact_kind": "CRANK_TURN_PROPOSAL",
        "source_world": node_id,
        "source_particular": f"static-os-crank-result-v0:{result_hash}",
        "source_history_head": f"static-os-crank-receipt-v0:{receipt_id}",
        "payload_refs": [
            {
                "address": f"sha256:{result_hash}",
                "role": "turn-result",
                "media_type": "application/json",
            },
            {
                "address": f"sha256:{receipt_bytes_hash}",
                "role": "turn-receipt",
                "media_type": "application/json",
            },
        ],
        "donor_claims": {
            "turn_id": result["turn_id"],
            "capability_id": result["capability_id"],
            "crank_receipt_id": receipt_id,
            "proposal_only": True,
            "automatic_next_turn": False,
            "authority_effect": "none",
            "admission_effect": "none",
            **provider_claims,
        },
        "requested_effect": {
            "kind": "PRESENT_FOR_LOCAL_REVIEW",
            "automatic_execution": False,
            "automatic_admission": False,
        },
        "return_address": None,
        "created_at": _timestamp(created_at),
    }

    candidate_without_hash = {
        "schema": CANDIDATE_SCHEMA,
        "owner": dict(RELATTE_OWNER),
        "spec": spec,
        "claims": {
            "signed_crossing_created": False,
            "transport_executed": False,
            "destination_received": False,
            "destination_disposition": None,
            "candidate_is_authority": False,
        },
        "laws": [
            "COMPUTATION != CROSSING",
            "CANDIDATE != SIGNED CROSSING",
            "PROPOSAL != ADMISSION",
            "PROVIDER ATTESTATION != INDEPENDENT VERIFICATION",
            "DONOR SEMANTICS != SUBSTRATE SEMANTICS",
            "ADAPTER != DONOR AUTHORITY",
            "DESTINATION MEANING REMAINS LOCAL",
        ],
    }
    return {
        **candidate_without_hash,
        "candidate_sha256": digest(candidate_without_hash),
    }
