import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-bardo-boot-witness.py"
SPEC = importlib.util.spec_from_file_location("validate_bbw001", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MANIFEST = MODULE.load(ROOT / "manifest" / "bardo-boot-witness-001.json")
FIXTURES = ROOT / "fixtures" / "bardo-boot-witness-001"


class BardoBootWitnessTests(unittest.TestCase):
    def test_committed_witness_validates(self):
        result = MODULE.validate(copy.deepcopy(MANIFEST), FIXTURES)
        self.assertTrue(result["claims"]["exact_byte_identity_preserved"])
        self.assertFalse(result["claims"]["physical_cold_boot_proven"])

    def mutated_fixture_dir(self, filename, mutate):
        temp = tempfile.TemporaryDirectory()
        dst = Path(temp.name)
        for source in FIXTURES.glob("*.json"):
            value = json.loads(source.read_text(encoding="utf-8"))
            if source.name == filename:
                mutate(value)
            (dst / source.name).write_text(json.dumps(value), encoding="utf-8")
        return temp, dst

    def test_refuses_hold_that_manufactures_admission(self):
        temp, fixtures = self.mutated_fixture_dir(
            "hold.json", lambda value: value["extensions"]["supabardo"].__setitem__("destination_disposition", "ADMIT")
        )
        with temp:
            with self.assertRaisesRegex(ValueError, "manufactured"):
                MODULE.validate(copy.deepcopy(MANIFEST), fixtures)

    def test_refuses_particular_hash_drift(self):
        temp, fixtures = self.mutated_fixture_dir(
            "evidence.json", lambda value: value["stages"][2].__setitem__("sha256", "0" * 64)
        )
        with temp:
            with self.assertRaisesRegex(ValueError, "particular changed"):
                MODULE.validate(copy.deepcopy(MANIFEST), fixtures)

    def test_refuses_authority_collapse(self):
        crossing = MODULE.load(FIXTURES / "crossing.json")
        temp, fixtures = self.mutated_fixture_dir(
            "admit.json", lambda value: value["signing"].__setitem__("public_key", crossing["signing"]["public_key"])
        )
        with temp:
            with self.assertRaisesRegex(ValueError, "authority domains collapsed"):
                MODULE.validate(copy.deepcopy(MANIFEST), fixtures)

    def test_refuses_physical_boot_claim_promotion(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["claims"]["physical_cold_boot_proven"] = True
        with self.assertRaisesRegex(ValueError, "silently promoted"):
            MODULE.validate(manifest, FIXTURES)

    def test_refuses_false_repository_byte_claim(self):
        manifest = copy.deepcopy(MANIFEST)
        manifest["source"]["bytes_vendored_in_repository"] = True
        with self.assertRaisesRegex(ValueError, "must not pretend"):
            MODULE.validate(manifest, FIXTURES)


if __name__ == "__main__":
    unittest.main()
