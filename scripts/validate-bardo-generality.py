#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

SCHEMA="static-os.bardo-generality/v0"
SHA40=re.compile(r"[0-9a-f]{40}\Z")
SB1="sb001-evidence-v0:cbb5e16c8209e1978d1cc1910c4b5128fa58bdab1bb9bbd7d4112ebd0f6c5174"
SB2="sb002-evidence-v0:a44ce387493dec11fbd0902a8ca03f090b3d08ee79db89e53084f84195bbd581"

def validate(v):
    if not isinstance(v,dict) or v.get("schema") != SCHEMA:
        raise ValueError("unsupported bardo-generality schema")
    if v.get("id") != "BARDO-GENERALITY-002":
        raise ValueError("wrong generality id")
    if v.get("status") != "second-family-proven-external":
        raise ValueError("generality status drift")
    specs=v.get("specimens",{})
    if set(specs) != {"sb001","sb002"}:
        raise ValueError("exact two-specimen set required")
    for name in ("sb001","sb002"):
        c=specs[name].get("proof_commit")
        if not isinstance(c,str) or not SHA40.fullmatch(c):
            raise ValueError(f"{name} proof commit must be exact")
        if specs[name].get("membrane_destroyed") is not True:
            raise ValueError(f"{name} membrane destruction must remain proven")
    if specs["sb001"].get("evidence_set_id") != SB1:
        raise ValueError("SB-001 evidence drift")
    if specs["sb002"].get("evidence_set_id") != SB2:
        raise ValueError("SB-002 evidence drift")
    if specs["sb001"].get("family") == specs["sb002"].get("family"):
        raise ValueError("source families must remain materially different")
    if specs["sb001"].get("destination_disposition") == specs["sb002"].get("destination_disposition"):
        raise ValueError("destination outcomes must remain divergent")
    if specs["sb002"].get("destination_disposition") != "HOLD":
        raise ValueError("SB-002 historical disposition is HOLD")
    if specs["sb002"].get("render_authority") is not False:
        raise ValueError("SB-002 HOLD must not mint render authority")
    g=v.get("generality",{})
    if g.get("materially_different_source_families") is not True:
        raise ValueError("second-family evidence missing")
    if g.get("divergent_destination_dispositions") is not True:
        raise ValueError("divergent outcomes missing")
    if g.get("live_membrane_required_for_reconstruction") is not False:
        raise ValueError("live membrane cannot become reconstruction dependency")
    if g.get("extraction_gate") != "eligible-for-reconsideration-not-promoted":
        raise ValueError("extraction gate silently promoted")
    n=v.get("nonclaims",{})
    if any(n.get(k) is not False for k in (
        "standalone_supabardo_repo","universal_protocol","central_event_bus",
        "persistent_bardo_storage","automatic_destination_authority"
    )):
        raise ValueError("nonclaim silently promoted")
    return v

def main(argv=None):
    args=sys.argv[1:] if argv is None else argv
    if len(args)!=1:
        print("usage: validate-bardo-generality.py PATH",file=sys.stderr); return 2
    try:
        validate(json.loads(Path(args[0]).read_text(encoding="utf-8")))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}",file=sys.stderr); return 2
    print("VALID BARDO-GENERALITY-002")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
