"""QUESTION-FIRST-SESSION-001 — one question, two candidate mechanisms, one owned action.

Deterministic founding question compilation is a *question generator*, not a
claim of live AI reasoning. The experiment runs an opted-in GHoT donor through
its native signed Instrument Rack. STATIC OS owns the session, the human gate,
and a durable PREPARED checkpoint that refuses ambiguous automatic retry.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from fractions import Fraction
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.gear_donor import FORWARD, INVERSE, SCHEMA as GEAR_SCHEMA

SEED = "static-os.question-seed/v0"
QUESTION = "static-os.question-first/v0"
SELECTION = "static-os.question-selection/v0"
STATE = "static-os.question-session-state/v0"
NEXT = "static-os.next-question-proposal/v0"
SOURCE = "MODERN_IDEALIZATION_NO_VERIFIED_LEONARDO_FOLIO"
ALLOWED = {FORWARD, INVERSE}
SAFE_OWNER = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")


class Hold(ValueError):
    """Bounded refusal / owner-local HOLD, not an automatic retry."""


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Hold(reason)


def _fraction(value: Fraction) -> dict[str, int]:
    return {"numerator": value.numerator, "denominator": value.denominator}


def _ratio(raw: Any) -> Fraction:
    require(isinstance(raw, dict) and set(raw) == {"numerator", "denominator"},
            "INVALID_RATIONAL_SHAPE")
    n, d = raw["numerator"], raw["denominator"]
    require(type(n) is int and type(d) is int and d > 0 and d <= 100000,
            "INVALID_RATIONAL_VALUE")
    return Fraction(n, d)


def _sealed(body: dict, field: str, prefix: str) -> dict:
    return {**body, field: prefix + digest(body)}


def _check_seal(value: Any, field: str, prefix: str) -> dict:
    require(isinstance(value, dict), "SEALED_OBJECT_REQUIRED")
    without = {k: v for k, v in value.items() if k != field}
    require(value.get(field) == prefix + digest(without), "CONTENT_ADDRESS_MISMATCH")
    return value


def validate_seed(value: Any) -> dict:
    require(isinstance(value, dict) and set(value) == {
        "schema", "source", "mechanism", "driver_teeth", "driven_teeth",
        "driver_turns", "claimed_driven_turns",
    }, "EXACT_QUESTION_SEED_REQUIRED")
    require(value["schema"] == SEED and value["source"] == SOURCE,
            "HISTORICAL_SOURCE_NOT_ATTESTED")
    require(value["mechanism"] == "two-external-spur-gears-ideal-no-slip",
            "UNKNOWN_MECHANISM_MODEL")
    for key, lower, upper in (
        ("driver_teeth", 4, 200), ("driven_teeth", 4, 200),
        ("driver_turns", -100, 100), ("claimed_driven_turns", -100, 100),
    ):
        require(type(value[key]) is int and lower <= value[key] <= upper,
                "INVALID_GEAR_SEED_" + key)
    return value


def _card(rack: Any, capability: str) -> dict:
    require(isinstance(rack, dict) and rack.get("schema") == "ghot.instrument-rack/v0",
            "NATIVE_GHOT_RACK_REQUIRED")
    cards = rack.get("cards")
    require(isinstance(cards, list), "NATIVE_GHOT_CARDS_REQUIRED")
    matches = [card for card in cards if isinstance(card, dict)
               and card.get("capability") == capability]
    require(len(matches) == 1, "GHOT_INSTRUMENT_NOT_UNAMBIGUOUS")
    card = matches[0]
    limits = card.get("limits")
    require(
        card.get("schema") == "ghot.instrument-card/v0"
        and card.get("available") is True
        and card.get("status") == "PROPOSAL_ONLY"
        and card.get("semantic_effect") == "none"
        and isinstance(card.get("card_id"), str)
        and isinstance(limits, dict)
        and limits.get("network") is False
        and limits.get("transmit") is False
        and limits.get("physical_effects") is False
        and limits.get("simulation_only") is True
        and limits.get("authority") == "none",
        "MISSING_SAFE_SIMULATION_CAPABILITY",
    )
    return card


def compile_question(seed: Any, rack: Any) -> dict:
    """Question comes from a bounded seed and actual donor offers; no effect."""
    s = validate_seed(seed)
    cards = {name: _card(rack, name) for name in sorted(ALLOWED)}
    forward = {
        "schema": GEAR_SCHEMA, "operation": "forward",
        "driver_teeth": s["driver_teeth"], "driven_teeth": s["driven_teeth"],
        "input_turns": s["driver_turns"],
    }
    inverse = {
        "schema": GEAR_SCHEMA, "operation": "inverse",
        "driver_teeth": s["driver_teeth"], "driven_teeth": s["driven_teeth"],
        "input_turns": s["claimed_driven_turns"],
    }
    candidates = [
        {
            "candidate_id": "simulate-forward",
            "capability": FORWARD, "card_id": cards[FORWARD]["card_id"],
            "input": forward,
            "expected": _fraction(Fraction(s["claimed_driven_turns"])),
            "measured_quantity": "driven_turns", "status": "PROPOSAL_ONLY",
        },
        {
            "candidate_id": "simulate-inverse",
            "capability": INVERSE, "card_id": cards[INVERSE]["card_id"],
            "input": inverse,
            "expected": _fraction(Fraction(s["driver_turns"])),
            "measured_quantity": "driver_turns", "status": "PROPOSAL_ONLY",
        },
    ]
    body = {
        "schema": QUESTION,
        "seed": s,
        "rack_id": rack["rack_id"],
        "question_text": (
            "Under an ideal no-slip external gear model, does the claimed "
            "driven motion agree with the declared driver motion and tooth counts?"
        ),
        "competing_hypotheses": [
            "IDEAL_GEAR_MODEL_MATCHES_CLAIM",
            "IDEAL_GEAR_MODEL_DIFFERS_FROM_CLAIM",
        ],
        "candidate_experiments": candidates,
        "generation": "DETERMINISTIC_QUESTION_COMPILER_NOT_AI_MODEL",
        "historical_source": "NO_VERIFIED_FOLIO_ATTACHED",
        "apparatus": "TWO_REPLACEABLE_GHOT_SOFTWARE_INSTRUMENTS",
        "reality_contact": False,
        "status": "QUESTION_OPEN",
        "automatic_execution": False,
        "authority": "none",
    }
    return _sealed(body, "question_id", "static-os-question-v0:")


def verify_question(question: Any, rack: Any) -> dict:
    q = _check_seal(question, "question_id", "static-os-question-v0:")
    require(q == compile_question(q.get("seed"), rack), "STALE_QUESTION_OR_INSTRUMENTS")
    return q


def validate_selection(question: dict, selection: Any) -> dict:
    require(isinstance(selection, dict) and set(selection) == {
        "schema", "question_id", "candidate_id", "card_id", "approved",
        "owner_id",
    }, "OWNER_SELECTION_REQUIRED")
    require(
        selection["schema"] == SELECTION and selection["approved"] is True
        and selection["question_id"] == question["question_id"]
        and isinstance(selection["owner_id"], str)
        and SAFE_OWNER.fullmatch(selection["owner_id"]) is not None,
        "OWNER_SELECTION_NOT_AUTHORIZED",
    )
    chosen = [candidate for candidate in question["candidate_experiments"]
              if candidate["candidate_id"] == selection["candidate_id"]
              and candidate["card_id"] == selection["card_id"]]
    require(len(chosen) == 1, "SELECTED_CANDIDATE_MISMATCH")
    return chosen[0]


def _ghot_request(ghot_root: Path, request: dict, *, timeout: int = 25) -> dict:
    script = ghot_root / "ghot" / "instrument_rack.py"
    require(script.is_file(), "GHOT_NATIVE_INSTRUMENT_RACK_NOT_FOUND")
    try:
        executed = subprocess.run(
            [sys.executable, str(script)], input=json.dumps(request),
            text=True, capture_output=True, timeout=timeout, check=False,
            cwd=str(ghot_root),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Hold("GHOT_DISPATCH_OUTCOME_AMBIGUOUS") from exc
    require(executed.returncode == 0, "GHOT_NATIVE_OPERATION_REFUSED_OR_AMBIGUOUS")
    try:
        output = json.loads(executed.stdout)
    except json.JSONDecodeError as exc:
        raise Hold("GHOT_DID_NOT_RETURN_JSON") from exc
    require(isinstance(output, dict), "GHOT_RESULT_OBJECT_REQUIRED")
    return output


def discover_ghot(ghot_root: Path) -> dict:
    return _ghot_request(ghot_root, {"action": "rack"})


def native_packet_verify(ghot_root: Path, packet: Any) -> dict:
    """Invoke GHoT's own signature/lineage verifier, not a Static-OS imitation."""
    checker = Path(__file__).parents[1] / "scripts" / "question-ghot-verify.py"
    require(checker.is_file(), "NATIVE_PACKET_VERIFIER_NOT_FOUND")
    try:
        completed = subprocess.run(
            [sys.executable, str(checker), str(ghot_root)],
            input=json.dumps(packet), text=True, capture_output=True,
            timeout=15, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Hold("GHOT_PACKET_VERIFICATION_UNAVAILABLE") from exc
    require(completed.returncode == 0, "GHOT_NATIVE_PACKET_VERIFICATION_FAILED")
    try:
        body = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise Hold("GHOT_PACKET_VERIFIER_INVALID_OUTPUT") from exc
    require(body.get("status") == "VERIFIED_NATIVE_GHOT_PACKET"
            and body.get("packet_id") == packet.get("packet_id"),
            "GHOT_PACKET_ID_NOT_VERIFIED")
    return body


def _observe(question: dict, candidate: dict, native: dict, ghot_root: Path) -> dict:
    require(native.get("schema") == "ghot.instrument-dispatch-result/v0"
            and native.get("status") == "EXECUTED", "GHOT_DID_NOT_EXECUTE_INSTRUMENT")
    packet = native.get("packet")
    require(isinstance(packet, dict), "GHOT_PORTABLE_PACKET_REQUIRED")
    native_packet_verify(ghot_root, packet)
    require(
        packet.get("source_card_id") == candidate["card_id"]
        and packet.get("capability") == candidate["capability"]
        and packet.get("status") == "PORTABLE_NOT_ADMITTED"
        and packet.get("dispatch_id") == native.get("dispatch_id"),
        "GHOT_PACKET_CANDIDATE_MISMATCH",
    )
    donor = packet.get("donor_result")
    require(isinstance(donor, dict)
            and donor.get("capability") == candidate["capability"],
            "GHOT_DONOR_MISMATCH")
    outcome = donor.get("result")
    require(isinstance(outcome, dict)
            and outcome.get("schema") == "static-os.gear-model-observation/v0"
            and outcome.get("status") == "SIMULATION_ONLY"
            and outcome.get("physical_measurement") is False
            and outcome.get("historical_reconstruction_verified") is False
            and outcome.get("transmission") is False
            and outcome.get("source_claim") == SOURCE,
            "DONOR_CANNOT_CLAIM_REAL_WORLD")
    predicted = (
        -Fraction(candidate["input"]["driver_teeth"] * candidate["input"]["input_turns"],
                  candidate["input"]["driven_teeth"])
        if candidate["input"]["operation"] == "forward"
        else -Fraction(candidate["input"]["driven_teeth"] * candidate["input"]["input_turns"],
                       candidate["input"]["driver_teeth"])
    )
    actual = _ratio(outcome.get("value"))
    require(
        outcome.get("operation") == candidate["input"]["operation"]
        and outcome.get("quantity") == candidate["measured_quantity"]
        and actual == predicted,
        "MODEL_RESULT_FAILED_INDEPENDENT_RECOMPUTATION",
    )
    expectation = _ratio(candidate["expected"])
    match = actual == expectation
    return {
        "schema": "static-os.question-observation/v0",
        "question_id": question["question_id"],
        "candidate_id": candidate["candidate_id"],
        "dispatch_id": packet["dispatch_id"],
        "crossing_id": packet["dispatch_crossing_id"],
        "packet_id": packet["packet_id"],
        "value": _fraction(actual),
        "expected": _fraction(expectation),
        "result": "MATCHES_DECLARED_CLAIM" if match else "CONTRADICTS_DECLARED_CLAIM",
        "source_kind": "GHOT_SIGNED_DISPATCH_OF_MODERN_SIMULATION",
        "native_packet_verified": True,
        "physical_observation": False,
        "historical_authenticity_verified": False,
        "authority": "none",
    }


def _next_question(question: dict, candidate: dict, observation: dict) -> dict:
    other = next(item for item in question["candidate_experiments"]
                 if item["candidate_id"] != candidate["candidate_id"])
    if observation["result"] == "MATCHES_DECLARED_CLAIM":
        wording = "Will the alternate ideal gear calculation independently agree with this result?"
    else:
        wording = "Which declared gear-model assumption or input explains the contradiction?"
    return _sealed({
        "schema": NEXT,
        "parent_question_id": question["question_id"],
        "parent_packet_id": observation["packet_id"],
        "parent_observation_sha256": digest(observation),
        "question": wording,
        "proposed_other_candidate_id": other["candidate_id"],
        "status": "PROPOSAL_ONLY",
        "execution": "NONE",
        "automatic_next_turn": False,
        "authority": "none",
    }, "next_question_id", "static-os-next-question-v0:")


def _state_path(state_dir: Path, question: dict) -> Path:
    return state_dir / (question["question_id"].split(":")[-1] + ".json")


def _write_new(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise Hold("QUESTION_STATE_EXISTS") from exc
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(state, out, sort_keys=True, separators=(",", ":"))
        out.flush()
        os.fsync(out.fileno())


def _write_complete(path: Path, state: dict) -> None:
    target = path.with_suffix(".done-tmp")
    # An old interrupted completion temp is not permission to overwrite.
    _write_new(target, state)
    os.replace(target, path)


def _state(payload: dict) -> dict:
    return _sealed(payload, "state_id", "static-os-question-state-v0:")


def _load_state(path: Path) -> dict:
    require(path.is_file(), "QUESTION_STATE_UNAVAILABLE")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Hold("QUESTION_STATE_NOT_READABLE") from exc
    _check_seal(value, "state_id", "static-os-question-state-v0:")
    require(value.get("schema") == STATE, "QUESTION_STATE_SCHEMA_MISMATCH")
    return value


def execute_selected(
    seed: Any, rack: Any, selection: Any, *, ghot_root: Path,
    state_dir: Path,
) -> dict:
    question = compile_question(seed, rack)
    candidate = validate_selection(question, selection)
    path = _state_path(state_dir, question)
    if path.exists():
        previous = _load_state(path)
        if previous.get("stage") == "PREPARED":
            raise Hold("PREPARED_EXECUTION_OUTCOME_UNKNOWN_NO_AUTORETRY")
        require(previous.get("stage") == "COMPLETED", "UNKNOWN_QUESTION_STATE")
        verified = replay_state(path, ghot_root=ghot_root)
        require(verified["selection"] == selection, "NEW_SELECTION_CANNOT_REUSE_OLD_QUESTION")
        return {"state": verified, "replayed": True}

    # Fresh GHoT Rack revalidation happens *before* creating our prepared event,
    # but native GHoT also rechecks the exact card immediately before execution.
    fresh = discover_ghot(ghot_root)
    require(fresh == rack, "STALE_GHOT_INSTRUMENT_RACK")
    prepared = _state({
        "schema": STATE, "stage": "PREPARED",
        "question": question, "selection": selection,
        "candidate": candidate,
        "operation": "GHOT_SIGNED_INSTRUMENT_DISPATCH",
        "auto_retry": False,
    })
    _write_new(path, prepared)
    card = next(item for item in rack["cards"] if item.get("card_id") == candidate["card_id"])
    native = _ghot_request(ghot_root, {
        "action": "dispatch", "card": card,
        "payload": candidate["input"],
        "dispatch_source": "static-os:question-first:" + question["question_id"]
            + ":" + candidate["candidate_id"] + ":" + selection["owner_id"],
    })
    observed = _observe(question, candidate, native, ghot_root)
    completed = _state({
        "schema": STATE, "stage": "COMPLETED",
        "question": question, "selection": selection, "candidate": candidate,
        "observation": observed,
        "next_question": _next_question(question, candidate, observed),
        "native_ghot_result": native,
        "consequence": "SOFTWARE_SIMULATION_ONLY",
        "automatic_next_turn": False,
        "physical_action_claimed": False,
        "reLATTE_new_signed_crossing_by_static_os": False,
    })
    _write_complete(path, completed)
    return {"state": completed, "replayed": False}


def replay_state(path: Path, *, ghot_root: Path) -> dict:
    """Cold, read-only replay: GHoT-native signature verification; no dispatch."""
    state = _load_state(path)
    require(state.get("stage") == "COMPLETED", "COLD_REPLAY_REFUSES_PREPARED")
    question = state.get("question")
    candidate = state.get("candidate")
    require(_check_seal(question, "question_id", "static-os-question-v0:") is not None,
            "INVALID_QUESTION_IN_STATE")
    require(candidate in question.get("candidate_experiments", []),
            "STATE_CANDIDATE_NOT_IN_QUESTION")
    require(validate_selection(question, state.get("selection")) == candidate,
            "STATE_SELECTION_NOT_GROUNDED")
    observed = _observe(question, candidate, state.get("native_ghot_result"), ghot_root)
    require(observed == state.get("observation"), "COLD_REPLAY_OBSERVATION_MISMATCH")
    require(state.get("next_question") == _next_question(question, candidate, observed),
            "COLD_REPLAY_NEXT_QUESTION_MISMATCH")
    require(state.get("automatic_next_turn") is False
            and state.get("physical_action_claimed") is False,
            "STATE_MAKES_UNEARNED_EXECUTION_CLAIM")
    return state
