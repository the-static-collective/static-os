#!/usr/bin/env python3
"""A donor-owned ideal-gear arithmetic instrument. No Leonardo reconstruction."""
from __future__ import annotations

import json
import os
import sys
from fractions import Fraction

FORWARD = "mechanism.gear.forward.simulate"
INVERSE = "mechanism.gear.inverse.simulate"
SCHEMA = "static-os.gear-simulation-request/v0"


def run(request: object, capability: str) -> dict:
    if not isinstance(request, dict) or set(request) != {
        "schema", "operation", "driver_teeth", "driven_teeth", "input_turns"
    }:
        raise ValueError("EXACT_MECHANISM_INPUT_REQUIRED")
    if request["schema"] != SCHEMA:
        raise ValueError("UNSUPPORTED_MECHANISM_SCHEMA")
    if capability not in {FORWARD, INVERSE}:
        raise ValueError("UNREGISTERED_MECHANISM_CAPABILITY")
    operation = "forward" if capability == FORWARD else "inverse"
    if request["operation"] != operation:
        raise ValueError("CAPABILITY_OPERATION_MISMATCH")
    a, b, n = (request["driver_teeth"], request["driven_teeth"], request["input_turns"])
    if any(type(v) is not int for v in (a, b, n)):
        raise ValueError("MECHANISM_NUMERIC_TYPES")
    if not 4 <= a <= 200 or not 4 <= b <= 200 or not -100 <= n <= 100:
        raise ValueError("MECHANISM_BOUNDS")
    # Ideal external mesh: output rotates in the opposite direction.
    answer = -Fraction(a * n, b) if operation == "forward" else -Fraction(b * n, a)
    return {
        "schema": "static-os.gear-model-observation/v0",
        "status": "SIMULATION_ONLY",
        "operation": operation,
        "quantity": "driven_turns" if operation == "forward" else "driver_turns",
        "value": {"numerator": answer.numerator, "denominator": answer.denominator},
        "model": "IDEAL_TWO_EXTERNAL_SPUR_GEARS_NO_SLIP",
        "physical_measurement": False,
        "historical_reconstruction_verified": False,
        "transmission": False,
        "source_claim": "MODERN_IDEALIZATION_NO_VERIFIED_LEONARDO_FOLIO",
    }


def main() -> int:
    try:
        result = run(json.load(sys.stdin), os.environ.get("GHOT_EXTERNAL_CAPABILITY", ""))
        print(json.dumps(result, sort_keys=True))
        return 0
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {str(exc)[:120]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
