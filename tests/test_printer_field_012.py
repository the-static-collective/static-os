"""PRINT-FIELD-012: actual 011 signed-source integration and adversarial fleet routing."""
from __future__ import annotations
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from question_first.session import Hold
from question_first.printer_field import (
    REGISTRY, REQUIRED_FAMILIES, VIRTUAL_ID, _load_registry,
    verify_declaration, compile_field, verify_field,
)

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=json.loads((ROOT/"fixtures/printer-field-012/synthetic-fleet.json").read_text())
VIRTUAL=FIXTURE["machines"][0]


class PurePrinterFieldTests(unittest.TestCase):
    def test_open_world_registry_identifies_families_without_promising_actual_support(self):
        registry, records=_load_registry()
        self.assertEqual(set(records),set(REQUIRED_FAMILIES))
        self.assertEqual(registry["supported_printer_count_claim"],0)
        self.assertFalse(registry["machine_execution_enabled"])
        self.assertEqual(records["FFF_FDM"]["reference_adapter"],"VIRTUAL_PRUSASLICER_011")
        self.assertTrue(all(not v["physical_execution_verified"] for v in records.values()))
        self.assertTrue(all(v["reference_adapter"] is None
                            for k,v in records.items() if k!="FFF_FDM"))

    def test_untrusted_owner_declaration_is_just_data(self):
        self.assertEqual(verify_declaration(VIRTUAL)["claim_kind"],"OWNER_DECLARED_UNVERIFIED")
        for key in ("transport_allowed","hardware_execution_allowed"):
            x=copy.deepcopy(VIRTUAL);x[key]=True
            with self.assertRaisesRegex(Hold,"CONTROL_AUTHORITY"):
                verify_declaration(x)

    def test_forged_printer_specs_and_numeric_edge_cases_fail(self):
        for mutate in (
            lambda x:x["build_volume_mm"].update({"x":float("nan")}),
            lambda x:x["build_volume_mm"].update({"z":0}),
            lambda x:x["build_volume_mm"].update({"y":99999}),
            lambda x:x.update({"profile_ref":"../../etc/passwd"}),
            lambda x:x.update({"technology":"FFF_FDM; DROP TABLE"}),
            lambda x:x.update({"material_classes":["PLA","PLA"]}),
            lambda x:x.update({"material_classes":["PLUTONIUM"]}),
            lambda x:x.update({"manufacturer":"\nexec code"}),
            lambda x:x.update({"untrusted_grant":"PRINT_NOW"}),
        ):
            x=copy.deepcopy(VIRTUAL);mutate(x)
            with self.assertRaises(Hold):
                verify_declaration(x)

    def test_unknown_vendor_is_accepted_as_declaration_not_trusted_authority(self):
        x=copy.deepcopy(VIRTUAL)
        x.update({"machine_id":"owner:some-brand-model-123",
                  "manufacturer":"Arbitrary Manufacturer",
                  "model":"The Owner Calls It V6",
                  "technology":"FFF_FDM","profile_ref":None})
        self.assertEqual(verify_declaration(x)["machine_id"],x["machine_id"])

    def test_catalog_command_is_read_only_and_no_file_arguments(self):
        result=subprocess.run([sys.executable,str(ROOT/"scripts/static-printer-field.py"),
            "catalog"],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertEqual(json.loads(result.stdout)["physically_validated_printers"],0)
        self.assertEqual(len(json.loads(result.stdout)["recognized_families"]),10)


class NativePrinterFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=os.environ.get("STATIC_OS_PRINT012_SOURCE")
        packet=os.environ.get("STATIC_OS_PRINT012_PACKET")
        if not src or not packet:
            raise unittest.SkipTest("requires actual signed CAD and real PrusaSlicer job")
        cls.source=Path(src).resolve()
        cls.packet=Path(packet).resolve()
        if not cls.source.is_dir() or not cls.packet.is_dir():
            raise RuntimeError("CI did not provide original native donor files")

    def test_one_valid_native_source_routes_all_eleven_process_examples(self):
        field=compile_field(self.source,self.packet,FIXTURE)
        self.assertEqual(field,verify_field(self.source,self.packet,FIXTURE,field))
        self.assertEqual(field["machine_count"],12)
        self.assertEqual(field["recognized_process_families"],10)
        self.assertEqual(field["status"],"DISCOVERY_AND_PROPOSALS_ONLY")
        self.assertFalse(field["physical_printer_connected"])
        self.assertFalse(field["transport_executed"])
        self.assertEqual(field["manufactured_parts"],0)
        self.assertFalse(field["treasury_inventory_increased"])
        classes={m["machine_id"]:m["compatibility_status"] for m in field["machines"]}
        self.assertEqual(classes[VIRTUAL_ID],"SOFTWARE_TOOLPATH_ONLY")
        self.assertEqual(classes["example:machine-01"],"HOLD_MACHINE_PROFILE")
        for i in range(2,11):
            self.assertEqual(classes[f"example:machine-{i:02d}"],"HOLD_PROCESS_ADAPTER")
        self.assertEqual(classes["example:machine-11"],"HOLD_UNKNOWN_PROCESS")
        self.assertEqual(field["machines"][0]["reference_gcode_sha256"],
                         json.loads((self.packet/"packet.json").read_text())["gcode_sha256"])
        self.assertTrue(all(m["reference_gcode_sha256"] is None for m in field["machines"][1:]))
        self.assertTrue(all(not m["physical_execution_authorized"]
                            and not m["machine_connected"]
                            and not m["physical_output_created"] for m in field["machines"]))

    def test_small_bed_is_declared_envelope_blocker_not_a_print_attempt(self):
        fleet=copy.deepcopy(FIXTURE)
        fleet["machines"][1]["build_volume_mm"]={"x":2,"y":2,"z":2}
        field=compile_field(self.source,self.packet,fleet)
        self.assertEqual(field["machines"][1]["compatibility_status"],
                         "HOLD_DECLARED_ENVELOPE")
        self.assertTrue(field["machines"][1]["original_orientation_assumed"])

    def test_adversarial_replacement_of_frozen_virtual_profile_denied(self):
        fleet=copy.deepcopy(FIXTURE)
        fleet["machines"][0]["profile_ref"]="some-other-profile"
        with self.assertRaisesRegex(Hold,"RESERVED"):
            compile_field(self.source,self.packet,fleet)

    def test_duplicate_machine_ids_refused(self):
        fleet=copy.deepcopy(FIXTURE)
        fleet["machines"][1]["machine_id"]=VIRTUAL_ID
        with self.assertRaisesRegex(Hold,"DUPLICATE"):
            compile_field(self.source,self.packet,fleet)

    def test_forged_machine_authority_flag_is_refused(self):
        for key in ("hardware_execution_allowed","transport_allowed"):
            fleet=copy.deepcopy(FIXTURE)
            fleet["machines"][1][key]=True
            with self.assertRaisesRegex(Hold,"CONTROL_AUTHORITY"):
                compile_field(self.source,self.packet,fleet)

    def test_data_is_immutable_by_compilation_and_replay(self):
        before=json.dumps(FIXTURE,sort_keys=True)
        source_before=(self.source/"solid.stl").read_bytes()
        tool_before=(self.packet/"toolpath.gcode").read_bytes()
        first=compile_field(self.source,self.packet,FIXTURE)
        second=compile_field(self.source,self.packet,FIXTURE)
        self.assertEqual(first["field_id"],second["field_id"])
        self.assertEqual(before,json.dumps(FIXTURE,sort_keys=True))
        self.assertEqual(source_before,(self.source/"solid.stl").read_bytes())
        self.assertEqual(tool_before,(self.packet/"toolpath.gcode").read_bytes())

    def test_forging_a_read_only_report_never_passes_cold_verifier(self):
        result=compile_field(self.source,self.packet,FIXTURE)
        for case in (
            lambda x:x["machines"][1].update({"physical_execution_authorized":True}),
            lambda x:x["machines"][1].update({"compatibility_status":"PRINT_NOW"}),
            lambda x:x.update({"manufactured_parts":100}),
            lambda x:x.update({"technology_registry_sha256":"0"*64}),
        ):
            fake=copy.deepcopy(result)
            case(fake)
            from crank.runtime import digest
            body={k:v for k,v in fake.items() if k!="field_id"}
            fake["field_id"]="static-os-printer-field-012:"+digest(body)
            with self.assertRaisesRegex(Hold,"FIELD_COLD_REPLAY_DISAGREEMENT"):
                verify_field(self.source,self.packet,FIXTURE,fake)

    def test_original_toolpath_tamper_denies_all_target_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"held"
            shutil.copytree(self.packet,root)
            with (root/"toolpath.gcode").open("a") as f:f.write("\nM500\n")
            with self.assertRaisesRegex(Hold,"PRINT_TOOLPATH_BYTES_CHANGED"):
                compile_field(self.source,root,FIXTURE)

    def test_source_model_tamper_denies_all_target_families(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"source"
            shutil.copytree(self.source,root)
            with (root/"solid.step").open("ab") as f:f.write(b"tampered")
            with self.assertRaises(Hold):
                compile_field(root,self.packet,FIXTURE)

    def test_command_writes_only_new_proposal_and_verifies_cold(self):
        with tempfile.TemporaryDirectory() as tmp:
            result=Path(tmp)/"field.json"
            script=str(ROOT/"scripts/static-printer-field.py")
            fleet=str(ROOT/"fixtures/printer-field-012/synthetic-fleet.json")
            cmd=[sys.executable,script,"discover","--source",str(self.source),
                 "--print-packet",str(self.packet),"--fleet",fleet,"--out",str(result)]
            first=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(first.returncode,0,first.stderr)
            self.assertEqual(json.loads(first.stdout)["prints_started"],0)
            second=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(second.returncode,2)
            self.assertIn("FIELD_OUTPUT_OCCUPIED_NO_AUTORETRY",second.stderr)
            cmd[2]="verify"
            third=subprocess.run(cmd,capture_output=True,text=True)
            self.assertEqual(third.returncode,0,third.stderr)
            self.assertEqual(json.loads(result.read_text())["machine_count"],12)


if __name__=="__main__":
    unittest.main()
