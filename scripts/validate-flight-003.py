#!/usr/bin/env python3
"""FLIGHT-003: pure candidate/source-consistency check; never installs or runs code."""
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\\Z")
EXPECTED = (
    ("workbench", "the-static-collective/static-workbench", "local-house-and-manual-elf", "candidate-pinned-source"),
    ("storyship", "the-static-collective/STORYSHIP", "local-ark-arrival-evidence", "reference-only-not-packaged"),
    ("tranchnode", "the-static-collective/tranchnode", "proposal-only-continuity-adapter", "reference-only-not-packaged"),
)


def exact(obj, keys):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError("unexpected/missing contract fields")


def validate(value, genesis, triad):
    exact(value, ("schema", "status", "base", "candidate", "sources", "claims", "boundary"))
    if (value["schema"] != "static-os.flight-003/v0"
            or value["status"] != "contract-candidate"
            or value["base"] != "genesis-001-live-iso"):
        raise ValueError("FLIGHT-003 may not claim constituted release")
    house = genesis.get("house")
    elf = genesis.get("elf")
    if not isinstance(house, dict) or not isinstance(elf, dict):
        raise ValueError("manual ELF Genesis candidate required")
    sha = house.get("commit")
    if not isinstance(sha, str) or not SHA.fullmatch(sha) or elf.get("source_commit") != sha:
        raise ValueError("HOUSE/ELF source pin must match")
    candidate = value["candidate"]
    exact(candidate, ("house_source_commit", "elf_source_commit", "manifest", "triad"))
    if candidate != {
        "house_source_commit": sha, "elf_source_commit": sha,
        "manifest": "manifest/genesis-001.json", "triad": "interop/triad-001.json",
    }:
        raise ValueError("candidate must use exact active source and local contracts")
    sources = value["sources"]
    if not isinstance(sources, list) or len(sources) != len(EXPECTED):
        raise ValueError("exact source inventory required")
    for source, (ident, repository, role, image_status) in zip(sources, EXPECTED):
        exact(source, ("id", "repository", "commit", "role", "image_status", "authority"))
        if ((source["id"], source["repository"], source["role"], source["image_status"])
                != (ident, repository, role, image_status)
                or source["authority"] != "none"
                or not isinstance(source["commit"], str) or not SHA.fullmatch(source["commit"])):
            raise ValueError("invalid source identity or packaging/authority escalation")
    if sources[0]["commit"] != sha or triad.get("sources", [None, None, {}])[2].get("commit") != sha:
        raise ValueError("Workbench must be pinned identically in all three contracts")
    claims = value["claims"]
    exact(claims, ("source_contracts", "os_iso", "vm_boot", "offline_guest", "cross_boot",
                   "storyship_guest", "tranchnode_guest", "automatic_upgrade"))
    if (claims["source_contracts"] != "testable"
            or any(claims[key] != "unverified"
                   for key in ("os_iso", "vm_boot", "offline_guest"))
            or any(claims[key] != "not_implemented"
                   for key in ("cross_boot", "storyship_guest", "tranchnode_guest"))
            or claims["automatic_upgrade"] is not False):
        raise ValueError("unearned flight gate or upgrade claim")
    boundary = value["boundary"]
    exact(boundary, ("operator_only", "automatic_promotion", "extra_user_services",
                     "os_mutation", "run_untrusted_commands"))
    if (boundary["operator_only"] is not True or
            any(boundary[key] is not False for key in boundary if key != "operator_only")):
        raise ValueError("FLIGHT-003 may not expand effect or admission authority")
    if (genesis.get("admission", {}).get("automatic") is not False
            or genesis.get("admission", {}).get("may_mutate_running_system") is not False
            or elf.get("automatic") is not False or elf.get("authority") != "none"):
        raise ValueError("GENESIS/ELF automatic authority escalation")
    return value


def main():
    root = Path(__file__).resolve().parents[1]
    try:
        value = json.loads((root / "interop/flight-003.json").read_text(encoding="utf-8"))
        genesis = json.loads((root / "manifest/genesis-001.json").read_text(encoding="utf-8"))
        triad = json.loads((root / "interop/triad-001.json").read_text(encoding="utf-8"))
        validate(value, genesis, triad)
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        print(f"REFUSE FLIGHT-003: {exc}", file=sys.stderr)
        return 2
    print("VALID FLIGHT-003 contract-candidate; Storyship/TranchNode not packaged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
