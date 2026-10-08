"""STATIC-CAD-004: exact sketch exports and a separately executable FreeCAD macro.

Generated STL/STEP/FCStd are never claimed in an export package. The
generated macro requires an operator-controlled fresh output directory.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path

from crank.runtime import digest
from question_first.session import Hold, require
from question_first.sketch_solver import verify_sketch

FILES=("sketch.json","drawing.svg","geometry.dxf","features.json",
       "generate-sketch-freecad.FCMacro")
PACKAGE="static-os.sketch-package/v0"


def _pt(points: dict, name: str) -> tuple[float,float]:
    p=points[name]
    return p["x_um"]/1000,p["y_um"]/1000


def _mm(v: int) -> str:
    return f"{v/1000:.3f}"


def svg(sketch: dict) -> str:
    s=verify_sketch(sketch)
    require(s["constraint_report"]["state"]=="SOLVED",
            "UNSOLVED_SKETCH_MUST_NOT_EXPORT")
    pts=s["resolved_points"]
    seed=s["seed"]
    xs=[p["x_um"]/1000 for p in pts.values()]
    ys=[p["y_um"]/1000 for p in pts.values()]
    x0=min(xs)-8;y0=min(ys)-8
    w=max(xs)-x0+14;h=max(ys)-y0+14
    path=[]
    for index,seg in enumerate(seed["path"]):
        x,y=_pt(pts,seg["start"])
        if index==0:path.append(f"M {x:.3f},{y:.3f}")
        u,v=_pt(pts,seg["end"])
        if seg["kind"]=="line":
            path.append(f"L {u:.3f},{v:.3f}")
        else:
            cx,cy=_pt(pts,seg["center"])
            radius=math.hypot(x-cx,y-cy)
            a0=math.atan2(y-cy,x-cx)
            a1=math.atan2(v-cy,u-cx)
            delta=((a1-a0)%(2*math.pi) if seg["direction"]=="CCW"
                   else (a0-a1)%(2*math.pi))
            large=int(delta>math.pi)
            sweep=int(seg["direction"]=="CCW")
            path.append(f"A {radius:.4f},{radius:.4f} 0 {large},{sweep} {u:.3f},{v:.3f}")
    path.append("Z")
    elements=[
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{x0:.3f} {y0:.3f} {w:.3f} {h:.3f}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        f'<path d="{" ".join(path)}" fill="#e2e8f0" stroke="#1e293b" stroke-width=".55"/>',
    ]
    for hole in seed["holes"]:
        x,y=_pt(pts,hole["center"])
        elements.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" '
                        f'r="{hole["radius_um"]/1000:.3f}" '
                        'stroke="#0f766e" fill="white" stroke-width=".5"/>')
    elements.extend([
        f'<text x="{x0+1:.2f}" y="{y0+3.5:.2f}" font-size="2.5">'
        'STATIC-CAD-004 / sketch-space mm / UNVERIFIED ENGINEERING CANDIDATE</text>',
        "</svg>",
    ])
    return "\n".join(elements)+"\n"


def dxf(sketch: dict) -> str:
    s=verify_sketch(sketch)
    require(s["constraint_report"]["state"]=="SOLVED","UNSOLVED_DXF_REFUSED")
    points=s["resolved_points"]
    records=[(0,"SECTION"),(2,"HEADER"),(9,"$ACADVER"),(1,"AC1009"),
             (0,"ENDSEC"),(0,"SECTION"),(2,"ENTITIES")]
    def ent(kind:str,attrs:list[tuple[int,str]]) -> None:
        records.extend([(0,kind),(8,"STATIC_SKETCH")]+attrs)
    for seg in s["seed"]["path"]:
        ax,ay=_pt(points,seg["start"])
        bx,by=_pt(points,seg["end"])
        if seg["kind"]=="line":
            ent("LINE",[(10,f"{ax:.5f}"),(20,f"{ay:.5f}"),
                        (11,f"{bx:.5f}"),(21,f"{by:.5f}")])
        else:
            cx,cy=_pt(points,seg["center"])
            r=math.hypot(ax-cx,ay-cy)
            start=math.degrees(math.atan2(ay-cy,ax-cx))%360
            end=math.degrees(math.atan2(by-cy,bx-cx))%360
            if seg["direction"]=="CW":start,end=end,start
            ent("ARC",[(10,f"{cx:.5f}"),(20,f"{cy:.5f}"),(40,f"{r:.5f}"),
                       (50,f"{start:.5f}"),(51,f"{end:.5f}")])
    for hole in s["seed"]["holes"]:
        cx,cy=_pt(points,hole["center"])
        ent("CIRCLE",[(10,f"{cx:.5f}"),(20,f"{cy:.5f}"),
                      (40,_mm(hole["radius_um"]))])
    records.extend([(0,"ENDSEC"),(0,"EOF")])
    return "\n".join(str(value) for pair in records for value in pair)+"\n"


def features(sketch: dict) -> str:
    s=verify_sketch(sketch)
    require(s["constraint_report"]["state"]=="SOLVED","UNSOLVED_FEATURE_EXPORT_REFUSED")
    return json.dumps({
        "schema":"static-os.sketch-feature-plan/v0",
        "source_sketch_id":s["sketch_id"],
        "ordered_features":s["features"],
        "geometry_report":s["geometry_report"],
        "source_cad_project_id":s["cad_parent_id"],
        "execution":"NOT_PERFORMED",
        "fabrication_authority":"NONE",
    },sort_keys=True,indent=2)+"\n"


def freecad_macro(sketch: dict) -> str:
    s=verify_sketch(sketch)
    require(s["constraint_report"]["state"]=="SOLVED","UNSOLVED_BREP_MACRO_REFUSED")
    data={
        "sketch_id":s["sketch_id"],
        "points":s["resolved_points"],
        "path":s["seed"]["path"],
        "holes":s["seed"]["holes"],
        "features":s["features"],
    }
    payload=json.dumps(data,sort_keys=True,separators=(",",":"))
    macro=r'''# STATIC-CAD-004 — generated source; operator-run FreeCAD B-rep candidate
# No network, actuator, slicing, printer, manufacturing claim or boot.
import json
import math
import os
from pathlib import Path
import FreeCAD as App
import Part
import Import
import Mesh

SOURCE = json.loads(__PAYLOAD__)
location = os.environ.get("STATIC_CAD_SKETCH_FREECAD_OUTPUT")
if not location:
    raise RuntimeError("EXPLICIT_OPERATOR_OUTPUT_REQUIRED")
out = Path(location).expanduser().resolve()
out.mkdir(mode=0o700, parents=False, exist_ok=False)
doc = App.newDocument("QuestionSketch004")

def vertex(name):
    p = SOURCE["points"][name]
    return App.Vector(p["x_um"]/1000,p["y_um"]/1000,0)
edges=[]
for segment in SOURCE["path"]:
    first = vertex(segment["start"])
    last = vertex(segment["end"])
    if segment["kind"]=="line":
        edges.append(Part.makeLine(first,last))
    elif segment["kind"]=="arc":
        center=vertex(segment["center"])
        first_angle=math.atan2(first.y-center.y,first.x-center.x)
        last_angle=math.atan2(last.y-center.y,last.x-center.x)
        radius=(first.sub(center).Length+last.sub(center).Length)/2
        if segment["direction"]=="CCW":
            angle=(last_angle-first_angle)%(2*math.pi)
        else:
            angle=-((first_angle-last_angle)%(2*math.pi))
        mid_angle=first_angle+angle/2
        midpoint=App.Vector(center.x+radius*math.cos(mid_angle),
                            center.y+radius*math.sin(mid_angle),0)
        edges.append(Part.Arc(first,midpoint,last).toShape())
    else:
        raise RuntimeError("BAD_SKETCH_SEGMENT")
wire=Part.Wire(edges)
if not wire.isClosed() or not wire.isValid():
    raise RuntimeError("PROFILE_WIRE_NOT_CLOSED_OR_INVALID")
face=Part.Face(wire)
depth=SOURCE["features"][0]["depth_um"]/1000
solid=face.extrude(App.Vector(0,0,depth))
if len(SOURCE["features"])==2:
    if SOURCE["features"][1]["kind"]!="pocket_through":
        raise RuntimeError("UNSUPPORTED_FEATURE")
    for hole in SOURCE["holes"]:
        center=vertex(hole["center"])
        cutter=Part.makeCylinder(hole["radius_um"]/1000,depth+2,
                                 App.Vector(center.x,center.y,-1))
        solid=solid.cut(cutter)
solid=solid.removeSplitter()
if not solid.isValid() or solid.isNull() or len(solid.Solids)!=1 or solid.Volume<=0:
    raise RuntimeError("INVALID_BREP_RESULT")
obj=doc.addObject("PartDesign::Feature","StaticSketch")
obj.Label="sketch-pad-and-pockets"
obj.Shape=solid
obj.addProperty("App::PropertyString","SourceSketchId")
obj.SourceSketchId=SOURCE["sketch_id"]
doc.recompute()
doc.saveAs(str(out/"sketch-candidate.FCStd"))
Import.export([obj],str(out/"sketch-candidate.step"))
Mesh.export([obj],str(out/"sketch-candidate.stl"))
print("STATIC_CAD_004_BREP_CANDIDATE_EXPORTED_NOT_CERTIFIED")
'''
    return macro.replace("__PAYLOAD__",repr(payload))


def artifacts(sketch: dict) -> dict[str,bytes]:
    s=verify_sketch(sketch)
    require(s["constraint_report"]["state"]=="SOLVED",
            "UNSOLVED_SKETCH_CANNOT_RENDER")
    return {
        "sketch.json":(json.dumps(s,indent=2,sort_keys=True)+"\n").encode(),
        "drawing.svg":svg(s).encode(),
        "geometry.dxf":dxf(s).encode(),
        "features.json":features(s).encode(),
        "generate-sketch-freecad.FCMacro":freecad_macro(s).encode(),
    }


def manifest(sketch: dict, files: dict[str,bytes]) -> dict:
    s=verify_sketch(sketch)
    require(set(files)==set(FILES),"SKETCH_PACKAGE_FILES_MISMATCH")
    body={
        "schema":PACKAGE,
        "sketch_id":s["sketch_id"],
        "parent_cad_project_id":s["cad_parent_id"],
        "artifact_sha256":{name:hashlib.sha256(files[name]).hexdigest()
                           for name in sorted(FILES)},
        "exported":["SVG","ASCII_DXF_R12","FEATURE_PLAN","FREECAD_MACRO_SOURCE"],
        "not_exported":["FCSTD","STEP","STL"],
        "brep_engine_executed":False,
        "manufacturing_authority":"NONE",
        "status":"SOURCE_RECONSTRUCTIBLE_SKETCH_PACKAGE",
    }
    return {**body,"manifest_id":"static-os-sketch-package-v0:"+digest(body)}


def write_package(sketch: dict, directory: Path) -> dict:
    files=artifacts(sketch)
    receipt=manifest(sketch,files)
    files["manifest.json"]=(json.dumps(receipt,sort_keys=True,indent=2)+"\n").encode()
    path=Path(directory).expanduser()
    path.parent.mkdir(parents=True,exist_ok=True)
    path.mkdir(mode=0o700,exist_ok=False)
    for name,data in files.items():
        fd=os.open(str(path/name),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"wb") as out:
            out.write(data)
            out.flush()
            os.fsync(out.fileno())
    return receipt


def verify_package(directory: Path) -> dict:
    path=Path(directory).expanduser()
    sketch=json.loads((path/"sketch.json").read_text(encoding="utf-8"))
    saved=json.loads((path/"manifest.json").read_text(encoding="utf-8"))
    regenerated=artifacts(sketch)
    current={name:(path/name).read_bytes() for name in FILES}
    require(current==regenerated,"COLD_SKETCH_ARTIFACTS_NOT_RECONSTRUCTIBLE")
    require(saved==manifest(sketch,current),
            "COLD_SKETCH_PACKAGE_MANIFEST_MISMATCH")
    return saved
