"""CRANKNODE-001: one explicit turn, one bounded transformation, one receipt.

This module deliberately has no scheduler, daemon, network client, model client,
or recursive dispatcher. Capability visibility is inert. A caller must select one
registered capability for each invocation of execute_turn().
"""
from __future__ import annotations

import hashlib
import json
from typing import Any, Callable

REGISTRY_SCHEMA = "static-os.crank-capability-registry/v0"
REQUEST_SCHEMA = "static-os.crank-turn-request/v0"
RESULT_SCHEMA = "static-os.crank-turn-result/v0"
RECEIPT_SCHEMA = "static-os.crank-receipt/v0"

ALLOWED_SOURCES = {"human", "physical-input", "timer", "peer-node"}
FORBIDDEN_CHAIN_KEYS = {"next_turn", "next", "chain", "pipeline", "steps", "loop", "autonomous_continue"}


class Refuse(ValueError):
    """Raised when a requested turn would weaken the CRANKNODE boundary."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Refuse(message)


def _reject_chain_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_CHAIN_KEYS:
                raise Refuse(f"hidden chaining key refused at {path}.{key}")
            _reject_chain_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_chain_keys(child, f"{path}[{index}]")


def _validate_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _require(isinstance(registry, dict), "registry must be an object")
    _require(registry.get("schema") == REGISTRY_SCHEMA, "unsupported capability registry schema")
    capabilities = registry.get("capabilities")
    _require(isinstance(capabilities, list) and capabilities, "registry requires capabilities")

    by_id: dict[str, dict[str, Any]] = {}
    for capability in capabilities:
        _require(isinstance(capability, dict), "capability must be an object")
        capability_id = capability.get("id")
        _require(isinstance(capability_id, str) and capability_id, "capability id required")
        _require(capability_id not in by_id, "duplicate capability id")
        _require(capability.get("handler") in HANDLERS, f"unknown handler for {capability_id}")
        cost = capability.get("cost_units")
        _require(isinstance(cost, int) and not isinstance(cost, bool) and cost >= 0, "cost_units must be a non-negative integer")
        _require(isinstance(capability.get("proposal_only"), bool), "proposal_only must be boolean")
        _require(capability.get("authority") == "none", "capability cannot manufacture authority")
        by_id[capability_id] = capability
    return by_id


def list_capabilities(registry: dict[str, Any]) -> list[dict[str, Any]]:
    """Return inert capability cards. Listing performs no work and emits no receipt."""
    by_id = _validate_registry(registry)
    return [
        {
            "id": cap_id,
            "description": by_id[cap_id].get("description", ""),
            "cost_units": by_id[cap_id]["cost_units"],
            "proposal_only": by_id[cap_id]["proposal_only"],
        }
        for cap_id in sorted(by_id)
    ]


def _validate_request(request: dict[str, Any], by_id: dict[str, dict[str, Any]]) -> dict[str, Any]:
    _require(isinstance(request, dict), "turn request must be an object")
    _reject_chain_keys(request)
    _require(request.get("schema") == REQUEST_SCHEMA, "unsupported turn request schema")
    _require(isinstance(request.get("turn_id"), str) and request["turn_id"], "turn_id required")

    source = request.get("source")
    _require(isinstance(source, dict), "source required")
    _require(source.get("kind") in ALLOWED_SOURCES, "unsupported turn source kind")
    _require(isinstance(source.get("id"), str) and source["id"], "source id required")

    selected = request.get("selected_capability")
    _require(isinstance(selected, str), "exactly one selected_capability string is required")
    _require(selected in by_id, "selected capability is not registered")

    budget = request.get("budget_units")
    _require(isinstance(budget, int) and not isinstance(budget, bool) and budget >= 0, "budget_units must be a non-negative integer")
    _require(request.get("authority_request") == "none", "a turn cannot request authority")
    _require(request.get("admission_request") == "none", "a turn cannot request admission")
    _require(isinstance(request.get("payload"), dict), "payload must be an object")

    capability = by_id[selected]
    _require(budget >= capability["cost_units"], "insufficient declared work budget")
    return capability


def _hash_text(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    _require(isinstance(text, str), "hash-text requires payload.text")
    return {"sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(), "bytes": len(text.encode("utf-8"))}


def _uppercase_text(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    _require(isinstance(text, str), "uppercase-text requires payload.text")
    return {"text": text.upper()}


def _proposal_echo(payload: dict[str, Any]) -> dict[str, Any]:
    prompt = payload.get("prompt")
    _require(isinstance(prompt, str) and prompt, "proposal-echo requires payload.prompt")
    return {
        "proposal": prompt,
        "proposal_only": True,
        "model_execution": "not-performed-placeholder-seam",
    }


HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "hash-text": _hash_text,
    "uppercase-text": _uppercase_text,
    "proposal-echo": _proposal_echo,
}


def execute_turn(registry: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Execute exactly one selected capability and return result plus durable receipt."""
    by_id = _validate_registry(registry)
    capability = _validate_request(request, by_id)
    selected = request["selected_capability"]

    request_hash = digest(request)
    input_hash = digest(request["payload"])
    output = HANDLERS[capability["handler"]](request["payload"])

    result = {
        "schema": RESULT_SCHEMA,
        "turn_id": request["turn_id"],
        "capability_id": selected,
        "output": output,
        "proposal_only": capability["proposal_only"],
        "authority_effect": "none",
        "admission_effect": "none",
        "automatic_next_turn": False,
    }
    result_hash = digest(result)

    cost = capability["cost_units"]
    receipt_without_hash = {
        "schema": RECEIPT_SCHEMA,
        "turn_id": request["turn_id"],
        "source": request["source"],
        "capability_id": selected,
        "request_sha256": request_hash,
        "input_sha256": input_hash,
        "result_sha256": result_hash,
        "budget": {
            "declared_units": request["budget_units"],
            "cost_units": cost,
            "remaining_units": request["budget_units"] - cost,
            "authority_effect": "none",
        },
        "proposal_only": capability["proposal_only"],
        "authority_effect": "none",
        "admission_effect": "none",
        "transport_effect": "none",
        "automatic_next_turn": False,
        "carrier_profile": "canonical-json-utf8",
        "signature_status": "unsigned-local-receipt",
        "laws": [
            "TURN != LOOP",
            "WORK != AUTHORITY",
            "COMPUTATION != ADMISSION",
            "INFERENCE != DECISION",
            "AVAILABLE != SELECTED",
            "SELECTED != EXECUTED",
            "EXECUTED != ACCEPTED",
            "NODE != NETWORK",
            "TRANSPORT != TRUST",
            "OFFLINE != DEAD",
            "PAPER != LOSSY FALLBACK",
            "HUMAN TURN != HUMAN APPROVAL",
            "ENERGY != AUTHORITY",
        ],
    }
    receipt = dict(receipt_without_hash)
    receipt["receipt_sha256"] = digest(receipt_without_hash)

    return {"result": result, "receipt": receipt}
