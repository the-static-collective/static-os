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


    def test_elf_source_must_match_house(self):
        bad = copy.deepcopy(BASE)
        bad["elf"]["source_commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "match pinned HOUSE"):
            module.validate(bad)

    def test_refuse_elf_auto_execution_and_authority(self):
        for key, value in (("automatic", True), ("authority", "root"),
                           ("mode", "autostart"), ("producer", "openmanus")):
            with self.subTest(key=key):
                bad = copy.deepcopy(BASE)
                bad["elf"][key] = value
                with self.assertRaisesRegex(ValueError, "must not gain authority"):
                    module.validate(bad)

    def test_refuse_elf_guest_success_without_guest_evidence(self):
        bad = copy.deepcopy(BASE)
        bad["evidence"]["elf_offline_guest"] = "passed"
        with self.assertRaisesRegex(ValueError, "unverified gates"):
            module.validate(bad)

    def test_refuse_unearned_live_provider_claim(self):
        bad = copy.deepcopy(BASE)
        bad["evidence"]["openmanus_live"] = "passed"
        with self.assertRaisesRegex(ValueError, "live OpenManus"):
            module.validate(bad)

    def test_refuse_elf_executed_before_house(self):
        bad = copy.deepcopy(BASE)
        bad["stages"][2]["requires"] = []
        with self.assertRaisesRegex(ValueError, "HOUSE-dependent"):
            module.validate(bad)

    def test_guest_proof_script_is_manual_and_user_scoped(self):
        guest = ROOT / "config" / "includes.chroot" / "usr" / "local" / "bin" / "static-elf-proof"
        script = guest.read_text(encoding="utf-8")
        self.assertIn('if [ "$(id -u)" -eq 0 ]; then', script)
        self.assertIn("workbench-venv/bin/python", script)
        self.assertIn("elf_genesis demo", script)
        self.assertTrue(guest.is_file())


if __name__ == "__main__":
    unittest.main()
