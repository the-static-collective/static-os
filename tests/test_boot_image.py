import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("static_boot_image_manifest", ROOT / "scripts" / "validate-boot-image.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)
BASE = json.loads((ROOT / "manifest" / "genesis-boot-003.json").read_text())


class FirstBootImageTests(unittest.TestCase):
    def test_image_manifest_explicitly_holds_all_unearned_proofs(self):
        self.assertEqual(len(mod.validate(copy.deepcopy(BASE))["sources"]), 11)
        self.assertEqual(set(BASE["gate_status"].values()), {"UNVERIFIED"})
        self.assertTrue(BASE["claims"]["experimental_not_owner_canon"])

    def test_pins_refuse_mutable_branch_source_substitution(self):
        for index in (0, 1, 6, 10):
            changed = copy.deepcopy(BASE)
            changed["sources"][index]["commit"] = "main"
            with self.assertRaisesRegex(ValueError, "source pin"):
                mod.validate(changed)

    def test_refuses_remote_interface_and_automatic_execution(self):
        for key, value in [
            ("host", "0.0.0.0"), ("port", 80), ("start", "AUTOMATIC_INSTALL"),
            ("auto_execution", True), ("public_network", True)
        ]:
            changed = copy.deepcopy(BASE)
            changed["service"][key] = value
            with self.assertRaisesRegex(ValueError, "unsafe"):
                mod.validate(changed)

    def test_refuses_unearned_uefi_and_bios_boot_claims(self):
        for field in ("bios_vm_boot", "uefi_vm_boot", "offline_first_boot", "physical_hardware"):
            changed = copy.deepcopy(BASE)
            changed["gate_status"][field] = "PASSED"
            with self.assertRaisesRegex(ValueError, "separate evidence"):
                mod.validate(changed)

    def test_refuses_node_checksum_drift_or_version_drift(self):
        for key, val in [("sha256", "a"*64), ("version", "v26.0.0")]:
            changed = copy.deepcopy(BASE)
            changed["runtime"][key] = val
            with self.assertRaisesRegex(ValueError, "Node distribution"):
                mod.validate(changed)

    def test_image_source_and_user_launcher_have_no_auto_build(self):
        root = ROOT / "config" / "genesis-boot"
        start = (root / "static-genesis-start").read_text()
        launch = (root / "static-genesis-launch").read_text()
        unit = (root / "static-genesis.service").read_text()
        desktop = (root / "static-genesis.desktop").read_text()
        self.assertIn("127.0.0.1:8766/", launch)
        self.assertIn("--out-parent", start)
        self.assertIn("--warm-cannon", start)
        self.assertIn("NoNewPrivileges=true", unit)
        self.assertIn("ReadWritePaths=%h", unit)
        self.assertIn("Exec=/usr/local/bin/static-genesis-launch", desktop)
        for forbidden in ("npm install", "apt install", "mkfs.", "mount /dev", "curl https:"):
            self.assertNotIn(forbidden, start + launch)
        self.assertNotIn("--question", start)
        self.assertNotIn("house-compose", start)

    def test_staging_needs_explicit_source_pins_and_reviewed_runtime(self):
        s = (ROOT / "scripts" / "stage-genesis-boot.sh").read_text()
        self.assertIn("sha256sum -c -", s)
        self.assertIn("git -C \"$dest\" rev-parse HEAD", s)
        self.assertIn('"$NPM" ci --prefix', s)
        self.assertIn("--ignore-scripts", s)
        self.assertIn("/opt/static-os/genesis-sources/", s)

    def test_ci_vm_has_positive_marker_and_negative_claims(self):
        vm = (ROOT / "tests" / "vm-genesis-probe.py").read_text()
        self.assertIn("CROSS_BRANCH_NATIVE_COLD_REPLAY_VERIFIED", vm)
        self.assertIn("WARM_SOURCE_NATIVE_COLD_REPLAY_VERIFIED", vm)
        self.assertIn('== "NOT_WITNESSED"', vm)
        sh = (ROOT / "tests" / "vm-genesis-probe.sh").read_text()
        self.assertIn("STATIC-OS-GENESIS-BIOS-BOOT-VERIFIED", sh)
        self.assertIn("runuser -u user", sh)


if __name__ == "__main__":
    unittest.main()
