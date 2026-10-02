import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class GhotPinTests(unittest.TestCase):
    def test_ghot_manifest_matches_genesis_house_pin(self):
        genesis = json.loads((ROOT / "manifest" / "genesis-001.json").read_text(encoding="utf-8"))
        ghot = json.loads((ROOT / "manifest" / "ghot-idle-operator-001.json").read_text(encoding="utf-8"))
        self.assertEqual(ghot["workbench"]["commit"], genesis["house"]["commit"])
        self.assertEqual(genesis["house"]["commit"], genesis["elf"]["source_commit"])
        self.assertEqual(ghot["workbench"]["default_view"], "ghot")

    def test_polsia_remains_held_and_uncredentialed(self):
        ghot = json.loads((ROOT / "manifest" / "ghot-idle-operator-001.json").read_text(encoding="utf-8"))
        specimen = ghot["staticjack"]["polsia"]
        self.assertEqual(specimen["status"], "HELD")
        self.assertFalse(specimen["credentials"])
        self.assertEqual(specimen["authority"], "none")
        self.assertIsNone(specimen["budget"])


if __name__ == "__main__":
    unittest.main()
