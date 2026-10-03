#!/usr/bin/env python3
"""NAV Bridge Packet 001 runtime.

This tool does not take external actions. It helps a human or local system
orient a bounded move, record world-contact, and emit a receipt.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKET_SCHEMA = "static.bridge-packet/v0"
RECEIPT_SCHEMA = "static.nav-receipt/v0"
DOGRAM_TRANSITION_SCHEMA = "static.dogram-transition/v0"
REORIENTATION_SCHEMA = "static.nav-reorientation/v0"
EXPECTED_INVARIANT = "ORIENTATION PRECEDES FORCE."


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(value, path: str | Path | None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def validate_packet(packet):
    if not isinstance(packet, dict) or packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("unsupported packet schema")
    if packet.get("id") != "nav-001":
        raise ValueError("unexpected packet id")
    if packet.get("core_distinction") != EXPECTED_INVARIANT:
        raise ValueError("NAV invariant changed")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    commands = runtime.get("commands")
    if commands != ["validate", "card", "orient", "encounter", "game", "reorient"]:
        raise ValueError("unexpected runtime command set")
    experiment = packet.get("field_experiment")
    if not isinstance(experiment, dict) or experiment.get("requires_world_contact") is not True:
        raise ValueError("field experiment must require world contact")
    return packet


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported receipt schema")
    if receipt.get("packet_id") != "nav-001":
        raise ValueError("receipt packet mismatch")
    status = receipt.get("status")
    if status not in ("oriented", "contacted"):
        raise ValueError("invalid receipt status")
    for key in ("heading", "preserve", "aperture", "bounded_move", "stop_condition"):
        if not receipt.get(key):
            raise ValueError(f"missing receipt field: {key}")
    if not isinstance(receipt["preserve"], list) or not isinstance(receipt["aperture"], list):
        raise ValueError("preserve and aperture must be lists")
    if status == "oriented":
        if any(receipt.get(key) is not None for key in ("observed", "delta", "next_heading")):
            raise ValueError("oriented receipt cannot claim encounter results")
    else:
        for key in ("observed", "delta", "next_heading"):
            if not receipt.get(key):
                raise ValueError(f"contacted receipt missing: {key}")
    return receipt


def make_orientation(args):
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": "nav-001",
        "status": "oriented",
        "heading": args.heading,
        "preserve": args.preserve,
        "aperture": args.aperture,
        "bounded_move": args.move,
        "stop_condition": args.stop,
        "claim_limit": args.claim_limit,
        "observed": None,
        "delta": None,
        "next_heading": None,
    }
    return validate_receipt(receipt)


def record_encounter(receipt, observed, delta, next_heading):
    validate_receipt(receipt)
    if receipt["status"] != "oriented":
        raise ValueError("encounter can only extend an oriented receipt")
    updated = dict(receipt)
    updated.update(
        status="contacted",
        observed=observed,
        delta=delta,
        next_heading=next_heading,
    )
    return validate_receipt(updated)


def game_event(receipt):
    validate_receipt(receipt)
    if receipt["status"] == "oriented":
        return {
            "schema": "static.game-event/v0",
            "packet_id": "nav-001",
            "verb": "ENCOUNTER",
            "progress_class": "awaiting-world-contact",
            "scalar_score": None,
            "available": True,
            "reason": "A heading exists, but the world has not answered yet.",
        }
    return {
        "schema": "static.game-event/v0",
        "packet_id": "nav-001",
        "verb": "REORIENT",
        "progress_class": "world-contacted",
        "scalar_score": None,
        "available": True,
        "reason": "World-contact is recorded; the next heading may now differ from the first.",
    }


def validate_dogram_transition(transition):
    if not isinstance(transition, dict) or transition.get("schema") != DOGRAM_TRANSITION_SCHEMA:
        raise ValueError("unsupported Dogram transition schema")
    if transition.get("status") != "proposed":
        raise ValueError("Dogram transition must remain proposed")
    for key in ("from_heading", "to_heading", "delta_summary", "claim_limit"):
        if not isinstance(transition.get(key), str) or not transition[key]:
            raise ValueError(f"Dogram transition missing: {key}")
    for key in ("trace_ledger_sha256", "world_recursion_sha256"):
        value = transition.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"Dogram transition digest missing: {key}")
    if not isinstance(transition.get("preserved"), list) or not transition["preserved"]:
        raise ValueError("Dogram transition preserve set missing")
    return transition


def make_reorientation(transition):
    validate_dogram_transition(transition)
    return {
        "schema": REORIENTATION_SCHEMA,
        "packet_id": "nav-001",
        "status": "proposed",
        "from_heading": transition["from_heading"],
        "proposed_heading": transition["to_heading"],
        "transition_sha256": __import__("hashlib").sha256(
            json.dumps(
                transition,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
                allow_nan=False,
            ).encode("utf-8")
        ).hexdigest(),
        "trace_ledger_sha256": transition["trace_ledger_sha256"],
        "world_recursion_sha256": transition["world_recursion_sha256"],
        "preserved": list(transition["preserved"]),
        "reason": transition["delta_summary"],
        "claim_limit": (
            "This is a NAV reorientation proposal grounded in a Dogram path receipt. "
            "Proposal does not activate the heading, prove the trace is causal history, "
            "or erase the previous heading."
        ),
    }


def render_card(packet):
    validate_packet(packet)
    card = packet["pocket_card"]
    lines = [card["title"], card["carry_line"], ""]
    lines.extend(f"{i}. {step}" for i, step in enumerate(card["steps"], start=1))
    return "\n".join(lines) + "\n"


def build_parser():
    parser = argparse.ArgumentParser(description="NAV Bridge Packet 001 runtime")
    parser.add_argument("--packet", default="bridge/nav.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")
    sub.add_parser("card")

    orient = sub.add_parser("orient")
    orient.add_argument("--heading", required=True)
    orient.add_argument("--preserve", action="append", required=True)
    orient.add_argument("--aperture", action="append", required=True)
    orient.add_argument("--move", required=True)
    orient.add_argument("--stop", required=True)
    orient.add_argument(
        "--claim-limit",
        default="This bounded move does not establish a final answer.",
    )
    orient.add_argument("-o", "--out")

    encounter = sub.add_parser("encounter")
    encounter.add_argument("receipt")
    encounter.add_argument("--observed", required=True)
    encounter.add_argument("--delta", required=True)
    encounter.add_argument("--next-heading", required=True)
    encounter.add_argument("-o", "--out")

    game = sub.add_parser("game")
    game.add_argument("receipt")

    reorient = sub.add_parser("reorient")
    reorient.add_argument("transition")
    reorient.add_argument("-o", "--out")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        packet = validate_packet(_read_json(args.packet))
        if args.command == "validate":
            print(f"VALID {packet['id']}: {packet['core_distinction']}")
            return 0
        if args.command == "card":
            sys.stdout.write(render_card(packet))
            return 0
        if args.command == "orient":
            _write_json(make_orientation(args), args.out)
            return 0
        if args.command == "encounter":
            receipt = _read_json(args.receipt)
            _write_json(
                record_encounter(receipt, args.observed, args.delta, args.next_heading),
                args.out,
            )
            return 0
        if args.command == "game":
            _write_json(game_event(_read_json(args.receipt)), None)
            return 0
        if args.command == "reorient":
            _write_json(make_reorientation(_read_json(args.transition)), args.out)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
