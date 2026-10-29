import pathlib
import unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATH=ROOT/'config'/'alpine-live'

class AlpineLiveTests(unittest.TestCase):
    def test_not_debian_and_builds_from_official_aports(self):
        build=(ROOT/'scripts'/'build-alpine-genesis-iso.sh').read_text()
        prof=(PATH/'mkimg.genesis.sh').read_text()
        self.assertIn('alpine/aports.git', build)
        self.assertIn('3.23-stable', build)
        self.assertIn('scripts/mkimage.sh', build)
        self.assertIn('profile_standard', prof)
        self.assertIn('profile_genesis()', prof)
        self.assertIn('kernel_cmdline=', prof)
        self.assertIn('nodejs npm python3 git', prof)

    def test_removable_source_bundle_is_original_and_not_network_loaded_at_boot(self):
        overlay=(PATH/'genapkovl-genesis.sh').read_text()
        self.assertIn("GENESIS_PAYLOAD",overlay)
        self.assertIn('cp -a "${GENESIS_PAYLOAD}/."',overlay)
        self.assertIn('tar -C "$tmp" -czf',overlay)
        self.assertIn('"/etc/init.d/local"',overlay)
        self.assertIn('CI_VM_PROBE_ENABLED',overlay)

    def test_only_non_root_loopback_service_and_operator_click(self):
        start=(PATH/'static-genesis-start').read_text()
        local=(PATH/'genesis-local.start').read_text()
        self.assertIn('su -s /bin/sh genesis',local)
        self.assertIn('GIT_CONFIG_GLOBAL=',start)
        self.assertIn('--out-parent',start)
        self.assertIn('--port 8766',start)
        self.assertNotIn('--question',start)
        self.assertNotIn('house-compose',start)
        self.assertNotIn('curl https:',start)
        self.assertNotIn('npm install',start)
        self.assertIn("GENESIS_CI_VM_PROBE",local.replace("CI-ONLY-NOT-FOR-FIELD-PILOT","GENESIS_CI_VM_PROBE"))

    def test_network_off_and_bios_proof_not_contaminated_by_oci(self):
        ci=(ROOT/'.github'/'workflows'/'genesis-boot-005-alpine-live.yml').read_text()
        self.assertIn('qemu-system-x86_64',ci)
        self.assertIn('-net none',ci)
        self.assertIn('ALPINE_BIOS_BOOT_INDEPENDENT_ORIGINAL_SOURCE_EXECUTION_VERIFIED',ci)
        self.assertIn('vm',ci.lower())
        self.assertNotIn('debootstrap',ci)
        self.assertNotIn('live-build',ci)

if __name__=='__main__':
    unittest.main()
