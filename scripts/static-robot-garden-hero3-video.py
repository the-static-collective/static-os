#!/usr/bin/env python3
"""ROBOT-GARDEN-004: local HERO3-target MP4 frame import, never camera control."""
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
from question_first.robot_garden_hero3_video import capture_hero3, replay_hero3
from question_first.session import Hold, require


def read_obj(path: str | Path) -> dict:
    result = json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(result) is dict, "EXPECTED_JSON_OBJECT")
    return result


def cold_source_plan(args) -> dict:
    source = Path(args.source)
    authenticated = verify_request(
        source, Path(args.packet), read_obj(args.fleet),
        read_obj(args.selection), read_obj(args.request))
    return plan_inspection(authenticated, _solid_dims(source),
                           read_obj(args.station))


def main(argv=None):
    p = argparse.ArgumentParser(
        description="HERO3-family video is a provisional local file donor, not connected hardware.")
    p.add_argument("command", choices=("receive", "verify"))
    for key in ("source", "packet", "fleet", "selection", "request",
                "station", "phone-photo", "t3i-photo", "gopro-video",
                "hero3-profile", "gopro-lens", "chart-spec", "out-dir"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--frame-index", type=int, default=0)
    args = p.parse_args(argv)
    plan = cold_source_plan(args)
    inputs = (plan, Path(args.phone_photo), Path(args.t3i_photo),
              Path(args.gopro_video), read_obj(args.hero3_profile),
              read_obj(args.gopro_lens), read_obj(args.chart_spec),
              args.frame_index)
    output = Path(args.out_dir).expanduser().resolve()
    frame_path = output / f"gopro-derived-frame-{args.frame_index:06d}.png"
    receipt_path = output / "video-frame-receipt.json"
    if args.command == "receive":
        require(not output.exists(), "VIDEO_FRAME_OCCURRENCE_EXISTS_NO_AUTORETRY")
        report, frame_png = capture_hero3(*inputs)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.mkdir(exist_ok=False)
        frame_path.write_bytes(frame_png)
        receipt_path.write_text(json.dumps(report, sort_keys=True, indent=2) + "\n",
                                encoding="utf-8")
    else:
        report = replay_hero3(*inputs, read_obj(receipt_path),
                              frame_path.read_bytes())
    print(json.dumps({
        "status": report["status"],
        "record_id": report["record_id"],
        "original_video_sha256": report["original_video_lineage"][
            "original_h264_mp4_sha256"],
        "extracted_frame_index": args.frame_index,
        "camera_identity_authenticated": False,
        "frame_was_original_still_photo": False,
        "robot_movement_executed": False,
        "new_physical_inventory": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, ValueError, TypeError, KeyError, OSError,
            json.JSONDecodeError) as err:
        print("HOLD: " + str(err)[:280], file=sys.stderr)
        raise SystemExit(2)
