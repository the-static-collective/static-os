#!/usr/bin/env python3
import json
import sys

request = json.loads(sys.stdin.read())
if request.get("schema") != "static-os.ai-provider-request/v0":
    raise SystemExit(2)
if request.get("proposal_only") is not True:
    raise SystemExit(3)
if request.get("authority_request") != "none" or request.get("admission_request") != "none":
    raise SystemExit(4)

prompt = request.get("prompt", "")
response = {
    "schema": "static-os.ai-provider-response/v0",
    "provider_id": "fixture-alpha",
    "model_id": "fixture-alpha-v1",
    "proposal": f"ALPHA proposes one bounded move for: {prompt}",
    "model_execution_claim": "fixture-provider-executed-not-a-live-model",
}
sys.stdout.write(json.dumps(response, sort_keys=True))
