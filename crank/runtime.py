"""CRANKNODE bounded-turn runtime.

CRANKNODE-001 established one explicit turn -> one bounded transformation ->
one local receipt -> stop. CRANKNODE-002 adds a replaceable external provider
process for proposal generation while preserving the same authority boundary.

The provider command is operator-owned registry configuration, never turn
payload data. It is invoked without a shell and receives/returns one JSON
message over stdio. A valid provider response proves only that the configured
provider process returned a protocol-conforming response; it does not by itself
prove model identity, remote service identity, or substantive correctness.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from typing import Any, Callable

REGISTRY_SCHEMA_V0 = "static-os.crank-capability-registry/v0"
REGISTRY_SCHEMA_V1 = "static-os.crank-capability-registry/v1"
REQUEST_SCHEMA = "static-os.crank-turn-request/v0"
RESULT_SCHEMA = "static-os.crank-turn-result/v0"
RECEIPT_SCHEMA = "static-os.crank-receipt/v0"
PROVIDER_BINDING_SCHEMA = "static-os.ai-provider-binding/v0"
PROVIDER_REQUEST_SCHEMA = "static-os.ai-provider-request/v0"
PROVIDER_RESPONSE_SCHEMA = "static-os.ai-provider-response/v0"

ALLOWED_SOURCES = {"human", "physical-input", "timer", "peer-node"}
FORBIDDEN_CHAIN_KEYS = {
    "next_turn",
    "next",
    "chain",
    "pipeline",
    "steps",
    "loop",
    "autonomous_continue",
}


class Refuse(ValueError):
    """Raised when a requested turn would weaken the CRANKNODE boundary."""


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


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


def _validate_provider(provider: Any) -> dict[str, Any]:
    _require(isinstance(provider, dict), "external-provider requires provider binding")
    _require(
        provider.get("schema") == PROVIDER_BINDING_SCHEMA,
        "unsupported provider binding schema",
    )
    _require(provider.get("transport") == "stdio-json", "provider transport must be stdio-json")
    _require(
        isinstance(provider.get("provider_id"), str) and provider["provider_id"],
        "provider_id required",
    )
    _require(
        isinstance(provider.get("model_id"), str) and provider["model_id"],
        "model_id required",
    )
    command = provider.get("command")
    _require(
        isinstance(command, list)
        and command
        and all(isinstance(part, str) and part for part in command),
        "provider command must be a non-empty argv list",
    )
    timeout = provider.get("timeout_seconds")
    _require(
        isinstance(timeout, int)
        and not isinstance(timeout, bool)
        and 1 <= timeout <= 30,
        "provider timeout_seconds must be 1..30",
    )
    _require(
        provider.get("operator_configured") is True,
        "provider binding must be explicitly operator-configured",
    )
    return provider


def _validate_registry(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    _require(isinstance(registry, dict), "registry must be an object")
    schema = registry.get("schema")
    _require(
        schema in {REGISTRY_SCHEMA_V0, REGISTRY_SCHEMA_V1},
        "unsupported capability registry schema",
    )
    capabilities = registry.get("capabilities")
    _require(isinstance(capabilities, list) and capabilities, "registry requires capabilities")

    by_id: dict[str, dict[str, Any]] = {}
    for capability in capabilities:
        _require(isinstance(capability, dict), "capability must be an object")
        capability_id = capability.get("id")
        _require(isinstance(capability_id, str) and capability_id, "capability id required")
        _require(capability_id not in by_id, "duplicate capability id")
        handler = capability.get("handler")
        _require(handler in HANDLERS or handler == "external-provider", f"unknown handler for {capability_id}")
        if handler == "external-provider":
            _require(schema == REGISTRY_SCHEMA_V1, "external-provider requires registry v1")
            _validate_provider(capability.get("provider"))
        elif "provider" in capability:
            raise Refuse("provider binding only belongs to external-provider capability")

        cost = capability.get("cost_units")
        _require(
            isinstance(cost, int) and not isinstance(cost, bool) and cost >= 0,
            "cost_units must be a non-negative integer",
        )
        _require(
            isinstance(capability.get("proposal_only"), bool),
            "proposal_only must be boolean",
        )
        _require(
            capability.get("authority") == "none",
            "capability cannot manufacture authority",
        )
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


def _validate_request(
    request: dict[str, Any],
    by_id: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    _require(isinstance(request, dict), "turn request must be an object")
    _reject_chain_keys(request)
    _require(request.get("schema") == REQUEST_SCHEMA, "unsupported turn request schema")
    _require(
        isinstance(request.get("turn_id"), str) and request["turn_id"],
        "turn_id required",
    )

    source = request.get("source")
    _require(isinstance(source, dict), "source required")
    _require(source.get("kind") in ALLOWED_SOURCES, "unsupported turn source kind")
    _require(
        isinstance(source.get("id"), str) and source["id"],
        "source id required",
    )

    selected = request.get("selected_capability")
    _require(
        isinstance(selected, str),
        "exactly one selected_capability string is required",
    )
    _require(selected in by_id, "selected capability is not registered")

    budget = request.get("budget_units")
    _require(
        isinstance(budget, int)
        and not isinstance(budget, bool)
        and budget >= 0,
        "budget_units must be a non-negative integer",
    )
    _require(
        request.get("authority_request") == "none",
        "a turn cannot request authority",
    )
    _require(
        request.get("admission_request") == "none",
        "a turn cannot request admission",
    )
    _require(isinstance(request.get("payload"), dict), "payload must be an object")

    capability = by_id[selected]
    _require(
        budget >= capability["cost_units"],
        "insufficient declared work budget",
    )
    return capability


def _hash_text(payload: dict[str, Any]) -> dict[str, Any]:
    text = payload.get("text")
    _require(isinstance(text, str), "hash-text requires payload.text")
    encoded = text.encode("utf-8")
    return {"sha256": hashlib.sha256(encoded).hexdigest(), "bytes": len(encoded)}


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


def _external_provider(
    capability: dict[str, Any],
    payload: dict[str, Any],
    turn_id: str,
) -> dict[str, Any]:
    prompt = payload.get("prompt")
    _require(isinstance(prompt, str) and prompt, "external-provider requires payload.prompt")
    provider = _validate_provider(capability.get("provider"))

    provider_request = {
        "schema": PROVIDER_REQUEST_SCHEMA,
        "turn_id": turn_id,
        "prompt": prompt,
        "proposal_only": True,
        "authority_request": "none",
        "admission_request": "none",
    }
    try:
        completed = subprocess.run(
            provider["command"],
            input=json.dumps(provider_request, sort_keys=True) + "\n",
            text=True,
            capture_output=True,
            timeout=provider["timeout_seconds"],
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Refuse(f"provider process failed: {exc}") from exc

    _require(completed.returncode == 0, "provider process returned nonzero")
    _require(not completed.stderr.strip(), "provider wrote to stderr")

    try:
        response = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Refuse("provider returned invalid JSON") from exc

    _require(isinstance(response, dict), "provider response must be an object")
    _reject_chain_keys(response, "$provider_response")
    _require(
        set(response) == {
            "schema",
            "provider_id",
            "model_id",
            "proposal",
            "model_execution_claim",
        },
        "provider response fields changed",
    )
    _require(
        response.get("schema") == PROVIDER_RESPONSE_SCHEMA,
        "unsupported provider response schema",
    )
    _require(
        response.get("provider_id") == provider["provider_id"],
        "provider identity mismatch",
    )
    _require(
        response.get("model_id") == provider["model_id"],
        "provider model identity mismatch",
    )
    _require(
        isinstance(response.get("proposal"), str) and response["proposal"],
        "provider proposal required",
    )
    _require(
        isinstance(response.get("model_execution_claim"), str)
        and response["model_execution_claim"],
        "provider execution claim required",
    )

    return {
        "proposal": response["proposal"],
        "proposal_only": True,
        "model_execution": "external-provider-process-returned-valid-response",
        "provider": {
            "provider_id": provider["provider_id"],
            "model_id": provider["model_id"],
            "transport": "stdio-json",
            "request_sha256": digest(provider_request),
            "response_sha256": digest(response),
            "provider_attestation": response["model_execution_claim"],
            "provider_attestation_independently_verified": False,
        },
    }


def execute_turn(
    registry: dict[str, Any],
    request: dict[str, Any],
) -> dict[str, Any]:
    """Execute exactly one selected capability and return result plus durable receipt."""
    by_id = _validate_registry(registry)
    capability = _validate_request(request, by_id)
    selected = request["selected_capability"]

    request_hash = digest(request)
    input_hash = digest(request["payload"])
    if capability["handler"] == "external-provider":
        output = _external_provider(capability, request["payload"], request["turn_id"])
    else:
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
