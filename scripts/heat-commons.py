#!/usr/bin/env python3
"""Display or execute ONE inert HEAT COMMONS route simulation. No actuators."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from crank.heat_commons import evaluate, simulate_route, validate_world  # noqa: E402
from crank.runtime import Refuse  # noqa: E402


def read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("inspect", "evaluate", "simulate"))
    parser.add_argument("--world", default=str(ROOT / "fixtures/kettlenode-002/world.json"))
    parser.add_argument("--route", default=str(ROOT / "fixtures/kettlenode-002/route.json"))
    args = parser.parse_args()
    try:
        world = read(args.world)
        validate_world(world)
        if args.action == "inspect":
            output = {
                "evidence_kind": world["evidence_kind"],
                "nodes": list(world["nodes"]),
                "exchangers": list(world["exchangers"]),
                "physical_hardware_observed": False,
            }
        elif args.action == "evaluate":
            output = evaluate(world, read(args.route))
        else:
            output = simulate_route(world, read(args.route))
        print(json.dumps(output, sort_keys=True, indent=2))
        return 0
    except (Refuse, OSError, ValueError, KeyError) as exc:
        print(json.dumps({"status": "REFUSE", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
