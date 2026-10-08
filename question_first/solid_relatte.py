"""STATIC-CAD-005 native reLATTE crossing of the inspectable decision ledger.

Each donor record is revalidated against bytes. The native reLATTE R14
roundtrip owns its signatures, transport, RECEIVE and independent HOLD.
STATIC OS only carries exact payload refs and cold-verifies all returned
cryptographic signatures. Neither public output nor report contains keys.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from question_first.session import Hold, require
from question_first.solid_body import verify_files

SCHEMA = "static-os.cad-relatte-request/v0"
ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _refs(folder: Path) -> list[dict]:
    return [
        {"address": "sha256:"+sha(folder/name), "role": role,
         "media_type": media}
        for name,role,media in (
            ("sketch.json","source-sketch","application/json"),
            ("design-trace.json","declared-decision-history","application/json"),
            ("solid.step","occt-step-solid","model/step"),
            ("solid.stl","occt-stl-mesh","model/stl"),
        )
    ]


def _invoke(mode: str, payload: Path, *, timeout=80) -> dict:
    script=ROOT/"scripts"/"solid-relatte-bridge.mjs"
    require(script.is_file(), "NATIVE_RELATTE_BRIDGE_MISSING")
    require((ROOT/"external"/"reLATTE"/"src"/"index.ts").is_file(),
            "PINNED_NATIVE_RELATTE_SOURCE_MISSING")
    try:
        proc=subprocess.run(
            ["node",str(script),mode,str(payload)],capture_output=True,
            text=True,timeout=timeout,cwd=str(ROOT),check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise Hold("RELATTE_OUTCOME_UNKNOWN_NO_AUTORETRY") from exc
    require(proc.returncode == 0, "NATIVE_RELATTE_REFUSED:"+proc.stderr[:180])
    try:
        body=json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise Hold("RELATTE_DID_NOT_RETURN_JSON") from exc
    require(type(body) is dict,"RELATTE_BAD_VERIFICATION_OBJECT")
    return body


def request_for(folder: Path, runtime: Path) -> dict:
    manifest,trace,report=verify_files(folder)
    rt=Path(runtime).resolve()
    require(rt != Path(folder).resolve()
            and not str(rt).startswith(str(Path(folder).resolve())+os.sep),
            "RELATTE_SECRET_ROOT_MUST_NOT_BE_PUBLIC_PACKAGE")
    t0=datetime.now(timezone.utc)
    fmt=lambda t:t.isoformat(timespec="milliseconds").replace("+00:00","Z")
    fingerprint=trace["trace_id"].split(":")[-1]
    key="cad005-"+fingerprint[:20]
    req={
        "schema":"relatte.opaque-roundtrip-request/v0",
        "spec":{
            "schema":"relatte.opaque-organ-spec/v0",
            "family_ref":"static-os.static-cad-005/v0",
            "donor_contract_ref":"static-os:CAD005_DECISION_LEDGER",
            "artifact_kind":"STATIC_CAD_005_DECISION_TRACE",
            "source_world":"static-os:cad-workbench",
            "source_particular":"static-os:solid:"+manifest["manifest_id"],
            "source_history_head":trace["trace_id"],
            "payload_refs":_refs(folder),
            "donor_claims":{
                "source_sketch_id":trace["source_sketch_id"],
                "decision_event_count":len(trace["events"]),
                "occt_engine_executed":True,
                "step_reimport_verified":True,
                "private_model_reasoning_captured":False,
                "manufacturing_permission":False,
                "source_authority_transferred":False,
            },
            "requested_effect":{"kind":"PRESENT_FOR_LOCAL_REVIEW",
                                "automatic_execution":False,
                                "fabrication_authorized":False},
            "return_address":None,
            "created_at":fmt(t0),
        },
        "receiver_root":str(rt/"receiver"),
        "receiver":{
            "world_id":"static-os:cad-independent-receiver",
            "receiver_particular":"cad005:audit-room",
            "contract_ref":"static-os:CAD_EVIDENCE_REVIEW_ONLY",
        },
        "bundle_path":str(rt/"transport"/(key+".json")),
        "result_path":str(rt/"receipts"/(key+".json")),
        "disposition":"HOLD",
        "transport_created_at":fmt(t0+timedelta(milliseconds=1)),
        "received_at":fmt(t0+timedelta(milliseconds=2)),
        "disposed_at":fmt(t0+timedelta(milliseconds=3)),
        "route_note":"STATIC-CAD-005 evidence donor to independently owned HOLD",
    }
    return {"schema":SCHEMA,"trace_id":trace["trace_id"],"request":req}


def cross(folder: Path, runtime: Path) -> dict:
    directory=Path(folder).resolve()
    require(not (directory/"relatte-evidence.json").exists(),
            "CAD_RELATTE_ALREADY_CROSSED_NO_AUTORETRY")
    runtime=Path(runtime).expanduser().resolve()
    require(not runtime.exists(),"PRIVATE_RELATTE_ROOT_ALREADY_OCCUPIED")
    runtime.mkdir(mode=0o700,parents=True,exist_ok=False)
    request=request_for(directory,runtime)
    (runtime/"crossing-request.json").write_text(
        json.dumps(request,sort_keys=True,indent=2)+"\n")
    evidence=_invoke("cross",runtime/"crossing-request.json")
    out=directory/"relatte-evidence.json"
    with out.open("x",encoding="utf-8") as writer:
        json.dump(evidence,writer,sort_keys=True,indent=2)
        writer.write("\n")
    verify_native(directory)
    return evidence


def verify_native(folder: Path) -> dict:
    directory=Path(folder).resolve()
    manifest,trace,report=verify_files(directory)
    file=directory/"relatte-evidence.json"
    evidence=json.loads(file.read_text())
    require(evidence.get("trace_id")==trace["trace_id"]
            and evidence.get("expected_refs")==_refs(directory),
            "RELATTE_PUBLIC_PAYLOADS_DO_NOT_BIND_CURRENT_BYTES")
    result=evidence.get("result")
    crossing=result.get("crossing") if type(result) is dict else {}
    require(type(crossing) is dict
            and crossing.get("source_particular") ==
                "static-os:solid:"+manifest["manifest_id"]
            and crossing.get("source_history_head")==trace["trace_id"]
            and crossing.get("payload_refs")==_refs(directory)
            and crossing.get("extensions",{}).get("organ_adapter",{}).get(
                "donor_claims",{}).get("source_sketch_id")==trace["source_sketch_id"],
            "RELATTE_DONOR_BINDING_TAMPERED")
    validation=_invoke("verify",file,timeout=25)
    require(validation.get("status")=="SIGNED_CROSSING_AND_RECEIVE_HOLD_VERIFIED"
            and validation.get("source_trace_id")==trace["trace_id"]
            and validation.get("disposition")=="HOLD"
            and validation.get("fabrication_grant") is False,
            "NATIVE_RELATTE_VERIFIER_DID_NOT_CONFIRM_HOLD")
    return validation
