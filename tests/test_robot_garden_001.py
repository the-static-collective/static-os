"""ROBOT-GARDEN-001: hostile boundaries and image-derived simulated inspection."""
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
from question_first.robot_garden import (
    inspect_frame, plan_inspection, synthetic_pgm, verify_simulation,
)
from question_first.session import Hold

ROOT = Path(__file__).resolve().parents[1]
STATION = json.loads(
    (ROOT / "fixtures/robot-garden-001/synthetic-jubilee-station.json").read_text())
REQUEST = {
    "schema": "static-os.fabrication-request/v0",
    "state": "FABRICATION_PROPOSAL_ONLY",
    "fabrication_occurred": False,
    "owner_machine_grants_included": False,
    "physical_parts": 0,
    "new_money": 0,
    "requested_node_count": 3,
    "request_id": "static-os-fabrication-013:fixture-parent",
    "original_signed_cad_crossing_id": "signed-cad-fixture-not-real",
    "original_print_packet_id": "packet-fixture-not-real",
    "source_design_candidate_id": "design-fixture-not-real",
    "selected_nodes": [
        {"machine_id": "example:machine-01",
         "published_compatibility": "HOLD_MACHINE_PROFILE",
         "hardware_authenticated": False, "physical_print_permission": False},
        {"machine_id": "example:machine-02",
         "published_compatibility": "HOLD_PROCESS_ADAPTER",
         "hardware_authenticated": False, "physical_print_permission": False},
        {"machine_id": "virtual:fff-pla-180",
         "published_compatibility": "SOFTWARE_TOOLPATH_ONLY",
         "hardware_authenticated": False, "physical_print_permission": False},
    ],
}
DIMS = {"x": 35.2, "y": 25.4, "z": 7.0}


class PureCamera(unittest.TestCase):
    def plan(self):
        return plan_inspection(REQUEST, DIMS, STATION)

    def test_dimensions_measured_from_pixels_not_from_claim(self):
        plan = self.plan()
        report = inspect_frame(plan, synthetic_pgm(plan))
        self.assertEqual(report["classification"], "SIMULATED_GEOMETRY_MATCH")
        self.assertLess(abs(report["delta_xy_mm"]["x"]), 0.6)
        self.assertLess(abs(report["delta_xy_mm"]["y"]), 0.6)
        self.assertFalse(report["is_physical_observation"])
        self.assertFalse(report["material_witness_accepted"])
        self.assertFalse(report["printer_or_robot_activated"])
        self.assertEqual(report["new_physical_inventory"], 0)

    def test_wrong_part_fails_measured_width(self):
        plan = self.plan()
        frame = synthetic_pgm(plan, width_factor=0.75)
        report = inspect_frame(plan, frame)
        self.assertEqual(report["classification"], "SIMULATED_GEOMETRY_MISMATCH")
        self.assertLess(report["delta_xy_mm"]["x"], -2.0)
        self.assertEqual(report, verify_simulation(plan, frame, report))

    def test_changed_frame_cannot_keep_report(self):
        plan = self.plan()
        report = inspect_frame(plan, synthetic_pgm(plan))
        changed = synthetic_pgm(plan, width_factor=0.8)
        with self.assertRaisesRegex(Hold, "COLD_INSPECTION_REPLAY_DISAGREEMENT"):
            verify_simulation(plan, changed, report)

    def test_claimed_success_mutation_is_denied(self):
        plan = self.plan()
        frame = synthetic_pgm(plan, width_factor=0.8)
        report = inspect_frame(plan, frame)
        forged = copy.deepcopy(report)
        forged["classification"] = "SIMULATED_GEOMETRY_MATCH"
        forged["report_id"] = "static-os-robot-report-001:" + digest(
            {k: v for k, v in forged.items() if k != "report_id"})
        with self.assertRaisesRegex(Hold, "COLD_INSPECTION_REPLAY_DISAGREEMENT"):
            verify_simulation(plan, frame, forged)

    def test_sensor_evidence_or_custody_laundering_denied(self):
        plan = self.plan()
        frame = synthetic_pgm(plan)
        report = inspect_frame(plan, frame)
        for key, value in [
            ("is_physical_observation", True), ("is_signed_sensor_evidence", True),
            ("part_custody_verified", True), ("material_witness_accepted", True),
            ("printer_or_robot_activated", True), ("new_physical_inventory", 1)]:
            with self.subTest(key=key):
                forged = copy.deepcopy(report)
                forged[key] = value
                forged["report_id"] = "static-os-robot-report-001:" + digest(
                    {k: v for k, v in forged.items() if k != "report_id"})
                with self.assertRaisesRegex(Hold, "COLD_INSPECTION_REPLAY_DISAGREEMENT"):
                    verify_simulation(plan, frame, forged)

    def test_camera_or_motion_grant_on_station_denied(self):
        for key in ("hardware_present", "camera_connected", "movement_authorized",
                    "toolchange_authorized", "transport_authorized",
                    "physical_inspection_authorized"):
            with self.subTest(key=key):
                station = copy.deepcopy(STATION)
                station[key] = True
                with self.assertRaisesRegex(Hold, "SIMULATOR_MUST_NOT_IMPLY_HARDWARE_AUTHORITY"):
                    plan_inspection(REQUEST, DIMS, station)

    def test_parent_authority_laundering_denied(self):
        for key, value in [("fabrication_occurred", True),
                           ("owner_machine_grants_included", True),
                           ("physical_parts", 1), ("new_money", 10)]:
            with self.subTest(key=key):
                bad = copy.deepcopy(REQUEST)
                bad[key] = value
                with self.assertRaises(Hold):
                    plan_inspection(bad, DIMS, STATION)
        bad = copy.deepcopy(REQUEST)
        bad["selected_nodes"][-1]["physical_print_permission"] = True
        with self.assertRaisesRegex(Hold, "NO_SOURCE_MACHINE_PERMISSIONS"):
            plan_inspection(bad, DIMS, STATION)

    def test_pixel_corruption_is_not_allowed_to_pass(self):
        plan = self.plan()
        image = bytearray(synthetic_pgm(plan))
        image[-10] = 17
        with self.assertRaisesRegex(Hold, "SYNTHETIC_BINARY_PIXELS_ONLY"):
            inspect_frame(plan, bytes(image))

    def test_plan_forged_physical_auth_cannot_be_rehashed(self):
        plan = self.plan()
        forged = copy.deepcopy(plan)
        forged["physical_execution_authorized"] = True
        forged["plan_id"] = "static-os-robot-garden-001:" + digest(
            {k: v for k, v in forged.items() if k != "plan_id"})
        with self.assertRaisesRegex(Hold, "PLAN_NOT_A_SAFE_SIMULATION"):
            inspect_frame(forged, synthetic_pgm(plan))

    def test_extra_station_fields_rejected(self):
        station = copy.deepcopy(STATION)
        station["servo_endpoint"] = "localhost"
        with self.assertRaisesRegex(Hold, "STATION_EXACT_FIELDS_REQUIRED"):
            plan_inspection(REQUEST, DIMS, station)

    def test_invalid_geometry_and_camera_scale_denied(self):
        for geometry in ({"x": -1, "y": 20, "z": 5},
                         {"x": 1000, "y": 20, "z": 5},
                         {"x": True, "y": 20, "z": 5}):
            with self.assertRaises(Hold):
                plan_inspection(REQUEST, geometry, STATION)
        s = copy.deepcopy(STATION)
        s["camera_pixels_per_mm"] = 0
        with self.assertRaisesRegex(Hold, "INVALID_SYNTHETIC_CAMERA_SCALE"):
            plan_inspection(REQUEST, DIMS, s)

    def test_frame_incomplete_denied(self):
        plan = self.plan()
        with self.assertRaisesRegex(Hold, "PGM_SIZE_MISMATCH"):
            inspect_frame(plan, synthetic_pgm(plan)[:-10])


class NativeIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = os.environ.get("STATIC_OS_ROBOT001_SOURCE")
        cls.packet = os.environ.get("STATIC_OS_ROBOT001_PACKET")
        cls.request = os.environ.get("STATIC_OS_ROBOT001_REQUEST")
        if not all((cls.source, cls.packet, cls.request)):
            raise unittest.SkipTest("native signed CAD, real slicer and 013 proposal required")

    def test_cold_source_gate_cli_run_and_verify(self):
        cli = [sys.executable, str(ROOT / "scripts/static-robot-garden.py")]
        args = [
            "--source", self.source,
            "--packet", self.packet,
            "--request", self.request,
            "--fleet", str(ROOT / "fixtures/printer-field-012/synthetic-fleet.json"),
            "--selection", str(ROOT / "fixtures/fabrication-013/three-node-selection.json"),
            "--station", str(ROOT / "fixtures/robot-garden-001/synthetic-jubilee-station.json"),
        ]
        with tempfile.TemporaryDirectory() as t:
            out = Path(t) / "inspection-001"
            call = lambda command, extra=[]: subprocess.run(
                cli + [command] + args + ["--out-dir", str(out)] + extra,
                capture_output=True, text=True)
            success = call("run")
            self.assertEqual(success.returncode, 0, success.stderr)
            self.assertEqual(json.loads(success.stdout)["robot_actuated"], False)
            self.assertEqual(call("run").returncode, 2)
            verified = call("verify")
            self.assertEqual(verified.returncode, 0, verified.stderr)
            corrupted = json.loads((out / "report.json").read_text())
            corrupted["new_physical_inventory"] = 1
            (out / "report.json").write_text(json.dumps(corrupted))
            self.assertEqual(call("verify").returncode, 2)


if __name__ == "__main__":
    unittest.main()
