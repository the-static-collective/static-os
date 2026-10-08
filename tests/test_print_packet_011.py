"""PRINT-011 actual slicer tests against real native signed CAD package."""
from __future__ import annotations
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from question_first.session import Hold
from question_first.print_packet import prepare_print,verify_print,preflight,PROFILE

class Print011(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=os.environ.get("STATIC_OS_PRINT011_CAD")
        if not src:raise unittest.SkipTest("native signed CAD package from workflow required")
        cls.solid=Path(src).resolve()
        cls.tmp=tempfile.TemporaryDirectory(prefix="static-print011-")
        cls.folder=Path(cls.tmp.name)
        cls.packet=prepare_print(cls.solid,cls.folder/"packet")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_real_slicer_export_is_nonempty_and_is_never_an_execution(self):
        root=self.folder/"packet"
        self.assertGreater((root/"toolpath.gcode").stat().st_size,200)
        self.assertEqual(self.packet,verify_print(self.solid,root))
        report=json.loads((root/"preflight.json").read_text())
        self.assertGreaterEqual(report["extrusion_candidate_moves"],10)
        self.assertFalse(report["actual_printer_execution"])
        self.assertFalse(self.packet["physical_output_created"])
        self.assertFalse(self.packet["printer_connected"])
        self.assertFalse(self.packet["transmission_enabled"])

    def test_same_occurrence_never_slices_twice_automatically(self):
        with self.assertRaisesRegex(Hold,"NO_AUTORETRY"):
            prepare_print(self.solid,self.folder/"packet")

    def test_malicious_thermal_override_refused(self):
        fake=self.folder/"too-hot.gcode"
        original=(self.folder/"packet/toolpath.gcode").read_text()
        fake.write_text("M104 S280\n"+original)
        with self.assertRaisesRegex(Hold,"TEMPERATURE_EXCEEDED"):
            preflight(fake)

    def test_arbitrary_firmware_action_refused(self):
        fake=self.folder/"bad-firmware.gcode"
        fake.write_text("M500\n"+(self.folder/"packet/toolpath.gcode").read_text())
        with self.assertRaisesRegex(Hold,"UNSAFE_GCODE_OPCODE"):
            preflight(fake)

    def test_relative_motion_and_coordinate_reset_cannot_escape_bounds(self):
        for cmd,needle in (("G91","UNSAFE_GCODE_OPCODE"),
                           ("G92 X0","NO_XYZ_COORDINATE_RESET"),
                           ("G1 X181 Y5 F1000","VIRTUAL_BED_BOUND_EXCEEDED"),
                           ("G1 Z181 F1000","VIRTUAL_BED_BOUND_EXCEEDED"),
                           ("G1 F90000","FEEDRATE")):
            f=self.folder/("attack-"+cmd.replace(" ","-")+".gcode")
            f.write_text(cmd+"\n"+(self.folder/"packet/toolpath.gcode").read_text())
            with self.assertRaisesRegex(Hold,needle):
                preflight(f)

    def test_changed_gcode_and_profile_cannot_pass_cold_review(self):
        root=self.folder/"packet"
        with tempfile.TemporaryDirectory() as tmp:
            copied=Path(tmp)/"packet"
            shutil.copytree(root,copied)
            with (copied/"toolpath.gcode").open("a") as stream:
                stream.write("\nM104 S300\n")
            with self.assertRaisesRegex(Hold,"TOOLPATH_BYTES_CHANGED"):
                verify_print(self.solid,copied)
        with tempfile.TemporaryDirectory() as tmp:
            copied=Path(tmp)/"packet"
            shutil.copytree(root,copied)
            with (copied/"profile.ini").open("a") as stream:
                stream.write("\nstart_gcode = M500\n")
            with self.assertRaisesRegex(Hold,"UNTRUSTED_PHYSICAL_PRINTER_PROFILE"):
                verify_print(self.solid,copied)

    def test_rehashing_fabrication_claim_does_not_establish_execution(self):
        from crank.runtime import digest
        root=self.folder/"packet"
        with tempfile.TemporaryDirectory() as tmp:
            copied=Path(tmp)/"packet"
            shutil.copytree(root,copied)
            p=copied/"packet.json"
            packet=json.loads(p.read_text())
            packet["physical_output_created"]=True
            body={k:v for k,v in packet.items() if k!="packet_id"}
            packet["packet_id"]="static-os-print-011:"+digest(body)
            p.write_text(json.dumps(packet))
            with self.assertRaisesRegex(Hold,"MANUFACTURES_AUTHORITY"):
                verify_print(self.solid,copied)

    def test_cold_verify_never_changes_existing_bytes_or_opens_machine(self):
        root=self.folder/"packet"
        before={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
        verify_print(self.solid,root)
        after={p.name:p.read_bytes() for p in root.iterdir() if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual(self.packet["profile_kind"],"VIRTUAL_FFF_PLA_180_NO_PHYSICAL_PRINTER")

if __name__=="__main__":
    unittest.main()
