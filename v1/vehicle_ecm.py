"""V1 vehicle ECM observation adapter.

This module is intentionally observation-only. It accepts bounded telemetry
that was already obtained by an authorized local adapter and produces a
content-addressed receipt. It does not open a vehicle bus, transmit diagnostic
requests, actuate controls, clear faults, unlock sessions, reflash modules, or
write calibration/state.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

OBSERVATION_SCHEMA = "static-os.v1-vehicle-ecm-observation/v0"
RECEIPT_SCHEMA = "static-os.v1-vehicle-ecm-receipt/v0"

ALLOWED_SIGNALS = {
    "engine_rpm": "rpm",
    "vehicle_speed": "km/h",
    "coolant_temperature": "degC",
    "battery_voltage": "V",
    "fuel_level": "percent",
    "intake_air_temperature": "degC",
}

FORBIDDEN_KEYS = {
    "command",
    "write",
    "actuate",
    "throttle",
    "brake",
    "steering",
    "reflash",
    "flash",
    "erase",
    "clear_faults",
    "security_access",
    "diagnostic_session",
    "seed_key",
    "torque_request",
}


class Refuse(ValueError):
    """Raised when input crosses V1's observation-only vehicle boundary."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise Refuse(message)


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def _reject_forbidden(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if key in FORBIDDEN_KEYS:
                raise Refuse(f"vehicle control field refused at {path}.{key}")
            _reject_forbidden(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_forbidden(child, f"{path}[{index}]")


def normalize_observation(value: Any) -> dict[str, Any]:
    _require(isinstance(value, dict), "vehicle observation must be an object")
    _reject_forbidden(value)
    expected = {
        "schema",
        "vehicle_ref",
        "source_adapter",
        "session_id",
        "observed_at",
        "signals",
        "trouble_codes",
    }
    _require(set(value) == expected, "vehicle observation fields changed")
    _require(value.get("schema") == OBSERVATION_SCHEMA, "unsupported vehicle observation schema")
    for field in ("vehicle_ref", "source_adapter", "session_id", "observed_at"):
        _require(isinstance(value.get(field), str) and value[field], f"{field} required")

    signals = value.get("signals")
    _require(isinstance(signals, dict), "signals must be an object")
    normalized_signals: dict[str, dict[str, Any]] = {}
    for signal_name, signal in signals.items():
        _require(signal_name in ALLOWED_SIGNALS, f"signal not allowlisted: {signal_name}")
        _require(isinstance(signal, dict), f"signal {signal_name} must be an object")
        _require(set(signal) == {"value", "unit"}, f"signal {signal_name} fields changed")
        reading = signal.get("value")
        _require(
            isinstance(reading, (int, float)) and not isinstance(reading, bool),
            f"signal {signal_name} value must be numeric",
        )
        _require(
            signal.get("unit") == ALLOWED_SIGNALS[signal_name],
            f"signal {signal_name} unit mismatch",
        )
        normalized_signals[signal_name] = {
            "value": reading,
            "unit": signal["unit"],
        }

    codes = value.get("trouble_codes")
    _require(isinstance(codes, list), "trouble_codes must be a list")
    normalized_codes = []
    for code in codes:
        _require(isinstance(code, str) and 1 <= len(code) <= 16, "invalid trouble code token")
        normalized_codes.append(code)

    return {
        "schema": OBSERVATION_SCHEMA,
        "vehicle_ref": value["vehicle_ref"],
        "source_adapter": value["source_adapter"],
        "session_id": value["session_id"],
        "observed_at": value["observed_at"],
        "signals": normalized_signals,
        "trouble_codes": normalized_codes,
    }


def ingest_observation(value: Any) -> dict[str, Any]:
    observation = normalize_observation(value)
    observation_hash = digest(observation)
    receipt_without_hash = {
        "schema": RECEIPT_SCHEMA,
        "observation_sha256": observation_hash,
        "vehicle_ref": observation["vehicle_ref"],
        "source_adapter": observation["source_adapter"],
        "session_id": observation["session_id"],
        "observed_at": observation["observed_at"],
        "signal_names": sorted(observation["signals"]),
        "trouble_code_count": len(observation["trouble_codes"]),
        "mode": "observation-only",
        "vehicle_control_authority": "none",
        "diagnostic_write_authority": "none",
        "safety_critical_actuation": "forbidden",
        "automatic_next_turn": False,
        "laws": [
            "VEHICLE TELEMETRY != VEHICLE CONTROL",
            "BUS ACCESS != ACTUATION AUTHORITY",
            "DIAGNOSTIC ADDRESSABILITY != PERMISSION",
            "OBSERVATION != COMMAND",
            "ECM != DRIVER AUTHORITY",
            "SAFETY-CRITICAL WRITE != V1",
        ],
    }
    return {
        **receipt_without_hash,
        "receipt_sha256": digest(receipt_without_hash),
    }
