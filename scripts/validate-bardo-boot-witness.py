#!/usr/bin/env python3
"""Validate BARDO-BOOT-WITNESS-001 without silently promoting its claims."""
from __future__ import annotations

import json
import sys
from pathlib import Path

SCHEMA = "static-os.bardo-boot-witness/v0"
EVIDENCE_SCHEMA = "static-os.bardo-boot-witness-evidence/v0"
EXPECTED_HASH = "af82b9a3b2d5eeb1ce3d58038b3415ca62f0815bd6f0a04662ec8cf5b773d171"
EXPECTED_SIZE = 670478
RELATTE_PIN = "5d96af53a730b0ce3111e8551e62030596815069"


def load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {path}")
    return value


def same_public_key(left: dict, right: dict) -> bool:
    return left.get("signing", {}).get("public_key") == right.get("signing", {}).get("public_key")


def validate(manifest: dict, fixture_dir: Path) -> dict:
    if manifest.get("schema") != SCHEMA or manifest.get("id") != "BARDO-BOOT-WITNESS-001":
        raise ValueError("unsupported witness contract")
    if manifest.get("status") != "host-executed-exact-byte-witness":
        raise ValueError("witness status drift")

    source = manifest.get("source", {})
    if source.get("particular") != f"sha256:{EXPECTED_HASH}" or source.get("byte_length") != EXPECTED_SIZE:
        raise ValueError("source particular drift")
    if source.get("detected_media_type") != "image/jpeg" or source.get("filename_media_type_mismatch") is not True:
        raise ValueError("source media witness drift")
    if source.get("bytes_vendored_in_repository") is not False:
        raise ValueError("repository must not pretend the source bytes are vendored")

    stacked = manifest.get("stacked_on", {})
    if stacked.get("relatte_commit") != RELATTE_PIN:
        raise ValueError("reLATTE proof pin drift")

    admission = manifest.get("admission", {})
    if admission != {
        "mandatory_hold": True,
        "automatic": False,
        "decision": "ADMIT",
        "authority": "destination-local-human-explicit",
    }:
        raise ValueError("admission contract drift")

    claims = manifest.get("claims", {})
    required_false = {
        "actual_process_restart_proven",
        "vm_cold_boot_proven",
        "physical_cold_boot_proven",
        "live_supabardo_membrane_used",
        "second_live_membrane_crossing_proven",
        "supabardo_extraction_gate_satisfied",
    }
    for key in required_false:
        if claims.get(key) is not False:
            raise ValueError(f"claim silently promoted: {key}")
    if claims.get("host_root_reopen_proven") is not True:
        raise ValueError("host root reopen witness lost")

    crossing = load(fixture_dir / "crossing.json")
    release = load(fixture_dir / "release.json")
    hold = load(fixture_dir / "hold.json")
    admit = load(fixture_dir / "admit.json")
    exit_receipt = load(fixture_dir / "exit.json")
    evidence = load(fixture_dir / "evidence.json")

    if evidence.get("schema") != EVIDENCE_SCHEMA or evidence.get("id") != "BARDO-BOOT-WITNESS-001":
        raise ValueError("evidence schema drift")
    esource = evidence.get("source", {})
    if esource.get("sha256") != EXPECTED_HASH or esource.get("byte_length") != EXPECTED_SIZE:
        raise ValueError("evidence source drift")
    if esource.get("bytes_vendored_in_repository") is not False:
        raise ValueError("evidence falsely claims vendored bytes")

    payload = crossing.get("payload_refs", [])
    if len(payload) != 1 or payload[0].get("address") != f"sha256:{EXPECTED_HASH}":
        raise ValueError("crossing payload address drift")
    if payload[0].get("media_type") != "image/jpeg" or payload[0].get("byte_length") != EXPECTED_SIZE:
        raise ValueError("crossing payload media witness drift")

    crossing_id = crossing.get("crossing_id")
    receipts = [release, hold, admit, exit_receipt]
    if not crossing_id or any(row.get("crossing_id") != crossing_id for row in receipts):
        raise ValueError("crossing ancestry drift")

    if release.get("kind") != "BBW001_RELEASE" or release.get("post_state_ref") != crossing_id:
        raise ValueError("release chain drift")
    if f"sha256:{EXPECTED_HASH}" not in release.get("residual_refs", []):
        raise ValueError("release erased source residual")

    supa = hold.get("extensions", {}).get("supabardo", {})
    if hold.get("kind") != "BBW001_HOLD" or hold.get("semantic_effect") != "none":
        raise ValueError("mandatory HOLD drift")
    if supa.get("state") != "OPEN" or supa.get("destination_disposition") is not None:
        raise ValueError("HOLD manufactured destination meaning")
    if supa.get("mandatory_hold") is not True:
        raise ValueError("mandatory HOLD marker lost")
    if hold.get("pre_state_ref") != release.get("receipt_id"):
        raise ValueError("HOLD ancestry drift")

    local = admit.get("extensions", {}).get("local_receiver", {})
    if admit.get("kind") != "R3_ADMIT" or local.get("disposition") != "ADMIT":
        raise ValueError("local admission drift")
    if local.get("supabardo_unresolved_receipt_id") != hold.get("receipt_id"):
        raise ValueError("admission bypassed HOLD")
    if admit.get("post_state_ref") != f"sha256:{EXPECTED_HASH}":
        raise ValueError("Corpus constitution no longer binds exact bytes")

    if exit_receipt.get("kind") != "BBW001_EXIT" or exit_receipt.get("semantic_effect") != "none":
        raise ValueError("Bardo EXIT semantics drift")
    if exit_receipt.get("pre_state_ref") != hold.get("receipt_id") or exit_receipt.get("post_state_ref") != admit.get("receipt_id"):
        raise ValueError("EXIT ancestry drift")

    if not same_public_key(crossing, release):
        raise ValueError("source authority split unexpectedly")
    if not same_public_key(hold, exit_receipt):
        raise ValueError("Bardo witness authority split unexpectedly")
    if same_public_key(crossing, hold) or same_public_key(crossing, admit) or same_public_key(hold, admit):
        raise ValueError("authority domains collapsed")

    erelatte = evidence.get("relatte", {})
    expected_ids = {
        "crossing_id": crossing_id,
        "release_receipt_id": release.get("receipt_id"),
        "hold_receipt_id": hold.get("receipt_id"),
        "admit_receipt_id": admit.get("receipt_id"),
        "exit_receipt_id": exit_receipt.get("receipt_id"),
    }
    for key, expected in expected_ids.items():
        if erelatte.get(key) != expected:
            raise ValueError(f"evidence ID drift: {key}")
    if erelatte.get("proof_pin") != RELATTE_PIN or erelatte.get("three_distinct_authority_keys") is not True:
        raise ValueError("evidence authority/pin drift")

    hashes = [row.get("sha256") for row in evidence.get("stages", [])]
    if len(hashes) != 5 or set(hashes) != {EXPECTED_HASH}:
        raise ValueError("particular changed across witness stages")

    decision = evidence.get("decision", {})
    if decision.get("disposition") != "ADMIT" or decision.get("mandatory_hold_preceded_decision") is not True:
        raise ValueError("decision/HOLD ordering drift")
    if decision.get("repository_can_independently_prove_human_identity") is not False:
        raise ValueError("repository overclaims human authority proof")

    custody = evidence.get("custody", {})
    if custody.get("same_root") is not True or custody.get("distinct_boots") is not True:
        raise ValueError("root/boot distinction lost")
    if custody.get("corpus_sha256") != EXPECTED_HASH:
        raise ValueError("reopened Corpus bytes changed")
    if custody.get("bardo_runtime_destroyed") is not True or custody.get("persistent_supabardo_interior") is not False:
        raise ValueError("Bardo persistence boundary drift")

    eclaims = evidence.get("claims", {})
    for key in required_false - {"supabardo_extraction_gate_satisfied"}:
        if eclaims.get(key) is not False:
            raise ValueError(f"evidence claim silently promoted: {key}")
    if eclaims.get("host_root_reopen_proven") is not True or eclaims.get("exact_byte_identity_preserved") is not True:
        raise ValueError("evidence result lost")

    return evidence


def main(argv=None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: validate-bardo-boot-witness.py MANIFEST FIXTURE_DIR", file=sys.stderr)
        return 2
    try:
        manifest = load(Path(args[0]))
        validate(manifest, Path(args[1]))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print("VALID BARDO-BOOT-WITNESS-001 bounded host witness")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
