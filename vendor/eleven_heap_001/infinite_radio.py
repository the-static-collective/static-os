"""ELEVEN-HEAP-001 reference model. Standard library only; no RF hardware path.

Historic settings are data. Current authority belongs to a separate trusted gate.
This models reLATTE semantics; it is not an integration with an existing reLATTE implementation.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from fractions import Fraction
from hashlib import sha256
import json
from typing import Literal

RADIX = 11
Curve = Literal["linear", "logarithmic", "thresholded", "context-sensitive"]
CURVES = ("linear", "logarithmic", "thresholded", "context-sensitive")
# Version-1 fixed-point lookup of 10*log10(1 + 9*ticks/10), at ticks 0..10.
# The table itself is normative: serialization never relies on platform libm.
LOG_RESPONSE = (0, 2787536, 4471580, 5682017, 6627578, 7403627,
                8061800, 8633229, 9138139, 9590414, 10000000)


def digest(value: object) -> str:
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def integer(value: object) -> int:
    if type(value) is not int:
        raise ValueError("expected an integer")
    return value


@dataclass(frozen=True)
class Address:
    """Base-eleven path, digits 0..10. Each digit selects one of eleven child regions."""

    digits: tuple[int, ...] = (5,)

    def __post_init__(self) -> None:
        if not isinstance(self.digits, tuple) or not self.digits:
            raise ValueError("an address needs a nonempty tuple of digits")
        if any(type(d) is not int or not 0 <= d < RADIX for d in self.digits):
            raise ValueError("address digits must be integers from 0 through 10")

    @property
    def index(self) -> int:
        value = 0
        for digit in self.digits:
            value = value * RADIX + digit
        return value

    @property
    def interval(self) -> tuple[Fraction, Fraction]:
        denominator = RADIX ** len(self.digits)
        return Fraction(self.index, denominator), Fraction(self.index + 1, denominator)

    @property
    def center(self) -> Fraction:
        low, high = self.interval
        return (low + high) / 2

    def zoom(self, child: int = 5) -> Address:
        return Address(self.digits + (child,))

    def shift(self, steps: int) -> Address:
        integer(steps)
        value = max(0, min(RADIX ** len(self.digits) - 1, self.index + steps))
        digits = []
        for _ in self.digits:
            value, digit = divmod(value, RADIX)
            digits.append(digit)
        return Address(tuple(reversed(digits)))

    def to_dict(self) -> dict:
        return {"radix": RADIX, "digits": list(self.digits)}

    @classmethod
    def from_dict(cls, data: dict) -> Address:
        if type(data["radix"]) is not int or data["radix"] != RADIX:
            raise ValueError("unknown address grammar")
        return cls(tuple(data["digits"]))


@dataclass(frozen=True)
class Dial:
    """A dial may contain another dial controlling its motion sensitivity.

    Response transforms movement, never authority. Context and fractional movement
    remainder are captured, so small movements and context-dependent replay are reproducible.
    """

    address: Address = Address()
    curve: Curve = "linear"
    context_load: Fraction = Fraction(0)
    threshold: int = 2
    remainder: Fraction = Fraction(0)
    sensitivity: Dial | None = None

    def __post_init__(self) -> None:
        if self.curve not in CURVES:
            raise ValueError("unknown response curve")
        if type(self.threshold) is not int or not 1 <= self.threshold <= 10:
            raise ValueError("threshold must be an integer from 1 through 10")
        if not isinstance(self.context_load, Fraction) or self.context_load < 0:
            raise ValueError("context load must be a nonnegative rational")
        if not isinstance(self.remainder, Fraction) or abs(self.remainder) >= 1:
            raise ValueError("movement remainder must be between -1 and 1")

    @property
    def gain(self) -> Fraction:
        own = 1 / (1 + 10 * self.address.center)
        return own * (self.sensitivity.gain if self.sensitivity else 1)

    def turn(self, ticks: int) -> Dial:
        integer(ticks)
        if not -10 <= ticks <= 10:
            raise ValueError("one gesture must contain between -10 and 10 ticks")
        magnitude = abs(ticks)
        if self.curve == "logarithmic":
            response = Fraction(LOG_RESPONSE[magnitude], 1_000_000)
        elif self.curve == "thresholded":
            response = Fraction(magnitude if magnitude >= self.threshold else 0)
        elif self.curve == "context-sensitive":
            response = Fraction(magnitude) / (1 + self.context_load)
        else:
            response = Fraction(magnitude)
        if ticks < 0:
            response = -response
        motion = self.remainder + response * (self.sensitivity.gain if self.sensitivity else 1)
        steps = int(motion)  # Truncate toward zero; preserve fractional pending motion.
        address = self.address.shift(steps)
        # Discard pending motion at an end stop; it must not cause a delayed jump.
        blocked = (address.index == 0 and motion < 0) or (
            address.index == RADIX ** len(address.digits) - 1 and motion > 0
        )
        return replace(self, address=address, remainder=Fraction(0) if blocked else motion - steps)

    def zoom(self, child: int = 5) -> Dial:
        return replace(self, address=self.address.zoom(child), remainder=Fraction(0))

    def to_dict(self) -> dict:
        return {
            "address": self.address.to_dict(), "curve": self.curve,
            "context_load": str(self.context_load), "threshold": self.threshold,
            "remainder": str(self.remainder),
            "sensitivity": self.sensitivity.to_dict() if self.sensitivity else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Dial:
        return cls(
            Address.from_dict(data["address"]), data["curve"], Fraction(data["context_load"]),
            integer(data["threshold"]), Fraction(data["remainder"]),
            cls.from_dict(data["sensitivity"]) if data["sensitivity"] else None,
        )


@dataclass(frozen=True)
class Signal:
    id: str
    frequency_hz: Fraction
    samples: tuple[int, ...]
    source_history: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"id": self.id, "frequency_hz": str(self.frequency_hz),
                "samples": list(self.samples), "source_history": list(self.source_history)}


@dataclass(frozen=True)
class FrequencySelection:
    frequency_hz: Fraction
    cell_hz: tuple[Fraction, Fraction]


@dataclass(frozen=True)
class AttentionSelection:
    signal_id: str
    sample_region: tuple[int, int]  # Half-open source sample indices; never Hz.


@dataclass(frozen=True)
class TransmissionRequest:
    frequency_hz: Fraction
    power_w: Fraction
    mode: str


Selection = FrequencySelection | AttentionSelection | TransmissionRequest


@dataclass(frozen=True)
class ControlMap:
    id: str
    version: int
    kind: Literal["frequency", "attention", "transmit"]
    low_hz: Fraction = Fraction(88_000_000)
    high_hz: Fraction = Fraction(108_000_000)
    signal_id: str | None = None
    sample_region: tuple[int, int] | None = None
    power_w: Fraction = Fraction(1)
    mode: str = "FM"

    def __post_init__(self) -> None:
        if self.kind not in ("frequency", "attention", "transmit"):
            raise ValueError("unknown typed control map")
        if not self.id or type(self.version) is not int or self.version < 1:
            raise ValueError("map needs an id and a positive version")
        if self.low_hz <= 0 or self.high_hz <= self.low_hz or self.power_w <= 0:
            raise ValueError("invalid frequency or power range")
        if self.kind == "attention":
            if not self.signal_id or self.sample_region is None:
                raise ValueError("attention requires an explicit source and sample region")
            low, high = self.sample_region
            if type(low) is not int or type(high) is not int or low < 0 or high <= low:
                raise ValueError("invalid attention region")

    @property
    def operation(self) -> str:
        return {"frequency": "receive", "attention": "attend", "transmit": "transmit"}[self.kind]

    def interpret(self, address: Address) -> Selection:
        if self.kind == "attention":
            assert self.sample_region is not None and self.signal_id is not None
            low, high = self.sample_region
            offset = int(address.center * (high - low))
            return AttentionSelection(self.signal_id, (low + offset, low + offset + 1))
        span = self.high_hz - self.low_hz
        value = self.low_hz + span * address.center
        if self.kind == "transmit":
            return TransmissionRequest(value, self.power_w, self.mode)
        return FrequencySelection(value, tuple(self.low_hz + span * x for x in address.interval))

    def to_dict(self) -> dict:
        return {"id": self.id, "version": self.version, "kind": self.kind,
                "low_hz": str(self.low_hz), "high_hz": str(self.high_hz),
                "signal_id": self.signal_id,
                "sample_region": list(self.sample_region) if self.sample_region else None,
                "power_w": str(self.power_w), "mode": self.mode}

    @classmethod
    def from_dict(cls, data: dict) -> ControlMap:
        return cls(data["id"], integer(data["version"]), data["kind"], Fraction(data["low_hz"]),
                   Fraction(data["high_hz"]), data["signal_id"],
                   tuple(data["sample_region"]) if data["sample_region"] else None,
                   Fraction(data["power_w"]), data["mode"])


class Denied(RuntimeError):
    pass


@dataclass(frozen=True)
class RadioAuthorization:
    operator: str
    device: str
    jurisdiction: str
    low_hz: Fraction
    high_hz: Fraction
    max_power_w: Fraction
    modes: tuple[str, ...]
    expires_at: int


class AuthorityGate:
    """Trusted simulation fixture, outside the dial grammar.

    Grant/revoke are administrative operations. A dial, map, proposal, request,
    or imported history has no reference to those operations. No actual RF adapter exists.
    """

    def __init__(self, *, operator: str = "experimenter", device: str = "simulated-receiver",
                 jurisdiction: str = "simulation") -> None:
        self.operator, self.device, self.jurisdiction = operator, device, jurisdiction
        self._epochs: dict[str, int] = {}
        self._affordances: set[str] = set()
        self._permission_until: int | None = None
        self._radio: RadioAuthorization | None = None

    def grant_affordance(self, operation: str) -> None:
        self._epochs[operation] = self.epoch(operation) + 1
        self._affordances.add(operation)

    def withdraw(self, operation: str) -> None:
        self._epochs[operation] = self.epoch(operation) + 1
        self._affordances.discard(operation)

    def epoch(self, operation: str) -> int:
        return self._epochs.get(operation, 0)

    def set_transmit_permission(self, expires_at: int | None) -> None:
        self._permission_until = expires_at
        self._epochs["transmit"] = self.epoch("transmit") + 1

    def set_radio_authorization(self, authorization: RadioAuthorization | None) -> None:
        self._radio = authorization
        self._epochs["transmit"] = self.epoch("transmit") + 1

    def state(self) -> dict:
        return {"epochs": dict(self._epochs), "affordances": sorted(self._affordances),
                "transmit_permission_until": self._permission_until,
                "radio_authorization": None if self._radio is None else {
                    "operator": self._radio.operator, "device": self._radio.device,
                    "jurisdiction": self._radio.jurisdiction,
                    "low_hz": str(self._radio.low_hz), "high_hz": str(self._radio.high_hz),
                    "max_power_w": str(self._radio.max_power_w),
                    "modes": list(self._radio.modes), "expires_at": self._radio.expires_at}}

    def check(self, operation: str, epoch: int, selection: Selection, *, now: int) -> None:
        if epoch != self.epoch(operation):
            raise Denied("stale authority epoch")
        if operation not in self._affordances:
            raise Denied("affordance withdrawn or absent")
        expected = {"receive": FrequencySelection, "attend": AttentionSelection,
                    "transmit": TransmissionRequest}.get(operation)
        if expected is None or type(selection) is not expected:
            raise Denied("operation and selection type disagree")
        if operation == "transmit":
            if self._permission_until is None or now >= self._permission_until:
                raise Denied("separate transmission permission absent or expired")
            radio = self._radio
            if radio is None or now >= radio.expires_at:
                raise Denied("applicable radio authorization absent or expired")
            assert isinstance(selection, TransmissionRequest)
            if (radio.operator != self.operator or radio.device != self.device
                    or radio.jurisdiction != self.jurisdiction
                    or not radio.low_hz <= selection.frequency_hz <= radio.high_hz
                    or not 0 < selection.power_w <= radio.max_power_w
                    or selection.mode not in radio.modes):
                raise Denied("radio authorization does not cover this request")


@dataclass(frozen=True)
class Prepared:
    id: int
    revision: int
    epoch: int
    map_digest: str
    operation: str
    selection: Selection
    source_digest: str


@dataclass(frozen=True)
class Proposal:
    id: int
    revision: int
    map_digest: str
    signal_id: str
    source_digest: str
    region: tuple[int, int]
    rationale: str


class Console:
    def __init__(self, gate: AuthorityGate, signals: tuple[Signal, ...],
                 dial: Dial | None = None) -> None:
        if len({s.id for s in signals}) != len(signals):
            raise ValueError("signal IDs must be unique")
        self.gate = gate
        self.signals = {s.id: s for s in signals}
        self.dial = dial or Dial()
        self.response_dial = Dial(Address((0,)))
        self.response_dial = replace(self.response_dial, address=Address((CURVES.index(self.dial.curve) * 3,)))
        self.control_map = ControlMap("frequency", 1, "frequency")
        self.revision = 0
        self._history: list[dict] = []
        self._requests: dict[int, Prepared] = {}
        self._proposals: dict[int, Proposal] = {}
        self._used: set[int] = set()
        self._event("initialized")

    def snapshot(self) -> dict:
        return {"revision": self.revision, "dial": self.dial.to_dict(),
                "response_dial": self.response_dial.to_dict(),
                "control_map": self.control_map.to_dict(),
                "sources": [s.to_dict() for s in self.signals.values()]}

    def _event(self, action: str, detail: dict | None = None) -> None:
        previous = self._history[-1]["hash"] if self._history else "genesis"
        event = {"sequence": len(self._history), "action": action, "detail": detail or {},
                 "snapshot": self.snapshot(), "previous": previous}
        self._history.append({**event, "hash": digest(event)})

    @property
    def history(self) -> list[dict]:
        return json.loads(json.dumps(self._history))  # Do not expose mutable historic objects.

    def _change(self, action: str, detail: dict | None = None) -> None:
        self.revision += 1
        self._event(action, detail)

    def turn(self, ticks: int) -> None:
        self.dial = self.dial.turn(ticks)
        self._change("turned", {"ticks": ticks})

    def zoom(self, child: int = 5) -> None:
        self.dial = self.dial.zoom(child)
        self._change("zoomed", {"child": child})

    def set_response(self, curve: Curve, *, context_load: Fraction = Fraction(0)) -> None:
        self.dial = replace(self.dial, curve=curve, context_load=context_load)
        self.response_dial = Dial(Address((CURVES.index(curve) * 3,)))
        self._change("response_changed")

    def turn_response(self, ticks: int) -> None:
        """The second physical selector is interpreted as a response policy, not a quantity."""
        self.response_dial = self.response_dial.turn(ticks)
        curve = CURVES[min(3, int(self.response_dial.address.center * 4))]
        self.dial = replace(self.dial, curve=curve)
        self._change("response_dial_turned", {"ticks": ticks})

    def turn_sensitivity(self, ticks: int, *, depth: int = 1) -> None:
        """Turn a meta-dial at any installed depth; no grant operation is reachable."""
        if type(depth) is not int or depth < 1:
            raise ValueError("sensitivity depth must be a positive integer")

        def move(node: Dial, remaining: int) -> Dial:
            if node.sensitivity is None:
                raise ValueError("no sensitivity dial at that depth")
            sensitivity = (node.sensitivity.turn(ticks) if remaining == 1
                           else move(node.sensitivity, remaining - 1))
            return replace(node, sensitivity=sensitivity)

        self.dial = move(self.dial, depth)
        self._change("sensitivity_dial_turned", {"ticks": ticks, "depth": depth})

    def set_sensitivity(self, sensitivity: Dial | None) -> None:
        self.dial = replace(self.dial, sensitivity=sensitivity)
        self._change("sensitivity_changed")

    def switch_map(self, control_map: ControlMap) -> None:
        if control_map.kind == "attention":
            signal = self.signals.get(control_map.signal_id)
            if signal is None or control_map.sample_region[1] > len(signal.samples):
                raise ValueError("attention map is outside the source")
        self.control_map = control_map
        self._change("map_switched")

    def prepare(self) -> Prepared:
        request = Prepared(len(self._requests), self.revision,
                           self.gate.epoch(self.control_map.operation),
                           digest(self.control_map.to_dict()), self.control_map.operation,
                           self.control_map.interpret(self.dial.address),
                           digest([s.to_dict() for s in self.signals.values()]))
        self._requests[request.id] = request
        self._event("request_prepared", {"request_id": request.id, "operation": request.operation})
        return request

    def execute(self, request: Prepared, *, now: int) -> dict:
        try:
            if self._requests.get(request.id) is not request:
                raise Denied("request was not prepared by this console")
            if request.id in self._used:
                raise Denied("request already consumed")
            if request.revision != self.revision or request.map_digest != digest(self.control_map.to_dict()):
                raise Denied("stale control binding")
            if request.source_digest != digest([s.to_dict() for s in self.signals.values()]):
                raise Denied("stale source binding")
            if request.selection != self.control_map.interpret(self.dial.address):
                raise Denied("stale dial binding")
            self.gate.check(request.operation, request.epoch, request.selection, now=now)
        except Denied as error:
            self._event("request_denied", {"request_id": request.id, "reason": str(error)})
            raise
        selection = request.selection
        if isinstance(selection, FrequencySelection):
            matches = sorted((s for s in self.signals.values()
                              if selection.cell_hz[0] <= s.frequency_hz < selection.cell_hz[1]),
                             key=lambda s: (abs(s.frequency_hz - selection.frequency_hz), s.id))
            result = {"kind": "simulated_reception", "frequency_hz": str(selection.frequency_hz),
                      "signal": matches[0].to_dict() if matches else None}
        elif isinstance(selection, AttentionSelection):
            signal = self.signals[selection.signal_id]
            low, high = selection.sample_region
            result = {"kind": "attention", "signal_id": signal.id,
                      "sample_region": [low, high], "samples": list(signal.samples[low:high]),
                      "source_history": list(signal.source_history)}
        else:
            result = {"kind": "simulated_transmission", "rf_emitted": False,
                      "frequency_hz": str(selection.frequency_hz),
                      "power_w": str(selection.power_w), "mode": selection.mode}
        self._used.add(request.id)
        self._event("request_executed", {"request_id": request.id, "result": result})
        return result

    def autodisco(self, width: int = 3) -> Proposal:
        """Deterministic stand-in: propose the highest-energy window inside the current region."""
        if self.control_map.kind != "attention":
            raise ValueError("Autodisco needs a typed attention map")
        low, high = self.control_map.sample_region
        if type(width) is not int or not 0 < width < high - low:
            raise ValueError("proposal must be strictly narrower")
        signal = self.signals[self.control_map.signal_id]
        start = max(range(low, high - width + 1),
                    key=lambda i: sum(x * x for x in signal.samples[i:i + width]))
        proposal = Proposal(len(self._proposals), self.revision, digest(self.control_map.to_dict()),
                            signal.id, digest(signal.to_dict()), (start, start + width),
                            "highest squared-amplitude window; earliest start breaks ties")
        self._proposals[proposal.id] = proposal
        self._event("autodisco_proposed", {"proposal_id": proposal.id,
                                          "region": list(proposal.region), "rationale": proposal.rationale})
        return proposal

    def accept(self, proposal: Proposal, *, now: int) -> None:
        if self._proposals.get(proposal.id) is not proposal:
            raise Denied("proposal was not created by this console")
        if (proposal.revision != self.revision
                or proposal.map_digest != digest(self.control_map.to_dict())
                or proposal.source_digest != digest(self.signals[proposal.signal_id].to_dict())):
            raise Denied("stale proposal")
        # Acceptance changes the map but cannot restore a withdrawn attention affordance.
        self.gate.check("attend", self.gate.epoch("attend"),
                        AttentionSelection(proposal.signal_id, proposal.region), now=now)
        self.switch_map(replace(self.control_map, version=self.control_map.version + 1,
                                sample_region=proposal.region))
        self._event("autodisco_accepted", {"proposal_id": proposal.id})

    def export(self) -> dict:
        return {"experiment": "ELEVEN-HEAP-001", "schema": 1, "history": self.history}


def replay(archive: dict, gate: AuthorityGate) -> Console:
    """Reconstruct data on another machine; caller supplies fresh, current authority.

    Hash chains detect accidental edits, not malicious replacement of a whole archive.
    Replay never imports affordances, permissions, radio authorizations, or executable requests.
    """
    if archive.get("experiment") != "ELEVEN-HEAP-001" or archive.get("schema") != 1:
        raise ValueError("unknown replay schema")
    history = archive.get("history", [])
    if not history:
        raise ValueError("empty history")
    previous = "genesis"
    for sequence, event in enumerate(history):
        payload = {k: v for k, v in event.items() if k != "hash"}
        if event["sequence"] != sequence or event["previous"] != previous or digest(payload) != event["hash"]:
            raise ValueError("history integrity check failed")
        Dial.from_dict(event["snapshot"]["dial"])
        ControlMap.from_dict(event["snapshot"]["control_map"])
        previous = event["hash"]
    snapshot = history[-1]["snapshot"]
    signals = tuple(Signal(s["id"], Fraction(s["frequency_hz"]), tuple(s["samples"]),
                           tuple(s["source_history"])) for s in snapshot["sources"])
    console = Console(gate, signals, Dial.from_dict(snapshot["dial"]))
    console.response_dial = Dial.from_dict(snapshot["response_dial"])
    console.switch_map(ControlMap.from_dict(snapshot["control_map"]))
    console.revision = integer(snapshot["revision"])
    console._history = json.loads(json.dumps(history))
    console._event("reconstructed_with_current_authority")
    return console
