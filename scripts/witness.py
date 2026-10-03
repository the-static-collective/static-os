#!/usr/bin/env python3
"""WITNESS Bridge Packet 003 runtime.

This tool ingests provenance-bearing artifacts without upgrading their claims.
The first executable crossing is a contacted NAV receipt -> WITNESS intake.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PACKET_SCHEMA = "static.bridge-packet/v0"
PACKET_ID = "witness-001"
EXPECTED_INVARIANT = "SOURCE ≠ STORY."
NAV_RECEIPT_SCHEMA = "static.nav-receipt/v0"
INTAKE_SCHEMA = "static.witness-intake/v0"


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value):
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


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
    if packet.get("id") != PACKET_ID:
        raise ValueError("unexpected packet id")
    if packet.get("core_distinction") != EXPECTED_INVARIANT:
        raise ValueError("WITNESS invariant changed")
    crossings = packet.get("crossings")
    if not isinstance(crossings, dict):
        raise ValueError("crossing contract missing")
    if NAV_RECEIPT_SCHEMA not in crossings.get("accepts", []):
        raise ValueError("NAV receipt crossing not declared")
    if INTAKE_SCHEMA not in crossings.get("emits", []):
        raise ValueError("WITNESS intake emission not declared")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    if runtime.get("commands") != ["validate", "intake", "inspect"]:
        raise ValueError("unexpected runtime command set")
    return packet


def validate_nav_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != NAV_RECEIPT_SCHEMA:
        raise ValueError("unsupported source schema")
    if receipt.get("packet_id") != "nav-001":
        raise ValueError("source packet mismatch")
    if receipt.get("status") != "contacted":
        raise ValueError("WITNESS intake requires a contacted NAV receipt")
    for key in (
        "heading",
        "bounded_move",
        "stop_condition",
        "claim_limit",
        "observed",
        "delta",
        "next_heading",
    ):
        if not isinstance(receipt.get(key), str) or not receipt[key]:
            raise ValueError(f"contacted NAV receipt missing: {key}")
    for key in ("preserve", "aperture"):
        if not isinstance(receipt.get(key), list) or not receipt[key]:
            raise ValueError(f"contacted NAV receipt missing: {key}")
    return receipt


def validate_intake(intake):
    if not isinstance(intake, dict) or intake.get("schema") != INTAKE_SCHEMA:
        raise ValueError("unsupported intake schema")
    if intake.get("packet_id") != PACKET_ID:
        raise ValueError("intake packet mismatch")
    source = intake.get("source")
    if not isinstance(source, dict):
        raise ValueError("source record missing")
    if source.get("schema") != NAV_RECEIPT_SCHEMA:
        raise ValueError("unexpected source schema")
    if source.get("packet_id") != "nav-001" or source.get("status") != "contacted":
        raise ValueError("unexpected NAV source identity")
    digest = source.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("source digest missing")
    records = intake.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("expected four source-preserving records")
    expected_classes = [
        "source_record",
        "derivative_interpretation",
        "orientation_proposal",
        "source_limit",
    ]
    if [record.get("claim_class") for record in records] != expected_classes:
        raise ValueError("claim classes drifted or collapsed")
    for record in records:
        if not isinstance(record.get("value"), str):
            raise ValueError("record value must remain text")
        if not record.get("source_field"):
            raise ValueError("record source field missing")
    establishes = intake.get("establishes")
    does_not = intake.get("does_not_establish")
    if not isinstance(establishes, list) or not establishes:
        raise ValueError("establishes boundary missing")
    if not isinstance(does_not, list) or not does_not:
        raise ValueError("does-not-establish boundary missing")
    if not isinstance(intake.get("corrections"), list):
        raise ValueError("corrections must be a list")
    return intake


def intake_nav(receipt):
    validate_nav_receipt(receipt)
    intake = {
        "schema": INTAKE_SCHEMA,
        "packet_id": PACKET_ID,
        "source": {
            "schema": receipt["schema"],
            "packet_id": receipt["packet_id"],
            "status": receipt["status"],
            "sha256": _sha256(receipt),
        },
        "records": [
            {
                "kind": "reported_observation",
                "value": receipt["observed"],
                "source_field": "observed",
                "claim_class": "source_record",
            },
            {
                "kind": "reported_delta",
                "value": receipt["delta"],
                "source_field": "delta",
                "claim_class": "derivative_interpretation",
            },
            {
                "kind": "next_heading",
                "value": receipt["next_heading"],
                "source_field": "next_heading",
                "claim_class": "orientation_proposal",
            },
            {
                "kind": "claim_limit",
                "value": receipt["claim_limit"],
                "source_field": "claim_limit",
                "claim_class": "source_limit",
            },
        ],
        "establishes": [
            "A contacted NAV receipt artifact was ingested.",
            "The source artifact records the preserved observation text.",
            "The source artifact records a delta interpretation and a next-heading proposal.",
            "The source artifact carries an explicit claim limit.",
        ],
        "does_not_establish": [
            "The reported outside event is independently verified by WITNESS.",
            "The source's delta interpretation is correct.",
            "The source's next-heading proposal should be followed.",
            "The source's world-contact claim has been independently reproduced.",
        ],
        "corrections": [],
    }
    return validate_intake(intake)


def inspect_intake(intake):
    validate_intake(intake)
    classes = Counter(record["claim_class"] for record in intake["records"])
    return {
        "schema": "static.witness-inspection/v0",
        "packet_id": PACKET_ID,
        "source_sha256": intake["source"]["sha256"],
        "record_count": len(intake["records"]),
        "claim_classes": dict(sorted(classes.items())),
        "establishes_count": len(intake["establishes"]),
        "does_not_establish_count": len(intake["does_not_establish"]),
        "correction_count": len(intake["corrections"]),
        "independent_verification_claimed": False,
        "next_door": "Acquire a genuinely independent witness or preserve a correction without rewriting this source.",
    }


def build_parser():
    parser = argparse.ArgumentParser(description="WITNESS Bridge Packet 003 runtime")
    parser.add_argument("--packet", default="bridge/witness.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    intake = sub.add_parser("intake")
    intake.add_argument("source")
    intake.add_argument("-o", "--out")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("intake")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        packet = validate_packet(_read_json(args.packet))
        if args.command == "validate":
            print(f"VALID {packet['id']}: {packet['core_distinction']}")
            return 0
        if args.command == "intake":
            _write_json(intake_nav(_read_json(args.source)), args.out)
            return 0
        if args.command == "inspect":
            _write_json(inspect_intake(_read_json(args.intake)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
