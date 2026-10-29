#!/usr/bin/env python3
"""GENESIS on an old laptop, Android/Termux or Raspberry Pi without Node.

A strictly offline HUMAN-FACING PORTABLE INTERFACE (not full CANNON).
Requires Python >=3.8 and a manually selected writable destination.
The only output is a 13-field fixed public-safe JSON proposal; no build,
network, apt, flashing, device probing, enrolment or installation.
"""
import argparse
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("portable_bridge", ROOT/"scripts"/"portable-to-cannon.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)

DEVICES = ("ANDROID_TERMUX_LOCAL", "RASPBERRY_PI_LOCAL", "LEGACY_LINUX_PYTHON3")


def create_only(directory, data):
    output = pathlib.Path(directory)
    if not output.is_dir():
        raise ValueError("EXPLICIT_DESTINATION_DIRECTORY_MUST_ALREADY_EXIST")
    for n in range(1, 1000):
        path = output / ("intent-%03d.json" % n)
        try:
            with path.open("x", encoding="utf8") as handle:
                handle.write(json.dumps(data, indent=2, sort_keys=True)+"\n")
            path.chmod(0o600)
            return path
        except FileExistsError:
            continue
    raise ValueError("REFUSE_999_EXISTING_FILES_NOT_OVERWRITTEN")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device", choices=DEVICES, required=True)
    parser.add_argument("--out-dir", required=True)
    args = parser.parse_args(argv)
    print("STATIC GENESIS / tiny-device operator porch")
    print("HELLO, WORLD. What shall we build together?")
    print("A local proposal is not real evidence and is never executed here.\n")
    for i, name in enumerate(bridge.QUESTIONS, 1):
        print("%d. %s" % (i, name))
    try:
        choice = input("Select 1-4 or ENTER to cancel: ").strip()
        if choice not in ("1", "2", "3", "4"):
            print("HOLD: no proposal exported.")
            return 0
        focus = list(bridge.QUESTIONS)[int(choice)-1]
        print("\nProposed question: "+bridge.QUESTIONS[focus])
        print("This records a FICTIONAL A/B software request, not actual household work.")
        if input("Type EXPORT exactly to write one local JSON file: ").strip() != "EXPORT":
            print("HOLD: no file created.")
            return 0
        candidate = bridge.validate(bridge.make_intent(args.device, focus))
        path = create_only(args.out_dir, candidate)
        print("LOCAL INTENT ONLY: "+str(path))
        print("Copy manually to another independently controlled CANNON computer.")
        return 0
    except (OSError, EOFError, ValueError) as error:
        print("HOLD: "+str(error)[:240], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
