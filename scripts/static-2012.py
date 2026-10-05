#!/usr/bin/env python3
import argparse, importlib.util, json, os, platform, shutil, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
vp=ROOT/"scripts"/"validate-static-2012.py"
spec=importlib.util.spec_from_file_location("static_2012_validation",vp)
validator=importlib.util.module_from_spec(spec); spec.loader.exec_module(validator)

def collect_host_facts(path_for_disk=None):
    mem=None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("MemTotal:"):
                mem=int(line.split()[1])//1024; break
    except (OSError,ValueError,IndexError): pass
    d=shutil.disk_usage(path_for_disk or str(Path.home()))
    arch=platform.machine().lower()
    if arch=="x86_64": arch="amd64"
    return {"architecture":arch,"cpu_cores":os.cpu_count() or 1,"memory_mib":mem,"free_disk_gib":d.free//(1024**3)}

def assess(profile,facts):
    validator.validate(profile); t=profile["target"]
    checks={
      "architecture":facts.get("architecture")==t["architecture"],
      "cpu_cores":isinstance(facts.get("cpu_cores"),int) and facts["cpu_cores"]>=t["minimum_cpu_cores"],
      "memory":isinstance(facts.get("memory_mib"),int) and facts["memory_mib"]>=t["minimum_memory_mib"],
      "disk":isinstance(facts.get("free_disk_gib"),int) and facts["free_disk_gib"]>=t["minimum_free_disk_gib"]
    }
    ready=all(checks.values())
    comfortable=ready and facts["memory_mib"]>=t["comfortable_memory_mib"] and facts["free_disk_gib"]>=t["comfortable_free_disk_gib"]
    state="comfortable" if comfortable else ("reference-ready" if ready else "below-floor")
    return {
      "schema":"static-os.static-2012-assessment/v0","profile_id":profile["id"],"facts":facts,"checks":checks,
      "state":state,"core_local_possible":ready,"gpu_required_for_core":False,"network_required_after_sync":False,
      "capability_board":[{"id":c["id"],"class":c["class"],"local":c["local"]} for c in profile["capabilities"]],
      "claims":{"physical_install_verified":False,"performance_benchmarked":False,"assessment_is_contract_only":True}
    }

def clone_plan(profile,root):
    validator.validate(profile); root=str(root); out=[f'mkdir -p "{root}"']
    for item in profile["loadout"]:
        repo=item["repository"]; name=repo.split("/",1)[1]
        prefix="git clone" if item["sync"]=="full" else "git clone --depth=1"
        out.append(f'{prefix} https://github.com/{repo}.git "{root}/{name}"')
    return out

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("profile",nargs="?",default=str(ROOT/"profiles"/"static-2012.json"))
    p.add_argument("--facts")
    p.add_argument("--clone-plan",metavar="ROOT")
    a=p.parse_args(argv)
    try:
        profile=json.loads(Path(a.profile).read_text(encoding="utf-8")); validator.validate(profile)
        if a.clone_plan:
            print("\n".join(clone_plan(profile,a.clone_plan))); return 0
        facts=json.loads(Path(a.facts).read_text(encoding="utf-8")) if a.facts else collect_host_facts()
        print(json.dumps(assess(profile,facts),indent=2,sort_keys=True)); return 0
    except (OSError,ValueError,TypeError,json.JSONDecodeError) as exc:
        print(f"REFUSE: {exc}",file=sys.stderr); return 2
if __name__=="__main__": raise SystemExit(main())
