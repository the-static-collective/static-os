#!/usr/bin/env python3
"""Fresh NAV cycle rooted in an admitted typed-weave generation.

The composed generation becomes a new navigation origin by address. Ordinary NAV
orientation/contact receipts remain ordinary; the typed weave provenance stays
recoverable in a shared content-addressed cycle ledger.
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


nav = _load("static_os_nav_for_composed_cycle", "scripts/nav.py")
weave_nav = _load("static_os_weave_nav_for_cycle", "scripts/weave_nav.py")

ORIGIN_SCHEMA = "static.nav-composed-origin/v0"
CYCLE_SCHEMA = "static.nav-composed-cycle/v0"
LEDGER_SCHEMA = "static.nav-composed-cycle-ledger/v0"
RELATION_KINDS = {"branch_continuation", "open_branch"}

ORIGIN_KEYS = {
    "schema",
    "source_generation_sha256",
    "admitted_heading",
    "admission_sha256",
    "weave_capsule_sha256",
    "parent_set_sha256",
    "weave_ledger_sha256",
    "root_cycle_digest",
    "relation_kinds",
    "claim_limit",
}
CYCLE_KEYS = {
    "schema",
    "cycle_id",
    "origin_sha256",
    "orientation_sha256",
    "contact_sha256",
    "from_heading",
    "next_heading",
    "status",
    "relation_kinds",
    "provenance_mode",
    "claim_limit",
}


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


def make_origin(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
    admission,
    generation,
):
    result = weave_nav.verify_generation(
        base_history,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
        admission,
        generation,
    )
    if result.get("status") != "complete":
        raise ValueError(f"source weave generation is not complete: {result.get('reason')}")

    origin = {
        "schema": ORIGIN_SCHEMA,
        "source_generation_sha256": canonical_digest(generation),
        "admitted_heading": generation["admitted_heading"],
        "admission_sha256": generation["admission_sha256"],
        "weave_capsule_sha256": generation["weave_capsule_sha256"],
        "parent_set_sha256": generation["parent_set_sha256"],
        "weave_ledger_sha256": generation["weave_ledger_sha256"],
        "root_cycle_digest": generation["root_cycle_digest"],
        "relation_kinds": list(generation["relation_kinds"]),
        "claim_limit": (
            "This origin makes an admitted typed-weave generation available as the "
            "starting heading of a fresh NAV cycle by content address. It does not "
            "embed the parents or imply that composition erased their relation types."
        ),
    }
    return validate_origin(origin)


def validate_origin(origin):
    if not isinstance(origin, dict) or origin.get("schema") != ORIGIN_SCHEMA:
        raise ValueError("unsupported composed NAV origin schema")
    if set(origin) != ORIGIN_KEYS:
        raise ValueError("composed NAV origin shape drifted")
    for key in ("admitted_heading", "claim_limit"):
        if not isinstance(origin.get(key), str) or not origin[key]:
            raise ValueError(f"composed NAV origin missing: {key}")
    for key in (
        "source_generation_sha256",
        "admission_sha256",
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        value = origin.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"composed NAV origin digest missing: {key}")
    kinds = origin.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("composed NAV origin relation kinds invalid")
    return origin


def verify_origin_against_generation(origin, generation):
    validate_origin(origin)
    weave_nav.validate_generation(generation)
    if origin["source_generation_sha256"] != canonical_digest(generation):
        raise ValueError("origin generation digest mismatch")
    if origin["admitted_heading"] != generation["admitted_heading"]:
        raise ValueError("origin heading differs from admitted generation")
    for key in (
        "admission_sha256",
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        if origin[key] != generation[key]:
            raise ValueError(f"origin provenance mismatch: {key}")
    if sorted(origin["relation_kinds"]) != sorted(generation["relation_kinds"]):
        raise ValueError("origin relation kinds drifted")
    return origin


def start_cycle(
    origin,
    generation,
    preserve,
    aperture,
    bounded_move,
    stop_condition,
    claim_limit,
):
    verify_origin_against_generation(origin, generation)
    if not preserve:
        raise ValueError("fresh cycle preserve set missing")
    if not aperture:
        raise ValueError("fresh cycle aperture missing")
    if not bounded_move:
        raise ValueError("fresh cycle bounded move missing")
    if not stop_condition:
        raise ValueError("fresh cycle stop condition missing")

    receipt = {
        "schema": nav.RECEIPT_SCHEMA,
        "packet_id": "nav-001",
        "status": "oriented",
        "heading": origin["admitted_heading"],
        "preserve": list(preserve),
        "aperture": list(aperture),
        "bounded_move": bounded_move,
        "stop_condition": stop_condition,
        "claim_limit": claim_limit,
        "observed": None,
        "delta": None,
        "next_heading": None,
    }
    return nav.validate_receipt(receipt)


def contact_cycle(
    generation,
    origin,
    orientation,
    observed,
    delta,
    next_heading,
):
    verify_origin_against_generation(origin, generation)
    nav.validate_receipt(orientation)
    if orientation["status"] != "oriented":
        raise ValueError("composed cycle must start from an oriented NAV receipt")
    if orientation["heading"] != origin["admitted_heading"]:
        raise ValueError("fresh NAV cycle does not begin at composed admitted heading")

    contact = nav.record_encounter(
        orientation,
        observed,
        delta,
        next_heading,
    )

    cycle = {
        "schema": CYCLE_SCHEMA,
        "cycle_id": "weave-origin-nav-cycle-001",
        "origin_sha256": canonical_digest(origin),
        "orientation_sha256": canonical_digest(orientation),
        "contact_sha256": canonical_digest(contact),
        "from_heading": origin["admitted_heading"],
        "next_heading": contact["next_heading"],
        "status": "contacted",
        "relation_kinds": list(origin["relation_kinds"]),
        "provenance_mode": "addressable",
        "claim_limit": (
            "This cycle records a fresh NAV encounter whose origin is an admitted "
            "typed-weave generation. The cycle does not embed the prior weave and "
            "does not imply the still-open branch was closed or forgotten."
        ),
    }
    validate_cycle(cycle)

    generation_digest = canonical_digest(generation)
    origin_digest = canonical_digest(origin)
    orientation_digest = canonical_digest(orientation)
    contact_digest = canonical_digest(contact)
    cycle_digest = canonical_digest(cycle)

    ledger = {
        "schema": LEDGER_SCHEMA,
        "source_generation_sha256": generation_digest,
        "origin_sha256": origin_digest,
        "cycle_sha256": cycle_digest,
        "generations": {generation_digest: generation},
        "origins": {origin_digest: origin},
        "orientations": {orientation_digest: orientation},
        "contacts": {contact_digest: contact},
        "cycles": {cycle_digest: cycle},
        "claim_limit": (
            "This ledger keeps composed history addressable behind a fresh NAV cycle. "
            "Content addressing does not establish causal truth or automatically "
            "upgrade the new contact into an independent witness."
        ),
    }
    result = verify_cycle_ledger(ledger)
    if result.get("status") != "complete":
        raise ValueError(f"new composed cycle did not verify complete: {result.get('reason')}")
    return ledger


def validate_cycle(cycle):
    if not isinstance(cycle, dict) or cycle.get("schema") != CYCLE_SCHEMA:
        raise ValueError("unsupported composed NAV cycle schema")
    if set(cycle) != CYCLE_KEYS:
        raise ValueError("composed NAV cycle shape drifted")
    if cycle.get("status") != "contacted":
        raise ValueError("composed NAV cycle must be contacted")
    if cycle.get("provenance_mode") != "addressable":
        raise ValueError("composed NAV cycle provenance must remain addressable")
    for key in ("cycle_id", "from_heading", "next_heading", "claim_limit"):
        if not isinstance(cycle.get(key), str) or not cycle[key]:
            raise ValueError(f"composed NAV cycle missing: {key}")
    for key in ("origin_sha256", "orientation_sha256", "contact_sha256"):
        value = cycle.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"composed NAV cycle digest missing: {key}")
    kinds = cycle.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("composed NAV cycle relation kinds invalid")
    return cycle


def _incomplete(reason):
    return {"status": "incomplete", "reason": reason}


def _invalid(reason):
    return {"status": "invalid", "reason": reason}


def verify_cycle_ledger(ledger):
    if not isinstance(ledger, dict) or ledger.get("schema") != LEDGER_SCHEMA:
        return _invalid("ledger_shape")
    for bucket_name in ("generations", "origins", "orientations", "contacts", "cycles"):
        if not isinstance(ledger.get(bucket_name), dict):
            return _invalid(f"{bucket_name}_bucket_shape")
    if not ledger.get("claim_limit"):
        return _invalid("claim_limit_missing")

    generation_digest = ledger.get("source_generation_sha256")
    origin_digest = ledger.get("origin_sha256")
    cycle_digest = ledger.get("cycle_sha256")

    generation = ledger["generations"].get(generation_digest)
    if generation is None:
        return _incomplete("missing_generation")
    if canonical_digest(generation) != generation_digest:
        return _invalid("generation_digest_mismatch")
    try:
        weave_nav.validate_generation(generation)
    except ValueError:
        return _invalid("generation_invalid")

    origin = ledger["origins"].get(origin_digest)
    if origin is None:
        return _incomplete("missing_origin")
    if canonical_digest(origin) != origin_digest:
        return _invalid("origin_digest_mismatch")
    try:
        verify_origin_against_generation(origin, generation)
    except ValueError as error:
        return _invalid(str(error).replace(" ", "_"))

    cycle = ledger["cycles"].get(cycle_digest)
    if cycle is None:
        return _incomplete("missing_cycle")
    if canonical_digest(cycle) != cycle_digest:
        return _invalid("cycle_digest_mismatch")
    try:
        validate_cycle(cycle)
    except ValueError as error:
        return _invalid(str(error).replace(" ", "_"))

    orientation = ledger["orientations"].get(cycle["orientation_sha256"])
    if orientation is None:
        return _incomplete("missing_orientation")
    if canonical_digest(orientation) != cycle["orientation_sha256"]:
        return _invalid("orientation_digest_mismatch")

    contact = ledger["contacts"].get(cycle["contact_sha256"])
    if contact is None:
        return _incomplete("missing_contact")
    if canonical_digest(contact) != cycle["contact_sha256"]:
        return _invalid("contact_digest_mismatch")

    try:
        nav.validate_receipt(orientation)
        nav.validate_receipt(contact)
    except ValueError as error:
        return _invalid(str(error).replace(" ", "_"))

    if orientation["status"] != "oriented":
        return _invalid("orientation_status_mismatch")
    if contact["status"] != "contacted":
        return _invalid("contact_status_mismatch")
    if orientation["heading"] != origin["admitted_heading"]:
        return _invalid("origin_heading_mismatch")
    if contact["heading"] != orientation["heading"]:
        return _invalid("contact_heading_mismatch")
    if cycle["from_heading"] != origin["admitted_heading"]:
        return _invalid("cycle_origin_heading_mismatch")
    if cycle["next_heading"] != contact["next_heading"]:
        return _invalid("cycle_next_heading_mismatch")
    if cycle["origin_sha256"] != origin_digest:
        return _invalid("cycle_origin_digest_mismatch")
    if sorted(cycle["relation_kinds"]) != sorted(origin["relation_kinds"]):
        return _invalid("cycle_relation_kinds_mismatch")

    if set(ledger["generations"]) != {generation_digest}:
        return _invalid("undeclared_generation_present")
    if set(ledger["origins"]) != {origin_digest}:
        return _invalid("undeclared_origin_present")
    if set(ledger["orientations"]) != {cycle["orientation_sha256"]}:
        return _invalid("undeclared_orientation_present")
    if set(ledger["contacts"]) != {cycle["contact_sha256"]}:
        return _invalid("undeclared_contact_present")
    if set(ledger["cycles"]) != {cycle_digest}:
        return _invalid("undeclared_cycle_present")

    return {
        "status": "complete",
        "reason": None,
        "source_generation_sha256": generation_digest,
        "origin_sha256": origin_digest,
        "cycle_sha256": cycle_digest,
        "from_heading": cycle["from_heading"],
        "next_heading": cycle["next_heading"],
        "relation_kinds": cycle["relation_kinds"],
        "provenance_mode": cycle["provenance_mode"],
        "orientation_status": orientation["status"],
        "contact_status": contact["status"],
        "generation_embedded_in_cycle": False,
        "typed_parents_embedded_in_cycle": False,
    }


def inspect(ledger):
    result = verify_cycle_ledger(ledger)
    return {
        "schema": "static.nav-composed-cycle-inspection/v0",
        **result,
        "composed_history_is_new_ground": (
            result.get("status") == "complete"
            and result.get("orientation_status") == "oriented"
            and result.get("contact_status") == "contacted"
        ),
        "typed_provenance_preserved": (
            set(result.get("relation_kinds", [])) == RELATION_KINDS
            if result.get("status") == "complete" else None
        ),
        "open_branch_closed": False,
        "automatic_authority_claimed": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Fresh NAV cycle from admitted weave generation")
    sub = parser.add_subparsers(dest="command", required=True)

    origin = sub.add_parser("origin")
    for name in (
        "base_history",
        "braid_ledger",
        "branch_set",
        "weave_ledger",
        "parent_set",
        "weave_capsule",
        "admission",
        "generation",
    ):
        origin.add_argument(name)
    origin.add_argument("-o", "--out")

    start = sub.add_parser("start")
    start.add_argument("origin")
    start.add_argument("generation")
    start.add_argument("--preserve", action="append", required=True)
    start.add_argument("--aperture", action="append", required=True)
    start.add_argument("--move", required=True)
    start.add_argument("--stop", required=True)
    start.add_argument(
        "--claim-limit",
        default="This fresh cycle does not establish a final answer.",
    )
    start.add_argument("-o", "--out")

    contact = sub.add_parser("contact")
    contact.add_argument("generation")
    contact.add_argument("origin")
    contact.add_argument("orientation")
    contact.add_argument("--observed", required=True)
    contact.add_argument("--delta", required=True)
    contact.add_argument("--next-heading", required=True)
    contact.add_argument("-o", "--out")

    verify = sub.add_parser("verify")
    verify.add_argument("ledger")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("ledger")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "origin":
            values = [
                _read_json(getattr(args, name))
                for name in (
                    "base_history",
                    "braid_ledger",
                    "branch_set",
                    "weave_ledger",
                    "parent_set",
                    "weave_capsule",
                    "admission",
                    "generation",
                )
            ]
            _write_json(make_origin(*values), args.out)
            return 0
        if args.command == "start":
            _write_json(
                start_cycle(
                    _read_json(args.origin),
                    _read_json(args.generation),
                    args.preserve,
                    args.aperture,
                    args.move,
                    args.stop,
                    args.claim_limit,
                ),
                args.out,
            )
            return 0
        if args.command == "contact":
            _write_json(
                contact_cycle(
                    _read_json(args.generation),
                    _read_json(args.origin),
                    _read_json(args.orientation),
                    args.observed,
                    args.delta,
                    args.next_heading,
                ),
                args.out,
            )
            return 0
        if args.command == "verify":
            _write_json(verify_cycle_ledger(_read_json(args.ledger)), None)
            return 0
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.ledger)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
