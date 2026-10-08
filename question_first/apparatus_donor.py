#!/usr/bin/env python3
"""Two replaceable SIMULATION-ONLY apparatus instruments. No hardware API.

A modern mechanical idealization, NOT a reconstruction of a Leonardo folio.
The composite capability performs one bounded pure calculation rather than
quietly dispatching a series of other capabilities.
"""
from __future__ import annotations
import json
import os
import sys
from fractions import Fraction

DIRECT = "mechanism.leadscrew.translate.simulate"
GEARED = "mechanism.apparatus.gear-leadscrew.simulate"
SCHEMA = "static-os.apparatus-input/v0"
OUT = "static-os.apparatus-simulation/v0"


def rational(number: Fraction) -> dict:
    return {"numerator": number.numerator, "denominator": number.denominator}


def run(payload: object, capability: str) -> dict:
    if type(payload) is not dict or set(payload) != {
        "schema", "mode", "driver_teeth", "driven_teeth", "input_turns",
        "lead_um_per_turn", "source_ref",
    } or payload.get("schema") != SCHEMA:
        raise ValueError("EXACT_APPARATUS_INPUT_REQUIRED")
    if capability not in (DIRECT, GEARED):
        raise ValueError("UNREGISTERED_APPARATUS_CAPABILITY")
    mode = "geared" if capability == GEARED else "direct"
    if payload["mode"] != mode:
        raise ValueError("APPARATUS_MODE_CAPABILITY_MISMATCH")
    for key, lower, upper in (
        ("driver_teeth", 4, 200), ("driven_teeth", 4, 200),
        ("input_turns", -100, 100), ("lead_um_per_turn", 100, 20000),
    ):
        v = payload[key]
        if type(v) is not int or not lower <= v <= upper:
            raise ValueError("APPARATUS_NUMERIC_BOUNDS")
    if (type(payload["source_ref"]) is not str
            or not payload["source_ref"].startswith("apparatus-source-v0:")
            or len(payload["source_ref"]) != len("apparatus-source-v0:") + 64
            or any(c not in "0123456789abcdef" for c in payload["source_ref"].split(":")[-1])):
        raise ValueError("APPARATUS_SOURCE_REF_INVALID")
    # An external gear mesh reverses direction. A modern leadscrew then
    # converts rotation to ideal signed axial travel, with zero loss/backlash.
    turns = (Fraction(-payload["driver_teeth"] * payload["input_turns"],
                      payload["driven_teeth"]) if mode == "geared"
             else Fraction(payload["input_turns"]))
    travel_um = turns * payload["lead_um_per_turn"]
    return {
        "schema": OUT,
        "status": "SIMULATION_ONLY",
        "mode": mode,
        "source_ref": payload["source_ref"],
        "gear_output_turns": rational(turns),
        "output_axial_um": rational(travel_um),
        "model": "IDEAL_EXTERNAL_GEARS_AND_LEADSCREW_ZERO_LOSS",
        "instrument_steps": (
            ["IDEAL_GEAR_RATIO", "IDEAL_LEADSCREW_TRANSLATION"]
            if mode == "geared" else ["IDEAL_LEADSCREW_TRANSLATION"]
        ),
        "physical_execution": False,
        "historical_reconstruction": False,
        "automatic_next_execution": False,
        "transmission": False,
    }


if __name__ == "__main__":
    try:
        result = run(json.load(sys.stdin),
                     os.environ.get("GHOT_EXTERNAL_CAPABILITY", ""))
        print(json.dumps(result, sort_keys=True))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f"REFUSE: {str(exc)[:150]}", file=sys.stderr)
        raise SystemExit(2)
