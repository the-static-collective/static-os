#!/usr/bin/env python3
import json, re, sys
from pathlib import Path

SCHEMA="static-os.reference-machine/v0"
STATUS="candidate-unverified"
CLASSES={"GREEN","YELLOW","BLUE","RED"}
SYNC={"full","shallow"}
CORE_REPOS={
 "the-static-collective/static-os","the-static-collective/static-workbench",
 "the-static-collective/reLATTE","the-static-collective/GrO",
 "the-static-collective/tranchnode","the-static-collective/Dogram",
 "the-static-collective/GHoT"
}

def pos(v,name):
    if not isinstance(v,int) or isinstance(v,bool) or v<=0: raise ValueError(f"{name} must be a positive integer")
    return v

def validate(data):
    if not isinstance(data,dict): raise ValueError("profile must be an object")
    if data.get("schema")!=SCHEMA or data.get("status")!=STATUS: raise ValueError("invalid STATIC 2012 schema or status")
    if data.get("id")!="STATIC-2012-001" or data.get("label")!="STATIC 2012": raise ValueError("unexpected reference-machine identity")
    t=data.get("target")
    if not isinstance(t,dict): raise ValueError("target is required")
    if t.get("architecture")!="amd64": raise ValueError("STATIC 2012 currently declares amd64 only")
    cores=pos(t.get("minimum_cpu_cores"),"minimum_cpu_cores")
    mm=pos(t.get("minimum_memory_mib"),"minimum_memory_mib")
    cm=pos(t.get("comfortable_memory_mib"),"comfortable_memory_mib")
    md=pos(t.get("minimum_free_disk_gib"),"minimum_free_disk_gib")
    cd=pos(t.get("comfortable_free_disk_gib"),"comfortable_free_disk_gib")
    if cores<2: raise ValueError("reference floor must preserve at least two CPU cores")
    if cm<mm or cd<md: raise ValueError("comfortable envelope cannot be below minimum")
    if t.get("gpu_required_for_core") is not False: raise ValueError("core sovereignty must not require a GPU")
    if t.get("network_required_for_initial_sync") is not True: raise ValueError("initial sync is network-bound")
    if t.get("network_required_after_sync") is not False: raise ValueError("post-sync continuity must remain network-optional")
    if "MORE MACHINE REQUIRES A NAMED BOTTLENECK" not in data.get("laws",[]): raise ValueError("named-bottleneck law is required")

    load=data.get("loadout")
    if not isinstance(load,list) or not load: raise ValueError("bounded living loadout is required")
    seen=set(); required=set()
    for item in load:
        if not isinstance(item,dict): raise ValueError("loadout entries must be objects")
        repo=item.get("repository")
        if not isinstance(repo,str) or not re.fullmatch(r"the-static-collective/[A-Za-z0-9._-]+",repo): raise ValueError("invalid repository slug")
        if repo in seen: raise ValueError(f"duplicate loadout repository: {repo}")
        seen.add(repo)
        if not isinstance(item.get("role"),str) or not item["role"].strip(): raise ValueError(f"role required for {repo}")
        if item.get("sync") not in SYNC: raise ValueError(f"unsupported sync mode for {repo}")
        if not isinstance(item.get("required"),bool): raise ValueError(f"required flag must be boolean for {repo}")
        if item["required"]:
            required.add(repo)
            if item["sync"]!="full": raise ValueError(f"core repository must use full sync: {repo}")
    if not CORE_REPOS <= required: raise ValueError("core sovereignty repositories must all be required")

    caps=data.get("capabilities")
    if not isinstance(caps,list) or not caps: raise ValueError("capability board is required")
    by={}
    for cap in caps:
        if not isinstance(cap,dict): raise ValueError("capabilities must be objects")
        cid=cap.get("id"); cls=cap.get("class")
        if not isinstance(cid,str) or not cid.strip() or cid in by: raise ValueError("capability ids must be unique")
        if cls not in CLASSES: raise ValueError(f"invalid class for {cid}")
        if not isinstance(cap.get("local"),bool): raise ValueError(f"local flag required for {cid}")
        if not isinstance(cap.get("description"),str) or not cap["description"].strip(): raise ValueError(f"description required for {cid}")
        if cls=="GREEN":
            if cap["local"] is not True: raise ValueError(f"GREEN capability must be local: {cid}")
            if "bottleneck" in cap or "fallback" in cap: raise ValueError(f"GREEN capability must not invent a more-machine claim: {cid}")
        else:
            b=cap.get("bottleneck"); f=cap.get("fallback")
            if not isinstance(b,dict): raise ValueError(f"named bottleneck required for {cid}")
            if not isinstance(b.get("resource"),str) or not b["resource"].strip(): raise ValueError(f"bottleneck resource required for {cid}")
            if not isinstance(b.get("evidence"),str) or not b["evidence"].strip(): raise ValueError(f"bottleneck evidence required for {cid}")
            if not isinstance(f,str) or not f.strip(): raise ValueError(f"lawful fallback required for {cid}")
        by[cid]=cap
    core=data.get("core_sovereignty_capabilities")
    if not isinstance(core,list) or not core or len(core)!=len(set(core)): raise ValueError("core sovereignty ids must be unique")
    for cid in core:
        cap=by.get(cid)
        if not cap or cap["class"]!="GREEN" or cap["local"] is not True: raise ValueError(f"core sovereignty must remain GREEN/local: {cid}")
    return {"profile_id":data["id"],"required_repositories":sorted(required),"capability_count":len(caps),"core_capability_count":len(core)}

def main():
    if len(sys.argv)!=2:
        print("usage: validate-static-2012.py PATH",file=sys.stderr); return 2
    try: result=validate(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")))
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}",file=sys.stderr); return 2
    print(f"VALID STATIC 2012 candidate; {result['core_capability_count']} core local capabilities; {len(result['required_repositories'])} required repositories")
    return 0
if __name__=="__main__": raise SystemExit(main())
