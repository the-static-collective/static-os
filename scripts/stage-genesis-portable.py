#!/usr/bin/env python3
"""Stage the original GENESIS source commits for any Linux filesystem.

Used by Alpine (musl) and Fedora (RPM) image builders. No git branch
resolution, main/default-branch fallback, installation to host devices, or
runtime fetching. The source matrix is exactly the existing ISO manifest.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
from urllib.parse import urlparse

SHA = re.compile(r"^[a-f0-9]{40}$")
ID = re.compile(r"^[a-z0-9-]+$")


def checked(args, **kwargs):
    return subprocess.run(args, check=True, text=True, timeout=120, **kwargs)


def stage(manifest_path, destination):
    m = json.loads(pathlib.Path(manifest_path).read_text(encoding="utf-8"))
    assert m["schema"] == "static-os.genesis-first-boot-image/v1"
    assert m["status"] == "IMAGE_CANDIDATE_NOT_BOOT_PROOF"
    assert len(m["sources"]) == 11
    assert all(x == "UNVERIFIED" for x in m["gate_status"].values())
    assert m["service"]["host"] == "127.0.0.1"
    assert m["service"]["auto_execution"] is False
    target = pathlib.Path(destination)
    if target.exists():
        raise ValueError("SOURCE_STAGING_TARGET_ALREADY_EXISTS")
    target.mkdir(parents=True, mode=0o755)
    safe = pathlib.Path("/usr/share/static-os/genesis-gitconfig")
    safe.parent.mkdir(parents=True, exist_ok=True)
    entries = ["[safe]"]
    seen = set()
    for row in m["sources"]:
        if set(row) != {"id", "url", "commit", "repository"}:
            raise ValueError("SOURCE_ROW_SHAPE")
        ident, commit, url, owner = row["id"], row["commit"], row["url"], row["repository"]
        if not ID.fullmatch(ident) or not SHA.fullmatch(commit) or ident in seen:
            raise ValueError("UNSAFE_SOURCE_ID_OR_SHA")
        if not owner.startswith("the-static-collective/") or url != f"https://github.com/{owner}.git":
            raise ValueError("UNTRUSTED_SOURCE_ORIGIN")
        seen.add(ident)
        source = target / ident
        checked(["git", "init", "-q", str(source)])
        checked(["git", "-C", str(source), "remote", "add", "origin", url])
        checked(["git", "-C", str(source), "-c", "protocol.version=2",
                 "fetch", "-q", "--depth=1", "origin", commit])
        got = subprocess.check_output(["git", "-C", str(source), "rev-parse", "FETCH_HEAD"],
                                      text=True, timeout=10).strip()
        if got != commit:
            raise ValueError(f"ORIGINAL_SOURCE_SHA_MISMATCH_{ident}")
        checked(["git", "-C", str(source), "-c", "advice.detachedHead=false",
                 "checkout", "-q", "--detach", commit])
        # A second head check catches unexpected checkout movement.
        head = subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"],
                                       text=True, timeout=10).strip()
        if head != commit:
            raise ValueError(f"SOURCE_HEAD_DRIFT_{ident}")
        entries.append(f"    directory = {source}")
        print(f"STAGED ORIGINAL {ident} {head}", flush=True)
    safe.write_text("\n".join(entries)+"\n", encoding="utf8")
    os.chmod(safe, 0o644)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("USAGE: stage-genesis-portable.py MANIFEST ABSOLUTE_DESTINATION")
    stage(sys.argv[1], sys.argv[2])
