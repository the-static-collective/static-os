#!/usr/bin/env python3
"""Validate exact source and proof boundaries for STATIC OS first-boot ISO.

No hardware probing, network, image construction, signatures, secrets or Git
operations. Explicit exact-git selection != owner-selected canon.
"""
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[a-f0-9]{40}\Z")
HEX64 = re.compile(r"[a-f0-9]{64}\Z")
SCHEMA = "static-os.genesis-first-boot-image/v1"
NODE_SHA = "2642f4428869aca32443660fd71b3918e2be1277a899bdcaeb64c93b54b5af17"
SOURCES = (
    ("cannon", "CANNON", "92a73324ec6918765cbd15b7a12cb83878b403eb"),
    ("staticos", "static-os", "b02b5016cbd5bf2f73d758d5ed1416246b789157"),
    ("webz", "webZ", "83b35070d8d56155156655279bfdcf50aa77794f"),
    ("gro", "GrO", "9e6361105aae335ccb0657092809eef43e7ab4da"),
    ("ghot", "GHoT", "6f0cc9e93e2544cd2fc67a0aa43a06198825a654"),
    ("jarvis", "JAR-VIS", "c9b8341f2eff16105f58dcd5bb9031245bcb0558"),
    ("cannon-warm", "CANNON", "ee461d7be29795907384c791be88c18e030e0222"),
    ("ghot-warm", "GHoT", "3c8be40cbaef2f9c786e5424abf15d4b138d2966"),
    ("full", "full-measure-world-layer", "553e97401a8483a0ee3c369fed9d3fb8f1c9058d"),
    ("band", "band-runtime", "f2c889df90905eda533fe6d978cd1a52c788a33e"),
    ("garden", "BananaSpork", "6738230a8557060dd59aabc19caf21826806d16f"),
)
GATES = ("manifest", "iso_build", "bios_vm_boot", "uefi_vm_boot",
         "user_desktop", "offline_first_boot", "physical_hardware")


def exact(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError(f"{label} unknown or missing keys")


def validate(v):
    exact(v, ("schema", "status", "base", "runtime", "service",
              "sources", "gate_status", "claims"), "root")
    if v["schema"] != SCHEMA or v["status"] != "IMAGE_CANDIDATE_NOT_BOOT_PROOF":
        raise ValueError("image candidate cannot claim boot success")
    exact(v["base"], ("family", "codename", "architecture", "image", "installer"), "base")
    if v["base"] != {"family": "debian", "codename": "bookworm",
                     "architecture": "amd64", "image": "iso-hybrid",
                     "installer": False}:
        raise ValueError("unexpected base or installer escalation")
    exact(v["runtime"], ("name", "version", "file", "sha256"), "node runtime")
    if v["runtime"] != {"name": "node", "version": "v24.10.0",
                        "file": "node-v24.10.0-linux-x64.tar.xz", "sha256": NODE_SHA}:
        raise ValueError("Node distribution not pinned to reviewed digest")
    exact(v["service"], ("host", "port", "start", "auto_execution",
                         "public_network"), "first boot")
    if v["service"] != {"host": "127.0.0.1", "port": 8766,
                        "start": "EXPLICIT_LOCAL_SESSION_START",
                        "auto_execution": False, "public_network": False}:
        raise ValueError("unsafe first boot service")
    if not isinstance(v["sources"], list) or len(v["sources"]) != 11:
        raise ValueError("exactly eleven original checkouts required")
    for entry, (ident, name, commit) in zip(v["sources"], SOURCES):
        exact(entry, ("id", "repository", "url", "commit"), "source")
        if not SHA.fullmatch(entry["commit"]) or entry != {
           "id": ident, "repository": f"the-static-collective/{name}",
           "url": f"https://github.com/the-static-collective/{name}.git",
           "commit": commit
        }:
            raise ValueError("source pin/owner drift or mutable reference")
    exact(v["gate_status"], GATES, "unearned gates")
    if any(x != "UNVERIFIED" for x in v["gate_status"].values()):
        raise ValueError("boot/test gates must be established by separate evidence")
    exact(v["claims"], ("no_installer", "no_real_site", "no_automatic_build",
                        "no_remote_service", "original_source_unchanged",
                        "experimental_not_owner_canon"), "claimed boundaries")
    if any(x is not True for x in v["claims"].values()):
        raise ValueError("one or more physical/authority boundaries weakened")
    return v


def main():
    try:
        if len(sys.argv) != 2:
            raise ValueError("expected candidate manifest path")
        v = json.loads(Path(sys.argv[1]).read_text(encoding="utf8"))
        validate(v)
        print(f"VALID SOURCE-PINNED IMAGE CANDIDATE: {len(v['sources'])} checked refs; no ISO/VM proof claimed")
        return 0
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f"REFUSE: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
