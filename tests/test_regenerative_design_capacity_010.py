"""010 tests of real CAD signed evidence → inert economic design candidate.

The test workflow supplies one already-constructed native CAD-005 package.
This suite does not create an OCCT solid or sign a new reLATTE receipt.
"""
from __future__ import annotations
import copy
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from question_first.session import Hold
from question_first.design_capacity import export_candidate,verify_candidate

class RegenerativeDesignCapacity010(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get("STATIC_OS_CAD010_PACKAGE")
        if not path:
            raise unittest.SkipTest("dedicated native CAD 010 package required")
        cls.folder=Path(path).resolve()
        if not cls.folder.is_dir():
            raise RuntimeError("CAD 010 package is missing")

    def test_cold_export_verified_and_reconstructible(self):
        x=export_candidate(self.folder)
        self.assertEqual(x,verify_candidate(self.folder,x))
        self.assertEqual(x,export_candidate(self.folder))
        self.assertTrue(x["native_relatte"]["native_signatures_cold_verified"])
        self.assertEqual(x["native_relatte"]["disposition"],"HOLD")
        self.assertEqual(x["declared_capacity"]["fabricated_physical_units"],0)
        self.assertFalse(x["declared_capacity"]["legal_rights_verified"])
        self.assertFalse(x["declared_capacity"]["eligible_for_treasury_receipt"])
        self.assertEqual(len(x["artifacts"]),4)
        self.assertNotIn("receiver-key",json.dumps(x))
        self.assertNotIn("donor",json.dumps(x).lower())

    def test_changed_proposal_fields_cannot_verify_even_with_rehashed_candidate(self):
        x=export_candidate(self.folder)
        tampered=copy.deepcopy(x)
        tampered["declared_capacity"]["fabricated_physical_units"]=100
        from crank.runtime import digest
        body={k:v for k,v in tampered.items() if k!="candidate_id"}
        tampered["candidate_id"]="static-os-design-010:"+digest(body)
        with self.assertRaisesRegex(Hold,"CANDIDATE_NOT_CURRENT_SIGNED_SOURCE"):
            verify_candidate(self.folder,tampered)

    def test_mutated_step_cannot_be_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"copied"
            shutil.copytree(self.folder,dest)
            with (dest/"solid.step").open("ab") as f:
                f.write(b"\nTAMPERED-BY-010")
            with self.assertRaises(Hold):
                export_candidate(dest)

    def test_forged_native_signature_cannot_be_exported(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest=Path(tmp)/"copied"
            shutil.copytree(self.folder,dest)
            p=dest/"relatte-evidence.json"
            evidence=json.loads(p.read_text())
            signing=evidence["result"]["crossing"]["signing"]
            signed=signing["signature"]
            signing["signature"]=("A" if signed[0]!="A" else "B")+signed[1:]
            p.write_text(json.dumps(evidence))
            with self.assertRaises(Hold):
                export_candidate(dest)

    def test_wrong_family_and_missing_package_refuse(self):
        with self.assertRaises(Hold):
            export_candidate(self.folder,"PHYSICAL_MACHINE")
        with self.assertRaises(OSError):
            export_candidate(self.folder/"missing")

if __name__=="__main__":
    unittest.main()
