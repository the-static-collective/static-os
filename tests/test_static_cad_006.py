"""STATIC-CAD-006: branch-preserving CAD execution via reLATTE and GOATnote.

Requires real native GHoT, real CadQuery OCCT, real reLATTE source and a
pinned GOATnote version. No fake signer or simulated GOATnote library.
"""
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

from question_first.session import Hold,discover_ghot
from question_first.apparatus_compiler import compile_apparatus
from question_first.static_cad import compile_project,SEED as CAD_SEED
from question_first.sketch_solver import compile_sketch
from question_first.feature_tree import (
    SELECTION, plan_tree,verify_tree,choose,
    compile_selected,verify_branch_result,
)
from question_first.cad_goatnote import (
    execute_branch,verify_branch,handoff_from_native,
)

ROOT=Path(__file__).resolve().parents[1]
AP=json.loads((ROOT/"fixtures/apparatus-002/source-grounded-question.json").read_text())
PARAMS=json.loads((ROOT/"fixtures/static-cad-003/reference-parameters.json").read_text())
SKETCH=json.loads((ROOT/"fixtures/static-cad-004/rounded-mount-sketch.json").read_text())
ADAPTER=ROOT/"integrations/apparatus-002/adapter-manifest.json"


class FeatureGoatnote006Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if "GHOT_SRC" not in os.environ:
            raise unittest.SkipTest("Dedicated CI needs the pinned native GHoT source")
        cls.working=tempfile.TemporaryDirectory(prefix="static-cad-goat-006-")
        cls.root=Path(cls.working.name)
        cls.previous={n:os.environ.get(n)
                      for n in ("GHOT_HOME","GHOT_ADAPTER_MANIFESTS")}
        os.environ["GHOT_HOME"]=str(cls.root/"ghot")
        os.environ["GHOT_ADAPTER_MANIFESTS"]=str(ADAPTER)
        app=compile_apparatus(AP,discover_ghot(Path(os.environ["GHOT_SRC"])))
        cad=compile_project({
            "schema":CAD_SEED,"apparatus_plan_id":app["plan_id"],
            "selected_candidate_id":"gear-then-screw",
            "parameters":PARAMS,"revision_parent_id":None,
        },app)
        parent={**SKETCH,"cad_parent_id":cad["project_id"]}
        cls.root_sketch=compile_sketch(parent,cad)
        cls.tree=plan_tree(cls.root_sketch)
        cls.outputs={}
        cls.selections={}
        for candidate in ("pad-deeper","bore-wider"):
            selected={
                "schema":SELECTION,"tree_id":cls.tree["tree_id"],
                "candidate_id":candidate,"owner_id":"test-local-operator",
                "approved":True,
                "execution_scope":"SOFTWARE_CAD_KERNEL_AND_SIGNED_HOLD",
            }
            cls.selections[candidate]=selected
            folder=cls.root/candidate
            runtime=cls.root/(candidate+"-private-native-relatte")
            cls.outputs[candidate]=execute_branch(
                cls.tree,selected,output_root=folder,
                private_relatte_root=runtime)
        cls.original=copy.deepcopy(cls.root_sketch)

    @classmethod
    def tearDownClass(cls):
        for key,old in cls.previous.items():
            if old is None:os.environ.pop(key,None)
            else:os.environ[key]=old
        cls.working.cleanup()

    def test_root_question_source_remains_immutable(self):
        self.assertEqual(self.tree,verify_tree(self.tree))
        self.assertEqual(len(self.tree["feature_nodes"]),3)
        self.assertEqual([c["id"] for c in self.tree["candidate_revisions"]],
                         ["pad-deeper","bore-wider"])
        self.assertFalse(self.tree["source_mutation"])
        self.assertEqual(self.root_sketch,self.original)
        self.assertEqual(self.tree["status"],"PROPOSAL_ONLY")

    def test_two_alternatives_create_distinct_signed_kernel_results(self):
        a=self.outputs["pad-deeper"]
        b=self.outputs["bore-wider"]
        self.assertNotEqual(a["manifest"]["branch_sketch_id"],
                            b["manifest"]["branch_sketch_id"])
        self.assertNotEqual(a["manifest"]["relatte_crossing_id"],
                            b["manifest"]["relatte_crossing_id"])
        self.assertNotEqual(a["manifest"]["goatnote_source_note_id"],
                            b["manifest"]["goatnote_source_note_id"])
        self.assertEqual(a["manifest"]["parent_sketch_id"],
                         self.root_sketch["sketch_id"])
        self.assertEqual(b["manifest"]["parent_sketch_id"],
                         self.root_sketch["sketch_id"])
        sa=a["handoff"]["branch"];sb=b["handoff"]["branch"]
        self.assertEqual(sa["alternatives_not_executed"],["bore-wider"])
        self.assertEqual(sb["alternatives_not_executed"],["pad-deeper"])
        self.assertFalse(sa["construction_authorized"])
        self.assertFalse(sb["construction_authorized"])

    def test_bounded_feature_tree_reconstructs_exact_selected_solved_revision(self):
        for candidate in ("pad-deeper","bore-wider"):
            s=self.selections[candidate]
            rev=compile_selected(self.tree,s)
            self.assertEqual(rev["seed"]["revision_parent_id"],
                             self.root_sketch["sketch_id"])
            witness=self.outputs[candidate]["handoff"]["branch"]
            verify_branch_result(self.tree,s,rev,witness)
            if candidate=="pad-deeper":
                self.assertEqual(rev["features"][0]["depth_um"],
                                 self.root_sketch["features"][0]["depth_um"]+2000)
            else:
                self.assertEqual(rev["seed"]["holes"][0]["radius_um"],
                                 self.root_sketch["seed"]["holes"][0]["radius_um"]+500)

    def test_native_goatnote_has_exact_version_bound_margins(self):
        for candidate,output in self.outputs.items():
            note=output["preview"]["source_note"]
            version=note["versions"][0]
            self.assertEqual(len(note["margins"]),12)
            self.assertEqual(len(note["returnThreads"]),1)
            self.assertIn("Selected branch: "+candidate,version["text"])
            self.assertIn("GOATnote has NOT independently verified",version["text"])
            self.assertTrue(note["cadJournal"]["upstream_native_verified"])
            self.assertFalse(note["cadJournal"]["goatnote_signature_verified"])
            for m in note["margins"]:
                self.assertEqual(m["versionId"],version["id"])
                a=m["anchor"]
                self.assertEqual(version["text"][a["start"]:a["end"]],a["quote"])
            self.assertEqual(note["returnThreads"][0]["sourceVersionId"],
                             version["id"])
            self.assertEqual(output["manifest"]["browser_imported"],False)

    def test_native_relatte_hold_and_crossing_bytes_reconstruct_readonly(self):
        for candidate,output in self.outputs.items():
            folder=self.root/candidate
            actual=verify_branch(folder)
            self.assertEqual(actual,output["manifest"])
            h=output["handoff"]
            self.assertEqual(h["evidence"]["disposition"],"HOLD")
            self.assertFalse(h["evidence"]["fabrication_grant"])
            self.assertEqual(h["evidence"]["native_verification"],
                             "SIGNED_CROSSING_AND_RECEIVE_HOLD_VERIFIED")
            proof=json.loads((folder/"solid"/"relatte-evidence.json").read_text())
            self.assertEqual(proof["result"]["receive_receipt"]["kind"],"RECEIVED")
            self.assertEqual(proof["result"]["disposition_receipt"]["kind"],"R3_HOLD")
            self.assertTrue((self.root/(candidate+"-private-native-relatte")/
                             "receiver"/"receiver-key.json").is_file())
            self.assertFalse((folder/"solid"/"receiver-key.json").exists())

    def test_repeat_explicit_selection_refuses_no_reissue_crossing(self):
        folder=self.root/"pad-deeper"
        step=(folder/"solid"/"solid.step").read_bytes()
        with self.assertRaisesRegex(Hold,"NO_AUTORETRY"):
            execute_branch(self.tree,self.selections["pad-deeper"],
                           output_root=folder,
                           private_relatte_root=self.root/"another-secret")
        self.assertEqual((folder/"solid"/"solid.step").read_bytes(),step)

    def test_refuse_no_selection_and_capability_laundering(self):
        selected=self.selections["pad-deeper"]
        bad=[
            {**selected,"approved":False},
            {**selected,"approved":1},
            {**selected,"candidate_id":"undeclared-motor"},
            {**selected,"owner_id":"inject;rm -rf"},
            {**selected,"tree_id":"stale"},
            {**selected,"execution_scope":"FABRICATE_NOW"},
            {**selected,"authority":"OWNER_OVERRIDE"},
        ]
        for row in bad:
            with self.subTest(row=row),self.assertRaises(Hold):
                choose(self.tree,row)
        self.assertEqual(self.tree["selected_candidate"],"NONE")

    def test_rehashed_tampered_feature_graph_fails_source_reconstruction(self):
        mutated=copy.deepcopy(self.tree)
        mutated["feature_nodes"][1]["depth_um"]=1000000
        from question_first.session import _sealed
        readdressed=_sealed({
            k:v for k,v in mutated.items() if k!="tree_id"
        },"tree_id","static-os-cad-feature-tree-v0:")
        with self.assertRaises(Hold):
            verify_tree(readdressed)

    def test_changed_goatnote_journal_source_or_relatte_payload_ref_refuses(self):
        source=self.root/"pad-deeper"
        copy=self.root/"tampered-goat-preview"
        shutil.copytree(source,copy)
        path=copy/"goatnote-preview.json"
        data=json.loads(path.read_text())
        data["source_note"]["versions"][0]["text"]="MUTATED ORIGINAL"
        path.write_text(json.dumps(data))
        with self.assertRaises(Hold):
            verify_branch(copy)
        copy2=self.root/"tampered-goat-handoff"
        shutil.copytree(source,copy2)
        path=copy2/"goatnote-handoff.json"
        data=json.loads(path.read_text())
        data["evidence"]["disposition"]="ADMIT"
        path.write_text(json.dumps(data))
        with self.assertRaises(Hold):
            verify_branch(copy2)

    def test_changed_native_signatures_refuse_cold_journal(self):
        original=self.root/"bore-wider"
        victim=self.root/"tampered-native-receipt"
        shutil.copytree(original,victim)
        file=victim/"solid"/"relatte-evidence.json"
        data=json.loads(file.read_text())
        signature=data["result"]["disposition_receipt"]["signing"]["signature"]
        data["result"]["disposition_receipt"]["signing"]["signature"]=(
            ("A" if signature[0]!="A" else "B")+signature[1:])
        file.write_text(json.dumps(data))
        with self.assertRaises(Hold):
            verify_branch(victim)

    def test_cli_plan_and_cold_verify(self):
        sketch_file=self.root/"root-source.json"
        plan_file=self.root/"plan.json"
        sketch_file.write_text(json.dumps(self.root_sketch))
        cli=[sys.executable,str(ROOT/"scripts/static-cad-goatnote.py")]
        proc=subprocess.run(cli+["plan","--source-sketch",str(sketch_file),
                                 "--out",str(plan_file)],
                            capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertEqual(json.loads(plan_file.read_text()),self.tree)
        proc=subprocess.run(cli+["verify","--out-dir",str(self.root/"pad-deeper")],
                            capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("COLD_NATIVE_GOATNOTE_RELATTE_CAD_VERIFIED",proc.stdout)
        second=subprocess.run(cli+["plan","--source-sketch",str(sketch_file),
                                   "--out",str(plan_file)],
                              capture_output=True,text=True)
        self.assertNotEqual(second.returncode,0)


if __name__=="__main__":
    unittest.main()
