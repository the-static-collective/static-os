"""STATIC-CAD-004: source-bound, bounded 2D parametric sketch constraint solver.

Self-contained numerical damped least squares. This is *not* a production
geometric kernel: finite-difference Jacobians and static rank classification
must not be promoted to a certified kinematics/manufacturing result.
"""
from __future__ import annotations

import math
import re
from typing import Any

from crank.runtime import digest
from question_first.session import Hold, require, _sealed, _check_seal
from question_first.static_cad import verify_project

SEED = "static-os.sketch-seed/v0"
SKETCH = "static-os.solved-sketch/v0"
ID = re.compile(r"^[a-z][a-z0-9_-]{0,31}$")
KINDS = {"fix", "horizontal", "vertical", "distance", "coincident",
         "equal_length", "tangent_line_arc", "point_on_circle"}
MAX_COORD = 500_000  # absolute coordinate in micrometres


def _integer(value: Any, lo: int, hi: int, reason: str) -> int:
    require(type(value) is int and lo <= value <= hi, reason)
    return value


def validate_seed(seed: Any) -> dict:
    require(type(seed) is dict and set(seed) == {
        "schema", "cad_parent_id", "points", "path", "holes",
        "constraints", "features", "revision_parent_id",
    } and seed["schema"] == SEED, "EXACT_SKETCH_SEED_REQUIRED")
    require(type(seed["cad_parent_id"]) is str
            and seed["cad_parent_id"].startswith("static-os-cad-project-v0:"),
            "SOURCE_CAD_PROJECT_REQUIRED")
    parent = seed["revision_parent_id"]
    require(parent is None or (type(parent) is str
            and parent.startswith("static-os-solved-sketch-v0:")
            and len(parent.split(":")[-1]) == 64), "INVALID_SKETCH_REVISION")
    points = seed["points"]
    require(type(points) is dict and 3 <= len(points) <= 20,
            "BOUNDED_POINT_SET_REQUIRED")
    for name, position in points.items():
        require(type(name) is str and ID.fullmatch(name) is not None
                and type(position) is dict
                and set(position) == {"x_um", "y_um"}, "EXACT_NAMED_POINT_REQUIRED")
        for dim in ("x_um", "y_um"):
            _integer(position[dim], -MAX_COORD, MAX_COORD, "POINT_COORD_OUT_OF_BOUNDS")
    path = seed["path"]
    require(type(path) is list and 3 <= len(path) <= 24,
            "BOUNDED_CLOSED_SKETCH_PATH_REQUIRED")
    for edge in path:
        require(type(edge) is dict
                and edge.get("kind") in {"line", "arc"}, "INVALID_PATH_EDGE")
        if edge["kind"] == "line":
            require(set(edge) == {"kind", "start", "end"}, "EXACT_LINE_EDGE_REQUIRED")
        else:
            require(set(edge) == {"kind", "start", "end", "center", "direction"}
                    and edge["direction"] in {"CCW", "CW"}, "EXACT_ARC_EDGE_REQUIRED")
            require(edge["center"] in points, "UNKNOWN_ARC_CENTER")
        for key in ("start", "end"):
            require(type(edge[key]) is str and edge[key] in points,
                    "UNKNOWN_EDGE_ENDPOINT")
        require(edge["start"] != edge["end"], "COLLAPSED_PATH_EDGE")
    for i, edge in enumerate(path):
        following = path[(i + 1) % len(path)]
        require(edge["end"] == following["start"], "PATH_MUST_CLOSE_BY_ID")
    holes = seed["holes"]
    require(type(holes) is list and len(holes) <= 8, "TOO_MANY_HOLES")
    names: set[str] = set()
    for hole in holes:
        require(type(hole) is dict and set(hole) == {"id", "center", "radius_um"}
                and type(hole["id"]) is str and ID.fullmatch(hole["id"])
                and hole["id"] not in names, "INVALID_HOLE")
        names.add(hole["id"])
        require(hole["center"] in points, "HOLE_CENTER_NOT_IN_SKETCH")
        _integer(hole["radius_um"], 1_000, 25_000, "INVALID_HOLE_RADIUS")
    features = seed["features"]
    require(type(features) is list and len(features) in {1, 2},
            "BOUNDED_FEATURE_SEQUENCE_REQUIRED")
    require(type(features[0]) is dict and set(features[0]) == {
        "kind", "depth_um"
    } and features[0]["kind"] == "pad", "FIRST_FEATURE_MUST_BE_PAD")
    _integer(features[0]["depth_um"], 1_000, 30_000, "PAD_DEPTH_OUT_OF_BOUNDS")
    if len(features) == 2:
        require(type(features[1]) is dict
                and features[1] == {"kind": "pocket_through", "holes": names and
                                     [h["id"] for h in holes]},
                "POCKET_FEATURE_MUST_BIND_ALL_HOLES_IN_ORDER")
    require((len(holes) > 0) == (len(features) == 2),
            "HOLES_AND_POCKET_MUST_MATCH")

    constraints = seed["constraints"]
    require(type(constraints) is list and 1 <= len(constraints) <= 80,
            "BOUNDED_CONSTRAINT_SET_REQUIRED")
    for constraint in constraints:
        require(type(constraint) is dict and constraint.get("kind") in KINDS,
                "UNKNOWN_CONSTRAINT_KIND")
        kind = constraint["kind"]
        fields = {
            "fix": {"kind", "point", "x_um", "y_um"},
            "horizontal": {"kind", "a", "b"},
            "vertical": {"kind", "a", "b"},
            "distance": {"kind", "a", "b", "length_um"},
            "coincident": {"kind", "a", "b"},
            "equal_length": {"kind", "a", "b", "c", "d"},
            "tangent_line_arc": {"kind", "line_start", "line_end",
                                  "arc_point", "center"},
            "point_on_circle": {"kind", "point", "center", "radius_um"},
        }[kind]
        require(set(constraint) == fields, "EXACT_CONSTRAINT_FIELDS_REQUIRED")
        for key in fields - {"kind", "x_um", "y_um", "length_um", "radius_um"}:
            require(type(constraint[key]) is str and constraint[key] in points,
                    "UNKNOWN_CONSTRAINT_POINT")
        for key in fields & {"x_um", "y_um"}:
            _integer(constraint[key], -MAX_COORD, MAX_COORD, "CONSTRAINT_FIX_BOUNDS")
        for key in fields & {"length_um", "radius_um"}:
            _integer(constraint[key], 1_000, MAX_COORD, "CONSTRAINT_LENGTH_BOUNDS")
        if "a" in constraint and "b" in constraint:
            require(constraint["a"] != constraint["b"]
                    or kind == "coincident", "ZERO_LENGTH_REFERENCE")
        if kind == "tangent_line_arc":
            require(constraint["line_start"] != constraint["line_end"]
                    and constraint["arc_point"] != constraint["center"],
                    "DEGENERATE_TANGENT_REFERENCE")
    return seed


def _points(keys: list[str], vector: list[float]) -> dict:
    return {name: (vector[i*2], vector[i*2+1]) for i, name in enumerate(keys)}


def _residuals(seed: dict, keys: list[str], x: list[float]) -> list[float]:
    pts = _points(keys, x)
    def v(name: str) -> tuple[float, float]:
        return pts[name]
    def delta(a: str, b: str) -> tuple[float, float]:
        pa, pb=v(a),v(b)
        return pb[0]-pa[0],pb[1]-pa[1]
    def length(a: str, b: str) -> float:
        dx,dy=delta(a,b)
        return math.hypot(dx,dy)
    result=[]
    for c in seed["constraints"]:
        kind=c["kind"]
        if kind=="fix":
            px,py=v(c["point"])
            result.extend([px-c["x_um"]/1000, py-c["y_um"]/1000])
        elif kind=="horizontal":
            result.append(delta(c["a"],c["b"])[1])
        elif kind=="vertical":
            result.append(delta(c["a"],c["b"])[0])
        elif kind=="distance":
            result.append(length(c["a"],c["b"])-c["length_um"]/1000)
        elif kind=="coincident":
            result.extend(delta(c["a"],c["b"]))
        elif kind=="equal_length":
            result.append(length(c["a"],c["b"])-length(c["c"],c["d"]))
        elif kind=="point_on_circle":
            result.append(length(c["point"],c["center"])-c["radius_um"]/1000)
        else:
            dx,dy=delta(c["line_start"],c["line_end"])
            rx,ry=delta(c["center"],c["arc_point"])
            norm=math.hypot(dx,dy)*math.hypot(rx,ry)
            # dimensionless orthogonality, scaled to mm-sized residual.
            result.append(10 * (dx*rx+dy*ry)/max(norm,1e-8))
    return result


def _jac(seed: dict, keys: list[str], x: list[float]) -> list[list[float]]:
    base=_residuals(seed,keys,x)
    mat=[[0.0]*len(x) for _ in base]
    for j in range(len(x)):
        y=x.copy()
        step=1e-5
        y[j]+=step
        v=_residuals(seed,keys,y)
        for i in range(len(base)):
            mat[i][j]=(v[i]-base[i])/step
    return mat


def _solve_linear(mat: list[list[float]], rhs: list[float]) -> list[float]:
    n=len(rhs)
    a=[list(row)+[rhs[i]] for i,row in enumerate(mat)]
    for j in range(n):
        pivot=max(range(j,n),key=lambda k:abs(a[k][j]))
        if abs(a[pivot][j])<1e-14:
            raise Hold("SINGULAR_NUMERIC_STEP")
        a[j],a[pivot]=a[pivot],a[j]
        z=a[j][j]
        for k in range(j,n+1): a[j][k]/=z
        for i in range(j+1,n):
            w=a[i][j]
            for k in range(j,n+1): a[i][k]-=w*a[j][k]
    ans=[0.0]*n
    for j in reversed(range(n)):
        ans[j]=a[j][n]-sum(a[j][k]*ans[k] for k in range(j+1,n))
    return ans


def _rank(jac: list[list[float]], threshold: float=1e-6) -> int:
    # Modified Gram-Schmidt over Jacobian rows; rank <= min(m,n).
    basis=[]
    for row in jac:
        v=row.copy()
        for _ in range(2):
            for q in basis:
                dot=sum(a*b for a,b in zip(v,q))
                v=[a-dot*b for a,b in zip(v,q)]
        length=math.sqrt(sum(a*a for a in v))
        if length>threshold:
            basis.append([a/length for a in v])
    return len(basis)


def _lm(seed: dict, keys: list[str], initial: list[float]) -> tuple[list[float],int,float]:
    x=initial.copy()
    damping=0.01
    iterations=0
    for iteration in range(240):
        iterations=iteration+1
        residual=_residuals(seed,keys,x)
        score=sum(t*t for t in residual)
        if max(abs(r) for r in residual)<1e-7:
            break
        jac=_jac(seed,keys,x)
        n=len(x)
        gram=[[sum(jac[k][i]*jac[k][j] for k in range(len(jac)))
               for j in range(n)] for i in range(n)]
        grad=[sum(jac[k][i]*residual[k] for k in range(len(jac)))
              for i in range(n)]
        for i in range(n): gram[i][i]+=damping
        move=_solve_linear(gram,[-g for g in grad])
        # No arbitrary unbounded motion across space.
        candidate=[max(-500,min(500,x[i]+move[i])) for i in range(n)]
        trial=_residuals(seed,keys,candidate)
        if sum(t*t for t in trial)<score:
            x=candidate
            damping=max(damping*0.4,1e-10)
        else:
            damping=min(damping*8,1e12)
    return x,iterations,max(abs(r) for r in _residuals(seed,keys,x))


def _segments_and_holes(seed: dict, pts: dict[str,dict]) -> dict:
    def xy(name: str) -> tuple[float,float]:
        p=pts[name]
        return p["x_um"]/1000,p["y_um"]/1000
    def distance(a:tuple,b:tuple) -> float:
        return math.hypot(a[0]-b[0],a[1]-b[1])
    poly=[]
    arcs=[]
    for edge in seed["path"]:
        start,end=xy(edge["start"]),xy(edge["end"])
        require(distance(start,end)>0.01,"DEGENERATE_SKETCH_EDGE")
        if not poly: poly.append(start)
        if edge["kind"]=="line":
            poly.append(end)
            continue
        center=xy(edge["center"])
        r0=distance(start,center);r1=distance(end,center)
        require(r0>0.1 and abs(r0-r1)<=0.005,
                "ARC_ENDPOINT_RADIUS_MISMATCH")
        a0=math.atan2(start[1]-center[1],start[0]-center[0])
        a1=math.atan2(end[1]-center[1],end[0]-center[0])
        ccw=edge["direction"]=="CCW"
        sweep=((a1-a0)%(2*math.pi)) if ccw else -((a0-a1)%(2*math.pi))
        require(1e-4<abs(sweep)<2*math.pi-1e-4,
                "ARC_SWEEP_INVALID")
        n=max(3,math.ceil(abs(sweep)/(math.pi/90)))
        for j in range(1,n):
            angle=a0+sweep*j/n
            poly.append((center[0]+r0*math.cos(angle),
                         center[1]+r0*math.sin(angle)))
        poly.append(end)
        arcs.append({"start":edge["start"],"end":edge["end"],
                     "center":edge["center"],"sweep_degrees":round(
                         sweep*180/math.pi,6)})
    require(distance(poly[0],poly[-1])<.003,"SKETCH_PATH_NOT_CLOSED_AFTER_SOLVE")
    poly[-1]=poly[0]
    edges=list(zip(poly[:-1],poly[1:]))
    def orient(a,b,c):
        return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def intersects(a,b,c,d):
        return ((orient(a,b,c)*orient(a,b,d)<-1e-9)
                and (orient(c,d,a)*orient(c,d,b)<-1e-9))
    for i,(a,b) in enumerate(edges):
        for j in range(i+1,len(edges)):
            if j==i+1 or (i==0 and j==len(edges)-1):continue
            c,d=edges[j]
            require(not intersects(a,b,c,d),"SELF_INTERSECTING_SKETCH_PROFILE")
    signed_area=sum(a[0]*b[1]-b[0]*a[1] for a,b in edges)/2
    require(signed_area>1.0,"PROFILE_MUST_BE_CCW_POSITIVE_AREA")
    def inside(point):
        x,y=point
        count=False
        for a,b in edges:
            if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
                count=not count
        return count
    def edge_distance(point,a,b):
        dx=b[0]-a[0];dy=b[1]-a[1]
        k=max(0.0,min(1.0,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/
                       max(dx*dx+dy*dy,1e-12)))
        return distance(point,(a[0]+k*dx,a[1]+k*dy))
    circles=[]
    for hole in seed["holes"]:
        center=xy(hole["center"]);r=hole["radius_um"]/1000
        require(inside(center),"HOLE_CENTER_OUTSIDE_PROFILE")
        require(min(edge_distance(center,a,b) for a,b in edges)>=r+0.5,
                "HOLE_EDGE_CLEARANCE_FAILED")
        for prior in circles:
            require(distance(center,prior["center_mm"])>=r+prior["radius_mm"]+0.5,
                    "HOLE_TO_HOLE_CLEARANCE_FAILED")
        circles.append({"id":hole["id"],"center_mm":center,"radius_mm":r})
    return {"positive_area_mm2":round(signed_area,4),
            "net_area_mm2":round(signed_area-sum(math.pi*h["radius_mm"]**2
                                              for h in circles),4),
            "arc_segments":arcs,"polygon_sample_segments":len(edges),
            "holes_count":len(circles),
            "boolean_geometry_tested":False,
            "source_geometry_status":"POLYLINE_SAMPLING_CHECK_ONLY"}


def compile_sketch(seed: Any, parent: Any) -> dict:
    s=validate_seed(seed)
    cad=verify_project(parent)
    require(s["cad_parent_id"]==cad["project_id"],"CAD_003_PARENT_MISMATCH")
    keys=sorted(s["points"])
    x0=[coord/1000 for name in keys
        for coord in (s["points"][name]["x_um"],s["points"][name]["y_um"])]
    x,steps,error=_lm(s,keys,x0)
    jac=_jac(s,keys,x)
    rank=_rank(jac)
    dof=len(x)-rank
    redundancy=len(jac)-rank
    coords={name:{"x_um":round(x[i*2]*1000),
                  "y_um":round(x[i*2+1]*1000)}
            for i,name in enumerate(keys)}
    stable=[coord/1000 for name in keys for coord in (
        coords[name]["x_um"],coords[name]["y_um"])]
    final_error=max(abs(t) for t in _residuals(s,keys,stable))
    if final_error>0.004:
        status="INCONSISTENT"
    elif dof>0:
        status="UNDERCONSTRAINED"
    elif redundancy>0:
        status="REDUNDANT_CONSTRAINTS"
    else:
        status="SOLVED"
    metrics=None
    if status=="SOLVED":
        metrics=_segments_and_holes(s,coords)
    body={
        "schema":SKETCH, "seed":s, "cad_parent_id":cad["project_id"],
        "resolved_points":coords,
        "constraint_report":{
            "state":status,"variables":len(x),"equation_count":len(jac),
            "jacobian_rank":rank,"degrees_of_freedom":dof,
            "redundant_equations":max(0,redundancy),
            "max_residual_mm":round(final_error,8),"solver_iterations":steps,
            "solver":"BOUNDED_FINITE_DIFFERENCE_LEVENBERG_MARQUARDT",
            "tolerance_mm":0.004,
            "independently_certified":False,
        },
        "geometry_report":metrics,
        "cad_parent":cad,
        "features":s["features"],
        "units":"micrometres",
        "source_image_verified":False,
        "physical_effects":False,
        "freecad_engine_executed":False,
        "fabrication_permission":"NONE",
        "status":"SKETCH_CANDIDATE_ONLY" if status=="SOLVED" else "SKETCH_HOLD",
        "next_execution":"NONE",
    }
    return _sealed(body,"sketch_id","static-os-solved-sketch-v0:")


def verify_sketch(value: Any) -> dict:
    sketch=_check_seal(value,"sketch_id","static-os-solved-sketch-v0:")
    require(sketch.get("schema")==SKETCH and
            sketch==compile_sketch(sketch["seed"],sketch["cad_parent"]),
            "COLD_SKETCH_RECONSTRUCTION_MISMATCH")
    return sketch
