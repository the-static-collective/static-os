#!/usr/bin/env python3
"""TRIAD-001 reference-only contract; validates declarations, performs no imports/effects."""
import json
import re
import sys
from pathlib import Path

SHA = re.compile(r"[0-9a-f]{40}\Z")
SOURCES = (
    ("corpus", "the-static-collective/corpus-os", "warranted-execution", "reference-only"),
    ("jubilee", "the-static-collective/Jubilee-Engine-VM", "act-preservation", "reference-only"),
    ("workbench", "the-static-collective/static-workbench", "local-interface", "existing-genesis-house-only"),
)
HANDOFFS = (
    ("corpus", "jubilee", "candidate-particular-evidence", "explicit-human-acceptance"),
    ("jubilee", "workbench", "verified-receipt-view", "display-only"),
)


def exact_keys(obj, keys, path):
    if not isinstance(obj, dict) or set(obj) != set(keys):
        raise ValueError(f"{path}: unexpected/missing keys")


def validate(value):
    exact_keys(value, ("schema", "status", "genesis", "sources", "handoffs", "deployment", "evidence"), "root")
    if value["schema"] != "static-os.triad/v0" or value["status"] != "contract-only":
        raise ValueError("contract-only schema/status required")
    genesis = value["genesis"]
    exact_keys(genesis, ("branch", "bootGate", "isoInclusion"), "genesis")
    if genesis != {"branch": "genesis-001-live-iso", "bootGate": "unverified", "isoInclusion": False}:
        raise ValueError("no boot claim or image inclusion")
    sources = value["sources"]
    if not isinstance(sources, list) or len(sources) != len(SOURCES):
        raise ValueError("exact source inventory required")
    for index, (source, expected) in enumerate(zip(sources, SOURCES)):
        exact_keys(source, ("id", "repository", "commit", "role", "integration"), f"sources[{index}]")
        observed = tuple(source[k] for k in ("id", "repository", "role", "integration"))
        if observed != expected or not isinstance(source["commit"], str) or not SHA.fullmatch(source["commit"]):
            raise ValueError("source owner, role, mode or pinned SHA mismatch")
    if sources[2]["commit"] != "25efe8487efaf4af003cb887a8f0072ffcb77c9e":
        raise ValueError("must preserve existing GENESIS-001 HOUSE pin")
    handoffs = value["handoffs"]
    if not isinstance(handoffs, list) or len(handoffs) != len(HANDOFFS):
        raise ValueError("exact evidence-only handoffs required")
    for index, (handoff, expected) in enumerate(zip(handoffs, HANDOFFS)):
        exact_keys(handoff, ("from", "to", "kind", "authority", "review", "implementation"), f"handoffs[{index}]")
        observed = tuple(handoff[k] for k in ("from", "to", "kind", "review"))
        if observed != expected or handoff["authority"] != "evidence-only" or handoff["implementation"] != "not-implemented":
            raise ValueError("handoff may not transfer authority or claim implementation")
    deployment = value["deployment"]
    flags = ("autoStartNewServices", "allowHostEffects", "allowNetworkListeners", "allowOsMutation", "allowAutomaticPromotion")
    exact_keys(deployment, flags, "deployment")
    if any(deployment[flag] is not False for flag in flags):
        raise ValueError("no new services, effects, listeners, OS mutation or automatic promotion")
    evidence = value["evidence"]
    exact_keys(evidence, ("integration", "isoBuild", "vmBoot", "offlineHouse"), "evidence")
    if any(item != "unverified" for item in evidence.values()):
        raise ValueError("no unearned integration or boot claim")
    return value


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: validate-triad.py PATH", file=sys.stderr)
        return 2
    try:
        validate(json.loads(Path(args[0]).read_text(encoding="utf-8")))
    except (OSError, ValueError, TypeError, KeyError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    print("VALID TRIAD-001 contract-only; no runtime or boot gate asserted")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
