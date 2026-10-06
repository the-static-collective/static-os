#!/usr/bin/env python3
"""Validate STATIC OS WHOLE-BODY-001 composition without executing any organ."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

SCHEMA = "static-os.whole-body/v0"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
EXPECTED = {
    "ghot": ("the-static-collective/GHoT", "body-capability-liveness"),
    "relatte": ("the-static-collective/reLATTE", "crossing-grammar-receipts"),
    "jubilee": ("the-static-collective/Jubilee-Engine-VM", "bounded-occurrence-provenance"),
    "corpus": ("the-static-collective/corpus-os", "local-constitution-causal-present"),
    "tranchnode": ("the-static-collective/tranchnode", "durable-addressed-particulars"),
    "supabardo": ("the-static-collective/Human-Witness", "unresolved-crossing-field"),
}
LIFECYCLE = ["ENTER", "FORM", "WITNESS", "WAIT", "EXIT", "DECAY"]


def validate(value):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("unsupported WHOLE-BODY schema")
    if value.get("id") != "WHOLE-BODY-001":
        raise ValueError("wrong composition id")
    if value.get("status") != "source-bundle-candidate":
        raise ValueError("runtime/boot status must not be pre-promoted")

    organs = value.get("organs")
    if not isinstance(organs, list):
        raise ValueError("organs must be a list")
    by_id = {}
    for organ in organs:
        if not isinstance(organ, dict):
            raise ValueError("organ entry must be an object")
        oid = organ.get("id")
        if oid in by_id:
            raise ValueError(f"duplicate organ id: {oid}")
        by_id[oid] = organ
    if set(by_id) != set(EXPECTED):
        raise ValueError("exact organ set changed")

    for oid, (repo, role) in EXPECTED.items():
        organ = by_id[oid]
        if organ.get("repository") != repo:
            raise ValueError(f"{oid} repository mismatch")
        if organ.get("role") != role:
            raise ValueError(f"{oid} role mismatch")
        if organ.get("image_source") is not True:
            raise ValueError(f"{oid} exact source must be bundled")
        commit = organ.get("commit")
        if not isinstance(commit, str) or not SHA40.fullmatch(commit):
            raise ValueError(f"{oid} commit must be exact 40-hex SHA")

    sb = by_id["supabardo"]
    if sb.get("runtime") != "sb-001-external-specimen-only":
        raise ValueError("SupaBardo must remain an external bounded specimen")
    if sb.get("spec_path") != "docs/superpowers/specs/2026-08-25-supabardo-crossing-field-design.md":
        raise ValueError("SupaBardo source spec drift")

    bardo = value.get("supabardo")
    if not isinstance(bardo, dict):
        raise ValueError("missing SupaBardo boundary")
    if bardo.get("lifecycle") != LIFECYCLE:
        raise ValueError("SupaBardo lifecycle drift")
    if bardo.get("canonical") is not False or bardo.get("durable_memory_owner") is not False:
        raise ValueError("SupaBardo must not become canon or durable memory owner")
    if bardo.get("automatic_admission") is not False:
        raise ValueError("SupaBardo must not admit automatically")
    if bardo.get("meaning") != "receiver-local":
        raise ValueError("crossing meaning must remain receiver-local")

    deploy = value.get("deployment")
    if not isinstance(deploy, dict):
        raise ValueError("missing deployment policy")
    required_false = ("auto_start_foreign_organs", "auto_admit_crossings", "auto_apply_git_updates")
    if any(deploy.get(key) is not False for key in required_false):
        raise ValueError("automatic authority escalation is forbidden")
    if deploy.get("vendor_exact_sources_into_iso") is not True:
        raise ValueError("WHOLE-BODY source bundle must be image-vendored")
    if deploy.get("requires_persistence_for_cross_boot_identity") is not True:
        raise ValueError("cross-boot identity must not be inferred without persistence")

    claims = value.get("claims")
    if not isinstance(claims, dict):
        raise ValueError("missing bounded claims")
    expected_claims = {
        "source_bundle": "buildable-candidate",
        "runtime_composition": "unverified",
        "supabardo_sb001": "external-in-progress",
        "persistent_volume": "not_implemented",
        "cross_boot_continuity": "not_proven",
        "physical_boot": "not_proven",
    }
    if claims != expected_claims:
        raise ValueError("WHOLE-BODY claims were silently promoted")

    laws = set(value.get("laws", []))
    for law in {
        "RECEIVED != ADMITTED",
        "UNRESOLVED != ABSENT",
        "SUPABARDO STATE != CANON",
        "BOOT != CONTINUITY",
    }:
        if law not in laws:
            raise ValueError(f"missing law: {law}")
    return value


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: validate-whole-body.py PATH", file=sys.stderr)
        return 2
    try:
        value = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        validate(value)
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print("VALID WHOLE-BODY-001 source-bundle candidate")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
