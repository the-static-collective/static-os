#!/usr/bin/env python3
"""Native GHoT portable-packet signature verifier, invoked read-only by STATIC OS."""
from __future__ import annotations

import json
import sys
from pathlib import Path

def main() -> int:
    if len(sys.argv) != 2:
        raise ValueError("GHOT_SOURCE_ROOT_REQUIRED")
    root = Path(sys.argv[1]).expanduser().resolve(strict=True)
    lib = root / "ghot"
    if not (lib / "instrument_rack.py").is_file():
        raise ValueError("GHOT_NATIVE_VERIFIER_MISSING")
    sys.path.insert(0, str(lib))
    from instrument_rack import _validate_packet
    packet = json.load(sys.stdin)
    verified = _validate_packet(packet)
    print(json.dumps({
        "status": "VERIFIED_NATIVE_GHOT_PACKET",
        "packet_id": verified["packet_id"],
        "signature_checked_by": "ghot.instrument_rack._validate_packet",
    }))
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"REFUSE: {type(exc).__name__}: {str(exc)[:180]}", file=sys.stderr)
        raise SystemExit(2)
