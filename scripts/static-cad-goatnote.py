#!/usr/bin/env python3
"""STATIC-CAD-006: propose alternatives, choose one, publish GOATnote handoff."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from question_first.session import Hold,require
from question_first.feature_tree import plan_tree,verify_tree
from question_first.cad_goatnote import execute_branch,verify_branch


def read(path: str) -> dict:
    value=json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(value) is dict,"EXACT_JSON_OBJECT_REQUIRED")
    return value


def write_exclusive(target: str, value: dict) -> None:
    p=Path(target).expanduser().resolve()
    p.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(str(p),os.O_WRONLY|os.O_EXCL|os.O_CREAT,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as stream:
        json.dump(value,stream,indent=2,sort_keys=True)
        stream.write("\n")


def main(argv:list[str]) -> int:
    p=argparse.ArgumentParser(description="GOATnote-native CAD feature revision")
    p.add_argument("command",choices=("plan","execute","verify"))
    p.add_argument("--source-sketch")
    p.add_argument("--tree")
    p.add_argument("--selection")
    p.add_argument("--out")
    p.add_argument("--out-dir")
    p.add_argument("--private-relatte-root")
    a=p.parse_args(argv)
    if a.command=="plan":
        require(a.source_sketch and a.out and not any(
            (a.tree,a.selection,a.out_dir,a.private_relatte_root)),
            "PLAN_REQUIRES_ONLY_EXPLICIT_SOURCE_AND_OUTPUT")
        value=plan_tree(read(a.source_sketch))
        write_exclusive(a.out,value)
        print(json.dumps({"status":"FEATURE_TREE_PROPOSAL_ONLY",
                          "tree_id":value["tree_id"],
                          "candidates":[c["id"] for c in value["candidate_revisions"]],
                          "work_executed":False}))
    elif a.command=="execute":
        require(a.tree and a.selection and a.out_dir and a.private_relatte_root
                and not a.source_sketch and not a.out,
                "EXECUTE_REQUIRES_TREE_EXACT_OWNER_SELECTION_AND_TWO_ROOTS")
        result=execute_branch(read(a.tree),read(a.selection),
                    output_root=Path(a.out_dir),
                    private_relatte_root=Path(a.private_relatte_root))
        print(json.dumps({
            "status":"REAL_CAD_SIGNED_HOLD_GOATNOTE_JOURNAL_PROPOSED",
            "manifest_id":result["manifest"]["manifest_id"],
            "selected":result["manifest"]["selected_candidate_id"],
            "browser_imported":False,
            "fabrication_authorized":False
        },sort_keys=True))
    else:
        require(a.out_dir and not any(
            (a.source_sketch,a.tree,a.selection,a.out,a.private_relatte_root)),
            "VERIFY_USES_ONLY_EXACT_OUTPUT_DIRECTORY")
        result=verify_branch(Path(a.out_dir))
        print(json.dumps({
            "status":"COLD_NATIVE_GOATNOTE_RELATTE_CAD_VERIFIED",
            "manifest_id":result["manifest_id"],
            "goatnote_note_id":result["goatnote_source_note_id"],
            "signatures_reissued":False,
            "solids_rebuilt":False,
            "notebook_modified":False
        },sort_keys=True))
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (Hold,ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:260],file=sys.stderr)
        raise SystemExit(2)
