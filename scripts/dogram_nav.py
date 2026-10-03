#!/usr/bin/env python3
"""Dogram path membrane for WORLD -> NAV reorientation.

This is a bounded adapter using Dogram's content-addressed lineage grammar:
keep the path addressable, not recursively embedded. It records a declared
artifact path and emits a proposed transition. It does not decide the heading.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

LEDGER_SCHEMA = "static.dogram-trace-ledger/v0"
TRANSITION_SCHEMA = "static.dogram-transition/v0"
NAV_SCHEMA = "static.nav-receipt/v0"
WORLD_RECURSION_SCHEMA = "static.world-recursion-receipt/v0"

STEP_SPECS = (
    ("nav_contact", "declared_root"),
    ("witness_intake", "source_preserved"),
    ("world_comparison", "evidence_paths_compared"),
    ("ground_observation", "field_conditions_changed"),
    ("witness_reentry", "new_source_reentered"),
    ("world_recursion", "novelty_and_independence_separated"),
)


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_digest(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(value, path: str | Path | None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def build_trace(artifacts):
    if len(artifacts) != len(STEP_SPECS):
        raise ValueError("trace requires exactly six bridge artifacts")
    if artifacts[0].get("schema") != NAV_SCHEMA:
        raise ValueError("trace root must be a NAV receipt")
    if artifacts[-1].get("schema") != WORLD_RECURSION_SCHEMA:
        raise ValueError("trace head must be a WORLD recursion receipt")

    entries = []
    store = {}
    previous = None
    for position, (artifact, (kind, relation)) in enumerate(zip(artifacts, STEP_SPECS)):
        digest = canonical_digest(artifact)
        if digest in store:
            raise ValueError("trace artifact repeated")
        store[digest] = artifact
        entries.append(
            {
                "position": position,
                "kind": kind,
                "artifact_digest": digest,
                "parent_digest": previous,
                "relation": relation,
            }
        )
        previous = digest

    ledger = {
        "schema": LEDGER_SCHEMA,
        "trace_id": "bridge-loop-001",
        "root_digest": entries[0]["artifact_digest"],
        "head_digest": entries[-1]["artifact_digest"],
        "entries": entries,
        "artifacts": store,
        "claim_limit": (
            "This ledger receipts a declared artifact path. Content-addressed links "
            "do not by themselves prove external causality, truth, or authority."
        ),
    }
    result = verify_trace(ledger)
    if result["status"] != "complete":
        raise ValueError(f"new trace did not verify complete: {result['reason']}")
    return ledger


def _shape_ok(ledger):
    return (
        isinstance(ledger, dict)
        and ledger.get("schema") == LEDGER_SCHEMA
        and isinstance(ledger.get("trace_id"), str)
        and bool(ledger["trace_id"])
        and isinstance(ledger.get("entries"), list)
        and len(ledger["entries"]) >= 2
        and isinstance(ledger.get("artifacts"), dict)
        and isinstance(ledger.get("root_digest"), str)
        and isinstance(ledger.get("head_digest"), str)
        and bool(ledger.get("claim_limit"))
    )


def verify_trace(ledger):
    if not _shape_ok(ledger):
        return {"status": "invalid", "reason": "ledger_shape", "positions": []}

    entries = ledger["entries"]
    artifacts = ledger["artifacts"]
    positions = []
    seen = set()
    previous = None

    for expected_position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            return {"status": "invalid", "reason": "entry_not_mapping", "positions": positions}
        if entry.get("position") != expected_position:
            return {"status": "invalid", "reason": "position_gap", "positions": positions}

        digest = entry.get("artifact_digest")
        if not isinstance(digest, str) or len(digest) != 64:
            return {"status": "invalid", "reason": "artifact_digest_shape", "positions": positions}
        if digest in seen:
            return {"status": "invalid", "reason": "cycle_or_repeat", "positions": positions}
        seen.add(digest)

        if entry.get("parent_digest") != previous:
            return {"status": "invalid", "reason": "parent_link_mismatch", "positions": positions}

        artifact = artifacts.get(digest)
        if artifact is None:
            return {"status": "incomplete", "reason": "missing_artifact", "positions": positions}
        if not isinstance(artifact, dict):
            return {"status": "invalid", "reason": "artifact_not_mapping", "positions": positions}
        if canonical_digest(artifact) != digest:
            return {"status": "invalid", "reason": "artifact_digest_mismatch", "positions": positions}

        positions.append(expected_position)
        previous = digest

    if ledger["root_digest"] != entries[0]["artifact_digest"]:
        return {"status": "invalid", "reason": "root_digest_mismatch", "positions": positions}
    if ledger["head_digest"] != entries[-1]["artifact_digest"]:
        return {"status": "invalid", "reason": "head_digest_mismatch", "positions": positions}

    return {
        "status": "complete",
        "reason": None,
        "positions": positions,
        "root_digest": ledger["root_digest"],
        "head_digest": ledger["head_digest"],
        "trace_ledger_sha256": canonical_digest(ledger),
    }


def validate_transition(transition):
    if not isinstance(transition, dict) or transition.get("schema") != TRANSITION_SCHEMA:
        raise ValueError("unsupported Dogram transition schema")
    if transition.get("status") != "proposed":
        raise ValueError("Dogram transition must remain proposed")
    for key in ("transition_id", "from_heading", "to_heading", "delta_summary", "claim_limit"):
        if not isinstance(transition.get(key), str) or not transition[key]:
            raise ValueError(f"Dogram transition missing: {key}")
    for key in (
        "root_digest",
        "path_head_digest",
        "trace_ledger_sha256",
        "world_recursion_sha256",
    ):
        value = transition.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"Dogram transition digest missing: {key}")
    if transition["path_head_digest"] != transition["world_recursion_sha256"]:
        raise ValueError("Dogram path head must be the WORLD recursion receipt")
    if not isinstance(transition.get("preserved"), list) or not transition["preserved"]:
        raise ValueError("Dogram transition preserve set missing")
    return transition


def make_transition(ledger, to_heading, delta_summary, preserved):
    verification = verify_trace(ledger)
    if verification["status"] != "complete":
        raise ValueError(f"trace is not complete: {verification['reason']}")

    nav = ledger["artifacts"][ledger["root_digest"]]
    world = ledger["artifacts"][ledger["head_digest"]]
    if nav.get("schema") != NAV_SCHEMA:
        raise ValueError("trace root is not NAV")
    if world.get("schema") != WORLD_RECURSION_SCHEMA:
        raise ValueError("trace head is not WORLD recursion")
    from_heading = nav.get("next_heading")
    if not isinstance(from_heading, str) or not from_heading:
        raise ValueError("NAV root has no next heading")
    if not to_heading:
        raise ValueError("proposed destination heading missing")
    if not delta_summary:
        raise ValueError("transition delta summary missing")
    if not preserved:
        raise ValueError("transition preserve set missing")

    transition = {
        "schema": TRANSITION_SCHEMA,
        "transition_id": "world-dogram-nav-001",
        "from_heading": from_heading,
        "to_heading": to_heading,
        "root_digest": ledger["root_digest"],
        "path_head_digest": ledger["head_digest"],
        "trace_ledger_sha256": canonical_digest(ledger),
        "world_recursion_sha256": canonical_digest(world),
        "delta_summary": delta_summary,
        "preserved": list(preserved),
        "status": "proposed",
        "claim_limit": (
            "This transition receipts why a heading change is proposed. "
            "It does not authorize the heading change or prove the path is a causal history."
        ),
    }
    return validate_transition(transition)


def compare_destination(first, second):
    validate_transition(first)
    validate_transition(second)
    same_destination = first["to_heading"] == second["to_heading"]
    same_trace = (
        first["trace_ledger_sha256"] == second["trace_ledger_sha256"]
        and first["root_digest"] == second["root_digest"]
        and first["path_head_digest"] == second["path_head_digest"]
    )
    same_origin = first["from_heading"] == second["from_heading"]
    return {
        "schema": "static.dogram-transition-comparison/v0",
        "same_destination": same_destination,
        "same_trace": same_trace,
        "same_origin": same_origin,
        "same_navigation": same_destination and same_trace and same_origin,
        "law": "SAME DESTINATION ≠ SAME NAVIGATION.",
    }


def inspect(value):
    if not isinstance(value, dict):
        raise ValueError("unsupported Dogram inspection input")
    if value.get("schema") == LEDGER_SCHEMA:
        result = verify_trace(value)
        return {
            "schema": "static.dogram-trace-inspection/v0",
            **result,
            "claim_limit": value.get("claim_limit"),
        }
    if value.get("schema") == TRANSITION_SCHEMA:
        validate_transition(value)
        return {
            "schema": "static.dogram-transition-inspection/v0",
            "transition_id": value["transition_id"],
            "from_heading": value["from_heading"],
            "to_heading": value["to_heading"],
            "trace_ledger_sha256": value["trace_ledger_sha256"],
            "world_recursion_sha256": value["world_recursion_sha256"],
            "status": value["status"],
            "authority_claimed": False,
        }
    raise ValueError("unsupported Dogram inspection schema")


def build_parser():
    parser = argparse.ArgumentParser(description="Dogram membrane for WORLD -> NAV")
    sub = parser.add_subparsers(dest="command", required=True)

    trace = sub.add_parser("trace")
    trace.add_argument("nav")
    trace.add_argument("witness")
    trace.add_argument("world")
    trace.add_argument("ground")
    trace.add_argument("reentry")
    trace.add_argument("world_recursion")
    trace.add_argument("-o", "--out")

    transition = sub.add_parser("transition")
    transition.add_argument("ledger")
    transition.add_argument("--to-heading", required=True)
    transition.add_argument("--delta-summary", required=True)
    transition.add_argument("--preserve", action="append", required=True)
    transition.add_argument("-o", "--out")

    compare = sub.add_parser("compare-destination")
    compare.add_argument("first")
    compare.add_argument("second")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("source")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "trace":
            artifacts = [
                _read_json(args.nav),
                _read_json(args.witness),
                _read_json(args.world),
                _read_json(args.ground),
                _read_json(args.reentry),
                _read_json(args.world_recursion),
            ]
            _write_json(build_trace(artifacts), args.out)
            return 0
        if args.command == "transition":
            _write_json(
                make_transition(
                    _read_json(args.ledger),
                    args.to_heading,
                    args.delta_summary,
                    args.preserve,
                ),
                args.out,
            )
            return 0
        if args.command == "compare-destination":
            _write_json(
                compare_destination(
                    _read_json(args.first),
                    _read_json(args.second),
                ),
                None,
            )
            return 0
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.source)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
