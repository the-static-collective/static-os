import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("static_os_triad", ROOT / "scripts" / "validate-triad.py")
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
BASE = json.loads((ROOT / "interop" / "triad-001.json").read_text(encoding="utf-8"))


class TriadContractTests(unittest.TestCase):
    def test_reference_only_candidate(self):
        self.assertEqual(module.validate(copy.deepcopy(BASE))["status"], "contract-only")

    def refuse(self, path, value, reason):
        bad = copy.deepcopy(BASE)
        node = bad
        for part in path[:-1]:
            node = node[part]
        node[path[-1]] = value
        with self.assertRaisesRegex(ValueError, reason):
            module.validate(bad)

    def test_refuse_mutable_upstream_source(self):
        self.refuse(("sources", 0, "commit"), "main", "pinned SHA")

    def test_refuse_unreviewed_act(self):
        self.refuse(("handoffs", 0, "review"), "automatic", "handoff")

    def test_refuse_authority_transfer(self):
        self.refuse(("handoffs", 0, "authority"), "action-warrant", "handoff")

    def test_refuse_claimed_adapter(self):
        self.refuse(("handoffs", 0, "implementation"), "complete", "handoff")

    def test_refuse_unearned_boot(self):
        self.refuse(("evidence", "vmBoot"), "passed", "unearned")

    def test_refuse_image_inclusion(self):
        self.refuse(("genesis", "isoInclusion"), True, "no boot claim")

    def test_refuse_host_effect(self):
        self.refuse(("deployment", "allowHostEffects"), True, "no new services")

    def test_refuse_shadow_capability_field(self):
        bad = copy.deepcopy(BASE)
        bad["handoffs"][0]["operationInput"] = {"command": "anything"}
        with self.assertRaisesRegex(ValueError, "unexpected/missing keys"):
            module.validate(bad)


if __name__ == "__main__":
    unittest.main()
