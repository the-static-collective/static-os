#!/usr/bin/env python3
"""Export/verify source-owned 013 crossing proposals. Never contact machines."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from question_first.fabrication_request import request_from_original,verify_request
from question_first.session import Hold,require

def read(name):
    value=json.loads(Path(name).read_text(encoding="utf-8"))
    require(type(value) is dict,"JSON_OBJECT_REQUIRED")
    return value

def main():
    p=argparse.ArgumentParser()
    p.add_argument("command",choices=("propose","verify"))
    p.add_argument("--source",required=True)
    p.add_argument("--packet",required=True)
    p.add_argument("--fleet",required=True)
    p.add_argument("--selection",required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    root=Path(a.out).expanduser().resolve()
    fleet=read(a.fleet)
    selection=read(a.selection)
    if a.command=="propose":
        require(not root.exists(),"OCCURRENCE_EXISTS_NO_AUTORETRY")
        candidate=request_from_original(Path(a.source),Path(a.packet),fleet,selection)
        root.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(str(root),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as f:
            json.dump(candidate,f,sort_keys=True,indent=2)
            f.write("\n")
    else:
        candidate=verify_request(Path(a.source),Path(a.packet),fleet,selection,read(a.out))
    print(json.dumps({"status":"THREE_NODE_FABRICATION_PROPOSAL_ONLY",
         "request_id":candidate["request_id"],"selected_nodes":
         [n["machine_id"] for n in candidate["selected_nodes"]],
         "native_cad_cold_verified":True,
         "physical_print_grants_issued":0,
         "physical_parts_created":0},sort_keys=True))

if __name__=="__main__":
    try:raise SystemExit(main())
    except (Hold,ValueError,TypeError,KeyError,OSError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:260],file=sys.stderr)
        raise SystemExit(2)
