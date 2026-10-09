"""Hostile GLEAN-001 conservation, permission scope and source cold-replay tests."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from glean.kernel import Hold, plan, journal, cold_verify

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "fixtures/glean-001"


def load(name):
    return json.loads((FIX / name).read_text())


def operator_event(o, p, number, amount, report_day="2026-10-10"):
    return {
        "schema": "static-os.glean-operator-pickup/v0",
        "pickup_ref": "specimen:pickup-" + str(number).zfill(3),
        "offer_ref": o["offer_ref"],
        "plan_id": p["plan_id"],
        "operator_ref": "specimen:reporting-volunteer",
        "recipient_ref": o["intended_recipient_ref"],
        "reported_on": report_day,
        "amount": amount,
        "unit": o["quantity"]["unit"],
        "handoff_evidence_ref": "specimen:unverified-notebook-" + str(number),
        "operator_reports_collection": True,
        "independent_receipt_authenticated": False,
        "recipient_accepted_by_software": False,
        "physical_inventory_delta": 0,
    }


class Glean(unittest.TestCase):
    def setUp(self):
        self.o = load("orchard-offer.json")
        self.r = load("orchard-review.json")

    def test_no_offer_becomes_automatic_right_to_glean(self):
        result = plan(self.o)
        self.assertEqual(result["state"], "HOLD_AND_VERIFY")
        self.assertIn("NO_SCOPED_STEWARD_REVIEW", result["reason_codes"])
        self.assertFalse(result["owner_permission_legally_verified"])
        self.assertFalse(result["food_safety_certified"])
        self.assertFalse(result["physical_inventory_admitted"])
        self.assertEqual(result, cold_verify(self.o, None, result))

    def test_specific_review_gives_proposal_not_legal_certification(self):
        result = plan(self.o, self.r)
        self.assertEqual(result["state"], "HUMAN_REVIEWED_PROPOSAL_ONLY")
        self.assertEqual(result["reason_codes"], [])
        self.assertFalse(result["owner_permission_legally_verified"])
        self.assertFalse(result["transport_or_robot_actuated"])
        self.assertFalse(result["donor_legal_protection_certified"])
        self.assertEqual(result, cold_verify(self.o, self.r, result))

    def test_two_reports_conserve_same_remainder_without_inventory_credit(self):
        p = plan(self.o, self.r)
        events = [operator_event(self.o, p, 1, 3),
                  operator_event(self.o, p, 2, 4, "2026-10-11")]
        record = journal(self.o, self.r, events)
        self.assertEqual(record["aggregate_operator_reported_amount"], 7)
        self.assertEqual(record["remaining_unverified_offer_amount"], 3)
        self.assertEqual([e["reported_remaining"] for e in record["receipts"]], [7, 3])
        self.assertEqual(record["receipts"][0]["prior_receipt_or_plan_id"], p["plan_id"])
        self.assertEqual(record["receipts"][1]["prior_receipt_or_plan_id"],
                         record["receipts"][0]["report_id"])
        self.assertEqual(record["real_inventory_delta"], 0)
        self.assertFalse(record["receiver_local_admission"])
        self.assertFalse(record["independent_physical_count_verified"])
        self.assertEqual(record, cold_verify(self.o, self.r, record, events))

    def test_repeated_identifier_and_overharvesting_refuse(self):
        p = plan(self.o, self.r)
        a = operator_event(self.o, p, 1, 5)
        with self.assertRaisesRegex(Hold, "UNIQUE_PICKUP_REF"):
            journal(self.o, self.r, [a, a])
        with self.assertRaisesRegex(Hold, "REMAINDER_CAP_EXCEEDED"):
            journal(self.o, self.r, [a, operator_event(self.o, p, 2, 4)])
        with self.assertRaisesRegex(Hold, "REMAINDER_CAP_EXCEEDED"):
            journal(self.o, self.r, [operator_event(self.o, p, i, 1)
                                     for i in range(1, 10)])
        with self.assertRaisesRegex(Hold, "PICKUP_REPORT_OUTSIDE_SCOPE"):
            journal(self.o, self.r, [operator_event(self.o, p, 1, -2)])

    def test_claimed_owner_without_verification_doesnt_make_legal_certification(self):
        self.o["owner_donation_asserted"] = False
        a = plan(self.o, self.r)
        self.assertIn("OWNER_DONATION_NOT_EVEN_ASSERTED", a["reason_codes"])
        with self.assertRaisesRegex(Hold, "BLOCKED_REMAINDER"):
            journal(self.o, self.r, [])
        self.o["owner_donation_asserted"] = True
        self.o["offer_is_authenticated_by_software"] = True
        with self.assertRaisesRegex(Hold, "INVALID_OFFER_OR_FORGED_AUTHENTICITY"):
            plan(self.o)

    def test_independent_custody_or_food_safety_authority_cannot_be_inserted(self):
        for key in ("owner_identity_authenticated_by_software",
                    "food_safety_certified", "physical_ownership_transferred"):
            r = copy.deepcopy(self.r)
            r[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(Hold, "REVIEW_CANNOT_AUTHENTICATE"):
                plan(self.o, r)
        p = plan(self.o, self.r)
        for key, value in (
            ("independent_receipt_authenticated", True),
            ("recipient_accepted_by_software", True),
            ("physical_inventory_delta", 4),
        ):
            e = operator_event(self.o, p, 1, 2)
            e[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(Hold, "PICKUP_REPORT_OUTSIDE_SCOPE"):
                journal(self.o, self.r, [e])

    def test_wrong_recipient_site_purpose_dates_and_quantity_are_denied(self):
        for field, value in (
            ("recipient_ref", "specimen:someone-else"),
            ("site_ref", "specimen:other-place"),
            ("purpose", "NONCOMMERCIAL_WORKSHOP_GIFT"),
            ("maximum_quantity", 11),
            ("unit", "ITEM"),
            ("valid_until", "2026-11-01"),
        ):
            r = copy.deepcopy(self.r)
            r["scope"][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(Hold, "SCOPE_SITE_PURPOSE"):
                plan(self.o, r)
        p = plan(self.o, self.r)
        event = operator_event(self.o, p, 1, 2, "2026-11-12")
        with self.assertRaisesRegex(Hold, "PICKUP_REPORT_OUTSIDE_SCOPE"):
            journal(self.o, self.r, [event])

    def test_protected_unsafe_and_sharp_surplus_hold(self):
        for hazard in ("SPOILED_OR_UNSAFE_FOOD", "UNIDENTIFIED_EDIBLE",
                       "CONTAMINATION", "PROTECTED_RESOURCE",
                       "POSTED_OR_LOCKED", "UNKNOWN_CHEMICAL",
                       "DAMAGED_BATTERY"):
            o = copy.deepcopy(self.o)
            o["hazards"] = [hazard]
            with self.subTest(hazard=hazard):
                self.assertIn("STOP_" + hazard, plan(o, self.r)["reason_codes"])
        o = copy.deepcopy(self.o)
        o["hazards"] = ["SHARP_OR_POWERED_EQUIPMENT"]
        self.assertIn("SPECIALIST_REVIEW_REQUIRED", plan(o, self.r)["reason_codes"])

    def test_food_statute_not_inherited_by_workshop_surplus(self):
        w = load("workshop-offer.json")
        state = plan(w)
        self.assertEqual(state["purpose"], "NONCOMMERCIAL_WORKSHOP_GIFT")
        self.assertEqual(state["material_type"], "WORKSHOP_SURPLUS")
        for key, value in (
            ("source_status", "AFTER_PRIMARY_HARVEST"),
            ("purpose", "FREE_DISTRIBUTION"),
        ):
            fake = copy.deepcopy(w)
            fake[key] = value
            with self.subTest(field=key), self.assertRaisesRegex(Hold, "NONFOOD_SURPLUS"):
                plan(fake)
        o = copy.deepcopy(self.o)
        o["purpose"] = "NONCOMMERCIAL_WORKSHOP_GIFT"
        with self.assertRaisesRegex(Hold, "AGRICULTURAL_GLEANING_REQUIRES"):
            plan(o)
        o = copy.deepcopy(self.o)
        o["material_type"] = "WORKSHOP_SURPLUS"
        with self.assertRaisesRegex(Hold, "NONFOOD_SURPLUS"):
            plan(o)

    def test_original_source_mutations_and_hashed_receipt_claims_fail_replay(self):
        p = plan(self.o, self.r)
        x = operator_event(self.o, p, 1, 2)
        record = journal(self.o, self.r, [x])
        changed = copy.deepcopy(record)
        changed["receiver_local_admission"] = True
        with self.assertRaisesRegex(Hold, "GLEAN_COLD_REPLAY_CONTRADICTION"):
            cold_verify(self.o, self.r, changed, [x])
        self.o["quantity"]["amount"] = 9
        with self.assertRaises(Hold):
            cold_verify(self.o, self.r, record, [x])


class CLI(unittest.TestCase):
    def test_assess_and_verify_without_actual_pickup(self):
        command = [sys.executable, str(ROOT / "scripts/static-glean.py")]
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "offer-assessment.json"
            args = ["--offer", str(FIX / "orchard-offer.json"),
                    "--out", str(out)]
            a = subprocess.run(command + ["assess"] + args, capture_output=True, text=True)
            self.assertEqual(a.returncode, 0, a.stderr)
            self.assertEqual(json.loads(out.read_text())["state"], "HOLD_AND_VERIFY")
            b = subprocess.run(command + ["verify"] + args, capture_output=True, text=True)
            self.assertEqual(b.returncode, 0, b.stderr)
            second = subprocess.run(command + ["assess"] + args, capture_output=True, text=True)
            self.assertEqual(second.returncode, 2)

    def test_scoped_pickup_journal_cli_with_original_events(self):
        command = [sys.executable, str(ROOT / "scripts/static-glean.py")]
        with tempfile.TemporaryDirectory() as tmp:
            p = plan(load("orchard-offer.json"), load("orchard-review.json"))
            events = [operator_event(load("orchard-offer.json"), p, 1, 2)]
            events_path = Path(tmp) / "report.json"
            events_path.write_text(json.dumps(events))
            out = Path(tmp) / "journal.json"
            args = ["--offer", str(FIX / "orchard-offer.json"),
                    "--review", str(FIX / "orchard-review.json"),
                    "--pickups", str(events_path), "--out", str(out)]
            one = subprocess.run(command + ["journal"] + args, capture_output=True, text=True)
            self.assertEqual(one.returncode, 0, one.stderr)
            self.assertEqual(json.loads(out.read_text())["real_inventory_delta"], 0)
            same = subprocess.run(command + ["verify"] + args, capture_output=True, text=True)
            self.assertEqual(same.returncode, 0, same.stderr)
            events[0]["amount"] = 3
            events_path.write_text(json.dumps(events))
            bad = subprocess.run(command + ["verify"] + args, capture_output=True, text=True)
            self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
