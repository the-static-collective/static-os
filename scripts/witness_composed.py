#!/usr/bin/env python3
"""WITNESS adapter for a fresh NAV contact rooted in composed history.

The NAV contact is ingested through the existing WITNESS intake unchanged.
Typed-weave provenance remains a separate addressable sidecar.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


witness = _load("static_os_witness_for_composed_intake", "scripts/witness.py")
weave_cycle = _load("static_os_weave_cycle_for_witness", "scripts/weave_cycle.py")

SCHEMA = "static.witness-composed-intake/v0"
RELATION_KINDS = {"branch_continuation", "open_branch"}

EXPECTED_CLASSES = [
    "source_record",
    "derivative_interpretation",
    "orientation_proposal",
    "source_limit",
]


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


def validate_composed_intake(value):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("unsupported composed WITNESS intake schema")
    if value.get("packet_id") != "witness-001":
        raise ValueError("composed WITNESS packet mismatch")

    source = value.get("source")
    if not isinstance(source, dict):
        raise ValueError("composed WITNESS source missing")
    if source.get("schema") != "static.nav-receipt/v0":
        raise ValueError("composed WITNESS source schema mismatch")
    if source.get("packet_id") != "nav-001" or source.get("status") != "contacted":
        raise ValueError("composed WITNESS source identity mismatch")
    for key in ("sha256", "intake_sha256"):
        digest = source.get(key)
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"composed WITNESS source digest missing: {key}")

    provenance = value.get("origin_provenance")
    if not isinstance(provenance, dict):
        raise ValueError("composed WITNESS origin provenance missing")
    for key in (
        "cycle_sha256",
        "origin_sha256",
        "source_generation_sha256",
        "admission_sha256",
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        digest = provenance.get(key)
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError(f"composed WITNESS provenance digest missing: {key}")

    kinds = provenance.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("composed WITNESS relation kinds invalid")

    records = value.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("composed WITNESS expected four source records")
    if [record.get("claim_class") for record in records] != EXPECTED_CLASSES:
        raise ValueError("composed WITNESS claim classes drifted")
    for record in records:
        if not isinstance(record.get("value"), str):
            raise ValueError("composed WITNESS record value must remain text")
        if not record.get("source_field"):
            raise ValueError("composed WITNESS source field missing")

    if not isinstance(value.get("establishes"), list) or not value["establishes"]:
        raise ValueError("composed WITNESS establishes boundary missing")
    if not isinstance(value.get("does_not_establish"), list) or not value["does_not_establish"]:
        raise ValueError("composed WITNESS does-not-establish boundary missing")
    if not isinstance(value.get("corrections"), list):
        raise ValueError("composed WITNESS corrections must be a list")
    if not value.get("next_door"):
        raise ValueError("composed WITNESS next door missing")
    return value


def intake_cycle(ledger):
    verification = weave_cycle.verify_cycle_ledger(ledger)
    if verification.get("status") != "complete":
        raise ValueError(f"composed NAV cycle is not complete: {verification.get('reason')}")

    cycle_digest = ledger["cycle_sha256"]
    cycle = ledger["cycles"][cycle_digest]
    origin_digest = ledger["origin_sha256"]
    origin = ledger["origins"][origin_digest]
    generation_digest = ledger["source_generation_sha256"]
    generation = ledger["generations"][generation_digest]
    contact = ledger["contacts"][cycle["contact_sha256"]]

    ordinary_intake = witness.intake_nav(contact)

    if ordinary_intake["source"]["sha256"] != cycle["contact_sha256"]:
        raise ValueError("ordinary WITNESS intake contact digest mismatch")
    if origin["source_generation_sha256"] != generation_digest:
        raise ValueError("origin does not address source generation")
    if origin["admission_sha256"] != generation["admission_sha256"]:
        raise ValueError("origin/generation admission mismatch")
    if origin["weave_capsule_sha256"] != generation["weave_capsule_sha256"]:
        raise ValueError("origin/generation weave capsule mismatch")
    if origin["parent_set_sha256"] != generation["parent_set_sha256"]:
        raise ValueError("origin/generation parent set mismatch")
    if origin["weave_ledger_sha256"] != generation["weave_ledger_sha256"]:
        raise ValueError("origin/generation weave ledger mismatch")
    if origin["root_cycle_digest"] != generation["root_cycle_digest"]:
        raise ValueError("origin/generation root mismatch")
    if sorted(origin["relation_kinds"]) != sorted(generation["relation_kinds"]):
        raise ValueError("origin/generation relation kinds mismatch")

    value = {
        "schema": SCHEMA,
        "packet_id": "witness-001",
        "source": {
            "schema": contact["schema"],
            "packet_id": contact["packet_id"],
            "status": contact["status"],
            "sha256": cycle["contact_sha256"],
            "intake_sha256": canonical_digest(ordinary_intake),
        },
        "origin_provenance": {
            "cycle_sha256": cycle_digest,
            "origin_sha256": origin_digest,
            "source_generation_sha256": generation_digest,
            "admission_sha256": generation["admission_sha256"],
            "weave_capsule_sha256": generation["weave_capsule_sha256"],
            "parent_set_sha256": generation["parent_set_sha256"],
            "weave_ledger_sha256": generation["weave_ledger_sha256"],
            "root_cycle_digest": generation["root_cycle_digest"],
            "relation_kinds": list(generation["relation_kinds"]),
        },
        "records": [dict(record) for record in ordinary_intake["records"]],
        "establishes": [
            "A fresh contacted NAV receipt was ingested through the ordinary WITNESS intake path.",
            "The ordinary NAV observation, delta, next-heading proposal, and claim limit retain their existing claim classes.",
            "The address of the composed navigation origin survives beside the source record.",
            "The typed parent relation summary remains branch_continuation plus open_branch.",
        ],
        "does_not_establish": [
            "The fresh NAV contact independently verifies the composed history that oriented it.",
            "The composed origin is correct because a fresh contact occurred from it.",
            "The still-open branch was closed, selected against, or erased.",
            "The typed provenance graph has been independently re-audited by WITNESS.",
            "The fresh NAV delta or next-heading proposal is correct.",
        ],
        "corrections": [],
        "next_door": (
            "Treat the contacted NAV receipt as new source material while retaining the "
            "composed-origin address. Any later WORLD comparison must distinguish the "
            "new contact from the history that oriented the move."
        ),
    }
    return validate_composed_intake(value)


def inspect(value):
    validate_composed_intake(value)
    classes = {
        claim_class: sum(
            1 for record in value["records"]
            if record["claim_class"] == claim_class
        )
        for claim_class in EXPECTED_CLASSES
    }
    return {
        "schema": "static.witness-composed-intake-inspection/v0",
        "packet_id": "witness-001",
        "source_sha256": value["source"]["sha256"],
        "intake_sha256": value["source"]["intake_sha256"],
        "origin_sha256": value["origin_provenance"]["origin_sha256"],
        "source_generation_sha256": value["origin_provenance"]["source_generation_sha256"],
        "claim_classes": classes,
        "typed_provenance_preserved": set(
            value["origin_provenance"]["relation_kinds"]
        ) == RELATION_KINDS,
        "ordinary_claim_classes_preserved": [
            record["claim_class"] for record in value["records"]
        ] == EXPECTED_CLASSES,
        "independent_verification_claimed": False,
        "open_branch_closed": False,
        "origin_embedded_in_observation": False,
        "next_door": value["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="WITNESS intake for a composed-origin NAV contact"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    intake = sub.add_parser("intake")
    intake.add_argument("cycle_ledger")
    intake.add_argument("-o", "--out")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("source")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "intake":
            _write_json(intake_cycle(_read_json(args.cycle_ledger)), args.out)
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
