"""KETTLENODE-001 — fail-closed, source-attested energy accounting.

This is an energy *allowance*, NOT proof that a kettle or battery supplied power.
A sample never chooses or runs a capability. A separately selected human turn
spends its configured allowance once, durably before execution.
"""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .runtime import Refuse, digest, execute_turn

SAMPLE_SCHEMA = "static-os.kettlenode-energy-sample/v0"
POLICY_SCHEMA = "static-os.kettlenode-policy/v0"
STATE_SCHEMA = "static-os.kettlenode-ledger/v0"
RESERVATION_SCHEMA = "static-os.kettlenode-reservation/v0"
KINDS = {"simulation", "meter-reported-unverified"}
MAX_ENERGY = 10**12


def require(condition: bool, message: str) -> None:
    if not condition:
        raise Refuse(message)


def natural(value: Any, name: str, *, positive: bool = False) -> int:
    require(type(value) is int and (value > 0 if positive else value >= 0)
            and value <= MAX_ENERGY, f"{name} must be a bounded integer")
    return value


def validate_policy(policy: Any) -> dict[str, Any]:
    require(isinstance(policy, dict) and set(policy) == {
        "schema", "source_id", "session_id", "observation_kind",
        "max_increment_mj", "min_reserve_mj", "capability_allowances_mj",
    }, "policy fields changed")
    require(policy["schema"] == POLICY_SCHEMA, "unsupported policy schema")
    for key in ("source_id", "session_id"):
        require(isinstance(policy[key], str) and bool(policy[key]), f"{key} required")
    require(policy["observation_kind"] in KINDS, "unsupported observation kind")
    natural(policy["max_increment_mj"], "max_increment_mj", positive=True)
    natural(policy["min_reserve_mj"], "min_reserve_mj")
    costs = policy["capability_allowances_mj"]
    require(isinstance(costs, dict) and bool(costs), "cost map required")
    for capability, cost in costs.items():
        require(isinstance(capability, str) and bool(capability), "capability id required")
        natural(cost, "capability allowance", positive=True)
    return policy


def normalize_sample(sample: Any, policy: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(sample, dict) and set(sample) == {
        "schema", "source_id", "session_id", "sequence",
        "cumulative_millijoules", "observation_kind",
    }, "energy sample fields changed")
    require(sample["schema"] == SAMPLE_SCHEMA, "unsupported sample schema")
    for key in ("source_id", "session_id", "observation_kind"):
        require(sample[key] == policy[key], f"sample {key} mismatch")
    natural(sample["sequence"], "sample sequence")
    natural(sample["cumulative_millijoules"], "cumulative_millijoules")
    return dict(sample)


def _checked(state: Any, policy: dict[str, Any]) -> dict[str, Any]:
    require(isinstance(state, dict) and set(state) == {
        "schema", "policy_sha256", "sequence", "cumulative_mj",
        "available_mj", "turns", "state_sha256",
    }, "ledger fields changed")
    body = {k: v for k, v in state.items() if k != "state_sha256"}
    require(state["state_sha256"] == digest(body), "ledger state hash mismatch")
    require(state["schema"] == STATE_SCHEMA, "unsupported ledger schema")
    require(state["policy_sha256"] == digest(policy), "policy changed within session")
    natural(state["sequence"], "ledger sequence")
    natural(state["cumulative_mj"], "ledger cumulative_mj")
    natural(state["available_mj"], "ledger available_mj")
    require(state["available_mj"] <= state["cumulative_mj"], "ledger allowance exceeds input")
    require(isinstance(state["turns"], list), "ledger turns malformed")
    ids = []
    for t in state["turns"]:
        require(isinstance(t, dict) and set(t) == {
            "schema", "turn_id", "request_sha256", "cost_mj", "available_after_mj",
            "execution_proven", "actual_consumption_metered", "automatic_retry",
            "reservation_sha256",
        }, "ledger reservation fields changed")
        b = {k: v for k, v in t.items() if k != "reservation_sha256"}
        require(t["reservation_sha256"] == digest(b), "reservation hash mismatch")
        require(t["schema"] == RESERVATION_SCHEMA, "reservation schema mismatch")
        require(isinstance(t["turn_id"], str) and bool(t["turn_id"]), "turn id required")
        require(isinstance(t["request_sha256"], str) and len(t["request_sha256"]) == 64,
                "request hash malformed")
        natural(t["cost_mj"], "reserved allowance", positive=True)
        natural(t["available_after_mj"], "remaining allowance")
        require(t["execution_proven"] is False and
                t["actual_consumption_metered"] is False and
                t["automatic_retry"] is False, "reservation claims exceed evidence")
        ids.append(t["turn_id"])
    require(len(ids) == len(set(ids)), "duplicate turn ids in ledger")
    require(state["available_mj"] + sum(t["cost_mj"] for t in state["turns"])
            == state["cumulative_mj"], "ledger accounting imbalance")
    return state


@contextmanager
def _locked(path: Path) -> Iterator[None]:
    path.parent.mkdir(parents=True, exist_ok=True)
    with (path.with_name(path.name + ".lock")).open("a+b") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


def _read(path: Path, policy: dict[str, Any]) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise Refuse("ledger unreadable; refuse rather than repair") from exc
    return _checked(state, policy)


def _write(path: Path, body: dict[str, Any]) -> dict[str, Any]:
    state = dict(body)
    state["state_sha256"] = digest(body)
    tmp = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                         dir=path.parent, prefix=".kettlenode-",
                                         delete=False) as handle:
            tmp = Path(handle.name)
            json.dump(state, handle, sort_keys=True, separators=(",", ":"))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if tmp is not None and tmp.exists():
            tmp.unlink()
    return state


def observe(sample: Any, ledger: str | Path, policy: Any) -> dict[str, Any]:
    """Register one source-attested cumulative observation; execute NO work."""
    policy = validate_policy(policy)
    sample = normalize_sample(sample, policy)
    path = Path(ledger)
    with _locked(path):
        state = _read(path, policy)
        if state is None:
            require(sample["sequence"] == 0 and sample["cumulative_millijoules"] == 0,
                    "fresh session requires zero baseline at sequence 0")
            return _write(path, {
                "schema": STATE_SCHEMA, "policy_sha256": digest(policy),
                "sequence": 0, "cumulative_mj": 0, "available_mj": 0, "turns": [],
            })
        require(sample["sequence"] == state["sequence"] + 1,
                "sample replay, gap, or reordering refused")
        total = sample["cumulative_millijoules"]
        require(total >= state["cumulative_mj"], "cumulative energy decreased")
        delta = total - state["cumulative_mj"]
        require(delta <= policy["max_increment_mj"], "energy increment exceeds policy")
        require(state["available_mj"] + delta <= MAX_ENERGY, "allowance overflow")
        updated = {k: v for k, v in state.items() if k != "state_sha256"}
        updated.update(sequence=sample["sequence"], cumulative_mj=total,
                       available_mj=state["available_mj"] + delta)
        return _write(path, updated)


def inspect(ledger: str | Path, policy: Any) -> dict[str, Any] | None:
    policy = validate_policy(policy)
    path = Path(ledger)
    with _locked(path):
        return _read(path, policy)


def reserve(ledger: str | Path, policy: Any, request: Any) -> dict[str, Any]:
    """Spend allowance before invoking a separately chosen operator turn."""
    policy = validate_policy(policy)
    require(isinstance(request, dict), "request must be an object")
    require(request.get("schema") == "static-os.crank-turn-request/v0",
            "unsupported request schema")
    source = request.get("source")
    require(isinstance(source, dict) and source.get("kind") == "human"
            and isinstance(source.get("id"), str) and bool(source["id"]),
            "KETTLENODE-001 requires an explicit human-selected turn")
    turn_id = request.get("turn_id")
    require(isinstance(turn_id, str) and bool(turn_id), "turn id required")
    cap = request.get("selected_capability")
    require(isinstance(cap, str) and cap in policy["capability_allowances_mj"],
            "capability not operator-funded")
    cost = policy["capability_allowances_mj"][cap]
    path = Path(ledger)
    with _locked(path):
        state = _read(path, policy)
        require(state is not None, "no energy baseline observed")
        require(all(t["turn_id"] != turn_id for t in state["turns"]),
                "turn already reserved; automatic retry refused")
        require(state["available_mj"] >= cost + policy["min_reserve_mj"],
                "insufficient reported-energy allowance")
        receipt = {
            "schema": RESERVATION_SCHEMA, "turn_id": turn_id,
            "request_sha256": digest(request), "cost_mj": cost,
            "available_after_mj": state["available_mj"] - cost,
            "execution_proven": False, "actual_consumption_metered": False,
            "automatic_retry": False,
        }
        receipt["reservation_sha256"] = digest(receipt)
        updated = {k: v for k, v in state.items() if k != "state_sha256"}
        updated["available_mj"] -= cost
        updated["turns"] = state["turns"] + [receipt]
        _write(path, updated)
        return receipt


def attempt_turn(ledger: str | Path, policy: Any,
                 registry: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """One reservation then one ordinary CRANKNODE attempt; no automatic retries.

    The returned result is runtime evidence, not physical watt-hour evidence.
    A crash after reserve leaves a spent allowance and no success claim.
    """
    receipt = reserve(ledger, policy, request)
    bundle = execute_turn(registry, request)
    return {
        "schema": "static-os.kettlenode-turn-outcome/v0",
        "reservation": receipt,
        "crank": bundle,
        "claims": {
            "actual_consumption_metered": False,
            "heat_source_physically_observed": False,
            "signed_relatte_crossing_created": False,
            "automatic_next_turn": False,
        },
    }
