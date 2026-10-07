#!/usr/bin/env python3
"""CLI for CRANKNODE-001."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crank.runtime import Refuse, execute_turn, list_capabilities


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRANKNODE-001 bounded turn runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("list", help="show inert capability cards; execute nothing")
    show.add_argument("registry")

    turn = sub.add_parser("turn", help="execute exactly one explicit turn")
    turn.add_argument("registry")
    turn.add_argument("request")
    turn.add_argument("--out", help="optional path for result + receipt JSON")

    args = parser.parse_args(argv)
    try:
        registry = load(args.registry)
        if args.command == "list":
            print(json.dumps({"capabilities": list_capabilities(registry), "executed": False}, indent=2, sort_keys=True))
            return 0

        bundle = execute_turn(registry, load(args.request))
        rendered = json.dumps(bundle, indent=2, sort_keys=True) + "\n"
        if args.out:
            Path(args.out).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, json.JSONDecodeError, Refuse) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
