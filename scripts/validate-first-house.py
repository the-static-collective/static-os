#!/usr/bin/env python3
"""Validate the desktop-only First House pin; never alter ISO/ELF manifests."""
import json
import re
import sys
from pathlib import Path

EXPECTED = {
    "schema": "static-os.first-house-desktop/v0",
    "status": "release-candidate-unverified",
}
ROUTES = ["/arg", "/arg/world"]
ASSETS = ["arg.html", "arg.js", "arg-theme.css", "arg-world.html", "arg-world.js"]


def validate(data):
    if not isinstance(data, dict) or any(data.get(k) != v for k, v in EXPECTED.items()):
        raise ValueError("invalid first-house schema or release status")
    workbench = data.get("workbench")
    if not isinstance(workbench, dict) or set(workbench) != {
        "repository", "source_commit", "start_route", "required_routes", "required_assets"
    }:
        raise ValueError("explicit first-house source, route and assets required")
    if workbench["repository"] != "the-static-collective/static-workbench":
        raise ValueError("unexpected first-house source")
    if not isinstance(workbench["source_commit"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", workbench["source_commit"]
    ):
        raise ValueError("pin an exact Workbench commit")
    if (workbench["start_route"] != "/arg" or workbench["required_routes"] != ROUTES
            or workbench["required_assets"] != ASSETS):
        raise ValueError("First Door and World Entry are required")
    if data.get("claims") != {
        "desktop_package": "candidate-only",
        "physical_install": "unverified",
        "iso_boot": "not-applicable",
        "cross_project_game": "not-integrated",
        "offline_after_install": "pending-device-test",
    }:
        raise ValueError("unsupported release claim")
    if data.get("user_data") != {
        "import_existing": False, "auto_seed": False,
        "keep_user_state_on_uninstall": True, "save_owner": "static-workbench"
    }:
        raise ValueError("user state must remain opt-in and Workbench-owned")
    return workbench["source_commit"]


def main():
    if len(sys.argv) != 2:
        print("usage: validate-first-house.py PATH", file=sys.stderr)
        return 2
    try:
        sha = validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2
    print(f"VALID First House desktop candidate; Workbench source {sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
