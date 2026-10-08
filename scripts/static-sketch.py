#!/usr/bin/env python3
"""STATIC-CAD-004: solve / render / verify a source-linked constrained sketch."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

from question_first.session import Hold,require
from question_first.static_cad import verify_project
from question_first.sketch_solver import compile_sketch
from question_first.sketch_exports import write_package,verify_package


def obj(filename: str) -> dict:
    raw=json.loads(Path(filename).read_text(encoding="utf-8"))
    require(type(raw) is dict,"JSON_OBJECT_REQUIRED")
    return raw


def main(argv: list[str]) -> int:
    parser=argparse.ArgumentParser(description="Finite constrained sketch design")
    parser.add_argument("action",choices=("solve","verify"))
    parser.add_argument("--seed")
    parser.add_argument("--parent-project")
    parser.add_argument("--out-dir",required=True)
    args=parser.parse_args(argv)
    out=Path(args.out_dir).expanduser()
    if args.action=="verify":
        require(args.seed is None and args.parent_project is None,
                "COLD_VERIFICATION_HAS_NO_EXTERNAL_SOURCE_ARGUMENTS")
        saved=verify_package(out)
        print(json.dumps({"status":"EXACT_SKETCH_PACKAGE_VERIFIED",
                          "manifest_id":saved["manifest_id"],
                          "freecad_executed":False},sort_keys=True))
        return 0
    require(args.seed is not None and args.parent_project is not None,
            "SKETCH_AND_SOURCE_PROJECT_REQUIRED")
    require(not out.exists(),"OUTPUT_ALREADY_EXISTS_NO_NEW_COMPUTATION")
    project=verify_project(obj(args.parent_project))
    seed=obj(args.seed)
    sketch=compile_sketch(seed,project)
    result=sketch["constraint_report"]
    if result["state"]!="SOLVED":
        # Surface diagnostics, but cannot turn unready geometry into an export.
        print(json.dumps({"status":"SKETCH_HOLD","constraint_report":result,
                          "sketch_id":sketch["sketch_id"],
                          "physical_effects":False},indent=2))
        return 3
    receipt=write_package(sketch,out)
    print(json.dumps({
        "status":"SKETCH_SOLVED_AND_PACKAGED",
        "sketch_id":sketch["sketch_id"],
        "manifest_id":receipt["manifest_id"],
        "freecad_executed":False,"fabrication_authority":"NONE",
    },sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold,TypeError,KeyError,ValueError,OSError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:230],file=sys.stderr)
        raise SystemExit(2)
