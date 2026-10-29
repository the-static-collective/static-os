"""Non-Debian image/source contracts: two real userlands, no fabricated BIOS proof."""
from pathlib import Path
import json
import unittest

ROOT = Path(__file__).resolve().parents[1]
YML = ROOT / ".github" / "workflows" / "genesis-boot-004-multidistro.yml"
DOCKER = ROOT / "config" / "multidistro" / "Dockerfile"
RUN = ROOT / "config" / "multidistro" / "run-genesis.sh"
STAGE = ROOT / "scripts" / "stage-genesis-portable.py"

class DistroTests(unittest.TestCase):
    def test_distinct_genuinely_non_debian_userspaces(self):
        workflow = YML.read_text()
        docker = DOCKER.read_text()
        self.assertIn("node:24-alpine", workflow)
        self.assertIn("fedora:43", workflow)
        self.assertIn("apk add --no-cache", docker)
        self.assertIn("dnf install -y", docker)
        self.assertIn("nodejs24-bin", docker)
        self.assertIn("USER 10001:10001", docker)
        self.assertIn("ENV HOME=", docker)

    def test_original_unmerged_histories_staged_not_main(self):
        stage = STAGE.read_text()
        manifest = json.loads((ROOT/"manifest/genesis-boot-003.json").read_text())
        self.assertEqual(len(manifest["sources"]), 11)
        self.assertIn('"fetch", "-q", "--depth=1", "origin", commit', stage)
        self.assertIn('"checkout", "-q", "--detach", commit', stage)
        self.assertIn("SOURCE_HEAD_DRIFT_", stage)
        self.assertIn("SOURCE_STAGING_TARGET_ALREADY_EXISTS", stage)
        self.assertNotIn("checkout main", stage)

    def test_no_container_auto_build_untrusted_network_or_actuation(self):
        docker = DOCKER.read_text()
        run = RUN.read_text()
        work = YML.read_text()
        self.assertIn("ENTRYPOINT", docker)
        self.assertIn("test-native", run)
        self.assertIn("--out-parent", run)
        self.assertIn("--warm-cannon", run)
        self.assertNotIn("house-compose", run)
        self.assertIn("--network none", work)
        self.assertIn("--read-only", work)
        self.assertIn("--cap-drop ALL", work)
        self.assertIn("physicalTestsCompleted", work)
        self.assertIn("oci-image.tar.gz.sha256", work)

    def test_distro_variants_are_not_called_bios_proofs(self):
        work = YML.read_text()
        self.assertIn("NOT BIOS/UEFI-booted ISO", work)
        self.assertNotIn("BIOS_VM_BOOT_AND_ORIGINAL_OFFLINE_SOURCE_EXECUTION_VERIFIED", work)

if __name__ == "__main__":
    unittest.main()
