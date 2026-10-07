#!/usr/bin/env python3
"""CLI for CRANKNODE bounded-turn runtime."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crank.relatte_candidate import make_relatte_candidate
from crank.runtime import Refuse, execute_turn, list_capabilities


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv=None):
    parser = argparse.ArgumentParser(description="CRANKNODE bounded turn runtime")
    sub = parser.add_subparsers(dest="command", required=True)

    show = sub.add_parser("list", help="show inert capability cards; execute nothing")
    show.add_argument("registry")

    turn = sub.add_parser("turn", help="execute exactly one explicit turn")
    turn.add_argument("registry")
    turn.add_argument("request")
    turn.add_argument("--out", help="optional path for result + receipt JSON")

    candidate = sub.add_parser(
        "candidate",
        help="build an unsigned reLATTE opaque-organ spec candidate from one turn bundle",
    )
    candidate.add_argument("registry")
    candidate.add_argument("bundle")
    candidate.add_argument("created_at")
    candidate.add_argument("--out", help="optional path for candidate JSON")

    args = parser.parse_args(argv)
    try:
        registry = load(args.registry)
        if args.command == "list":
            print(
                json.dumps(
                    {
                        "capabilities": list_capabilities(registry),
                        "executed": False,
                    },
                    indent=2,
                    sort_keys=True,
                )
            )
            return 0

        if args.command == "candidate":
            result = make_relatte_candidate(
                registry,
                load(args.bundle),
                args.created_at,
            )
        else:
            result = execute_turn(registry, load(args.request))

        rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
        if getattr(args, "out", None):
            Path(args.out).write_text(rendered, encoding="utf-8")
        print(rendered, end="")
        return 0
    except (OSError, json.JSONDecodeError, Refuse) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
