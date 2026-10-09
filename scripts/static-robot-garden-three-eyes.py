#!/usr/bin/env python3
"""ROBOT-GARDEN-003: 3 original image files + SVG calibration *proposal*."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_first.fabrication_request import verify_request
from question_first.printer_field import _solid_dims
from question_first.robot_garden import plan_inspection
from question_first.robot_garden_three_eyes import (
    capture_three_eyes, chart_svg, replay_three_eyes,
)
from question_first.session import Hold, require


def read_obj(p):
    value = json.loads(Path(p).read_text(encoding="utf-8"))
    require(type(value) is dict, "EXPECTED_JSON_OBJECT")
    return value


def get_plan(args):
    source = Path(args.source)
    original = verify_request(
        source, Path(args.packet), read_obj(args.fleet),
        read_obj(args.selection), read_obj(args.request))
    return plan_inspection(original, _solid_dims(source), read_obj(args.station))


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Three eye local image intake: no camera, robot or metric authority.")
    ap.add_argument("command", choices=("receive", "verify"))
    for flag in ("source", "packet", "fleet", "selection", "request",
                 "station", "phone-photo", "t3i-photo", "gopro-photo",
                 "gopro-lens", "chart-spec", "out-dir"):
        ap.add_argument("--" + flag, required=True)
    args = ap.parse_args(argv)
    parent = get_plan(args)  # original signed CAD and held slicer cold verified
    lens, chart = read_obj(args.gopro_lens), read_obj(args.chart_spec)
    paths = (Path(args.phone_photo), Path(args.t3i_photo), Path(args.gopro_photo))
    output = Path(args.out_dir).expanduser().resolve()

    if args.command == "receive":
        require(not output.exists(), "THREE_EYES_OCCURRENCE_ALREADY_EXISTS")
        receipt = capture_three_eyes(parent, *paths, lens, chart)
        svg = chart_svg(chart)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(exist_ok=False)
        (output / "receipt.json").write_text(
            json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        (output / "nominal-checkerboard.svg").write_bytes(svg)
    else:
        receipt = replay_three_eyes(
            parent, *paths, lens, chart, read_obj(output / "receipt.json"))
        require((output / "nominal-checkerboard.svg").read_bytes()
                == chart_svg(chart), "PRINTABLE_TARGET_NOT_COLD_REPLAYED")

    print(json.dumps({
        "state": receipt["result"],
        "triplet_id": receipt["triplet_id"],
        "image_file_count": 3,
        "camera_hardware_authenticated": False,
        "chart_physically_measured": False,
        "real_world_measurements": False,
        "robot_actuated": False,
        "new_physical_inventory": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, ValueError, TypeError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("HOLD: " + str(exc)[:320], file=sys.stderr)
        raise SystemExit(2)
