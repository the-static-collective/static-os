#!/usr/bin/env python3
"""ROBOT-GARDEN-002: phone + Canon T3i files, no camera or robot connection."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from question_first.fabrication_request import verify_request
from question_first.printer_field import _solid_dims
from question_first.robot_garden import plan_inspection
from question_first.robot_garden_photos import inspect_original, verify_original
from question_first.session import Hold, require


def read_obj(path):
    candidate = json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(candidate) is dict, "EXPECTED_JSON_OBJECT")
    return candidate


def source_plan(args):
    source = Path(args.source)
    original = verify_request(
        source, Path(args.packet), read_obj(args.fleet),
        read_obj(args.selection), read_obj(args.request))
    return plan_inspection(original, _solid_dims(source), read_obj(args.station))


def write_once(path, result):
    p = Path(path)
    require(not p.exists(), "IMAGE_PAIR_RECEIPT_EXISTS_NO_AUTORETRY")
    p.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(p), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, sort_keys=True)
        f.write("\n")


def main(argv=None):
    p = argparse.ArgumentParser(
        description="Cold-source-bound image quality observations. No camera control.")
    p.add_argument("command", choices=("receive", "verify"))
    for name in ("source", "packet", "fleet", "selection", "request", "station",
                 "phone-photo", "t3i-photo", "out"):
        p.add_argument("--" + name, required=True)
    args = p.parse_args(argv)
    plan = source_plan(args)
    phone, t3i = Path(args.phone_photo), Path(args.t3i_photo)
    if args.command == "receive":
        require(not Path(args.out).exists(), "IMAGE_PAIR_RECEIPT_EXISTS_NO_AUTORETRY")
        report = inspect_original(plan, phone, t3i)
        write_once(args.out, report)
    else:
        report = verify_original(plan, phone, t3i, read_obj(args.out))
    print(json.dumps({
        "status": report["state"],
        "pair_id": report["pair_id"],
        "image_files_decoded": report["input_count"],
        "role_names_verified": False,
        "camera_hardware_control": False,
        "physical_part_verified": False,
        "new_physical_inventory": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, ValueError, TypeError, KeyError, OSError,
            json.JSONDecodeError) as exc:
        print("HOLD: " + str(exc)[:260], file=sys.stderr)
        raise SystemExit(2)
