"""GLEAN-001: bounded human-steward surplus offers, independent of FORAGE.

Documented offer != legal grant. Human review != authenticated owner. An
operator-reported harvest != physical or food-safety certification. Records
are content-addressed for cold replay, not signed by land owners.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any

OFFER = "static-os.glean-offer/v0"
REVIEW = "static-os.glean-human-review/v0"
PLAN = "static-os.glean-pickup-plan/v0"
PICKUP = "static-os.glean-operator-pickup/v0"
JOURNAL = "static-os.glean-pickup-journal/v0"
TYPES = {"AGRICULTURAL_CROP", "WORKSHOP_SURPLUS"}
PURPOSES = {"FREE_DISTRIBUTION", "NONCOMMERCIAL_WORKSHOP_GIFT"}
UNITS = {"ITEM", "POUND", "KILOGRAM", "LITER"}
HAZARDS = {
    "UNIDENTIFIED_EDIBLE", "CONTAMINATION", "SPOILED_OR_UNSAFE_FOOD",
    "PROTECTED_RESOURCE", "POSTED_OR_LOCKED", "UNKNOWN_CHEMICAL",
    "DAMAGED_BATTERY", "SHARP_OR_POWERED_EQUIPMENT",
}
HARD = HAZARDS - {"SHARP_OR_POWERED_EQUIPMENT"}
REF = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._:/-]{2,119}$")


class Hold(ValueError):
    pass


def require(ok: bool, why: str):
    if not ok:
        raise Hold(why)


def fields(record: Any, keys: set[str], code: str) -> dict:
    require(type(record) is dict and set(record) == keys, code)
    return record


def ref(value: Any):
    return type(value) is str and REF.fullmatch(value) is not None


def description(value: Any):
    return type(value) is str and 3 <= len(value) <= 240 and "\x00" not in value


def iso(value: Any) -> date:
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
            is not None, "ISO_DAY_REQUIRED")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Hold("INVALID_DAY") from exc


def digest(value: Any) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def seal(body: dict, key: str, family: str) -> dict:
    return {**body, key: family + ":" + digest(body)}


def offer_check(value: Any) -> dict:
    v = fields(value, {
        "schema", "offer_ref", "site_ref", "steward_ref", "owner_claim_ref",
        "material_ref", "material_type", "description", "source_status",
        "purpose", "intended_recipient_ref", "quantity", "valid_from",
        "valid_until", "donation_evidence_ref", "owner_donation_asserted",
        "hazards", "offer_is_authenticated_by_software",
    }, "OFFER_EXACT_FIELDS")
    require(v["schema"] == OFFER and all(ref(v[k]) for k in (
        "offer_ref", "site_ref", "steward_ref", "owner_claim_ref", "material_ref",
        "intended_recipient_ref", "donation_evidence_ref"))
        and description(v["description"]) and v["material_type"] in TYPES
        and v["purpose"] in PURPOSES and type(v["owner_donation_asserted"]) is bool
        and v["offer_is_authenticated_by_software"] is False
        and v["source_status"] in {"AFTER_PRIMARY_HARVEST", "UNUSED_SURPLUS"},
        "INVALID_OFFER_OR_FORGED_AUTHENTICITY")
    q = fields(v["quantity"], {"amount", "unit"}, "QUANTITY_EXACT_FIELDS")
    require(type(q["amount"]) is int and 1 <= q["amount"] <= 100000
            and q["unit"] in UNITS, "QUANTITY_MUST_BE_POSITIVE_BOUNDED_INTEGER")
    require(iso(v["valid_from"]) <= iso(v["valid_until"]), "INVALID_OFFER_WINDOW")
    h = v["hazards"]
    require(type(h) is list and len(h) == len(set(h))
            and all(type(z) is str and z in HAZARDS for z in h),
            "HAZARD_UNRECOGNIZED_OR_DUPLICATED")
    if v["material_type"] == "AGRICULTURAL_CROP":
        require(v["source_status"] == "AFTER_PRIMARY_HARVEST"
                and v["purpose"] == "FREE_DISTRIBUTION",
                "AGRICULTURAL_GLEANING_REQUIRES_DONATED_CROP_FREE_DISTRIBUTION")
    else:
        require(v["source_status"] == "UNUSED_SURPLUS"
                and v["purpose"] == "NONCOMMERCIAL_WORKSHOP_GIFT"
                and q["unit"] == "ITEM",
                "NONFOOD_SURPLUS_IS_NOT_AGRICULTURAL_GLEANING")
    return v


def review_check(value: Any, offer: dict) -> dict:
    v = fields(value, {
        "schema", "offer_ref", "reviewer_ref", "reviewed_on", "decision",
        "evidence_ref", "scope", "owner_identity_authenticated_by_software",
        "access_and_removal_checked_by_human", "site_rules_checked_by_human",
        "recipient_scope_checked_by_human", "food_safety_certified",
        "physical_ownership_transferred",
    }, "REVIEW_EXACT_FIELDS")
    require(v["schema"] == REVIEW and v["offer_ref"] == offer["offer_ref"]
            and all(ref(v[k]) for k in ("reviewer_ref", "evidence_ref"))
            and v["decision"] in {"HOLD", "SCOPED_ACCESS_ASSERTED"}
            and all(type(v[k]) is bool for k in (
                "access_and_removal_checked_by_human", "site_rules_checked_by_human",
                "recipient_scope_checked_by_human"))
            and v["owner_identity_authenticated_by_software"] is False
            and v["food_safety_certified"] is False
            and v["physical_ownership_transferred"] is False,
            "REVIEW_CANNOT_AUTHENTICATE_OWNER_OR_FOOD_OR_CUSTODY")
    scope = fields(v["scope"], {
        "site_ref", "material_ref", "purpose", "recipient_ref",
        "maximum_quantity", "unit", "valid_from", "valid_until",
        "operation",
    }, "SCOPE_EXACT_FIELDS")
    require(scope["site_ref"] == offer["site_ref"]
            and scope["material_ref"] == offer["material_ref"]
            and scope["purpose"] == offer["purpose"]
            and scope["recipient_ref"] == offer["intended_recipient_ref"]
            and type(scope["maximum_quantity"]) is int
            and 1 <= scope["maximum_quantity"] <= offer["quantity"]["amount"]
            and scope["unit"] == offer["quantity"]["unit"]
            and scope["operation"] == "ENTER_AND_REMOVE_REMAINDER_ONLY"
            and iso(offer["valid_from"]) <= iso(scope["valid_from"])
            and iso(scope["valid_from"]) <= iso(v["reviewed_on"])
            and iso(v["reviewed_on"]) <= iso(scope["valid_until"])
            and iso(scope["valid_until"]) <= iso(offer["valid_until"]),
            "SCOPE_SITE_PURPOSE_RECIPIENT_QUANTITY_OR_TIME_MISMATCH")
    return v


def reasons(offer: dict, review: dict | None) -> list[str]:
    blockers = []
    if not offer["owner_donation_asserted"]:
        blockers.append("OWNER_DONATION_NOT_EVEN_ASSERTED")
    for hazard in sorted(HARD.intersection(offer["hazards"])):
        blockers.append("STOP_" + hazard)
    if "SHARP_OR_POWERED_EQUIPMENT" in offer["hazards"]:
        blockers.append("SPECIALIST_REVIEW_REQUIRED")
    if review is None:
        blockers.append("NO_SCOPED_STEWARD_REVIEW")
    else:
        if review["decision"] != "SCOPED_ACCESS_ASSERTED":
            blockers.append("HUMAN_REVIEW_REMAINS_HOLD")
        for field, code in (
            ("access_and_removal_checked_by_human", "ENTRY_AND_REMOVAL_NOT_REVIEWED"),
            ("site_rules_checked_by_human", "LOCAL_SITE_RULES_NOT_REVIEWED"),
            ("recipient_scope_checked_by_human", "RECIPIENT_SCOPE_NOT_REVIEWED"),
        ):
            if not review[field]:
                blockers.append(code)
    return sorted(set(blockers))


def plan(offer: Any, review: Any = None) -> dict:
    o = offer_check(offer)
    r = review_check(review, o) if review is not None else None
    blockers = reasons(o, r)
    return seal({
        "schema": PLAN,
        "offer_ref": o["offer_ref"],
        "offer_digest": digest(o),
        "review_digest": digest(r) if r is not None else None,
        "material_type": o["material_type"],
        "purpose": o["purpose"],
        "max_remainder_amount": o["quantity"]["amount"],
        "unit": o["quantity"]["unit"],
        "reason_codes": blockers,
        "state": "HOLD_AND_VERIFY" if blockers else "HUMAN_REVIEWED_PROPOSAL_ONLY",
        "owner_permission_legally_verified": False,
        "donor_legal_protection_certified": False,
        "food_safety_certified": False,
        "physical_inventory_admitted": False,
        "transport_or_robot_actuated": False,
    }, "plan_id", "static-os-glean-plan-001")


def _event(e: Any, o: dict, r: dict):
    v = fields(e, {
        "schema", "pickup_ref", "offer_ref", "plan_id", "operator_ref",
        "recipient_ref", "reported_on", "amount", "unit",
        "handoff_evidence_ref", "operator_reports_collection",
        "independent_receipt_authenticated", "recipient_accepted_by_software",
        "physical_inventory_delta",
    }, "PICKUP_EXACT_FIELDS")
    require(v["schema"] == PICKUP and v["offer_ref"] == o["offer_ref"]
            and all(ref(v[k]) for k in (
                "pickup_ref", "operator_ref", "recipient_ref", "handoff_evidence_ref"))
            and v["recipient_ref"] == o["intended_recipient_ref"]
            and type(v["amount"]) is int and 1 <= v["amount"] <= r["scope"]["maximum_quantity"]
            and v["unit"] == o["quantity"]["unit"]
            and v["operator_reports_collection"] is True
            and v["independent_receipt_authenticated"] is False
            and v["recipient_accepted_by_software"] is False
            and type(v["physical_inventory_delta"]) is int
            and v["physical_inventory_delta"] == 0
            and iso(r["reviewed_on"]) <= iso(v["reported_on"])
            and iso(r["scope"]["valid_from"]) <= iso(v["reported_on"])
            and iso(v["reported_on"]) <= iso(r["scope"]["valid_until"]),
            "PICKUP_REPORT_OUTSIDE_SCOPE_OR_MINTS_AUTHORITY")
    return v


def journal(offer: Any, review: Any, pickups: Any) -> dict:
    o = offer_check(offer)
    r = review_check(review, o)
    p = plan(o, r)
    require(p["state"] == "HUMAN_REVIEWED_PROPOSAL_ONLY",
            "BLOCKED_REMAINDER_CANNOT_HAVE_PICKUP_JOURNAL")
    require(type(pickups) is list and len(pickups) <= 128,
            "PICKUP_LIST_BOUNDED")
    used = 0
    seen = set()
    previous = p["plan_id"]
    receipts = []
    for input_event in pickups:
        e = _event(input_event, o, r)
        require(e["plan_id"] == p["plan_id"] and e["pickup_ref"] not in seen,
                "UNIQUE_PICKUP_REF_AND_CURRENT_PLAN_REQUIRED")
        seen.add(e["pickup_ref"])
        used += e["amount"]
        require(used <= o["quantity"]["amount"]
                and used <= r["scope"]["maximum_quantity"],
                "REMAINDER_CAP_EXCEEDED_NO_DOUBLE_EXTRACTION")
        item = seal({
            "schema": "static-os.glean-operator-report-receipt/v0",
            "pickup_ref": e["pickup_ref"],
            "source_pickup_digest": digest(e),
            "prior_receipt_or_plan_id": previous,
            "reported_aggregate": used,
            "reported_remaining": o["quantity"]["amount"] - used,
            "unit": o["quantity"]["unit"],
            "physical_remaining_verified": False,
            "source_owner_attestation_verified": False,
            "recipient_acceptance_verified": False,
            "actual_harvest_quality_verified": False,
            "inventory_delta": 0,
        }, "report_id", "static-os-glean-report-001")
        previous = item["report_id"]
        receipts.append(item)
    return seal({
        "schema": JOURNAL,
        "plan_id": p["plan_id"],
        "offer_digest": digest(o),
        "review_digest": digest(r),
        "source_pickup_digests": [digest(e) for e in pickups],
        "receipts": receipts,
        "aggregate_operator_reported_amount": used,
        "remaining_unverified_offer_amount": o["quantity"]["amount"] - used,
        "independent_physical_count_verified": False,
        "owner_title_verified_by_software": False,
        "receiver_local_admission": False,
        "real_inventory_delta": 0,
    }, "journal_id", "static-os-glean-journal-001")


def cold_verify(offer: Any, review: Any, result: Any, pickups: Any = None):
    require(type(result) is dict, "SEALED_RESULT_REQUIRED")
    expected = plan(offer, review) if pickups is None else journal(offer, review, pickups)
    require(result == expected, "GLEAN_COLD_REPLAY_CONTRADICTION")
    return expected
