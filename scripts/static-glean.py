#!/usr/bin/env python3
"""GLEAN-001 independent steward-bounded remainder assessment and cold replay."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from glean.kernel import Hold, plan, journal, cold_verify, require


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_once(file, data):
    output = Path(file).expanduser().resolve()
    require(not output.exists(), "NO_OVERWRITE_OR_DOUBLE_REPORT")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(output), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("assess", "journal", "verify"))
    parser.add_argument("--offer", required=True)
    parser.add_argument("--review")
    parser.add_argument("--pickups")
    parser.add_argument("--out", required=True)
    x = parser.parse_args(argv)
    offer, review = read(x.offer), read(x.review) if x.review else None
    pickups = read(x.pickups) if x.pickups else None
    if x.action == "journal":
        require(review is not None and pickups is not None,
                "HUMAN_REVIEW_AND_OPERATOR_REPORTS_REQUIRED")
        result = journal(offer, review, pickups)
    elif x.action == "assess":
        require(pickups is None, "PLAN_DOES_NOT_IMPLY_PHYSICAL_PICKUP")
        result = plan(offer, review)
    else:
        old = read(x.out)
        if old.get("schema") == "static-os.glean-pickup-journal/v0":
            require(review is not None and pickups is not None,
                    "JOURNAL_REPLAY_REQUIRES_ALL_ORIGINAL_INPUTS")
        else:
            require(pickups is None, "PLAN_REPLAY_MUST_NOT_INCLUDE_PICKUP_REPORTS")
        result = cold_verify(offer, review, old, pickups)
    if x.action != "verify":
        write_once(x.out, result)
    print(json.dumps({
        "state": result.get("state", "OPERATOR_REPORTED_UNVERIFIED"),
        "id": result.get("plan_id", result.get("journal_id")),
        "reasons": result.get("reason_codes", []),
        "remaining_reported": result.get("remaining_unverified_offer_amount"),
        "legally_authorized_by_software": False,
        "inventory_delta": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, ValueError, OSError, KeyError, TypeError,
            json.JSONDecodeError) as exc:
        print("HOLD: " + str(exc)[:280], file=sys.stderr)
        raise SystemExit(2)
