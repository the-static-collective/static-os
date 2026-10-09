#!/usr/bin/env python3
"""PRINT-FIELD-012 — discover all declared printer families; NEVER dispatch."""
from __future__ import annotations
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from question_first.session import Hold, require
from question_first.printer_field import compile_field, verify_field, _load_registry


def load(path: str) -> dict:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    require(type(data) is dict, "EXPECTED_JSON_OBJECT")
    return data


def write_once(path: Path, result: dict) -> None:
    path = path.expanduser().resolve()
    require(not path.exists(), "FIELD_OUTPUT_OCCUPIED_NO_AUTORETRY")
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_EXCL | os.O_CREAT, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Discover all owner-declared machine technologies; refuse all physical effects.")
    parser.add_argument("command", choices=("catalog", "discover", "verify"))
    parser.add_argument("--source")
    parser.add_argument("--print-packet")
    parser.add_argument("--fleet")
    parser.add_argument("--out")
    opts = parser.parse_args(argv)
    if opts.command == "catalog":
        require(not any((opts.source, opts.print_packet, opts.fleet, opts.out)),
                "CATALOG_IS_READ_ONLY")
        registry, families = _load_registry()
        print(json.dumps({
            "schema": registry["schema"], "recognized_families": list(families),
            "physically_validated_printers": 0, "auto_execution": False
        }, sort_keys=True))
        return 0
    require(all((opts.source, opts.print_packet, opts.fleet, opts.out)),
            "EXACT_SOURCE_PACKET_FLEET_OUTPUT_REQUIRED")
    source, print_packet = Path(opts.source), Path(opts.print_packet)
    fleet = load(opts.fleet)
    out = Path(opts.out)
    if opts.command == "discover":
        require(not out.exists(), "FIELD_OUTPUT_OCCUPIED_NO_AUTORETRY")
        result = compile_field(source, print_packet, fleet)
        write_once(out, result)
    else:
        result = verify_field(source, print_packet, fleet, load(opts.out))
    print(json.dumps({
        "status": "PRINTER_FIELD_READ_ONLY",
        "field_id": result["field_id"],
        "machine_count": result["machine_count"],
        "recognized_technologies": result["recognized_process_families"],
        "route_statuses": {m["machine_id"]: m["compatibility_status"] for m in result["machines"]},
        "printers_connected": 0, "prints_started": 0, "physical_output_created": False,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (Hold, OSError, ValueError, TypeError, KeyError, json.JSONDecodeError) as err:
        print("HOLD: " + str(err)[:240], file=sys.stderr)
        raise SystemExit(2)
