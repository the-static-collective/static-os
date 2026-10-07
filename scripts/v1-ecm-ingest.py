#!/usr/bin/env python3
"""Ingest one authorized, already-collected vehicle ECM observation."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from v1.vehicle_ecm import Refuse, ingest_observation


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: v1-ecm-ingest.py OBSERVATION.json", file=sys.stderr)
        return 2
    try:
        value = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        print(json.dumps(ingest_observation(value), indent=2, sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, Refuse) as exc:
        print(f"REFUSE: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
