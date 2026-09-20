#!/usr/bin/env python3
"""Static OS GENESIS 001: deterministic, read-only manifest validation."""
import json
import re
import sys
from pathlib import Path

SCHEMA = "static-os.genesis/v0"
SHA40 = re.compile(r"[0-9a-f]{40}\Z")
WORKBENCH_URL = "https://github.com/the-static-collective/static-workbench.git"
STAGES = ("boot", "house", "elf", "foundry")


def validate(value):
    if not isinstance(value, dict) or value.get("schema") != SCHEMA:
        raise ValueError("unsupported manifest schema")
    if value.get("status") != "build-candidate":
        raise ValueError("a proposal must not claim built status")
    base = value.get("base", {})
    if not isinstance(base, dict) or (base.get("family"), base.get("codename"),
                                      base.get("architecture"), base.get("image"),
                                      base.get("installer")) != (
                                          "debian", "bookworm", "amd64",
                                          "iso-hybrid", False):
        raise ValueError("unexpected base or installer escalation")
    house = value.get("house", {})
    if not isinstance(house, dict) or house.get("url") != WORKBENCH_URL:
        raise ValueError("HOUSE source must be project-owned, explicit URL")
    if house.get("owner") != "the-static-collective/static-workbench":
        raise ValueError("HOUSE owner mismatch")
    if not isinstance(house.get("commit"), str) or not SHA40.fullmatch(house["commit"]):
        raise ValueError("HOUSE source must have an exact 40-hex commit")
    if house.get("bind_host") != "127.0.0.1" or house.get("port") != 13700:
        raise ValueError("HOUSE must bind to its declared loopback endpoint")
    elf = value.get("elf", {})
    if not isinstance(elf, dict) or set(elf) != {
        "carrier", "source_commit", "mode", "producer", "automatic", "authority"
    }:
        raise ValueError("ELF declaration must be explicit and bounded")
    if elf["carrier"] != "static_workbench.elf_genesis" or (
        elf["source_commit"] != house["commit"]
    ):
        raise ValueError("ELF carrier must match pinned HOUSE source commit")
    if (elf["mode"], elf["producer"], elf["automatic"], elf["authority"]) != (
        "manual_guest_only", "deterministic_fixture_not_openmanus", False, "none"
    ):
        raise ValueError("ELF fixture must not gain authority or provider claims")
    admission = value.get("admission", {})
    if not isinstance(admission, dict) or admission.get("automatic") is not False or (
        admission.get("may_mutate_running_system") is not False
    ):
        raise ValueError("experimental capability promotion is not automatic")
    stages = value.get("stages")
    if not isinstance(stages, list) or [s.get("id") for s in stages
                                        if isinstance(s, dict)] != list(STAGES):
        raise ValueError("unexpected/missing composition stages")
    if stages[2].get("requires") != ["house"]:
        raise ValueError("ELF must remain a manual HOUSE-dependent stage")
    known = set()
    for stage in stages:
        requirements = stage.get("requires")
        if not isinstance(requirements, list) or len(requirements) != len(set(requirements)):
            raise ValueError("invalid/duplicate dependencies")
        if any(requirement not in known for requirement in requirements):
            raise ValueError("unknown, forward or cyclic stage dependency")
        known.add(stage["id"])
    evidence = value.get("evidence", {})
    if not isinstance(evidence, dict) or any(
        evidence.get(key) != "unverified" for key in
        ("iso_build", "vm_boot", "hardware_boot", "offline_house", "elf_offline_guest")
    ):
        raise ValueError("unverified gates must not be silently promoted")
    if evidence.get("openmanus_live") != "not_run":
        raise ValueError("live OpenManus provider has not been tested by this fixture")
    if evidence.get("installed_persistence") != "not_implemented" or (
        evidence.get("self_development") != "not_implemented"
    ):
        raise ValueError("later milestones must remain explicitly unimplemented")
    return value


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: validate-manifest.py PATH", file=sys.stderr)
        return 2
    try:
        parsed = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        validate(parsed)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    print(f"VALID candidate: {SCHEMA}; pinned HOUSE {parsed['house']['commit']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
