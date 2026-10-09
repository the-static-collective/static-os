#!/usr/bin/env python3
"""WALL-E / FORAGE-002: local photo intake to FORAGE-001 HOLD, never collection."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from forage.ledger import Hold, require
from forage.scout import cold_replay, scout


def read(name):
    x = json.loads(Path(name).read_text(encoding="utf-8"))
    require(type(x) is dict, "EXPECTED_JSON_OBJECT")
    return x


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("receive", "verify"))
    for arg in ("lead", "photo-evidence", "photo", "out"):
        p.add_argument("--" + arg, required=True)
    a = p.parse_args(argv)
    lead, evidence = read(a.lead), read(a.photo_evidence)
    original, output = Path(a.photo), Path(a.out)
    if a.command == "receive":
        require(not output.exists(), "SCOUT_RECEIPT_EXISTS_NO_SILENT_RETRY")
        record = scout(lead, evidence, original)
        output.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(output), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, sort_keys=True)
            f.write("\n")
    else:
        record = cold_replay(lead, evidence, original, read(output))
    print(json.dumps({
        "status": record["state"],
        "scout_id": record["scout_id"],
        "lead_ref": record["source_lead_ref"],
        "candidate_affordances": record["candidate_affordances"],
        "permission_review_completed": False,
        "automated_collection": False,
        "image_recognition_executed": False,
        "robot_inventory_delta": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, OSError, ValueError, TypeError, KeyError,
            json.JSONDecodeError) as exc:
        print("HOLD: " + str(exc)[:280], file=sys.stderr)
        raise SystemExit(2)
