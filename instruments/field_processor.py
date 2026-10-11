"""FIELD-PROCESSOR-001: synthetic opt-in ambient field as a native read-only instrument.

This imports STATIC-OS InstrumentAdapterV0 and its original ELEVEN-HEAP mathematics.
It has NO sensor access, wireless transmission, matching server, consent service,
messaging side effects, network access, or independent execution authority.
"""
from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from vendor.eleven_heap_001.infinite_radio import Address, digest
from .contract import InstrumentDescriptorV0, Refuse, controls, observation, require

SCHEMA = "static-os.field-source/v0"
RESULT_SCHEMA = "static-os.field-result/v0"
MAX_SOURCE_BYTES = 65536
MAX_ROOMS = 16
MAX_CANDIDATES = 128
MODES = frozenset({"SONG_SEAT", "ROOM_RHYME", "GROUND_ECHO"})
ALLOWED_FIELDS = frozenset({
    "id", "opted_in", "revoked", "expires_at", "modes", "share",
    "song_ref", "texture", "weather", "weather_basis",
    "ground_event", "ground_basis"
})
ALL_ATTRIBUTES = frozenset({
    "song_ref", "texture", "weather", "ground_event"
})
DECISIONS = frozenset({"ACCEPT", "HOLD", "DECLINE"})


def _utc(value: object) -> datetime:
    require(isinstance(value, str) and value.endswith("Z"), "UTC timestamp required")
    try:
        d = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise Refuse("invalid timestamp") from error
    require(d.tzinfo is not None, "timezone required")
    return d.astimezone(timezone.utc)


def _read(path: Path) -> tuple[bytes, dict]:
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_SOURCE_BYTES + 1)
    except OSError as error:
        raise Refuse("field source unavailable") from error
    require(0 < len(raw) <= MAX_SOURCE_BYTES, "field source outside byte budget")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeError) as error:
        raise Refuse("invalid source JSON") from error
    require(type(data) is dict and set(data) == {
        "schema", "classification", "now", "offers", "decisions"
    }, "field source schema changed")
    require(data["schema"] == SCHEMA and data["classification"] == "SYNTHETIC_ONLY",
            "only explicitly synthetic field sources supported")
    require(type(data["offers"]) is list and 1 <= len(data["offers"]) <= MAX_ROOMS,
            "room count out of budget")
    require(type(data["decisions"]) is dict, "invalid simulated decisions")
    now = _utc(data["now"])
    ids = set()
    for room in data["offers"]:
        require(type(room) is dict and set(room) == ALLOWED_FIELDS,
                "room attributes changed or contain prohibited data")
        rid = room["id"]
        require(type(rid) is str and 1 <= len(rid) <= 48 and rid not in ids,
                "invalid/duplicate room ID")
        ids.add(rid)
        require(type(room["opted_in"]) is bool and type(room["revoked"]) is bool,
                "opt-in and revoke must be explicit booleans")
        require(type(room["modes"]) is list
                and len(set(room["modes"])) == len(room["modes"])
                and set(room["modes"]) <= MODES, "invalid room modes")
        require(type(room["share"]) is list
                and len(set(room["share"])) == len(room["share"])
                and set(room["share"]) <= ALL_ATTRIBUTES, "invalid disclosed attributes")
        for key in ("song_ref", "texture", "weather", "weather_basis",
                    "ground_event", "ground_basis"):
            value = room[key]
            require(value is None or (type(value) is str and 0 < len(value) <= 128),
                    "invalid feature or overlong value")
        _utc(room["expires_at"])
    require(set(data["decisions"]) <= ids, "decision references unknown room")
    require(all(v in DECISIONS for v in data["decisions"].values()),
            "invalid simulated decision")
    return raw, data


def _evaluate_validated(data: dict) -> dict:
    now = _utc(data["now"])
    active = sorted((
        o for o in data["offers"]
        if o["opted_in"] is True and o["revoked"] is False
        and _utc(o["expires_at"]) > now
    ), key=lambda o: o["id"])
    candidates = []
    evaluated = 0
    for i, left in enumerate(active):
        for right in active[i + 1:]:
            evaluated += 1
            shared_modes = set(left["modes"]) & set(right["modes"])
            def both_share(*keys: str) -> bool:
                return all(k in left["share"] and k in right["share"] for k in keys)
            def emit(mode: str, evidence: list[str]) -> None:
                decisions = (data["decisions"].get(left["id"], "HOLD"),
                             data["decisions"].get(right["id"], "HOLD"))
                state = ("REFUSED" if "DECLINE" in decisions else
                         "MUTUAL_READY_SIMULATED" if decisions == ("ACCEPT", "ACCEPT") else "HOLD")
                candidates.append({
                    "mode": mode, "left": left["id"], "right": right["id"],
                    "status": state, "evidence": evidence, "authority": "NONE",
                    "independence": "UNPROVEN", "consequence": "NONE"
                })
            if ("SONG_SEAT" in shared_modes and both_share("song_ref")
                    and left["song_ref"] is not None and left["song_ref"] == right["song_ref"]):
                emit("SONG_SEAT", ["SAME_DECLARED_RECORDING_REF"])
            if ("ROOM_RHYME" in shared_modes and both_share("texture", "weather")
                    and left["texture"] is not None and left["weather"] is not None
                    and left["texture"] == right["texture"]
                    and left["weather"] == right["weather"]
                    and left["weather_basis"] is not None
                    and left["weather_basis"] == right["weather_basis"]):
                emit("ROOM_RHYME", ["SHARED_COARSE_TEXTURE", "SAME_TYPED_WEATHER"])
            if ("GROUND_ECHO" in shared_modes and both_share("ground_event")
                    and left["ground_event"] is not None
                    and left["ground_event"] == right["ground_event"]
                    and left["ground_basis"] == right["ground_basis"] == "SYNTHETIC_SENSOR"):
                emit("GROUND_ECHO", ["SHARED_SIMULATED_EVENT_CLASS", "SAME_VEHICLE_UNPROVEN"])
    require(len(candidates) <= MAX_CANDIDATES, "candidate count over budget")
    candidates.sort(key=lambda c: (c["mode"], c["left"], c["right"]))
    result = {
        "schema": RESULT_SCHEMA,
        "source_classification": "SYNTHETIC_ONLY",
        "active_room_count": len(active),
        "candidate_count": len(candidates),
        "pair_comparisons": evaluated,
        "candidates": candidates,
        "created_connections": [],
        "device_commands": [],
        "nonclaims": [
            "PHYSICAL_RECEPTION", "HARDWARE_MEASUREMENT", "COLOCATION",
            "PERSON_IDENTITY", "GROUND_CAUSATION", "CONSENT_TO_CONNECT"
        ]
    }
    return {**result, "result_sha256": digest(result)}


class FieldProcessorAdapter:
    """Propose limited ROOMTONE candidates through STATIC-OS's existing host."""

    def __init__(self, path: Path, *, instrument_id: str = "synthetic-field-processor"):
        self.path = path.resolve()
        self.instrument_id = instrument_id

    def _descriptor(self, raw: bytes) -> InstrumentDescriptorV0:
        source_hash = sha256(raw).hexdigest()
        return InstrumentDescriptorV0(
            self.instrument_id, "static-os.field-processor/v0",
            "ROOMTONE SYNTHETIC FIELD (NO SENSOR HARDWARE)",
            {
                "kind": "synthetic-field-fixture",
                "reference": "fixture-sha256:" + source_hash,
                "history": ["FIELD-PROCESSOR-001", "declared opt-in simulation only",
                            "no real persons, actual weather, or ground sensors"],
                "sha256": source_hash
            },
            {"revision": "field-processor-001", "synthetic_only": True,
             "max_rooms": MAX_ROOMS, "max_candidates": MAX_CANDIDATES},
            controls("candidate index", "synthetic ordinal", [0, MAX_CANDIDATES])
        )

    def describe(self) -> InstrumentDescriptorV0:
        raw, _ = _read(self.path)
        return self._descriptor(raw)

    def observe(self) -> dict:
        raw, data = _read(self.path)
        descriptor = self._descriptor(raw)
        result = _evaluate_validated(data)
        # Only consented candidate references enter durable host observation.
        # Nonparticipant identities and raw offered features are not exported.
        items = result["candidates"] or [{
            "type": "NO_CANDIDATE", "status": "HOLD",
            "authority": "NONE", "consequence": "NONE"
        }]
        return observation(descriptor.source, items,
                           classification="synthetic opt-in field evaluation; no sensing, network or connection")

    def select(self, observed: dict, mode: str, address: Address,
               region: tuple[int, int] | None = None, focus: int | None = None) -> dict:
        require(mode in ("field", "attention"), "invalid field control mode")
        require(type(observed) is dict and type(observed.get("items")) is list,
                "invalid observation")
        items = observed["items"]
        require(0 < len(items) <= MAX_CANDIDATES, "candidate item budget")
        low, high = region if (mode == "attention" and region is not None) else (0, len(items))
        require(type(low) is int and type(high) is int and 0 <= low < high <= len(items),
                "invalid bounded selection region")
        index = low + min(high - low - 1, int(address.center * (high - low)))
        result = items[index]
        require(result.get("authority") == "NONE" and result.get("consequence") == "NONE",
                "candidate gained authority")
        return {"type": "FieldCandidateSelection", "mode": mode, "index": index,
                "candidate": result, "may_connect": False, "may_transmit": False,
                "may_actuate": False, "requires_owner_admission_for_record": True}
