import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("static_os_manifest", ROOT / "scripts" / "validate-manifest.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
BASE = json.loads((ROOT / "manifest" / "genesis-001.json").read_text(encoding="utf-8"))


class GenesisManifestTests(unittest.TestCase):
    def test_candidate_contract(self):
        self.assertEqual(module.validate(copy.deepcopy(BASE))["status"], "build-candidate")

    def test_refuse_mutable_house_ref(self):
        bad = copy.deepcopy(BASE)
        bad["house"]["commit"] = "main"
        with self.assertRaisesRegex(ValueError, "exact 40-hex"):
            module.validate(bad)

    def test_refuse_network_exposure(self):
        bad = copy.deepcopy(BASE)
        bad["house"]["bind_host"] = "0.0.0.0"
        with self.assertRaisesRegex(ValueError, "loopback"):
            module.validate(bad)

    def test_refuse_unapproved_admission(self):
        bad = copy.deepcopy(BASE)
        bad["admission"]["automatic"] = True
        with self.assertRaisesRegex(ValueError, "not automatic"):
            module.validate(bad)

    def test_refuse_forward_dependency(self):
        bad = copy.deepcopy(BASE)
        bad["stages"][0]["requires"] = ["house"]
        with self.assertRaisesRegex(ValueError, "unknown, forward or cyclic"):
            module.validate(bad)

    def test_refuse_unearned_boot_claim(self):
        bad = copy.deepcopy(BASE)
        bad["evidence"]["vm_boot"] = "passed"
        with self.assertRaisesRegex(ValueError, "unverified gates"):
            module.validate(bad)

    def test_refuse_enabled_installer(self):
        bad = copy.deepcopy(BASE)
        bad["base"]["installer"] = True
        with self.assertRaisesRegex(ValueError, "installer"):
            module.validate(bad)


if __name__ == "__main__":
    unittest.main()
