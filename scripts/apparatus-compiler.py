#!/usr/bin/env python3
"""STATIC OS question-first apparatus desk. No boot hook, daemon, or auto-execute."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_first.session import Hold, discover_ghot
from question_first.apparatus_compiler import (
    compile_apparatus, execute_selected, replay_state, verify_plan,
)


def read(path: str) -> dict:
    item = json.loads(Path(path).read_text(encoding="utf-8"))
    if type(item) is not dict:
        raise Hold("JSON_OBJECT_REQUIRED")
    return item


def exclusive(path: str, value: dict) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(value, out, sort_keys=True, indent=2)
        out.write("\n")


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Question-first apparatus compiler")
    parser.add_argument("action", choices=("compile", "execute", "replay"))
    parser.add_argument("--ghot-root", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--plan")
    parser.add_argument("--selection")
    parser.add_argument("--state-dir")
    parser.add_argument("--state")
    parser.add_argument("--out")
    args = parser.parse_args(argv)
    root = Path(args.ghot_root).expanduser().resolve(strict=True)

    # Deny an occupied destination BEFORE any possibly effectful GHoT dispatch.
    # exclusive() repeats this guard atomically against filesystem races.
    if args.out and os.path.lexists(args.out):
        raise Hold("APPARATUS_OUTPUT_OCCUPIED_BEFORE_EXECUTION")
    if args.action == "compile":
        if not args.seed or args.plan or args.selection or args.state:
            raise Hold("COMPILE_REQUIRES_SEED_ONLY")
        value = {"plan": compile_apparatus(read(args.seed), discover_ghot(root)),
                 "executed": False, "authority": "none"}
    elif args.action == "execute":
        if not args.plan or not args.selection or not args.state_dir or not args.out:
            raise Hold("EXECUTE_REQUIRES_PLAN_SELECTION_PRIVATE_OUTPUT_AND_STATE_DIR")
        saved = read(args.plan)
        if set(saved) != {"plan", "executed", "authority"} or saved["executed"] is not False:
            raise Hold("INVALID_SAVED_APPARATUS_PLAN")
        plan = verify_plan(saved["plan"])
        if compile_apparatus(plan["question_seed"], discover_ghot(root)) != plan:
            raise Hold("STALE_APPARATUS_PLAN")
        value = execute_selected(plan, read(args.selection), ghot_root=root,
                                 state_dir=Path(args.state_dir).expanduser())
    else:
        if not args.state or args.plan or args.selection:
            raise Hold("REPLAY_REQUIRES_EXACT_STATE_FILE_ONLY")
        state = replay_state(Path(args.state).expanduser(), ghot_root=root)
        value = {"state": state, "read_only_replay": True, "executed_again": False}

    if args.out:
        exclusive(args.out, value)
        print(json.dumps({"status": "WRITTEN_PRIVATELY", "path": str(Path(args.out).resolve()),
                          "automatic_execution": False, "physical_effects": False}))
    else:
        print(json.dumps(value, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HOLD: {str(exc)[:240]}", file=sys.stderr)
        raise SystemExit(2)
