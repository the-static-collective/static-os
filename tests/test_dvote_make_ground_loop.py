import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "static_os_dvote_make_ground_loop",
    ROOT / "scripts" / "dvote_make_ground_loop.py",
)
loop = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(loop)

TAKE = json.loads((ROOT / "examples" / "dvote-make-ground.take.json").read_text(encoding="utf-8"))
HOLD = json.loads((ROOT / "examples" / "dvote-make-ground.hold.json").read_text(encoding="utf-8"))
PASS = json.loads((ROOT / "examples" / "dvote-make-ground.pass.json").read_text(encoding="utf-8"))
CANDIDATE = json.loads((ROOT / "examples" / "dvote-make-ground.independent-candidate.json").read_text(encoding="utf-8"))
FIELD = json.loads((ROOT / "examples" / "dvote-make-ground.field-profile.json").read_text(encoding="utf-8"))


class DvoteMakeGroundLoopTests(unittest.TestCase):
    def test_take_with_witness_is_only_contacting_disposition(self):
        result = loop.make_field_return(copy.deepcopy(TAKE))
        self.assertEqual(result["status"], "contacted")
        self.assertTrue(result["may_contact_nav"])

        held = loop.make_field_return(copy.deepcopy(HOLD))
        self.assertEqual(held["status"], "held")
        self.assertFalse(held["may_contact_nav"])

        passed = loop.make_field_return(copy.deepcopy(PASS))
        self.assertEqual(passed["status"], "passed")
        self.assertFalse(passed["may_contact_nav"])

    def test_take_without_witness_does_not_fake_world_contact(self):
        receipt = copy.deepcopy(TAKE)
        receipt["note"] = ""
        result = loop.make_field_return(receipt)
        self.assertEqual(result["status"], "awaiting_witness")
        self.assertFalse(result["may_contact_nav"])
        with self.assertRaisesRegex(ValueError, "only TAKE"):
            loop.make_nav_contact(receipt, result, "delta", "heading")

    def test_hold_and_pass_cannot_be_laundered_into_nav_contact(self):
        for receipt in (HOLD, PASS):
            result = loop.make_field_return(copy.deepcopy(receipt))
            with self.assertRaisesRegex(ValueError, "only TAKE"):
                loop.make_nav_contact(receipt, result, "delta", "heading")

    def test_full_take_loop_returns_candidate_edition_material(self):
        bundle = loop.run_loop(
            copy.deepcopy(TAKE),
            copy.deepcopy(CANDIDATE),
            copy.deepcopy(FIELD),
            "Changing representation exposed a new question in this witness, but that remains a self-report and may not reproduce.",
            "Compare the conditions under which a representation change does and does not expose a new question.",
            "Run paired Better Hole trials with explicit conditions before teaching the effect as if it were universal.",
        )
        self.assertEqual(bundle["nav_contact"]["status"], "contacted")
        self.assertEqual(bundle["world_receipt"]["claim_relation"], "contradicts")
        self.assertTrue(bundle["world_receipt"]["independence_claim_accepted"])
        self.assertFalse(bundle["world_recursion_receipt"]["counts_as_second_witness"])
        self.assertEqual(bundle["dogram_transition"]["status"], "proposed")
        self.assertEqual(bundle["nav_reorientation"]["status"], "proposed")
        self.assertEqual(bundle["edition_return"]["status"], "candidate_material")
        self.assertFalse(bundle["edition_return"]["automatic_book_edit"])
        self.assertEqual(
            bundle["edition_return"]["source"]["dvote_receipt_sha256"],
            loop.canonical_digest(TAKE),
        )

    def test_source_mutation_changes_crossing_identity(self):
        first = loop.make_field_return(copy.deepcopy(TAKE))
        changed = copy.deepcopy(TAKE)
        changed["note"] += " One more detail."
        second = loop.make_field_return(changed)
        self.assertNotEqual(first["source_sha256"], second["source_sha256"])


if __name__ == "__main__":
    unittest.main()
