"""STATIC-CAD-003: deterministic engineering package, not fabricated CAD results.

Emits real SVG and minimal ASCII DXF 2D plan geometry, CSV BOM and an
operator-run FreeCAD macro that *can* generate CAD solids and export
FCStd/STEP/STL if FreeCAD is separately installed. Those 3D outputs are
not claimed to exist merely because the macro was generated.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import os
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.session import Hold, require
from question_first.static_cad import verify_project

MANIFEST = "static-os.cad-artifact-manifest/v0"
FILES = ("project.json", "drawing.svg", "plan.dxf",
         "bill-of-materials.csv", "generate-freecad.FCMacro")


def _mm(value: int) -> str:
    return f"{value / 1000:.3f}"


def svg(project: Any) -> str:
    p = verify_project(project)
    base, upright = p["parts"]
    length, width, thick = base["dimensions_um"]
    ox, oy, _ = upright["origin_um"]
    ux, uy, uz = upright["dimensions_um"]
    L, W = length/1000, width/1000
    pitch = p["derived"]["driven_pitch_diameter_um"] / 1000
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {L+25:.3f} {W+uz/1000+45:.3f}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<rect x="0" y="0" width="{L:.3f}" height="{W:.3f}" '
        'fill="#e2e8f0" stroke="#111827" stroke-width=".5"/>',
        f'<rect x="{ox/1000:.3f}" y="{oy/1000:.3f}" '
        f'width="{ux/1000:.3f}" height="{uy/1000:.3f}" fill="none" '
        'stroke="#0f766e" stroke-width=".45" stroke-dasharray="1.5 1"/>',
        f'<circle cx="{L/2:.3f}" cy="{W/2:.3f}" r="{pitch/2:.3f}" '
        'fill="none" stroke="#c2410c" stroke-width=".35" stroke-dasharray="2 1"/>',
    ]
    for hole in base["holes"]:
        x,y = hole["center_um"]
        parts.append(f'<circle cx="{x/1000:.3f}" cy="{y/1000:.3f}" '
                     f'r="{hole["diameter_um"]/2000:.3f}" fill="white" '
                     'stroke="#111827" stroke-width=".4"/>')
    x,y = upright["holes"][0]["center_um"]
    parts.append(f'<circle cx="{(ox+x)/1000:.3f}" cy="{(oy+y)/1000:.3f}" '
                 f'r="{upright["holes"][0]["diameter_um"]/2000:.3f}" '
                 'fill="white" stroke="#0f766e" stroke-width=".4"/>')
    row = W + 9
    parts.extend([
        f'<text x="0" y="{row-2:.3f}" font-size="3.5" fill="#111827">'
        'TOP / BORE / PITCH REFERENCE (pitch circle is NOT gear teeth)</text>',
        f'<rect x="{ox/1000:.3f}" y="{row:.3f}" '
        f'width="{ux/1000:.3f}" height="{uz/1000:.3f}" '
        'fill="#e2e8f0" stroke="#111827" stroke-width=".45"/>',
        f'<line x1="0" y1="{row+uz/1000:.3f}" x2="{L:.3f}" '
        f'y2="{row+uz/1000:.3f}" stroke="#0f766e" stroke-width=".8"/>',
        f'<text x="0" y="{row+uz/1000+6:.3f}" font-size="3.2" fill="#111827">'
        'SIDE ELEVATION / reference only; no gear teeth or moving shaft</text>',
        '</svg>',
    ])
    return "\n".join(parts)+"\n"


def dxf(project: Any) -> str:
    p = verify_project(project)
    base, upright = p["parts"]
    width, depth, thick = base["dimensions_um"]
    tuples = []
    def entity(kind: str, attrs: list[tuple[int, str]]) -> None:
        tuples.extend([(0,kind), (8, "STATIC_CAD")] + attrs)
    def line(x1: int,y1: int,x2: int,y2: int) -> None:
        entity("LINE",[(10,_mm(x1)),(20,_mm(y1)),(11,_mm(x2)),(21,_mm(y2))])
    def rect(x:int,y:int,w:int,h:int) -> None:
        line(x,y,x+w,y);line(x+w,y,x+w,y+h)
        line(x+w,y+h,x,y+h);line(x,y+h,x,y)
    def circle(x:int,y:int,r:int) -> None:
        entity("CIRCLE",[(10,_mm(x)),(20,_mm(y)),(40,_mm(r))])
    rect(0,0,width,depth)
    for h in base["holes"]:
        x,y=h["center_um"]
        circle(x,y,h["diameter_um"]//2)
    ox,oy,_=upright["origin_um"]
    ux,uy,uz=upright["dimensions_um"]
    rect(ox,oy,ux,uy)
    hx,hy=upright["holes"][0]["center_um"]
    circle(ox+hx,oy+hy,upright["holes"][0]["diameter_um"]//2)
    circle(width//2,depth//2,p["derived"]["driven_pitch_diameter_um"]//2)
    # Side-elevation projection offset in drawing coordinates, not 3D mesh.
    rect(ox,depth+10_000,ux,uz)
    records=[(0,"SECTION"),(2,"HEADER"),(9,"$ACADVER"),(1,"AC1009"),
             (0,"ENDSEC"),(0,"SECTION"),(2,"ENTITIES")]
    records.extend(tuples)
    records.extend([(0,"ENDSEC"),(0,"EOF")])
    return "\n".join(str(v) for item in records for v in item)+"\n"


def bom(project: Any) -> str:
    p = verify_project(project)
    file = io.StringIO()
    writer=csv.writer(file,lineterminator="\n")
    writer.writerow(["part_id","qty","material_candidate","x_um","y_um","z_um",
                     "through_bores","verified_manufacturable"])
    for part in p["parts"]:
        writer.writerow([part["id"],part["quantity"],part["material_candidate"],
                         *part["dimensions_um"],len(part["holes"]),"NO"])
    return file.getvalue()


def freecad_macro(project: Any) -> str:
    """Constructible FreeCAD Python macro; not executed by package generation."""
    p=verify_project(project)
    # Source data are entirely validated integers, enums and static strings;
    # repr of the canonical JSON is a *string literal*, never executable code.
    raw=json.dumps({"project_id":p["project_id"],"parts":p["parts"]},
                   sort_keys=True,separators=(",",":"))
    template=r'''# STATIC-CAD-003: generated, explicit operator-run FreeCAD macro
# No networking, shell, motor, printing, upload, transmission or auto approval.
# Requires FreeCAD's Part, Import, Mesh modules in its own Python environment.
import json
import os
from pathlib import Path
import FreeCAD as App
import Part
import Import
import Mesh

SOURCE = json.loads(__CAD_JSON__)
output = os.environ.get("STATIC_CAD_FREECAD_OUTPUT")
if not output:
    raise RuntimeError("OPERATOR_MUST_SET_STATIC_CAD_FREECAD_OUTPUT")
root = Path(output).expanduser().resolve()
# Refuse existing directory to avoid silent modification/overwrite.
root.mkdir(mode=0o700, parents=False, exist_ok=False)
doc = App.newDocument("StaticCAD003")
solids = []
def mm(um):
    return um / 1000.0
for part in SOURCE["parts"]:
    dx, dy, dz = (mm(v) for v in part["dimensions_um"])
    ox, oy, oz = (mm(v) for v in part["origin_um"])
    shape = Part.makeBox(dx, dy, dz, App.Vector(ox,oy,oz))
    for hole in part["holes"]:
        x, y = (mm(v) for v in hole["center_um"])
        radius = mm(hole["diameter_um"])/2
        tool = Part.makeCylinder(radius,dz+2,
                                 App.Vector(ox+x,oy+y,oz-1),
                                 App.Vector(0,0,1))
        shape = shape.cut(tool)
    shape = shape.removeSplitter()
    if not shape.isValid() or shape.isNull() or shape.Volume <= 0:
        raise RuntimeError("FREECAD_BREP_VALIDATION_FAILED:" + part["id"])
    obj = doc.addObject("PartDesign::Feature",
                        "Cad_" + part["id"].replace("-","_"))
    obj.Label = part["id"]
    obj.Shape = shape
    obj.addProperty("App::PropertyString","StaticProjectId")
    obj.StaticProjectId = SOURCE["project_id"]
    solids.append(obj)
# Reject positive solid overlap; face-to-face contact is allowed.
for i, first in enumerate(solids):
    for second in solids[i+1:]:
        if first.Shape.common(second.Shape).Volume > 1e-7:
            raise RuntimeError("FREECAD_ACTUAL_SOLID_INTERFERENCE")
doc.recompute()
doc.saveAs(str(root / "candidate.FCStd"))
Import.export(solids, str(root / "candidate.step"))
Mesh.export(solids, str(root / "candidate.stl"))
print("STATIC_CAD_FREECAD_EXPORTED_UNVERIFIED_ENGINEERING_CANDIDATE")
'''
    return template.replace("__CAD_JSON__",repr(raw))


def artifacts(project: Any) -> dict[str, bytes]:
    p=verify_project(project)
    return {
        "project.json": (json.dumps(p,sort_keys=True,indent=2)+"\n").encode(),
        "drawing.svg": svg(p).encode(),
        "plan.dxf": dxf(p).encode(),
        "bill-of-materials.csv": bom(p).encode(),
        "generate-freecad.FCMacro": freecad_macro(p).encode(),
    }


def manifest(project: Any, files: dict[str, bytes]) -> dict:
    p=verify_project(project)
    require(set(files)==set(FILES), "STATIC_CAD_OUTPUT_SET_NOT_EXACT")
    body={
        "schema":MANIFEST,
        "project_id":p["project_id"],
        "artifact_sha256":{name:hashlib.sha256(files[name]).hexdigest()
                           for name in sorted(FILES)},
        "exports_created": ["SVG_2D","DXF_R12_2D","BOM_CSV","FREECAD_MACRO_SOURCE"],
        "exports_not_created": ["FCSTD","STEP","STL"],
        "cad_kernel_executed": False,
        "physical_validation": False,
        "fabrication_authority": "none",
        "status":"CANDIDATE_RENDERED_NOT_FABRICATED",
    }
    return {**body,"manifest_id":"static-os-cad-manifest-v0:"+digest(body)}


def write_package(project: Any, folder: Path) -> dict:
    p=verify_project(project)
    dest=Path(folder).expanduser()
    dest.parent.mkdir(parents=True,exist_ok=True)
    # exclusive directory creation; no preexisting package is touched
    dest.mkdir(mode=0o700,exist_ok=False)
    files=artifacts(p)
    out=manifest(p,files)
    files["manifest.json"]=(json.dumps(out,sort_keys=True,indent=2)+"\n").encode()
    for name in list(FILES)+["manifest.json"]:
        target=dest/name
        fd=os.open(str(target),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
        with os.fdopen(fd,"wb") as f:
            f.write(files[name])
            f.flush()
            os.fsync(f.fileno())
    return out


def verify_package(folder: Path) -> dict:
    target=Path(folder).expanduser()
    data=json.loads((target/"manifest.json").read_text())
    p=json.loads((target/"project.json").read_text())
    verify_project(p)
    files={name:(target/name).read_bytes() for name in FILES}
    require(data == manifest(p,files),"CAD_PACKAGE_HASH_OR_ID_MISMATCH")
    # Verify exact geometry exports too, not just rehashing a replaced
    # manifest to bless mismatched drawing or macro content.
    require(files == artifacts(p),"CAD_PACKAGE_CONTENT_DID_NOT_REGENERATE")
    return data
