#!/usr/bin/env python3
"""Independently call the actual VM-local operator endpoint, *never mock output*.

Use only a fictional question, and assert no physical/real-witness claims.
If the ISO has booted and the service is running, this proves a real kernel to
live-system userspace to source-native execution path, not GUI/XFCE success.
"""
import json
from urllib.request import Request, urlopen
from pathlib import Path

ROOT = "http://127.0.0.1:8766"
def call(path, body=None, token=None):
    headers = {"Accept": "application/json"}
    if body is not None:
        headers.update({"Origin": ROOT, "X-Genesis-Token": token,
                        "Content-Type": "application/json"})
    request = Request(ROOT + path, data=None if body is None else
                      json.dumps(body).encode(), headers=headers,
                      method="GET" if body is None else "POST")
    with urlopen(request, timeout=95) as response:
        return json.loads(response.read(2000000))

status = call("/api/status")
assert status["mode"] == "LOCAL_ONLY_SOURCE_PINNED_HUMAN_REVIEW"
assert status["history"] == [] and status["warmAvailable"] is True
assert status["physicalProof"] == "NONE" and status["independentOperators"] == "NONE"
print("STATIC-OS-VM-EXPLORATION-STATUS-OK", flush=True)
nonce = status["nonce"]
result = call("/api/compose", {
    "question": "Could one Suitcase build a cooperative house?",
    "acknowledgePublicSafe": True}, nonce)
assert result["generated"] is True
proof = call("/api/verify", {"id": result["id"]}, nonce)
assert proof["status"] == "CROSS_BRANCH_NATIVE_COLD_REPLAY_VERIFIED"
assert proof["housePlans"] == 2 and proof["fieldStatus"] == "NOT_WITNESSED"
print("STATIC-OS-VM-HOUSE-A-B-NATIVE-OK", flush=True)
warm = call("/api/warm", {"acknowledgeFictional": True}, nonce)
witness = call("/api/verify", {"id": warm["id"]}, nonce)
assert witness["status"] == "WARM_SOURCE_NATIVE_COLD_REPLAY_VERIFIED"
assert witness["remainingFictionalLoad"] == 1
assert witness["personConfirmedDelivery"] == 0
assert witness["fieldStatus"] == "NOT_WITNESSED"
print("STATIC-OS-VM-WARM-THREAD-NATIVE-OK", flush=True)
# No source package or project authority is added to the operator's real world.
assert len(call("/api/status")["history"]) == 2
