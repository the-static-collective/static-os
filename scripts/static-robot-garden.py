#!/usr/bin/env python3
"""ROBOT-GARDEN-001: replayable synthetic camera experiment, never machine control."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from question_first.fabrication_request import verify_request
from question_first.printer_field import _solid_dims
from question_first.robot_garden import (
    inspect_frame, plan_inspection, synthetic_pgm, verify_simulation,
)
from question_first.session import Hold, require


def read_obj(path):
    x = json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(x) is dict, "EXPECTED_JSON_OBJECT")
    return x


def original_plan(args):
    # verify_request transitively cold-replays the 011 sliced packet, its
    # native signed original CAD crossing and the exact 012 printer field.
    source = Path(args.source)
    request = verify_request(
        source, Path(args.packet), read_obj(args.fleet),
        read_obj(args.selection), read_obj(args.request))
    return plan_inspection(request, _solid_dims(source), read_obj(args.station))


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Source-verified synthetic Jubilee-style inspection, no hardware.")
    parser.add_argument("command", choices=("run", "verify"))
    for key in ("source", "packet", "fleet", "selection", "request",
                "station", "out-dir"):
        parser.add_argument("--" + key, required=True)
    parser.add_argument("--mock-width-factor", type=float, default=1.0)
    parser.add_argument("--mock-height-factor", type=float, default=1.0)
    args = parser.parse_args(argv)
    plan = original_plan(args)
    output = Path(args.out_dir).resolve()
    if args.command == "run":
        require(not output.exists(), "INSPECTION_OCCURRENCE_EXISTS_NO_RETRY")
        image = synthetic_pgm(plan, args.mock_width_factor,
                              args.mock_height_factor)
        report = inspect_frame(plan, image)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(exist_ok=False)
        (output / "plan.json").write_text(
            json.dumps(plan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (output / "mock-frame.pgm").write_bytes(image)
        (output / "report.json").write_text(
            json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    else:
        require(args.mock_width_factor == 1 and args.mock_height_factor == 1,
                "VERIFICATION_NEVER_GENERATES_NEW_OBSERVATIONS")
        require(read_obj(output / "plan.json") == plan,
                "PLAN_DISAGREES_WITH_SIGNED_ORIGINAL")
        report = verify_simulation(
            plan, (output / "mock-frame.pgm").read_bytes(),
            read_obj(output / "report.json"))
    print(json.dumps({
        "status": report["classification"],
        "plan_id": plan["plan_id"],
        "report_id": report["report_id"],
        "camera_connected": False,
        "robot_actuated": False,
        "physical_parts_inspected": 0,
        "new_physical_inventory": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as error:
        print("HOLD: " + str(error)[:300], file=sys.stderr)
        raise SystemExit(2)
