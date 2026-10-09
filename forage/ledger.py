"""FORAGE-001: local permission-first recovery lead and witnessed handoff journal.

Not a legal decision engine. Any claim of authority is human-entered and
unverified; a content hash is not a signature. No scavenging, geolocation,
machine control, physical inventory change, or unsafe collection occurs here.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from typing import Any

LEAD = "static-os.forage-lead/v0"
REVIEW = "static-os.forage-human-review/v0"
PICKUP = "static-os.forage-operator-pickup/v0"
ASSESSMENT = "static-os.forage-assessment/v0"
HANDOFF = "static-os.forage-handoff/v0"

CATEGORIES = frozenset({
    "TECH_ELECTRONICS", "TECH_PARTS", "GENERAL_MATERIAL", "BOTANICAL",
    "FOOD", "MINERAL", "DIGITAL_MATERIAL",
})
SOURCES = frozenset({
    "DIRECT_OWNER_OFFER", "MUNICIPAL_REUSE", "PUBLIC_LAND_COLLECTION",
    "PRIVATE_GROUND", "CURBSIDE_UNVERIFIED", "UNKNOWN",
})
LANDS = frozenset({
    "PRIVATE", "MUNICIPAL", "BLM", "USFS", "STATE_TRUST",
    "STATE_PARK", "UNKNOWN",
})
PURPOSES = frozenset({"PERSONAL_NONCOMMERCIAL",
                      "COMMUNITY_NONCOMMERCIAL", "COMMERCIAL"})
UNITS = frozenset({"ITEM", "GRAM", "KILOGRAM", "POUND", "LITER"})
HAZARDS = frozenset({
    "POSTED_NO_ENTRY", "LOCKED_CONTAINER", "PROTECTED_SPECIES",
    "CULTURAL_ARTIFACT", "ACTIVE_MINING_CLAIM", "DAMAGED_LITHIUM",
    "UNKNOWN_CHEMICAL", "BIOHAZARD", "UNIDENTIFIED_EDIBLE",
    "PRESSURIZED_CONTAINER", "BATTERY_PRESENT", "MAINS_POWER",
    "SHARP_MATERIAL", "UNCERTAIN_CONTAMINATION",
})
HARD_STOPS = frozenset({
    "POSTED_NO_ENTRY", "LOCKED_CONTAINER", "PROTECTED_SPECIES",
    "CULTURAL_ARTIFACT", "ACTIVE_MINING_CLAIM", "DAMAGED_LITHIUM",
    "UNKNOWN_CHEMICAL", "BIOHAZARD", "UNIDENTIFIED_EDIBLE",
    "PRESSURIZED_CONTAINER",
})
INSPECTION_REQUIRED = HAZARDS - HARD_STOPS
SOURCE_LAND = {
    "DIRECT_OWNER_OFFER": {"PRIVATE"},
    "MUNICIPAL_REUSE": {"MUNICIPAL"},
    "PUBLIC_LAND_COLLECTION": {"BLM", "USFS", "STATE_TRUST", "STATE_PARK"},
    "PRIVATE_GROUND": {"PRIVATE"},
    "CURBSIDE_UNVERIFIED": {"PRIVATE", "MUNICIPAL", "UNKNOWN"},
    "UNKNOWN": set(LANDS),
}
AUTHORITY_KIND = frozenset({
    "SOURCE_OWNER", "LAND_MANAGER", "PROGRAM_STEWARD", "NONE",
})
BASIS = frozenset({
    "DIRECT_OWNER_GRANT", "MUNICIPAL_PROGRAM_RULE",
    "SITE_SPECIFIC_PUBLIC_RULE", "SPECIFIC_WRITTEN_PERMIT", "NONE",
})
TOKEN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,119}$")


class Hold(ValueError):
    """Explicit refusal, never an authorization or a substitute for advice."""


def require(ok: bool, why: str) -> None:
    if not ok:
        raise Hold(why)


def exact(data: Any, keys: set[str], why: str) -> dict:
    require(type(data) is dict and set(data) == keys, why)
    return data


def identifier(value: Any) -> bool:
    return type(value) is str and TOKEN.fullmatch(value) is not None


def words(value: Any) -> bool:
    return type(value) is str and 3 <= len(value) <= 240 and "\x00" not in value


def day(value: Any) -> date:
    require(type(value) is str and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value)
            is not None, "ISO_DATE_REQUIRED")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise Hold("INVALID_DATE") from exc


def digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def sealed(value: dict, key: str, namespace: str) -> dict:
    return {**value, key: namespace + ":" + digest(value)}


def validate_lead(value: Any) -> dict:
    v = exact(value, {
        "schema", "lead_ref", "item_ref", "description", "category",
        "source_kind", "land_class", "site_ref", "steward_ref",
        "purpose", "quantity", "hazards", "observation",
        "operator_claim_of_ownership",
    }, "LEAD_EXACT_FIELDS_REQUIRED")
    require(v["schema"] == LEAD
            and all(identifier(v[k]) for k in
                    ("lead_ref", "item_ref", "site_ref", "steward_ref"))
            and words(v["description"]) and words(v["observation"])
            and v["category"] in CATEGORIES
            and v["source_kind"] in SOURCES
            and v["land_class"] in LANDS
            and v["land_class"] in SOURCE_LAND[v["source_kind"]]
            and v["purpose"] in PURPOSES
            and v["operator_claim_of_ownership"] is False,
            "INVALID_LEAD_OR_UNEARNED_OWNERSHIP")
    quantity = exact(v["quantity"], {"amount", "unit"},
                     "EXACT_QUANTITY_REQUIRED")
    require(type(quantity["amount"]) is int and 1 <= quantity["amount"] <= 100_000
            and quantity["unit"] in UNITS, "BOUNDED_POSITIVE_QUANTITY_REQUIRED")
    flags = v["hazards"]
    require(type(flags) is list and len(flags) == len(set(flags))
            and len(flags) <= len(HAZARDS)
            and all(type(h) is str and h in HAZARDS for h in flags),
            "UNKNOWN_OR_DUPLICATE_HAZARD")
    require(not (v["category"] == "DIGITAL_MATERIAL"
                 and v["source_kind"] == "PUBLIC_LAND_COLLECTION"),
            "DIGITAL_LICENSE_NOT_A_PUBLIC_LAND_HARVEST")
    return v


def validate_review(value: Any, lead: dict) -> dict:
    v = exact(value, {
        "schema", "lead_ref", "reviewer_ref", "reviewed_on", "decision",
        "authority_kind", "authority_ref", "basis", "evidence_ref",
        "scope", "entry_and_removal_checked_by_human",
        "site_and_species_rules_checked_by_human",
        "hazard_review_by_human", "evidence_authenticated_by_software",
    }, "REVIEW_EXACT_FIELDS_REQUIRED")
    require(v["schema"] == REVIEW and v["lead_ref"] == lead["lead_ref"]
            and identifier(v["reviewer_ref"]) and identifier(v["authority_ref"])
            and identifier(v["evidence_ref"])
            and v["decision"] in ("REQUEST_MORE_INFO", "DECLINE",
                                  "SCOPED_PERMISSION_ASSERTED")
            and v["authority_kind"] in AUTHORITY_KIND
            and v["basis"] in BASIS
            and v["hazard_review_by_human"] in ("UNKNOWN", "CLEAR",
                                               "SPECIALIST_REVIEW_NEEDED")
            and type(v["entry_and_removal_checked_by_human"]) is bool
            and type(v["site_and_species_rules_checked_by_human"]) is bool
            and v["evidence_authenticated_by_software"] is False,
            "INVALID_REVIEW_OR_UNEARNED_AUTHENTICATION")
    reviewed = day(v["reviewed_on"])
    scope = exact(v["scope"], {
        "site_ref", "item_ref", "max_amount", "unit", "purpose",
        "valid_from", "valid_until", "permission_action",
    }, "EXACT_PERMISSION_SCOPE_REQUIRED")
    require(scope["site_ref"] == lead["site_ref"]
            and scope["item_ref"] == lead["item_ref"]
            and type(scope["max_amount"]) is int
            and scope["max_amount"] >= lead["quantity"]["amount"]
            and scope["max_amount"] <= 100_000
            and scope["unit"] == lead["quantity"]["unit"]
            and scope["purpose"] == lead["purpose"]
            and scope["permission_action"] == "ENTER_AND_REMOVE_SPECIFIED_ITEMS"
            and day(scope["valid_from"]) <= reviewed <= day(scope["valid_until"]),
            "PERMISSION_SCOPE_DATE_QUANTITY_USE_OR_SITE_MISMATCH")
    return v


def _reasons(lead: dict, review: dict | None) -> list[str]:
    reasons = []
    if lead["category"] == "DIGITAL_MATERIAL":
        reasons.append("DIGITAL_RIGHTS_AND_LICENSE_NEED_SEPARATE_REVIEW")
    if lead["source_kind"] in ("CURBSIDE_UNVERIFIED", "UNKNOWN"):
        reasons.append("DISCARD_OR_LOCATION_DOES_NOT_ESTABLISH_TITLE")
    if lead["source_kind"] == "PRIVATE_GROUND":
        reasons.append("PRIVATE_GROUND_REQUIRES_EXPLICIT_OWNER_GRANT")
    if lead["land_class"] in ("STATE_PARK", "STATE_TRUST"):
        reasons.append("SPECIAL_LAND_REGIME_REQUIRES_LOCAL_AUTHORITY_REVIEW")
    if lead["land_class"] in ("BLM", "USFS"):
        reasons.append("LOCAL_LAND_RULES_SPECIES_QUANTITY_CLOSURES_MUST_BE_CHECKED")
    if lead["purpose"] != "PERSONAL_NONCOMMERCIAL" and lead["source_kind"] == "PUBLIC_LAND_COLLECTION":
        reasons.append("PUBLIC_RESOURCE_COMMUNITY_OR_COMMERCIAL_USE_NEEDS_SEPARATE_RIGHTS")
    for hazard in sorted(HARD_STOPS.intersection(lead["hazards"])):
        reasons.append("STOP_" + hazard)
    conditional = INSPECTION_REQUIRED.intersection(lead["hazards"])
    if conditional:
        reasons.append("SPECIALIST_OR_PHYSICAL_SAFETY_CHECK_REQUIRED")
    if review is None:
        reasons.append("NO_SCOPED_AUTHORITY_REVIEW")
    else:
        if review["decision"] != "SCOPED_PERMISSION_ASSERTED":
            reasons.append("REVIEW_HAS_NOT_ASSERTED_SPECIFIC_PERMISSION")
        if not review["entry_and_removal_checked_by_human"]:
            reasons.append("ACCESS_AND_REMOVAL_NOT_BOTH_REVIEWED")
        if not review["site_and_species_rules_checked_by_human"]:
            reasons.append("AREA_SPECIES_QUOTA_AND_SIGNS_NOT_REVIEWED")
        if review["hazard_review_by_human"] != "CLEAR":
            reasons.append("HAZARD_NOT_CLEARED_FOR_HANDOFF")
        source = lead["source_kind"]
        compatible = {
            "DIRECT_OWNER_OFFER": {
                ("SOURCE_OWNER", "DIRECT_OWNER_GRANT"),
            },
            "PRIVATE_GROUND": {
                ("SOURCE_OWNER", "DIRECT_OWNER_GRANT"),
            },
            "MUNICIPAL_REUSE": {
                ("PROGRAM_STEWARD", "MUNICIPAL_PROGRAM_RULE"),
                ("PROGRAM_STEWARD", "SPECIFIC_WRITTEN_PERMIT"),
            },
            "PUBLIC_LAND_COLLECTION": {
                ("LAND_MANAGER", "SITE_SPECIFIC_PUBLIC_RULE"),
                ("LAND_MANAGER", "SPECIFIC_WRITTEN_PERMIT"),
            },
        }
        if (review["authority_kind"], review["basis"]) not in compatible.get(source, set()):
            reasons.append("AUTHORITY_BASIS_DOES_NOT_MATCH_SOURCE_STEWARD")
        if source == "PUBLIC_LAND_COLLECTION" and lead["purpose"] != "PERSONAL_NONCOMMERCIAL" and review["basis"] != "SPECIFIC_WRITTEN_PERMIT":
            reasons.append("NONPERSONAL_PUBLIC_RESOURCE_NEEDS_SPECIFIC_PERMIT")
        if lead["land_class"] in ("STATE_PARK", "STATE_TRUST") and review["basis"] != "SPECIFIC_WRITTEN_PERMIT":
            reasons.append("SPECIAL_LAND_NEEDS_SPECIFIC_WRITTEN_PERMISSION")
    return sorted(set(reasons))


def assess(lead: Any, review: Any = None) -> dict:
    source = validate_lead(lead)
    checked = validate_review(review, source) if review is not None else None
    blockers = _reasons(source, checked)
    body = {
        "schema": ASSESSMENT,
        "lead_digest": digest(source),
        "lead_ref": source["lead_ref"],
        "review_digest": digest(checked) if checked is not None else None,
        "category": source["category"],
        "land_class": source["land_class"],
        "source_kind": source["source_kind"],
        "reason_codes": blockers,
        "status": ("HOLD_AND_RESEARCH" if blockers
                   else "HUMAN_REVIEWED_PICKUP_PROPOSAL_ONLY"),
        "who_can_decide": "HUMAN_SITE_OWNER_LAND_STEWARD_AND_APPLICABLE_LAW",
        "permission_legally_verified_by_software": False,
        "retrieval_or_entry_executed": False,
        "machine_dispatch_enabled": False,
        "physical_inventory_delta": 0,
        "robots_can_use_this_material": False,
    }
    return sealed(body, "assessment_id", "static-os-forage-assessment-001")


def validate_pickup(pickup: Any, source: dict, review: dict) -> dict:
    v = exact(pickup, {
        "schema", "lead_ref", "assessment_id", "operator_ref", "reported_date",
        "reported_amount", "unit", "witness_ref", "handoff_evidence_ref",
        "reported_physical_receipt", "site_owner_rights_verified_by_software",
        "physical_safety_certified", "inventory_accepted",
    }, "PICKUP_EXACT_FIELDS_REQUIRED")
    require(v["schema"] == PICKUP and v["lead_ref"] == source["lead_ref"]
            and all(identifier(v[k]) for k in
                    ("operator_ref", "witness_ref", "handoff_evidence_ref"))
            and v["reported_physical_receipt"] is True
            and v["site_owner_rights_verified_by_software"] is False
            and v["physical_safety_certified"] is False
            and v["inventory_accepted"] is False
            and type(v["reported_amount"]) is int
            and 1 <= v["reported_amount"] <= source["quantity"]["amount"]
            and v["unit"] == source["quantity"]["unit"]
            and day(review["scope"]["valid_from"])
                <= day(v["reported_date"])
                <= day(review["scope"]["valid_until"])
            and day(v["reported_date"]) >= day(review["reviewed_on"]),
            "PICKUP_HUMAN_CLAIM_MUST_STAY_IN_REVIEWED_SCOPE")
    return v


def journal_handoff(lead: Any, review: Any, pickup: Any) -> dict:
    source = validate_lead(lead)
    checked = validate_review(review, source)
    state = assess(source, checked)
    require(state["status"] == "HUMAN_REVIEWED_PICKUP_PROPOSAL_ONLY",
            "BLOCKED_OR_UNREVIEWED_LEAD_CANNOT_CREATE_HANDOFF")
    record = validate_pickup(pickup, source, checked)
    require(record["assessment_id"] == state["assessment_id"],
            "PICKUP_PARENT_ASSESSMENT_NOT_CURRENT")
    body = {
        "schema": HANDOFF,
        "lead_ref": source["lead_ref"],
        "lead_digest": digest(source),
        "assessment_id": state["assessment_id"],
        "operator_review_digest": digest(checked),
        "human_pickup_digest": digest(record),
        "state": "OPERATOR_REPORTED_HANDOFF_NOT_INDEPENDENTLY_ATTESTED",
        "physical_receipt_operator_reported": True,
        "verified_legal_permission": False,
        "verified_source_title": False,
        "witness_independent_or_authenticated": False,
        "physical_quality_inspected": False,
        "robot_garden_part_admitted": False,
        "jubilee_treasury_inventory_delta": 0,
        "financial_claim": False,
    }
    return sealed(body, "handoff_id", "static-os-forage-handoff-001")


def cold_verify(lead: Any, review: Any, candidate: Any,
                pickup: Any = None) -> dict:
    require(type(candidate) is dict, "SEALED_RESULT_REQUIRED")
    expected = (assess(lead, review) if pickup is None else
                journal_handoff(lead, review, pickup))
    require(candidate == expected, "COLD_REPLAY_SOURCE_DISAGREEMENT")
    return expected
