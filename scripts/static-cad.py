#!/usr/bin/env python3
"""STATIC-CAD-003 operator desk: compile/revise/verify design packages.

Source plans are verified against APPARATUS-COMPILER-002; CAD work is inert.
Generated FreeCAD macro is operator-run separately, never invoked here.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from question_first.session import Hold, require
from question_first.apparatus_compiler import verify_plan
from question_first.static_cad import (
    SEED, revise_project, compile_project, verify_project, PARAMETERS
)
from question_first.cad_exports import write_package,verify_package


def read(path: str) -> dict:
    v=json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(v) is dict,"INPUT_MUST_BE_JSON_OBJECT")
    return v


def main(argv: list[str]) -> int:
    parser=argparse.ArgumentParser(
        description="Source-bound parametric design, inert fabrication gate"
    )
    parser.add_argument("action", choices=("compile","revise","verify"))
    parser.add_argument("--apparatus-plan")
    parser.add_argument("--parameters")
    parser.add_argument("--candidate",choices=("direct-screw","gear-then-screw"))
    parser.add_argument("--parent-project")
    parser.add_argument("--out-dir",required=True)
    a=parser.parse_args(argv)
    directory=Path(a.out_dir).expanduser()
    if a.action=="verify":
        require(not any((a.apparatus_plan,a.parameters,a.candidate,a.parent_project)),
                "VERIFY_MUST_BE_READ_ONLY")
        manifest=verify_package(directory)
        print(json.dumps({"status":"VERIFIED_EXACT_CAD_PACKAGE",
                          "manifest_id":manifest["manifest_id"],
                          "cad_kernel_executed":False}))
        return 0
    require(bool(a.apparatus_plan) and bool(a.parameters),
            "PARENT_PLAN_AND_PARAMETERS_REQUIRED")
    params=read(a.parameters)
    require(set(params)==PARAMETERS,"PARAMETER_FILE_FIELDS_CHANGED")
    wrapped=read(a.apparatus_plan)
    source=wrapped.get("plan") if "plan" in wrapped else wrapped
    plan=verify_plan(source)
    if a.action=="revise":
        require(a.parent_project is not None and a.candidate is None,
                "REVISION_REQUIRES_PARENT_WITH_UNCHANGED_QUESTION")
        previous=verify_project(read(a.parent_project))
        chosen=previous["cad_seed"]["selected_candidate_id"]
        previous_id=previous["project_id"]
    else:
        require(a.candidate is not None and a.parent_project is None,
                "COMPILATION_REQUIRES_EXPLICIT_CANDIDATE")
        chosen=a.candidate
        previous_id=None
    seed={
        "schema":SEED,
        "apparatus_plan_id":plan["plan_id"],
        "selected_candidate_id":chosen,
        "parameters":params,
        "revision_parent_id":previous_id,
    }
    proposal=(revise_project(previous,seed,plan) if a.action=="revise"
              else compile_project(seed,plan))
    out=write_package(proposal,directory)
    print(json.dumps({"status":"CAD_CANDIDATE_RENDERED",
                      "project_id":proposal["project_id"],
                      "manifest_id":out["manifest_id"],
                      "outputs":sorted(out["artifact_sha256"]),
                      "physical_effects":False,
                      "freecad_macro_executed":False},indent=2))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold,ValueError,OSError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:240],file=sys.stderr)
        raise SystemExit(2)
