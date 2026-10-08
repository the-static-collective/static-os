"""STATIC-CAD-005 hostile proof: real OCCT and signed reLATTE RECEIVE/HOLD.

Dedicated CI supplies external pinned GHoT and reLATTE. It does not need
a printer, FreeCAD, machine shop, or any human/physical authority.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from question_first.session import Hold,discover_ghot
from question_first.apparatus_compiler import compile_apparatus
from question_first.static_cad import compile_project,SEED as CAD_SEED
from question_first.sketch_solver import compile_sketch
from question_first.solid_body import build_solid,verify_files,validate_trace
from question_first.solid_relatte import cross,verify_native

ROOT=Path(__file__).resolve().parents[1]
AP=json.loads((ROOT/"fixtures/apparatus-002/source-grounded-question.json").read_text())
PARAMS=json.loads((ROOT/"fixtures/static-cad-003/reference-parameters.json").read_text())
SKETCH=json.loads((ROOT/"fixtures/static-cad-004/rounded-mount-sketch.json").read_text())
MANIFEST=ROOT/"integrations/apparatus-002/adapter-manifest.json"


class Solid005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "GHOT_SRC" not in os.environ:
            raise unittest.SkipTest("GHOT_SRC required by dedicated CI")
        cls.root_tmp=tempfile.TemporaryDirectory(prefix="static-solid-005-")
        cls.root=Path(cls.root_tmp.name)
        cls.old={k:os.environ.get(k) for k in
                 ("GHOT_HOME","GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"]=str(cls.root/"ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"]=str(MANIFEST)
        app=compile_apparatus(AP,discover_ghot(Path(os.environ["GHOT_SRC"])))
        cad=compile_project({
            "schema":CAD_SEED,"apparatus_plan_id":app["plan_id"],
            "selected_candidate_id":"gear-then-screw",
            "parameters":PARAMS,"revision_parent_id":None,
        },app)
        seed={**SKETCH,"cad_parent_id":cad["project_id"]}
        cls.sketch=compile_sketch(seed,cad)
        assert cls.sketch["constraint_report"]["state"]=="SOLVED"
        cls.folder=cls.root/"cad-solid"
        cls.manifest=build_solid(cls.sketch,cls.folder)

    @classmethod
    def tearDownClass(cls):
        for k,v in cls.old.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        cls.root_tmp.cleanup()

    def test_occ_solid_is_real_one_body_and_step_import_roundtrips(self):
        m,trace,report=verify_files(self.folder)
        self.assertEqual(m,self.manifest)
        self.assertEqual(report["engine"],"CADQUERY_OCCT_BREP")
        self.assertTrue(report["verified_closed_solid"])
        self.assertTrue(report["step_reimport_verified"])
        self.assertFalse(report["stl_mesh_watertight_verified"])
        self.assertEqual(report["pad"]["solid_count"],1)
        self.assertEqual(report["pocket"]["solid_count"],1)
        self.assertGreater(report["pad"]["volume_mm3"],
                           report["pocket"]["volume_mm3"])
        self.assertGreater((self.folder/"solid.step").stat().st_size,500)
        self.assertGreater((self.folder/"solid.stl").stat().st_size,100)

    def test_actual_ledger_contains_six_linked_explainable_decision_events(self):
        _,trace,_=verify_files(self.folder)
        self.assertEqual(len(trace["events"]),6)
        self.assertEqual([x["decision_code"] for x in trace["events"]],
                         ["SOURCE","SKETCH_TO_SOLID","PAD","POCKET",
                          "NEUTRAL_EXPORT","REIMPORT"])
        self.assertEqual(trace["events"][1]["selected"],"OCCT_EXACT_ARC_WIRE")
        self.assertEqual(trace["events"][-1]["selected"],
                         "REIMPORT_STEP_AND_COMPARE_VOLUME")
        self.assertTrue(all(x["declared_rationale_code"] for x in trace["events"]))
        self.assertTrue(all(x["source_refs"]==[self.sketch["sketch_id"]]
                            for x in trace["events"]))
        self.assertFalse(any(x["model_private_reasoning_captured"]
                             for x in trace["events"]))
        self.assertFalse(trace["physical_action"])
        self.assertEqual(validate_trace(trace,self.sketch),trace)

    def test_solid_build_is_single_occurrence_no_overwrite_or_hidden_actuation(self):
        original=(self.folder/"solid.step").read_bytes()
        with self.assertRaises(Hold):
            build_solid(self.sketch,self.folder)
        self.assertEqual((self.folder/"solid.step").read_bytes(),original)

    def test_unearned_reseal_cannot_change_source_or_trace(self):
        victim=self.root/"tampered-trace"
        shutil.copytree(self.folder,victim)
        trace_path=victim/"design-trace.json"
        trace=json.loads(trace_path.read_text())
        trace["events"][2]["selected"]="PRINTER_START"
        trace_path.write_text(json.dumps(trace))
        with self.assertRaises(Hold):
            verify_files(victim)

    def test_corrupted_step_refused_on_hash_even_without_kernel_inspection(self):
        victim=self.root/"tampered-step"
        shutil.copytree(self.folder,victim)
        with (victim/"solid.step").open("ab") as f:f.write(b"\nBAD-STEP")
        with self.assertRaisesRegex(Hold,"SOLID_FILE_HASH_MISMATCH"):
            verify_files(victim,inspect_kernel=False)

    def test_sketch_source_and_verified_portable_reports_are_bound(self):
        manifest,trace,report=verify_files(self.folder)
        self.assertEqual(report["source_sketch_id"],self.sketch["sketch_id"])
        self.assertEqual(manifest["source_sketch_id"],trace["source_sketch_id"])
        self.assertFalse(report["manufacturability_verified"])
        self.assertFalse(report["physical_fabrication"])
        self.assertEqual(manifest["authority"],"none")

    def test_real_relatte_signs_crossing_and_two_hold_receipts(self):
        runtime=self.root/"secret-native-relatte-runtime"
        result=cross(self.folder,runtime)
        v=verify_native(self.folder)
        self.assertEqual(v["status"],"SIGNED_CROSSING_AND_RECEIVE_HOLD_VERIFIED")
        self.assertEqual(v["disposition"],"HOLD")
        self.assertEqual(result["result"]["receive_receipt"]["kind"],"RECEIVED")
        self.assertEqual(result["result"]["disposition_receipt"]["kind"],"R3_HOLD")
        self.assertEqual(result["result"]["crossing"]["crossing_id"],v["crossing_id"])
        self.assertEqual(result["result"]["crossing"]["source_history_head"],
                         json.loads((self.folder/"design-trace.json").read_text())["trace_id"])
        self.assertFalse(v["fabrication_grant"])
        self.assertTrue((runtime/"receiver"/"receiver-key.json").exists())
        self.assertFalse((self.folder/"receiver-key.json").exists())
        self.assertEqual(stat.S_IMODE((runtime/"receiver"/"receiver-key.json").stat().st_mode),0o600)
        with self.assertRaisesRegex(Hold,"NO_AUTORETRY"):
            cross(self.folder,self.root/"another-runtime")

    def test_native_cold_replay_detects_forged_signature_or_payload(self):
        # Requires the previous test's real reLATTE witness; if test ordering
        # changes, run the real crossing once with a distinct private root.
        if not (self.folder/"relatte-evidence.json").exists():
            cross(self.folder,self.root/"native-proof-again")
        victim=self.root/"tampered-relatte"
        shutil.copytree(self.folder,victim)
        file=victim/"relatte-evidence.json"
        data=json.loads(file.read_text())
        signature=data["result"]["crossing"]["signing"]["signature"]
        data["result"]["crossing"]["signing"]["signature"]=(
            ("A" if signature[0]!="A" else "B")+signature[1:]
        )
        file.write_text(json.dumps(data))
        with self.assertRaises(Hold):
            verify_native(victim)
        again=self.root/"swapped-solid"
        shutil.copytree(self.folder,again)
        with (again/"solid.stl").open("ab") as f:f.write(b"tampering")
        with self.assertRaises(Hold):
            verify_native(again)

    def test_operator_cli_cold_verifies_without_second_kernel_execution(self):
        if not (self.folder/"relatte-evidence.json").exists():
            cross(self.folder,self.root/"cli-relatte-root")
        cli=ROOT/"scripts/static-solid.py"
        p=subprocess.run([sys.executable,str(cli),"verify","--out-dir",
                         str(self.folder)],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("NATIVE_RELATTE_COLD_VERIFIED",p.stdout)
        before=(self.folder/"solid.step").read_bytes()
        p2=subprocess.run([sys.executable,str(cli),"verify","--out-dir",
                           str(self.folder)],capture_output=True,text=True)
        self.assertEqual(p2.returncode,0,p2.stderr)
        self.assertEqual((self.folder/"solid.step").read_bytes(),before)


if __name__=="__main__":
    unittest.main()
