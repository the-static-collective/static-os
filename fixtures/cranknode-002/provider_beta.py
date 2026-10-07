#!/usr/bin/env python3
import json
import sys

request = json.loads(sys.stdin.read())
if request.get("schema") != "static-os.ai-provider-request/v0":
    raise SystemExit(2)

prompt = request.get("prompt", "")
response = {
    "schema": "static-os.ai-provider-response/v0",
    "provider_id": "fixture-beta",
    "model_id": "fixture-beta-v1",
    "proposal": f"BETA offers a different bounded proposal for: {prompt}",
    "model_execution_claim": "fixture-provider-executed-not-a-live-model",
}
sys.stdout.write(json.dumps(response, sort_keys=True))
