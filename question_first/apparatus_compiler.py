"""APPARATUS-COMPILER-002: gap -> proposed mechanism assembly -> one bounded effect.

STATIC OS compiles the assembly graph; GHoT owns the opted-in simulation
instrument and its signed reLATTE-shaped dispatch; source witnesses never
become physical or historical design certification. Cold replay uses GHoT's
native verifier and independently recomputes the model prediction.
"""
from __future__ import annotations

import json
import os
import re
from fractions import Fraction
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.gear_donor import FORWARD
from question_first.apparatus_donor import DIRECT, GEARED, SCHEMA as INPUT
from question_first.session import (
    Hold, _ghot_request, _sealed, _check_seal, _write_new, _write_complete,
    _load_state as _load_question_state, discover_ghot, native_packet_verify,
    require,
)

SEED = "static-os.apparatus-question-seed/v0"
PLAN = "static-os.apparatus-plan/v0"
APPROVAL = "static-os.apparatus-selection/v0"
STATE = "static-os.apparatus-session-state/v0"
NEXT = "static-os.apparatus-next-question/v0"
MODEL = "IDEAL_EXTERNAL_GEARS_AND_LEADSCREW_ZERO_LOSS"
NEEDS = (FORWARD, DIRECT, GEARED)
OWNER = re.compile(r"^[A-Za-z0-9._:-]{1,100}$")

# Verified *catalog reference*, NOT verified manuscript pixels, transcription,
# attributed engineering design, or claim that this exact assembly is depicted.
# Ambrosiana's public catalog identifies f.1069 recto as including water-lifting
# cochleas. The modern gear/lead-screw apparatus is an invented experiment.
CATALOG_WITNESS = {
    "schema": "static-os.catalog-source-witness/v0",
    "repository": "Veneranda Biblioteca Ambrosiana",
    "catalog_url": "https://www.ambrosiana.it/en/discover/masterpieces/codex-atlanticus/",
    "folio": "Codex Atlanticus f. 1069 recto",
    "catalog_topic": "water-lifting-cochleas",
    "relation_to_apparatus": "CONCEPTUAL_ANALOGY_ONLY",
    "source_image_sha256": None,
    "source_image_bytes_verified": False,
    "attribution_proof": "CURATORIAL_CATALOG_REFERENCE_ONLY",
    "exact_gear_leadscrew_assembly_depicted": False,
}


def verify_source(ref: Any) -> dict:
    require(ref == CATALOG_WITNESS, "SOURCE_WITNESS_CANNOT_INVENT_FOLIO_OR_BYTES")
    return ref


def validate_seed(raw: Any) -> dict:
    require(type(raw) is dict and set(raw) == {
        "schema", "question", "wanted_quantity", "driver_teeth",
        "driven_teeth", "input_turns", "lead_um_per_turn",
        "claimed_axial_um", "source_witness",
    }, "EXACT_APPARATUS_QUESTION_REQUIRED")
    require(raw["schema"] == SEED
            and raw["question"] == "does-gearing-change-leadscrew-travel"
            and raw["wanted_quantity"] == "AXIAL_TRAVEL_MICROMETRES",
            "UNKNOWN_QUESTION_OR_QUANTITY")
    for key, lo, hi in (
        ("driver_teeth", 4, 200), ("driven_teeth", 4, 200),
        ("input_turns", -100, 100), ("lead_um_per_turn", 100, 20000),
        ("claimed_axial_um", -2000000, 2000000),
    ):
        require(type(raw[key]) is int and lo <= raw[key] <= hi,
                "APPARATUS_SEED_VALUE_OUT_OF_BOUNDS:" + key)
    verify_source(raw["source_witness"])
    return raw


def _safe_card(card: dict) -> bool:
    limits = card.get("limits")
    return (
        card.get("schema") == "ghot.instrument-card/v0"
        and card.get("available") is True
        and card.get("status") == "PROPOSAL_ONLY"
        and card.get("semantic_effect") == "none"
        and type(card.get("card_id")) is str and bool(card["card_id"])
        and type(limits) is dict
        and limits.get("network") is False
        and limits.get("transmit") is False
        and limits.get("physical_effects") is False
        and limits.get("simulation_only") is True
        and limits.get("authority") == "none"
    )


def _offers(rack: Any) -> tuple[dict, list[str]]:
    require(type(rack) is dict and rack.get("schema") == "ghot.instrument-rack/v0"
            and type(rack.get("rack_id")) is str
            and type(rack.get("cards")) is list,
            "GHOT_NATIVE_RACK_REQUIRED")
    available = {}
    missing = []
    for name in NEEDS:
        entries = [card for card in rack["cards"]
                   if type(card) is dict and card.get("capability") == name]
        require(len(entries) <= 1, "DUPLICATE_APPARATUS_CAPABILITY")
        if not entries or entries[0].get("available") is not True:
            missing.append(name)
        else:
            require(_safe_card(entries[0]), "UNSAFE_APPARATUS_OFFER:" + name)
            available[name] = entries[0]
    return available, missing


def _nodes(mode: str, ids: dict) -> list[dict]:
    screw = {
        "id": "screw", "capability": DIRECT, "card_id": ids[DIRECT],
        "output": "AXIAL_TRAVEL_MICROMETRES",
    }
    if mode == "direct":
        return [{**screw, "input": "DRIVER_TURNS"}]
    return [
        {"id": "gear", "capability": FORWARD, "card_id": ids[FORWARD],
         "input": "DRIVER_TURNS", "output": "DRIVEN_TURNS"},
        {**screw, "input": "DRIVEN_TURNS"},
    ]


def compile_apparatus(seed: Any, rack: Any) -> dict:
    s = validate_seed(seed)
    cards, missing = _offers(rack)
    ids = {name: card["card_id"] for name, card in cards.items()}
    source_id = "apparatus-source-v0:" + digest(CATALOG_WITNESS)
    body = {
        "schema": PLAN,
        "question_seed": s,
        "rack_id": rack["rack_id"],
        "source_ref": source_id,
        "source_status": "CATALOG_MOTIF_ONLY_MODERN_APPARATUS_INFERENCE",
        "question": (
            "Which permitted idealized assembly would distinguish direct "
            "screw travel from geared screw travel?"
        ),
        "demand": "ROTATION_TO_AXIAL_DISPLACEMENT",
        "existing_gear_only_is_insufficient": True,
        "available_cards": cards,  # Frozen discovery for read-only reconstruction.
        "missing_capabilities": missing,
        "assembly_candidates": [],
        "status": "NEEDS_NEW_INSTRUMENT" if missing else "PROPOSAL_ONLY",
        "physical_effects": False,
        "actual_source_image_verified": False,
        "human_execution_approval": "NOT_GIVEN",
        "automatic_compilation_into_hardware": False,
        "autodisco_live_response": False,
    }
    if not missing:
        for identifier, mode, executor in (
            ("direct-screw", "direct", DIRECT),
            ("gear-then-screw", "geared", GEARED),
        ):
            request = {
                "schema": INPUT, "mode": mode,
                "driver_teeth": s["driver_teeth"],
                "driven_teeth": s["driven_teeth"],
                "input_turns": s["input_turns"],
                "lead_um_per_turn": s["lead_um_per_turn"],
                "source_ref": source_id,
            }
            body["assembly_candidates"].append({
                "candidate_id": identifier, "mode": mode,
                "nodes": _nodes(mode, ids),
                "executor_card_id": ids[executor],
                "executor_capability": executor,
                "request": request,
                "execution_contract": "ONE_NATIVE_GHOT_INSTRUMENT_DISPATCH",
                "submodule_dispatches": 0,
                "simulation_only": True,
            })
    return _sealed(body, "plan_id", "static-os-apparatus-plan-v0:")


def verify_plan(value: Any) -> dict:
    plan = _check_seal(value, "plan_id", "static-os-apparatus-plan-v0:")
    require(plan.get("schema") == PLAN, "INVALID_APPARATUS_PLAN_SCHEMA")
    rack = {
        "schema": "ghot.instrument-rack/v0",
        "rack_id": plan["rack_id"],
        "cards": list(plan["available_cards"].values()),
    }
    require(plan == compile_apparatus(plan["question_seed"], rack),
            "APPARATUS_GRAPH_DOES_NOT_RECONSTRUCT")
    return plan


def _selected(plan: dict, selection: Any) -> dict:
    require(plan.get("status") == "PROPOSAL_ONLY",
            "UNMET_APPARATUS_CAPABILITY_GAP")
    require(type(selection) is dict and set(selection) == {
        "schema", "plan_id", "candidate_id", "executor_card_id",
        "approved", "owner_id",
    }, "APPARATUS_EXPLICIT_SELECTION_REQUIRED")
    require(selection["schema"] == APPROVAL
            and selection["approved"] is True
            and selection["plan_id"] == plan["plan_id"]
            and type(selection["owner_id"]) is str
            and OWNER.fullmatch(selection["owner_id"]) is not None,
            "APPARATUS_NOT_APPROVED")
    choices = [c for c in plan["assembly_candidates"]
               if c["candidate_id"] == selection["candidate_id"]
               and c["executor_card_id"] == selection["executor_card_id"]]
    require(len(choices) == 1, "WRONG_APPARATUS_CHOICE")
    return choices[0]


def _rational(n: Fraction) -> dict:
    return {"numerator": n.numerator, "denominator": n.denominator}


def _verification(plan: dict, chosen: dict, native: Any, ghot_root: Path) -> dict:
    require(type(native) is dict
            and native.get("schema") == "ghot.instrument-dispatch-result/v0"
            and native.get("status") == "EXECUTED"
            and type(native.get("packet")) is dict,
            "NATIVE_GHOT_DISPATCH_NOT_COMPLETED")
    packet = native["packet"]
    native_packet_verify(ghot_root, packet)
    require(
        packet.get("source_card_id") == chosen["executor_card_id"]
        and packet.get("capability") == chosen["executor_capability"]
        and packet.get("input_sha256") == digest(chosen["request"])
        and packet.get("dispatch_id") == native["dispatch_id"]
        and packet.get("status") == "PORTABLE_NOT_ADMITTED",
        "APPARATUS_PACKET_DOES_NOT_BIND_CHOICE",
    )
    env = packet.get("donor_result")
    require(type(env) is dict and env.get("capability") == chosen["executor_capability"],
            "WRONG_GHOT_DONOR")
    observation = env.get("result")
    require(type(observation) is dict and set(observation) == {
        "schema", "status", "mode", "source_ref", "gear_output_turns",
        "output_axial_um", "model", "instrument_steps",
        "physical_execution", "historical_reconstruction",
        "automatic_next_execution", "transmission",
    }, "INVALID_APPARATUS_DONOR_OUTPUT")
    raw = chosen["request"]
    turns = (Fraction(-raw["driver_teeth"] * raw["input_turns"],
                     raw["driven_teeth"]) if chosen["mode"] == "geared"
             else Fraction(raw["input_turns"]))
    axial = turns * raw["lead_um_per_turn"]
    require(
        observation["schema"] == "static-os.apparatus-simulation/v0"
        and observation["status"] == "SIMULATION_ONLY"
        and observation["mode"] == chosen["mode"]
        and observation["source_ref"] == plan["source_ref"]
        and observation["gear_output_turns"] == _rational(turns)
        and observation["output_axial_um"] == _rational(axial)
        and observation["model"] == MODEL
        and observation["instrument_steps"] == (
            ["IDEAL_GEAR_RATIO", "IDEAL_LEADSCREW_TRANSLATION"]
            if chosen["mode"] == "geared" else ["IDEAL_LEADSCREW_TRANSLATION"]
        )
        and observation["physical_execution"] is False
        and observation["historical_reconstruction"] is False
        and observation["automatic_next_execution"] is False
        and observation["transmission"] is False,
        "APPARATUS_SIMULATION_NOT_INDEPENDENTLY_VERIFIED",
    )
    claim = Fraction(plan["question_seed"]["claimed_axial_um"])
    body = {
        "schema": "static-os.apparatus-observation/v0",
        "plan_id": plan["plan_id"],
        "candidate_id": chosen["candidate_id"],
        "native_packet_id": packet["packet_id"],
        "signed_crossing_id": packet["dispatch_crossing_id"],
        "signed_execution_receipt_id": packet.get("ghot_receipt_id"),
        "mode": chosen["mode"],
        "axial_um": _rational(axial),
        "claimed_axial_um": _rational(claim),
        "disposition": "IDEAL_CLAIM_MATCH" if axial == claim else "IDEAL_CLAIM_CONTRADICTED",
        "model_proof": "INDEPENDENT_FRACTION_RECOMPUTATION",
        "real_world_measurement": False,
        "historic_mechanism_verified": False,
        "authority": "none",
    }
    return _sealed(body, "observation_id", "static-os-apparatus-observation-v0:")


def _next(plan: dict, chosen: dict, observed: dict) -> dict:
    other = next(c["candidate_id"] for c in plan["assembly_candidates"]
                 if c["candidate_id"] != chosen["candidate_id"])
    body = {
        "schema": NEXT,
        "parent_plan_id": plan["plan_id"],
        "observation_id": observed["observation_id"],
        "source_packet_id": observed["native_packet_id"],
        "question": (
            "Would the alternate apparatus predict the claimed motion, "
            "and what real measurements would test ideal backlash/slip?"
        ),
        "proposed_candidate": other,
        "status": "PROPOSAL_ONLY",
        "action": "NONE",
        "historical_claim": "NONE",
        "automatic_next_turn": False,
    }
    return _sealed(body, "next_id", "static-os-apparatus-next-v0:")


def _state_file(state_dir: Path, plan: dict) -> Path:
    return state_dir / (plan["plan_id"].split(":")[-1] + ".json")


def _state(body: dict) -> dict:
    return _sealed(body, "state_id", "static-os-apparatus-state-v0:")


def _load(path: Path) -> dict:
    require(path.is_file(), "APPARATUS_STATE_MISSING")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Hold("APPARATUS_STATE_NOT_READABLE") from exc
    _check_seal(value, "state_id", "static-os-apparatus-state-v0:")
    require(value.get("schema") == STATE, "APPARATUS_STATE_WRONG_SCHEMA")
    return value


def execute_selected(plan: Any, selection: Any, *, ghot_root: Path,
                     state_dir: Path) -> dict:
    p = verify_plan(plan)
    chosen = _selected(p, selection)
    path = _state_file(state_dir, p)
    if path.exists():
        state = _load(path)
        require(state.get("stage") != "PREPARED",
                "APPARATUS_PREPARED_OUTCOME_UNKNOWN_NO_AUTORETRY")
        complete = replay_state(path, ghot_root=ghot_root)
        require(complete["selection"] == selection,
                "CHANGED_SELECTION_CANNOT_REUSE_OCCURRENCE")
        return {"state": complete, "replayed": True}

    fresh = discover_ghot(ghot_root)
    require(compile_apparatus(p["question_seed"], fresh) == p,
            "APPARATUS_STALE_GHOT_CAPABILITY_FIELD")
    _write_new(path, _state({
        "schema": STATE, "stage": "PREPARED",
        "plan": p, "selection": selection, "chosen": chosen,
        "auto_retry": False,
    }))
    card = fresh["cards"]
    card = next(c for c in card if c.get("card_id") == chosen["executor_card_id"])
    native = _ghot_request(ghot_root, {
        "action": "dispatch",
        "card": card,
        "payload": chosen["request"],
        "dispatch_source": "static-os:apparatus-002:"
                           + p["plan_id"] + ":" + chosen["candidate_id"]
                           + ":" + selection["owner_id"],
    })
    observation = _verification(p, chosen, native, ghot_root)
    complete = _state({
        "schema": STATE,
        "stage": "COMPLETED",
        "plan": p, "selection": selection, "chosen": chosen,
        "observation": observation,
        "native_result": native,
        "next_question": _next(p, chosen, observation),
        "apparatus_assembly": "MODEL_ONLY",
        "real_hardware": False,
        "next_turn_executed": False,
    })
    _write_complete(path, complete)
    return {"state": complete, "replayed": False}


def replay_state(path: Path, *, ghot_root: Path) -> dict:
    """Offline relative to instruments: verify signed native history, no dispatch."""
    state = _load(path)
    require(state.get("stage") == "COMPLETED", "APPARATUS_PREPARED_HOLD")
    plan = verify_plan(state.get("plan"))
    chosen = _selected(plan, state.get("selection"))
    require(chosen == state.get("chosen"), "APPARATUS_CHOICE_NOT_BOUND")
    observation = _verification(plan, chosen, state.get("native_result"), ghot_root)
    require(state.get("observation") == observation,
            "APPARATUS_OBSERVATION_MISMATCH")
    require(state.get("next_question") == _next(plan, chosen, observation),
            "APPARATUS_NEXT_QUESTION_MISMATCH")
    require(state.get("apparatus_assembly") == "MODEL_ONLY"
            and state.get("real_hardware") is False
            and state.get("next_turn_executed") is False,
            "APPARATUS_HISTORY_OVERCLAIMS_EFFECTS")
    return state
