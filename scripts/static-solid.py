#!/usr/bin/env python3
"""STATIC-CAD-005: execute real CAD kernel, cross evidence via native reLATTE.

No fabrication controller, no physical machine grant. A passed --build is
the explicit software kernel invocation, not a human safety authorization.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from question_first.session import Hold,require
from question_first.solid_body import build_solid,verify_files
from question_first.solid_relatte import cross,verify_native


def main(argv):
    p=argparse.ArgumentParser(description="Static-CAD solid and reLATTE witness")
    p.add_argument("operation",choices=("build","cross","verify"))
    p.add_argument("--sketch")
    p.add_argument("--out-dir",required=True)
    p.add_argument("--private-relatte-root")
    a=p.parse_args(argv)
    directory=Path(a.out_dir).expanduser().resolve()
    if a.operation=="build":
        require(a.sketch is not None and a.private_relatte_root is None,
                "BUILD_REQUIRES_EXACT_SOLVED_SKETCH")
        sketch=json.loads(Path(a.sketch).read_text(encoding="utf-8"))
        result=build_solid(sketch,directory)
        out={"status":"REAL_OCCT_SOLID_BUILT","manifest_id":result["manifest_id"],
             "native_relatte_cold_issued":False,"physical_fabrication":False}
    elif a.operation=="cross":
        require(a.sketch is None and a.private_relatte_root is not None,
                "CROSS_REQUIRES_SEPARATE_PRIVATE_RECEIVER_ROOT")
        value=cross(directory,Path(a.private_relatte_root))
        out={"status":"REAL_RELATTE_RECEIVE_AND_HOLD","crossing_id":
             value["result"]["crossing"]["crossing_id"],
             "signatures_verified":True,"fabrication_grant":False}
    else:
        require(a.sketch is None and a.private_relatte_root is None,
                "VERIFY_IS_READ_ONLY")
        verification=verify_native(directory)
        out={"status":"NATIVE_RELATTE_COLD_VERIFIED",
             "crossing_id":verification["crossing_id"],
             "receipt_id":verification["disposition_receipt_id"],
             "physical_fabrication":False}
    print(json.dumps(out,sort_keys=True,indent=2))
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold,OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:240],file=sys.stderr)
        raise SystemExit(2)
