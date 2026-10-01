import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "manifest" / "roadkit-001.json"


class RoadKitManifestTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(MANIFEST.read_text())

    def test_exact_parent_and_donor_pins(self):
        self.assertEqual(self.data["schema"], "static.roadkit-manifest/v0")
        self.assertEqual(self.data["id"], "ROADKIT-001")
        self.assertEqual(
            self.data["parent"]["commit"],
            "fa72a854867ecde431d59896dc0725f957faa0af",
        )
        self.assertEqual(
            self.data["organs"]["relatte"]["commit"],
            "9b4b7be38e67c8e9c3e43328ef0a940c08f7f2ca",
        )
        self.assertEqual(
            self.data["organs"]["tranchnode"]["commit"],
            "1d731fbb228f68bbefc008d18c48d6be001935be",
        )

    def test_both_deployment_roads_are_declared(self):
        roads = self.data["roads"]
        self.assertEqual(roads["removable_file"]["transport"], "relatte.file-bundle")
        self.assertEqual(roads["lan_http"]["transport"], "relatte.http-relay")
        self.assertEqual(roads["lan_http"]["discovery"], "manual-peer-address")
        self.assertFalse(roads["lan_http"]["encryption"])

    def test_noncollapse_laws_are_frozen(self):
        required = {
            "TRANSPORT != AUTHORITY",
            "RECEIVED != ADMITTED",
            "PULLED != ADMITTED",
            "HOLD != ADMIT",
            "FOREIGN CROSSING != LOCAL CONSEQUENCE",
            "HUMAN ACCEPTANCE REQUIRES LOCAL RE-CROSSING",
            "SOURCE ADMIT != RECEIVER ADMIT",
            "SHARED HISTORY != SHARED GLOBAL STATE",
            "PEER ADDRESS != PEER IDENTITY",
        }
        self.assertTrue(required.issubset(set(self.data["laws"])))

    def test_hardware_and_network_claims_remain_bounded(self):
        claims = set(self.data["claims_not_made"])
        self.assertIn("physical removable-drive hardware proof", claims)
        self.assertIn("two-installed-machine proof", claims)
        self.assertIn("encrypted LAN transport", claims)
        self.assertIn("automatic peer discovery", claims)
        self.assertIn("authenticated network peer identity", claims)


if __name__ == "__main__":
    unittest.main()
