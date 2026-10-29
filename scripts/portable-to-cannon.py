#!/usr/bin/env python3
"""Device-agnostic, intentionally inert community first-boot intent receiver.

Supported low-power front doors:
  Nintendo GameCube (external FAT/SD-Gecko, when present)
  Nintendo DS (DLDI-compatible FAT storage, when present)
  ESP32 (USB serial terminal; operator explicitly captures one JSON)
  Android Termux / Raspberry Pi / legacy laptop (Python 3)
Source device claims are self-declared, not device attestation. No autonomous
network calls, signing, physical access, permission transfer or field witness.
Only separately specified --execute may run *reviewed original CANNON code*.
"""
import argparse
import json
import pathlib
import subprocess
import sys

SCHEMA = "static-os.portable-first-boot-intent/v1"
PINNED_CANNON_SHA = "92a73324ec6918765cbd15b7a12cb83878b403eb"
QUESTIONS = {
    "Living House": "Can one Suitcase help an ordinary house become cooperative infrastructure?",
    "Community Food": "Can one Suitcase help a house coordinate a fictional community food table?",
    "Festival Table": "Can one Suitcase help a house plan a fictional cooperative festival?",
    "Repair Lab": "Can one Suitcase help a house plan a fictional repair workshop?",
}
DEVICES = frozenset((
    "NINTENDO_GAMECUBE_SD", "NINTENDO_DS_DLDI",
    "ESP32_USB_SERIAL", "ANDROID_TERMUX_LOCAL",
    "RASPBERRY_PI_LOCAL", "LEGACY_LINUX_PYTHON3",
))
FIELDS = frozenset((
    "schema", "mission", "focus", "question", "scenario", "mode",
    "source_device", "status", "operator_action", "network_transmitted",
    "physical_observation", "signed", "independent_witness",
))


def make_intent(device, focus):
    if device not in DEVICES or focus not in QUESTIONS:
        raise ValueError("UNSUPPORTED_DEVICE_OR_QUESTION")
    return {
        "schema": SCHEMA, "mission": "living-house",
        "focus": focus, "question": QUESTIONS[focus],
        "scenario": "FICTIONAL_A_B", "mode": "OFFLINE_HOLD_ONLY",
        "source_device": device, "status": "PROPOSAL_ONLY_NOT_EXECUTED",
        "operator_action": "EXPLICIT_LOCAL_EXPORT",
        "network_transmitted": False, "physical_observation": False,
        "signed": False, "independent_witness": False,
    }


def validate(value):
    if not isinstance(value, dict) or set(value) != FIELDS:
        raise ValueError("UNKNOWN_OR_MISSING_PORTABLE_INTENT_KEYS")
    expected = make_intent(value.get("source_device"), value.get("focus"))
    if value != expected:
        raise ValueError("UNSUPPORTED_OR_ESCALATED_INTENT")
    return value


def load_intent(path):
    file = pathlib.Path(path)
    if not file.is_file() or file.stat().st_size > 2048:
        raise ValueError("REFUSE_NONFILE_OR_OVERSIZED_INTENT")
    return validate(json.loads(file.read_text(encoding="utf8")))


def execute_with_cannon(request, args):
    needed = ["cannon", "staticos", "webz", "gro", "ghot", "jarvis", "out"]
    if any(not getattr(args, field) for field in needed):
        raise ValueError("MISSING_OPERATOR_SELECTED_SOURCE_ROOTS")
    cannon = pathlib.Path(args.cannon).resolve()
    actual = subprocess.check_output(
        ["git", "-C", str(cannon), "rev-parse", "HEAD"],
        stderr=subprocess.DEVNULL, text=True, timeout=12
    ).strip()
    if actual != PINNED_CANNON_SHA:
        raise ValueError("SOURCE_PIN_REFUSED: CANNON must match reviewed experiment")
    runner = cannon / "scripts" / "genesis-boot.mjs"
    if not runner.is_file():
        raise ValueError("MISSING_ORIGINAL_CANNON_RUNNER")
    output = pathlib.Path(args.out).resolve()
    if output.exists():
        raise ValueError("OUTPUT_ALREADY_EXISTS")
    cmd = ["node", str(runner), "build"]
    for field in ["staticos", "webz", "gro", "ghot", "jarvis"]:
        cmd += ["--"+field, str(pathlib.Path(getattr(args, field)).resolve())]
    cmd += ["--out", str(output), "--question", request["question"]]
    subprocess.run(cmd, check=True, timeout=120)
    return {"status": "SOURCE_PINNED_CANNON_SOFTWARE_PLAN_GENERATED",
            "witnessed_human": False, "real_material": False,
            "physical_work": False, "source_device_authenticated": False,
            "output": str(output)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--validate", action="store_true")
    mode.add_argument("--execute", action="store_true")
    for name in ["cannon", "staticos", "webz", "gro", "ghot", "jarvis", "out"]:
        parser.add_argument("--"+name)
    args = parser.parse_args(argv)
    try:
        proposed = load_intent(args.intent)
        if args.validate:
            print(json.dumps({"status": "VALID_INERT_PORTABLE_INTENT",
                              "focus": proposed["focus"],
                              "source_device_claim": proposed["source_device"],
                              "executed": False}, sort_keys=True))
        else:
            print(json.dumps(execute_with_cannon(proposed, args), sort_keys=True))
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print("HOLD: " + str(e)[:420], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
