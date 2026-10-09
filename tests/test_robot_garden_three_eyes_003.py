"""ROBOT-GARDEN-003 — hostile three-image replay and unearned calibration refusal."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crank.runtime import digest
from question_first.robot_garden import plan_inspection
from question_first.robot_garden_three_eyes import (
    ROLE, capture_three_eyes, chart_svg, replay_three_eyes,
    validate_chart, validate_lens_claim,
)
from question_first.session import Hold
from tests.test_robot_garden_001 import REQUEST, DIMS, STATION
from tests.test_robot_garden_photos_002 import make_image

ROOT = Path(__file__).resolve().parents[1]
LENS = json.loads((ROOT / "fixtures/robot-garden-003/gopro-operator-declaration.json").read_text())
CHART = json.loads((ROOT / "fixtures/robot-garden-003/nominal-checkerboard.json").read_text())


class ThreeEyes(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.phone = self.root / "phone.jpg"
        self.t3i = self.root / "t3i.jpg"
        self.gopro = self.root / "gopro.jpg"
        make_image(self.phone, 1)
        make_image(self.t3i, 3)
        make_image(self.gopro, 5)
        self.plan = plan_inspection(REQUEST, DIMS, STATION)

    def tearDown(self):
        self.temp.cleanup()

    def capture(self, lens=LENS, chart=CHART):
        return capture_three_eyes(self.plan, self.phone, self.t3i, self.gopro,
                                  lens, chart)

    def test_three_jpegs_have_distinct_file_bytes(self):
        got = self.capture()
        self.assertEqual(got["input_count"], 3)
        self.assertEqual(len(set(
            got["parent_pair_hashes"] + [got["gopro"]["original_bytes_sha256"]])), 3)
        self.assertEqual(got["gopro"]["role"], ROLE)
        self.assertEqual(got["gopro"]["decode"]["format"], "JPEG")
        self.assertEqual(got["gopro"]["decode"]["display_width_px"], 160)
        self.assertFalse(got["gopro"]["capture_device_authenticated"])
        self.assertFalse(got["gopro"]["geometric_distortion_calibrated"])
        self.assertFalse(got["real_world_capture_authenticated"])
        self.assertFalse(got["physical_measurements_verified"])
        self.assertFalse(got["frames_temporally_synchronized"])
        self.assertFalse(got["same_part_established"])
        self.assertFalse(got["physical_part_custody_verified"])
        self.assertFalse(got["robot_movement_executed"])
        self.assertFalse(got["hardware_camera_control_executed"])
        self.assertEqual(got["new_physical_inventory"], 0)
        self.assertEqual(replay_three_eyes(
            self.plan, self.phone, self.t3i, self.gopro, LENS, CHART, got), got)

    def test_jpeg_and_png_gopro_import_both_supported(self):
        target = self.root / "gopro.png"
        make_image(target, 7, fmt="PNG")
        self.gopro = target
        self.assertEqual(self.capture()["gopro"]["decode"]["format"], "PNG")

    def test_gopro_cannot_be_a_duplicate_phone_or_t3i(self):
        self.gopro.write_bytes(self.t3i.read_bytes())
        with self.assertRaisesRegex(Hold, "GOPRO_BYTES_MUST_NOT_DUPLICATE"):
            self.capture()
        self.gopro.write_bytes(self.phone.read_bytes())
        with self.assertRaisesRegex(Hold, "GOPRO_BYTES_MUST_NOT_DUPLICATE"):
            self.capture()

    def test_swap_or_modify_input_breaks_cold_replay(self):
        prior = self.capture()
        with self.assertRaisesRegex(Hold, "THREE_EYES_COLD_ORIGINAL_REPLAY_DISAGREEMENT"):
            replay_three_eyes(
                self.plan, self.phone, self.gopro, self.t3i, LENS, CHART, prior)
        make_image(self.gopro, 6)
        with self.assertRaisesRegex(Hold, "THREE_EYES_COLD_ORIGINAL_REPLAY_DISAGREEMENT"):
            replay_three_eyes(
                self.plan, self.phone, self.t3i, self.gopro, LENS, CHART, prior)

    def test_lens_mode_changes_receipt_but_never_calibrates(self):
        baseline = self.capture()
        claimed = copy.deepcopy(LENS)
        claimed["operator_reported_model"] = "HERO UNKNOWN"
        claimed["operator_reported_digital_lens"] = "WIDE"
        view = self.capture(lens=claimed)
        self.assertNotEqual(baseline["triplet_id"], view["triplet_id"])
        self.assertEqual(view["gopro"]["operator_reported_digital_lens"], "WIDE")
        self.assertFalse(view["gopro"]["geometric_distortion_calibrated"])
        with self.assertRaisesRegex(Hold, "THREE_EYES_COLD_ORIGINAL_REPLAY_DISAGREEMENT"):
            replay_three_eyes(self.plan, self.phone, self.t3i,
                              self.gopro, claimed, CHART, baseline)

    def test_untrusted_hardware_identity_claim_fails(self):
        for name, value in [
            ("camera_identity_authenticated", True),
            ("lens_intrinsics_calibrated", True),
            ("operator_reported_digital_lens", "CERTIFIED_UNDISTORTED"),
        ]:
            with self.subTest(name=name):
                claimed = copy.deepcopy(LENS)
                claimed[name] = value
                with self.assertRaisesRegex(Hold, "UNTRUSTED_GOPRO_MODE_IS_NOT_CAMERA_AUTHORITY"):
                    self.capture(lens=claimed)

    def test_nominal_checkerboard_exact_geometry(self):
        svg = chart_svg(CHART)
        self.assertEqual(
            svg, (ROOT / "fixtures/robot-garden-003/nominal-checkerboard.svg").read_bytes())
        self.assertIn(b'width="174mm"', svg)
        self.assertIn(b'height="129mm"', svg)
        self.assertEqual(svg.count(b'<rect x='), 35)
        self.assertIn(b'9x6 inner corners', svg)
        target = self.capture()["calibration_target"]
        self.assertEqual(target["inner_corners_across"], 9)
        self.assertEqual(target["inner_corners_down"], 6)
        self.assertEqual(target["nominal_square_mm"], 15)
        self.assertIsNone(target["actual_physical_square_mm"])
        self.assertIsNone(target["lens_intrinsics"])
        self.assertIsNone(target["reprojection_error_pixels"])

    def test_cannot_claim_target_printed_or_measured(self):
        for key in ("physical_chart_printed", "physical_square_measured",
                    "camera_calibrated", "lens_distortion_corrected",
                    "physical_scale_authorized"):
            with self.subTest(key=key):
                fake = copy.deepcopy(CHART)
                fake[key] = True
                with self.assertRaisesRegex(Hold, "NOMINAL_CHART_IS_NOT_PHYSICAL_CALIBRATION"):
                    self.capture(chart=fake)

    def test_rehashed_success_forge_denied(self):
        report = self.capture()
        for name, value in (
            ("real_world_capture_authenticated", True),
            ("frames_temporally_synchronized", True),
            ("same_part_established", True),
            ("physical_measurements_verified", True),
            ("physical_part_custody_verified", True),
            ("robot_movement_executed", True),
            ("hardware_camera_control_executed", True),
            ("new_physical_inventory", 1),
        ):
            with self.subTest(name=name):
                fake = copy.deepcopy(report)
                fake[name] = value
                fake["triplet_id"] = "static-os-robot-eyes-003:" + digest(
                    {k: v for k, v in fake.items() if k != "triplet_id"})
                with self.assertRaisesRegex(Hold, "THREE_EYES_COLD_ORIGINAL_REPLAY_DISAGREEMENT"):
                    replay_three_eyes(self.plan, self.phone, self.t3i,
                                      self.gopro, LENS, CHART, fake)

    def test_extra_chart_or_lens_field_denied(self):
        lens = copy.deepcopy(LENS)
        lens["gopro_remote_on"] = True
        with self.assertRaisesRegex(Hold, "GOPRO_LENS_DECLARATION_EXACT_FIELDS_REQUIRED"):
            self.capture(lens=lens)
        chart = copy.deepcopy(CHART)
        chart["authorized_for_robot_movement"] = True
        with self.assertRaisesRegex(Hold, "CHART_EXACT_FIELDS_REQUIRED"):
            self.capture(chart=chart)

    def test_replayed_parent_plan_is_required(self):
        mutated = copy.deepcopy(self.plan)
        mutated["camera_connected"] = True
        with self.assertRaisesRegex(Hold, "PLAN_NOT_A_SAFE_SIMULATION"):
            capture_three_eyes(mutated, self.phone, self.t3i, self.gopro, LENS, CHART)


class NativeThreeEyes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = os.environ.get("STATIC_OS_ROBOT001_SOURCE")
        cls.packet = os.environ.get("STATIC_OS_ROBOT001_PACKET")
        cls.request = os.environ.get("STATIC_OS_ROBOT001_REQUEST")
        if not all((cls.source, cls.packet, cls.request)):
            raise unittest.SkipTest("signed original CAD, real slice and 013 required")

    def test_native_cold_signed_source_three_eye_cli(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            phone, t3i, go = [root / (name + ".jpg") for name in ("phone", "t3i", "gopro")]
            for f, seed in ((phone, 1), (t3i, 4), (go, 6)):
                make_image(f, seed)
            output = root / "triple"
            command = [sys.executable, str(ROOT / "scripts/static-robot-garden-three-eyes.py")]
            flags = [
                "--source", self.source,
                "--packet", self.packet,
                "--request", self.request,
                "--fleet", str(ROOT / "fixtures/printer-field-012/synthetic-fleet.json"),
                "--selection", str(ROOT / "fixtures/fabrication-013/three-node-selection.json"),
                "--station", str(ROOT / "fixtures/robot-garden-001/synthetic-jubilee-station.json"),
                "--phone-photo", str(phone),
                "--t3i-photo", str(t3i),
                "--gopro-photo", str(go),
                "--gopro-lens", str(ROOT / "fixtures/robot-garden-003/gopro-operator-declaration.json"),
                "--chart-spec", str(ROOT / "fixtures/robot-garden-003/nominal-checkerboard.json"),
                "--out-dir", str(output),
            ]
            def cmd(action):
                return subprocess.run(command + [action] + flags, capture_output=True, text=True)
            first = cmd("receive")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(json.loads(first.stdout)["image_file_count"], 3)
            self.assertEqual(cmd("receive").returncode, 2)
            self.assertEqual(cmd("verify").returncode, 0)
            chart = output / "nominal-checkerboard.svg"
            chart.write_bytes(chart.read_bytes() + b" ")
            self.assertEqual(cmd("verify").returncode, 2)


if __name__ == "__main__":
    unittest.main()
