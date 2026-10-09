"""FABRICATION 013: real signed CAD/print/field gated, no physical authority."""
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
from question_first.session import Hold
from question_first.fabrication_request import request_from_original,verify_request

ROOT=Path(__file__).resolve().parents[1]
FLEET=json.loads((ROOT/"fixtures/printer-field-012/synthetic-fleet.json").read_text())
SELECTION=json.loads((ROOT/"fixtures/fabrication-013/three-node-selection.json").read_text())

class Pure(unittest.TestCase):
    def test_selection_is_only_three_node_proposal(self):
        self.assertEqual(len(SELECTION["requested_machine_ids"]),3)
        self.assertEqual(len(set(SELECTION["requested_machine_ids"])),3)
        self.assertEqual(SELECTION["authority_effect"],"PROPOSE_ONLY")

class SignedNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        src=os.environ.get("STATIC_OS_PRINT013_SOURCE")
        packet=os.environ.get("STATIC_OS_PRINT013_PACKET")
        if not src or not packet:raise unittest.SkipTest("original native signed source required")
        cls.source,cls.packet=Path(src),Path(packet)

    def test_original_source_reconstructs_exact_request(self):
        x=request_from_original(self.source,self.packet,FLEET,SELECTION)
        self.assertEqual(x,verify_request(self.source,self.packet,FLEET,SELECTION,x))
        self.assertEqual(x["requested_node_count"],3)
        self.assertEqual(x["fabrication_occurred"],False)
        self.assertEqual(x["owner_machine_grants_included"],False)
        self.assertEqual(x["physical_parts"],0)
        self.assertTrue(x["original_signed_cad_crossing_id"])
        self.assertEqual(x["selected_nodes"][0]["published_compatibility"],"HOLD_MACHINE_PROFILE")
        self.assertEqual(x["selected_nodes"][1]["published_compatibility"],"HOLD_PROCESS_ADAPTER")
        self.assertEqual(x["selected_nodes"][2]["published_compatibility"],"SOFTWARE_TOOLPATH_ONLY")

    def test_machine_permission_laundered_via_rehash_denied(self):
        x=request_from_original(self.source,self.packet,FLEET,SELECTION)
        forged=copy.deepcopy(x)
        forged["selected_nodes"][0]["physical_print_permission"]=True
        body={k:v for k,v in forged.items() if k!="request_id"}
        forged["request_id"]="static-os-fabrication-013:"+digest(body)
        with self.assertRaisesRegex(Hold,"SOURCE_OR_SELECTION_NOT_CURRENT"):
            verify_request(self.source,self.packet,FLEET,SELECTION,forged)

    def test_changed_human_selection_rejected(self):
        forged=copy.deepcopy(SELECTION)
        forged["authority_effect"]="EXECUTE_NOW"
        with self.assertRaisesRegex(Hold,"SELECTION_MUST_HAVE_EXPLICIT_OPERATOR_WITH_NO_AUTHORITY"):
            request_from_original(self.source,self.packet,FLEET,forged)

    def test_unadvertised_node_does_not_appear_as_discovered(self):
        forged=copy.deepcopy(SELECTION)
        forged["requested_machine_ids"][1]="a:never-advertised"
        with self.assertRaisesRegex(Hold,"NO_SILENT_MACHINE_DISCOVERY"):
            request_from_original(self.source,self.packet,FLEET,forged)

    def test_cli_proposal_is_once_only_and_cold_verifiable(self):
        args=["--source",str(self.source),"--packet",str(self.packet),
              "--fleet",str(ROOT/"fixtures/printer-field-012/synthetic-fleet.json"),
              "--selection",str(ROOT/"fixtures/fabrication-013/three-node-selection.json")]
        with tempfile.TemporaryDirectory() as t:
            file=Path(t)/"proposal.json"
            command=[sys.executable,str(ROOT/"scripts/static-fabrication-request.py")]
            p=subprocess.run(command+["propose",*args,"--out",str(file)],
                capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout)["physical_parts_created"],0)
            repeated=subprocess.run(command+["propose",*args,"--out",str(file)],
                capture_output=True,text=True)
            self.assertEqual(repeated.returncode,2)
            v=subprocess.run(command+["verify",*args,"--out",str(file)],
                capture_output=True,text=True)
            self.assertEqual(v.returncode,0,v.stderr)

if __name__=="__main__":unittest.main()
