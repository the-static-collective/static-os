import json
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specimens" / "open-page-001" / "manifest.json"
VALIDATOR = ROOT / "scripts" / "validate-open-page.py"


class OpenPage001Tests(unittest.TestCase):
    def test_validator_accepts_pinned_specimen(self):
        completed = subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        self.assertIn("OPEN-PAGE-SPECIMEN-001: PASS", completed.stdout)

    def test_source_particulars_remain_distinct(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        sources = data["particulars"]
        self.assertNotEqual(sources[0]["sha256"], sources[1]["sha256"])
        self.assertNotEqual(sources[0]["role"], sources[1]["role"])

    def test_mythic_echo_is_not_historical_claim(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        mythic = data["presentation"]["mythic_echo"]
        self.assertEqual(mythic["mode"], "artistic")
        self.assertFalse(mythic["historical_claim"])

    def test_selection_remains_human(self):
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(data["selection"]["authority"], "human")


if __name__ == "__main__":
    unittest.main()
