#!/usr/bin/env python3
"""FIRST-PHYSICAL-BOOT-001 receipt initializer and strict verifier."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = "static-os.physical-boot-receipt/v0"
EXPERIMENT = "FIRST-PHYSICAL-BOOT-001"
REPOSITORY = "the-static-collective/static-os"
SHA40 = re.compile(r"[0-9a-f]{40}\\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\\Z")
RFC3339 = re.compile(r"\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}(?:\\.\\d+)?(?:Z|[+-]\\d{2}:\\d{2})\\Z")

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest" / "genesis-001.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head() -> str:
    value = subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", "HEAD"], text=True
    ).strip()
    if not SHA40.fullmatch(value):
        raise ValueError("repository HEAD is not an exact 40-hex commit")
    return value


def _house_commit() -> str:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    value = data.get("house", {}).get("commit")
    if not isinstance(value, str) or not SHA40.fullmatch(value):
        raise ValueError("manifest HOUSE commit is not an exact 40-hex commit")
    return value


def initialize(iso_path: Path, out_path: Path) -> None:
    iso_path = iso_path.resolve()
    if not iso_path.is_file():
        raise ValueError(f"ISO does not exist: {iso_path}")
    receipt = {
        "schema": SCHEMA,
        "experiment": EXPERIMENT,
        "receipt_status": "candidate",
        "source": {
            "repository": REPOSITORY,
            "commit": _git_head(),
            "house_commit": _house_commit(),
        },
        "iso": {
            "filename": iso_path.name,
            "sha256": _sha256(iso_path),
            "bytes": iso_path.stat().st_size,
        },
        "vm": {
            "bios_boot": None,
            "uefi_boot": None,
            "offline_house": None,
        },
        "physical": {
            "medium": "usb",
            "observed_boot": None,
            "desktop_visible": None,
            "house_loopback": None,
            "network_disconnected": None,
            "installer_invoked": False,
            "internal_storage_written_by_operator": False,
        },
        "witness": {
            "kind": "human",
            "name": "",
            "observed_at": "",
            "statement": "",
        },
        "nonclaims": {
            "installed_os": False,
            "persistent_cross_boot": "not_proven",
        },
    }
    out_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"WROTE candidate receipt: {out_path}")
    print("Human observation fields remain unset; edit them only after the gates are actually observed.")


def _require_true(mapping: dict, keys: tuple[str, ...], label: str) -> None:
    for key in keys:
        if mapping.get(key) is not True:
            raise ValueError(f"{label}.{key} must be true from direct observation")


def validate(data: object) -> dict:
    if not isinstance(data, dict) or data.get("schema") != SCHEMA:
        raise ValueError("unsupported receipt schema")
    if data.get("experiment") != EXPERIMENT:
        raise ValueError("wrong experiment")
    if data.get("receipt_status") != "observed":
        raise ValueError("receipt_status must be observed")

    source = data.get("source")
    if not isinstance(source, dict) or source.get("repository") != REPOSITORY:
        raise ValueError("source repository mismatch")
    for key in ("commit", "house_commit"):
        value = source.get(key)
        if not isinstance(value, str) or not SHA40.fullmatch(value):
            raise ValueError(f"source.{key} must be an exact 40-hex commit")

    iso = data.get("iso")
    if not isinstance(iso, dict):
        raise ValueError("missing iso evidence")
    if not isinstance(iso.get("filename"), str) or not iso["filename"].endswith(".iso"):
        raise ValueError("iso.filename must name an .iso")
    if not isinstance(iso.get("sha256"), str) or not SHA256.fullmatch(iso["sha256"]):
        raise ValueError("iso.sha256 must be a lowercase SHA-256")
    if not isinstance(iso.get("bytes"), int) or isinstance(iso.get("bytes"), bool) or iso["bytes"] <= 0:
        raise ValueError("iso.bytes must be a positive integer")

    vm = data.get("vm")
    if not isinstance(vm, dict):
        raise ValueError("missing vm evidence")
    _require_true(vm, ("bios_boot", "uefi_boot", "offline_house"), "vm")

    physical = data.get("physical")
    if not isinstance(physical, dict) or physical.get("medium") != "usb":
        raise ValueError("physical.medium must be usb")
    _require_true(
        physical,
        (
            "observed_boot",
            "desktop_visible",
            "house_loopback",
            "network_disconnected",
        ),
        "physical",
    )
    if physical.get("installer_invoked") is not False:
        raise ValueError("FIRST-PHYSICAL-BOOT-001 must not invoke an installer")
    if physical.get("internal_storage_written_by_operator") is not False:
        raise ValueError("FIRST-PHYSICAL-BOOT-001 must not intentionally write internal storage")

    witness = data.get("witness")
    if not isinstance(witness, dict) or witness.get("kind") != "human":
        raise ValueError("witness.kind must be human")
    if not isinstance(witness.get("name"), str) or not witness["name"].strip():
        raise ValueError("witness.name must identify the observing human")
    if not isinstance(witness.get("observed_at"), str) or not RFC3339.fullmatch(witness["observed_at"]):
        raise ValueError("witness.observed_at must be RFC3339 with timezone")
    if not isinstance(witness.get("statement"), str) or len(witness["statement"].strip()) < 12:
        raise ValueError("witness.statement must record the observed event")

    nonclaims = data.get("nonclaims")
    if not isinstance(nonclaims, dict):
        raise ValueError("missing nonclaims")
    if nonclaims.get("installed_os") is not False:
        raise ValueError("USB live boot does not establish installed_os")
    if nonclaims.get("persistent_cross_boot") != "not_proven":
        raise ValueError("FIRST-PHYSICAL-BOOT-001 does not establish persistent cross-boot state")
    return data


def verify(path: Path) -> None:
    validate(json.loads(path.read_text(encoding="utf-8")))
    print(f"VALID observed receipt: {SCHEMA}")


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subs = root.add_subparsers(dest="command", required=True)

    init = subs.add_parser("init", help="hash an ISO and write an unobserved candidate receipt")
    init.add_argument("--iso", required=True, type=Path)
    init.add_argument("--out", required=True, type=Path)

    check = subs.add_parser("verify", help="strictly verify a completed human observation receipt")
    check.add_argument("receipt", type=Path)
    return root


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "init":
            initialize(args.iso, args.out)
        else:
            verify(args.receipt)
    except (OSError, subprocess.CalledProcessError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
