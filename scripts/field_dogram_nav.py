#!/usr/bin/env python3
"""Dogram/NAV membrane for unresolved independent witness fields.

WORLD preserves a healthy field of independent witnesses. Local candidate moves
declare bounded discriminators. Dogram selects the minimum declared structural
cost among candidates that distinguish every live relevant relation. NAV emits
a proposal only. Witness counts never participate in selection.
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


field_runtime = _load(
    "static_os_world_witness_field_for_nav",
    "scripts/world_witness_field.py",
)

CANDIDATE_SCHEMA = "static.field-discriminator-candidate/v0"
TRANSITION_SCHEMA = "static.dogram-field-transition/v0"
NAV_SCHEMA = "static.nav-field-reorientation/v0"

CANDIDATE_KEYS = {
    "schema",
    "candidate_id",
    "field_sha256",
    "proposed_heading",
    "bounded_move",
    "paths",
    "preserve",
    "aperture",
    "stop_condition",
    "cost_vector",
    "claim_limit",
}
COST_KEYS = {
    "irreversible_steps",
    "changed_variables",
    "world_contacts",
    "external_dependencies",
}
RELEVANT_RELATIONS = {"corroborates", "contradicts", "corrects"}


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


def validate_candidate(candidate):
    if not isinstance(candidate, dict) or candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("unsupported field discriminator candidate schema")
    if set(candidate) != CANDIDATE_KEYS:
        raise ValueError("field discriminator candidate shape drifted")
    for key in (
        "candidate_id",
        "proposed_heading",
        "bounded_move",
        "stop_condition",
        "claim_limit",
    ):
        if not isinstance(candidate.get(key), str) or not candidate[key]:
            raise ValueError(f"field discriminator candidate missing: {key}")

    field_digest = candidate.get("field_sha256")
    if not isinstance(field_digest, str) or len(field_digest) != 64:
        raise ValueError("field discriminator field digest missing")

    paths = candidate.get("paths")
    if not isinstance(paths, list) or len(paths) < 2:
        raise ValueError("field discriminator needs at least two relation paths")
    relations = []
    observations = []
    for path in paths:
        if not isinstance(path, dict) or set(path) != {
            "relation",
            "discriminating_observation",
        }:
            raise ValueError("field discriminator path shape mismatch")
        relation = path.get("relation")
        observation = path.get("discriminating_observation")
        if relation not in RELEVANT_RELATIONS:
            raise ValueError("field discriminator relation invalid")
        if not isinstance(observation, str) or not observation.strip():
            raise ValueError("field discriminator observation missing")
        relations.append(relation)
        observations.append(observation.strip())
    if len(relations) != len(set(relations)):
        raise ValueError("field discriminator relation repeated")
    if len(observations) != len(set(observations)):
        raise ValueError("field discriminator observations do not distinguish paths")

    for key in ("preserve", "aperture"):
        value = candidate.get(key)
        if not isinstance(value, list) or not value:
            raise ValueError(f"field discriminator {key} set missing")
        if any(not isinstance(item, str) or not item for item in value):
            raise ValueError(f"field discriminator {key} contains invalid item")
        if len(value) != len(set(value)):
            raise ValueError(f"field discriminator {key} contains duplicates")

    cost = candidate.get("cost_vector")
    if not isinstance(cost, dict) or set(cost) != COST_KEYS:
        raise ValueError("field discriminator cost vector shape mismatch")
    if cost.get("irreversible_steps") != 0:
        raise ValueError("field discriminator must remain reversible")
    if cost.get("world_contacts") != 1:
        raise ValueError("field discriminator must require exactly one world contact")
    for key in ("changed_variables", "external_dependencies"):
        value = cost.get(key)
        if not isinstance(value, int) or value < (1 if key == "changed_variables" else 0):
            raise ValueError(f"field discriminator invalid cost: {key}")
    return candidate


def _live_relations(field_receipt):
    counts = field_receipt["relation_counts"]
    return sorted(
        relation
        for relation in RELEVANT_RELATIONS
        if counts.get(relation, 0) > 0
    )


def _cost_key(candidate):
    cost = candidate["cost_vector"]
    return (
        cost["irreversible_steps"],
        cost["changed_variables"],
        cost["world_contacts"],
        cost["external_dependencies"],
        canonical_digest(candidate),
    )


def validate_transition(transition):
    if not isinstance(transition, dict) or transition.get("schema") != TRANSITION_SCHEMA:
        raise ValueError("unsupported Dogram field transition schema")
    if transition.get("status") != "proposed":
        raise ValueError("Dogram field transition must remain proposed")
    for key in (
        "transition_id",
        "to_heading",
        "bounded_move",
        "selection_basis",
        "claim_limit",
    ):
        if not isinstance(transition.get(key), str) or not transition[key]:
            raise ValueError(f"Dogram field transition missing: {key}")
    for key in (
        "field_sha256",
        "field_receipt_sha256",
        "candidate_sha256",
    ):
        value = transition.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"Dogram field transition digest missing: {key}")
    live = transition.get("live_relations")
    if not isinstance(live, list) or len(live) < 2 or set(live) - RELEVANT_RELATIONS:
        raise ValueError("Dogram field transition live relations invalid")
    if len(live) != len(set(live)):
        raise ValueError("Dogram field transition live relations repeated")
    cost = transition.get("cost_vector")
    if not isinstance(cost, dict) or set(cost) != COST_KEYS:
        raise ValueError("Dogram field transition cost vector invalid")
    if cost["irreversible_steps"] != 0 or cost["world_contacts"] != 1:
        raise ValueError("Dogram field transition exceeds bounded contact contract")
    preserved = transition.get("preserved")
    if not isinstance(preserved, list) or not preserved:
        raise ValueError("Dogram field transition preserve set missing")
    if transition.get("selection_basis") != "minimum_declared_structural_cost":
        raise ValueError("Dogram field transition selection basis drifted")
    return transition


def select_transition(field, field_receipt, candidates):
    field_runtime.validate_field(field)
    field_runtime.validate_receipt(field_receipt)

    field_digest = canonical_digest(field)
    receipt_digest = canonical_digest(field_receipt)
    if field_receipt["field_sha256"] != field_digest:
        raise ValueError("WORLD field receipt does not address supplied field")
    if field_receipt["composed_source_sha256"] != field["composed_source_sha256"]:
        raise ValueError("WORLD field receipt/source mismatch")
    if field_receipt["plurality_status"] != "independent_plurality_candidate":
        raise ValueError("Dogram requires independently qualified witness plurality")
    if field_receipt["field_state"] != "disagreement_preserved":
        raise ValueError("Dogram discriminator requires unresolved independent disagreement")
    if field_receipt["majority_rule_used"] is not False:
        raise ValueError("Dogram refuses majority-derived witness field")
    if field_receipt["verdict_status"] != "withheld":
        raise ValueError("Dogram requires WORLD verdict to remain withheld")

    live_relations = _live_relations(field_receipt)
    if len(live_relations) < 2:
        raise ValueError("witness field has fewer than two live relevant relation paths")

    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Dogram discriminator candidate set missing")

    qualified = []
    for candidate in candidates:
        validate_candidate(candidate)
        if candidate["field_sha256"] != field_digest:
            raise ValueError("field discriminator candidate addresses another field")
        candidate_relations = sorted(path["relation"] for path in candidate["paths"])
        if candidate_relations != live_relations:
            raise ValueError("field discriminator must cover every live relevant relation")
        qualified.append(candidate)

    selected = min(qualified, key=_cost_key)
    selected_digest = canonical_digest(selected)

    preserved = list(selected["preserve"])
    for invariant in (
        "independent witness disagreement",
        "majority rule remains unused",
        "WORLD verdict remains withheld",
        "typed composed origin remains addressable",
    ):
        if invariant not in preserved:
            preserved.append(invariant)

    transition = {
        "schema": TRANSITION_SCHEMA,
        "transition_id": "witness-field-dogram-nav-001",
        "field_sha256": field_digest,
        "field_receipt_sha256": receipt_digest,
        "live_relations": live_relations,
        "candidate_sha256": selected_digest,
        "to_heading": selected["proposed_heading"],
        "bounded_move": selected["bounded_move"],
        "cost_vector": dict(selected["cost_vector"]),
        "preserved": preserved,
        "selection_basis": "minimum_declared_structural_cost",
        "status": "proposed",
        "claim_limit": (
            "Dogram selected the minimum declared structural-cost candidate among "
            "submitted moves that distinguish every live relevant witness relation. "
            "This does not prove the move truly discriminates in the world, rank the "
            "witnesses, choose a majority, or authorize execution."
        ),
    }
    return validate_transition(transition)


def make_nav_reorientation(transition):
    validate_transition(transition)
    return {
        "schema": NAV_SCHEMA,
        "packet_id": "nav-001",
        "status": "proposed",
        "field_sha256": transition["field_sha256"],
        "field_receipt_sha256": transition["field_receipt_sha256"],
        "transition_sha256": canonical_digest(transition),
        "candidate_sha256": transition["candidate_sha256"],
        "live_relations": list(transition["live_relations"]),
        "proposed_heading": transition["to_heading"],
        "bounded_move": transition["bounded_move"],
        "preserved": list(transition["preserved"]),
        "reason": (
            "A healthy independent witness field contains unresolved disagreement; "
            "Dogram selected the smallest declared one-contact discriminator without "
            "using witness counts as a decision rule."
        ),
        "claim_limit": (
            "This NAV artifact is a reorientation proposal only. It does not admit "
            "the heading, execute the move, rank witness claims, or convert relation "
            "counts into authority."
        ),
    }


def inspect(value):
    if not isinstance(value, dict):
        raise ValueError("unsupported witness-field navigation inspection input")
    if value.get("schema") == TRANSITION_SCHEMA:
        validate_transition(value)
        return {
            "schema": "static.dogram-field-transition-inspection/v0",
            "live_relations": value["live_relations"],
            "cost_vector": value["cost_vector"],
            "selection_basis": value["selection_basis"],
            "status": value["status"],
            "majority_rule_used": False,
            "verdict_claimed": False,
            "authority_claimed": False,
        }
    if value.get("schema") == NAV_SCHEMA:
        if value.get("status") != "proposed":
            raise ValueError("NAV field reorientation must remain proposed")
        return {
            "schema": "static.nav-field-reorientation-inspection/v0",
            "live_relations": value.get("live_relations"),
            "proposed_heading": value.get("proposed_heading"),
            "status": value.get("status"),
            "majority_rule_used": False,
            "verdict_claimed": False,
            "heading_admitted": False,
        }
    raise ValueError("unsupported witness-field navigation inspection schema")


def build_parser():
    parser = argparse.ArgumentParser(description="Witness field -> Dogram -> NAV")
    sub = parser.add_subparsers(dest="command", required=True)

    select_cmd = sub.add_parser("select")
    select_cmd.add_argument("field")
    select_cmd.add_argument("field_receipt")
    select_cmd.add_argument("candidates", nargs="+")
    select_cmd.add_argument("-o", "--out")

    reorient = sub.add_parser("reorient")
    reorient.add_argument("transition")
    reorient.add_argument("-o", "--out")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("source")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "select":
            _write_json(
                select_transition(
                    _read_json(args.field),
                    _read_json(args.field_receipt),
                    [_read_json(path) for path in args.candidates],
                ),
                args.out,
            )
            return 0
        if args.command == "reorient":
            _write_json(make_nav_reorientation(_read_json(args.transition)), args.out)
            return 0
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.source)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
