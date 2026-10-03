#!/usr/bin/env python3
"""Navigation braid over a verified navigation-history spine.

A braid records multiple lawful descendants from one admitted parent without
rewriting the parent spine or recursively embedding it in each child.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

history = _load("static_os_navigation_history", "scripts/navigation_history.py")
dogram_nav = _load("static_os_dogram_nav", "scripts/dogram_nav.py")

BRANCH_SCHEMA = "static.navigation-branch-capsule/v0"
BRANCH_SET_SCHEMA = "static.navigation-branch-set/v0"
BRAID_SCHEMA = "static.navigation-braid-ledger/v0"

BRANCH_KEYS = {
    "schema",
    "branch_id",
    "parent_cycle_digest",
    "root_cycle_digest",
    "from_heading",
    "admitted_heading",
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


def _verified_parent(base_history):
    result = history.verify_history(base_history)
    if result.get("status") != "complete":
        raise ValueError(f"base history is not complete: {result.get('reason')}")
    parent_digest = base_history.get("head_cycle_digest")
    if not isinstance(parent_digest, str) or len(parent_digest) != 64:
        raise ValueError("base history needs an admitted head cycle")
    parent = base_history["cycles"].get(parent_digest)
    if not isinstance(parent, dict):
        raise ValueError("base history head cycle missing")
    if canonical_digest(parent) != parent_digest:
        raise ValueError("base history head digest mismatch")
    root_digest = (
        parent_digest
        if parent["cycle_index"] == 0
        else parent["root_cycle_digest"]
    )
    if not isinstance(root_digest, str) or len(root_digest) != 64:
        raise ValueError("base history root digest missing")
    return parent_digest, root_digest, parent


def make_branch_capsule(
    base_history,
    branch_id,
    trace,
    transition,
    reorientation,
    admission,
):
    if not isinstance(branch_id, str) or not branch_id:
        raise ValueError("branch id missing")

    parent_digest, root_digest, parent = _verified_parent(base_history)

    trace_result = dogram_nav.verify_trace(trace)
    if trace_result.get("status") != "complete":
        raise ValueError(f"branch trace is not complete: {trace_result.get('reason')}")
    dogram_nav.validate_transition(transition)
    history.validate_reorientation(reorientation, transition)
    history.validate_admission(admission, reorientation)

    if canonical_digest(trace) != transition["trace_ledger_sha256"]:
        raise ValueError("branch transition does not address supplied trace")
    if transition["from_heading"] != parent["admitted_heading"]:
        raise ValueError("branch does not descend from admitted parent heading")
    if reorientation["from_heading"] != parent["admitted_heading"]:
        raise ValueError("branch reorientation origin mismatch")

    capsule = {
        "schema": BRANCH_SCHEMA,
        "branch_id": branch_id,
        "parent_cycle_digest": parent_digest,
        "root_cycle_digest": root_digest,
        "from_heading": parent["admitted_heading"],
        "admitted_heading": admission["heading"],
        "trace_ledger_sha256": canonical_digest(trace),
        "transition_sha256": canonical_digest(transition),
        "reorientation_sha256": canonical_digest(reorientation),
        "admission_sha256": canonical_digest(admission),
    }
    if set(capsule) != BRANCH_KEYS:
        raise ValueError("branch capsule shape drifted")
    return capsule


def make_branch_set(capsules):
    if not isinstance(capsules, list) or len(capsules) < 2:
        raise ValueError("navigation braid requires at least two branches")

    for capsule in capsules:
        if not isinstance(capsule, dict) or capsule.get("schema") != BRANCH_SCHEMA:
            raise ValueError("invalid branch capsule")
        if set(capsule) != BRANCH_KEYS:
            raise ValueError("branch capsule shape mismatch")

    branch_ids = [c["branch_id"] for c in capsules]
    if len(branch_ids) != len(set(branch_ids)):
        raise ValueError("duplicate branch id")

    parent_digests = {c["parent_cycle_digest"] for c in capsules}
    if len(parent_digests) != 1:
        raise ValueError("branches do not share one parent")

    root_digests = {c["root_cycle_digest"] for c in capsules}
    if len(root_digests) != 1:
        raise ValueError("branches do not share one root history")

    headings = [c["admitted_heading"] for c in capsules]
    if len(headings) != len(set(headings)):
        raise ValueError("branch headings collapsed")

    descriptors = [
        {
            "branch_id": capsule["branch_id"],
            "branch_digest": canonical_digest(capsule),
            "admitted_heading": capsule["admitted_heading"],
        }
        for capsule in capsules
    ]
    descriptors.sort(key=lambda item: item["branch_digest"])

    return {
        "schema": BRANCH_SET_SCHEMA,
        "parent_cycle_digest": next(iter(parent_digests)),
        "root_cycle_digest": next(iter(root_digests)),
        "branches": descriptors,
    }


def build_braid(base_history, branch_bundles):
    parent_digest, root_digest, _ = _verified_parent(base_history)
    if not isinstance(branch_bundles, list) or len(branch_bundles) < 2:
        raise ValueError("navigation braid requires at least two branch bundles")

    branches = {}
    traces = {}
    transitions = {}
    reorientations = {}
    admissions = {}
    capsules = []

    for bundle in branch_bundles:
        if not isinstance(bundle, dict):
            raise ValueError("branch bundle must be a mapping")
        required = {
            "branch_id", "trace", "transition", "reorientation", "admission"
        }
        if set(bundle) != required:
            raise ValueError("branch bundle shape mismatch")

        capsule = make_branch_capsule(
            base_history,
            bundle["branch_id"],
            bundle["trace"],
            bundle["transition"],
            bundle["reorientation"],
            bundle["admission"],
        )
        branch_digest = canonical_digest(capsule)
        if branch_digest in branches:
            raise ValueError("duplicate branch capsule")
        branches[branch_digest] = copy.deepcopy(capsule)
        traces[capsule["trace_ledger_sha256"]] = copy.deepcopy(bundle["trace"])
        transitions[capsule["transition_sha256"]] = copy.deepcopy(bundle["transition"])
        reorientations[capsule["reorientation_sha256"]] = copy.deepcopy(bundle["reorientation"])
        admissions[capsule["admission_sha256"]] = copy.deepcopy(bundle["admission"])
        capsules.append(capsule)

    branch_set = make_branch_set(capsules)
    ledger = {
        "schema": BRAID_SCHEMA,
        "base_history_sha256": canonical_digest(base_history),
        "parent_cycle_digest": parent_digest,
        "root_cycle_digest": root_digest,
        "branch_set_sha256": canonical_digest(branch_set),
        "branches": branches,
        "traces": traces,
        "transitions": transitions,
        "reorientations": reorientations,
        "admissions": admissions,
        "claim_limit": (
            "This braid receipts multiple admitted navigation descendants from one "
            "verified parent. It does not rank branches, merge them, or establish "
            "that either heading is correct."
        ),
    }
    result = verify_braid(base_history, ledger, branch_set)
    if result.get("status") != "complete":
        raise ValueError(f"new braid did not verify complete: {result.get('reason')}")
    return ledger, branch_set


def _incomplete(reason, verified):
    return {"status": "incomplete", "reason": reason, "verified_branches": verified}


def _invalid(reason, verified):
    return {"status": "invalid", "reason": reason, "verified_branches": verified}


def verify_braid(base_history, ledger, branch_set):
    base_result = history.verify_history(base_history)
    if base_result.get("status") == "incomplete":
        return _incomplete("base_history_incomplete", 0)
    if base_result.get("status") != "complete":
        return _invalid("base_history_invalid", 0)

    if not isinstance(ledger, dict) or ledger.get("schema") != BRAID_SCHEMA:
        return _invalid("braid_ledger_shape", 0)
    if canonical_digest(base_history) != ledger.get("base_history_sha256"):
        return _invalid("base_history_digest_mismatch", 0)

    try:
        parent_digest, root_digest, parent = _verified_parent(base_history)
    except ValueError:
        return _invalid("base_parent_invalid", 0)

    if ledger.get("parent_cycle_digest") != parent_digest:
        return _invalid("parent_cycle_digest_mismatch", 0)
    if ledger.get("root_cycle_digest") != root_digest:
        return _invalid("root_cycle_digest_mismatch", 0)

    if not isinstance(branch_set, dict) or branch_set.get("schema") != BRANCH_SET_SCHEMA:
        return _invalid("branch_set_shape", 0)
    if canonical_digest(branch_set) != ledger.get("branch_set_sha256"):
        return _invalid("branch_set_digest_mismatch", 0)
    if branch_set.get("parent_cycle_digest") != parent_digest:
        return _invalid("branch_set_parent_mismatch", 0)
    if branch_set.get("root_cycle_digest") != root_digest:
        return _invalid("branch_set_root_mismatch", 0)

    descriptors = branch_set.get("branches")
    if not isinstance(descriptors, list) or len(descriptors) < 2:
        return _invalid("branch_plurality_missing", 0)

    descriptor_ids = [d.get("branch_id") for d in descriptors if isinstance(d, dict)]
    descriptor_headings = [d.get("admitted_heading") for d in descriptors if isinstance(d, dict)]
    if len(descriptor_ids) != len(descriptors):
        return _invalid("branch_descriptor_shape", 0)
    if len(descriptor_ids) != len(set(descriptor_ids)):
        return _invalid("duplicate_branch_id", 0)
    if len(descriptor_headings) != len(set(descriptor_headings)):
        return _invalid("branch_heading_collapse", 0)

    expected_order = sorted(descriptors, key=lambda item: item.get("branch_digest", ""))
    if descriptors != expected_order:
        return _invalid("branch_set_not_canonical", 0)

    verified = 0
    for descriptor in descriptors:
        branch_digest = descriptor.get("branch_digest")
        capsule = ledger.get("branches", {}).get(branch_digest)
        if capsule is None:
            return _incomplete("missing_branch_capsule", verified)
        if not isinstance(capsule, dict):
            return _invalid("branch_capsule_not_mapping", verified)
        if canonical_digest(capsule) != branch_digest:
            return _invalid("branch_capsule_digest_mismatch", verified)
        if set(capsule) != BRANCH_KEYS or capsule.get("schema") != BRANCH_SCHEMA:
            return _invalid("branch_capsule_shape", verified)

        if capsule["branch_id"] != descriptor["branch_id"]:
            return _invalid("branch_id_mismatch", verified)
        if capsule["admitted_heading"] != descriptor["admitted_heading"]:
            return _invalid("branch_heading_mismatch", verified)
        if capsule["parent_cycle_digest"] != parent_digest:
            return _invalid("branch_parent_mismatch", verified)
        if capsule["root_cycle_digest"] != root_digest:
            return _invalid("branch_root_mismatch", verified)
        if capsule["from_heading"] != parent["admitted_heading"]:
            return _invalid("branch_origin_heading_mismatch", verified)

        resolved = {}
        for field, bucket_name in (
            ("trace_ledger_sha256", "traces"),
            ("transition_sha256", "transitions"),
            ("reorientation_sha256", "reorientations"),
            ("admission_sha256", "admissions"),
        ):
            digest = capsule[field]
            value = ledger.get(bucket_name, {}).get(digest)
            if value is None:
                return _incomplete(f"missing_{bucket_name[:-1]}", verified)
            if canonical_digest(value) != digest:
                return _invalid(f"{bucket_name[:-1]}_digest_mismatch", verified)
            resolved[bucket_name] = value

        trace_result = dogram_nav.verify_trace(resolved["traces"])
        if trace_result.get("status") == "incomplete":
            return _incomplete("branch_trace_incomplete", verified)
        if trace_result.get("status") != "complete":
            return _invalid("branch_trace_invalid", verified)

        try:
            dogram_nav.validate_transition(resolved["transitions"])
            history.validate_reorientation(
                resolved["reorientations"], resolved["transitions"]
            )
            history.validate_admission(
                resolved["admissions"], resolved["reorientations"]
            )
        except ValueError as error:
            return _invalid(str(error).replace(" ", "_"), verified)

        if resolved["transitions"]["from_heading"] != parent["admitted_heading"]:
            return _invalid("branch_transition_parent_mismatch", verified)
        if resolved["admissions"]["heading"] != capsule["admitted_heading"]:
            return _invalid("branch_admission_heading_mismatch", verified)

        verified += 1

    if set(ledger.get("branches", {})) != {
        d["branch_digest"] for d in descriptors
    }:
        return _invalid("undeclared_branch_present", verified)

    return {
        "status": "complete",
        "reason": None,
        "verified_branches": verified,
        "parent_cycle_digest": parent_digest,
        "root_cycle_digest": root_digest,
        "parent_heading": parent["admitted_heading"],
        "branch_headings": [d["admitted_heading"] for d in descriptors],
        "branch_ids": [d["branch_id"] for d in descriptors],
        "branch_capsule_key_counts": [
            len(ledger["branches"][d["branch_digest"]]) for d in descriptors
        ],
        "base_history_sha256": ledger["base_history_sha256"],
        "braid_ledger_sha256": canonical_digest(ledger),
    }


def inspect(base_history, ledger, branch_set):
    result = verify_braid(base_history, ledger, branch_set)
    return {
        "schema": "static.navigation-braid-inspection/v0",
        **result,
        "base_history_unchanged": (
            canonical_digest(base_history) == ledger.get("base_history_sha256")
        ),
        "local_branches_fixed_shape": (
            len(set(result.get("branch_capsule_key_counts", []))) <= 1
            if result.get("status") == "complete" else None
        ),
        "branch_histories_recursively_embedded": False,
        "branch_ranking_claimed": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Navigation braid verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("base_history")
    verify.add_argument("braid_ledger")
    verify.add_argument("branch_set")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("base_history")
    inspect_cmd.add_argument("braid_ledger")
    inspect_cmd.add_argument("branch_set")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "verify":
            _write_json(
                verify_braid(
                    _read_json(args.base_history),
                    _read_json(args.braid_ledger),
                    _read_json(args.branch_set),
                ),
                None,
            )
            return 0
        if args.command == "inspect":
            _write_json(
                inspect(
                    _read_json(args.base_history),
                    _read_json(args.braid_ledger),
                    _read_json(args.branch_set),
                ),
                None,
            )
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
