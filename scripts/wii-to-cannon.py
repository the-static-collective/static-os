#!/usr/bin/env python3
"""Human-directed, offline Wii SD -> original CANNON GENESIS bridge.

The Wii runs native PowerPC code and exports a static *proposal*, not a program.
CANNON (on a separately controlled Linux/Windows/macOS computer) executes its
original source-pinned House A/B software only when the operator deliberately
invokes --execute. No Wii internet, live source calls, passwords, or external
permission. The input JSON is never treated as a shell command or Git ref.
"""
import argparse
import json
import pathlib
import subprocess
import sys

SCHEMA = "static-os.wii-first-boot-intent/v1"
PINNED_CANNON_SHA = "92a73324ec6918765cbd15b7a12cb83878b403eb"
FIELDS = frozenset((
    "schema", "mission", "focus", "question", "scenario", "mode",
    "source_device", "operator_action", "status", "transmitted",
    "physical_observation", "signed", "independent_witness",
))
QUESTION = {
    "Living House":
        "Can one Suitcase help an ordinary house become cooperative infrastructure?",
    "Community Food":
        "Can one Suitcase help a house coordinate a fictional community food table?",
    "Festival Table":
        "Can one Suitcase help a house plan a fictional cooperative festival?",
    "Repair Lab":
        "Can one Suitcase help a house plan a fictional repair workshop?",
}


def validate(payload):
    if not isinstance(payload, dict) or frozenset(payload) != FIELDS:
        raise ValueError("REFUSE_UNKNOWN_OR_MISSING_WII_FIELDS")
    expected = {
        "schema": SCHEMA,
        "mission": "living-house",
        "focus": payload.get("focus"),
        "question": QUESTION.get(payload.get("focus")),
        "scenario": "FICTIONAL_A_B",
        "mode": "OFFLINE_HOLD_ONLY",
        "source_device": "WII_HOMEBREW_LOCAL_OPERATOR",
        "operator_action": "PLUS_EXPORT_PRESSED",
        "status": "PROPOSAL_ONLY_NOT_EXECUTED",
        "transmitted": False,
        "physical_observation": False,
        "signed": False,
        "independent_witness": False,
    }
    if payload != expected or expected["question"] is None:
        raise ValueError("REFUSE_UNSUPPORTED_OR_ESCALATED_WII_PROPOSAL")
    return payload


def load(file):
    source = pathlib.Path(file)
    if not source.is_file() or source.stat().st_size > 2048:
        raise ValueError("REFUSE_WII_FILE_SIZE_OR_TYPE")
    return validate(json.loads(source.read_text(encoding="utf-8")))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", required=True, help="Copied SD public-safe JSON file")
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--validate", action="store_true", help="Only validate, do not execute anything")
    modes.add_argument("--execute", action="store_true", help="Explicitly run original CANNON code")
    for name in ("cannon", "staticos", "webz", "gro", "ghot", "jarvis", "out"):
        parser.add_argument("--"+name)
    args = parser.parse_args(argv)
    try:
        original = load(args.intent)
        if args.validate:
            print(json.dumps({"status": "VALID_INERT_WII_INTENT",
                              "focus": original["focus"], "executed": False},
                             sort_keys=True))
            return 0
        required = ("cannon", "staticos", "webz", "gro", "ghot", "jarvis", "out")
        if any(getattr(args, key) is None for key in required):
            raise ValueError("REFUSE_MISSING_OPERATOR_SELECTED_SOURCE_PATHS")
        cannon = pathlib.Path(args.cannon).resolve()
        actual = subprocess.check_output(
            ["git", "-C", str(cannon), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL, timeout=10,
        ).strip()
        if actual != PINNED_CANNON_SHA:
            raise ValueError("REFUSE_UNPINNED_CANNON_EXECUTABLE")
        launcher = cannon / "scripts" / "genesis-boot.mjs"
        if not launcher.is_file():
            raise ValueError("REFUSE_MISSING_CANNON_GENESIS_RUNNER")
        output = pathlib.Path(args.out).resolve()
        if output.exists():
            raise ValueError("REFUSE_OVERWRITE_EXISTING_OUTPUT")
        command = [
            "node", str(launcher), "build", "--staticos", str(pathlib.Path(args.staticos).resolve()),
            "--webz", str(pathlib.Path(args.webz).resolve()),
            "--gro", str(pathlib.Path(args.gro).resolve()),
            "--ghot", str(pathlib.Path(args.ghot).resolve()),
            "--jarvis", str(pathlib.Path(args.jarvis).resolve()),
            "--out", str(output), "--question", original["question"],
        ]
        # Executing reviewed CANNON functions is separate from Wii file creation.
        # CANNON checks exact donor commits/bytes, and produces HOLD-only receipts.
        subprocess.run(command, check=True, timeout=120)
        print(json.dumps({"status": "CANNON_NATIVE_SOFTWARE_PROPOSAL_GENERATED",
                          "wii_is_human_witness": False,
                          "physical_work_completed": False,
                          "source_transmitted_by_wii": False,
                          "output": str(output)}, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        print("HOLD: "+str(e)[:500], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
