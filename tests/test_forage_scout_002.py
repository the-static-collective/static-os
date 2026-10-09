"""FORAGE-002: genuine byte-binding to unreviewed FORAGE-001 lead and HOLD."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forage.ledger import Hold, assess, digest
from forage.scout import PHOTO, SCOUT, cold_replay, scout

ROOT = Path(__file__).resolve().parents[1]
LEAD = json.loads((ROOT / "fixtures/forage-001/owner-offered-stepper.json")
                  .read_text(encoding="utf-8"))
PNG = bytes.fromhex("89504e470d0a1a0a") + b"LOCAL-SYNTHETIC-PNG-FIXTURE-NOT-REAL-CAMERA"


def evidence(lead, blob=PNG):
    return {
        "schema": PHOTO,
        "lead_ref": lead["lead_ref"],
        "origin_role": "OPERATOR_SELECTED_LOCAL_IMAGE_UNVERIFIED",
        "original_bytes_sha256": hashlib.sha256(blob).hexdigest(),
        "original_byte_count": len(blob),
        "content_type": "image/png",
        "device_authenticated": False,
        "camera_capture_authenticated": False,
        "rights_inferred_from_photo": False,
        "hazards_screened_by_machine": False,
        "photo_included_in_receipt": False,
    }


class SourceBoundCamera(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "field-photo.png"
        self.path.write_bytes(PNG)
        self.lead = copy.deepcopy(LEAD)
        self.proof = evidence(self.lead)

    def tearDown(self):
        self.temp.cleanup()

    def compile(self):
        return scout(self.lead, self.proof, self.path)

    def test_photo_and_original_unreviewed_001_hold(self):
        x = self.compile()
        original = assess(self.lead)
        self.assertEqual(x["schema"], SCOUT)
        self.assertEqual(x["original_photo_sha256"],
                         hashlib.sha256(PNG).hexdigest())
        self.assertEqual(x["parent_foraging_assessment_id"],
                         original["assessment_id"])
        self.assertEqual(x["state"],
                         "DISCOVERED_UNREVIEWED_PHOTO_PROSPECT_HOLD")
        self.assertIn("NO_SCOPED_AUTHORITY_REVIEW",
                      x["parent_foraging_reason_codes"])
        self.assertFalse(x["image_classifier_executed"])
        self.assertFalse(x["authority_for_entry_or_removal"])
        self.assertFalse(x["human_permission_review_completed"])
        self.assertFalse(x["physical_item_retrieved"])
        self.assertEqual(x["robot_garden_inventory_delta"], 0)
        self.assertEqual(x["jubilee_treasury_inventory_delta"], 0)
        self.assertEqual(x["candidate_affordances"], [
            "Bracket or fixture candidate", "Motor/drive research",
            "Fastener recovery check"])
        self.assertEqual(x, cold_replay(self.lead, self.proof, self.path, x))

    def test_mutating_original_photo_or_evidence_denied(self):
        old = self.compile()
        self.path.write_bytes(PNG + b"x")
        with self.assertRaisesRegex(Hold, "PHOTO_FILE_OR_EVIDENCE_CHANGED"):
            cold_replay(self.lead, self.proof, self.path, old)
        self.path.write_bytes(PNG)
        self.proof["original_bytes_sha256"] = "a" * 64
        with self.assertRaisesRegex(Hold, "PHOTO_FILE_OR_EVIDENCE_CHANGED"):
            self.compile()

    def test_camera_and_rights_laundering_denied(self):
        for field in ("device_authenticated", "camera_capture_authenticated",
                      "rights_inferred_from_photo", "hazards_screened_by_machine",
                      "photo_included_in_receipt"):
            with self.subTest(field=field):
                forged = copy.deepcopy(self.proof)
                forged[field] = True
                with self.assertRaisesRegex(Hold, "PHOTO_CANNOT_MINT_PHYSICAL_OR_LEGAL_AUTHORITY"):
                    scout(self.lead, forged, self.path)

    def test_source_lead_mutation_and_rehashed_results_fail(self):
        original = self.compile()
        self.lead["source_kind"] = "PRIVATE_GROUND"
        with self.assertRaisesRegex(Hold, "SCOUT_ORIGINAL_PHOTO_COLD_REPLAY_DISAGREEMENT"):
            cold_replay(self.lead, self.proof, self.path, original)
        self.lead["source_kind"] = LEAD["source_kind"]
        for field, value in (
            ("authority_for_entry_or_removal", True),
            ("image_classifier_executed", True),
            ("human_permission_review_completed", True),
            ("physical_item_retrieved", True),
            ("robot_or_printer_activated", True),
            ("robot_garden_inventory_delta", 1),
            ("jubilee_treasury_inventory_delta", 1),
        ):
            with self.subTest(field=field):
                forged = copy.deepcopy(original)
                forged[field] = value
                forged["scout_id"] = "static-os-forage-scout-002:" + digest(
                    {k: v for k, v in forged.items() if k != "scout_id"})
                with self.assertRaisesRegex(Hold, "SCOUT_ORIGINAL_PHOTO_COLD_REPLAY_DISAGREEMENT"):
                    cold_replay(self.lead, self.proof, self.path, forged)

    def test_lead_evidence_identity_must_match(self):
        forged = copy.deepcopy(self.proof)
        forged["lead_ref"] = "scout:another"
        with self.assertRaisesRegex(Hold, "PHOTO_CANNOT_MINT_PHYSICAL_OR_LEGAL_AUTHORITY"):
            scout(self.lead, forged, self.path)

    def test_invalid_image_type_bounded_and_symlink_denied(self):
        self.path.write_bytes(b"GIF89a" + bytes(100))
        with self.assertRaisesRegex(Hold, "JPEG_OR_PNG_ONLY"):
            self.compile()
        self.path.write_bytes(b"x" * 12)
        with self.assertRaisesRegex(Hold, "JPEG_OR_PNG_ONLY"):
            self.compile()
        self.path.write_bytes(PNG)
        link = Path(self.temp.name) / "symbolic-photo.png"
        link.symlink_to(self.path)
        with self.assertRaisesRegex(Hold, "LOCAL_ORIGINAL_PHOTO_FILE_REQUIRED"):
            scout(self.lead, self.proof, link)

    def test_curbside_not_a_permission_even_with_photo(self):
        lead = json.loads((ROOT / "fixtures/forage-001/curbside-laptop-lead.json")
                          .read_text())
        record = scout(lead, evidence(lead), self.path)
        self.assertIn("DISCARD_OR_LOCATION_DOES_NOT_ESTABLISH_TITLE",
                      record["parent_foraging_reason_codes"])
        self.assertIn("SPECIALIST_OR_PHYSICAL_SAFETY_CHECK_REQUIRED",
                      record["parent_foraging_reason_codes"])
        self.assertFalse(record["authority_for_entry_or_removal"])

    def test_hazards_and_plant_collection_not_inferred_from_pixels(self):
        lead = json.loads((ROOT / "fixtures/forage-001/blm-pinyon-lead.json")
                          .read_text())
        x = scout(lead, evidence(lead), self.path)
        self.assertIn("LOCAL_LAND_RULES_SPECIES_QUANTITY_CLOSURES_MUST_BE_CHECKED",
                      x["parent_foraging_reason_codes"])
        self.assertTrue(x["hazards_not_independently_screened"])

    def test_cli_first_write_and_replay_after_photo_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lead_file = root / "lead.json"
            proof_file = root / "evidence.json"
            out = root / "receipt.json"
            lead_file.write_text(json.dumps(self.lead))
            proof_file.write_text(json.dumps(self.proof))
            command = [sys.executable, str(ROOT / "scripts/static-forage-scout.py")]
            flags = ["--lead", str(lead_file), "--photo-evidence", str(proof_file),
                     "--photo", str(self.path), "--out", str(out)]
            def run(action):
                return subprocess.run(command + [action] + flags,
                                      capture_output=True, text=True)
            first = run("receive")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertFalse(json.loads(first.stdout)["permission_review_completed"])
            self.assertEqual(run("receive").returncode, 2)
            self.assertEqual(run("verify").returncode, 0)
            body = json.loads(out.read_text())
            body["robot_garden_inventory_delta"] = 5
            out.write_text(json.dumps(body))
            self.assertEqual(run("verify").returncode, 2)


if __name__ == "__main__":
    unittest.main()
