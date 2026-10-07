"""CRANKNODE-003 physical-edge gate.

One accepted hardware edge may authorize at most one CRANKNODE turn attempt.
The edge is durably consumed before work begins, so a failed provider cannot
silently retry from the same physical act.

The serial protocol is deliberately small and device-agnostic. A rotary
encoder, pedal, lever, relay, or other appliance can emit one newline-delimited
JSON frame per physical event.
"""
from __future__ import annotations

import fcntl
import json
import os
import select
import termios
from pathlib import Path
from typing import Any

from .runtime import Refuse, digest

EDGE_SCHEMA = "static-os.crank-physical-edge/v0"
GATE_RECEIPT_SCHEMA = "static-os.crank-edge-gate-receipt/v0"
MAX_FRAME_BYTES = 4096

BAUDS = {
    9600: termios.B9600,
    19200: termios.B19200,
    38400: termios.B38400,
    57600: termios.B57600,
    115200: termios.B115200,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Refuse(message)


def normalize_edge(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "physical edge must be an object")
    expected = {
        "schema",
        "device_id",
        "session_id",
        "sequence",
        "direction",
        "ticks",
    }
    _require(set(value) == expected, "physical edge fields changed")
    _require(value.get("schema") == EDGE_SCHEMA, "unsupported physical edge schema")
    _require(
        isinstance(value.get("device_id"), str) and value["device_id"],
        "physical edge device_id required",
    )
    _require(
        isinstance(value.get("session_id"), str) and value["session_id"],
        "physical edge session_id required",
    )
    sequence = value.get("sequence")
    _require(
        isinstance(sequence, int) and not isinstance(sequence, bool) and sequence >= 0,
        "physical edge sequence must be a non-negative integer",
    )
    _require(value.get("direction") in {"CW", "CCW"}, "physical edge direction must be CW or CCW")
    _require(value.get("ticks") == 1, "one physical edge must contain exactly one tick")
    return {
        "schema": EDGE_SCHEMA,
        "device_id": value["device_id"],
        "session_id": value["session_id"],
        "sequence": sequence,
        "direction": value["direction"],
        "ticks": 1,
    }


def edge_id(value: Any) -> str:
    return f"static-os-crank-edge-v0:{digest(normalize_edge(value))}"


def edge_to_turn(
    edge: Any,
    capability_id: str,
    payload: dict[str, Any],
    budget_units: int,
) -> dict[str, Any]:
    normalized = normalize_edge(edge)
    identity = edge_id(normalized)
    _require(isinstance(capability_id, str) and capability_id, "capability_id required")
    _require(isinstance(payload, dict), "turn payload must be an object")
    _require(
        isinstance(budget_units, int)
        and not isinstance(budget_units, bool)
        and budget_units >= 0,
        "budget_units must be a non-negative integer",
    )
    return {
        "schema": "static-os.crank-turn-request/v0",
        "turn_id": f"TURN-PHYSICAL-{digest(normalized)[:24]}",
        "source": {
            "kind": "physical-input",
            "id": identity,
        },
        "selected_capability": capability_id,
        "budget_units": budget_units,
        "authority_request": "none",
        "admission_request": "none",
        "payload": payload,
    }


def claim_edge(value: Any, ledger_path: str | Path) -> dict[str, Any]:
    """Durably consume one edge exactly once.

    The ledger is append-only JSONL and protected with an advisory exclusive
    file lock. The claim is flushed and fsynced before returning.
    """
    edge = normalize_edge(value)
    identity = edge_id(edge)
    path = Path(ledger_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        for line in handle:
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError as exc:
                raise Refuse("physical edge ledger contains invalid JSON") from exc
            if entry.get("edge_id") == identity:
                raise Refuse("physical edge already consumed")

        receipt_without_hash = {
            "schema": GATE_RECEIPT_SCHEMA,
            "edge_id": identity,
            "edge": edge,
            "consumed": True,
            "authorizes": "one-turn-attempt-only",
            "semantic_authority": "none",
            "admission_authority": "none",
            "automatic_retry": False,
            "automatic_next_turn": False,
            "laws": [
                "PHYSICAL EDGE != SEMANTIC AUTHORITY",
                "ONE EDGE = AT MOST ONE TURN ATTEMPT",
                "BOUNCE != SECOND TURN",
                "REPLAY != NEW PHYSICAL ACT",
                "FAILED TURN != RETRY AUTHORITY",
            ],
        }
        receipt = dict(receipt_without_hash)
        receipt["gate_receipt_sha256"] = digest(receipt_without_hash)
        handle.seek(0, os.SEEK_END)
        handle.write(json.dumps(receipt, sort_keys=True, separators=(",", ":")) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
        return receipt


def decode_edge_frame(frame: bytes) -> dict[str, Any]:
    _require(isinstance(frame, bytes), "physical edge frame must be bytes")
    _require(0 < len(frame) <= MAX_FRAME_BYTES, "physical edge frame size invalid")
    _require(frame.endswith(b"\n"), "physical edge frame must end with newline")
    try:
        text = frame.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise Refuse("physical edge frame must be UTF-8") from exc
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise Refuse("physical edge frame must be JSON") from exc
    return normalize_edge(value)


def read_one_tty_frame(
    device_path: str,
    baud: int = 115200,
    timeout_seconds: float = 10.0,
) -> dict[str, Any]:
    """Read exactly one newline-delimited edge frame from a POSIX TTY and exit."""
    _require(baud in BAUDS, "unsupported serial baud")
    _require(timeout_seconds > 0, "serial timeout must be positive")

    fd = os.open(device_path, os.O_RDONLY | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        attrs = termios.tcgetattr(fd)
        attrs[0] = 0
        attrs[1] = 0
        attrs[2] = termios.CS8 | termios.CREAD | termios.CLOCAL
        attrs[3] = 0
        attrs[4] = BAUDS[baud]
        attrs[5] = BAUDS[baud]
        attrs[6][termios.VMIN] = 0
        attrs[6][termios.VTIME] = 0
        termios.tcsetattr(fd, termios.TCSANOW, attrs)

        data = bytearray()
        while True:
            ready, _, _ = select.select([fd], [], [], timeout_seconds)
            if not ready:
                raise Refuse("physical edge serial read timed out")
            chunk = os.read(fd, 256)
            if not chunk:
                continue
            data.extend(chunk)
            if len(data) > MAX_FRAME_BYTES:
                raise Refuse("physical edge frame exceeds maximum size")
            newline = data.find(b"\n")
            if newline >= 0:
                return decode_edge_frame(bytes(data[: newline + 1]))
    finally:
        os.close(fd)
