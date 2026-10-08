#!/usr/bin/env python3
"""PRINT-011: explicit software slicing, cold packet verification; no printer I/O."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from question_first.session import Hold
from question_first.print_packet import prepare_print,verify_print

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("command",choices=("slice","verify"))
    ap.add_argument("--source",required=True,help="full exact signed CAD-005 solid package")
    ap.add_argument("--packet",required=True,help="fresh output directory for slice; existing directory for verify")
    ap.add_argument("--slicer",default="prusa-slicer",help="operator selected installed native slicer")
    a=ap.parse_args(argv)
    if a.command=="slice":
        packet=prepare_print(Path(a.source),Path(a.packet),slicer=a.slicer)
    else:
        packet=verify_print(Path(a.source),Path(a.packet))
    print(json.dumps({
        "status":"REAL_SLICED_GCODE_CANDIDATE_HELD",
        "packet_id":packet["packet_id"],
        "gcode_sha256":packet["gcode_sha256"],
        "machine_authorized":False,
        "physical_object_printed":False,
        "printer_connected":False,
        "human_machine_profile_selection_required":True,
    },sort_keys=True))
    return 0

if __name__=="__main__":
    try:
        raise SystemExit(main())
    except (Hold,OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as exc:
        print("HOLD: "+str(exc)[:260],file=sys.stderr)
        raise SystemExit(2)
