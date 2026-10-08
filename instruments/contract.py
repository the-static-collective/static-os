"""Generic bounded instrument contract; ELEVEN-HEAP owns the dial mathematics."""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import json
from typing import Protocol, runtime_checkable

from vendor.eleven_heap_001.infinite_radio import Address, CURVES, Dial, digest

SCHEMA = "static-os.instrument-adapter/v0"
MAX_ADDRESS_DEPTH = 16
MAX_SENSITIVITY_DEPTH = 8
MAX_BYTES = 65536
READ_ONLY_CAPABILITIES = frozenset({"observe", "select", "attend", "record"})


class Refuse(ValueError):
    pass


def require(condition: bool, reason: str) -> None:
    if not condition:
        raise Refuse(reason)


def bounded(value: object) -> bytes:
    data = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    require(len(data) <= MAX_BYTES, "instrument payload exceeds byte budget")
    return data


def dial_from_profile(profile: dict, depth: int = 0) -> Dial:
    require(isinstance(profile, dict), "dial profile must be an object")
    if depth == 0:
        bounded(profile)
    require(depth <= MAX_SENSITIVITY_DEPTH, "sensitivity nesting exceeds budget")
    require(set(profile) == {"address", "curve", "context_load", "threshold", "remainder", "sensitivity"},
            "dial profile fields changed; profiles cannot carry authority")
    address = profile["address"]
    require(isinstance(address, dict) and set(address) == {"radix", "digits"}, "malformed dial address")
    require(isinstance(address["digits"], list) and 1 <= len(address["digits"]) <= MAX_ADDRESS_DEPTH,
            "address depth exceeds budget")
    if profile["sensitivity"] is not None:
        dial_from_profile(profile["sensitivity"], depth + 1)
    try:
        result = Dial.from_dict(profile)
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as error:
        raise Refuse("malformed dial profile") from error
    return result


def address_from_positions(positions: list[int]) -> Address:
    require(isinstance(positions, list) and 1 <= len(positions) <= MAX_ADDRESS_DEPTH,
            "invalid nested positions")
    require(all(type(p) is int and 1 <= p <= 11 for p in positions), "positions must be 1 through 11")
    return Address(tuple(p - 1 for p in positions))


def psi_regions(address: Address) -> list[dict]:
    """Each PSI region is an original ELEVEN-HEAP prefix interval, not new mathematics."""
    regions = []
    for depth in range(1, len(address.digits) + 1):
        prefix = Address(address.digits[:depth])
        low, high = prefix.interval
        regions.append({"positions": [x + 1 for x in prefix.digits], "address": prefix.to_dict(),
                        "normalized_interval": [str(low), str(high)]})
    return regions


@dataclass(frozen=True)
class InstrumentDescriptorV0:
    instrument_id: str
    adapter: str
    label: str
    source: dict
    calibration: dict
    controls: tuple[dict, ...]
    capabilities: tuple[str, ...] = ("observe", "select", "attend", "record")

    def to_dict(self) -> dict:
        return {"schema": SCHEMA, "instrument_id": self.instrument_id, "adapter": self.adapter,
                "label": self.label, "source": self.source, "calibration": self.calibration,
                "controls": list(self.controls), "capabilities": list(self.capabilities),
                "transmission": "DISABLED"}

    def validate(self) -> None:
        require(bool(self.instrument_id) and bool(self.adapter), "instrument identity required")
        require(set(self.capabilities) <= READ_ONLY_CAPABILITIES, "unauthorized capability expansion")
        require(set(self.capabilities) == READ_ONLY_CAPABILITIES, "read-only contract capabilities changed")
        require(len(self.controls) == 2, "selector and attention controls required")
        require({c.get("id") for c in self.controls} == {"selector", "attention"}, "controls changed")
        for control in self.controls:
            require(set(control) == {"id", "quantity", "unit", "range", "curves", "sensitivity"},
                    "control fields changed")
            require(control["curves"] == list(CURVES), "response policies changed")
            require(control["sensitivity"] == "recursive", "sensitivity grammar changed")
        require(set(self.source) == {"kind", "reference", "history", "sha256"}, "source fields changed")
        require(isinstance(self.source["history"], list) and bool(self.source["history"]), "source lineage required")
        bounded(self.to_dict())


def controls(quantity: str, unit: str, control_range: list) -> tuple[dict, ...]:
    return tuple({"id": id_, "quantity": q, "unit": u, "range": r,
                  "curves": list(CURVES), "sensitivity": "recursive"}
                 for id_, q, u, r in (("selector", quantity, unit, control_range),
                                      ("attention", "source region", "source item index", [0, 4096])))


@runtime_checkable
class InstrumentAdapterV0(Protocol):
    """Adapters expose bounded read-only data. The host owns receipts and lifecycle.

    describe() must freshly bind source lineage and calibration. observe() returns
    immutable content-addressed evidence. select() interprets an original Address
    as its own typed quantity. Adapters have no grant or transmit method.
    """

    def describe(self) -> InstrumentDescriptorV0: ...
    def observe(self) -> dict: ...
    def select(self, observation: dict, mode: str, address: Address,
               region: tuple[int, int] | None = None, focus: int | None = None) -> dict: ...


def observation(source: dict, items: list[dict], *, classification: str) -> dict:
    body = {"schema": "static-os.instrument-observation/v0", "source": source,
            "items": items, "classification": classification}
    require(0 < len(items) <= 4096, "observation item budget exceeded")
    bounded(body)
    return {**body, "observation_sha256": digest(body)}
