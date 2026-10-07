#!/usr/bin/env python3
"""Validate the append-only OPEN-PAGE-SPECIMEN-001 -> Open Page 002 roundtrip.

This establishes a bounded repository-local authoring proof, not historical
truth for the depicted images or a consequence outside this repository.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPECIMEN = ROOT / "specimens" / "open-page-001"
ROUNDTRIP = SPECIMEN / "roundtrip-001"

EXPECTED_SOURCE_MANIFEST_BLOB = "a913665b0e7319e782f2237afabc41b5b4d6a7ca"
EXPECTED_SOURCE_PAGE_BLOB = "8bd8a206b121ac682b92d6f7eda107839475aa08"
EXPECTED_BEFORE_HEAD = "1c3741293afd153b3e2d8f5d6ba848e48d2f4110"
EXPECTED_ACT_COMMIT = "20dc9202f08796cd457d0c8f287ba64471300174"

FILES = {
    "manifest": SPECIMEN / "manifest.json",
    "page1": SPECIMEN / "open-page.md",
    "door": ROUNDTRIP / "door-proposal.json",
    "choice": ROUNDTRIP / "choice-receipt.json",
    "act": ROUNDTRIP / "act-contract.json",
    "occurrence": ROUNDTRIP / "occurrence-receipt.json",
    "comparison": ROUNDTRIP / "expectation-comparison.json",
    "page2": ROUNDTRIP / "open-page-002.md",
}


def git_blob_sha1(raw: bytes) -> str:
    return hashlib.sha1(
        f"blob {len(raw)}\0".encode("ascii") + raw
    ).hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError("REFUSE: " + message)


def load() -> dict:
    result = {}
    for name, path in FILES.items():
        raw = path.read_text(encoding="utf-8")
        result[name] = raw if name.startswith("page") else json.loads(raw)
    return result


def validate(overrides: dict | None = None) -> dict:
    data = load()
    if overrides:
        data.update(overrides)

    manifest, door, choice = data["manifest"], data["door"], data["choice"]
    act, occurrence, comparison = data["act"], data["occurrence"], data["comparison"]

    require(
        git_blob_sha1(FILES["manifest"].read_bytes()) == EXPECTED_SOURCE_MANIFEST_BLOB,
        "source manifest bytes changed",
    )
    require(
        git_blob_sha1(FILES["page1"].read_bytes()) == EXPECTED_SOURCE_PAGE_BLOB,
        "original Open Page 001 bytes changed",
    )

    require(
        manifest.get("specimen_id") == "OPEN-PAGE-SPECIMEN-001",
        "wrong source specimen",
    )
    require(manifest.get("consequence", {}).get("state") == "OPEN",
            "source consequence history was retconned")
    require(manifest.get("next", {}).get("state") == "OPEN",
            "source next edge was retconned")
    pinned_sources = {
        part.get("sha256") for part in manifest.get("particulars", [])
    }
    require(pinned_sources == {
        "fba4b22be760c96a783fe05e469a1c3add7363719d9bd2acae43a3d0e92ffcf0",
        "91be56f8cca310713ca74ca5474ec4bbb632655c213221bc2c5e51b6bdc6469a",
    }, "source particular addresses changed")

    require(door.get("schema") == "static-os.life-authoring.door-proposal/v0",
            "wrong door schema")
    require(door.get("status") == "PROPOSAL_ONLY" and
            door.get("semantic_effect") == "none",
            "door gained execution or decision authority")
    require(door.get("source_manifest") == "specimens/open-page-001/manifest.json",
            "door lost its source manifest")
    require(door.get("source_page") == "specimens/open-page-001/open-page.md",
            "door lost its source page")
    require(door.get("required_authority") == "human",
            "door removed human authority requirement")

    require(choice.get("schema") == "static-os.life-authoring.choice-receipt/v0",
            "wrong choice schema")
    require(choice.get("door_id") == door.get("door_id"),
            "choice doesn't select the proposed door")
    require(choice.get("authority") == "human" and
            choice.get("status") == "SELECTED",
            "human selection absent")
    require(choice.get("witness_kind") == "external-live-conversation",
            "choice witness was misrepresented")
    require("OPEN-PAGE-SPECIMEN-001" in choice.get("selection_text", ""),
            "choice does not identify specimen")

    require(act.get("schema") == "static-os.life-authoring.act-contract/v0",
            "wrong act schema")
    require(act.get("authorized_by_choice") == choice.get("choice_id"),
            "act has no matching human choice")
    before = act.get("before", {})
    require(before.get("head_commit") == EXPECTED_BEFORE_HEAD,
            "baseline branch identity was rewritten")
    require(before.get("source_manifest_git_blob") == EXPECTED_SOURCE_MANIFEST_BLOB,
            "baseline manifest identity was rewritten")
    require(before.get("source_open_page_git_blob") == EXPECTED_SOURCE_PAGE_BLOB,
            "baseline page identity was rewritten")
    require(act.get("status") == "AUTHORIZED_NOT_YET_OBSERVED",
            "historical action contract was backdated")

    require(occurrence.get("schema") ==
            "static-os.life-authoring.occurrence-receipt/v0",
            "wrong occurrence schema")
    require(occurrence.get("action_id") == act.get("action_id"),
            "observation not linked to authorized action")
    require(occurrence.get("witness") == "github-api-observation",
            "observation witness was misrepresented")
    require(occurrence.get("status") == "OBSERVED_REPOSITORY_MUTATION",
            "repository act not observed")
    observed = occurrence.get("observed", {})
    require(observed.get("before_head") == EXPECTED_BEFORE_HEAD,
            "observed ancestry mismatch")
    require(observed.get("after_action_commit") == EXPECTED_ACT_COMMIT,
            "act commit reference changed")
    require(observed.get("source_manifest_git_blob") == EXPECTED_SOURCE_MANIFEST_BLOB,
            "observation substituted source manifest")
    require(observed.get("source_open_page_git_blob") == EXPECTED_SOURCE_PAGE_BLOB,
            "observation substituted source page")
    require(observed.get("pull_request") == 44 and
            observed.get("pull_request_draft") is True,
            "observed PR state retconned")
    require(occurrence.get("external_world_consequence") == "NOT_OBSERVED",
            "unwitnessed life consequence promoted")
    require(occurrence.get("original_source_page_rewritten") is False,
            "source page mutation falsely asserted")
    require(occurrence.get("semantic_effect") == "repository-state-only",
            "repository effect promoted beyond scope")

    require(comparison.get("schema") ==
            "static-os.life-authoring.expectation-comparison/v0",
            "wrong comparison schema")
    require(comparison.get("action_id") == act.get("action_id") and
            comparison.get("occurrence_id") == occurrence.get("occurrence_id"),
            "comparison does not cite the witnessed action")
    rows = {row.get("dimension"): row for row in comparison.get("comparisons", [])}
    require(len(rows) == len(comparison.get("comparisons", [])),
            "duplicate comparison dimensions")
    checks = {
        "branch-head-advance": EXPECTED_ACT_COMMIT,
        "source-manifest-immutability": EXPECTED_SOURCE_MANIFEST_BLOB,
        "source-page-immutability": EXPECTED_SOURCE_PAGE_BLOB,
        "append-only-door-choice-action": "three new roundtrip records present",
    }
    for dimension, expected_observation in checks.items():
        row = rows.get(dimension, {})
        require(row.get("status") == "MATCH" and
                row.get("observed") == expected_observation,
                "comparison falsely matches " + dimension)

    verification = rows.get("full-verification", {})
    require(verification.get("status") == "OPEN" and
            verification.get("observed") == "NOT_YET_OBSERVED_AT_ACTION_WITNESS",
            "verification result backdated into the action observation")
    external = rows.get("external-life-effect", {})
    require(external.get("status") == "OPEN" and
            external.get("observed") == "NOT_OBSERVED",
            "external life event fabricated")
    myth = comparison.get("mythic_echo", {})
    require(myth.get("mode") == "artistic" and
            myth.get("historical_claim") is False,
            "mythic page promoted to history")

    page = data["page2"]
    required = [
        "### NOW", "### PROPOSED", "### CHOSEN", "### ACT",
        "### EXPECTED", "### OBSERVED", "### COMPARE",
        "### CONSEQUENCE", "### LINEAGE", "### MYTHIC ECHO",
        "### NEXT",
    ]
    for heading in required:
        require(heading in page, "next page missing " + heading)
    require(EXPECTED_ACT_COMMIT in page, "next page lost act provenance")
    require("NOT" in page and "historical" in page.lower(),
            "next page lost non-history boundary")

    return {
        "status": "PASS",
        "source_specimen": "OPEN-PAGE-SPECIMEN-001",
        "source_manifest_blob": EXPECTED_SOURCE_MANIFEST_BLOB,
        "source_page_blob": EXPECTED_SOURCE_PAGE_BLOB,
        "observed_act_commit": EXPECTED_ACT_COMMIT,
        "next_page": "specimens/open-page-001/roundtrip-001/open-page-002.md",
        "unobserved_external_consequence": True,
        "source_next_remains_open": True,
    }


if __name__ == "__main__":
    try:
        print(json.dumps(validate(), indent=2, sort_keys=True))
    except (ValueError, OSError, json.JSONDecodeError) as error:
        raise SystemExit(str(error))
