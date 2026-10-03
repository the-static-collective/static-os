#!/usr/bin/env python3
"""Typed navigation weave over branch and branch-continuation relations.

The weave preserves relation kind while composing one continued branch with one
still-open sibling branch. It does not rank, merge, or activate the resulting
proposal.
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


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


history = _load("static_os_navigation_history", "scripts/navigation_history.py")
braid = _load("static_os_navigation_braid", "scripts/navigation_braid.py")
dogram_nav = _load("static_os_dogram_nav", "scripts/dogram_nav.py")

CONTINUATION_SCHEMA = "static.navigation-branch-continuation/v0"
PARENT_SET_SCHEMA = "static.navigation-weave-parent-set/v0"
WEAVE_CAPSULE_SCHEMA = "static.navigation-weave-capsule/v0"
WEAVE_LEDGER_SCHEMA = "static.navigation-weave-ledger/v0"

CONTINUATION_KEYS = {
    "schema",
    "continuation_id",
    "parent_branch_digest",
    "root_cycle_digest",
    "from_heading",
    "admitted_heading",
    "trace_ledger_sha256",
    "transition_sha256",
    "reorientation_sha256",
    "admission_sha256",
}
WEAVE_KEYS = {
    "schema",
    "weave_id",
    "parent_set_sha256",
    "root_cycle_digest",
    "proposed_heading",
    "relation_kinds",
    "status",
    "claim_limit",
}
RELATION_KINDS = {"branch_continuation", "open_branch"}


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


def _verify_braid(base_history, braid_ledger, branch_set):
    result = braid.verify_braid(base_history, braid_ledger, branch_set)
    if result.get("status") != "complete":
        raise ValueError(f"base braid is not complete: {result.get('reason')}")
    return result


def make_continuation(
    base_history,
    braid_ledger,
    branch_set,
    parent_branch_digest,
    continuation_id,
    trace,
    transition,
    reorientation,
    admission,
):
    _verify_braid(base_history, braid_ledger, branch_set)

    parent = braid_ledger.get("branches", {}).get(parent_branch_digest)
    if parent is None:
        raise ValueError("continuation parent branch missing")
    if canonical_digest(parent) != parent_branch_digest:
        raise ValueError("continuation parent branch digest mismatch")
    if parent.get("schema") != braid.BRANCH_SCHEMA:
        raise ValueError("continuation parent is not a branch capsule")

    trace_result = dogram_nav.verify_trace(trace)
    if trace_result.get("status") != "complete":
        raise ValueError(f"continuation trace is not complete: {trace_result.get('reason')}")
    dogram_nav.validate_transition(transition)
    history.validate_reorientation(reorientation, transition)
    history.validate_admission(admission, reorientation)

    if canonical_digest(trace) != transition["trace_ledger_sha256"]:
        raise ValueError("continuation transition does not address supplied trace")
    if transition["from_heading"] != parent["admitted_heading"]:
        raise ValueError("continuation does not begin at parent branch heading")
    if reorientation["from_heading"] != parent["admitted_heading"]:
        raise ValueError("continuation reorientation origin mismatch")
    if not isinstance(continuation_id, str) or not continuation_id:
        raise ValueError("continuation id missing")

    capsule = {
        "schema": CONTINUATION_SCHEMA,
        "continuation_id": continuation_id,
        "parent_branch_digest": parent_branch_digest,
        "root_cycle_digest": parent["root_cycle_digest"],
        "from_heading": parent["admitted_heading"],
        "admitted_heading": admission["heading"],
        "trace_ledger_sha256": canonical_digest(trace),
        "transition_sha256": canonical_digest(transition),
        "reorientation_sha256": canonical_digest(reorientation),
        "admission_sha256": canonical_digest(admission),
    }
    if set(capsule) != CONTINUATION_KEYS:
        raise ValueError("continuation capsule shape drifted")
    return capsule


def verify_continuation(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    continuation_digest,
):
    braid_result = braid.verify_braid(base_history, braid_ledger, branch_set)
    if braid_result.get("status") == "incomplete":
        return {"status": "incomplete", "reason": "base_braid_incomplete"}
    if braid_result.get("status") != "complete":
        return {"status": "invalid", "reason": "base_braid_invalid"}

    continuation = weave_ledger.get("continuations", {}).get(continuation_digest)
    if continuation is None:
        if continuation_digest in braid_ledger.get("branches", {}):
            return {"status": "invalid", "reason": "parent_kind_mismatch"}
        return {"status": "incomplete", "reason": "missing_continuation"}
    if not isinstance(continuation, dict):
        return {"status": "invalid", "reason": "continuation_not_mapping"}
    if canonical_digest(continuation) != continuation_digest:
        return {"status": "invalid", "reason": "continuation_digest_mismatch"}
    if (
        continuation.get("schema") != CONTINUATION_SCHEMA
        or set(continuation) != CONTINUATION_KEYS
    ):
        return {"status": "invalid", "reason": "continuation_shape"}

    parent_digest = continuation.get("parent_branch_digest")
    parent = braid_ledger.get("branches", {}).get(parent_digest)
    if parent is None:
        return {"status": "incomplete", "reason": "missing_parent_branch"}
    if canonical_digest(parent) != parent_digest:
        return {"status": "invalid", "reason": "parent_branch_digest_mismatch"}
    if continuation.get("root_cycle_digest") != parent.get("root_cycle_digest"):
        return {"status": "invalid", "reason": "continuation_root_mismatch"}
    if continuation.get("from_heading") != parent.get("admitted_heading"):
        return {"status": "invalid", "reason": "continuation_origin_mismatch"}

    resolved = {}
    for field, bucket_name in (
        ("trace_ledger_sha256", "traces"),
        ("transition_sha256", "transitions"),
        ("reorientation_sha256", "reorientations"),
        ("admission_sha256", "admissions"),
    ):
        digest = continuation.get(field)
        value = weave_ledger.get(bucket_name, {}).get(digest)
        if value is None:
            return {"status": "incomplete", "reason": f"missing_continuation_{bucket_name[:-1]}"}
        if canonical_digest(value) != digest:
            return {"status": "invalid", "reason": f"continuation_{bucket_name[:-1]}_digest_mismatch"}
        resolved[bucket_name] = value

    trace_result = dogram_nav.verify_trace(resolved["traces"])
    if trace_result.get("status") == "incomplete":
        return {"status": "incomplete", "reason": "continuation_trace_incomplete"}
    if trace_result.get("status") != "complete":
        return {"status": "invalid", "reason": "continuation_trace_invalid"}

    try:
        dogram_nav.validate_transition(resolved["transitions"])
        history.validate_reorientation(
            resolved["reorientations"], resolved["transitions"]
        )
        history.validate_admission(
            resolved["admissions"], resolved["reorientations"]
        )
    except ValueError as error:
        return {"status": "invalid", "reason": str(error).replace(" ", "_")}

    if resolved["transitions"]["from_heading"] != parent["admitted_heading"]:
        return {"status": "invalid", "reason": "continuation_transition_parent_mismatch"}
    if resolved["admissions"]["heading"] != continuation["admitted_heading"]:
        return {"status": "invalid", "reason": "continuation_admission_heading_mismatch"}

    return {
        "status": "complete",
        "reason": None,
        "heading": continuation["admitted_heading"],
        "root_cycle_digest": continuation["root_cycle_digest"],
        "parent_branch_digest": parent_digest,
    }


def make_parent_set(continuation, open_branch):
    if (
        not isinstance(continuation, dict)
        or continuation.get("schema") != CONTINUATION_SCHEMA
        or set(continuation) != CONTINUATION_KEYS
    ):
        raise ValueError("invalid continuation parent")
    if (
        not isinstance(open_branch, dict)
        or open_branch.get("schema") != braid.BRANCH_SCHEMA
        or set(open_branch) != braid.BRANCH_KEYS
    ):
        raise ValueError("invalid open branch parent")

    if continuation["parent_branch_digest"] == canonical_digest(open_branch):
        raise ValueError("continued branch cannot also be the open sibling")
    if continuation["root_cycle_digest"] != open_branch["root_cycle_digest"]:
        raise ValueError("weave parents do not share one root")

    parents = [
        {
            "kind": "branch_continuation",
            "head_digest": canonical_digest(continuation),
            "heading": continuation["admitted_heading"],
            "root_cycle_digest": continuation["root_cycle_digest"],
        },
        {
            "kind": "open_branch",
            "head_digest": canonical_digest(open_branch),
            "heading": open_branch["admitted_heading"],
            "root_cycle_digest": open_branch["root_cycle_digest"],
        },
    ]
    parents.sort(key=lambda item: (item["kind"], item["head_digest"]))

    return {
        "schema": PARENT_SET_SCHEMA,
        "root_cycle_digest": continuation["root_cycle_digest"],
        "parents": parents,
    }


def make_weave_capsule(parent_set, proposed_heading):
    if (
        not isinstance(parent_set, dict)
        or parent_set.get("schema") != PARENT_SET_SCHEMA
    ):
        raise ValueError("invalid weave parent set")
    parents = parent_set.get("parents")
    if not isinstance(parents, list) or len(parents) != 2:
        raise ValueError("first weave requires exactly two typed parents")

    kinds = sorted({parent.get("kind") for parent in parents})
    if set(kinds) != RELATION_KINDS:
        raise ValueError("weave must preserve both relation kinds")
    if not isinstance(proposed_heading, str) or not proposed_heading:
        raise ValueError("weave proposed heading missing")

    capsule = {
        "schema": WEAVE_CAPSULE_SCHEMA,
        "weave_id": "navigation-weave-001",
        "parent_set_sha256": canonical_digest(parent_set),
        "root_cycle_digest": parent_set["root_cycle_digest"],
        "proposed_heading": proposed_heading,
        "relation_kinds": kinds,
        "status": "proposed",
        "claim_limit": (
            "This weave proposes a composition across a continued branch and an "
            "open sibling branch. It does not rank, merge, close, or activate either "
            "parent relation, and it does not prove the proposed heading is correct."
        ),
    }
    if set(capsule) != WEAVE_KEYS:
        raise ValueError("weave capsule shape drifted")
    return capsule


def build_weave(
    base_history,
    braid_ledger,
    branch_set,
    continuation_bundle,
    open_branch_digest,
    proposed_heading,
):
    _verify_braid(base_history, braid_ledger, branch_set)

    if not isinstance(continuation_bundle, dict):
        raise ValueError("continuation bundle missing")
    required = {
        "parent_branch_digest",
        "continuation_id",
        "trace",
        "transition",
        "reorientation",
        "admission",
    }
    if set(continuation_bundle) != required:
        raise ValueError("continuation bundle shape mismatch")

    continuation = make_continuation(
        base_history,
        braid_ledger,
        branch_set,
        continuation_bundle["parent_branch_digest"],
        continuation_bundle["continuation_id"],
        continuation_bundle["trace"],
        continuation_bundle["transition"],
        continuation_bundle["reorientation"],
        continuation_bundle["admission"],
    )

    open_branch = braid_ledger.get("branches", {}).get(open_branch_digest)
    if open_branch is None:
        raise ValueError("open branch missing")
    if canonical_digest(open_branch) != open_branch_digest:
        raise ValueError("open branch digest mismatch")

    parent_set = make_parent_set(continuation, open_branch)
    weave_capsule = make_weave_capsule(parent_set, proposed_heading)

    ledger = {
        "schema": WEAVE_LEDGER_SCHEMA,
        "base_history_sha256": canonical_digest(base_history),
        "braid_ledger_sha256": canonical_digest(braid_ledger),
        "branch_set_sha256": canonical_digest(branch_set),
        "parent_set_sha256": canonical_digest(parent_set),
        "weave_capsule_sha256": canonical_digest(weave_capsule),
        "continuations": {
            canonical_digest(continuation): copy.deepcopy(continuation)
        },
        "traces": {
            canonical_digest(continuation_bundle["trace"]): copy.deepcopy(
                continuation_bundle["trace"]
            )
        },
        "transitions": {
            canonical_digest(continuation_bundle["transition"]): copy.deepcopy(
                continuation_bundle["transition"]
            )
        },
        "reorientations": {
            canonical_digest(continuation_bundle["reorientation"]): copy.deepcopy(
                continuation_bundle["reorientation"]
            )
        },
        "admissions": {
            canonical_digest(continuation_bundle["admission"]): copy.deepcopy(
                continuation_bundle["admission"]
            )
        },
        "claim_limit": (
            "This ledger preserves typed navigation parent relations. Typed graph "
            "composition does not establish causal truth, branch superiority, or authority."
        ),
    }

    result = verify_weave(
        base_history,
        braid_ledger,
        branch_set,
        ledger,
        parent_set,
        weave_capsule,
    )
    if result.get("status") != "complete":
        raise ValueError(f"new weave did not verify complete: {result.get('reason')}")
    return ledger, parent_set, weave_capsule


def _incomplete(reason, verified):
    return {"status": "incomplete", "reason": reason, "verified_parents": verified}


def _invalid(reason, verified):
    return {"status": "invalid", "reason": reason, "verified_parents": verified}


def verify_weave(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
):
    braid_result = braid.verify_braid(base_history, braid_ledger, branch_set)
    if braid_result.get("status") == "incomplete":
        return _incomplete("base_braid_incomplete", 0)
    if braid_result.get("status") != "complete":
        return _invalid("base_braid_invalid", 0)

    if not isinstance(weave_ledger, dict) or weave_ledger.get("schema") != WEAVE_LEDGER_SCHEMA:
        return _invalid("weave_ledger_shape", 0)
    if canonical_digest(base_history) != weave_ledger.get("base_history_sha256"):
        return _invalid("base_history_digest_mismatch", 0)
    if canonical_digest(braid_ledger) != weave_ledger.get("braid_ledger_sha256"):
        return _invalid("braid_ledger_digest_mismatch", 0)
    if canonical_digest(branch_set) != weave_ledger.get("branch_set_sha256"):
        return _invalid("branch_set_digest_mismatch", 0)

    if not isinstance(parent_set, dict) or parent_set.get("schema") != PARENT_SET_SCHEMA:
        return _invalid("parent_set_shape", 0)
    if canonical_digest(parent_set) != weave_ledger.get("parent_set_sha256"):
        return _invalid("parent_set_digest_mismatch", 0)

    if (
        not isinstance(weave_capsule, dict)
        or weave_capsule.get("schema") != WEAVE_CAPSULE_SCHEMA
        or set(weave_capsule) != WEAVE_KEYS
    ):
        return _invalid("weave_capsule_shape", 0)
    if canonical_digest(weave_capsule) != weave_ledger.get("weave_capsule_sha256"):
        return _invalid("weave_capsule_digest_mismatch", 0)
    if weave_capsule.get("parent_set_sha256") != canonical_digest(parent_set):
        return _invalid("weave_parent_set_link_mismatch", 0)
    if weave_capsule.get("root_cycle_digest") != parent_set.get("root_cycle_digest"):
        return _invalid("weave_root_mismatch", 0)
    if weave_capsule.get("status") != "proposed":
        return _invalid("weave_status_mismatch", 0)

    parents = parent_set.get("parents")
    if not isinstance(parents, list) or len(parents) != 2:
        return _invalid("typed_parent_plurality", 0)
    expected_order = sorted(parents, key=lambda item: (item.get("kind", ""), item.get("head_digest", "")))
    if parents != expected_order:
        return _invalid("typed_parent_set_not_canonical", 0)

    kinds = [p.get("kind") for p in parents]
    if set(kinds) != RELATION_KINDS or len(kinds) != len(set(kinds)):
        return _invalid("relation_kind_collapse", 0)
    if sorted(weave_capsule.get("relation_kinds", [])) != sorted(RELATION_KINDS):
        return _invalid("weave_relation_kinds_mismatch", 0)

    verified = 0
    continued_parent_branch = None
    open_branch_digest = None

    for descriptor in parents:
        if not isinstance(descriptor, dict) or set(descriptor) != {
            "kind", "head_digest", "heading", "root_cycle_digest"
        }:
            return _invalid("typed_parent_descriptor_shape", verified)
        kind = descriptor["kind"]
        head_digest = descriptor["head_digest"]

        if kind == "branch_continuation":
            result = verify_continuation(
                base_history,
                braid_ledger,
                branch_set,
                weave_ledger,
                head_digest,
            )
            if result["status"] != "complete":
                return (
                    _incomplete(result["reason"], verified)
                    if result["status"] == "incomplete"
                    else _invalid(result["reason"], verified)
                )
            if descriptor["heading"] != result["heading"]:
                return _invalid("continuation_heading_mismatch", verified)
            if descriptor["root_cycle_digest"] != result["root_cycle_digest"]:
                return _invalid("continuation_descriptor_root_mismatch", verified)
            continued_parent_branch = result["parent_branch_digest"]

        elif kind == "open_branch":
            open_branch = braid_ledger.get("branches", {}).get(head_digest)
            if open_branch is None:
                if head_digest in weave_ledger.get("continuations", {}):
                    return _invalid("parent_kind_mismatch", verified)
                return _incomplete("missing_open_branch", verified)
            if canonical_digest(open_branch) != head_digest:
                return _invalid("open_branch_digest_mismatch", verified)
            if open_branch.get("schema") != braid.BRANCH_SCHEMA or set(open_branch) != braid.BRANCH_KEYS:
                return _invalid("open_branch_shape", verified)
            if descriptor["heading"] != open_branch["admitted_heading"]:
                return _invalid("open_branch_heading_mismatch", verified)
            if descriptor["root_cycle_digest"] != open_branch["root_cycle_digest"]:
                return _invalid("open_branch_root_mismatch", verified)
            open_branch_digest = head_digest

        else:
            return _invalid("unsupported_relation_kind", verified)

        verified += 1

    if continued_parent_branch is None or open_branch_digest is None:
        return _invalid("typed_parent_dispatch_incomplete", verified)
    if continued_parent_branch == open_branch_digest:
        return _invalid("open_branch_is_continued_branch", verified)

    if any(
        parent["root_cycle_digest"] != parent_set["root_cycle_digest"]
        for parent in parents
    ):
        return _invalid("root_union_mismatch", verified)

    if set(weave_ledger.get("continuations", {})) != {
        p["head_digest"] for p in parents if p["kind"] == "branch_continuation"
    }:
        return _invalid("undeclared_continuation_present", verified)

    return {
        "status": "complete",
        "reason": None,
        "verified_parents": verified,
        "relation_kinds": kinds,
        "root_cycle_digest": parent_set["root_cycle_digest"],
        "parent_headings": [p["heading"] for p in parents],
        "proposed_heading": weave_capsule["proposed_heading"],
        "continued_parent_branch_digest": continued_parent_branch,
        "open_branch_digest": open_branch_digest,
        "weave_capsule_key_count": len(weave_capsule),
        "weave_ledger_sha256": canonical_digest(weave_ledger),
    }


def inspect(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
):
    result = verify_weave(
        base_history,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
    )
    return {
        "schema": "static.navigation-weave-inspection/v0",
        **result,
        "relation_kinds_preserved": (
            set(result.get("relation_kinds", [])) == RELATION_KINDS
            if result.get("status") == "complete" else None
        ),
        "branch_ranking_claimed": False,
        "branch_merge_claimed": False,
        "weave_activated": False,
        "history_recursively_embedded": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Typed navigation weave verifier")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("base_history")
    verify.add_argument("braid_ledger")
    verify.add_argument("branch_set")
    verify.add_argument("weave_ledger")
    verify.add_argument("parent_set")
    verify.add_argument("weave_capsule")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("base_history")
    inspect_cmd.add_argument("braid_ledger")
    inspect_cmd.add_argument("branch_set")
    inspect_cmd.add_argument("weave_ledger")
    inspect_cmd.add_argument("parent_set")
    inspect_cmd.add_argument("weave_capsule")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        values = [
            _read_json(args.base_history),
            _read_json(args.braid_ledger),
            _read_json(args.branch_set),
            _read_json(args.weave_ledger),
            _read_json(args.parent_set),
            _read_json(args.weave_capsule),
        ]
        if args.command == "verify":
            _write_json(verify_weave(*values), None)
            return 0
        if args.command == "inspect":
            _write_json(inspect(*values), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
