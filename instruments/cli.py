"""STATIC-OS instrument entry point: discover, demonstrate, or cold-verify sessions."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .adapters import GhotSystemAdapter, RecordedRadioAdapter
from .authority import NativeRelatte, UnavailableRelatte
from .contract import Refuse
from .host import InstrumentHost

ROOT = Path(__file__).resolve().parents[1]


def demo(session: Path, ghot: Path | None = None, relatte: Path | None = None,
         *, owner_record: bool = False) -> dict:
    authority = NativeRelatte(relatte, session / "relatte") if relatte else UnavailableRelatte()
    if relatte and not (session / "relatte" / "receiver").exists():
        authority.initialize()
    host = InstrumentHost(session, authority)
    try:
        radio = RecordedRadioAdapter(ROOT / "fixtures/instrument-host-001/two-stations.wav")
        host.install(radio)
        observed = host.observe(radio.instrument_id)
        host.set_positions(radio.instrument_id, [1])
        low = host.select(radio.instrument_id)
        host.turn(radio.instrument_id, 10)
        high = host.select(radio.instrument_id)
        host.set_mode(radio.instrument_id, "attention")
        host.zoom(radio.instrument_id)
        first = host.select(radio.instrument_id)
        host.turn(radio.instrument_id, -1)
        second = host.select(radio.instrument_id)
        proposal = host.simulated_autodisco(radio.instrument_id)
        host.accept_region(proposal)
        selected = host.select(radio.instrument_id)
        request = host.propose_operation(radio.instrument_id)
        receipt = None
        if owner_record:
            host.owner_admit(request)
            receipt = host.execute(request)
        local = None
        if ghot:
            adapter = GhotSystemAdapter(ghot)
            host.install(adapter)
            host.observe(adapter.instrument_id)
            host.set_positions(adapter.instrument_id, [1])
            os_name = host.select(adapter.instrument_id)
            host.turn(adapter.instrument_id, 2)
            cpu_count = host.select(adapter.instrument_id)
            local = {"native_ghot": True, "first": os_name, "second": cpu_count}
        controls_before_withdraw = host.state["instruments"][radio.instrument_id]["dial"]
        pending = host.propose_operation(radio.instrument_id)
        host.withdraw(radio.instrument_id)
        try:
            host.execute(pending)
        except Refuse:
            withdrawal_denied = True
        else:
            withdrawal_denied = False
        state = host.state["instruments"][radio.instrument_id]
        proof = {"schema": "static-os.instrument-host-proof/v0", "experiment": "STATIC-OS INSTRUMENT HOST 001",
                 "source_observe_select_attend_record": receipt is not None,
                 "frequency_changes_selected_recorded_track": low["station"] != high["station"],
                 "attention_changes_sample_region": first["sample_region"] != second["sample_region"],
                 "observation_ref": observed["observation_sha256"], "selected": selected,
                 "controls_survive_withdrawal": state["dial"] == controls_before_withdraw,
                 "withdrawal_denied": withdrawal_denied, "native_ghot": local,
                 "native_relatte": relatte is not None, "autodisco_boundary": proposal["producer"],
                 "native_autodisco": False, "physical_reception": False, "rf_emitted": False,
                 "transmission": "DISABLED", "session_id": host.state["session_id"],
                 "execution_receipt": receipt, "discovery": host.discover()}
        (session / "export.json").write_text(json.dumps(host.export(), indent=2) + "\n")
        (session / "proof.json").write_text(json.dumps(proof, indent=2) + "\n")
        return proof
    finally:
        host.close()


def cold_verify(session: Path, relatte: Path | None = None) -> dict:
    authority = NativeRelatte(relatte, session / "relatte") if relatte else UnavailableRelatte()
    host = InstrumentHost(session, authority)
    try:
        host.store.verify()
        events = host.store.events()
        requests = [e["detail"]["request"] for e in events if e["kind"] == "OPERATION_PROPOSED"]
        denied = 0
        for request in requests:
            try:
                host.execute(request)
            except Refuse:
                denied += 1
        native = authority.snapshot() if relatte else None
        result = {"schema": "static-os.instrument-cold-verification/v0", "session_id": host.state["session_id"],
                  "history_verified": True, "cold_requests_denied": denied, "historical_requests": len(requests),
                  "no_current_adapters": not host.adapters, "discovery": host.discover(),
                  "native_relatte_journal_verified": native is not None, "native_receiver": native,
                  "transmission": "DISABLED", "rf_emitted": False}
        (session / "cold-proof.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    finally:
        host.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "verify"))
    parser.add_argument("--session", required=True, type=Path)
    parser.add_argument("--ghot", type=Path)
    parser.add_argument("--relatte", type=Path)
    parser.add_argument("--owner-record", action="store_true",
                        help="explicit owner-local admission of one read-only record; never enables transmission")
    args = parser.parse_args()
    try:
        result = (demo(args.session, args.ghot, args.relatte, owner_record=args.owner_record)
                  if args.command == "demo" else cold_verify(args.session, args.relatte))
        print(json.dumps(result, indent=2))
        return 0
    except Refuse as error:
        print(json.dumps({"status": "REFUSED", "reason": str(error), "rf_emitted": False}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
