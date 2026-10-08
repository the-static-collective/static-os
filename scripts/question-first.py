#!/usr/bin/env python3
"""Static-OS question-first user-space desk: ask / execute / replay.

No boot hooks, background daemon, ambient permissions, or automatic questions.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_first.session import (
    Hold, compile_question, discover_ghot, execute_selected, replay_state,
)


def read(path: str) -> dict:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise Hold("EXACT_JSON_OBJECT_REQUIRED")
    return value


def save_new(path: str, result: dict) -> None:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(target), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2, sort_keys=True)
        out.write("\n")


def main(args: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Question first, instruments second")
    parser.add_argument("command", choices=("ask", "execute", "replay"))
    parser.add_argument("--ghot-root", required=True)
    parser.add_argument("--seed")
    parser.add_argument("--selection")
    parser.add_argument("--state-dir")
    parser.add_argument("--state")
    parser.add_argument("--out")
    options = parser.parse_args(args)
    root = Path(options.ghot_root).expanduser().resolve()

    # Check output existence before any possible physical operation.
    if options.out and os.path.lexists(options.out):
        raise Hold("OUTPUT_OCCUPIED_NO_EXECUTION")
    if options.command == "ask":
        if not options.seed:
            raise Hold("QUESTION_SEED_REQUIRED")
        question = compile_question(read(options.seed), discover_ghot(root))
        output = {"question": question, "executed": False, "authority": "none"}
    elif options.command == "execute":
        if not all((options.seed, options.selection, options.state_dir)):
            raise Hold("SEED_SELECTION_AND_STATE_DIR_REQUIRED")
        output = execute_selected(
            read(options.seed), discover_ghot(root), read(options.selection),
            ghot_root=root, state_dir=Path(options.state_dir).expanduser(),
        )
    else:
        if not options.state:
            raise Hold("EXPLICIT_STATE_FILE_REQUIRED")
        state = replay_state(Path(options.state).expanduser(), ghot_root=root)
        output = {"state": state, "read_only_replay": True, "executed_again": False}

    if options.out:
        save_new(options.out, output)
        print(json.dumps({"status": "WRITTEN", "path": str(Path(options.out).resolve()),
                          "automatic_execution": False, "authority": "none"}))
    else:
        print(json.dumps(output, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"HOLD: {str(exc)[:220]}", file=sys.stderr)
        raise SystemExit(2)
