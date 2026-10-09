#!/usr/bin/env python3
"""FORAGE-001: evidence-first local leads, scoped reviews and pickup journals.

No search/scraping, location lookup, entry, material collection, legal advice,
payment, real-world authority, robot dispatch or automatic inventory admission.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from forage.ledger import Hold, assess, cold_verify, journal_handoff, require


def read(path):
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(value) is dict, "INPUT_JSON_OBJECT_REQUIRED")
    return value


def write_once(path, body):
    output = Path(path).expanduser().resolve()
    require(not output.exists(), "OCCURRENCE_EXISTS_NO_SILENT_OVERWRITE")
    output.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as writer:
        json.dump(body, writer, indent=2, sort_keys=True)
        writer.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("assess", "handoff", "verify"))
    parser.add_argument("--lead", required=True)
    parser.add_argument("--review")
    parser.add_argument("--pickup")
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)

    lead = read(args.lead)
    review = read(args.review) if args.review else None
    pickup = read(args.pickup) if args.pickup else None
    if args.command == "assess":
        require(pickup is None, "ASSESS_CANNOT_IMPLY_PICKUP")
        expected = assess(lead, review)
    elif args.command == "handoff":
        require(review is not None and pickup is not None,
                "HANDOFF_REQUIRES_EXPLICIT_REVIEW_AND_PICKUP_REPORT")
        expected = journal_handoff(lead, review, pickup)
    else:
        previous = read(args.out)
        if previous.get("schema") == "static-os.forage-handoff/v0":
            require(review is not None and pickup is not None,
                    "HANDOFF_REPLAY_REQUIRES_ORIGINAL_INPUTS")
        else:
            require(pickup is None, "ASSESSMENT_REPLAY_MUST_NOT_INCLUDE_PICKUP")
        expected = cold_verify(lead, review, previous, pickup)
    if args.command != "verify":
        write_once(args.out, expected)
    print(json.dumps({
        "state": expected["state"] if "state" in expected else expected["status"],
        "reason_codes": expected.get("reason_codes", []),
        "id": expected.get("assessment_id", expected.get("handoff_id")),
        "legal_permission_software_verified": False,
        "automatic_collection": False,
        "robot_garden_inventory_added": False,
        "physical_inventory_delta": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, OSError, ValueError, TypeError, KeyError,
            json.JSONDecodeError) as err:
        print("HOLD: " + str(err)[:280], file=sys.stderr)
        raise SystemExit(2)
