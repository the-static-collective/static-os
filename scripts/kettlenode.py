#!/usr/bin/env python3
"""Run the KETTLENODE-001 standalone energy/turn specimen.

Examples:
  python3 scripts/kettlenode.py observe --sample fixtures/kettlenode-001/baseline.json
  python3 scripts/kettlenode.py observe --sample fixtures/kettlenode-001/warm.json
  python3 scripts/kettlenode.py turn --request fixtures/kettlenode-001/turn.json
  python3 scripts/kettlenode.py status

Use --ledger /tmp/kettle.json to avoid modifying the repository.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from crank.runtime import Refuse  # noqa: E402
from crank.thermal import observe, inspect, attempt_turn  # noqa: E402

FIXTURES = ROOT / "fixtures" / "kettlenode-001"


def load(path: str | Path) -> dict:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser(description="KETTLENODE-001 simulation / unverified meter seam")
    parser.add_argument("action", choices=("observe", "turn", "status"))
    parser.add_argument("--ledger", default="/tmp/kettlenode-001-ledger.json")
    parser.add_argument("--policy", default=str(FIXTURES / "policy.json"))
    parser.add_argument("--registry", default=str(ROOT / "fixtures" / "cranknode-001" / "capabilities.json"))
    parser.add_argument("--sample")
    parser.add_argument("--request")
    args = parser.parse_args()
    try:
        policy = load(args.policy)
        if args.action == "observe":
            if not args.sample:
                parser.error("observe requires --sample")
            result = observe(load(args.sample), args.ledger, policy)
        elif args.action == "turn":
            if not args.request:
                parser.error("turn requires --request")
            result = attempt_turn(args.ledger, policy, load(args.registry), load(args.request))
        else:
            result = inspect(args.ledger, policy)
        print(json.dumps(result, sort_keys=True, indent=2))
        return 0
    except (Refuse, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
