"""ROBOT-GARDEN-002 — actual image decodes with deliberately untrusted camera roles."""
from __future__ import annotations

import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from crank.runtime import digest
from question_first.robot_garden import plan_inspection
from question_first.robot_garden_photos import (
    _image_metrics, inspect_original, verify_original,
)
from question_first.session import Hold
from tests.test_robot_garden_001 import REQUEST, DIMS, STATION

ROOT = Path(__file__).resolve().parents[1]


def make_image(path: Path, seed: int, *, fmt="JPEG", dims=(160, 120)):
    img = Image.new("RGB", dims, (45 + seed * 10, 70, 115))
    canvas = ImageDraw.Draw(img)
    canvas.rectangle((20, 20, 95, 88), fill=(170, 120 + seed, 80))
    canvas.line((20 + seed, 25, 110, 90), fill="white", width=4)
    exif = Image.Exif()
    exif[0x0110] = "OPERATOR-REPORTED-DEVICE-NOT_ATTESTED"
    img.save(path, format=fmt, exif=exif if fmt == "JPEG" else None)


class PurePhotos(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.TemporaryDirectory()
        root = Path(self.work.name)
        self.phone = root / "phone.jpg"
        self.t3i = root / "t3i.jpg"
        make_image(self.phone, 1)
        make_image(self.t3i, 4)
        self.plan = plan_inspection(REQUEST, DIMS, STATION)

    def tearDown(self):
        self.work.cleanup()

    def test_both_real_jpeg_decoders_produce_file_grounded_metrics(self):
        x = inspect_original(self.plan, self.phone, self.t3i)
        self.assertEqual(x["input_count"], 2)
        self.assertEqual(x["state"], "REAL_FILES_DECODED_SOURCE_ROLES_UNVERIFIED")
        self.assertNotEqual(x["records"][0]["original_bytes_sha256"],
                            x["records"][1]["original_bytes_sha256"])
        for image in x["records"]:
            self.assertEqual(image["decode"]["format"], "JPEG")
            self.assertEqual(image["decode"]["encoded_width_px"], 160)
            self.assertGreater(image["decode"]["sample_mean_luminance_0_255"], 0)
            self.assertGreater(image["decode"]["sample_edge_delta_0_255"], 0)
            self.assertFalse(image["camera_identity_verified"])
            self.assertFalse(image["capture_time_authenticated"])
            self.assertFalse(image["independent_real_world_witness"])
        self.assertFalse(x["physical_part_verified"])
        self.assertFalse(x["signed_sensor_evidence"])
        self.assertFalse(x["material_custody_verified"])
        self.assertFalse(x["robot_or_camera_command_sent"])
        self.assertEqual(x["new_physical_inventory"], 0)
        self.assertEqual(verify_original(self.plan, self.phone, self.t3i, x), x)
        self.assertNotIn("OPERATOR-REPORTED-DEVICE", json.dumps(x))

    def test_png_and_jpeg_can_coexist(self):
        png = Path(self.work.name) / "phone.png"
        make_image(png, 2, fmt="PNG")
        report = inspect_original(self.plan, png, self.t3i)
        self.assertEqual([r["decode"]["format"] for r in report["records"]],
                         ["PNG", "JPEG"])

    def test_same_photo_cannot_be_dual_source(self):
        with self.assertRaisesRegex(Hold, "SAME_IMAGE_BYTES"):
            inspect_original(self.plan, self.phone, self.phone)

    def test_swapping_or_modifying_images_breaks_cold_replay(self):
        report = inspect_original(self.plan, self.phone, self.t3i)
        with self.assertRaisesRegex(Hold, "REAL_PHOTO_PAIR_COLD_REPLAY_DISAGREEMENT"):
            verify_original(self.plan, self.t3i, self.phone, report)
        make_image(self.t3i, 6)
        with self.assertRaisesRegex(Hold, "REAL_PHOTO_PAIR_COLD_REPLAY_DISAGREEMENT"):
            verify_original(self.plan, self.phone, self.t3i, report)

    def test_physical_certification_forge_denied_even_with_new_hash(self):
        report = inspect_original(self.plan, self.phone, self.t3i)
        for field, val in [
            ("physical_part_verified", True), ("signed_sensor_evidence", True),
            ("robot_or_camera_command_sent", True),
            ("material_custody_verified", True), ("new_physical_inventory", 1)]:
            with self.subTest(field=field):
                forged = copy.deepcopy(report)
                forged[field] = val
                forged["pair_id"] = "static-os-robot-photos-002:" + digest(
                    {k: v for k, v in forged.items() if k != "pair_id"})
                with self.assertRaisesRegex(Hold, "REAL_PHOTO_PAIR_COLD_REPLAY_DISAGREEMENT"):
                    verify_original(self.plan, self.phone, self.t3i, forged)

    def test_untrusted_device_identity_cannot_be_rewritten(self):
        report = inspect_original(self.plan, self.phone, self.t3i)
        report["records"][0]["camera_identity_verified"] = True
        with self.assertRaisesRegex(Hold, "REAL_PHOTO_PAIR_COLD_REPLAY_DISAGREEMENT"):
            verify_original(self.plan, self.phone, self.t3i, report)

    def test_corrupt_header_and_truncated_image_denied(self):
        self.phone.write_bytes(b"not actually jpeg data")
        with self.assertRaisesRegex(Hold, "ONLY_JPEG_OR_PNG_ACCEPTED"):
            inspect_original(self.plan, self.phone, self.t3i)
        make_image(self.phone, 1)
        self.phone.write_bytes(self.phone.read_bytes()[:25])
        with self.assertRaisesRegex(Hold, "ORIGINAL_IMAGE_FAILED_STRICT_DECODE"):
            inspect_original(self.plan, self.phone, self.t3i)

    def test_size_and_resolution_limit(self):
        tiny = Path(self.work.name) / "tiny.png"
        make_image(tiny, 2, fmt="PNG", dims=(32, 32))
        with self.assertRaisesRegex(Hold, "DECODED_IMAGE_DIMENSIONS_OUT_OF_BOUNDS"):
            inspect_original(self.plan, tiny, self.t3i)
        self.phone.write_bytes(b"x" * (40 * 1024 * 1024 + 1))
        with self.assertRaisesRegex(Hold, "ORIGINAL_IMAGE_SIZE_LIMIT"):
            inspect_original(self.plan, self.phone, self.t3i)

    def test_file_origin_is_not_an_automatic_camera_connection(self):
        report = inspect_original(self.plan, self.phone, self.t3i)
        self.assertFalse(report["comparison"]["independent_capture_devices_authenticated"])
        self.assertFalse(report["comparison"]["physical_object_identity_established"])
        self.assertFalse(report["comparison"]["calibrated_part_dimensions_present"])
        self.assertFalse(report["comparison"]["geometry_calibration_present"])


class NativePhotos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = os.environ.get("STATIC_OS_ROBOT001_SOURCE")
        cls.packet = os.environ.get("STATIC_OS_ROBOT001_PACKET")
        cls.request = os.environ.get("STATIC_OS_ROBOT001_REQUEST")
        if not all((cls.source, cls.packet, cls.request)):
            raise unittest.SkipTest("original native signed CAD and 013 proposal required")

    def test_real_decoded_images_against_original_signed_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phone = root / "phone.jpg"
            t3i = root / "t3i.jpg"
            out = root / "paired-dossier.json"
            make_image(phone, 1)
            make_image(t3i, 3)
            cli = [sys.executable, str(ROOT / "scripts/static-robot-garden-photos.py")]
            args = [
                "--source", self.source,
                "--packet", self.packet,
                "--fleet", str(ROOT / "fixtures/printer-field-012/synthetic-fleet.json"),
                "--selection", str(ROOT / "fixtures/fabrication-013/three-node-selection.json"),
                "--request", self.request,
                "--station", str(ROOT / "fixtures/robot-garden-001/synthetic-jubilee-station.json"),
                "--phone-photo", str(phone),
                "--t3i-photo", str(t3i),
                "--out", str(out),
            ]
            def cmd(action):
                return subprocess.run(cli + [action] + args,
                                      capture_output=True, text=True)
            a = cmd("receive")
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(cmd("receive").returncode, 2)
            self.assertEqual(cmd("verify").returncode, 0)
            receipt = json.loads(out.read_text())
            self.assertEqual(receipt["input_count"], 2)
            self.assertFalse(receipt["physical_part_verified"])
            receipt["records"][1]["camera_identity_verified"] = True
            out.write_text(json.dumps(receipt))
            self.assertEqual(cmd("verify").returncode, 2)


if __name__ == "__main__":
    unittest.main()
