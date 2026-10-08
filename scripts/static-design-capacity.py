#!/usr/bin/env python3
"""Cold-verify native CAD evidence and export proposal-only design capacity."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from question_first.session import Hold,require
from question_first.design_capacity import export_candidate,verify_candidate,FAMILIES

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("export","verify"))
    ap.add_argument("--package",required=True)
    ap.add_argument("--family",choices=FAMILIES,default="STATIC_CAD_005")
    ap.add_argument("--out",required=True,help="new candidate file for export; existing candidate for verify")
    args=ap.parse_args(argv)
    if args.command=="export":
        candidate=export_candidate(Path(args.package),args.family)
        dest=Path(args.out).expanduser().resolve()
        dest.parent.mkdir(parents=True,exist_ok=True)
        fd=os.open(str(dest),os.O_WRONLY|os.O_EXCL|os.O_CREAT,0o600)
        with os.fdopen(fd,"w",encoding="utf-8") as stream:
            json.dump(candidate,stream,sort_keys=True,indent=2)
            stream.write("\n")
    else:
        candidate=json.loads(Path(args.out).read_text(encoding="utf-8"))
        require(candidate.get("family")==args.family,"WRONG_VERIFICATION_FAMILY")
        verify_candidate(Path(args.package),candidate)
    print(json.dumps({
        "status":"COLD_NATIVE_CAD_EVIDENCE_TO_DESIGN_PROPOSAL",
        "candidate_id":candidate["candidate_id"],
        "family":candidate["family"],
        "reLATTE_disposition":"HOLD",
        "treasury_offer_created":False,
        "physical_capacity_created":False,
        "cad_kernel_executed_during_export":False,
        "signatures_issued_during_export":False
    },sort_keys=True))
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (Hold,ValueError,KeyError,TypeError,OSError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:280],file=sys.stderr)
        raise SystemExit(2)
