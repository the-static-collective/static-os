#!/usr/bin/env python3
"""Consume one physical CRANK edge, execute one turn attempt, then exit."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from crank.physical import claim_edge, decode_edge_frame, edge_to_turn, read_one_tty_frame
from crank.relatte_candidate import make_relatte_candidate
from crank.runtime import Refuse, execute_turn


def load(path: str):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def read_edge(args):
    if args.device:
        return read_one_tty_frame(args.device, args.baud, args.timeout)
    if args.edge_file:
        return decode_edge_frame(Path(args.edge_file).read_bytes())
    return decode_edge_frame(sys.stdin.buffer.readline())


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="CRANKNODE-003 one physical edge -> at most one turn attempt"
    )
    parser.add_argument("registry")
    parser.add_argument("capability")
    parser.add_argument("payload")
    parser.add_argument("ledger")
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--device", help="POSIX TTY device such as /dev/ttyACM0")
    source.add_argument("--edge-file", help="newline-delimited JSON edge fixture")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--budget", type=int, default=3)
    parser.add_argument(
        "--candidate-at",
        help="also emit unsigned reLATTE candidate using this ISO-8601 time",
    )

    args = parser.parse_args(argv)
    try:
        registry = load(args.registry)
        payload = load(args.payload)
        edge = read_edge(args)

        # Consume before work. A provider crash does not create retry authority.
        gate = claim_edge(edge, args.ledger)
        request = edge_to_turn(edge, args.capability, payload, args.budget)
        bundle = execute_turn(registry, request)

        result = {
            "schema": "static-os.crank-physical-turn-execution/v0",
            "gate": gate,
            "turn": bundle,
            "automatic_next_turn": False,
        }
        if args.candidate_at:
            result["relatte_candidate"] = make_relatte_candidate(
                registry,
                bundle,
                args.candidate_at,
            )

        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, Refuse) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
