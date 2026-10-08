"""STATIC-CAD-004: exact constrained sketches, geometry and export refusals."""
from __future__ import annotations

import copy
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from crank.runtime import digest
from question_first.session import Hold,discover_ghot,_sealed
from question_first.apparatus_compiler import compile_apparatus
from question_first.static_cad import SEED as CAD_SEED,compile_project
from question_first.sketch_solver import SEED, compile_sketch,verify_sketch,validate_seed
from question_first.sketch_exports import (
    artifacts,dxf,features,freecad_macro,manifest,svg,verify_package,write_package,
)

ROOT=Path(__file__).resolve().parents[1]
AP=json.loads((ROOT/"fixtures/apparatus-002/source-grounded-question.json").read_text())
PARAMS=json.loads((ROOT/"fixtures/static-cad-003/reference-parameters.json").read_text())
SOURCE=json.loads((ROOT/"fixtures/static-cad-004/rounded-mount-sketch.json").read_text())
MANIFEST=ROOT/"integrations/apparatus-002/adapter-manifest.json"


class StaticSketch004Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="sketch004-")
        self.root=Path(self.temp.name)
        self.ghot=Path(os.environ["GHOT_SRC"]) if os.environ.get("GHOT_SRC") else None
        self.previous={key:os.environ.get(key)
                       for key in ("GHOT_HOME","GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"]=str(self.root/"ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"]=str(MANIFEST)

    def tearDown(self):
        for k,v in self.previous.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
        self.temp.cleanup()

    def project(self):
        if self.ghot is None:
            self.skipTest("Pinned GHoT native source required in dedicated CI")
        app=compile_apparatus(AP,discover_ghot(self.ghot))
        return compile_project({
            "schema":CAD_SEED,
            "apparatus_plan_id":app["plan_id"],
            "selected_candidate_id":"gear-then-screw",
            "parameters":PARAMS,"revision_parent_id":None,
        },app)

    def seed(self, project=None):
        p=project or self.project()
        return {**copy.deepcopy(SOURCE),"cad_parent_id":p["project_id"]}

    def solved(self):
        parent=self.project()
        return compile_sketch(self.seed(parent),parent)

    def test_constraint_solver_recovers_rounded_profile_from_misaligned_initial_points(self):
        s=self.solved()
        self.assertEqual(s["constraint_report"]["state"],"SOLVED")
        self.assertEqual(s["constraint_report"]["degrees_of_freedom"],0)
        self.assertEqual(s["constraint_report"]["redundant_equations"],0)
        self.assertLess(s["constraint_report"]["max_residual_mm"],0.004)
        self.assertAlmostEqual(s["resolved_points"]["p1"]["x_um"],70000,delta=3)
        self.assertAlmostEqual(s["resolved_points"]["p1"]["y_um"],0,delta=3)
        self.assertAlmostEqual(s["resolved_points"]["p3"]["x_um"],80000,delta=3)
        self.assertAlmostEqual(s["resolved_points"]["p3"]["y_um"],50000,delta=3)
        self.assertGreater(s["geometry_report"]["net_area_mm2"],3500)
        self.assertEqual(s["geometry_report"]["holes_count"],2)
        self.assertFalse(s["freecad_engine_executed"])
        self.assertFalse(s["physical_effects"])
        self.assertEqual(verify_sketch(s),s)
        self.assertFalse((self.root/"ghot"/"instrument-rack").exists())

    def test_missing_dimension_is_underconstrained_not_a_ready_export(self):
        parent=self.project()
        seed=self.seed(parent)
        seed["constraints"]=[c for c in seed["constraints"]
                             if not (c["kind"]=="distance" and c["a"]=="p3"
                                     and c["b"]=="p4")]
        result=compile_sketch(seed,parent)
        self.assertEqual(result["constraint_report"]["state"],"UNDERCONSTRAINED")
        self.assertGreater(result["constraint_report"]["degrees_of_freedom"],0)
        with self.assertRaises(Hold):artifacts(result)

    def test_redundant_consistent_constraint_is_reported(self):
        parent=self.project()
        seed=self.seed(parent)
        seed["constraints"].append({"kind":"horizontal","a":"p0","b":"p1"})
        result=compile_sketch(seed,parent)
        self.assertEqual(result["constraint_report"]["state"],"REDUNDANT_CONSTRAINTS")
        self.assertGreater(result["constraint_report"]["redundant_equations"],0)
        with self.assertRaises(Hold):artifacts(result)

    def test_conflicting_position_constraint_is_inconsistent_not_exportable(self):
        parent=self.project()
        seed=self.seed(parent)
        seed["constraints"].append({
            "kind":"fix","point":"p1","x_um":10000,"y_um":10000,
        })
        result=compile_sketch(seed,parent)
        self.assertEqual(result["constraint_report"]["state"],"INCONSISTENT")
        with self.assertRaises(Hold):freecad_macro(result)

    def test_nonclosed_profile_and_unknown_center_refused(self):
        parent=self.project()
        seed=self.seed(parent)
        seed["path"][1]["end"]="p3"
        with self.assertRaises(Hold):validate_seed(seed)
        seed=self.seed(parent)
        seed["path"][1]["center"]="invented"
        with self.assertRaises(Hold):validate_seed(seed)

    def test_expressions_extra_actions_float_and_bool_refused(self):
        parent=self.project()
        for change in (
            ("p1","x_um",True),("p1","x_um",3.14),
            ("p1","x_um","100000+eval"),("p1","y_um",100000000),
        ):
            pt,dim,val=change
            seed=self.seed(parent)
            seed["points"][pt][dim]=val
            with self.subTest(change=change),self.assertRaises(Hold):
                validate_seed(seed)
        seed=self.seed(parent)
        seed["features"].append({"kind":"gcode","path":"/tmp/evil"})
        with self.assertRaises(Hold):validate_seed(seed)
        seed=self.seed(parent)
        seed["hardware_grant"]=True
        with self.assertRaises(Hold):validate_seed(seed)

    def test_bad_hole_geometry_fails_even_when_constraint_system_solved(self):
        parent=self.project()
        seed=self.seed(parent)
        seed["holes"][0]["radius_um"]=20000
        with self.assertRaisesRegex(Hold,"HOLE_EDGE_CLEARANCE_FAILED"):
            compile_sketch(seed,parent)
        seed=self.seed(parent)
        seed["holes"][1]["center"]="h1"
        with self.assertRaisesRegex(Hold,"HOLE_TO_HOLE_CLEARANCE_FAILED"):
            compile_sketch(seed,parent)

    def test_modified_fixed_arc_center_fails_radius_geometry(self):
        parent=self.project()
        seed=self.seed(parent)
        for c in seed["constraints"]:
            if c["kind"]=="fix" and c["point"]=="c0":
                c["y_um"]=14000
        with self.assertRaises(Hold):
            compile_sketch(seed,parent)

    def test_svg_dxf_have_real_arc_lines_and_circle_entities(self):
        sketch=self.solved()
        vector=svg(sketch)
        cad=dxf(sketch)
        self.assertIn("<svg",vector)
        self.assertIn(" A ",vector)
        self.assertEqual(vector.count("<circle "),2)
        self.assertIn("AC1009",cad)
        self.assertEqual(cad.count("\nARC\n"),1)
        self.assertEqual(cad.count("\nCIRCLE\n"),2)
        self.assertEqual(cad.count("\nLINE\n"),4)
        self.assertIn("pocket_through",features(sketch))

    def test_freecad_macro_is_operator_run_real_wire_pad_pocket_source(self):
        code=freecad_macro(self.solved())
        compile(code,"generated-sketch.FCMacro","exec")
        for token in (
            "Part.Wire(edges)","Part.Arc(","face.extrude(",
            "Part.makeCylinder(","solid.cut(cutter)",
            "doc.saveAs(","Import.export([obj]","Mesh.export([obj]",
            "STATIC_CAD_SKETCH_FREECAD_OUTPUT",
        ):self.assertIn(token,code)
        self.assertNotIn("subprocess.run",code)
        self.assertNotIn("os.system",code)

    def test_package_roundtrip_exact_source_and_no_stl_step_claim(self):
        sketch=self.solved()
        dest=self.root/"package"
        proof=write_package(sketch,dest)
        self.assertEqual(proof,verify_package(dest))
        self.assertEqual(len(proof["artifact_sha256"]),5)
        self.assertFalse(proof["brep_engine_executed"])
        self.assertEqual(proof["not_exported"],["FCSTD","STEP","STL"])
        for name in list(proof["artifact_sha256"])+["manifest.json"]:
            self.assertEqual(stat.S_IMODE((dest/name).stat().st_mode),0o600)
        with self.assertRaises(FileExistsError):
            write_package(sketch,dest)

    def test_package_drawing_rehashed_by_attacker_still_fails(self):
        sketch=self.solved()
        dest=self.root/"package"
        write_package(sketch,dest)
        altered=(dest/"drawing.svg").read_bytes()+b"<!-- replaced -->"
        (dest/"drawing.svg").write_bytes(altered)
        manifest_path=dest/"manifest.json"
        old=json.loads(manifest_path.read_text())
        old["artifact_sha256"]["drawing.svg"]=hashlib.sha256(altered).hexdigest()
        old["manifest_id"]="static-os-sketch-package-v0:"+digest({
            k:v for k,v in old.items() if k!="manifest_id"
        })
        manifest_path.write_text(json.dumps(old))
        with self.assertRaises(Hold):verify_package(dest)

    def test_source_parent_cannot_be_silently_changed(self):
        project=self.project()
        seed=self.seed(project)
        seed["cad_parent_id"]="static-os-cad-project-v0:"+"f"*64
        with self.assertRaises(Hold):compile_sketch(seed,project)
        original=self.solved()
        modified=copy.deepcopy(original)
        modified["source_image_verified"]=True
        modified=_sealed({k:v for k,v in modified.items() if k!="sketch_id"},
                         "sketch_id","static-os-solved-sketch-v0:")
        with self.assertRaises(Hold):verify_sketch(modified)

    def test_cli_source_bound_solve_verify_and_refuse_existing_output(self):
        project=self.project()
        fixture=self.root/"seed.json"
        parent=self.root/"parent.json"
        out=self.root/"output"
        fixture.write_text(json.dumps(self.seed(project)))
        parent.write_text(json.dumps(project))
        cli=[sys.executable,str(ROOT/"scripts/static-sketch.py")]
        command=cli+["solve","--seed",str(fixture),
                     "--parent-project",str(parent),"--out-dir",str(out)]
        first=subprocess.run(command,text=True,capture_output=True)
        self.assertEqual(first.returncode,0,first.stderr)
        cold=subprocess.run(cli+["verify","--out-dir",str(out)],
                            text=True,capture_output=True)
        self.assertEqual(cold.returncode,0,cold.stderr)
        self.assertIn("EXACT_SKETCH_PACKAGE_VERIFIED",cold.stdout)
        again=subprocess.run(command,text=True,capture_output=True)
        self.assertNotEqual(again.returncode,0)
        self.assertFalse((self.root/"ghot"/"instrument-rack").exists())


if __name__=="__main__":
    unittest.main()
