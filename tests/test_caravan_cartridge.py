import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location("cartridge", Path(__file__).resolve().parents[1] / "scripts/caravan-cartridge.py")
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)

class Cartridge(unittest.TestCase):
    def test_mission(self):
        p = c.mission(["radio", "library"])
        self.assertEqual(p["suggested_capabilities"], ["airwaves","crossing","library","seed","voice"])
        self.assertEqual(p["activation"], "EXPLICIT_LOCAL_OPERATOR")
        self.assertEqual(p["boot_proof"], "NOT_ESTABLISHED")

    def test_invalid_mission(self):
        for v in ([], ["church","church"], ["root"]):
            with self.assertRaises(ValueError): c.mission(v)

    def test_pin_and_staging(self):
        src = Path(os.environ["CARAVAN_TEST_SOURCE"])
        self.assertEqual(len(c.verify(src)), 21)
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "payload"
            self.assertEqual(c.stage(src,target), 21)
            with self.assertRaises(FileExistsError): c.stage(src,target)
            (target / "caravan.py").write_text("tampered")
            with self.assertRaises(ValueError): c.verify(target)

    def test_manifest_and_symlink(self):
        src = Path(os.environ["CARAVAN_TEST_SOURCE"])
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "payload"
            c.stage(src,target)
            (target / "voice.py").unlink()
            (target / "voice.py").symlink_to(src / "voice.py")
            with self.assertRaises(ValueError): c.verify(target)
            (target / "SOURCE-SHA256.json").write_text("{}")
            with self.assertRaises(ValueError): c.verify(target)

if __name__ == "__main__":
    unittest.main()
