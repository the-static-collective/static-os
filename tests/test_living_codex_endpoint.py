import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest" / "living-codex-endpoint-001.json"


class LivingCodexEndpointManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text())

    def test_manifest_is_exact_pinned_integration_candidate(self):
        self.assertEqual(
            self.data["schema"],
            "static.living-codex-endpoint-manifest/v0",
        )
        self.assertEqual(self.data["id"], "LIVING-CODEX-ENDPOINT-001")
        self.assertEqual(self.data["status"], "integration-candidate")

        expected = {
            "relatte": "9b4b7be38e67c8e9c3e43328ef0a940c08f7f2ca",
            "roroomom": "5e93843ceae80a2bca94ff438f0bc24dc49a4b85",
            "tranchnode": "1d731fbb228f68bbefc008d18c48d6be001935be",
        }
        for name, sha in expected.items():
            with self.subTest(name=name):
                organ = self.data["organs"][name]
                self.assertEqual(organ["commit"], sha)
                self.assertRegex(organ["commit"], r"^[0-9a-f]{40}$")

    def test_manifest_preserves_noncollapse_laws(self):
        laws = set(self.data["laws"])
        required = {
            "TRANSPORT != AUTHORITY",
            "RECEIVED != ADMITTED",
            "HOLD != ADMIT",
            "FOREIGN CROSSING != LOCAL CONSEQUENCE",
            "HUMAN ACCEPTANCE REQUIRES LOCAL RE-CROSSING",
            "SHARED HISTORY != SHARED GLOBAL STATE",
            "REPLICATION != IDENTITY",
        }
        self.assertTrue(required.issubset(laws))

    def test_manifest_does_not_overclaim_endpoint_status(self):
        claims = set(self.data["claims_not_made"])
        self.assertIn("bootable ISO proof", claims)
        self.assertIn("USB hardware proof", claims)
        self.assertIn("network mesh discovery", claims)
        self.assertIn("global consensus", claims)

    def test_proof_sequence_contains_foreign_hold_then_local_admit(self):
        sequence = self.data["proof"]["sequence"]
        self.assertLess(
            sequence.index("house-b-foreign-hold"),
            sequence.index("house-b-human-local-recrossing"),
        )
        self.assertLess(
            sequence.index("house-b-human-local-recrossing"),
            sequence.index("house-b-local-admit"),
        )


if __name__ == "__main__":
    unittest.main()
