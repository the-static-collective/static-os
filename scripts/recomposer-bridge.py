#!/usr/bin/env python3
"""Source-owned read-only ABI for JAR;VIS Recursive Workshop (RECOMPOSER-003).

JSON object in via stdin, one JSON object out on stdout. No persistent state,
network, model calls, shell, file writes or external action. The caller holds
the returned state and decides whether to preserve an approved event.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from question_first.recomposer import genesis, compile_turn, observe_feedback, verify_state
from question_first.recomposer_witness import compile_candidate_family, witness_artifact

MAX_REQUEST = 160_000
OPERATIONS = {"genesis", "compile", "feedback", "artifact", "inspect"}


def run(request: object) -> dict:
    if type(request) is not dict or request.get("action") not in OPERATIONS:
        raise ValueError("INVALID_RECOMPOSER_ACTION")
    action = request["action"]
    if action == "genesis":
        return {"schema": "static-os.recomposer-bridge/v0", "state": genesis()}
    state = request.get("state")
    verify_state(state)
    if action == "inspect":
        return {"schema": "static-os.recomposer-bridge/v0", "state": state}
    plan = request.get("plan")
    if action == "compile":
        question = request.get("text")
        plan = compile_turn(state, question)
        family = compile_candidate_family(state, plan, request.get("artifact_receipts", []))
        return {"schema": "static-os.recomposer-bridge/v0",
                "plan": plan, "family": family}
    if action == "feedback":
        updated = observe_feedback(state, plan, request.get("selected"),
                                   request.get("outcome"),
                                   consent=request.get("consent") is True,
                                   promote_recipe=request.get("promote_recipe") is True)
        return {"schema": "static-os.recomposer-bridge/v0", "state": updated}
    if action == "artifact":
        receipt = witness_artifact(plan, request.get("topic"),
                                   request.get("output_sha256"),
                                   consent=request.get("consent") is True)
        return {"schema": "static-os.recomposer-bridge/v0", "receipt": receipt}
    raise ValueError("INVALID_RECOMPOSER_ACTION")


def main() -> int:
    try:
        body = sys.stdin.buffer.read(MAX_REQUEST + 1)
        if len(body) > MAX_REQUEST:
            raise ValueError("REQUEST_TOO_LARGE")
        data = json.loads(body)
        result = run(data)
        sys.stdout.write(json.dumps(result, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    except (ValueError, TypeError, KeyError, json.JSONDecodeError) as err:
        sys.stderr.write("HOLD:" + str(err).split("\n")[0][:150] + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
