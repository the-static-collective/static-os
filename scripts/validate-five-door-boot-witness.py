#!/usr/bin/env python3
"""Validate FIVE-DOOR-BOOT-WITNESS-001 without promoting synthetic evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

CONTRACT_SCHEMA = "static-os.five-door-boot-witness-contract/v0"
SESSION_SCHEMA = "static-os.five-door-session/v0"
DOORS = {"PRESENT", "MOTION", "SOUND", "VOICE", "PRINT"}
RETURN_DISPOSITIONS = {"ADMIT", "HOLD", "REFUSE"}
CLAIMS = {
    "validator_executable": True,
    "synthetic_constellation_defined": True,
    "real_adapters_bound": False,
    "real_dispatch_executed": False,
    "real_returns_observed": False,
    "actual_shutdown_executed": False,
    "actual_reboot_executed": False,
    "cold_replay_of_real_session_proven": False,
    "causal_attribution_proven": False,
}
REQUIRED_LAWS = {
    "VISIBLE POSSIBILITY != EXECUTION",
    "SESSION != AUTHORITY",
    "CONSTELLATION != MERGE",
    "SIBLING != SUCCESSOR",
    "RETURN != ADMISSION",
    "ADMISSION != EXECUTION",
    "IN FLIGHT != LOST",
    "UNFINISHED != ERROR",
    "UNOBSERVED != FAILED",
    "REBOOT != NEW WORLD",
    "THE HOUSE REMEMBERS RECEIPTS, NOT ASSUMPTIONS",
    "G_field != G_local",
}


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(contract, session):
    if not isinstance(contract, dict) or contract.get("schema") != CONTRACT_SCHEMA:
        raise ValueError("unsupported five-door contract schema")
    if contract.get("id") != "FIVE-DOOR-BOOT-WITNESS-001":
        raise ValueError("wrong five-door contract id")
    if contract.get("status") != "synthetic-contract-harness":
        raise ValueError("synthetic harness status silently promoted")

    stacked = contract.get("stacked_on", {})
    if stacked.get("static_os_pr") != 42 or stacked.get("static_os_commit") != "17e209cebb8d45b05dd9c564e99b5f5519b2d4a0":
        raise ValueError("stacked STATIC OS witness drift")

    reported = contract.get("reported_adapter_harvest", {})
    if reported.get("short_commit") != "043e89a":
        raise ValueError("reported adapter-harvest identity drift")
    if reported.get("provenance") != "human-reported-local-work":
        raise ValueError("adapter-harvest provenance promoted")
    if reported.get("github_verifiable") is not False or reported.get("bound_into_this_contract") is not False:
        raise ValueError("unverifiable adapter work must remain unbound")

    doors = contract.get("doors")
    if not isinstance(doors, list) or len(doors) != 5:
        raise ValueError("exact five-door set required")
    by_id = {door.get("id"): door for door in doors if isinstance(door, dict)}
    if set(by_id) != DOORS or len(by_id) != len(doors):
        raise ValueError("five-door identity set changed")
    for door_id, door in by_id.items():
        if door.get("binding") != "unbound":
            raise ValueError(f"{door_id} real binding is not yet proven")
        if door.get("automatic_execution") is not False:
            raise ValueError(f"{door_id} visibility must not execute")
        if door.get("authority") != "none":
            raise ValueError(f"{door_id} card cannot manufacture authority")

    policy = contract.get("execution_policy", {})
    required_true = {
        "rack_visibility_executes_nothing",
        "dispatch_requires_explicit_selection",
        "branches_are_siblings",
        "return_requires_local_disposition",
        "unfinished_branches_remain_visible",
        "shutdown_may_preserve_unresolved_state",
        "reboot_must_not_infer_completion",
    }
    if any(policy.get(key) is not True for key in required_true):
        raise ValueError("execution policy boundary weakened")

    observer = contract.get("causal_observer", {})
    if observer.get("id") != "TranchNOSE" or observer.get("role") != "comparison-observer":
        raise ValueError("causal observer identity drift")
    if observer.get("authority") != "none":
        raise ValueError("observer cannot acquire session authority")
    if observer.get("held_constant") != ["parent_identity", "source_admission", "human_intent"]:
        raise ValueError("causal comparison constants drift")
    if observer.get("varied_dimension") != "door-field-configuration":
        raise ValueError("causal comparison varied dimension drift")
    if observer.get("result") != "comparison-ready-only" or observer.get("causal_attribution_proven") is not False:
        raise ValueError("comparison must not become causal proof")

    if contract.get("claims") != CLAIMS:
        raise ValueError("five-door claims silently promoted")
    if not REQUIRED_LAWS.issubset(set(contract.get("laws", []))):
        raise ValueError("required five-door law missing")

    if not isinstance(session, dict) or session.get("schema") != SESSION_SCHEMA:
        raise ValueError("unsupported five-door session schema")
    if session.get("id") != "FIVE-DOOR-SESSION-SYNTHETIC-001":
        raise ValueError("wrong synthetic session id")
    if session.get("synthetic") is not True or session.get("real_source_bytes") is not False:
        raise ValueError("synthetic session must not pose as real evidence")

    particular = session.get("particular", {})
    parent = particular.get("id")
    if parent != "synthetic:five-door-parent-001":
        raise ValueError("synthetic parent identity drift")
    if particular.get("admission") != "SYNTHETIC_ADMITTED_FOR_HARNESS_ONLY":
        raise ValueError("synthetic admission boundary drift")
    if particular.get("authority") != "fixture-only-no-real-authority":
        raise ValueError("synthetic fixture cannot claim real authority")

    intent = session.get("human_intent")
    if intent != "derive sibling expressions without changing parent authority":
        raise ValueError("human intent drift")

    dispatch = session.get("dispatch", {})
    if dispatch.get("automatic") is not False:
        raise ValueError("dispatch must remain explicit")
    if dispatch.get("decision") != "human-explicit-synthetic-fixture":
        raise ValueError("dispatch decision provenance drift")
    if set(dispatch.get("selected_doors", [])) != DOORS:
        raise ValueError("founding fixture must exercise all five doors")

    branches = session.get("branches")
    if not isinstance(branches, list) or len(branches) != 5:
        raise ValueError("founding session requires five sibling branches")
    branch_ids = [branch.get("id") for branch in branches if isinstance(branch, dict)]
    if len(branch_ids) != 5 or len(set(branch_ids)) != 5:
        raise ValueError("branch identities must be unique")
    if {branch.get("door") for branch in branches} != DOORS:
        raise ValueError("each door must own exactly one sibling branch")

    computed_states = {}
    returned = set()
    unfinished = set()
    for branch in branches:
        branch_id = branch.get("id")
        if branch.get("parent") != parent:
            raise ValueError("sibling parent drift")
        if branch.get("intent") != intent:
            raise ValueError("branch intent drift")
        if branch.get("real_execution") is not False:
            raise ValueError("synthetic branch cannot claim real execution")
        if branch.get("canonical_result") is not False:
            raise ValueError("sibling branch cannot become canonical result")
        if branch.get("may_mutate_sibling") is not False:
            raise ValueError("sibling branch may not mutate another sibling")

        phase = branch.get("phase")
        disposition = branch.get("disposition")
        if phase == "RETURNED":
            if disposition not in RETURN_DISPOSITIONS:
                raise ValueError("returned branch requires explicit local disposition")
            returned.add(branch_id)
        elif phase == "IN_FLIGHT":
            if disposition is not None:
                raise ValueError("in-flight branch cannot already have disposition")
            unfinished.add(branch_id)
        elif phase == "UNOBSERVED":
            if disposition is not None:
                raise ValueError("unobserved branch cannot have disposition")
            unfinished.add(branch_id)
        else:
            raise ValueError("unknown LIFE branch phase")
        computed_states[branch_id] = {"phase": phase, "disposition": disposition}

    tray = session.get("return_tray", {})
    if tray.get("automatic_admission") is not False or tray.get("independent_disposition") is not True:
        raise ValueError("return tray authority boundary weakened")
    if set(tray.get("returned_branch_ids", [])) != returned:
        raise ValueError("return tray does not match returned siblings")

    snapshot = session.get("shutdown_snapshot", {})
    if snapshot.get("branch_states") != computed_states:
        raise ValueError("shutdown constellation does not match LIFE")
    if set(snapshot.get("unfinished_branch_ids", [])) != unfinished:
        raise ValueError("unfinished LIFE branches were erased")

    reboot = session.get("reboot_expectation", {})
    if reboot.get("preserve_exact_branch_states") is not True:
        raise ValueError("reboot must preserve exact unresolved state")
    if reboot.get("infer_completion") is not False or reboot.get("same_process_inferred") is not False:
        raise ValueError("reboot must not invent completion or continuous process")
    if reboot.get("actual_shutdown_executed") is not False or reboot.get("actual_reboot_executed") is not False:
        raise ValueError("synthetic replay expectation promoted to executed reboot")

    return {
        "doors": sorted(DOORS),
        "branch_states": computed_states,
        "returned": sorted(returned),
        "unfinished": sorted(unfinished),
        "causal_result": "comparison-ready-only",
    }


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: validate-five-door-boot-witness.py CONTRACT SESSION", file=sys.stderr)
        return 2
    try:
        result = validate(load(Path(args[0])), load(Path(args[1])))
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
