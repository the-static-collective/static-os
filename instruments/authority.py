"""A thin native reLATTE client, never an alternative admission system."""
from __future__ import annotations

import base64
import json
from pathlib import Path
import subprocess
import time

from .adapters import RELATTE_COMMIT, verify_donor
from .contract import Refuse, bounded, require


class NativeRelatte:
    boundary = "native-relatte"

    def __init__(self, donor: Path, root: Path):
        self.donor, self.root = donor.resolve(), root.resolve()

    def call(self, action: str, value: dict) -> dict:
        verify_donor(self.donor, RELATTE_COMMIT)
        bridge = Path(__file__).with_name("relatte_bridge.mjs")
        try:
            proc = subprocess.run(["node", "--experimental-strip-types", str(bridge), str(self.donor),
                                   str(self.root), action], input=bounded(value), capture_output=True,
                                  timeout=20, check=True)
            require(len(proc.stdout) <= 65536, "native reLATTE response budget exceeded")
            return json.loads(proc.stdout)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            # Error text is public protocol feedback, not native private key material.
            stderr = getattr(error, "stderr", b"") or b""
            reason = stderr.decode(errors="replace")[-2000:]
            raise Refuse("native reLATTE refused or unavailable: " + reason) from error

    def initialize(self) -> dict:
        return self.call("init", {})

    def snapshot(self) -> dict:
        return self.call("snapshot", {})

    def propose(self, request: dict) -> dict:
        return self.call("propose", {"request": request, "bytes": base64.b64encode(bounded(request)).decode()})

    def owner_admit(self, id_: str, *, ttl_seconds: int = 60) -> dict:
        require(type(ttl_seconds) is int and 0 < ttl_seconds <= 3600, "invalid admission lifetime")
        return self.call("owner-admit", {"id": id_, "expires_at": int(time.time() * 1000) + ttl_seconds * 1000})

    def verify(self, request: dict) -> dict:
        from hashlib import sha256
        return self.call("verify-admission", {"id": request["id"], "request_sha256": sha256(bounded(request)).hexdigest()})


class UnavailableRelatte:
    """Discovery may proceed; protected execution never falls back to a simulated grant."""

    boundary = "native-relatte-unavailable"

    def propose(self, request: dict) -> dict:
        return {"boundary": self.boundary, "candidate_only": True, "admitted": False,
                "native_hold_receipt": None}

    def owner_admit(self, id_: str, **kwargs) -> dict:
        raise Refuse("native reLATTE owner admission unavailable")

    def verify(self, request: dict) -> dict:
        raise Refuse("native reLATTE owner admission unavailable")
