"""ROBOT-GARDEN-004: bounded HERO3 reference + actual H264 MP4 frame lineage."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crank.runtime import digest
from question_first.robot_garden import plan_inspection
from question_first.robot_garden_hero3_video import (
    capture_hero3, extract_frame, replay_hero3, validate_profile,
)
from question_first.session import Hold
from tests.test_robot_garden_001 import DIMS, REQUEST, STATION
from tests.test_robot_garden_photos_002 import make_image

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "fixtures/robot-garden-004/provisional-hero3-2012.json").read_text())
LENS = json.loads((ROOT / "fixtures/robot-garden-003/gopro-operator-declaration.json").read_text())
CHART = json.loads((ROOT / "fixtures/robot-garden-003/nominal-checkerboard.json").read_text())


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "requires installed ffmpeg and ffprobe")
class LocalVideo(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.phone = root / "phone.jpg"
        self.t3i = root / "t3i.jpg"
        self.video = root / "GOPR0001.MP4"
        make_image(self.phone, 1)
        make_image(self.t3i, 4)
        self.plan = plan_inspection(REQUEST, DIMS, STATION)
        command = [
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
            "-f", "lavfi", "-i", "testsrc=size=160x120:rate=8",
            "-frames:v", "8", "-threads", "1", "-c:v", "libx264",
            "-pix_fmt", "yuv420p", str(self.video),
        ]
        proc = subprocess.run(command, capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, frame=0, profile=PROFILE):
        return capture_hero3(self.plan, self.phone, self.t3i, self.video,
                             profile, LENS, CHART, frame)

    def test_original_mp4_hash_links_actual_decoded_frame_to_three_eyes(self):
        receipt, png = self.capture(0)
        vid = receipt["original_video_lineage"]
        self.assertEqual(vid["original_h264_mp4_sha256"],
                         hashlib.sha256(self.video.read_bytes()).hexdigest())
        self.assertEqual(vid["frame_png_sha256"], hashlib.sha256(png).hexdigest())
        self.assertEqual(receipt["three_eyes"]["gopro"]["original_bytes_sha256"],
                         vid["frame_png_sha256"])
        self.assertEqual(receipt["three_eyes"]["input_count"], 3)
        self.assertEqual(vid["video_probe"]["video_codec"], "H264_PROBED")
        self.assertEqual(vid["video_probe"]["video_width_px"], 160)
        self.assertTrue(receipt["frame_is_derived_video_extract"])
        self.assertFalse(receipt["frame_is_original_camera_still"])
        self.assertFalse(receipt["camera_model_authenticated"])
        self.assertFalse(receipt["video_original_from_camera_authenticated"])
        self.assertFalse(receipt["physical_scene_or_part_verified"])
        self.assertFalse(receipt["robot_camera_control_executed"])
        self.assertEqual(receipt["new_physical_inventory"], 0)
        self.assertEqual(receipt, replay_hero3(
            self.plan, self.phone, self.t3i, self.video,
            PROFILE, LENS, CHART, 0, receipt, png))

    def test_frame_index_changes_derived_image_but_not_source_mp4(self):
        first, a = self.capture(0)
        second, b = self.capture(5)
        self.assertNotEqual(a, b)
        self.assertNotEqual(first["record_id"], second["record_id"])
        self.assertEqual(first["original_video_lineage"]["original_h264_mp4_sha256"],
                         second["original_video_lineage"]["original_h264_mp4_sha256"])

    def test_corrupt_frame_refused(self):
        receipt, png = self.capture()
        with self.assertRaisesRegex(Hold, "HERO3_ORIGINAL_VIDEO_FRAME_COLD_REPLAY_DISAGREEMENT"):
            replay_hero3(self.plan, self.phone, self.t3i, self.video,
                         PROFILE, LENS, CHART, 0, receipt, png + b"changed")

    def test_changed_source_refused(self):
        receipt, png = self.capture()
        self.video.write_bytes(self.video.read_bytes()[:-1] + b"!")
        with self.assertRaises(Hold):
            replay_hero3(self.plan, self.phone, self.t3i, self.video,
                         PROFILE, LENS, CHART, 0, receipt, png)

    def test_fake_signatures_and_physical_inventory_refused_after_rehash(self):
        receipt, png = self.capture()
        for key, value in (
            ("camera_model_authenticated", True),
            ("video_original_from_camera_authenticated", True),
            ("physical_scene_or_part_verified", True),
            ("robot_camera_control_executed", True),
            ("new_physical_inventory", 1),
        ):
            with self.subTest(key=key):
                forged = copy.deepcopy(receipt)
                forged[key] = value
                forged["record_id"] = "static-os-robot-hero3-004:" + digest(
                    {k: v for k, v in forged.items() if k != "record_id"})
                with self.assertRaisesRegex(Hold, "HERO3_ORIGINAL_VIDEO_FRAME_COLD_REPLAY_DISAGREEMENT"):
                    replay_hero3(self.plan, self.phone, self.t3i, self.video,
                                 PROFILE, LENS, CHART, 0, forged, png)

    def test_profile_cannot_assert_black_silver_or_white_without_evidence(self):
        for field, val in (
            ("edition", "BLACK"),
            ("owner_confirmed_device", True),
            ("wifi_authorized", True),
            ("usb_camera_control_authorized", True),
            ("robot_motion_authorized", True),
        ):
            with self.subTest(field=field):
                bad = copy.deepcopy(PROFILE)
                bad[field] = val
                with self.assertRaisesRegex(Hold, "HERO3_PROVISIONAL_REFERENCE_CANNOT_GRANT_HARDWARE_AUTHORITY"):
                    self.capture(profile=bad)

    def test_corrupt_file_rejected_even_when_named_mp4(self):
        self.video.write_bytes(b"\x00" * 100)
        with self.assertRaisesRegex(Hold, "MP4_FILE_SIGNATURE_REQUIRED"):
            self.capture()

    def test_wrong_video_codec_rejected(self):
        bad = Path(self.temp.name) / "other.MP4"
        proc = subprocess.run([
            "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f",
            "lavfi", "-i", "testsrc=size=160x120:rate=5", "-frames:v", "4",
            "-c:v", "mpeg4", str(bad),
        ], capture_output=True, text=True, timeout=20)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.video = bad
        with self.assertRaisesRegex(Hold, "HERO3_ADAPTER_REQUIRES_BOUNDED_H264_VIDEO"):
            self.capture()

    def test_out_of_bounds_frame_selection_denied(self):
        for index in (-1, 1801, True):
            with self.subTest(index=index):
                with self.assertRaisesRegex(Hold, "EXPLICIT_BOUNDED_FRAME_INDEX_REQUIRED"):
                    self.capture(index)

    def test_missing_later_frame_wont_be_fake_success(self):
        with self.assertRaises(Hold):
            self.capture(100)

    def test_duplicate_camera_file_rejected(self):
        self.phone.write_bytes(self.t3i.read_bytes())
        with self.assertRaisesRegex(Hold, "SAME_IMAGE_BYTES_CANNOT_BECOME_TWO_CAMERA_WITNESSES"):
            self.capture()


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"),
                     "requires local ffmpeg")
class NativeProvenance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = os.environ.get("STATIC_OS_ROBOT001_SOURCE")
        cls.packet = os.environ.get("STATIC_OS_ROBOT001_PACKET")
        cls.request = os.environ.get("STATIC_OS_ROBOT001_REQUEST")
        if not (cls.source and cls.packet and cls.request):
            raise unittest.SkipTest("native original signed CAD/held slice/013 proposal required")

    def test_004_cli_crosses_from_native_signed_source_to_video_lineage(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            phone, t3i, movie = [work / n for n in ("phone.jpg", "t3i.jpg", "sample.MP4")]
            make_image(phone, 1)
            make_image(t3i, 4)
            p = subprocess.run([
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=160x120:rate=5",
                "-frames:v", "7", "-threads", "1", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", str(movie),
            ], capture_output=True, text=True, timeout=20)
            self.assertEqual(p.returncode, 0, p.stderr)
            target = work / "receipt"
            cmd = [sys.executable, str(ROOT / "scripts/static-robot-garden-hero3-video.py")]
            flags = [
                "--source", self.source,
                "--packet", self.packet,
                "--request", self.request,
                "--fleet", str(ROOT / "fixtures/printer-field-012/synthetic-fleet.json"),
                "--selection", str(ROOT / "fixtures/fabrication-013/three-node-selection.json"),
                "--station", str(ROOT / "fixtures/robot-garden-001/synthetic-jubilee-station.json"),
                "--phone-photo", str(phone), "--t3i-photo", str(t3i),
                "--gopro-video", str(movie),
                "--hero3-profile", str(ROOT / "fixtures/robot-garden-004/provisional-hero3-2012.json"),
                "--gopro-lens", str(ROOT / "fixtures/robot-garden-003/gopro-operator-declaration.json"),
                "--chart-spec", str(ROOT / "fixtures/robot-garden-003/nominal-checkerboard.json"),
                "--frame-index", "3", "--out-dir", str(target),
            ]
            def call(action):
                return subprocess.run(cmd + [action] + flags,
                                      capture_output=True, text=True, timeout=180)
            a = call("receive")
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertFalse(json.loads(a.stdout)["robot_movement_executed"])
            self.assertEqual(call("receive").returncode, 2)
            self.assertEqual(call("verify").returncode, 0)
            frame = target / "gopro-derived-frame-000003.png"
            frame.write_bytes(frame.read_bytes() + b"!")
            self.assertEqual(call("verify").returncode, 2)


if __name__ == "__main__":
    unittest.main()
