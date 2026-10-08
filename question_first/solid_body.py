"""STATIC-CAD-005: actual OCCT solid generation + inspectable decision evidence.

The operator explicitly runs a software-only CAD kernel. This module cannot
fabricate, print, actuate machinery, grant permission, or infer hidden model
reasoning. It records declared rationale codes, selected features, source
references, verified outcomes, and alternatives—not private chain of thought.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from crank.runtime import digest
from question_first.session import Hold, require, _sealed, _check_seal
from question_first.sketch_solver import verify_sketch

TRACE = "static-os.cad-decision-trace/v0"
EVENT = "static-os.cad-decision-event/v0"
ENGINE = "CADQUERY_OCCT_BREP"
FILES = ("sketch.json", "design-trace.json", "solid.step", "solid.stl",
         "feature-verification.json", "evidence-manifest.json")


def _millimetres(sketch: dict, name: str) -> tuple[float, float]:
    p = sketch["resolved_points"][name]
    return p["x_um"] / 1000, p["y_um"] / 1000


def _profile(sketch: dict):
    import cadquery as cq
    contour = sketch["seed"]["path"]
    first = _millimetres(sketch, contour[0]["start"])
    work = cq.Workplane("XY").moveTo(*first)
    for edge in contour:
        dest = _millimetres(sketch, edge["end"])
        if edge["kind"] == "line":
            work = work.lineTo(*dest)
        else:
            center = _millimetres(sketch, edge["center"])
            beginning = _millimetres(sketch, edge["start"])
            radius = math.dist(beginning, center)
            angle_0 = math.atan2(beginning[1]-center[1], beginning[0]-center[0])
            angle_1 = math.atan2(dest[1]-center[1], dest[0]-center[0])
            sweep = ((angle_1-angle_0) % (2*math.pi)
                     if edge["direction"] == "CCW"
                     else -((angle_0-angle_1) % (2*math.pi)))
            mid = angle_0+sweep/2
            middle = (center[0]+radius*math.cos(mid),
                      center[1]+radius*math.sin(mid))
            work = work.threePointArc(middle, dest)
    return work.close()


def _valid_solid(work, stage: str) -> dict:
    val = work.val()
    require(val is not None and val.isValid(), "INVALID_OCCT_SOLID:" + stage)
    solids = work.solids().vals()
    require(len(solids) == 1, "NOT_EXACTLY_ONE_SOLID:" + stage)
    volume = float(solids[0].Volume())
    require(math.isfinite(volume) and 1 < volume < 1e8,
            "OCCT_VOLUME_NOT_BOUNDED:" + stage)
    box = val.BoundingBox()
    bounds = [round(v, 5) for v in (box.xmin, box.ymin, box.zmin,
                                     box.xmax, box.ymax, box.zmax)]
    require(all(math.isfinite(t) for t in bounds), "INVALID_OCCT_BOUNDS")
    return {"stage": stage, "valid": True, "solid_count": len(solids),
            "volume_mm3": round(volume, 6), "bbox_mm": bounds}


def _event(previous: str | None, ordinal: int, code: str, *,
           sources: list[str], alternatives: list[str],
           selected: str, rationale_code: str,
           observed: dict) -> dict:
    body = {
        "schema": EVENT, "ordinal": ordinal,
        "previous_event_id": previous,
        "decision_code": code,
        "source_refs": sources,
        "alternatives_considered": alternatives,
        "selected": selected,
        "declared_rationale_code": rationale_code,
        "observable_result": observed,
        "authority_effect": "none",
        "model_private_reasoning_captured": False,
    }
    return _sealed(body, "event_id", "static-os-cad-event-v0:")


def validate_trace(trace: object, sketch: dict) -> dict:
    require(type(trace) is dict and trace.get("schema") == TRACE,
            "INVALID_CAD_TRACE")
    source = verify_sketch(sketch)
    require(trace.get("source_sketch_id") == source["sketch_id"],
            "TRACE_SOURCE_SKETCH_MISMATCH")
    events = trace.get("events")
    require(type(events) is list and len(events) == 6, "CAD_TRACE_EVENTS_MISSING")
    previous = None
    expected = ["SOURCE", "SKETCH_TO_SOLID", "PAD", "POCKET",
                "NEUTRAL_EXPORT", "REIMPORT"]
    for i, item in enumerate(events):
        require(type(item) is dict, "BAD_CAD_TRACE_EVENT")
        _check_seal(item, "event_id", "static-os-cad-event-v0:")
        require(item.get("ordinal") == i+1
                and item.get("decision_code") == expected[i]
                and item.get("previous_event_id") == previous
                and item.get("authority_effect") == "none"
                and item.get("model_private_reasoning_captured") is False
                and item.get("source_refs") == [source["sketch_id"]],
                "CAD_TRACE_CHAIN_MISMATCH")
        previous = item["event_id"]
    _check_seal(trace, "trace_id", "static-os-cad-trace-v0:")
    require(trace.get("head") == previous
            and trace.get("physical_action") is False
            and trace.get("status") == "DECLARED_DECISION_AND_KERNEL_EVIDENCE",
            "CAD_TRACE_SEMANTICS_INVALID")
    return trace


def build_solid(sketch: object, output_dir: Path) -> dict:
    source = verify_sketch(sketch)
    require(source["constraint_report"]["state"] == "SOLVED",
            "UNSOLVED_SKETCH_CANNOT_BECOME_SOLID")
    path = Path(output_dir).expanduser().resolve()
    require(not path.exists(), "OUTPUT_ALREADY_EXISTS")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.mkdir(mode=0o700, exist_ok=False)
    import cadquery as cq
    before = _profile(source).extrude(source["features"][0]["depth_um"]/1000)
    pad = _valid_solid(before, "PAD")
    after = before
    depth = source["features"][0]["depth_um"]/1000
    for hole in source["seed"]["holes"]:
        x,y = _millimetres(source, hole["center"])
        radius = hole["radius_um"]/1000
        tool = cq.Workplane("XY", origin=(x,y,-1)).circle(radius).extrude(depth+2)
        after = after.cut(tool)
    pocket = _valid_solid(after, "POCKET")
    require(pocket["volume_mm3"] < pad["volume_mm3"] or not source["seed"]["holes"],
            "POCKET_FAILED_TO_REMOVE_VOLUME")

    # Real native OCCT STEP and tessellated STL bytes, not a macro proposal.
    step_file = path / "solid.step"
    stl_file = path / "solid.stl"
    after.export(str(step_file))
    after.export(str(stl_file),
                 tolerance=0.04, angularTolerance=0.12)
    require(step_file.stat().st_size > 500 and stl_file.stat().st_size > 100,
            "EMPTY_CAD_KERNEL_EXPORT")

    step_reimport = cq.importers.importStep(str(step_file))
    reread = _valid_solid(step_reimport, "STEP_REIMPORT")
    require(abs(reread["volume_mm3"]-pocket["volume_mm3"]) <=
            max(0.01,pocket["volume_mm3"]*1e-6), "STEP_REIMPORT_VOLUME_DISAGREEMENT")
    report = {
        "schema": "static-os.cad-occt-verification/v0",
        "source_sketch_id": source["sketch_id"],
        "engine": ENGINE,
        "cadquery_version": getattr(cq, "__version__", "NOT_EXPOSED"),
        "pad": pad, "pocket": pocket, "step_reimport": reread,
        "verified_closed_solid": True,
        "stl_mesh_watertight_verified": False,
        "step_reimport_verified": True,
        "physical_tolerance_tested": False,
        "manufacturability_verified": False,
        "physical_fabrication": False,
    }
    evidence_refs = [source["sketch_id"]]
    events = []
    def put(code, alternatives, selected, rationale, observed):
        events.append(_event(events[-1]["event_id"] if events else None,
                             len(events)+1, code, sources=evidence_refs,
                             alternatives=alternatives,selected=selected,
                             rationale_code=rationale,observed=observed))
    put("SOURCE",["UNLINKED_GEOMETRY","VERIFIED_004_SOURCE"],
        "VERIFIED_004_SOURCE","PRESERVE_ANCESTRY",
        {"sketch_id":source["sketch_id"],"parent_cad_id":source["cad_parent_id"]})
    put("SKETCH_TO_SOLID",["POLYGON_FACET_APPROXIMATION","OCCT_EXACT_ARC_WIRE"],
        "OCCT_EXACT_ARC_WIRE","REQUIRE_EXACT_CURVE_TOPOLOGY",
        {"profile_edges":len(source["seed"]["path"])})
    put("PAD",["NO_OP","PAD"],
        "PAD","DECLARED_FEATURE_ORDER",pad)
    put("POCKET",["SKIP_POCKETS","POCKET_THROUGH"],
        "POCKET_THROUGH","PRESERVE_DECLARED_HOLES",pocket)
    put("NEUTRAL_EXPORT",["DRAFT_ONLY","STEP_AND_STL"],
        "STEP_AND_STL","CROSS_ENGINE_INSPECTION_REQUIRED",
        {"step_sha256":hashlib.sha256(step_file.read_bytes()).hexdigest(),
         "stl_sha256":hashlib.sha256(stl_file.read_bytes()).hexdigest()})
    put("REIMPORT",["TRUST_EXPORT_CLAIM","REIMPORT_STEP_AND_COMPARE_VOLUME"],
        "REIMPORT_STEP_AND_COMPARE_VOLUME","INDEPENDENT_GEOMETRY_READBACK",reread)
    body = {
        "schema": TRACE, "source_sketch_id":source["sketch_id"],
        "events":events,"head":events[-1]["event_id"],
        "status":"DECLARED_DECISION_AND_KERNEL_EVIDENCE",
        "physical_action":False,
        "hidden_chain_of_thought": "NOT_COLLECTED",
    }
    trace = _sealed(body, "trace_id", "static-os-cad-trace-v0:")
    validate_trace(trace,source)
    data = {
        "sketch.json":source,
        "design-trace.json":trace,
        "feature-verification.json":report,
    }
    for name,value in data.items():
        (path/name).write_text(json.dumps(value,sort_keys=True,indent=2)+"\n")
    for name in ("solid.step","solid.stl"):
        (path/name).chmod(0o600)
    manifest_body = {
        "schema":"static-os.solid-evidence-manifest/v0",
        "source_sketch_id":source["sketch_id"],
        "trace_id":trace["trace_id"],
        "files":{name:hashlib.sha256((path/name).read_bytes()).hexdigest()
                 for name in ("sketch.json","design-trace.json",
                              "feature-verification.json","solid.step","solid.stl")},
        "engine_executed":True,
        "step_reimport_verified":True,
        "physical_fabrication":False,
        "authority":"none",
    }
    manifest = _sealed(manifest_body,"manifest_id","static-os-solid-manifest-v0:")
    (path/"evidence-manifest.json").write_text(json.dumps(manifest,sort_keys=True,indent=2)+"\n")
    return manifest


def verify_files(output_dir: Path, *, inspect_kernel: bool=True) -> tuple[dict,dict,dict]:
    path=Path(output_dir)
    manifest=json.loads((path/"evidence-manifest.json").read_text())
    _check_seal(manifest,"manifest_id","static-os-solid-manifest-v0:")
    require(manifest.get("schema")=="static-os.solid-evidence-manifest/v0"
            and manifest.get("engine_executed") is True
            and manifest.get("step_reimport_verified") is True
            and manifest.get("physical_fabrication") is False,
            "SOLID_MANIFEST_OVERCLAIMS")
    require(set(manifest.get("files",{}))=={
        "sketch.json","design-trace.json","feature-verification.json",
        "solid.step","solid.stl"},"SOLID_MANIFEST_FILE_SET")
    for name,sha in manifest["files"].items():
        require(hashlib.sha256((path/name).read_bytes()).hexdigest()==sha,
                "SOLID_FILE_HASH_MISMATCH:"+name)
    sketch=json.loads((path/"sketch.json").read_text())
    trace=json.loads((path/"design-trace.json").read_text())
    report=json.loads((path/"feature-verification.json").read_text())
    validate_trace(trace,sketch)
    require(trace["trace_id"]==manifest["trace_id"]
            and sketch["sketch_id"]==manifest["source_sketch_id"],
            "SOLID_SOURCE_ID_MISMATCH")
    require(report.get("source_sketch_id")==sketch["sketch_id"]
            and report.get("engine")==ENGINE
            and report.get("physical_fabrication") is False,
            "INVALID_KERNEL_VERIFICATION_REPORT")
    if inspect_kernel:
        import cadquery as cq
        found=_valid_solid(cq.importers.importStep(str(path/"solid.step")),"STEP_REIMPORT")
        require(abs(found["volume_mm3"]-report["pocket"]["volume_mm3"])
                <= max(0.01,found["volume_mm3"]*1e-6),
                "REPLAY_KERNEL_VOLUME_MISMATCH")
    return manifest,trace,report
