"""ROBOT-GARDEN-003: third GoPro file donor + nominal calibration chart.

Only local file bytes and operator-reported camera metadata. NO device auth,
robot movement, exposure synchronization, physical chart or metric calibration.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.robot_garden import _check_plan
from question_first.robot_garden_photos import (
    PHONE, T3I, _image_metrics, _read_image, inspect_original,
)
from question_first.session import require

SCHEMA = "static-os.robot-garden-three-eyes/v0"
LENS_SCHEMA = "static-os.operator-gopro-lens-declaration/v0"
CHART_SCHEMA = "static-os.robot-garden-nominal-chart/v0"
ROLE = "GOPRO_OPERATOR_IMPORT_UNVERIFIED"
LENS_MODES = frozenset({"UNKNOWN", "WIDE", "LINEAR", "NARROW", "SUPERVIEW",
                        "HYPERVIEW", "OTHER"})
MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._()+:/-]{0,79}$")


def _exact(candidate: Any, keys: set[str]) -> bool:
    return type(candidate) is dict and set(candidate) == keys


def validate_lens_claim(raw: Any) -> dict:
    require(_exact(raw, {"schema", "operator_reported_model",
                         "operator_reported_digital_lens",
                         "operator_reported_image_processing",
                         "camera_identity_authenticated",
                         "lens_intrinsics_calibrated"}),
            "GOPRO_LENS_DECLARATION_EXACT_FIELDS_REQUIRED")
    require(raw["schema"] == LENS_SCHEMA
            and type(raw["operator_reported_model"]) is str
            and MODEL_RE.fullmatch(raw["operator_reported_model"]) is not None
            and raw["operator_reported_digital_lens"] in LENS_MODES
            and raw["operator_reported_image_processing"] in (
                "UNKNOWN", "CAMERA_ORIGINAL_JPEG", "EXPORTED_OR_DERIVED_IMAGE")
            and raw["camera_identity_authenticated"] is False
            and raw["lens_intrinsics_calibrated"] is False,
            "UNTRUSTED_GOPRO_MODE_IS_NOT_CAMERA_AUTHORITY")
    return raw


def validate_chart(raw: Any) -> dict:
    require(_exact(raw, {"schema", "squares_across", "squares_down",
                         "nominal_square_mm", "physical_chart_printed",
                         "physical_square_measured", "camera_calibrated",
                         "lens_distortion_corrected", "physical_scale_authorized"}),
            "CHART_EXACT_FIELDS_REQUIRED")
    require(raw["schema"] == CHART_SCHEMA
            and raw["squares_across"] == 10
            and raw["squares_down"] == 7
            and type(raw["nominal_square_mm"]) is int
            and raw["nominal_square_mm"] == 15
            and all(raw[key] is False for key in (
                "physical_chart_printed", "physical_square_measured",
                "camera_calibrated", "lens_distortion_corrected",
                "physical_scale_authorized")),
            "NOMINAL_CHART_IS_NOT_PHYSICAL_CALIBRATION")
    return raw


def chart_svg(raw: dict) -> bytes:
    """A vector target with 9x6 inner corners; real print scale is unverified."""
    chart = validate_chart(raw)
    n, m, step, margin = (chart["squares_across"], chart["squares_down"],
                           chart["nominal_square_mm"], 12)
    w, h = n * step + margin * 2, m * step + margin * 2
    blocks = []
    for y in range(m):
        for x in range(n):
            if (x + y) % 2 == 0:
                blocks.append(
                    f'<rect x="{margin + x * step}" y="{margin + y * step}" '
                    f'width="{step}" height="{step}" fill="#000"/>')
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}mm" height="{h}mm" '
        f'viewBox="0 0 {w} {h}">\n'
        f'<title>ROBOT-GARDEN-003 nominal 10 by 7 checkerboard</title>\n'
        '<desc>Nominal dimensions only. Print at 100 percent, then physically '
        'measure squares before any calibration.</desc>\n'
        f'<rect width="{w}" height="{h}" fill="#fff"/>\n'
        + "\n".join(blocks)
        + f'\n<text x="{margin}" y="{h - 3}" font-size="3.5" fill="#000">'
        f'10x7 squares; 9x6 inner corners; nominal {step} mm/square; '
        f'MEASURE ACTUAL PRINT</text>\n</svg>\n'
    ).encode("utf-8")


def capture_three_eyes(plan: dict, phone: Path, t3i: Path, gopro: Path,
                       lens: Any, chart: Any) -> dict:
    _check_plan(plan)
    claim = validate_lens_claim(lens)
    chart_claim = validate_chart(chart)
    pair = inspect_original(plan, phone, t3i)
    raw = _read_image(Path(gopro))
    go_hash = hashlib.sha256(raw).hexdigest()
    already = {record["original_bytes_sha256"] for record in pair["records"]}
    require(go_hash not in already,
            "GOPRO_BYTES_MUST_NOT_DUPLICATE_PHONE_OR_T3I")
    require(len(already) == 2, "PARENT_PAIR_NOT_DISTINCT")
    go_observation = {
        "role": ROLE,
        "operator_reported_model": claim["operator_reported_model"],
        "operator_reported_digital_lens": claim["operator_reported_digital_lens"],
        "operator_reported_processing": claim["operator_reported_image_processing"],
        "original_bytes_sha256": go_hash,
        "original_bytes_length": len(raw),
        "decode": _image_metrics(raw),
        "capture_device_authenticated": False,
        "lens_metadata_authenticated": False,
        "geometric_distortion_calibrated": False,
        "sensor_time_authenticated": False,
        "image_is_real_part_witness": False,
    }
    svg = chart_svg(chart_claim)
    body = {
        "schema": SCHEMA,
        "parent_plan_id": plan["plan_id"],
        "source_signed_cad_crossing_id": plan["signed_cad_crossing_id"],
        "original_print_packet_id": plan["source_print_packet_id"],
        "source_fabrication_request_id": plan["fabrication_request_id"],
        "parent_phone_t3i_pair_id": pair["pair_id"],
        "parent_pair_hashes": [r["original_bytes_sha256"] for r in pair["records"]],
        "input_roles": [PHONE, T3I, ROLE],
        "input_count": 3,
        "three_distinct_encoded_file_hashes": True,
        "gopro": go_observation,
        "operator_lens_declaration_digest": digest(claim),
        "calibration_target": {
            "schema": chart_claim["schema"],
            "chart_declaration_digest": digest(chart_claim),
            "svg_sha256": hashlib.sha256(svg).hexdigest(),
            "squares_across": 10,
            "squares_down": 7,
            "inner_corners_across": 9,
            "inner_corners_down": 6,
            "nominal_square_mm": chart_claim["nominal_square_mm"],
            "actual_physical_square_mm": None,
            "lens_intrinsics": None,
            "reprojection_error_pixels": None,
            "calibration_state": "NOMINAL_DIGITAL_TARGET_NOT_PHYSICAL_CALIBRATION",
        },
        "result": "THREE_IMAGE_FILES_DECODED_ROLES_NOT_AUTHENTICATED",
        "real_world_capture_authenticated": False,
        "frames_temporally_synchronized": False,
        "same_part_established": False,
        "physical_measurements_verified": False,
        "physical_part_custody_verified": False,
        "robot_movement_executed": False,
        "hardware_camera_control_executed": False,
        "new_physical_inventory": 0,
    }
    return {**body, "triplet_id": "static-os-robot-eyes-003:" + digest(body)}


def replay_three_eyes(plan: dict, phone: Path, t3i: Path, gopro: Path,
                      lens: Any, chart: Any, candidate: Any) -> dict:
    require(type(candidate) is dict
            and candidate == capture_three_eyes(plan, phone, t3i, gopro,
                                                lens, chart),
            "THREE_EYES_COLD_ORIGINAL_REPLAY_DISAGREEMENT")
    return candidate
