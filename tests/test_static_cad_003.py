"""STATIC-CAD-003 hostile contracts and native APPARATUS-002 interop.

The renderer is a deterministic design candidate. Tests intentionally do not
claim a FreeCAD engine ran or that printable/structural parts are certified.
"""
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

from question_first.session import Hold, discover_ghot, _sealed
from question_first.apparatus_compiler import compile_apparatus
from question_first.static_cad import (
    SEED, compile_project, verify_project, revise_project,
)
from question_first.cad_exports import (
    svg, dxf, bom, artifacts, manifest, freecad_macro,
    write_package, verify_package,
)

ROOT=Path(__file__).resolve().parents[1]
AP_SEED=json.loads((ROOT/"fixtures/apparatus-002/source-grounded-question.json").read_text())
PARAMS=json.loads((ROOT/"fixtures/static-cad-003/reference-parameters.json").read_text())
MANIFEST=ROOT/"integrations/apparatus-002/adapter-manifest.json"


class StaticCAD003Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="static-cad-003-")
        self.root=Path(self.temp.name)
        self.ghot=Path(os.environ["GHOT_SRC"]) if os.environ.get("GHOT_SRC") else None
        self.previous={k:os.environ.get(k) for k in ("GHOT_HOME","GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"]=str(self.root/"ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"]=str(MANIFEST)

    def tearDown(self):
        for k,v in self.previous.items():
            if v is None: os.environ.pop(k,None)
            else: os.environ[k]=v
        self.temp.cleanup()

    def parent(self):
        if not self.ghot:
            self.skipTest("Dedicated CAD CI supplies pinned GHOT_SRC")
        return compile_apparatus(AP_SEED,discover_ghot(self.ghot))

    def make(self, p=None, candidate="gear-then-screw", params=None, revision=None):
        parent=p or self.parent()
        seed={
            "schema":SEED, "apparatus_plan_id":parent["plan_id"],
            "selected_candidate_id":candidate,
            "parameters":copy.deepcopy(PARAMS if params is None else params),
            "revision_parent_id":revision,
        }
        return compile_project(seed,parent)

    def test_parameterized_two_part_reference_builds_and_binds_parent(self):
        parent=self.parent()
        cad=self.make(parent)
        self.assertEqual(cad["source_apparatus_plan"]["plan_id"],parent["plan_id"])
        self.assertEqual(len(cad["parts"]),2)
        self.assertEqual([x["id"] for x in cad["parts"]],
                         ["base-plate","bearing-upright"])
        self.assertEqual(cad["derived"]["driven_pitch_diameter_um"],57600)
        self.assertEqual(cad["derived"]["expected_ideal_axial_um"],
                         {"numerator":-3000,"denominator":1})
        self.assertEqual(cad["mates"][0]["residual_um"],0)
        self.assertTrue(all(cad["constraints"].values()))
        self.assertFalse(cad["fabrication_allowed"])
        self.assertFalse(cad["geometric_boolean_executed"])
        self.assertFalse(cad["freecad_engine_tested"])
        self.assertEqual(verify_project(cad),cad)
        self.assertFalse((self.root/"ghot"/"instrument-rack").exists())

    def test_different_design_candidate_is_distinguished(self):
        parent=self.parent()
        direct=self.make(parent,candidate="direct-screw")
        geared=self.make(parent,candidate="gear-then-screw")
        self.assertNotEqual(direct["project_id"],geared["project_id"])
        self.assertEqual(direct["derived"]["expected_ideal_axial_um"],
                         {"numerator":9000,"denominator":1})
        self.assertEqual(geared["derived"]["expected_ideal_axial_um"],
                         {"numerator":-3000,"denominator":1})

    def test_integer_parameters_reject_float_bool_and_expr(self):
        parent=self.parent()
        for name,value in (
            ("module_um",True),("module_um",1.6),("module_um","1600"),
            ("module_um","__import__('os')"),("module_um",100000),
            ("wall_um",0),("base_width_um",10_000),
            ("mount_margin_um",-1),
        ):
            params={**PARAMS,name:value}
            with self.subTest(name=name,value=value),self.assertRaises(Hold):
                self.make(parent,params=params)
        self.assertFalse((self.root/"ghot"/"instrument-rack").exists())

    def test_unowned_params_and_fabrication_fields_refused(self):
        parent=self.parent()
        for params in (
            {**PARAMS,"run_machine":True},
            {k:v for k,v in PARAMS.items() if k!="clearance_um"},
            {**PARAMS,"material":"INVENTED_TITANIUM_CERTIFIED"},
        ):
            with self.subTest(params=params),self.assertRaises(Hold):
                self.make(parent,params=params)
        s=self.make(parent)["cad_seed"]
        for key,value in (
            ("apparatus_plan_id","forged"),
            ("selected_candidate_id","laser-cutter"),
            ("revision_parent_id","not-a-parent"),
        ):
            with self.subTest(key=key),self.assertRaises(Hold):
                compile_project({**s,key:value},parent)

    def test_through_hole_clearance_and_geometry_reject(self):
        parent=self.parent()
        samples=(
            {**PARAMS,"mount_margin_um":8000,"mount_hole_diameter_um":9000,
             "clearance_um":5000},
            {**PARAMS,"base_width_um":35000,"bore_diameter_um":15000,
             "wall_um":12000,"clearance_um":5000},
            {**PARAMS,"module_um":5000,"base_width_um":35000,
             "bore_diameter_um":15000,"wall_um":20000},
        )
        for x in samples:
            with self.subTest(params=x),self.assertRaises(Hold):
                self.make(parent,params=x)

    def test_mutated_or_resealed_geometry_does_not_pass_cold_check(self):
        cad=self.make()
        altered=copy.deepcopy(cad)
        altered["parts"][0]["holes"][0]["center_um"][0]=-100
        with self.assertRaises(Hold):
            verify_project(altered)
        changed=_sealed({k:v for k,v in altered.items() if k!="project_id"},
                        "project_id","static-os-cad-project-v0:")
        with self.assertRaises(Hold):
            verify_project(changed)
        altered=copy.deepcopy(cad)
        altered["source_bytes_verified"]=True
        changed=_sealed({k:v for k,v in altered.items() if k!="project_id"},
                        "project_id","static-os-cad-project-v0:")
        with self.assertRaises(Hold):
            verify_project(changed)

    def test_revision_preserves_original_design_and_records_parent(self):
        parent=self.parent()
        initial=self.make(parent)
        params={**PARAMS,"base_width_um":69000}
        child=revise_project(initial,{
            "schema":SEED,
            "apparatus_plan_id":parent["plan_id"],
            "selected_candidate_id":"gear-then-screw",
            "revision_parent_id":initial["project_id"],"parameters":params,
        },parent)
        self.assertNotEqual(child["project_id"],initial["project_id"])
        self.assertEqual(child["cad_seed"]["revision_parent_id"],initial["project_id"])
        self.assertEqual(initial["parameters_resolved"]["base_width_um"],64000)
        self.assertEqual(child["parameters_resolved"]["base_width_um"],69000)
        with self.assertRaises(Hold):
            revise_project(initial,{**child["cad_seed"],"revision_parent_id":None},parent)
        with self.assertRaises(Hold):
            revise_project(initial,{**child["cad_seed"],"parameters":PARAMS},parent)

    def test_actual_svg_and_dxf_contain_four_drill_holes_and_outline(self):
        cad=self.make()
        image=svg(cad)
        plan=dxf(cad)
        self.assertIn("<svg",image)
        self.assertIn("TOP / BORE / PITCH REFERENCE",image)
        self.assertEqual(image.count('fill="white"'),5)  # 4 mount + bore
        self.assertIn("AC1009",plan)
        self.assertEqual(plan.count("\nCIRCLE\n"),6)  # holes+bore+pitch reference
        self.assertTrue(plan.rstrip().endswith("EOF"))
        self.assertEqual(bom(cad).count("\n"),3)  # header and two parts
        self.assertNotIn("verified_manufacturable,YES",bom(cad))

    def test_freecad_macro_source_exposes_genuine_solid_cut_not_claimed_execution(self):
        cad=self.make()
        macro=freecad_macro(cad)
        self.assertIn("Part.makeBox",macro)
        self.assertIn("Part.makeCylinder",macro)
        self.assertIn("shape.cut(tool)",macro)
        self.assertIn("Import.export(solids",macro)
        self.assertIn("Mesh.export(solids",macro)
        self.assertIn("doc.saveAs",macro)
        self.assertIn("STATIC_CAD_FREECAD_OUTPUT",macro)
        self.assertNotIn("subprocess.run",macro)
        self.assertNotIn("os.system",macro)
        self.assertNotIn("os.makedirs",macro)
        self.assertNotIn("os.exec",macro)
        self.assertFalse(cad["freecad_engine_tested"])

    def test_export_bom_manifest_and_reverify_exact_bytes(self):
        cad=self.make()
        path=self.root/"package"
        m=write_package(cad,path)
        self.assertEqual(verify_package(path),m)
        self.assertEqual(len(m["artifact_sha256"]),5)
        self.assertEqual(m["exports_not_created"],["FCSTD","STEP","STL"])
        for filename in ("project.json","drawing.svg","plan.dxf",
                         "bill-of-materials.csv","generate-freecad.FCMacro","manifest.json"):
            self.assertEqual(stat.S_IMODE((path/filename).stat().st_mode),0o600)
        with self.assertRaises(FileExistsError):
            write_package(cad,path)

    def test_rehashed_corrupted_drawing_still_refuses(self):
        cad=self.make()
        path=self.root/"pkg"
        write_package(cad,path)
        altered=(path/"drawing.svg").read_bytes()+b"<!-- injected -->"
        (path/"drawing.svg").write_bytes(altered)
        with self.assertRaises(Hold):
            verify_package(path)
        # Rehash the manifest after tampering; verifier independently regenerates SVG.
        m=json.loads((path/"manifest.json").read_text())
        m["artifact_sha256"]["drawing.svg"]=hashlib.sha256(altered).hexdigest()
        from crank.runtime import digest
        m["manifest_id"]="static-os-cad-manifest-v0:"+digest({
            k:v for k,v in m.items() if k!="manifest_id"
        })
        (path/"manifest.json").write_text(json.dumps(m))
        with self.assertRaises(Hold):
            verify_package(path)

    def test_cli_compiles_package_then_read_only_verifies_and_refuses_overwrite(self):
        self.parent()
        repo=ROOT/"scripts/static-cad.py"
        apparatus_plan=self.parent()
        parent_path=self.root/"apparatus-plan.json"
        parent_path.write_text(json.dumps({"plan":apparatus_plan,
                                            "executed":False,"authority":"none"}))
        output=self.root/"cad"
        command=[
            sys.executable,str(repo),"compile",
            "--apparatus-plan",str(parent_path),
            "--parameters",str(ROOT/"fixtures/static-cad-003/reference-parameters.json"),
            "--candidate","gear-then-screw","--out-dir",str(output),
        ]
        before=self.root/"ghot"/"instrument-rack"
        res=subprocess.run(command,capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        self.assertFalse(before.exists())
        again=subprocess.run(command,capture_output=True,text=True)
        self.assertNotEqual(again.returncode,0)
        verify=subprocess.run([sys.executable,str(repo),"verify",
                               "--out-dir",str(output)],capture_output=True,text=True)
        self.assertEqual(verify.returncode,0,verify.stderr)
        self.assertIn("VERIFIED_EXACT_CAD_PACKAGE",verify.stdout)

    def test_cli_revision_changes_parameters_without_mutating_first(self):
        self.parent()
        old=self.make()
        path=self.root/"first"
        write_package(old,path)
        parent_plan=self.parent()
        par=self.root/"parent.json"
        par.write_text(json.dumps({"plan":parent_plan}))
        changed=self.root/"adjusted.json"
        changed.write_text(json.dumps({**PARAMS,"base_width_um":68000}))
        second=self.root/"second"
        res=subprocess.run([
            sys.executable,str(ROOT/"scripts/static-cad.py"),"revise",
            "--apparatus-plan",str(par),"--parameters",str(changed),
            "--parent-project",str(path/"project.json"),
            "--out-dir",str(second),
        ],capture_output=True,text=True)
        self.assertEqual(res.returncode,0,res.stderr)
        new=verify_project(json.loads((second/"project.json").read_text()))
        self.assertEqual(new["cad_seed"]["revision_parent_id"],old["project_id"])
        self.assertEqual(verify_package(path)["project_id"],old["project_id"])
        self.assertEqual(verify_package(second)["project_id"],new["project_id"])


if __name__=="__main__":
    unittest.main()
