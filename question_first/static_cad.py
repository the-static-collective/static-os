"""STATIC-CAD-003: typed parametric layout compiled from APPARATUS-COMPILER-002.

This compiler emits an engineering *candidate*, not a certified mechanism.
It uses exact integer micrometres, no eval, no invented source ancestry,
no OS boot/physical actuation, and no auto-fabrication. The drawing is a
mounting/envelope reference, NOT true involute gear geometry or fit analysis.
"""
from __future__ import annotations

import copy
import math
from typing import Any
from crank.runtime import digest
from question_first.session import Hold, require, _sealed, _check_seal
from question_first.apparatus_compiler import verify_plan

PROJECT = "static-os.cad-project/v0"
SEED = "static-os.cad-design-seed/v0"
SAFE_MATERIALS = {"UNSPECIFIED", "ALUMINUM_CANDIDATE", "PLA_CANDIDATE"}
COMPONENTS = ("base-plate", "bearing-upright")
MAX_DIM = 500_000  # 500mm for intentionally bounded first specimen
LIMITS = {
    "module_um": (500, 5_000),
    "base_width_um": (35_000, 160_000),
    "base_thickness_um": (3_000, 15_000),
    "wall_um": (5_000, 20_000),
    "upright_height_um": (15_000, 120_000),
    "bore_diameter_um": (3_000, 15_000),
    "mount_hole_diameter_um": (2_000, 9_000),
    "mount_margin_um": (8_000, 25_000),
    "clearance_um": (500, 5_000),
}
PARAMETERS = set(LIMITS) | {"material"}


def _value(seed: dict, key: str) -> int:
    raw = seed[key]
    lo, hi = LIMITS[key]
    require(type(raw) is int and lo <= raw <= hi, "INVALID_CAD_DIMENSION:" + key)
    return raw


def validate_seed(seed: Any) -> dict:
    require(type(seed) is dict and set(seed) == {
        "schema", "apparatus_plan_id", "selected_candidate_id",
        "parameters", "revision_parent_id",
    }, "EXACT_CAD_SEED_REQUIRED")
    require(seed["schema"] == SEED, "UNSUPPORTED_CAD_SEED")
    require(type(seed["apparatus_plan_id"]) is str
            and seed["apparatus_plan_id"].startswith("static-os-apparatus-plan-v0:"),
            "APPARATUS_PARENT_REQUIRED")
    require(seed["selected_candidate_id"] in {"gear-then-screw", "direct-screw"},
            "UNKNOWN_APPARATUS_CANDIDATE")
    params = seed["parameters"]
    require(type(params) is dict and set(params) == PARAMETERS,
            "CAD_PARAMETERS_EXACT_SET_REQUIRED")
    for name in LIMITS:
        # read via dimensions dictionary, never execute expressions in inputs.
        lo, hi = LIMITS[name]
        require(type(params[name]) is int and lo <= params[name] <= hi,
                "INVALID_CAD_DIMENSION:" + name)
    require(params["material"] in SAFE_MATERIALS, "UNKNOWN_MATERIAL_PROPOSAL")
    parent = seed["revision_parent_id"]
    require(parent is None or (type(parent) is str and
            parent.startswith("static-os-cad-project-v0:") and len(parent.split(":")[-1]) == 64),
            "INVALID_CAD_REVISION_PARENT")
    return seed


def _hole_centers(length: int, width: int, margin: int) -> list[dict]:
    return [{"x_um": x, "y_um": y} for x, y in (
        (margin, margin), (length - margin, margin),
        (margin, width - margin), (length - margin, width - margin),
    )]


def compile_project(seed: Any, apparatus_plan: Any) -> dict:
    s = validate_seed(seed)
    parent = verify_plan(apparatus_plan)
    require(s["apparatus_plan_id"] == parent["plan_id"],
            "CAD_APPARATUS_PARENT_MISMATCH")
    candidates = [c for c in parent["assembly_candidates"]
                  if c["candidate_id"] == s["selected_candidate_id"]]
    require(len(candidates) == 1 and parent["status"] == "PROPOSAL_ONLY",
            "NO_VERIFIED_APPARATUS_GRAPH")
    chosen = candidates[0]
    require(chosen["simulation_only"] is True
            and chosen["execution_contract"] == "ONE_NATIVE_GHOT_INSTRUMENT_DISPATCH",
            "APPARATUS_CANNOT_GRANT_FABRICATION")

    p = s["parameters"]
    n = parent["question_seed"]
    pitch_diameter = p["module_um"] * n["driven_teeth"]
    driven_radius = pitch_diameter // 2
    base_length = pitch_diameter + 2 * p["wall_um"] + 2 * p["mount_margin_um"]
    base_width = p["base_width_um"]
    upright_width = pitch_diameter + 2 * p["wall_um"]
    upright_depth = p["bore_diameter_um"] + 2 * p["wall_um"] + 4_000
    upright_x = (base_length - upright_width) // 2
    upright_y = (base_width - upright_depth) // 2
    clearance = p["clearance_um"]
    hd = p["mount_hole_diameter_um"]
    bore = p["bore_diameter_um"]

    for dim in (base_length, base_width, upright_width, upright_depth,
                p["upright_height_um"]):
        require(0 < dim <= MAX_DIM, "CAD_BOUNDED_ENVELOPE_EXCEEDED")
    require(upright_depth + 2 * clearance <= base_width,
            "UPRIGHT_EXCEEDS_BASE_CLEARANCE")
    require(p["mount_margin_um"] >= hd // 2 + clearance,
            "MOUNT_HOLE_EDGE_CLEARANCE_FAILED")
    require(2 * p["mount_margin_um"] + hd + 2 * clearance < base_width,
            "MOUNT_HOLE_ROWS_COLLIDE")
    require(2 * p["mount_margin_um"] + hd + 2 * clearance < base_length,
            "MOUNT_HOLE_COLUMNS_COLLIDE")
    require(upright_depth >= bore + 2 * p["wall_um"],
            "UPRIGHT_BORE_REQUIRES_MORE_WALL")
    require(pitch_diameter >= bore + 2 * clearance,
            "GEAR_REFERENCE_ENVELOPE_TOO_SMALL")
    require(upright_x >= p["mount_margin_um"] - clearance
            and upright_y >= 0, "UPRIGHT_PLACEMENT_INVALID")

    base = {
        "id": "base-plate", "type": "EXTRUDED_RECTANGLE_WITH_BORE_PATTERN",
        "bbox_um": [0, 0, 0, base_length, base_width, p["base_thickness_um"]],
        "dimensions_um": [base_length, base_width, p["base_thickness_um"]],
        "origin_um": [0, 0, 0],
        "holes": [{"diameter_um": hd, "center_um": [point["x_um"], point["y_um"]],
                   "axis": "Z_THROUGH"} for point in _hole_centers(
                    base_length, base_width, p["mount_margin_um"])],
        "material_candidate": p["material"],
        "quantity": 1,
    }
    upright = {
        "id": "bearing-upright", "type": "EXTRUDED_RECTANGLE_WITH_BORE_PATTERN",
        "bbox_um": [upright_x, upright_y, p["base_thickness_um"],
                    upright_x + upright_width, upright_y + upright_depth,
                    p["base_thickness_um"] + p["upright_height_um"]],
        "dimensions_um": [upright_width, upright_depth, p["upright_height_um"]],
        "origin_um": [upright_x, upright_y, p["base_thickness_um"]],
        "holes": [{"diameter_um": bore,
                   "center_um": [upright_width // 2, upright_depth // 2],
                   "axis": "Z_THROUGH"}],
        "material_candidate": p["material"],
        "quantity": 1,
    }
    # Axial cuts are real boolean candidates for FreeCAD; no fake STL mesh.
    parts = [base, upright]
    for i, a in enumerate(parts):
        x0, y0, z0, x1, y1, z1 = a["bbox_um"]
        require(x0 >= 0 and y0 >= 0 and z0 >= 0 and x1 > x0 and y1 > y0
                and z1 > z0, "INVALID_PART_AABB")
        for b in parts[i+1:]:
            u0, v0, w0, u1, v1, w1 = b["bbox_um"]
            volume_overlap = (
                min(x1, u1) > max(x0, u0)
                and min(y1, v1) > max(y0, v0)
                and min(z1, w1) > max(z0, w0)
            )
            require(not volume_overlap, "PARTS_INTERFERE_BY_BOUNDING_BOX")
    # This is a static assembly layout, NOT full kinematic verification.
    nodes = chosen["nodes"]
    derived = {
        "driven_pitch_diameter_um": pitch_diameter,
        "reference_gear_radius_um": driven_radius,
        "expected_ideal_axial_um": (
            -(n["driver_teeth"] * n["input_turns"] * n["lead_um_per_turn"])
            / n["driven_teeth"] if chosen["mode"] == "geared"
            else n["input_turns"] * n["lead_um_per_turn"]
        ),
        "travel_envelope_um": abs(n["driver_teeth"] * n["input_turns"]
                                  * n["lead_um_per_turn"]) // n["driven_teeth"]
                                  + 2 * clearance,
    }
    # For non-integral predictions, keep exact numerator and denominator,
    # rather than float in the actual contract.
    from fractions import Fraction
    axial = (Fraction(-n["driver_teeth"] * n["input_turns"]
                      * n["lead_um_per_turn"], n["driven_teeth"])
             if chosen["mode"] == "geared"
             else Fraction(n["input_turns"] * n["lead_um_per_turn"]))
    derived["expected_ideal_axial_um"] = {
        "numerator": axial.numerator, "denominator": axial.denominator,
    }
    body = {
        "schema": PROJECT,
        "cad_seed": s,
        "source_apparatus_plan": parent,
        "source_question_graph_id": chosen["candidate_id"],
        "design_method": "PARAMETRIC_REFERENCE_LAYOUT_NOT_AUTOCAD_EQUIVALENCE",
        "geometric_kernel": "INTEGER_UM_WITH_FREECAD_BOOLEAN_EXPORT_CANDIDATE",
        "units": "micrometres",
        "typed_assembly_graph": copy.deepcopy(nodes),
        "parameters_resolved": copy.deepcopy(p),
        "derived": derived,
        "parts": parts,
        "mates": [{"kind": "COINCIDENT_PLANE",
                   "a": "base-plate:TOP", "b": "bearing-upright:BOTTOM",
                   "residual_um": 0}],
        "drawing_views": ["BASE_TOP_WITH_HOLES_AND_GEAR_PITCH_REFERENCE",
                          "UPRIGHT_ELEVATION"],
        "constraints": {
            "mount_holes_inside": True,
            "bearing_bore_wall": True,
            "axis_aligned_bbox_noninterference": True,
            "plane_mate_satisfied": True,
            "dimensions_bounded": True,
        },
        "material_specified": p["material"] != "UNSPECIFIED",
        "material_mechanical_properties_tested": False,
        "source_bytes_verified": False,
        "source_attribution": "CATALOG_REFERENCE_CONCEPTUAL_ANALOGY_ONLY",
        "fabrication_allowed": False,
        "physical_validation": "NOT_PERFORMED",
        "geometric_boolean_executed": False,
        "freecad_engine_tested": False,
        "status": "DESIGN_CANDIDATE_ONLY",
        "authority": "none",
    }
    return _sealed(body, "project_id", "static-os-cad-project-v0:")


def verify_project(value: Any) -> dict:
    project = _check_seal(value, "project_id", "static-os-cad-project-v0:")
    require(project.get("schema") == PROJECT
            and project == compile_project(project["cad_seed"],
                                           project["source_apparatus_plan"]),
            "CAD_PROJECT_CANNOT_RECONSTRUCT")
    return project


def revise_project(parent: Any, seed: Any, apparatus_plan: Any) -> dict:
    previous = verify_project(parent)
    child_seed = validate_seed(seed)
    require(child_seed["revision_parent_id"] == previous["project_id"],
            "CAD_REVISION_MUST_BIND_PARENT")
    require(child_seed["apparatus_plan_id"] == previous["cad_seed"]["apparatus_plan_id"]
            and child_seed["selected_candidate_id"] == previous["cad_seed"]["selected_candidate_id"],
            "CAD_REVISION_CANNOT_SILENTLY_SWITCH_QUESTION")
    require(child_seed["parameters"] != previous["parameters_resolved"],
            "CAD_REVISION_WITHOUT_CHANGE")
    return compile_project(child_seed, apparatus_plan)
