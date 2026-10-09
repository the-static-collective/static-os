"""FORAGE-002: offline photo evidence and human-selected recovery candidate.

This adapts a phone file into the existing FORAGE-001 *unreviewed* lead.
Neither image pixels nor deterministic category suggestions confer owner rights.
No remote inference, biological identification, physical pickup or robot action.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from forage.ledger import Hold, assess, digest, exact, identifier, require, validate_lead, sealed

PHOTO = "static-os.forage-photo-evidence/v0"
SCOUT = "static-os.forage-scout/v0"
MAX_BYTES = 16 * 1024 * 1024

# Human-selected category maps to workshop hypotheses, not image classification.
# Deliberately never declares a recovered part safe or functional.
SUGGESTIONS = {
    "TECH_ELECTRONICS": ("Enclosure reference", "Repair/parts research", "Electronics recycling check"),
    "TECH_PARTS": ("Bracket or fixture candidate", "Motor/drive research", "Fastener recovery check"),
    "GENERAL_MATERIAL": ("Stock dimensions to inspect", "Fixture/stand candidate", "Material condition check"),
    "BOTANICAL": ("Species/land rights research", "Composting suitability research", "Ecology observation"),
    "FOOD": ("Positive species identification needed", "Food safety research", "Do not taste to identify"),
    "MINERAL": ("Geological documentation", "Land and claim status review", "Material identification"),
    "DIGITAL_MATERIAL": ("Licensing and provenance review", "Reusable design reference", "No unauthorized copying"),
}


def media_type(data: bytes) -> str:
    """Header sniff; integrity signal, never authentic camera attribution."""
    require(len(data) >= 12, "IMAGE_FILE_TOO_SHORT")
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image/png"
    if data[:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    raise Hold("JPEG_OR_PNG_ONLY")


def inspect_file(path: Path) -> tuple[bytes, str]:
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), "LOCAL_ORIGINAL_PHOTO_FILE_REQUIRED")
    size = p.stat().st_size
    require(12 <= size <= MAX_BYTES, "PHOTO_FILE_EXCEEDS_SCOUT_BOUNDS")
    with p.open("rb") as f:
        raw = f.read(MAX_BYTES + 1)
    require(len(raw) == size, "PHOTO_FILE_CHANGED_DURING_READ")
    return raw, media_type(raw)


def validate_evidence(lead: Any, evidence: Any, photo_path: Path) -> dict:
    source = validate_lead(lead)
    item = exact(evidence, {
        "schema", "lead_ref", "origin_role", "original_bytes_sha256",
        "original_byte_count", "content_type", "device_authenticated",
        "camera_capture_authenticated", "rights_inferred_from_photo",
        "hazards_screened_by_machine", "photo_included_in_receipt",
    }, "PHOTO_EVIDENCE_EXACT_FIELDS_REQUIRED")
    require(
        item["schema"] == PHOTO
        and item["lead_ref"] == source["lead_ref"]
        and item["origin_role"] == "OPERATOR_SELECTED_LOCAL_IMAGE_UNVERIFIED"
        and item["device_authenticated"] is False
        and item["camera_capture_authenticated"] is False
        and item["rights_inferred_from_photo"] is False
        and item["hazards_screened_by_machine"] is False
        and item["photo_included_in_receipt"] is False
        and type(item["original_byte_count"]) is int
        and 12 <= item["original_byte_count"] <= MAX_BYTES
        and type(item["original_bytes_sha256"]) is str
        and len(item["original_bytes_sha256"]) == 64
        and all(c in "0123456789abcdef" for c in item["original_bytes_sha256"]),
        "PHOTO_CANNOT_MINT_PHYSICAL_OR_LEGAL_AUTHORITY"
    )
    raw, guessed_type = inspect_file(photo_path)
    require(item["original_byte_count"] == len(raw)
            and item["original_bytes_sha256"] == hashlib.sha256(raw).hexdigest()
            and item["content_type"] == guessed_type,
            "PHOTO_FILE_OR_EVIDENCE_CHANGED")
    return item


def scout(lead: Any, evidence: Any, photo_path: Path) -> dict:
    source = validate_lead(lead)
    checked = validate_evidence(source, evidence, photo_path)
    unreviewed = assess(source)
    require(unreviewed["status"] == "HOLD_AND_RESEARCH"
            and "NO_SCOPED_AUTHORITY_REVIEW" in unreviewed["reason_codes"],
            "SCOUT_MUST_START_WITH_UNREVIEWED_FORAGE_001_HOLD")
    body = {
        "schema": SCOUT,
        "source_lead_ref": source["lead_ref"],
        "original_lead_sha256": digest(source),
        "photo_evidence_digest": digest(checked),
        "original_photo_sha256": checked["original_bytes_sha256"],
        "parent_foraging_assessment_id": unreviewed["assessment_id"],
        "parent_foraging_reason_codes": unreviewed["reason_codes"],
        "operator_selected_category": source["category"],
        "candidate_affordances": list(SUGGESTIONS[source["category"]]),
        "affordances_method": "STATIC_CATEGORY_HEURISTIC_NOT_GHOT_EXECUTION_OR_IMAGE_RECOGNITION",
        "state": "DISCOVERED_UNREVIEWED_PHOTO_PROSPECT_HOLD",
        "hazards_not_independently_screened": True,
        "authority_for_entry_or_removal": False,
        "land_or_owner_rights_verified": False,
        "image_classifier_executed": False,
        "camera_device_authenticated": False,
        "human_permission_review_completed": False,
        "physical_item_retrieved": False,
        "robot_or_printer_activated": False,
        "robot_garden_inventory_delta": 0,
        "jubilee_treasury_inventory_delta": 0,
    }
    return sealed(body, "scout_id", "static-os-forage-scout-002")


def cold_replay(lead: Any, evidence: Any, photo_path: Path, candidate: Any) -> dict:
    require(type(candidate) is dict and candidate == scout(lead, evidence, photo_path),
            "SCOUT_ORIGINAL_PHOTO_COLD_REPLAY_DISAGREEMENT")
    return candidate
