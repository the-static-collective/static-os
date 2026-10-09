"""FORAGE-001: hostile authority/custody/property and actual local CLI replay."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from forage.ledger import (
    Hold, assess, cold_verify, digest, journal_handoff, validate_lead,
    validate_review,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "fixtures/forage-001"


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class FieldReview(unittest.TestCase):
    def setUp(self):
        self.offered = load("owner-offered-stepper.json")
        self.review = load("owner-stepper-human-review.json")

    def test_unknown_owner_offer_is_held_until_review(self):
        a = assess(self.offered)
        self.assertEqual(a["status"], "HOLD_AND_RESEARCH")
        self.assertIn("NO_SCOPED_AUTHORITY_REVIEW", a["reason_codes"])
        self.assertFalse(a["permission_legally_verified_by_software"])
        self.assertEqual(a["physical_inventory_delta"], 0)
        self.assertFalse(a["robots_can_use_this_material"])

    def test_direct_owner_scope_is_only_a_human_reviewed_proposal(self):
        a = assess(self.offered, self.review)
        self.assertEqual(a["status"], "HUMAN_REVIEWED_PICKUP_PROPOSAL_ONLY")
        self.assertEqual(a["reason_codes"], [])
        self.assertFalse(a["retrieval_or_entry_executed"])
        self.assertFalse(a["permission_legally_verified_by_software"])
        self.assertEqual(a, cold_verify(self.offered, self.review, a))

    def test_physical_handoff_is_only_an_operator_report(self):
        assessment = assess(self.offered, self.review)
        pickup = load("owner-stepper-operator-pickup.json")
        pickup["assessment_id"] = assessment["assessment_id"]
        handoff = journal_handoff(self.offered, self.review, pickup)
        self.assertEqual(handoff["state"],
                         "OPERATOR_REPORTED_HANDOFF_NOT_INDEPENDENTLY_ATTESTED")
        self.assertTrue(handoff["physical_receipt_operator_reported"])
        self.assertFalse(handoff["verified_source_title"])
        self.assertFalse(handoff["verified_legal_permission"])
        self.assertFalse(handoff["robot_garden_part_admitted"])
        self.assertFalse(handoff["physical_quality_inspected"])
        self.assertEqual(handoff["jubilee_treasury_inventory_delta"], 0)
        self.assertEqual(handoff, cold_verify(
            self.offered, self.review, handoff, pickup))

    def test_handoff_never_auto_transmutes_into_authority(self):
        a = assess(self.offered, self.review)
        pickup = load("owner-stepper-operator-pickup.json")
        pickup["assessment_id"] = a["assessment_id"]
        receipt = journal_handoff(self.offered, self.review, pickup)
        forged = copy.deepcopy(receipt)
        forged["verified_legal_permission"] = True
        forged["robot_garden_part_admitted"] = True
        forged["jubilee_treasury_inventory_delta"] = 1
        body = {k: v for k, v in forged.items() if k != "handoff_id"}
        forged["handoff_id"] = "static-os-forage-handoff-001:" + digest(body)
        with self.assertRaisesRegex(Hold, "COLD_REPLAY_SOURCE_DISAGREEMENT"):
            cold_verify(self.offered, self.review, forged, pickup)

    def test_rehashed_pickup_with_unverified_title_is_denied(self):
        a = assess(self.offered, self.review)
        pickup = load("owner-stepper-operator-pickup.json")
        pickup["assessment_id"] = a["assessment_id"]
        pickup["site_owner_rights_verified_by_software"] = True
        with self.assertRaisesRegex(Hold, "PICKUP_HUMAN_CLAIM_MUST_STAY_IN_REVIEWED_SCOPE"):
            journal_handoff(self.offered, self.review, pickup)

    def test_unexpected_or_untrusted_rights_fields_rejected(self):
        lead = copy.deepcopy(self.offered)
        lead["this_is_free_take_it"] = True
        with self.assertRaisesRegex(Hold, "LEAD_EXACT_FIELDS_REQUIRED"):
            assess(lead, self.review)
        lead = copy.deepcopy(self.offered)
        lead["operator_claim_of_ownership"] = True
        with self.assertRaisesRegex(Hold, "INVALID_LEAD_OR_UNEARNED_OWNERSHIP"):
            assess(lead, self.review)
        review = copy.deepcopy(self.review)
        review["evidence_authenticated_by_software"] = True
        with self.assertRaisesRegex(Hold, "INVALID_REVIEW_OR_UNEARNED_AUTHENTICATION"):
            assess(self.offered, review)

    def test_wrong_site_quantity_and_purpose_do_not_make_grants(self):
        for field, value in (("site_ref", "fixture:wrong-site"),
                             ("max_amount", 0),
                             ("purpose", "COMMERCIAL"),
                             ("valid_until", "2026-01-01")):
            with self.subTest(field=field):
                fake = copy.deepcopy(self.review)
                fake["scope"][field] = value
                with self.assertRaisesRegex(Hold, "PERMISSION_SCOPE_DATE_QUANTITY_USE_OR_SITE_MISMATCH"):
                    assess(self.offered, fake)

    def test_deny_or_no_entry_grant_does_not_enable_pickup(self):
        for field, value in (("decision", "DECLINE"),
                             ("entry_and_removal_checked_by_human", False),
                             ("site_and_species_rules_checked_by_human", False),
                             ("hazard_review_by_human", "UNKNOWN"),
                             ("basis", "SITE_SPECIFIC_PUBLIC_RULE")):
            with self.subTest(field=field):
                edited = copy.deepcopy(self.review)
                edited[field] = value
                a = assess(self.offered, edited)
                self.assertEqual(a["status"], "HOLD_AND_RESEARCH")
                self.assertGreater(len(a["reason_codes"]), 0)

    def test_curbsides_do_not_automatically_convey_title(self):
        x = assess(load("curbside-laptop-lead.json"))
        self.assertIn("DISCARD_OR_LOCATION_DOES_NOT_ESTABLISH_TITLE", x["reason_codes"])
        self.assertIn("SPECIALIST_OR_PHYSICAL_SAFETY_CHECK_REQUIRED", x["reason_codes"])
        self.assertFalse(x["robots_can_use_this_material"])
        false_owner = copy.deepcopy(self.review)
        false_owner["lead_ref"] = "fixture:curbside-laptop-001"
        false_owner["scope"]["site_ref"] = "fixture:street-location-undisclosed"
        false_owner["scope"]["item_ref"] = "fixture:laptop-001"
        assert assess(load("curbside-laptop-lead.json"), false_owner)["status"] == "HOLD_AND_RESEARCH"

    def test_public_land_requires_local_rule_or_manager_not_private_owner_grant(self):
        blm = load("blm-pinyon-lead.json")
        x = assess(blm)
        self.assertEqual(x["status"], "HOLD_AND_RESEARCH")
        self.assertIn("LOCAL_LAND_RULES_SPECIES_QUANTITY_CLOSURES_MUST_BE_CHECKED",
                      x["reason_codes"])
        false_owner = copy.deepcopy(self.review)
        false_owner["lead_ref"] = blm["lead_ref"]
        false_owner["scope"]["site_ref"] = blm["site_ref"]
        false_owner["scope"]["item_ref"] = blm["item_ref"]
        false_owner["scope"]["unit"] = "POUND"
        false_owner["scope"]["purpose"] = "PERSONAL_NONCOMMERCIAL"
        x = assess(blm, false_owner)
        self.assertIn("AUTHORITY_BASIS_DOES_NOT_MATCH_SOURCE_STEWARD",
                      x["reason_codes"])

    def test_special_land_cannot_become_general_free_pickup(self):
        blm = load("blm-pinyon-lead.json")
        blm["land_class"] = "STATE_TRUST"
        human = copy.deepcopy(self.review)
        human["lead_ref"] = blm["lead_ref"]
        human["scope"]["site_ref"] = blm["site_ref"]
        human["scope"]["item_ref"] = blm["item_ref"]
        human["scope"]["unit"] = "POUND"
        human["scope"]["purpose"] = "PERSONAL_NONCOMMERCIAL"
        human["authority_kind"] = "LAND_MANAGER"
        human["basis"] = "SITE_SPECIFIC_PUBLIC_RULE"
        x = assess(blm, human)
        self.assertIn("SPECIAL_LAND_NEEDS_SPECIFIC_WRITTEN_PERMISSION",
                      x["reason_codes"])

    def test_no_damaged_battery_protected_artifacts_or_locked_access(self):
        for name, expected in (
            ("locked-e-waste-lead.json", "STOP_LOCKED_CONTAINER"),
            ("swollen-battery-lead.json", "STOP_DAMAGED_LITHIUM")):
            with self.subTest(name=name):
                lead = load(name)
                x = assess(lead)
                self.assertIn(expected, x["reason_codes"])
                fake = copy.deepcopy(self.review)
                fake["lead_ref"] = lead["lead_ref"]
                fake["scope"]["site_ref"] = lead["site_ref"]
                fake["scope"]["item_ref"] = lead["item_ref"]
                self.assertEqual(assess(lead, fake)["status"], "HOLD_AND_RESEARCH")

    def test_unidentified_food_and_cultural_artifacts_are_hard_holds(self):
        for category, hazard in (("FOOD", "UNIDENTIFIED_EDIBLE"),
                                 ("MINERAL", "CULTURAL_ARTIFACT"),
                                 ("BOTANICAL", "PROTECTED_SPECIES")):
            with self.subTest(hazard=hazard):
                lead = copy.deepcopy(self.offered)
                lead["category"] = category
                lead["hazards"] = [hazard]
                a = assess(lead, self.review)
                self.assertIn("STOP_" + hazard, a["reason_codes"])

    def test_past_scope_rejects_alleged_later_pickup(self):
        assessment = assess(self.offered, self.review)
        pickup = load("owner-stepper-operator-pickup.json")
        pickup["assessment_id"] = assessment["assessment_id"]
        pickup["reported_date"] = "2026-12-01"
        with self.assertRaisesRegex(Hold, "PICKUP_HUMAN_CLAIM_MUST_STAY_IN_REVIEWED_SCOPE"):
            journal_handoff(self.offered, self.review, pickup)

    def test_repeat_pickup_parent_must_match_exact_assessment(self):
        pickup = load("owner-stepper-operator-pickup.json")
        with self.assertRaisesRegex(Hold, "PICKUP_PARENT_ASSESSMENT_NOT_CURRENT"):
            journal_handoff(self.offered, self.review, pickup)

    def test_digital_license_never_becomes_material_pickup(self):
        lead = copy.deepcopy(self.offered)
        lead["category"] = "DIGITAL_MATERIAL"
        state = assess(lead, self.review)
        self.assertIn("DIGITAL_RIGHTS_AND_LICENSE_NEED_SEPARATE_REVIEW",
                      state["reason_codes"])


class CLI(unittest.TestCase):
    def test_first_write_only_and_cold_replay(self):
        cli = [sys.executable, str(ROOT / "scripts/static-forage.py")]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            proposal = root / "assessment.json"
            args = ["--lead", str(DATA / "owner-offered-stepper.json"),
                    "--review", str(DATA / "owner-stepper-human-review.json"),
                    "--out", str(proposal)]
            def run(command, flags=args):
                return subprocess.run(cli + [command] + flags,
                                      capture_output=True, text=True)
            a = run("assess")
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(json.loads(a.stdout)["state"],
                             "HUMAN_REVIEWED_PICKUP_PROPOSAL_ONLY")
            self.assertEqual(run("assess").returncode, 2)
            self.assertEqual(run("verify").returncode, 0)
            tampered = json.loads(proposal.read_text())
            tampered["permission_legally_verified_by_software"] = True
            proposal.write_text(json.dumps(tampered))
            self.assertEqual(run("verify").returncode, 2)

    def test_logged_handoff_from_original_human_pickup(self):
        cli = [sys.executable, str(ROOT / "scripts/static-forage.py")]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pickup = load("owner-stepper-operator-pickup.json")
            lead, review = load("owner-offered-stepper.json"), load(
                "owner-stepper-human-review.json")
            pickup["assessment_id"] = assess(lead, review)["assessment_id"]
            pickup_path, out = root / "pickup.json", root / "handoff.json"
            pickup_path.write_text(json.dumps(pickup))
            args = ["--lead", str(DATA / "owner-offered-stepper.json"),
                    "--review", str(DATA / "owner-stepper-human-review.json"),
                    "--pickup", str(pickup_path), "--out", str(out)]
            p = subprocess.run(cli + ["handoff"] + args,
                               capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stderr)
            got = json.loads(out.read_text())
            self.assertFalse(got["verified_legal_permission"])
            self.assertEqual(got["jubilee_treasury_inventory_delta"], 0)
            replay = subprocess.run(cli + ["verify"] + args,
                                    capture_output=True, text=True)
            self.assertEqual(replay.returncode, 0, replay.stderr)


if __name__ == "__main__":
    unittest.main()
