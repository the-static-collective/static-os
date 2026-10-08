"""STATIC OS 010: source-owned read-only digital design capacity exports.

Never creates an asset, turns a reLATTE HOLD into ADMIT, changes GOATnote,
executes CAD, or claims physical materials or manufacturability.
Verification cold-reopens existing CAD and calls the *native* reLATTE verifier.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.session import Hold, require
from question_first.solid_body import verify_files
from question_first.solid_relatte import verify_native

SCHEMA = "static-os.regenerative-design-capacity/v0"
FAMILIES = ("STATIC_CAD_005", "STATIC_CAD_006")

def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def _source(folder: Path, family: str) -> dict:
    require(family in FAMILIES, "UNSUPPORTED_DIGITAL_DESIGN_FAMILY")
    root = Path(folder).expanduser().resolve(strict=True)
    if family == "STATIC_CAD_006":
        # This step uses the actual native GOATnote adapter, reLATTE signatures,
        # complete selected feature tree, and cold source reconstruction.
        from question_first.cad_goatnote import verify_branch
        branch = verify_branch(root)
        solid = root / "solid"
    else:
        branch = None
        solid = root

    # The native source checks the solved sketch, exact source files, real OCCT
    # STEP readback, declared event chain and all cryptographic reLATTE receipts.
    manifest, trace, report = verify_files(solid)
    native = verify_native(solid)
    require(native.get("status") == "SIGNED_CROSSING_AND_RECEIVE_HOLD_VERIFIED"
            and native.get("disposition") == "HOLD"
            and native.get("fabrication_grant") is False
            and report.get("physical_fabrication") is False
            and report.get("manufacturability_verified") is False,
            "NATIVE_CAD_SIGNATURE_NOT_A_FABRICATION_GRANT")
    if branch is not None:
        require(branch["branch_sketch_id"] == trace["source_sketch_id"]
                and branch["relatte_crossing_id"] == native["crossing_id"],
                "SELECTED_FEATURE_BRANCH_NOT_SIGNED_SOLID")

    assets = [
        {"role":"source-sketch","sha256":_sha(solid/"sketch.json")},
        {"role":"design-decision-trace","sha256":_sha(solid/"design-trace.json")},
        {"role":"step-brep","sha256":_sha(solid/"solid.step")},
        {"role":"stl-mesh","sha256":_sha(solid/"solid.stl")},
    ]
    require(all(x["sha256"] in manifest["files"].values() for x in assets),
            "EXPORTED_BYTES_NOT_COMMITTED_BY_NATIVE_MANIFEST")
    return {
        "schema":SCHEMA,
        "source_repository":"the-static-collective/static-os",
        "family":family,
        "source_ids":{
            "sketch":trace["source_sketch_id"],
            "decision_trace":trace["trace_id"],
            "solid_manifest":manifest["manifest_id"],
            "feature_branch":branch["manifest_id"] if branch else None,
        },
        "native_relatte":{
            "crossing_id":native["crossing_id"],
            "receive_receipt_id":native["receive_receipt_id"],
            "hold_receipt_id":native["disposition_receipt_id"],
            "disposition":"HOLD",
            "native_signatures_cold_verified":True,
        },
        "artifacts":assets,
        "declared_capacity":{
            "kind":"digital_design",
            "unit":"design",
            "quantity":1,
            "subject":"digitally verified CAD source, STEP and STL",
            "real_software_artifacts":True,
            "fabricated_physical_units":0,
            "engineering_safety_certified":False,
            "legal_rights_verified":False,
            "eligible_for_treasury_receipt":False,
        },
        "authority_effect":"NONE",
        "economic_value_established":False,
        "public_warning":"Cold verified signed digital CAD evidence is not a physical machine, transferable right, cash, manufacturing permission or investment value.",
    }

def export_candidate(folder: Path, family: str="STATIC_CAD_005") -> dict:
    body = _source(folder, family)
    return {**body,"candidate_id":"static-os-design-010:"+digest(body)}

def verify_candidate(folder: Path, candidate: Any) -> dict:
    require(type(candidate) is dict and candidate.get("family") in FAMILIES,
            "BAD_DIGITAL_DESIGN_CANDIDATE")
    expected = export_candidate(folder,candidate["family"])
    require(candidate == expected, "CANDIDATE_NOT_CURRENT_SIGNED_SOURCE")
    return expected
