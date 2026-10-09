"""ROBOT-GARDEN-001: Jubilee-inspired *simulation* of camera-based inspection.

No motion commands, machine transport, authentic camera capture, part custody,
hardware inventory, or owner grants. A source-verified CAD bundle is mandatory
at the CLI boundary; these pure functions do not independently authenticate it.
"""
from __future__ import annotations

import hashlib
import math
import re
from typing import Any

from crank.runtime import digest
from question_first.session import require

SCHEMA = "static-os.robot-garden-plan/v0"
STATION_SCHEMA = "static-os.robot-garden-station/v0"
REPORT_SCHEMA = "static-os.robot-garden-report/v0"
FABRICATION_SCHEMA = "static-os.fabrication-request/v0"
STATION_ID = "sim:science-jubilee-camera"
SOURCE_NODE = "virtual:fff-pla-180"
MAX_PIXELS = 512 * 512
MAX_SIDE = 512
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9:._-]{2,99}$")


def _exact(value: Any, keys: set[str]) -> bool:
    return type(value) is dict and set(value) == keys


def _sealed(body: dict, field: str, prefix: str) -> dict:
    return {**body, field: prefix + digest(body)}


def validate_station(station: Any) -> dict:
    require(_exact(station, {
        "schema", "station_id", "reference_platform", "reference_software",
        "simulator_kind", "camera_pixels_per_mm", "envelope_mm",
        "owner_claim", "hardware_present", "camera_connected",
        "movement_authorized", "toolchange_authorized", "transport_authorized",
        "physical_inspection_authorized",
    }), "STATION_EXACT_FIELDS_REQUIRED")
    require(station["schema"] == STATION_SCHEMA
            and station["station_id"] == STATION_ID
            and station["reference_platform"] == "machineagency/jubilee"
            and station["reference_software"] == "machineagency/science-jubilee"
            and station["simulator_kind"] == "SYNTHETIC_MONOCHROME_PGM"
            and station["owner_claim"] == "NONE_REFERENCE_ONLY"
            and all(station[k] is False for k in (
                "hardware_present", "camera_connected", "movement_authorized",
                "toolchange_authorized", "transport_authorized",
                "physical_inspection_authorized")),
            "SIMULATOR_MUST_NOT_IMPLY_HARDWARE_AUTHORITY")
    scale = station["camera_pixels_per_mm"]
    require(type(scale) is int and 1 <= scale <= 4, "INVALID_SYNTHETIC_CAMERA_SCALE")
    envelope = station["envelope_mm"]
    require(_exact(envelope, {"x", "y", "z"})
            and all(type(envelope[k]) is int and 1 <= envelope[k] <= 300
                    for k in ("x", "y", "z")),
            "SIMULATOR_BOUNDS_MISSING")
    return station


def plan_inspection(verified_request: Any, solid_dims: Any, station: Any) -> dict:
    """Caller must independently cold-verify 013 + derive dims from signed CAD."""
    validate_station(station)
    require(type(verified_request) is dict
            and verified_request.get("schema") == FABRICATION_SCHEMA
            and verified_request.get("state") == "FABRICATION_PROPOSAL_ONLY"
            and verified_request.get("fabrication_occurred") is False
            and verified_request.get("owner_machine_grants_included") is False
            and type(verified_request.get("physical_parts")) is int
            and verified_request.get("physical_parts") == 0
            and type(verified_request.get("new_money")) is int
            and verified_request.get("new_money") == 0
            and verified_request.get("requested_node_count") == 3,
            "ONLY_BOUNDED_UNEXECUTED_013_PROPOSAL")
    nodes = verified_request.get("selected_nodes")
    require(type(nodes) is list and len(nodes) == 3, "THREE_SOURCE_NODES_REQUIRED")
    require(all(type(n) is dict and n.get("hardware_authenticated") is False
                and n.get("physical_print_permission") is False
                for n in nodes), "NO_SOURCE_MACHINE_PERMISSIONS")
    virtual = [n for n in nodes if n.get("machine_id") == SOURCE_NODE
               and n.get("published_compatibility") == "SOFTWARE_TOOLPATH_ONLY"]
    require(len(virtual) == 1, "VERIFIED_VIRTUAL_013_NODE_REQUIRED")
    for key in ("request_id", "original_signed_cad_crossing_id",
                "original_print_packet_id", "source_design_candidate_id"):
        require(type(verified_request.get(key)) is str
                and len(verified_request[key]) >= 8,
                "SOURCE_IDENTITY_REQUIRED_" + key)
    require(_exact(solid_dims, {"x", "y", "z"}),
            "SOURCE_GEOMETRY_EXACT_AXES_REQUIRED")
    require(all(type(solid_dims[k]) in (int, float)
                and math.isfinite(solid_dims[k]) and solid_dims[k] > 0
                and solid_dims[k] <= station["envelope_mm"][k]
                for k in ("x", "y", "z")),
            "SIGNED_SOURCE_NOT_IN_STATION_ENVELOPE")
    xy = {k: round(solid_dims[k], 5) for k in ("x", "y")}
    scale = station["camera_pixels_per_mm"]
    require(all(round(xy[k] * scale * 1.7) + 20 <= MAX_SIDE
                and xy[k] * scale >= 4 for k in ("x", "y")),
            "SYNTHETIC_CAPTURE_SIZE_UNSUPPORTED")
    body = {
        "schema": SCHEMA,
        "source_repository": "the-static-collective/static-os",
        "fabrication_request_id": verified_request["request_id"],
        "signed_cad_crossing_id": verified_request["original_signed_cad_crossing_id"],
        "source_print_packet_id": verified_request["original_print_packet_id"],
        "source_design_candidate_id": verified_request["source_design_candidate_id"],
        "selected_source_node": SOURCE_NODE,
        "station_id": station["station_id"],
        "station_declaration_digest": digest(station),
        "inspection_modality": "SYNTHETIC_CAMERA_2D_BOUNDING_BOX",
        "source_target_xy_mm": xy,
        "pixels_per_mm": scale,
        "tolerance_mm": 0.6,
        "plan_state": "SIMULATION_ONLY_NO_MACHINE_EFFECT",
        "no_machine_commands": True,
        "camera_connected": False,
        "physical_part_present": False,
        "toolchange_permitted": False,
        "robot_motion_permitted": False,
        "physical_inventory_delta": 0,
    }
    return _sealed(body, "plan_id", "static-os-robot-garden-001:")


def _check_plan(plan: Any) -> None:
    require(type(plan) is dict and isinstance(plan.get("plan_id"), str),
            "PLAN_REQUIRED")
    expected_keys = {
        "schema", "source_repository", "fabrication_request_id",
        "signed_cad_crossing_id", "source_print_packet_id",
        "source_design_candidate_id", "selected_source_node", "station_id",
        "station_declaration_digest", "inspection_modality",
        "source_target_xy_mm", "pixels_per_mm", "tolerance_mm",
        "plan_state", "no_machine_commands", "camera_connected",
        "physical_part_present", "toolchange_permitted",
        "robot_motion_permitted", "physical_inventory_delta", "plan_id",
    }
    require(set(plan) == expected_keys, "PLAN_NOT_A_SAFE_SIMULATION")
    body = {k: v for k, v in plan.items() if k != "plan_id"}
    require(plan["plan_id"] == "static-os-robot-garden-001:" + digest(body)
            and plan.get("schema") == SCHEMA
            and plan.get("plan_state") == "SIMULATION_ONLY_NO_MACHINE_EFFECT"
            and plan.get("no_machine_commands") is True
            and plan.get("camera_connected") is False
            and plan.get("physical_part_present") is False
            and plan.get("toolchange_permitted") is False
            and plan.get("robot_motion_permitted") is False
            and plan.get("physical_inventory_delta") == 0,
            "PLAN_NOT_A_SAFE_SIMULATION")


def synthetic_pgm(plan: dict, width_factor: float = 1.0,
                  height_factor: float = 1.0) -> bytes:
    """Synthetic pixels ONLY. No camera, gripper, or motion controller."""
    _check_plan(plan)
    require(all(type(v) in (float, int) and math.isfinite(v) and
                0.5 <= v <= 1.5 for v in (width_factor, height_factor)),
            "MOCK_FACTOR_OUT_OF_RANGE")
    scale = plan["pixels_per_mm"]
    target = plan["source_target_xy_mm"]
    width = round(target["x"] * scale * 1.7) + 20
    height = round(target["y"] * scale * 1.7) + 20
    require(16 <= width <= MAX_SIDE and 16 <= height <= MAX_SIDE,
            "SYNTHETIC_FRAME_BOUNDS")
    rect_w = round(target["x"] * float(width_factor) * scale)
    rect_h = round(target["y"] * float(height_factor) * scale)
    require(2 <= rect_w < width and 2 <= rect_h < height,
            "SYNTHETIC_OBJECT_OUT_OF_VIEW")
    left = (width - rect_w) // 2
    top = (height - rect_h) // 2
    pixels = bytearray([255]) * (width * height)
    for y in range(top, top + rect_h):
        p = y * width + left
        pixels[p:p + rect_w] = bytes(rect_w)
    return f"P5\n{width} {height}\n255\n".encode("ascii") + pixels


def _image_bounds(image: bytes) -> dict:
    require(type(image) is bytes and len(image) < MAX_PIXELS + 40,
            "IMAGE_TOO_LARGE_OR_INVALID")
    parts = image.split(b"\n", 3)
    require(len(parts) == 4 and parts[0] == b"P5" and parts[2] == b"255",
            "UNSUPPORTED_PGM_HEADER")
    try:
        dims = parts[1].split(b" ")
        require(len(dims) == 2 and all(d.isdigit() for d in dims),
                "INVALID_PGM_AXES")
        width, height = (int(d) for d in dims)
    except (ValueError, UnicodeError):
        raise ValueError("INVALID_PGM_AXES")
    require(1 <= width <= MAX_SIDE and 1 <= height <= MAX_SIDE
            and len(parts[3]) == width * height, "PGM_SIZE_MISMATCH")
    raw = parts[3]
    require(all(p in (0, 255) for p in raw), "SYNTHETIC_BINARY_PIXELS_ONLY")
    xs, ys = [], []
    for i, p in enumerate(raw):
        if p == 0:
            xs.append(i % width)
            ys.append(i // width)
    require(len(xs) > 0, "NO_INSPECTABLE_FOREGROUND")
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    require(len(xs) == (maxx - minx + 1) * (maxy - miny + 1),
            "NON_RECTANGULAR_MOCK_OBJECT")
    return {"width_px": maxx - minx + 1,
            "height_px": maxy - miny + 1,
            "frame_width_px": width,
            "frame_height_px": height}


def inspect_frame(plan: dict, image: bytes) -> dict:
    """Independent pixel measurement; neither an actual camera nor metrology."""
    _check_plan(plan)
    box = _image_bounds(image)
    measured = {axis: round(box[n] / plan["pixels_per_mm"], 5)
                for axis, n in (("x", "width_px"), ("y", "height_px"))}
    delta = {axis: round(measured[axis] - plan["source_target_xy_mm"][axis], 5)
             for axis in ("x", "y")}
    match = all(abs(delta[k]) <= plan["tolerance_mm"] for k in ("x", "y"))
    body = {
        "schema": REPORT_SCHEMA,
        "plan_id": plan["plan_id"],
        "source_fabrication_request_id": plan["fabrication_request_id"],
        "frame_sha256": hashlib.sha256(image).hexdigest(),
        "frame_kind": "LOCALLY_SYNTHESIZED_NO_CAMERA",
        "pixel_bounding_box": box,
        "measured_xy_mm": measured,
        "delta_xy_mm": delta,
        "classification": "SIMULATED_GEOMETRY_MATCH" if match
                          else "SIMULATED_GEOMETRY_MISMATCH",
        "is_physical_observation": False,
        "is_signed_sensor_evidence": False,
        "part_custody_verified": False,
        "material_witness_accepted": False,
        "printer_or_robot_activated": False,
        "new_physical_inventory": 0,
    }
    return _sealed(body, "report_id", "static-os-robot-report-001:")


def verify_simulation(plan: dict, image: bytes, report: Any) -> dict:
    require(type(report) is dict and report == inspect_frame(plan, image),
            "COLD_INSPECTION_REPLAY_DISAGREEMENT")
    return report
