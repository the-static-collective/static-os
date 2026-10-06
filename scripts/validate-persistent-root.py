#!/usr/bin/env python3
"""Validate the PERSISTENT-ROOT-001 OS contract."""
from __future__ import annotations
import json, sys
from pathlib import Path

SCHEMA = "static-os.persistent-root/v0"

EXPECTED_PATHS = {
    "house_users": "users",
    "ghot": "organs/ghot",
    "relatte": "organs/relatte",
    "jubilee": "organs/jubilee",
    "corpus": "organs/corpus",
    "tranchnode": "organs/tranchnode",
    "crossing_exports": "crossing-exports",
    "boot_receipts": "lineage/boots",
    "shutdown_receipts": "lineage/shutdowns",
}

def validate(value):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("unsupported persistence schema")
    if value.get("id") != "PERSISTENT-ROOT-001":
        raise ValueError("wrong persistence id")
    if value.get("status") != "mount-and-lineage-candidate":
        raise ValueError("persistence claim silently promoted")

    device = value.get("device", {})
    expected = {
        "filesystem_label": "STATIC_STATE",
        "filesystem": "ext4",
        "mountpoint": "/var/lib/static-os",
        "auto_format": False,
        "internal_disk_install": False,
    }
    if device != expected:
        raise ValueError("device contract drift or destructive escalation")

    layout = value.get("layout", {})
    if layout.get("version") != 0 or layout.get("paths") != EXPECTED_PATHS:
        raise ValueError("persistent layout drift")

    bardo = value.get("supabardo", {})
    if bardo.get("persistent_interior") is not False:
        raise ValueError("SupaBardo interior must not become persistent")
    if bardo.get("durable_outputs_path") != "crossing-exports":
        raise ValueError("SupaBardo durable-output boundary drift")

    boot = value.get("boot", {})
    if boot.get("fresh_occurrence_each_boot") is not True:
        raise ValueError("each boot must remain a fresh occurrence")
    if boot.get("same_root_does_not_mean_same_process") is not True:
        raise ValueError("root identity must not collapse into process identity")
    if boot.get("missing_previous_shutdown_is_visible") is not True:
        raise ValueError("unclean predecessor termination must remain visible")

    attach = value.get("attachment", {})
    if attach.get("replace_existing_user_state") is not False:
        raise ValueError("existing user state must not be silently replaced")

    claims = value.get("claims", {})
    if claims != {
        "partition_creation": "human-external",
        "mount_contract": "candidate",
        "root_reopen": "host-testable",
        "vm_cross_boot": "unverified",
        "physical_cross_boot": "unverified",
        "organ_runtime_reconstruction": "not_implemented",
    }:
        raise ValueError("persistence claims silently promoted")

    laws = set(value.get("laws", []))
    for law in {
        "PERSISTENT BYTES != CONTINUOUS PROCESS",
        "ROOT IDENTITY != BOOT IDENTITY",
        "SUPABARDO INTERIOR != DURABLE ROOT",
        "NO FORMAT WITHOUT HUMAN ACTION",
    }:
        if law not in laws:
            raise ValueError(f"missing persistence law: {law}")
    return value

def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: validate-persistent-root.py PATH", file=sys.stderr)
        return 2
    try:
        value=json.loads(Path(args[0]).read_text(encoding="utf-8"))
        validate(value)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print("VALID PERSISTENT-ROOT-001 candidate")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
