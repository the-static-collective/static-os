"""PRINT-FIELD-012: an open-world, multi-machine *proposal* router.

Uses actual signed Static OS CAD + real 011 held G-code evidence. Accepts any
owner-declared brand/model without pretending that G-code is universal or that
untrusted machine metadata creates print, safety, copyright, or custody rights.
There is deliberately NO transport, network client, serial port or execution.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.session import Hold, require
from question_first.print_packet import verify_print

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "fixtures/printer-field-012/technology-registry.json"
SCHEMA = "static-os.printer-field/v0"
DECLARATION = "static-os.printer-owner-declaration/v0"
FLEET = "static-os.printer-fleet/v0"
OUTCOME = "static-os.printer-compatibility-field/v0"
REQUIRED_FAMILIES = (
    "FFF_FDM", "MSLA", "LASER_SLA", "DLP", "SLS_POLYMER",
    "MJF_POLYMER", "BINDER_JETTING", "MATERIAL_JETTING",
    "METAL_PBF", "DED",
)
MATERIALS = {"PLA", "PETG", "ABS", "TPU", "NYLON_FILAMENT",
             "STANDARD_RESIN", "ENGINEERING_RESIN", "NYLON_POWDER",
             "POLYMER_POWDER", "METAL_POWDER", "CERAMIC_POWDER",
             "PROPRIETARY", "UNKNOWN"}
SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._+:/()-]{0,99}$")
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,99}$")
VIRTUAL_ID = "virtual:fff-pla-180"
VIRTUAL_REFERENCE = "VIRTUAL_FFF_PLA_180_NO_PHYSICAL_PRINTER"


def _exact(value: Any, keys: set[str]) -> bool:
    return type(value) is dict and set(value) == keys


def _label(value: Any) -> bool:
    return type(value) is str and SAFE_LABEL.fullmatch(value) is not None


def _id(value: Any) -> bool:
    return type(value) is str and SAFE_ID.fullmatch(value) is not None


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_registry() -> tuple[dict, dict[str, dict]]:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    require(_exact(registry, {"schema", "purpose", "supported_printer_count_claim",
              "machine_execution_enabled", "families", "laws"})
            and registry["schema"] == "static-os.print-technology-registry/v0"
            and registry["purpose"] == "OPEN_WORLD_MACHINE_DISCOVERY_NOT_HARDWARE_AUTHORITY"
            and registry["supported_printer_count_claim"] == 0
            and registry["machine_execution_enabled"] is False,
            "TECHNOLOGY_REGISTRY_MUST_NOT_CLAIM_PHYSICAL_AUTHORITY")
    entries = registry["families"]
    require(type(entries) is list and len(entries) == len(REQUIRED_FAMILIES),
            "INCOMPLETE_TECHNOLOGY_FAMILY_REGISTRY")
    by_id: dict[str, dict] = {}
    for entry in entries:
        require(_exact(entry, {"id", "process", "required_bridge", "output_class",
                       "reference_adapter", "physical_execution_verified"})
                and entry["id"] in REQUIRED_FAMILIES
                and entry["id"] not in by_id
                and all(_label(entry[k]) for k in
                        ("id", "process", "required_bridge", "output_class"))
                and entry["physical_execution_verified"] is False,
                "TECHNOLOGY_REGISTRY_UNSAFE_OR_AMBIGUOUS")
        require((entry["reference_adapter"] == "VIRTUAL_PRUSASLICER_011"
                 if entry["id"] == "FFF_FDM" else
                 entry["reference_adapter"] is None),
                "TECHNOLOGY_FAMILY_DOES_NOT_HAVE_THIS_DONOR")
        by_id[entry["id"]] = entry
    require(set(by_id) == set(REQUIRED_FAMILIES), "MISSING_PROCESS_FAMILY")
    return registry, by_id


def verify_declaration(machine: Any) -> dict:
    require(_exact(machine, {"schema", "machine_id", "manufacturer", "model",
                            "technology", "build_volume_mm", "material_classes",
                            "profile_ref", "claim_kind", "transport_allowed",
                            "hardware_execution_allowed"}),
            "MACHINE_DECLARATION_EXACT_FIELDS_REQUIRED")
    require(machine["schema"] == DECLARATION and
            _id(machine["machine_id"]) and
            _label(machine["manufacturer"]) and _label(machine["model"]) and
            _label(machine["technology"]) and
            machine["claim_kind"] == "OWNER_DECLARED_UNVERIFIED" and
            machine["transport_allowed"] is False and
            machine["hardware_execution_allowed"] is False,
            "UNTRUSTED_MACHINE_CANNOT_MINT_CONTROL_AUTHORITY")
    dims = machine["build_volume_mm"]
    require(_exact(dims, {"x", "y", "z"}) and
            all(type(dims[k]) in (int, float) and
                math.isfinite(dims[k]) and 1 <= dims[k] <= 5000
                for k in ("x", "y", "z")),
            "MACHINE_BUILD_ENVELOPE_MISSING_OR_INVALID")
    mats = machine["material_classes"]
    require(type(mats) is list and len(mats) == len(set(mats))
            and 1 <= len(mats) <= 12 and
            all(type(m) is str and m in MATERIALS for m in mats),
            "UNKNOWN_OR_DUPLICATE_MATERIAL_CLASS")
    require(machine["profile_ref"] is None or _id(machine["profile_ref"]),
            "PROFILE_POINTER_INVALID")
    return machine


def _solid_dims(source: Path) -> dict:
    # verify_print has already performed cold original CAD / reLATTE verification,
    # including the signed manifest binding feature-verification.json.
    report = json.loads((source / "feature-verification.json").read_text(encoding="utf-8"))
    bounds = report["pocket"]["bbox_mm"]
    require(type(bounds) is list and len(bounds) == 6
            and all(type(x) in (int, float) and math.isfinite(x) for x in bounds),
            "SIGNED_SOLID_ENVELOPE_UNAVAILABLE")
    dim = [round(bounds[i + 3] - bounds[i], 5) for i in range(3)]
    require(all(0 < d <= 5000 for d in dim),
            "SIGNED_SOLID_ENVELOPE_OUTSIDE_DECLARED_LIMITS")
    return dict(zip(("x", "y", "z"), dim))


def compile_field(source: Path, packet_root: Path, fleet: Any) -> dict:
    """Never slices, prints, transmits, books stock or auto-selects a printer."""
    original = verify_print(Path(source), Path(packet_root))
    registry, families = _load_registry()
    require(_exact(fleet, {"schema", "requested_effect", "machines"})
            and fleet["schema"] == FLEET
            and fleet["requested_effect"] == "DISCOVER_ONLY_NO_EXECUTION"
            and type(fleet["machines"]) is list
            and 1 <= len(fleet["machines"]) <= 100,
            "EXPLICIT_BOUNDED_READ_ONLY_FLEET_REQUIRED")
    requested = [verify_declaration(x) for x in fleet["machines"]]
    identities = [x["machine_id"] for x in requested]
    require(len(identities) == len(set(identities)), "MACHINE_IDENTITY_DUPLICATE")
    dims = _solid_dims(Path(source))
    offers = []
    for item in requested:
        tech = item["technology"]
        known = families.get(tech)
        too_small = any(dims[k] > item["build_volume_mm"][k]
                        for k in ("x", "y", "z"))
        is_virtual = item["machine_id"] == VIRTUAL_ID
        require(not is_virtual or
                (tech == "FFF_FDM" and
                 item["manufacturer"] == "Static OS" and
                 item["model"] == "Virtual FFF 180" and
                 item["profile_ref"] == "virtual-pla-180-011" and
                 item["build_volume_mm"] == {"x": 180, "y": 180, "z": 180}
                 and item["material_classes"] == ["PLA"]),
                "VIRTUAL_REFERENCE_MACHINE_ID_IS_RESERVED")
        if known is None:
            route, reason = ("HOLD_UNKNOWN_PROCESS", "UNRECOGNIZED_TECHNOLOGY_NEEDS_NEW_ADAPTER")
        elif too_small:
            route, reason = ("HOLD_DECLARED_ENVELOPE", "SOURCE_AXIS_ENVELOPE_EXCEEDS_OWNER_DECLARATION")
        elif is_virtual:
            route, reason = ("SOFTWARE_TOOLPATH_ONLY", "REAL_011_VIRTUAL_SLICER_PACKET_VERIFIED_NOT_PHYSICAL")
        elif tech == "FFF_FDM":
            route, reason = ("HOLD_MACHINE_PROFILE", "NO_VERIFIED_MODEL_FIRMWARE_AND_MATERIAL_PROFILE")
        else:
            route, reason = ("HOLD_PROCESS_ADAPTER", "NO_VERIFIED_NATIVE_PROCESS_SPECIFIC_BUILD_PIPELINE")
        offers.append({
            "machine_id": item["machine_id"],
            "manufacturer": item["manufacturer"],
            "model": item["model"],
            "technology": tech,
            "machine_claim_class": "OWNER_DECLARED_UNVERIFIED",
            "format_reference": "STL_SHA256_AND_STEP_SHA256_ONLY",
            "required_bridge": known["required_bridge"] if known else "UNKNOWN_ADAPTER_REQUIRED",
            "compatibility_status": route,
            "blocking_reason": reason,
            "original_orientation_assumed": True,
            "input_machine_profile_verified": False,
            "physical_material_available_verified": False,
            "machine_connected": False,
            "physical_execution_authorized": False,
            "automatic_transmission_enabled": False,
            "physical_output_created": False,
            "reference_gcode_sha256": original["gcode_sha256"] if is_virtual and not too_small else None,
        })
    body = {
        "schema": OUTCOME,
        "source_design_candidate_id": original["source_design_candidate_id"],
        "source_print_packet_id": original["packet_id"],
        "technology_registry_sha256": _hash_file(REGISTRY),
        "source_solid_envelope_mm": dims,
        "machine_count": len(offers),
        "recognized_process_families": len(families),
        "machines": offers,
        "status": "DISCOVERY_AND_PROPOSALS_ONLY",
        "machine_authentication": False,
        "rights_established": False,
        "new_slicing_executed": False,
        "physical_printer_connected": False,
        "transport_executed": False,
        "manufactured_parts": 0,
        "treasury_inventory_increased": False,
        "limitations": "This routes proposals across process families, not runnable files for all printers. Actual machine-specific slicing and supervised physical execution remain unimplemented.",
    }
    return {**body, "field_id": "static-os-printer-field-012:" + digest(body)}


def verify_field(source: Path, packet_root: Path, fleet: Any, field: Any) -> dict:
    require(type(field) is dict, "FIELD_OBJECT_REQUIRED")
    expected = compile_field(source, packet_root, fleet)
    require(field == expected, "FIELD_COLD_REPLAY_DISAGREEMENT")
    return expected
