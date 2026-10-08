from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ORACLE = ROOT / "vendor/eleven_heap_001"


class OracleImportTests(unittest.TestCase):
    def test_original_source_files_are_byte_preserved(self):
        manifest = json.loads((ROOT / "manifest/instrument-host-001.json").read_text())
        for filename, expected in manifest["oracle"]["sha256"].items():
            with self.subTest(filename=filename):
                self.assertEqual(sha256((ORACLE / filename).read_bytes()).hexdigest(), expected)

    def test_original_25_checks_and_33_tests_stay_runnable(self):
        tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
                               cwd=ORACLE, capture_output=True, timeout=30, check=True)
        self.assertIn("Ran 33 tests", tests.stderr.decode())
        with tempfile.TemporaryDirectory() as output:
            experiment = subprocess.run([sys.executable, "experiment.py", "--output", output],
                                        cwd=ORACLE, capture_output=True, timeout=30, check=True)
            self.assertIn("PASS (25 checks)", experiment.stdout.decode())
            result = json.loads((Path(output) / "experiment.json").read_text())
            self.assertEqual(len(result["checks"]), 25)
            self.assertTrue(all(check["passed"] for check in result["checks"]))

    def test_installed_entrypoint_and_generic_second_instrument(self):
        with tempfile.TemporaryDirectory() as temp:
            prefix, session = Path(temp) / "prefix", Path(temp) / "session"
            subprocess.run([sys.executable, "scripts/install-instrument-host.py", "--prefix", str(prefix)],
                           cwd=ROOT, capture_output=True, timeout=10, check=True)
            executable = prefix / "bin/static-instrument"
            proc = subprocess.run([str(executable), "demo", "--session", str(session)],
                                  capture_output=True, timeout=20, check=True)
            proof = json.loads(proc.stdout)
            self.assertTrue(proof["frequency_changes_selected_recorded_track"])
            self.assertFalse(proof["native_relatte"])
            self.assertFalse(proof["source_observe_select_attend_record"])
            self.assertFalse(proof["rf_emitted"])
            library = prefix / "lib/static-os/instrument-host"
            code = """import sys
from pathlib import Path
from instruments.host import InstrumentHost
from instruments.adapters import RecordedRadioAdapter
h=InstrumentHost(Path(sys.argv[1])); p=Path(sys.argv[2]); h.install(RecordedRadioAdapter(p,instrument_id='second'))
h.observe('second'); h.select('second'); assert len(h.discover()['instruments'])==2; h.close()
"""
            subprocess.run([sys.executable, "-c", code, str(session), str(library / "fixtures/instrument-host-001/two-stations.wav")],
                           cwd=library, capture_output=True, timeout=10, check=True)


if __name__ == "__main__":
    unittest.main()
