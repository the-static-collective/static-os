#!/usr/bin/env python3
"""Kill a recording process without closing SQLite, then verify in another process."""
import argparse
import json
from pathlib import Path
import signal
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--session", required=True, type=Path)
args = parser.parse_args()
if args.session.exists():
    raise SystemExit("use a fresh session directory")
child_code = """import os,signal,sys
from pathlib import Path
from instruments.adapters import RecordedRadioAdapter
from instruments.host import InstrumentHost
from vendor.eleven_heap_001.infinite_radio import Address,Dial
h=InstrumentHost(Path(sys.argv[1])); a=RecordedRadioAdapter(Path(sys.argv[2])); h.install(a)
h.configure(a.instrument_id,Dial(Address((7,3,10,2,8,4)),sensitivity=Dial(Address((3,7)),sensitivity=Dial(Address((8,1))))).to_dict())
h.observe(a.instrument_id); h.select(a.instrument_id); h.propose_operation(a.instrument_id)
os.kill(os.getpid(),signal.SIGKILL)
"""
child = subprocess.run([sys.executable, "-c", child_code, str(args.session.resolve()),
                        str(ROOT / "fixtures/instrument-host-001/two-stations.wav")],
                       cwd=ROOT, capture_output=True, timeout=20)
if child.returncode != -signal.SIGKILL:
    raise SystemExit("SIGKILL witness failed: " + child.stderr.decode())
cold = subprocess.run([sys.executable, "-m", "instruments.cli", "verify", "--session", str(args.session.resolve())],
                      cwd=ROOT, capture_output=True, check=True, timeout=20)
result = json.loads(cold.stdout)
if (not result["history_verified"] or result["cold_requests_denied"] != 1
        or result["discovery"]["instruments"][0]["dial"]["address"]["digits"] != [7,3,10,2,8,4]):
    raise SystemExit("cold reconstruction witness failed")
proof = {"schema": "static-os.instrument-process-death-proof/v0", "actual_sigkill": True,
         "child_returncode": child.returncode, "sqlite_closed_by_child": False,
         "fresh_verifier_process": True, "cold": result,
         "physical_os_boot": "NOT_RUN", "rf_emitted": False}
(args.session / "process-death-proof.json").write_text(json.dumps(proof, indent=2) + "\n")
print(json.dumps(proof, indent=2))
