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
SB001_RELATTE_COMMIT = "5d96af53a730b0ce3111e8551e62030596815069"
SB001_EVIDENCE_SET_ID = "sb001-evidence-v0:cbb5e16c8209e1978d1cc1910c4b5128fa58bdab1bb9bbd7d4112ebd0f6c5174"


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

    if by_id["relatte"].get("commit") != SB001_RELATTE_COMMIT:
        raise ValueError("reLATTE pin must carry the proven SB-001 specimen")

    sb = by_id["supabardo"]
    if sb.get("runtime") != "sb-001-proven-external-specimen":
        raise ValueError("SupaBardo runtime posture must remain proven external specimen")
    if sb.get("spec_path") != "docs/superpowers/specs/2026-08-25-supabardo-crossing-field-design.md":
        raise ValueError("SupaBardo source spec drift")
    sb_proof = sb.get("proof")
    if not isinstance(sb_proof, dict):
        raise ValueError("missing SB-001 proof binding")
    if sb_proof.get("repository") != "the-static-collective/reLATTE":
        raise ValueError("SB-001 proof repository drift")
    if sb_proof.get("commit") != SB001_RELATTE_COMMIT:
        raise ValueError("SB-001 proof commit drift")
    if sb_proof.get("evidence_set_id") != SB001_EVIDENCE_SET_ID:
        raise ValueError("SB-001 evidence-set drift")
    if sb_proof.get("runtime_destroyed_after_export") is not True:
        raise ValueError("SB-001 must preserve destructible membrane result")
    if sb_proof.get("reconstruction_requires_live_membrane") is not False:
        raise ValueError("SB-001 reconstruction must not require live Bardo")
    if sb_proof.get("verified_tests") != 134:
        raise ValueError("SB-001 verified test-count witness drift")

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
    proof = bardo.get("proof")
    if not isinstance(proof, dict):
        raise ValueError("missing SupaBardo proof status")
    if proof.get("status") != "proven-external-destructible-specimen":
        raise ValueError("SupaBardo proof status drift")
    if proof.get("commit") != SB001_RELATTE_COMMIT:
        raise ValueError("SupaBardo proof pin drift")
    if proof.get("evidence_set_id") != SB001_EVIDENCE_SET_ID:
        raise ValueError("SupaBardo proof evidence drift")
    if proof.get("runtime_destroyed_after_export") is not True:
        raise ValueError("Bardo runtime destruction proof lost")
    if proof.get("live_membrane_required_for_reconstruction") is not False:
        raise ValueError("live Bardo must not become historical dependency")

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
        "supabardo_sb001": "proven-external-destructible-specimen",
        "persistent_volume": "mount-and-lineage-candidate",
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
        "SERVICE DEATH != HISTORY DEATH",
        "DURABLE RECEIPT != IMMORTAL BARDO",
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
