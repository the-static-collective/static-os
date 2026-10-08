"""STATIC OS PRINT-011: actual slicer-produced G-code, never auto-print.

This module requires native CAD/reLATTE cold verification before slicing, and
rechecks the original source during cold verification. Its virtual generic
profile is deliberately NOT an authorization to use any physical printer.
"""
from __future__ import annotations
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

from crank.runtime import digest
from question_first.session import Hold, require
from question_first.design_capacity import export_candidate, verify_candidate

ROOT=Path(__file__).resolve().parents[1]
SCHEMA="static-os.fff-print-packet/v0"
PROFILE=ROOT/"fixtures/print-011/virtual-pla-180.ini"
MACHINE="VIRTUAL_FFF_PLA_180_NO_PHYSICAL_PRINTER"
ALLOWED={"G0","G1","G28","G90","G92","M82","M83","M84","M104","M109",
         "M140","M190","M106","M107","M73","M117","M201","M203","M204","M205",
         "M220","M221","M400","T0"}
MAX_GCODE_BYTES=16*1024*1024
MAX_LINES=450000
NUM=r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)"
ARGS=re.compile(r"([A-Za-z])("+NUM+r")(?=\s|$)")
CMDS=re.compile(r"^(?:G\d+|M\d+|T\d+)$")

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def jsonfile(p:Path)->dict:
    v=json.loads(p.read_text(encoding="utf-8"))
    require(type(v) is dict,"JSON_OBJECT_REQUIRED")
    return v

def write_new(p:Path,v:dict)->None:
    fd=os.open(str(p),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as f:
        json.dump(v,f,sort_keys=True,indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())

def preflight(gcode:Path)->dict:
    require(gcode.is_file() and 200 < gcode.stat().st_size <= MAX_GCODE_BYTES,
            "SLICER_OUTPUT_MISSING_OR_UNBOUNDED")
    total=0
    active=0
    deposition=0
    xy_moves=0
    bounds={"X":(0.,180.),"Y":(0.,180.),"Z":(0.,180.)}
    heat_max={"M104":225.,"M109":225.,"M140":65.,"M190":65.}
    xye={"X":90.,"Y":90.,"Z":0.}
    for raw in gcode.open("r",encoding="utf-8",errors="strict"):
        total+=1
        require(total<=MAX_LINES and len(raw)<=512,"GCODE_UNBOUNDED")
        command=raw.split(";",1)[0].strip()
        if not command:
            continue
        words=command.split()
        opcode=words[0].upper()
        require(CMDS.fullmatch(opcode) is not None and opcode in ALLOWED,
                "UNRECOGNIZED_OR_UNSAFE_GCODE_OPCODE:"+opcode[:24])
        param_text=command[len(words[0]):].strip().upper()
        fields=list(ARGS.finditer(param_text))
        # No nested command, checksum, arbitrary text/macro or bare script.
        if opcode!="M117":
            consumed="".join(m.group(0) for m in fields)
            compact="".join(param_text.split())
            require(consumed.replace(" ","")==compact,
                    "UNPARSED_GCODE_ARGUMENTS:"+opcode)
        kv={}
        for m in fields:
            k=m.group(1).upper()
            require(k not in kv,"GCODE_DUPLICATE_PARAMETER")
            v=float(m.group(2))
            require(math.isfinite(v),"GCODE_NONFINITE_PARAMETER")
            kv[k]=v
        if opcode in ("G0","G1"):
            require(set(kv).issubset({"X","Y","Z","E","F"}),"UNEXPECTED_MOTION_AXIS")
            if "F" in kv:
                require(0<kv["F"]<=18000,"EXCESSIVE_DECLARED_FEEDRATE")
            for k,(lo,hi) in bounds.items():
                if k in kv:
                    require(lo<=kv[k]<=hi,"VIRTUAL_BED_BOUND_EXCEEDED:"+k)
                    xye[k]=kv[k]
            if "X" in kv or "Y" in kv:
                xy_moves+=1
            if "E" in kv and xy_moves and ("X" in kv or "Y" in kv):
                deposition+=1
        elif opcode=="G92":
            # Coordinate resets other than extruder would defeat XY bounds.
            require(set(kv)=={"E"},"NO_XYZ_COORDINATE_RESET")
        elif opcode in heat_max:
            require("S" in kv and set(kv).issubset({"S","R","T"}) and
                0<=kv["S"]<=heat_max[opcode],"VIRTUAL_TEMPERATURE_EXCEEDED")
        elif opcode=="M106":
            require(set(kv).issubset({"S","P"}) and
                    0<=kv.get("S",255)<=255,"FAN_OUT_OF_BOUNDS")
        active+=1
    require(active>=20 and xy_moves>=10 and deposition>=10,
            "NO_REAL_SLICED_EXTRUSION_PATH")
    return {"schema":"static-os.fff-gcode-preflight/v0",
            "active_instructions":active,"lines":total,"xy_motion_commands":xy_moves,
            "extrusion_candidate_moves":deposition,
            "virtual_bounds_mm":{"x":180,"y":180,"z":180},
            "heat_caps_c":{"nozzle":225,"bed":65},
            "unsupported_machine_commands":0,
            "actual_printer_execution":False,
            "physical_safety_certification":False,
            "warning":"Static bounds/opcode inspection is not firmware simulation, collision analysis, clearance or thermal-safety proof."}

def _source(folder:Path)->dict:
    return export_candidate(Path(folder),"STATIC_CAD_005")

def prepare_print(source:Path,out:Path,*,slicer:str="prusa-slicer")->dict:
    source=Path(source).resolve(strict=True)
    origin=_source(source)
    program=shutil.which(slicer)
    require(program is not None and Path(program).name in ("prusa-slicer","prusa-slicer-console.exe"),
            "REAL_PRUSA_SLICER_BINARY_REQUIRED")
    require(PROFILE.is_file(),"FROZEN_VIRTUAL_PROFILE_MISSING")
    root=Path(out).expanduser().resolve()
    require(not root.exists(),"PRINT_OCCURRENCE_EXISTS_NO_AUTORETRY")
    root.parent.mkdir(parents=True,exist_ok=True)
    root.mkdir(mode=0o700)
    # PREPARED is intentionally persistent even if a slicer crashes: no
    # automatic retry with unknown partial output.
    write_new(root/"PREPARED.json",{
        "schema":"static-os.print-prepared/v0",
        "source_candidate_id":origin["candidate_id"],
        "state":"HOLD_UNTIL_ONE_SELECTED_SOFTWARE_SLICER_RUN",
        "automatic_retry":False,"printer_connection":False})
    write_new(root/"source-design.json",origin)
    shutil.copyfile(PROFILE,root/"profile.ini")
    result_path=root/"toolpath.gcode"
    try:
        version=subprocess.run([program,"--version"],capture_output=True,text=True,
                               timeout=20,check=False)
        require(version.returncode==0,"SLICER_VERSION_NOT_AVAILABLE")
        execution=subprocess.run([program,"--export-gcode","--load",
                        str(root/"profile.ini"),"--center","90,90",
                        "--output",str(result_path),str(source/"solid.stl")],
                        capture_output=True,text=True,timeout=240,check=False)
        require(execution.returncode==0 and result_path.is_file(),
                "REAL_SLICER_DID_NOT_COMPLETE:"+execution.stderr[:160])
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise Hold("SLICER_OUTCOME_UNKNOWN_NO_AUTORETRY") from exc
    report=preflight(result_path)
    write_new(root/"preflight.json",report)
    body={"schema":SCHEMA,"source_design_candidate_id":origin["candidate_id"],
          "source_crossing_id":origin["native_relatte"]["crossing_id"],
          "source_solid_sha256":sha(source/"solid.stl"),
          "profile_sha256":sha(root/"profile.ini"),
          "profile_kind":MACHINE,
          "slicer_software":Path(program).name,
          "slicer_version_claim":version.stdout.strip()[:120],
          "gcode_sha256":sha(result_path),"preflight_sha256":digest(report),
          "prepared_sha256":sha(root/"PREPARED.json"),
          "state":"PRINT_JOB_CANDIDATE_NOT_AUTHORIZED",
          "printer_model_verified":False,"printer_connected":False,
          "machine_motion_executed":False,"plastic_extruded":False,
          "material_reserved":False,"physical_output_created":False,
          "operator_safety_review_completed":False,
          "transmission_enabled":False}
    packet={**body,"packet_id":"static-os-print-011:"+digest(body)}
    write_new(root/"packet.json",packet)
    verify_print(source,root)
    return packet

def verify_print(source:Path,packet_root:Path)->dict:
    origin=_source(Path(source))
    root=Path(packet_root).resolve(strict=True)
    pack=jsonfile(root/"packet.json")
    body={k:v for k,v in pack.items() if k!="packet_id"}
    require(pack.get("packet_id")=="static-os-print-011:"+digest(body)
            and pack.get("schema")==SCHEMA
            and pack.get("state")=="PRINT_JOB_CANDIDATE_NOT_AUTHORIZED"
            and pack.get("profile_kind")==MACHINE
            and pack.get("printer_model_verified") is False
            and pack.get("printer_connected") is False
            and pack.get("machine_motion_executed") is False
            and pack.get("plastic_extruded") is False
            and pack.get("material_reserved") is False
            and pack.get("physical_output_created") is False
            and pack.get("operator_safety_review_completed") is False
            and pack.get("transmission_enabled") is False,
            "PRINT_PACKET_MANUFACTURES_AUTHORITY")
    require(pack["source_design_candidate_id"]==origin["candidate_id"] and
            pack["source_crossing_id"]==origin["native_relatte"]["crossing_id"] and
            pack["source_solid_sha256"]==sha(Path(source)/"solid.stl"),
            "PRINT_PACKET_NOT_FROM_THIS_NATIVE_CAD_SOURCE")
    require(sha(root/"profile.ini")==sha(PROFILE)==pack["profile_sha256"],
            "UNTRUSTED_PHYSICAL_PRINTER_PROFILE")
    require(sha(root/"PREPARED.json")==pack["prepared_sha256"]
            and jsonfile(root/"PREPARED.json")["automatic_retry"] is False,
            "PREPARED_CHECKPOINT_REPLACED")
    require(sha(root/"toolpath.gcode")==pack["gcode_sha256"],
            "PRINT_TOOLPATH_BYTES_CHANGED")
    checked=preflight(root/"toolpath.gcode")
    require(checked==jsonfile(root/"preflight.json")
            and digest(checked)==pack["preflight_sha256"],
            "PRINT_PREFLIGHT_REPORT_CONTRADICTION")
    require(origin==jsonfile(root/"source-design.json"),
            "PRINT_ORIGINAL_EVIDENCE_CHANGED")
    return pack
