#!/usr/bin/env python3
"""Two-cycle navigation history over bounded Dogram/NAV capsules.

The shared ledger stores the growing past. Each cycle capsule remains fixed-shape
and links to trace, transition, reorientation, and explicit local admission by
content address. The runtime does not admit headings on behalf of a human/local
authority; it only verifies supplied admissions.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOGRAM_SPEC = importlib.util.spec_from_file_location(
    "static_os_dogram_nav", ROOT / "scripts" / "dogram_nav.py"
)
dogram_nav = importlib.util.module_from_spec(DOGRAM_SPEC)
DOGRAM_SPEC.loader.exec_module(dogram_nav)

HISTORY_SCHEMA = "static.navigation-history-ledger/v0"
CYCLE_SCHEMA = "static.navigation-cycle-capsule/v0"
ADMISSION_SCHEMA = "static.nav-heading-admission/v0"
REORIENTATION_SCHEMA = "static.nav-reorientation/v0"

CYCLE_KEYS = {
    "schema",
    "cycle_index",
    "from_heading",
    "admitted_heading",
    "root_cycle_digest",
    "parent_cycle_digest",
    "trace_ledger_sha256",
    "transition_sha256",
    "reorientation_sha256",
    "admission_sha256",
}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def canonical_digest(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _write_json(value, path: str | Path | None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def make_ledger():
    return {
        "schema": HISTORY_SCHEMA,
        "head_cycle_digest": None,
        "cycles": {},
        "traces": {},
        "transitions": {},
        "reorientations": {},
        "admissions": {},
        "claim_limit": (
            "This ledger receipts declared navigation history. Content-addressed "
            "continuity does not prove external causality, correctness, or authority."
        ),
    }


def validate_admission(admission, reorientation):
    if not isinstance(admission, dict) or admission.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("unsupported NAV admission schema")
    if admission.get("status") != "admitted":
        raise ValueError("NAV admission must be explicit")
    if not admission.get("admitted_by"):
        raise ValueError("NAV admission actor missing")
    if admission.get("heading") != reorientation.get("proposed_heading"):
        raise ValueError("admitted heading does not match proposal")
    transition_digest = reorientation.get("transition_sha256")
    if admission.get("transition_sha256") != transition_digest:
        raise ValueError("admission transition digest mismatch")
    reorientation_digest = canonical_digest(reorientation)
    if admission.get("reorientation_sha256") != reorientation_digest:
        raise ValueError("admission reorientation digest mismatch")
    if not admission.get("claim_limit"):
        raise ValueError("admission claim limit missing")
    return admission


def validate_reorientation(reorientation, transition):
    if not isinstance(reorientation, dict) or reorientation.get("schema") != REORIENTATION_SCHEMA:
        raise ValueError("unsupported NAV reorientation schema")
    if reorientation.get("status") != "proposed":
        raise ValueError("NAV reorientation must remain proposed")
    if reorientation.get("from_heading") != transition.get("from_heading"):
        raise ValueError("reorientation origin mismatch")
    if reorientation.get("proposed_heading") != transition.get("to_heading"):
        raise ValueError("reorientation destination mismatch")
    if reorientation.get("transition_sha256") != canonical_digest(transition):
        raise ValueError("reorientation transition digest mismatch")
    if reorientation.get("trace_ledger_sha256") != transition.get("trace_ledger_sha256"):
        raise ValueError("reorientation trace digest mismatch")
    return reorientation


def make_cycle_capsule(
    ledger,
    trace,
    transition,
    reorientation,
    admission,
):
    trace_result = dogram_nav.verify_trace(trace)
    if trace_result.get("status") != "complete":
        raise ValueError(f"trace is not complete: {trace_result.get('reason')}")
    dogram_nav.validate_transition(transition)
    validate_reorientation(reorientation, transition)
    validate_admission(admission, reorientation)

    if canonical_digest(trace) != transition["trace_ledger_sha256"]:
        raise ValueError("transition does not address supplied trace")

    parent_digest = ledger.get("head_cycle_digest")
    cycles = ledger.get("cycles")
    if not isinstance(cycles, dict):
        raise ValueError("history cycles bucket missing")

    if parent_digest is None:
        cycle_index = 0
        root_cycle_digest = None
    else:
        parent = cycles.get(parent_digest)
        if parent is None:
            raise ValueError("history head cycle missing")
        if canonical_digest(parent) != parent_digest:
            raise ValueError("history head cycle digest mismatch")
        cycle_index = parent["cycle_index"] + 1
        root_cycle_digest = (
            parent_digest if parent["cycle_index"] == 0
            else parent["root_cycle_digest"]
        )
        if transition["from_heading"] != parent["admitted_heading"]:
            raise ValueError("next cycle does not begin at admitted prior heading")

    capsule = {
        "schema": CYCLE_SCHEMA,
        "cycle_index": cycle_index,
        "from_heading": transition["from_heading"],
        "admitted_heading": admission["heading"],
        "root_cycle_digest": root_cycle_digest,
        "parent_cycle_digest": parent_digest,
        "trace_ledger_sha256": canonical_digest(trace),
        "transition_sha256": canonical_digest(transition),
        "reorientation_sha256": canonical_digest(reorientation),
        "admission_sha256": canonical_digest(admission),
    }
    if set(capsule) != CYCLE_KEYS:
        raise ValueError("cycle capsule shape drifted")
    return capsule


def append_cycle(ledger, trace, transition, reorientation, admission):
    if not isinstance(ledger, dict) or ledger.get("schema") != HISTORY_SCHEMA:
        raise ValueError("unsupported navigation history ledger")
    updated = copy.deepcopy(ledger)
    capsule = make_cycle_capsule(updated, trace, transition, reorientation, admission)

    buckets = {
        "traces": (canonical_digest(trace), trace),
        "transitions": (canonical_digest(transition), transition),
        "reorientations": (canonical_digest(reorientation), reorientation),
        "admissions": (canonical_digest(admission), admission),
    }
    for bucket_name, (digest, value) in buckets.items():
        bucket = updated.get(bucket_name)
        if not isinstance(bucket, dict):
            raise ValueError(f"history bucket missing: {bucket_name}")
        bucket[digest] = copy.deepcopy(value)

    cycle_digest = canonical_digest(capsule)
    updated["cycles"][cycle_digest] = copy.deepcopy(capsule)
    updated["head_cycle_digest"] = cycle_digest

    result = verify_history(updated)
    if result["status"] != "complete":
        raise ValueError(f"updated history did not verify complete: {result['reason']}")
    return updated


def _incomplete(reason, cycle_indices):
    return {"status": "incomplete", "reason": reason, "cycle_indices": cycle_indices}


def _invalid(reason, cycle_indices):
    return {"status": "invalid", "reason": reason, "cycle_indices": cycle_indices}


def verify_history(ledger):
    if not isinstance(ledger, dict) or ledger.get("schema") != HISTORY_SCHEMA:
        return _invalid("ledger_shape", [])
    for bucket_name in ("cycles", "traces", "transitions", "reorientations", "admissions"):
        if not isinstance(ledger.get(bucket_name), dict):
            return _invalid(f"{bucket_name}_bucket_shape", [])
    if not ledger.get("claim_limit"):
        return _invalid("claim_limit_missing", [])

    head = ledger.get("head_cycle_digest")
    if head is None:
        return {
            "status": "complete",
            "reason": None,
            "cycle_indices": [],
            "head_cycle_digest": None,
        }
    if not isinstance(head, str) or len(head) != 64:
        return _invalid("head_digest_shape", [])

    seen = set()
    chain = []
    current_digest = head

    while current_digest is not None:
        if current_digest in seen:
            return _invalid("cycle_detected", [c["cycle_index"] for c in chain])
        seen.add(current_digest)

        capsule = ledger["cycles"].get(current_digest)
        if capsule is None:
            return _incomplete("missing_cycle_capsule", [c["cycle_index"] for c in chain])
        if not isinstance(capsule, dict):
            return _invalid("cycle_capsule_not_mapping", [c["cycle_index"] for c in chain])
        if canonical_digest(capsule) != current_digest:
            return _invalid("cycle_capsule_digest_mismatch", [c["cycle_index"] for c in chain])
        if set(capsule) != CYCLE_KEYS or capsule.get("schema") != CYCLE_SCHEMA:
            return _invalid("cycle_capsule_shape", [c["cycle_index"] for c in chain])

        for field, bucket_name in (
            ("trace_ledger_sha256", "traces"),
            ("transition_sha256", "transitions"),
            ("reorientation_sha256", "reorientations"),
            ("admission_sha256", "admissions"),
        ):
            digest = capsule.get(field)
            value = ledger[bucket_name].get(digest)
            if value is None:
                return _incomplete(f"missing_{bucket_name[:-1]}", [c["cycle_index"] for c in chain])
            if canonical_digest(value) != digest:
                return _invalid(f"{bucket_name[:-1]}_digest_mismatch", [c["cycle_index"] for c in chain])

        trace = ledger["traces"][capsule["trace_ledger_sha256"]]
        transition = ledger["transitions"][capsule["transition_sha256"]]
        reorientation = ledger["reorientations"][capsule["reorientation_sha256"]]
        admission = ledger["admissions"][capsule["admission_sha256"]]

        trace_result = dogram_nav.verify_trace(trace)
        if trace_result.get("status") == "incomplete":
            return _incomplete("trace_incomplete", [c["cycle_index"] for c in chain])
        if trace_result.get("status") != "complete":
            return _invalid("trace_invalid", [c["cycle_index"] for c in chain])

        try:
            dogram_nav.validate_transition(transition)
            validate_reorientation(reorientation, transition)
            validate_admission(admission, reorientation)
        except ValueError as error:
            return _invalid(str(error).replace(" ", "_"), [c["cycle_index"] for c in chain])

        if capsule["from_heading"] != transition["from_heading"]:
            return _invalid("capsule_origin_mismatch", [c["cycle_index"] for c in chain])
        if capsule["admitted_heading"] != admission["heading"]:
            return _invalid("capsule_destination_mismatch", [c["cycle_index"] for c in chain])

        chain.append(capsule)
        current_digest = capsule["parent_cycle_digest"]

    ordered = list(reversed(chain))
    expected_indices = list(range(len(ordered)))
    actual_indices = [c["cycle_index"] for c in ordered]
    if actual_indices != expected_indices:
        return _invalid("cycle_index_gap", actual_indices)

    for index, capsule in enumerate(ordered):
        if index == 0:
            if capsule["parent_cycle_digest"] is not None:
                return _invalid("root_has_parent", actual_indices)
            if capsule["root_cycle_digest"] is not None:
                return _invalid("root_has_root_link", actual_indices)
        else:
            parent_digest = canonical_digest(ordered[index - 1])
            if capsule["parent_cycle_digest"] != parent_digest:
                return _invalid("parent_cycle_link_mismatch", actual_indices)
            expected_root = canonical_digest(ordered[0])
            if capsule["root_cycle_digest"] != expected_root:
                return _invalid("root_cycle_link_mismatch", actual_indices)
            if capsule["from_heading"] != ordered[index - 1]["admitted_heading"]:
                return _invalid("heading_continuity_mismatch", actual_indices)

    return {
        "status": "complete",
        "reason": None,
        "cycle_indices": actual_indices,
        "head_cycle_digest": head,
        "root_cycle_digest": canonical_digest(ordered[0]) if ordered else None,
        "heading_path": (
            [ordered[0]["from_heading"]] + [c["admitted_heading"] for c in ordered]
            if ordered else []
        ),
        "capsule_key_counts": [len(c) for c in ordered],
        "shared_ledger_sha256": canonical_digest(ledger),
    }


def inspect(ledger):
    result = verify_history(ledger)
    return {
        "schema": "static.navigation-history-inspection/v0",
        **result,
        "local_capsules_fixed_shape": (
            len(set(result.get("capsule_key_counts", []))) <= 1
            if result.get("status") == "complete" else None
        ),
        "history_recursively_embedded": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Two-cycle navigation history")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("new")

    append = sub.add_parser("append")
    append.add_argument("ledger")
    append.add_argument("trace")
    append.add_argument("transition")
    append.add_argument("reorientation")
    append.add_argument("admission")
    append.add_argument("-o", "--out")

    verify = sub.add_parser("verify")
    verify.add_argument("ledger")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("ledger")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "new":
            _write_json(make_ledger(), None)
            return 0
        if args.command == "append":
            _write_json(
                append_cycle(
                    _read_json(args.ledger),
                    _read_json(args.trace),
                    _read_json(args.transition),
                    _read_json(args.reorientation),
                    _read_json(args.admission),
                ),
                args.out,
            )
            return 0
        if args.command == "verify":
            _write_json(verify_history(_read_json(args.ledger)), None)
            return 0
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.ledger)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
