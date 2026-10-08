import copy
from dataclasses import replace
from fractions import Fraction
import json
import os
from pathlib import Path
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest

from instruments.adapters import GhotSystemAdapter, RecordedRadioAdapter
from instruments.authority import NativeRelatte
from instruments.contract import MAX_ADDRESS_DEPTH, Refuse, address_from_positions, dial_from_profile
from instruments.host import InstrumentHost
from instruments.store import Store
from vendor.eleven_heap_001.infinite_radio import Address, Dial

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "fixtures/instrument-host-001/two-stations.wav"


class HostTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.recording = self.base / "recorded.wav"
        shutil.copyfile(FIXTURE, self.recording)
        self.host = InstrumentHost(self.base / "session")
        self.adapter = RecordedRadioAdapter(self.recording)
        self.id = self.adapter.instrument_id
        self.host.install(self.adapter)

    def tearDown(self):
        self.host.close()
        self.temp.cleanup()

    def selected(self):
        self.host.observe(self.id)
        return self.host.select(self.id)

    def attention(self):
        self.selected()
        self.host.set_mode(self.id, "attention")
        return self.host.select(self.id)

    def test_positions_one_through_eleven_use_original_addresses(self):
        self.assertEqual(address_from_positions([1, 11, 6]), Address((0, 10, 5)))
        self.host.set_positions(self.id, [8, 4, 11, 3, 9, 5])
        discovery = self.host.discover()["instruments"][0]
        self.assertEqual(discovery["dial"]["address"]["digits"], [7, 3, 10, 2, 8, 4])
        self.assertEqual(len(discovery["psi_regions"]), 6)
        self.assertEqual(discovery["psi_regions"][-1]["positions"], [8, 4, 11, 3, 9, 5])

    def test_malformed_and_excessive_addresses(self):
        for positions in ([], [0], [12], [True], [1.0], [6] * 17):
            with self.subTest(positions=positions), self.assertRaises(Refuse):
                self.host.set_positions(self.id, positions)
        self.host.set_positions(self.id, [6] * MAX_ADDRESS_DEPTH)
        with self.assertRaises(Refuse):
            self.host.zoom(self.id)
        profile = Dial().to_dict()
        profile["address"]["digits"] = [11]
        with self.assertRaises(Refuse):
            self.host.configure(self.id, profile)

    def test_profile_cannot_import_capabilities_or_admission(self):
        for key in ("capabilities", "admitted", "transmit_permission"):
            profile = Dial().to_dict()
            profile[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(Refuse, "profiles cannot carry authority"):
                self.host.configure(self.id, profile)

    def test_recursive_sensitivity_and_all_response_curves(self):
        dial = Dial(Address((5, 5)), context_load=Fraction(3, 2),
                    sensitivity=Dial(Address((5,)), sensitivity=Dial(Address((3,)))))
        self.host.configure(self.id, dial.to_dict())
        before = self.host.state["instruments"][self.id]["dial"]["address"]
        self.host.turn_sensitivity(self.id, 2, 2)
        for expected in ("logarithmic", "thresholded", "context-sensitive"):
            self.host.turn_response(self.id, 3)
            self.assertEqual(self.host.state["instruments"][self.id]["dial"]["curve"], expected)
        self.assertEqual(self.host.state["instruments"][self.id]["dial"]["address"], before)

    def test_excessive_sensitivity_nesting_is_bounded(self):
        nested = Dial()
        for _ in range(9):
            nested = replace(nested, sensitivity=Dial()) if nested.sensitivity is None else Dial(sensitivity=nested)
        with self.assertRaises(Refuse):
            self.host.configure(self.id, nested.to_dict())

    def test_frequency_changes_selected_input_without_authority_expansion(self):
        original = self.host.discover()["instruments"][0]["descriptor"]["capabilities"]
        self.host.observe(self.id)
        self.host.set_positions(self.id, [1])
        first = self.host.select(self.id)
        self.host.turn(self.id, 10)
        second = self.host.select(self.id)
        self.assertNotEqual(first["station"], second["station"])
        self.assertNotEqual(first["samples"], second["samples"])
        self.assertEqual(self.host.discover()["instruments"][0]["descriptor"]["capabilities"], original)
        self.assertFalse(first["physical_reception"])

    def test_attention_preserves_selected_station_and_changes_samples(self):
        frequency = self.selected()
        controls = copy.deepcopy(self.host.state["instruments"][self.id]["dial"])
        self.host.set_mode(self.id, "attention")
        self.assertEqual(self.host.state["instruments"][self.id]["dial"], controls)
        first = self.host.select(self.id)
        self.host.turn(self.id, -4)
        second = self.host.select(self.id)
        self.assertEqual(first["station"], frequency["station"])
        self.assertEqual(second["station"], frequency["station"])
        self.assertNotEqual(first["sample_region"], second["sample_region"])
        self.assertNotEqual(first["samples"], second["samples"])

    def test_proposal_is_visible_simulation_and_cannot_execute(self):
        self.attention()
        before = copy.deepcopy(self.host.state)
        proposal = self.host.simulated_autodisco(self.id)
        self.assertFalse(proposal["native_autodisco"])
        self.assertEqual(proposal["authority_effect"], "none")
        self.assertEqual(self.host.state, before)
        with self.assertRaises(Refuse):
            self.host.execute(proposal)

    def test_mutated_and_stale_proposals_are_rejected(self):
        self.attention()
        proposal = self.host.simulated_autodisco(self.id)
        changed = dict(proposal, native_autodisco=True)
        with self.assertRaisesRegex(Refuse, "laundered"):
            self.host.accept_region(changed)
        self.host.turn(self.id, 1)
        with self.assertRaisesRegex(Refuse, "stale"):
            self.host.accept_region(proposal)

    def test_explicit_region_selection_is_not_operation_admission(self):
        self.attention()
        self.host.accept_region(self.host.simulated_autodisco(self.id))
        self.host.select(self.id)
        request = self.host.propose_operation(self.id)
        with self.assertRaisesRegex(Refuse, "admission unavailable"):
            self.host.execute(request)

    def test_imported_or_mutated_operation_is_not_authority(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        for altered in (dict(request, admitted=True), dict(request, operation="transmit"),
                        dict(request, required_capabilities=["transmit"])):
            with self.subTest(altered=altered), self.assertRaisesRegex(Refuse, "laundered"):
                self.host.execute(altered)

    def test_withdrawal_retains_controls_and_invalidates_operations(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        before = copy.deepcopy(self.host.state["instruments"][self.id]["dial"])
        self.host.withdraw(self.id)
        self.assertEqual(self.host.state["instruments"][self.id]["dial"], before)
        with self.assertRaisesRegex(Refuse, "withdrawn"):
            self.host.execute(request)
        self.host.install(self.adapter)
        with self.assertRaisesRegex(Refuse, "stale"):
            self.host.execute(request)

    def test_retirement_requires_fresh_instrument_identity(self):
        self.host.withdraw(self.id, retire=True)
        with self.assertRaisesRegex(Refuse, "new identity"):
            self.host.install(self.adapter)
        self.host.install(RecordedRadioAdapter(self.recording, instrument_id="successor-radio"))
        self.assertEqual(len(self.host.discover()["instruments"]), 2)

    def test_adapter_substitution_requires_fresh_incarnation(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        before = self.host.state["instruments"][self.id]["incarnation"]
        self.host.install(RecordedRadioAdapter(self.recording))
        self.assertNotEqual(before, self.host.state["instruments"][self.id]["incarnation"])
        with self.assertRaisesRegex(Refuse, "stale"):
            self.host.execute(request)

    def test_disappearance_withdraws_source_and_cannot_resurrect_operation(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        self.recording.unlink()
        with self.assertRaisesRegex(Refuse, "disappeared"):
            self.host.execute(request)
        shutil.copyfile(FIXTURE, self.recording)
        with self.assertRaisesRegex(Refuse, "withdrawn"):
            self.host.execute(request)
        self.assertTrue(any(e["kind"] == "ADAPTER_WITHDRAWN" for e in self.host.store.events()))

    def test_stale_source_history(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        data = bytearray(self.recording.read_bytes())
        data[-1] ^= 1
        self.recording.write_bytes(data)
        with self.assertRaisesRegex(Refuse, "source history"):
            self.host.execute(request)

    def test_changed_calibration(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        self.adapter.calibration = "changed-calibration"
        with self.assertRaisesRegex(Refuse, "calibration"):
            self.host.execute(request)

    def test_unauthorized_control_expansion_and_units(self):
        class Expanded(RecordedRadioAdapter):
            def describe(inner):
                return replace(super().describe(), capabilities=("observe", "select", "attend", "record", "transmit"))
        with self.assertRaisesRegex(Refuse, "capability expansion"):
            self.host.install(Expanded(self.recording))
        for mode in ("transmit", "admin", "unbounded"):
            with self.assertRaises(Refuse):
                self.host.set_mode(self.id, mode)

    def test_transmission_is_denied_and_receipted_even_at_position_eleven(self):
        self.host.set_positions(self.id, [11] * 16)
        self.selected()
        with self.assertRaisesRegex(Refuse, "transmission DISABLED"):
            self.host.propose_operation(self.id, "transmit")
        last = self.host.store.events()[-1]
        self.assertEqual(last["kind"], "OPERATION_DENIED")
        self.assertFalse(last["detail"]["receipt"]["rf_emitted"])

    def test_changed_control_range_or_unit_withdraws_existing_binding(self):
        class Changed(RecordedRadioAdapter):
            change = None
            def describe(inner):
                descriptor = super().describe()
                if inner.change:
                    control = dict(descriptor.controls[0])
                    control[inner.change] = [1, 999999999] if inner.change == "range" else "arbitrary-unit"
                    return replace(descriptor, controls=(control, descriptor.controls[1]))
                return descriptor
        for field in ("range", "unit"):
            with self.subTest(field=field):
                changed = Changed(self.recording)
                self.host.install(changed)
                self.selected()
                request = self.host.propose_operation(self.id)
                changed.change = field
                with self.assertRaisesRegex(Refuse, "adapter changed"):
                    self.host.execute(request)
                self.assertEqual(self.host.state["instruments"][self.id]["lifecycle"], "withdrawn")

    def test_read_only_second_instrument_uses_same_contract(self):
        second = RecordedRadioAdapter(self.recording, instrument_id="second-instrument")
        self.host.install(second)
        self.host.observe(second.instrument_id)
        self.host.set_positions(second.instrument_id, [2, 3])
        self.assertEqual(self.host.select(second.instrument_id)["type"], "FrequencySelection")
        self.assertEqual(len(self.host.discover()["instruments"]), 2)

    def test_cold_reconstruction_keeps_exact_controls_and_denies_old_requests(self):
        self.host.set_positions(self.id, [8, 4, 11, 3, 9, 5])
        self.selected()
        request = self.host.propose_operation(self.id)
        controls = copy.deepcopy(self.host.state["instruments"][self.id]["dial"])
        self.host.close()
        self.host = InstrumentHost(self.base / "session")
        self.assertEqual(self.host.state["instruments"][self.id]["dial"], controls)
        with self.assertRaisesRegex(Refuse, "dead process"):
            self.host.execute(request)
        self.assertFalse(self.host.adapters)

    def test_process_supersession_rejects_old_live_host(self):
        other = InstrumentHost(self.base / "session")
        try:
            with self.assertRaisesRegex(Refuse, "superseded"):
                self.host.turn(self.id, 1)
        finally:
            other.close()

    def test_denial_by_old_writer_cannot_resurrect_superseded_process(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        other = InstrumentHost(self.base / "session")
        try:
            current_process = other.process
            for _ in range(2):
                with self.assertRaisesRegex(Refuse, "superseded"):
                    self.host.execute(request)
                self.assertEqual(self.host.store.load()["process_incarnation"], current_process)
            with self.assertRaisesRegex(Refuse, "superseded"):
                self.host.install(self.adapter)
            self.assertEqual(self.host.store.load()["process_incarnation"], current_process)
        finally:
            other.close()

    def test_changed_control_revision_requires_new_operation(self):
        self.selected()
        request = self.host.propose_operation(self.id)
        self.host.turn_response(self.id, 3)
        with self.assertRaisesRegex(Refuse, "stale"):
            self.host.execute(request)

    def test_recording_and_profile_byte_budgets(self):
        self.recording.write_bytes(b"x" * 65537)
        with self.assertRaisesRegex(Refuse, "byte budget"):
            self.adapter.observe()
        profile = Dial().to_dict()
        profile["context_load"] = "9" * 5000
        with self.assertRaises(Refuse):
            dial_from_profile(profile)


class ColdEvidenceTests(unittest.TestCase):
    def test_actual_sigkill_then_fresh_process_verifies_durable_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            session = Path(temp) / "session"
            code = """import os,signal,sys
from pathlib import Path
from instruments.adapters import RecordedRadioAdapter
from instruments.host import InstrumentHost
h=InstrumentHost(Path(sys.argv[1]))
a=RecordedRadioAdapter(Path(sys.argv[2]))
h.install(a)
h.set_positions(a.instrument_id,[8,4,11,3,9,5])
h.observe(a.instrument_id)
h.select(a.instrument_id)
h.propose_operation(a.instrument_id)
os.kill(os.getpid(),signal.SIGKILL)
"""
            child = subprocess.run([sys.executable, "-c", code, str(session), str(FIXTURE)], cwd=ROOT,
                                   capture_output=True, timeout=20)
            self.assertEqual(child.returncode, -signal.SIGKILL, child.stderr.decode())
            cold = subprocess.run([sys.executable, "-m", "instruments.cli", "verify", "--session", str(session)],
                                  cwd=ROOT, capture_output=True, timeout=20, check=True)
            evidence = json.loads(cold.stdout)
            self.assertTrue(evidence["history_verified"])
            self.assertEqual(evidence["cold_requests_denied"], 1)
            self.assertEqual(evidence["discovery"]["instruments"][0]["dial"]["address"]["digits"], [7,3,10,2,8,4])
            self.assertFalse(evidence["discovery"]["instruments"][0]["current_adapter_installed"])

    def test_durable_event_state_or_request_mutation_is_rejected(self):
        for target in ("events", "state", "requests", "consumed"):
            table = "requests" if target == "consumed" else target
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp:
                host = InstrumentHost(Path(temp))
                adapter = RecordedRadioAdapter(FIXTURE)
                host.install(adapter)
                host.observe(adapter.instrument_id)
                host.select(adapter.instrument_id)
                host.propose_operation(adapter.instrument_id)
                host.close()
                db = sqlite3.connect(Path(temp) / "instrument.sqlite3")
                row = db.execute(f"SELECT rowid,body FROM {table} ORDER BY rowid DESC LIMIT 1").fetchone()
                body = json.loads(row[1])
                body["tampered"] = True
                if target == "consumed":
                    db.execute("UPDATE requests SET consumed=1 WHERE rowid=?", (row[0],))
                else:
                    db.execute(f"UPDATE {table} SET body=? WHERE rowid=?", (json.dumps(body), row[0]))
                db.commit()
                db.close()
                with self.assertRaises(Refuse):
                    Store(Path(temp))


@unittest.skipUnless(os.environ.get("STATIC_INSTRUMENT_GHOT"), "native GHoT donor path not configured")
class NativeGhotTests(unittest.TestCase):
    def test_real_read_only_host_probe_and_second_instrument(self):
        donor = Path(os.environ["STATIC_INSTRUMENT_GHOT"])
        before = list(donor.rglob("body-p256.pem"))
        with tempfile.TemporaryDirectory() as temp:
            host = InstrumentHost(Path(temp))
            try:
                host.install(RecordedRadioAdapter(FIXTURE))
                adapter = GhotSystemAdapter(donor)
                host.install(adapter)
                observed = host.observe(adapter.instrument_id)
                host.set_positions(adapter.instrument_id, [1])
                first = host.select(adapter.instrument_id)
                host.turn(adapter.instrument_id, 2)
                second = host.select(adapter.instrument_id)
                self.assertEqual(first["field"], "os")
                self.assertEqual(first["value"], os.uname().sysname)
                self.assertEqual(second["field"], "cpu_count")
                self.assertEqual(second["value"], os.cpu_count())
                self.assertEqual(len(host.discover()["instruments"]), 2)
                self.assertEqual(observed["source"]["kind"], "local-os")
                self.assertEqual(list(donor.rglob("body-p256.pem")), before)
            finally:
                host.close()


@unittest.skipUnless(os.environ.get("STATIC_INSTRUMENT_RELATTE"), "native reLATTE donor path not configured")
class NativeRelatteTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.authority = NativeRelatte(Path(os.environ["STATIC_INSTRUMENT_RELATTE"]), self.root / "relatte")
        self.authority.initialize()
        self.host = InstrumentHost(self.root, self.authority)
        self.adapter = RecordedRadioAdapter(FIXTURE)
        self.host.install(self.adapter)
        self.host.observe(self.adapter.instrument_id)
        self.host.select(self.adapter.instrument_id)
        self.request = self.host.propose_operation(self.adapter.instrument_id)

    def tearDown(self):
        self.host.close()
        self.temp.cleanup()

    def test_genuine_crossing_hold_owner_local_admission_record_and_no_replay(self):
        proposed = self.authority.snapshot()
        self.assertEqual(len(proposed["held"]), 1)
        self.assertEqual(proposed["admitted"], [])
        with self.assertRaisesRegex(Refuse, "ADMISSION_REQUIRED"):
            self.host.execute(self.request)
        owner = self.host.owner_admit(self.request)
        self.assertTrue(owner["signature_verified"])
        self.assertEqual(owner["receipt"]["kind"], "R3_ADMIT")
        self.assertEqual(len(self.authority.snapshot()["held"]), 1)
        receipt = self.host.execute(self.request)
        self.assertEqual(receipt["status"], "RECORDED")
        self.assertFalse(receipt["rf_emitted"])
        with self.assertRaisesRegex(Refuse, "consumed"):
            self.host.execute(self.request)

    def test_expired_admission(self):
        self.host.owner_admit(self.request, ttl_seconds=1)
        time.sleep(1.1)
        with self.assertRaisesRegex(Refuse, "EXPIRED"):
            self.host.execute(self.request)

    def test_withdrawal_dominates_valid_signed_admission(self):
        self.host.owner_admit(self.request)
        self.host.withdraw(self.adapter.instrument_id)
        with self.assertRaisesRegex(Refuse, "withdrawn"):
            self.host.execute(self.request)

    def test_proposal_receipt_laundering_is_rejected_by_native_verifier(self):
        path = self.authority.root / "packets" / (self.request["id"] + ".json")
        packet = json.loads(path.read_text())
        packet["admission"] = {"crossing": packet["proposal_crossing"], "receipt": packet["hold_receipt"]}
        path.write_text(json.dumps(packet))
        with self.assertRaisesRegex(Refuse, "ADMISSION_REQUIRED"):
            self.host.execute(self.request)

    def test_native_receiver_cold_reopen_does_not_restore_executable_host_requests(self):
        self.host.owner_admit(self.request)
        self.host.close()
        code = """import json,sys
from pathlib import Path
from instruments.authority import NativeRelatte
from instruments.host import InstrumentHost
from instruments.contract import Refuse
r=Path(sys.argv[1]); a=NativeRelatte(Path(sys.argv[2]),r/'relatte'); h=InstrumentHost(r,a)
request=json.loads(sys.argv[3])
try: h.execute(request)
except Refuse as e: print(json.dumps({'denied':str(e),'native':a.snapshot()}))
else: raise SystemExit('unexpected execution')
h.close()
"""
        proc = subprocess.run([sys.executable, "-c", code, str(self.root), str(self.authority.donor), json.dumps(self.request)],
                              cwd=ROOT, capture_output=True, timeout=20, check=True)
        result = json.loads(proc.stdout)
        self.assertIn("dead process", result["denied"])
        self.assertEqual(len(result["native"]["admitted"]), 1)
        self.host = InstrumentHost(self.root, self.authority)


if __name__ == "__main__":
    unittest.main()
