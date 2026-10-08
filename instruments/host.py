"""Bounded generic instrument host, durable state, and native owner-local admission."""
from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
import json
from pathlib import Path
import time
import uuid

from vendor.eleven_heap_001.infinite_radio import Address, Console, Dial, Signal, ControlMap, digest
from .authority import UnavailableRelatte
from .contract import (
    CURVES, MAX_ADDRESS_DEPTH, InstrumentAdapterV0, Refuse, address_from_positions,
    bounded, dial_from_profile, psi_regions, require,
)
from .store import Store


class InstrumentHost:
    def __init__(self, root: Path, authority=None):
        self.store = Store(root)
        self.authority = authority or UnavailableRelatte()
        self.adapters: dict[str, InstrumentAdapterV0] = {}
        self.process = str(uuid.uuid4())
        with self.store.transaction():
            previous = self.store.load()
            self.state = previous or {"schema": "static-os.instrument-session/v0", "session_id": str(uuid.uuid4()),
                                      "process_incarnation": None, "instruments": {}, "transmission": "DISABLED"}
            for item in self.state["instruments"].values():
                dial_from_profile(item["dial"])
                dial_from_profile(item["response_dial"])
            self.state["process_incarnation"] = self.process
            self._event("COLD_RECONSTRUCT" if previous else "SESSION_CREATED",
                        {"historical_controls_restored": bool(previous), "executable_operations_restored": False,
                         "authority_boundary": self.authority.boundary})

    def _event(self, kind: str, detail: dict) -> dict:
        try:
            current = self.store.load()
            if current is not None and kind not in ("COLD_RECONSTRUCT", "SESSION_CREATED"):
                require(current["process_incarnation"] == self.process, "session process superseded")
            return self.store.append(kind, detail, self.state)
        except BaseException:
            durable = self.store.load()
            if durable is not None:
                self.state = durable
            raise

    def _item(self, id_: str) -> dict:
        require(self.store.load()["process_incarnation"] == self.process, "session process superseded")
        require(id_ in self.state["instruments"], "unknown instrument")
        return self.state["instruments"][id_]

    def _current(self, id_: str) -> dict:
        item = self._item(id_)
        require(item["lifecycle"] == "active", "instrument withdrawn or retired")
        require(id_ in self.adapters, "historical instrument requires fresh local adapter installation")
        try:
            current = self.adapters[id_].describe()
            current.validate()
            require(digest(current.to_dict()) == item["descriptor_sha256"], "source history, calibration, or adapter changed")
        except (Refuse, OSError) as error:
            item["lifecycle"] = "withdrawn"
            item["revision"] += 1
            self.adapters.pop(id_, None)
            detail = {"instrument_id": id_, "reason": str(error), "incarnation": item["incarnation"]}
            if self.store.db.in_transaction:
                self._event("ADAPTER_WITHDRAWN", detail)
            else:
                with self.store.transaction():
                    self._event("ADAPTER_WITHDRAWN", detail)
            raise Refuse("source withdrawn: " + str(error)) from error
        return item

    def install(self, adapter: InstrumentAdapterV0) -> dict:
        require(isinstance(adapter, InstrumentAdapterV0), "adapter does not satisfy InstrumentAdapterV0")
        descriptor = adapter.describe()
        descriptor.validate()
        id_ = descriptor.instrument_id
        require(len(self.state["instruments"]) < 16 or id_ in self.state["instruments"], "instrument count budget exceeded")
        previous = self.state["instruments"].get(id_)
        require(not previous or previous["lifecycle"] != "retired", "retired instrument requires a new identity")
        item = {
            "descriptor": descriptor.to_dict(), "descriptor_sha256": digest(descriptor.to_dict()),
            "incarnation": str(uuid.uuid4()), "lifecycle": "active", "revision": 0,
            "dial": previous["dial"] if previous else Dial().to_dict(),
            "response_dial": previous["response_dial"] if previous else Dial(Address((0,))).to_dict(),
            "mode": previous["mode"] if previous else ("frequency" if descriptor.controls[0]["quantity"] == "frequency" else "field"),
            "observation": None, "selection": None, "attention_region": None, "focus": None,
        }
        self.adapters[id_] = adapter
        self.state["instruments"][id_] = item
        with self.store.transaction():
            self._event("INSTRUMENT_INSTALLED", {"instrument_id": id_, "incarnation": item["incarnation"],
                                                "previous_incarnation": previous["incarnation"] if previous else None})
        return json.loads(json.dumps(item["descriptor"]))

    def discover(self) -> dict:
        return {"schema": "static-os.instrument-discovery/v0", "transmission": "DISABLED",
                "instruments": [{"instrument_id": id_, "descriptor": item["descriptor"],
                                 "lifecycle": item["lifecycle"], "incarnation": item["incarnation"],
                                 "current_adapter_installed": id_ in self.adapters,
                                 "dial": item["dial"], "mode": item["mode"],
                                 "psi_regions": psi_regions(dial_from_profile(item["dial"]).address)}
                                for id_, item in self.state["instruments"].items()]}

    def configure(self, id_: str, profile: dict) -> None:
        item = self._current(id_)
        dial = dial_from_profile(profile)
        item["dial"] = dial.to_dict()
        item["response_dial"] = Dial(Address((CURVES.index(dial.curve) * 3,))).to_dict()
        self._changed(id_, "CONTROLS_CONFIGURED")

    def set_positions(self, id_: str, positions: list[int]) -> None:
        item = self._current(id_)
        dial = dial_from_profile(item["dial"])
        item["dial"] = replace(dial, address=address_from_positions(positions), remainder=Fraction(0)).to_dict()
        self._changed(id_, "POSITIONS_SELECTED")

    def _changed(self, id_: str, kind: str, detail: dict | None = None) -> None:
        item = self.state["instruments"][id_]
        item["revision"] += 1
        item["selection"] = None
        with self.store.transaction():
            self._event(kind, {"instrument_id": id_, **(detail or {})})

    def turn(self, id_: str, ticks: int) -> None:
        item = self._current(id_)
        item["dial"] = dial_from_profile(item["dial"]).turn(ticks).to_dict()
        self._changed(id_, "DIAL_TURNED", {"ticks": ticks})

    def zoom(self, id_: str, position: int = 6) -> None:
        item = self._current(id_)
        dial = dial_from_profile(item["dial"])
        require(len(dial.address.digits) < MAX_ADDRESS_DEPTH, "zoom depth budget exceeded")
        require(type(position) is int and 1 <= position <= 11, "child position must be 1 through 11")
        item["dial"] = dial.zoom(position - 1).to_dict()
        self._changed(id_, "PSI_REGION_ENTERED", {"position": position})

    def turn_response(self, id_: str, ticks: int) -> None:
        item = self._current(id_)
        selector = dial_from_profile(item["response_dial"]).turn(ticks)
        curve = CURVES[min(3, int(selector.address.center * 4))]
        item["response_dial"] = selector.to_dict()
        item["dial"] = replace(dial_from_profile(item["dial"]), curve=curve).to_dict()
        self._changed(id_, "RESPONSE_DIAL_TURNED", {"ticks": ticks})

    def turn_sensitivity(self, id_: str, ticks: int, depth: int = 1) -> None:
        item = self._current(id_)
        require(type(depth) is int and 1 <= depth <= 8, "invalid sensitivity depth")
        def move(node: Dial, remaining: int) -> Dial:
            require(node.sensitivity is not None, "no sensitivity dial at that depth")
            changed = node.sensitivity.turn(ticks) if remaining == 1 else move(node.sensitivity, remaining - 1)
            return replace(node, sensitivity=changed)
        item["dial"] = move(dial_from_profile(item["dial"]), depth).to_dict()
        self._changed(id_, "SENSITIVITY_DIAL_TURNED", {"ticks": ticks, "depth": depth})

    def set_mode(self, id_: str, mode: str) -> None:
        item = self._current(id_)
        primary = "frequency" if item["descriptor"]["controls"][0]["quantity"] == "frequency" else "field"
        require(mode in (primary, "attention"), "unsupported typed map; authority expansion refused")
        if mode == "attention" and primary == "frequency":
            require(item["selection"] is not None and item["selection"]["type"] == "FrequencySelection",
                    "select a frequency source before attention")
            item["focus"] = item["selection"]["station"]
        item["mode"] = mode
        item["attention_region"] = None
        self._changed(id_, "TYPED_MAP_SELECTED")

    def observe(self, id_: str) -> dict:
        try:
            item = self._current(id_)
            observed = self.adapters[id_].observe()
            body = {k: v for k, v in observed.items() if k != "observation_sha256"}
            require(observed["observation_sha256"] == digest(body), "observation content hash changed")
            require(observed["source"] == item["descriptor"]["source"], "observation source history changed")
            require(0 < len(observed["items"]) <= 4096, "observation budget exceeded")
            bounded(observed)
            item["observation"] = observed
            item["selection"] = None
            item["revision"] += 1
            with self.store.transaction():
                self._event("SOURCE_OBSERVED", {"instrument_id": id_, "observation_ref": observed["observation_sha256"]})
            return json.loads(json.dumps(observed))
        except Refuse as error:
            self._deny(id_, "observe", str(error))
            raise

    def select(self, id_: str) -> dict:
        item = self._current(id_)
        require(item["observation"] is not None, "observe before selection")
        selected = self.adapters[id_].select(item["observation"], item["mode"],
                                            dial_from_profile(item["dial"]).address,
                                            tuple(item["attention_region"]) if item["attention_region"] else None,
                                            item["focus"])
        bounded(selected)
        item["selection"] = selected
        item["revision"] += 1
        with self.store.transaction():
            self._event("ATTENTION_SELECTED" if item["mode"] == "attention" else "INPUT_SELECTED",
                        {"instrument_id": id_, "selection": selected})
        return json.loads(json.dumps(selected))

    def simulated_autodisco(self, id_: str, width: int = 3) -> dict:
        item = self._current(id_)
        require(item["mode"] == "attention" and item["observation"] is not None,
                "Autodisco stand-in requires observed attention source")
        require(item["focus"] is not None, "simulated listening-region proposer requires recorded station")
        samples = item["observation"]["items"][item["focus"]]["samples"]
        # Invoke the unmodified oracle's proposer; its gate is never used for native operations.
        signal = Signal(str(item["focus"]), Fraction(1), tuple(samples), tuple(item["descriptor"]["source"]["history"]))
        oracle = Console(None, (signal,))  # Proposal-only; no authority service or execution.
        region = tuple(item["attention_region"]) if item["attention_region"] else (0, len(samples))
        oracle.switch_map(ControlMap("simulated-autodisco", 1, "attention", signal_id=signal.id, sample_region=region))
        proposed = oracle.autodisco(width)
        proposal = {"schema": "static-os.instrument-region-proposal/v0", "id": str(uuid.uuid4()),
                    "producer": "ELEVEN-HEAP simulated Autodisco (not native Autodisco)", "native_autodisco": False,
                    "instrument_id": id_, "incarnation": item["incarnation"], "revision": item["revision"],
                    "source_ref": item["descriptor"]["source"]["sha256"], "region": list(proposed.region),
                    "rationale": proposed.rationale, "proposal_only": True, "authority_effect": "none"}
        with self.store.transaction():
            self._event("SIMULATED_AUTODISCO_PROPOSAL", {"proposal": proposal})
        return proposal

    def accept_region(self, proposal: dict) -> None:
        id_ = proposal.get("instrument_id")
        item = self._current(id_)
        matches = [e for e in self.store.events() if e["kind"] == "SIMULATED_AUTODISCO_PROPOSAL"
                   and e["detail"]["proposal"]["id"] == proposal.get("id")]
        require(matches and matches[0]["detail"]["proposal"] == proposal, "unrecognized or laundered proposal")
        require(proposal["incarnation"] == item["incarnation"] and proposal["revision"] == item["revision"]
                and proposal["source_ref"] == item["descriptor"]["source"]["sha256"], "stale proposal")
        item["attention_region"] = proposal["region"]
        self._changed(id_, "REGION_EXPLICITLY_SELECTED", {"proposal_id": proposal["id"], "authority_effect": "none"})

    def propose_operation(self, id_: str, operation: str = "record") -> dict:
        try:
            item = self._current(id_)
            require(operation == "record", "transmission DISABLED; unsupported operation")
            require(item["selection"] is not None, "select before proposing a record")
            request = {"schema": "static-os.instrument-operation/v0", "id": str(uuid.uuid4()),
                       "session_id": self.state["session_id"], "process_incarnation": self.process,
                       "instrument_id": id_, "incarnation": item["incarnation"], "revision": item["revision"],
                       "descriptor_sha256": item["descriptor_sha256"], "source": item["descriptor"]["source"],
                       "observation_ref": item["observation"]["observation_sha256"],
                       "dial": item["dial"], "mode": item["mode"], "selection": item["selection"],
                       "operation": operation, "required_capabilities": ["observe", "record"],
                       "proposal_only": True, "transmission": "DISABLED"}
            bounded(request)
            boundary = self.authority.propose(request)
            with self.store.transaction():
                self.store.db.execute("INSERT INTO requests(id,body) VALUES(?,?)", (request["id"], bounded(request).decode()))
                self._event("OPERATION_PROPOSED", {"request": request, "crossing_boundary": boundary})
            return json.loads(json.dumps(request))
        except Refuse as error:
            self._deny(id_, operation, str(error))
            raise

    def _request(self, request: dict) -> dict:
        row = self.store.db.execute("SELECT body,consumed FROM requests WHERE id=?", (request.get("id"),)).fetchone()
        require(row is not None and json.loads(row[0]) == request, "unknown or laundered operation proposal")
        require(not row[1], "operation already consumed")
        require(request["process_incarnation"] == self.process, "historic operation belongs to a dead process")
        item = self._current(request["instrument_id"])
        require(request["incarnation"] == item["incarnation"] and request["revision"] == item["revision"]
                and request["descriptor_sha256"] == item["descriptor_sha256"]
                and request["source"] == item["descriptor"]["source"]
                and request["observation_ref"] == item["observation"]["observation_sha256"]
                and request["dial"] == item["dial"] and request["selection"] == item["selection"],
                "stale instrument operation binding")
        return item

    def owner_admit(self, request: dict, *, ttl_seconds: int = 60) -> dict:
        try:
            self._request(request)
            result = self.authority.owner_admit(request["id"], ttl_seconds=ttl_seconds)
            with self.store.transaction():
                self._event("OWNER_LOCAL_DECISION", {"request_id": request["id"], "native_receipt": result})
            return result
        except Refuse as error:
            self._deny(request.get("instrument_id"), "owner-admit", str(error))
            raise

    def execute(self, request: dict) -> dict:
        try:
            self._request(request)
            admission = self.authority.verify(request)
            require(admission.get("admitted") is True and admission.get("signature_verified") is True,
                    "native admission required")
            with self.store.transaction():
                # Recheck after native verification and take the single-consumption write lock.
                self._request(request)
                require(admission["crossing"]["requested_effect"]["expires_at"] > int(time.time() * 1000), "admission expired")
                receipt = {"schema": "static-os.instrument-execution-receipt/v0", "status": "RECORDED",
                           "request_id": request["id"], "instrument_id": request["instrument_id"],
                           "source": request["source"], "observation_ref": request["observation_ref"],
                           "selection": request["selection"], "dial": request["dial"],
                           "native_admission_receipt": admission["receipt"],
                           "authority_effect": "none", "rf_emitted": False}
                receipt["receipt_sha256"] = digest(receipt)
                self.store.db.execute("UPDATE requests SET consumed=1 WHERE id=?", (request["id"],))
                self._event("RECORD_EXECUTED", {"receipt": receipt})
            return receipt
        except Refuse as error:
            self._deny(request.get("instrument_id"), request.get("operation"), str(error), request.get("id"))
            raise

    def _deny(self, id_: str | None, operation: str | None, reason: str, request_id: str | None = None) -> dict:
        receipt = {"schema": "static-os.instrument-denial-receipt/v0", "instrument_id": id_,
                   "operation": operation, "request_id": request_id, "reason": reason,
                   "authority_effect": "none", "rf_emitted": False}
        receipt["receipt_sha256"] = digest(receipt)
        with self.store.transaction():
            current = self.store.load()
            if current["process_incarnation"] != self.process:
                # A rejected old writer may append evidence, but cannot resurrect its state.
                self.store.append("OPERATION_DENIED", {"receipt": receipt, "attempted_process": self.process}, current)
            else:
                self._event("OPERATION_DENIED", {"receipt": receipt})
        return receipt

    def withdraw(self, id_: str, *, retire: bool = False) -> None:
        item = self._item(id_)
        item["lifecycle"] = "retired" if retire else "withdrawn"
        item["revision"] += 1
        self.adapters.pop(id_, None)
        with self.store.transaction():
            self._event("INSTRUMENT_RETIRED" if retire else "INSTRUMENT_WITHDRAWN",
                        {"instrument_id": id_, "incarnation": item["incarnation"], "dial_preserved": True})

    def export(self) -> dict:
        self.store.verify()
        return {"schema": "static-os.instrument-evidence/v0", "session_id": self.state["session_id"],
                "transmission": "DISABLED", "events": self.store.events(),
                "native_admission_is_not_importable": True}

    def close(self) -> None:
        self.store.close()
