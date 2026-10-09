"""ROBOT-GARDEN-004 — HERO3-family manual H.264 MP4 import with frame ancestry.

Targets the *provisional* 2012 HERO3 family, edition unknown. Neither the
video filename nor ffprobe authenticates a GoPro device. ffprobe / ffmpeg
consume an operator-selected local MP4; no camera or network access is used.
"""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.robot_garden import _check_plan
from question_first.robot_garden_three_eyes import capture_three_eyes
from question_first.session import Hold, require

SCHEMA = "static-os.robot-garden-hero3-video/v0"
PROFILE = "static-os.provisional-hero3-family/v0"
MAX_VIDEO_BYTES = 512 * 1024 * 1024
MAX_FRAME_BYTES = 20 * 1024 * 1024
MAX_FRAME_INDEX = 1800
PROCESS_TIMEOUT_SECONDS = 45


def _exact(value: Any, keys: set[str]) -> bool:
    return type(value) is dict and set(value) == keys


def validate_profile(raw: Any) -> dict:
    require(_exact(raw, {
        "schema", "reference_family", "approximate_release_year", "edition",
        "identity_status", "owner_confirmed_device", "firmware_verified",
        "media_transfer", "expected_container", "expected_video_codec",
        "wifi_authorized", "usb_camera_control_authorized",
        "robot_motion_authorized", "physical_part_attested",
    }), "HERO3_PROFILE_EXACT_FIELDS_REQUIRED")
    require(raw["schema"] == PROFILE
            and raw["reference_family"] == "GOPRO_HERO3_2012"
            and raw["approximate_release_year"] == 2012
            and type(raw["approximate_release_year"]) is int
            and raw["edition"] == "UNKNOWN"
            and raw["identity_status"] == "PROVISIONAL_REFERENCE_NOT_OWNED_DEVICE_PROOF"
            and raw["media_transfer"] == "MANUAL_MICROSD_OR_LOCAL_COPY"
            and raw["expected_container"] == "MP4"
            and raw["expected_video_codec"] == "H264"
            and all(raw[k] is False for k in (
                "owner_confirmed_device", "firmware_verified",
                "wifi_authorized", "usb_camera_control_authorized",
                "robot_motion_authorized", "physical_part_attested")),
            "HERO3_PROVISIONAL_REFERENCE_CANNOT_GRANT_HARDWARE_AUTHORITY")
    return raw


def _tools() -> tuple[str, str]:
    probe, ffmpeg = shutil.which("ffprobe"), shutil.which("ffmpeg")
    require(probe is not None and ffmpeg is not None,
            "FFMPEG_AND_FFPROBE_LOCAL_TOOLS_REQUIRED")
    return probe, ffmpeg


def _run(argv: list[str], *, timeout: int = PROCESS_TIMEOUT_SECONDS) -> bytes:
    try:
        p = subprocess.run(argv, stdin=subprocess.DEVNULL,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           timeout=timeout, check=False)
    except (subprocess.TimeoutExpired, OSError) as err:
        raise Hold("LOCAL_MEDIA_TOOL_FAILED_OR_TIMED_OUT") from err
    require(p.returncode == 0, "MEDIA_PROBE_OR_FRAME_DECODE_REFUSED")
    return p.stdout


def _hash_video(path: Path) -> tuple[str, int]:
    path = Path(path)
    require(path.is_file() and not path.is_symlink()
            and path.suffix.lower() == ".mp4",
            "ORIGINAL_LOCAL_MP4_FILE_REQUIRED")
    size = path.stat().st_size
    require(32 < size <= MAX_VIDEO_BYTES, "MP4_VIDEO_SIZE_LIMIT")
    sha = hashlib.sha256()
    with path.open("rb") as f:
        require(f.read(4) != b"", "EMPTY_MP4")
        f.seek(0)
        head = f.read(12)
        require(head[4:8] == b"ftyp", "MP4_FILE_SIGNATURE_REQUIRED")
        sha.update(head)
        while chunk := f.read(1024 * 1024):
            sha.update(chunk)
    return sha.hexdigest(), size


def _probe_media(probe: str, file: Path) -> dict:
    data = _run([
        probe, "-v", "error", "-protocol_whitelist", "file",
        "-select_streams", "v:0", "-show_entries",
        "stream=codec_name,width,height,nb_frames,avg_frame_rate:format=format_name",
        "-of", "json", str(file.resolve())
    ])
    require(len(data) <= 16384, "MEDIA_PROBE_OUTPUT_TOO_LARGE")
    try:
        raw = json.loads(data)
    except (json.JSONDecodeError, UnicodeError) as err:
        raise Hold("MEDIA_PROBE_RETURNED_INVALID_JSON") from err
    require(type(raw) is dict
            and type(raw.get("streams")) is list
            and len(raw["streams"]) == 1
            and type(raw.get("format")) is dict,
            "EXACTLY_ONE_FIRST_VIDEO_STREAM_REQUIRED")
    stream = raw["streams"][0]
    w, h = stream.get("width"), stream.get("height")
    require(stream.get("codec_name") == "h264"
            and type(w) is int and type(h) is int
            and 64 <= w <= 4096 and 64 <= h <= 4096
            and w * h <= 16_000_000,
            "HERO3_ADAPTER_REQUIRES_BOUNDED_H264_VIDEO")
    require("mp4" in raw["format"].get("format_name", "").split(","),
            "MP4_CONTAINER_REQUIRED")
    return {
        "container": "MP4_PROBED",
        "video_codec": "H264_PROBED",
        "video_width_px": w,
        "video_height_px": h,
        "declared_frame_count_untrusted": stream.get("nb_frames"),
        "declared_frame_rate_untrusted": stream.get("avg_frame_rate"),
        "codec_metadata_source": "LOCAL_FFPROBE_NOT_ORIGINAL_CAMERA_ATTESTATION",
    }


def extract_frame(video: Path, frame_index: int) -> tuple[bytes, dict]:
    """Video file and deterministic frame selection; no sensor/temporal proof."""
    require(type(frame_index) is int and 0 <= frame_index <= MAX_FRAME_INDEX,
            "EXPLICIT_BOUNDED_FRAME_INDEX_REQUIRED")
    sha_pre, bytes_pre = _hash_video(Path(video))
    probe, ffmpeg = _tools()
    stream = _probe_media(probe, Path(video))
    # This is a fixed local process argv. The file protocol is the only input
    # protocol allowed, no shell, no URI/remote camera, no host actions.
    png = _run([
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-protocol_whitelist", "file", "-i", str(Path(video).resolve()),
        "-map", "0:v:0", "-vf", f"select=eq(n\\,{frame_index})",
        "-frames:v", "1", "-vsync", "0", "-pix_fmt", "rgb24",
        "-f", "image2pipe", "-vcodec", "png", "pipe:1",
    ])
    require(0 < len(png) <= MAX_FRAME_BYTES
            and png.startswith(b"\x89PNG\r\n\x1a\n"),
            "EXACTLY_ONE_BOUNDED_DECODED_PNG_REQUIRED")
    sha_post, bytes_post = _hash_video(Path(video))
    require(sha_pre == sha_post and bytes_pre == bytes_post,
            "ORIGINAL_VIDEO_CHANGED_DURING_DECODE")
    return png, {
        "original_h264_mp4_sha256": sha_pre,
        "original_video_byte_count": bytes_pre,
        "frame_index_zero_based": frame_index,
        "frame_png_sha256": hashlib.sha256(png).hexdigest(),
        "frame_png_byte_count": len(png),
        "video_probe": stream,
        "ffmpeg_tool_banner_untrusted": _run([ffmpeg, "-version"]).decode(
            "utf-8", "replace").splitlines()[0][:200],
        "frame_origin": "LOCAL_FFMPEG_REDECODE_FROM_HASHED_MP4",
        "video_is_authenticated_gopro_output": False,
        "frame_camera_timestamp_authenticated": False,
        "frame_extraction_is_physical_sensor_witness": False,
    }


def capture_hero3(plan: dict, phone: Path, t3i: Path, video: Path,
                  profile: Any, lens: Any, chart: Any,
                  frame_index: int = 0) -> tuple[dict, bytes]:
    _check_plan(plan)
    hardware = validate_profile(profile)
    png, lineage = extract_frame(Path(video), frame_index)
    with tempfile.TemporaryDirectory(prefix="robot-garden-hero3-frame-") as d:
        derived = Path(d) / "derived-gopro-frame.png"
        derived.write_bytes(png)
        triplet = capture_three_eyes(plan, Path(phone), Path(t3i),
                                     derived, lens, chart)
    require(triplet["gopro"]["original_bytes_sha256"]
            == lineage["frame_png_sha256"],
            "EXTRACTED_FRAME_MUST_BIND_PARENT_THREE_EYES")
    body = {
        "schema": SCHEMA,
        "provisional_hardware_profile_digest": digest(hardware),
        "source_signed_cad_crossing_id": plan["signed_cad_crossing_id"],
        "source_fabrication_request_id": plan["fabrication_request_id"],
        "parent_robot_plan_id": plan["plan_id"],
        "parent_three_eyes_triplet_id": triplet["triplet_id"],
        "three_eyes": triplet,
        "original_video_lineage": lineage,
        "frame_is_original_camera_still": False,
        "frame_is_derived_video_extract": True,
        "camera_model_authenticated": False,
        "video_original_from_camera_authenticated": False,
        "physical_scene_or_part_verified": False,
        "robot_camera_control_executed": False,
        "new_physical_inventory": 0,
        "status": "LOCAL_PROVISIONAL_HERO3_MP4_FRAME_REPLAYABLE_NO_CAMERA_AUTHORITY",
    }
    return {**body, "record_id": "static-os-robot-hero3-004:" + digest(body)}, png


def replay_hero3(plan: dict, phone: Path, t3i: Path, video: Path,
                 profile: Any, lens: Any, chart: Any,
                 frame_index: int, claim: Any, frame_png: bytes) -> dict:
    expected, redecoded = capture_hero3(plan, phone, t3i, video, profile,
                                        lens, chart, frame_index)
    require(type(claim) is dict and expected == claim
            and type(frame_png) is bytes and redecoded == frame_png,
            "HERO3_ORIGINAL_VIDEO_FRAME_COLD_REPLAY_DISAGREEMENT")
    return expected
