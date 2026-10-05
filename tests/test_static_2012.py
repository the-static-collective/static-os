import importlib.util, json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PROFILE=ROOT/"profiles"/"static-2012.json"
def mod(name,path):
    s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
validator=mod("static_2012_validation",ROOT/"scripts"/"validate-static-2012.py")
assessor=mod("static_2012_assessor",ROOT/"scripts"/"static-2012.py")

class Static2012Tests(unittest.TestCase):
    def data(self): return json.loads(PROFILE.read_text(encoding="utf-8"))
    def test_valid_core_is_green_local(self):
        d=self.data(); r=validator.validate(d); self.assertEqual(r["profile_id"],"STATIC-2012-001")
        caps={c["id"]:c for c in d["capabilities"]}
        for cid in d["core_sovereignty_capabilities"]:
            self.assertEqual(caps[cid]["class"],"GREEN"); self.assertTrue(caps[cid]["local"])
    def test_more_machine_requires_named_bottleneck(self):
        d=self.data()
        for c in d["capabilities"]:
            if c["class"]!="GREEN":
                self.assertTrue(c["bottleneck"]["resource"]); self.assertTrue(c["bottleneck"]["evidence"]); self.assertTrue(c["fallback"])
        blue=next(c for c in d["capabilities"] if c["class"]=="BLUE"); del blue["bottleneck"]
        with self.assertRaisesRegex(ValueError,"named bottleneck"): validator.validate(d)
    def test_core_no_gpu_or_post_sync_network(self):
        d=self.data(); self.assertFalse(d["target"]["gpu_required_for_core"]); self.assertFalse(d["target"]["network_required_after_sync"]); validator.validate(d)
    def test_reference_fixture_ready(self):
        r=assessor.assess(self.data(),{"architecture":"amd64","cpu_cores":2,"memory_mib":4096,"free_disk_gib":48})
        self.assertEqual(r["state"],"reference-ready"); self.assertTrue(r["core_local_possible"]); self.assertFalse(r["claims"]["physical_install_verified"])
    def test_comfortable_fixture(self):
        r=assessor.assess(self.data(),{"architecture":"amd64","cpu_cores":4,"memory_mib":8192,"free_disk_gib":120}); self.assertEqual(r["state"],"comfortable")
    def test_below_floor_honest(self):
        r=assessor.assess(self.data(),{"architecture":"amd64","cpu_cores":2,"memory_mib":2048,"free_disk_gib":120}); self.assertEqual(r["state"],"below-floor"); self.assertFalse(r["core_local_possible"])
    def test_clone_plan_core_full_optional_shallow(self):
        j="\n".join(assessor.clone_plan(self.data(),"/srv/static"))
        self.assertIn('git clone https://github.com/the-static-collective/reLATTE.git "/srv/static/reLATTE"',j)
        self.assertIn('git clone --depth=1 https://github.com/the-static-collective/the-haunted-toaster.git "/srv/static/the-haunted-toaster"',j)
        self.assertNotIn("--depth=1 https://github.com/the-static-collective/reLATTE.git",j)
if __name__=="__main__": unittest.main()
