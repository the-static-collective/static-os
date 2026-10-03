#!/usr/bin/env python3
"""Explicit NAV admission of a verified typed navigation weave.

The weave remains a proposal until a local caller explicitly accepts it.
Admission carries typed provenance addresses forward into a bounded generation
capsule; it does not re-rank or merge the parent relations.
"""
from __future__ import annotations

import argparse
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


weave = _load("static_os_navigation_weave", "scripts/navigation_weave.py")

ADMISSION_SCHEMA = "static.nav-weave-admission/v0"
GENERATION_SCHEMA = "static.navigation-weave-generation/v0"
RELATION_KINDS = {"branch_continuation", "open_branch"}

ADMISSION_KEYS = {
    "schema",
    "status",
    "heading",
    "weave_capsule_sha256",
    "parent_set_sha256",
    "weave_ledger_sha256",
    "root_cycle_digest",
    "relation_kinds",
    "admitted_by",
    "claim_limit",
}
GENERATION_KEYS = {
    "schema",
    "generation_id",
    "admitted_heading",
    "admission_sha256",
    "weave_capsule_sha256",
    "parent_set_sha256",
    "weave_ledger_sha256",
    "root_cycle_digest",
    "relation_kinds",
    "status",
    "claim_limit",
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


def make_admission(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
    admitted_by,
    accept_proposal,
):
    result = weave.verify_weave(
        base_history,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
    )
    if result.get("status") != "complete":
        raise ValueError(f"weave is not admissible: {result.get('reason')}")
    if accept_proposal is not True:
        raise ValueError("explicit local acceptance is required")
    if not isinstance(admitted_by, str) or not admitted_by:
        raise ValueError("admission actor missing")
    if weave_capsule.get("status") != "proposed":
        raise ValueError("weave must remain proposed before admission")

    parent_digest = canonical_digest(parent_set)
    capsule_digest = canonical_digest(weave_capsule)
    ledger_digest = canonical_digest(weave_ledger)

    if weave_capsule.get("parent_set_sha256") != parent_digest:
        raise ValueError("weave parent-set link mismatch")
    if weave_ledger.get("parent_set_sha256") != parent_digest:
        raise ValueError("weave ledger parent-set link mismatch")
    if weave_ledger.get("weave_capsule_sha256") != capsule_digest:
        raise ValueError("weave ledger capsule link mismatch")
    if weave_capsule.get("root_cycle_digest") != parent_set.get("root_cycle_digest"):
        raise ValueError("weave root mismatch")

    kinds = sorted(weave_capsule.get("relation_kinds", []))
    if set(kinds) != RELATION_KINDS:
        raise ValueError("typed parent relations not preserved")

    admission = {
        "schema": ADMISSION_SCHEMA,
        "status": "admitted",
        "heading": weave_capsule["proposed_heading"],
        "weave_capsule_sha256": capsule_digest,
        "parent_set_sha256": parent_digest,
        "weave_ledger_sha256": ledger_digest,
        "root_cycle_digest": weave_capsule["root_cycle_digest"],
        "relation_kinds": kinds,
        "admitted_by": admitted_by,
        "claim_limit": (
            "This artifact records explicit local admission of a verified typed-weave "
            "proposal. Admission does not make either parent relation correct, erase "
            "the still-open branch, rank the parents, or convert relation type into causality."
        ),
    }
    return validate_admission(admission)


def validate_admission(admission):
    if not isinstance(admission, dict) or admission.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("unsupported typed-weave admission schema")
    if set(admission) != ADMISSION_KEYS:
        raise ValueError("typed-weave admission shape drifted")
    if admission.get("status") != "admitted":
        raise ValueError("typed-weave admission must be admitted")
    for key in ("heading", "admitted_by", "claim_limit"):
        if not isinstance(admission.get(key), str) or not admission[key]:
            raise ValueError(f"typed-weave admission missing: {key}")
    for key in (
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        value = admission.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"typed-weave admission digest missing: {key}")
    kinds = admission.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("typed-weave admission relation kinds invalid")
    return admission


def make_generation(
    admission,
    weave_ledger,
    parent_set,
    weave_capsule,
):
    validate_admission(admission)

    if admission["weave_capsule_sha256"] != canonical_digest(weave_capsule):
        raise ValueError("generation weave-capsule digest mismatch")
    if admission["parent_set_sha256"] != canonical_digest(parent_set):
        raise ValueError("generation parent-set digest mismatch")
    if admission["weave_ledger_sha256"] != canonical_digest(weave_ledger):
        raise ValueError("generation weave-ledger digest mismatch")
    if admission["heading"] != weave_capsule.get("proposed_heading"):
        raise ValueError("generation heading differs from admitted weave proposal")
    if admission["root_cycle_digest"] != parent_set.get("root_cycle_digest"):
        raise ValueError("generation root-cycle mismatch")
    if sorted(admission["relation_kinds"]) != sorted(weave_capsule.get("relation_kinds", [])):
        raise ValueError("generation relation kinds drifted")

    generation = {
        "schema": GENERATION_SCHEMA,
        "generation_id": "navigation-weave-generation-001",
        "admitted_heading": admission["heading"],
        "admission_sha256": canonical_digest(admission),
        "weave_capsule_sha256": admission["weave_capsule_sha256"],
        "parent_set_sha256": admission["parent_set_sha256"],
        "weave_ledger_sha256": admission["weave_ledger_sha256"],
        "root_cycle_digest": admission["root_cycle_digest"],
        "relation_kinds": list(admission["relation_kinds"]),
        "status": "admitted",
        "claim_limit": (
            "This bounded generation records an admitted heading whose provenance "
            "includes typed weave parents. It does not embed those parents, close the "
            "open branch, or establish that the admitted heading is correct."
        ),
    }
    return validate_generation(generation)


def validate_generation(generation):
    if not isinstance(generation, dict) or generation.get("schema") != GENERATION_SCHEMA:
        raise ValueError("unsupported weave generation schema")
    if set(generation) != GENERATION_KEYS:
        raise ValueError("weave generation shape drifted")
    if generation.get("status") != "admitted":
        raise ValueError("weave generation must be admitted")
    for key in ("generation_id", "admitted_heading", "claim_limit"):
        if not isinstance(generation.get(key), str) or not generation[key]:
            raise ValueError(f"weave generation missing: {key}")
    for key in (
        "admission_sha256",
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        value = generation.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"weave generation digest missing: {key}")
    kinds = generation.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("weave generation relation kinds invalid")
    return generation


def verify_generation(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
    admission,
    generation,
):
    weave_result = weave.verify_weave(
        base_history,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
    )
    if weave_result.get("status") == "incomplete":
        return {"status": "incomplete", "reason": "weave_incomplete"}
    if weave_result.get("status") != "complete":
        return {"status": "invalid", "reason": "weave_invalid"}

    try:
        validate_admission(admission)
        validate_generation(generation)
    except ValueError as error:
        return {"status": "invalid", "reason": str(error).replace(" ", "_")}

    expected = {
        "weave_capsule_sha256": canonical_digest(weave_capsule),
        "parent_set_sha256": canonical_digest(parent_set),
        "weave_ledger_sha256": canonical_digest(weave_ledger),
        "root_cycle_digest": parent_set["root_cycle_digest"],
    }
    for key, value in expected.items():
        if admission.get(key) != value:
            return {"status": "invalid", "reason": f"admission_{key}_mismatch"}

    if admission["heading"] != weave_capsule["proposed_heading"]:
        return {"status": "invalid", "reason": "admission_heading_mismatch"}
    if sorted(admission["relation_kinds"]) != sorted(weave_capsule["relation_kinds"]):
        return {"status": "invalid", "reason": "admission_relation_kinds_mismatch"}

    if generation["admission_sha256"] != canonical_digest(admission):
        return {"status": "invalid", "reason": "generation_admission_digest_mismatch"}
    if generation["admitted_heading"] != admission["heading"]:
        return {"status": "invalid", "reason": "generation_heading_mismatch"}
    for key in (
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        if generation[key] != admission[key]:
            return {"status": "invalid", "reason": f"generation_{key}_mismatch"}
    if sorted(generation["relation_kinds"]) != sorted(admission["relation_kinds"]):
        return {"status": "invalid", "reason": "generation_relation_kinds_mismatch"}

    return {
        "status": "complete",
        "reason": None,
        "admitted_heading": generation["admitted_heading"],
        "relation_kinds": generation["relation_kinds"],
        "root_cycle_digest": generation["root_cycle_digest"],
        "parent_set_sha256": generation["parent_set_sha256"],
        "weave_capsule_sha256": generation["weave_capsule_sha256"],
        "weave_ledger_sha256": generation["weave_ledger_sha256"],
        "admission_sha256": generation["admission_sha256"],
        "generation_sha256": canonical_digest(generation),
    }


def inspect(
    base_history,
    braid_ledger,
    branch_set,
    weave_ledger,
    parent_set,
    weave_capsule,
    admission,
    generation,
):
    result = verify_generation(
        base_history,
        braid_ledger,
        branch_set,
        weave_ledger,
        parent_set,
        weave_capsule,
        admission,
        generation,
    )
    return {
        "schema": "static.nav-weave-admission-inspection/v0",
        **result,
        "typed_provenance_preserved": (
            set(result.get("relation_kinds", [])) == RELATION_KINDS
            if result.get("status") == "complete" else None
        ),
        "open_branch_closed": False,
        "parent_ranking_claimed": False,
        "automatic_admission_used": False,
        "parents_recursively_embedded": False,
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Explicit NAV typed-weave admission")
    sub = parser.add_subparsers(dest="command", required=True)

    admit = sub.add_parser("admit")
    admit.add_argument("base_history")
    admit.add_argument("braid_ledger")
    admit.add_argument("branch_set")
    admit.add_argument("weave_ledger")
    admit.add_argument("parent_set")
    admit.add_argument("weave_capsule")
    admit.add_argument("--admitted-by", required=True)
    admit.add_argument("--accept-proposal", action="store_true")
    admit.add_argument("-o", "--out")

    generation = sub.add_parser("generation")
    generation.add_argument("admission")
    generation.add_argument("weave_ledger")
    generation.add_argument("parent_set")
    generation.add_argument("weave_capsule")
    generation.add_argument("-o", "--out")

    verify = sub.add_parser("verify")
    for name in (
        "base_history",
        "braid_ledger",
        "branch_set",
        "weave_ledger",
        "parent_set",
        "weave_capsule",
        "admission",
        "generation",
    ):
        verify.add_argument(name)

    inspect_cmd = sub.add_parser("inspect")
    for name in (
        "base_history",
        "braid_ledger",
        "branch_set",
        "weave_ledger",
        "parent_set",
        "weave_capsule",
        "admission",
        "generation",
    ):
        inspect_cmd.add_argument(name)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "admit":
            _write_json(
                make_admission(
                    _read_json(args.base_history),
                    _read_json(args.braid_ledger),
                    _read_json(args.branch_set),
                    _read_json(args.weave_ledger),
                    _read_json(args.parent_set),
                    _read_json(args.weave_capsule),
                    args.admitted_by,
                    args.accept_proposal,
                ),
                args.out,
            )
            return 0
        if args.command == "generation":
            _write_json(
                make_generation(
                    _read_json(args.admission),
                    _read_json(args.weave_ledger),
                    _read_json(args.parent_set),
                    _read_json(args.weave_capsule),
                ),
                args.out,
            )
            return 0

        values = [
            _read_json(getattr(args, name))
            for name in (
                "base_history",
                "braid_ledger",
                "branch_set",
                "weave_ledger",
                "parent_set",
                "weave_capsule",
                "admission",
                "generation",
            )
        ]
        if args.command == "verify":
            _write_json(verify_generation(*values), None)
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
