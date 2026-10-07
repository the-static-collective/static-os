import importlib.util, json, unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts"/"validate-bardo-generality.py"
SPEC=importlib.util.spec_from_file_location("bardo_generality",SCRIPT)
MODULE=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(MODULE)
BASE=json.loads((ROOT/"manifest"/"bardo-generality-002.json").read_text())

def clone(): return json.loads(json.dumps(BASE))

class Tests(unittest.TestCase):
    def test_accepts_two_family_proof(self):
        self.assertEqual(MODULE.validate(clone())["status"],"second-family-proven-external")
    def test_refuses_same_family_collapse(self):
        v=clone(); v["specimens"]["sb002"]["family"]=v["specimens"]["sb001"]["family"]
        with self.assertRaisesRegex(ValueError,"different"): MODULE.validate(v)
    def test_refuses_keep_rewrite(self):
        v=clone(); v["specimens"]["sb002"]["destination_disposition"]="KEEP"
        with self.assertRaisesRegex(ValueError,"HOLD"): MODULE.validate(v)
    def test_refuses_render_authority(self):
        v=clone(); v["specimens"]["sb002"]["render_authority"]=True
        with self.assertRaisesRegex(ValueError,"render"): MODULE.validate(v)
    def test_refuses_auto_promotion(self):
        v=clone(); v["generality"]["extraction_gate"]="promoted"
        with self.assertRaisesRegex(ValueError,"promoted"): MODULE.validate(v)
    def test_refuses_persistent_bardo_nonclaim_flip(self):
        v=clone(); v["nonclaims"]["persistent_bardo_storage"]=True
        with self.assertRaisesRegex(ValueError,"nonclaim"): MODULE.validate(v)

if __name__=="__main__": unittest.main()
