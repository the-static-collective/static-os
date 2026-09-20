import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("flight003", ROOT / "scripts/validate-flight-003.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
VALUE = json.loads((ROOT / "interop/flight-003.json").read_text(encoding="utf-8"))
GENESIS = json.loads((ROOT / "manifest/genesis-001.json").read_text(encoding="utf-8"))
TRIAD = json.loads((ROOT / "interop/triad-001.json").read_text(encoding="utf-8"))


class Flight003Tests(unittest.TestCase):
    def check(self, candidate=None, genesis=None, triad=None):
        return module.validate(
            copy.deepcopy(candidate if candidate is not None else VALUE),
            copy.deepcopy(genesis if genesis is not None else GENESIS),
            copy.deepcopy(triad if triad is not None else TRIAD))

    def test_exact_reconciled_candidate(self):
        self.assertEqual(self.check()["status"], "contract-candidate")

    def test_refuses_mismatched_house_pin(self):
        bad = copy.deepcopy(VALUE)
        bad["sources"][0]["commit"] = "0" * 40
        with self.assertRaisesRegex(ValueError, "pinned identically"):
            self.check(candidate=bad)

    def test_refuses_packaging_storyship_without_own_gate(self):
        bad = copy.deepcopy(VALUE)
        bad["sources"][1]["image_status"] = "installed"
        with self.assertRaisesRegex(ValueError, "packaging/authority"):
            self.check(candidate=bad)

    def test_refuses_packaging_tranchnode_without_own_gate(self):
        bad = copy.deepcopy(VALUE)
        bad["sources"][2]["image_status"] = "installed"
        with self.assertRaisesRegex(ValueError, "packaging/authority"):
            self.check(candidate=bad)

    def test_refuses_unwitnessed_boot(self):
        bad = copy.deepcopy(VALUE)
        bad["claims"]["vm_boot"] = "passed"
        with self.assertRaisesRegex(ValueError, "unearned"):
            self.check(candidate=bad)

    def test_refuses_automatic_upgrade(self):
        bad = copy.deepcopy(VALUE)
        bad["claims"]["automatic_upgrade"] = True
        with self.assertRaisesRegex(ValueError, "unearned"):
            self.check(candidate=bad)

    def test_refuses_host_execution_and_extra_services(self):
        bad = copy.deepcopy(VALUE)
        bad["boundary"]["run_untrusted_commands"] = True
        with self.assertRaisesRegex(ValueError, "effect or admission"):
            self.check(candidate=bad)

    def test_refuses_elf_pin_drift(self):
        bad = copy.deepcopy(GENESIS)
        bad["elf"]["source_commit"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "HOUSE/ELF"):
            self.check(genesis=bad)

    def test_refuses_triads_with_different_workbench(self):
        bad = copy.deepcopy(TRIAD)
        bad["sources"][2]["commit"] = "f" * 40
        with self.assertRaisesRegex(ValueError, "pinned identically"):
            self.check(triad=bad)


if __name__ == "__main__":
    unittest.main()
