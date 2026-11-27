#!/usr/bin/env python3
"""Opt-in CARAVAN mission cartridge. No installer, network or service on import."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SOURCE_COMMIT = "72f52f8265a388a8eee894df38fc8c858b01db1c"
MANIFEST_SHA = "1bc5962ba8966ebd3a623adb05408d697fc79b3051375875e610cc1d32b0532e"
VOCATIONS = {
    "church": ["gather", "voice", "library"],
    "studio": ["voice", "crossing"],
    "library": ["library", "crossing"],
    "community": ["gather", "library", "crossing"],
    "radio": ["voice", "airwaves", "crossing"],
    "workshop": ["library", "gather"],
}
# These are advisory mission presets, not module-level access controls.
def verify(source):
    source = Path(source)
    mf = source / "SOURCE-SHA256.json"
    if mf.is_symlink() or not mf.is_file():
        raise ValueError("missing manifest")
    raw = mf.read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA:
        raise ValueError("manifest pin mismatch")
    files = json.loads(raw)
    if len(files) != 20:
        raise ValueError("unexpected file count")
    for name, digest in files.items():
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or any(
            (source / Path(*rel.parts[:i])).is_symlink()
            for i in range(1, len(rel.parts)+1)
        ):
            raise ValueError("unsafe source path")
        p = source / rel
        if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            raise ValueError("source mismatch: " + name)
    return sorted([*files, "SOURCE-SHA256.json"])

def stage(source, dest):
    names = verify(source)
    dest = Path(dest)
    dest.mkdir(mode=0o700)  # exclusive; never merge with an existing node
    try:
        for name in names:
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(Path(source) / name, target)
        verify(dest)
    except BaseException:
        shutil.rmtree(dest)
        raise
    return len(names)

def mission(vocations):
    if not vocations or len(set(vocations)) != len(vocations) or any(v not in VOCATIONS for v in vocations):
        raise ValueError("choose distinct known vocations")
    return {"schema": "static-os.caravan-mission/v0",
            "source_commit": SOURCE_COMMIT,
            "vocations": sorted(vocations),
            "suggested_capabilities": sorted({m for v in vocations for m in VOCATIONS[v]} | {"seed"}),
            "mode": "ADVISORY_PRESET_ONLY",
            "activation": "EXPLICIT_LOCAL_OPERATOR",
            "network": "LOOPBACK_DEFAULT", "boot_proof": "NOT_ESTABLISHED"}

def run(source, data, tool, args):
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise ValueError("run as a normal local user, not root")
    verify(source)
    source, data = Path(source).resolve(), Path(data).absolute()
    if data == source or source in data.parents or data.is_symlink():
        raise ValueError("data must be separate from the immutable source")
    # Fixed source entrypoints, no shell. Native applications retain their own controls.
    if tool not in ("caravan", "voice", "library", "crossing", "airwaves", "seed"):
        raise ValueError("unknown tool")
    os.umask(0o077)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    return subprocess.call([sys.executable, str(source / (tool + ".py")),
                            "--data", str(data), *args], env=env)

def main():
    p = argparse.ArgumentParser(description=__doc__)
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("verify"); s.add_argument("source", type=Path)
    s = sp.add_parser("stage"); s.add_argument("source", type=Path); s.add_argument("dest", type=Path)
    s = sp.add_parser("plan"); s.add_argument("vocation", choices=sorted(VOCATIONS), nargs="+")
    s = sp.add_parser("run"); s.add_argument("--source", type=Path, required=True)
    s.add_argument("--data", type=Path, required=True)
    s.add_argument("tool", choices=("caravan","voice","library","crossing","airwaves","seed"))
    s.add_argument("args", nargs=argparse.REMAINDER)
    a = p.parse_args()
    try:
        if a.cmd == "verify": print("VERIFIED SOURCE FILES:", len(verify(a.source)))
        elif a.cmd == "stage": print("STAGED SOURCE FILES:", stage(a.source, a.dest))
        elif a.cmd == "plan": print(json.dumps(mission(a.vocation), indent=2))
        else: return run(a.source, a.data, a.tool, a.args)
        return 0
    except (OSError, ValueError, TypeError) as e:
        print("HOLD:", e, file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
