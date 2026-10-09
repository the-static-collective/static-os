"""ROBOT-GARDEN-002 — real local JPEG/PNG bytes, but NOT authenticated sensor evidence.

A phone and Canon T3i are *operator-declared* input roles. The detector does
not connect to either device or infer real-world physical inspection, custody,
calibration, or machine permissions. Image hashes are not signatures.
"""
from __future__ import annotations

import hashlib
import io
from pathlib import Path
from typing import Any

from PIL import Image, ImageOps, UnidentifiedImageError

from crank.runtime import digest
from question_first.robot_garden import _check_plan
from question_first.session import Hold, require

SCHEMA = "static-os.robot-garden-photo-pair/v0"
PHONE = "PHONE_OPERATOR_IMPORT"
T3I = "CANON_EOS_REBEL_T3I_600D_OPERATOR_IMPORT"
MAX_BYTES = 40 * 1024 * 1024
MAX_PIXELS = 64_000_000
PREVIEW_SIDE = 256

# This is a real decoder boundary, not a claim of camera provenance.
Image.MAX_IMAGE_PIXELS = MAX_PIXELS


def _read_image(path: Path) -> bytes:
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "ORIGINAL_IMAGE_FILE_REQUIRED")
    require(0 < p.stat().st_size <= MAX_BYTES, "ORIGINAL_IMAGE_SIZE_LIMIT")
    with p.open("rb") as f:
        data = f.read(MAX_BYTES + 1)
    require(0 < len(data) <= MAX_BYTES, "ORIGINAL_IMAGE_SIZE_LIMIT")
    return data


def _image_metrics(data: bytes) -> dict:
    require(type(data) is bytes and 0 < len(data) <= MAX_BYTES,
            "ORIGINAL_IMAGE_BYTES_BOUNDED")
    is_jpeg = data[:3] == b"\xff\xd8\xff"
    is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
    require(is_jpeg or is_png, "ONLY_JPEG_OR_PNG_ACCEPTED")
    try:
        with Image.open(io.BytesIO(data)) as probe:
            image_format = probe.format
            width, height = probe.size
            require(image_format in ("JPEG", "PNG")
                    and ((image_format == "JPEG") == is_jpeg),
                    "IMAGE_TYPE_AND_SIGNATURE_DISAGREE")
            require(64 <= width <= 16384 and 64 <= height <= 16384
                    and width * height <= MAX_PIXELS,
                    "DECODED_IMAGE_DIMENSIONS_OUT_OF_BOUNDS")
            probe.verify()
        with Image.open(io.BytesIO(data)) as source:
            source.load()  # force actual decoding, never just trust file headers
            upright = ImageOps.exif_transpose(source)
            oriented_width, oriented_height = upright.size
            gray = upright.convert("L")
            gray.thumbnail((PREVIEW_SIDE, PREVIEW_SIDE), Image.Resampling.BILINEAR)
            width_small, height_small = gray.size
            luminance = gray.tobytes()
    except Hold:
        raise
    except (OSError, ValueError, SyntaxError, UnidentifiedImageError,
            Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise Hold("ORIGINAL_IMAGE_FAILED_STRICT_DECODE") from exc
    require(width_small > 1 and height_small > 1
            and len(luminance) == width_small * height_small,
            "IMAGE_SAMPLE_MISSING")

    dark_count = sum(v < 24 for v in luminance)
    bright_count = sum(v > 231 for v in luminance)
    mean = sum(luminance) / len(luminance)
    # Gradient is a rough texture/edge proxy, NOT a validated focus metric.
    gradient_sum = 0
    gradient_edges = 0
    for y in range(height_small):
        row = y * width_small
        for x in range(width_small):
            i = row + x
            if x + 1 < width_small:
                gradient_sum += abs(luminance[i] - luminance[i + 1])
                gradient_edges += 1
            if y + 1 < height_small:
                gradient_sum += abs(luminance[i] - luminance[i + width_small])
                gradient_edges += 1
    return {
        "format": image_format,
        "encoded_width_px": width,
        "encoded_height_px": height,
        "orientation_applied_from_untrusted_metadata": True,
        "display_width_px": oriented_width,
        "display_height_px": oriented_height,
        "sample_width_px": width_small,
        "sample_height_px": height_small,
        "sample_mean_luminance_0_255": round(mean, 4),
        "sample_dark_fraction": round(dark_count / len(luminance), 6),
        "sample_bright_fraction": round(bright_count / len(luminance), 6),
        "sample_edge_delta_0_255": round(gradient_sum / gradient_edges, 4),
        "metric_scope": "UNCALIBRATED_IMAGE_HEURISTICS_NOT_PART_METROLOGY",
    }


def inspect_original(plan: dict, phone_file: Path, t3i_file: Path) -> dict:
    """File bytes genuinely decoded. Device roles are user claims, not attestations."""
    _check_plan(plan)
    require(plan.get("schema") == "static-os.robot-garden-plan/v0"
            and plan.get("physical_part_present") is False
            and plan.get("camera_connected") is False,
            "PARENT_001_MUST_REMAIN_NONPHYSICAL")
    inputs = ((PHONE, Path(phone_file)), (T3I, Path(t3i_file)))
    records = []
    for source_role, path in inputs:
        raw = _read_image(path)
        records.append({
            "role": source_role,
            "acquisition": "MANUALLY_IMPORTED_FILE_OPERATOR_ASSERTION",
            "original_bytes_sha256": hashlib.sha256(raw).hexdigest(),
            "original_bytes_length": len(raw),
            "decode": _image_metrics(raw),
            "camera_identity_verified": False,
            "capture_time_authenticated": False,
            "exif_trusted": False,
            "independent_real_world_witness": False,
        })
    require(records[0]["original_bytes_sha256"] != records[1]["original_bytes_sha256"],
            "SAME_IMAGE_BYTES_CANNOT_BECOME_TWO_CAMERA_WITNESSES")
    body = {
        "schema": SCHEMA,
        "parent_inspection_plan_id": plan["plan_id"],
        "original_signed_cad_crossing_id": plan["signed_cad_crossing_id"],
        "fabrication_request_id": plan["fabrication_request_id"],
        "original_print_packet_id": plan["source_print_packet_id"],
        "input_count": 2,
        "records": records,
        "comparison": {
            "same_encoded_file_bytes": False,
            "physical_object_identity_established": False,
            "independent_capture_devices_authenticated": False,
            "same_capture_session_authenticated": False,
            "geometry_calibration_present": False,
            "calibrated_part_dimensions_present": False,
        },
        "state": "REAL_FILES_DECODED_SOURCE_ROLES_UNVERIFIED",
        "physical_part_verified": False,
        "signed_sensor_evidence": False,
        "robot_or_camera_command_sent": False,
        "material_custody_verified": False,
        "new_physical_inventory": 0,
    }
    return {**body, "pair_id": "static-os-robot-photos-002:" + digest(body)}


def verify_original(plan: dict, phone_file: Path, t3i_file: Path,
                    candidate: Any) -> dict:
    require(type(candidate) is dict
            and candidate == inspect_original(plan, phone_file, t3i_file),
            "REAL_PHOTO_PAIR_COLD_REPLAY_DISAGREEMENT")
    return candidate
