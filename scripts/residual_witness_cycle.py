#!/usr/bin/env python3
"""Second discriminator for challenged-but-retained witness paths.

The first contact is immutable history, not a verdict. A residual candidate
targets one challenged relation against the relation supported by contact #1.
The second contact may show that the challenged path survives or challenge it
again; either way, every witness remains addressable.
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


first_cycle = _load(
    "static_os_field_discrimination_cycle_for_residual",
    "scripts/field_discrimination_cycle.py",
)
field_runtime = _load(
    "static_os_world_witness_field_for_residual",
    "scripts/world_witness_field.py",
)
nav = _load("static_os_nav_for_residual", "scripts/nav.py")

CANDIDATE_SCHEMA = "static.residual-witness-discriminator-candidate/v0"
TRANSITION_SCHEMA = "static.dogram-residual-witness-transition/v0"
NAV_SCHEMA = "static.nav-residual-witness-reorientation/v0"
ADMISSION_SCHEMA = "static.nav-residual-witness-admission/v0"
CONTACT_SCHEMA = "static.residual-witness-contact/v0"
UPDATE_SCHEMA = "static.world-residual-witness-update/v0"

RELEVANT = {"corroborates", "contradicts", "corrects"}
COST_KEYS = {
    "irreversible_steps",
    "changed_variables",
    "world_contacts",
    "external_dependencies",
}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _write_json(value, path=None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def validate_candidate(candidate):
    required = {
        "schema","candidate_id","original_field_sha256","first_update_sha256",
        "first_contact_sha256","prior_supported_relation","target_challenged_relation",
        "proposed_heading","bounded_move","paths","preserve","aperture",
        "stop_condition","cost_vector","claim_limit",
    }
    if not isinstance(candidate, dict) or candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("unsupported residual discriminator candidate schema")
    if set(candidate) != required:
        raise ValueError("residual discriminator candidate shape drifted")
    for key in ("candidate_id","proposed_heading","bounded_move","stop_condition","claim_limit"):
        if not isinstance(candidate.get(key), str) or not candidate[key]:
            raise ValueError(f"residual discriminator candidate missing: {key}")
    for key in ("original_field_sha256","first_update_sha256","first_contact_sha256"):
        if not isinstance(candidate.get(key), str) or len(candidate[key]) != 64:
            raise ValueError(f"residual discriminator digest missing: {key}")
    prior = candidate.get("prior_supported_relation")
    target = candidate.get("target_challenged_relation")
    if prior not in RELEVANT or target not in RELEVANT or prior == target:
        raise ValueError("residual discriminator relation pair invalid")
    paths = candidate.get("paths")
    if not isinstance(paths, list) or len(paths) != 2:
        raise ValueError("residual discriminator requires exactly two paths")
    rels, observations = [], []
    for item in paths:
        if not isinstance(item, dict) or set(item) != {"relation","discriminating_observation"}:
            raise ValueError("residual discriminator path shape mismatch")
        if item["relation"] not in RELEVANT:
            raise ValueError("residual discriminator path relation invalid")
        if not isinstance(item["discriminating_observation"], str) or not item["discriminating_observation"]:
            raise ValueError("residual discriminator observation missing")
        rels.append(item["relation"])
        observations.append(item["discriminating_observation"])
    if set(rels) != {prior, target}:
        raise ValueError("residual discriminator paths must cover prior and challenged relations")
    if len(set(observations)) != 2:
        raise ValueError("residual discriminator observations do not distinguish paths")
    for key in ("preserve","aperture"):
        value = candidate.get(key)
        if not isinstance(value, list) or not value or len(value) != len(set(value)):
            raise ValueError(f"residual discriminator {key} invalid")
    cost = candidate.get("cost_vector")
    if not isinstance(cost, dict) or set(cost) != COST_KEYS:
        raise ValueError("residual discriminator cost vector shape mismatch")
    if cost["irreversible_steps"] != 0 or cost["world_contacts"] != 1:
        raise ValueError("residual discriminator must be reversible and one-contact")
    if not isinstance(cost["changed_variables"], int) or cost["changed_variables"] < 1:
        raise ValueError("residual discriminator changed_variables invalid")
    if not isinstance(cost["external_dependencies"], int) or cost["external_dependencies"] < 0:
        raise ValueError("residual discriminator external_dependencies invalid")
    return candidate


def _cost_key(candidate):
    c = candidate["cost_vector"]
    return (
        c["irreversible_steps"],
        c["changed_variables"],
        c["world_contacts"],
        c["external_dependencies"],
        digest(candidate),
    )


def _validate_first_context(field, field_receipt, first_update, first_contact):
    field_runtime.validate_field(field)
    field_runtime.validate_receipt(field_receipt)
    first_cycle.validate_update(first_update)
    first_cycle.validate_contact_capsule(first_contact)

    field_sha = digest(field)
    receipt_sha = digest(field_receipt)
    contact_sha = digest(first_contact)
    if field_receipt["field_sha256"] != field_sha:
        raise ValueError("first field receipt does not address supplied field")
    if first_update["original_field_sha256"] != field_sha:
        raise ValueError("first update does not address supplied field")
    if first_update["original_field_receipt_sha256"] != receipt_sha:
        raise ValueError("first update does not address supplied field receipt")
    if first_update["discrimination_contact_sha256"] != contact_sha:
        raise ValueError("first update does not address supplied first contact")
    if first_update["contact_supported_relations"] != [first_update["observed_relation"]]:
        raise ValueError("first update supported relation shape drifted")
    if not first_update["contact_challenged_relations"]:
        raise ValueError("first update has no challenged relation to test")
    return field_sha, digest(first_update), contact_sha


def select_transition(field, field_receipt, first_update, first_contact, candidates):
    field_sha, update_sha, contact_sha = _validate_first_context(
        field, field_receipt, first_update, first_contact
    )
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("residual discriminator candidate set missing")

    prior = first_update["contact_supported_relations"][0]
    challenged = set(first_update["contact_challenged_relations"])
    qualified = []
    for candidate in candidates:
        validate_candidate(candidate)
        if candidate["original_field_sha256"] != field_sha:
            raise ValueError("residual candidate addresses another field")
        if candidate["first_update_sha256"] != update_sha:
            raise ValueError("residual candidate addresses another first update")
        if candidate["first_contact_sha256"] != contact_sha:
            raise ValueError("residual candidate addresses another first contact")
        if candidate["prior_supported_relation"] != prior:
            raise ValueError("residual candidate rewrites prior supported relation")
        if candidate["target_challenged_relation"] not in challenged:
            raise ValueError("residual candidate must target a challenged relation")
        qualified.append(candidate)

    selected = min(qualified, key=_cost_key)
    preserved = list(selected["preserve"])
    for invariant in (
        "first contact remains immutable history",
        "challenged witnesses remain addressable",
        "majority rule remains unused",
        "WORLD verdict remains withheld",
    ):
        if invariant not in preserved:
            preserved.append(invariant)

    transition = {
        "schema": TRANSITION_SCHEMA,
        "transition_id": "residual-witness-dogram-nav-001",
        "original_field_sha256": field_sha,
        "first_update_sha256": update_sha,
        "first_contact_sha256": contact_sha,
        "prior_supported_relation": selected["prior_supported_relation"],
        "target_challenged_relation": selected["target_challenged_relation"],
        "candidate_sha256": digest(selected),
        "to_heading": selected["proposed_heading"],
        "bounded_move": selected["bounded_move"],
        "cost_vector": dict(selected["cost_vector"]),
        "preserved": preserved,
        "selection_basis": "minimum_declared_structural_cost",
        "status": "proposed",
        "claim_limit": (
            "Dogram selected a minimum declared-cost second discriminator targeted "
            "at a challenged witness path. It does not revise contact #1, declare "
            "the challenged witness false, or authorize execution."
        ),
    }
    return validate_transition(transition)


def validate_transition(value):
    required = {
        "schema","transition_id","original_field_sha256","first_update_sha256",
        "first_contact_sha256","prior_supported_relation","target_challenged_relation",
        "candidate_sha256","to_heading","bounded_move","cost_vector","preserved",
        "selection_basis","status","claim_limit",
    }
    if not isinstance(value, dict) or value.get("schema") != TRANSITION_SCHEMA:
        raise ValueError("unsupported residual Dogram transition schema")
    if set(value) != required or value.get("status") != "proposed":
        raise ValueError("residual Dogram transition shape/status invalid")
    if value["prior_supported_relation"] == value["target_challenged_relation"]:
        raise ValueError("residual Dogram transition relation pair collapsed")
    if value.get("selection_basis") != "minimum_declared_structural_cost":
        raise ValueError("residual Dogram selection basis drifted")
    return value


def make_reorientation(transition):
    validate_transition(transition)
    return {
        "schema": NAV_SCHEMA,
        "packet_id": "nav-001",
        "status": "proposed",
        "original_field_sha256": transition["original_field_sha256"],
        "first_update_sha256": transition["first_update_sha256"],
        "first_contact_sha256": transition["first_contact_sha256"],
        "transition_sha256": digest(transition),
        "candidate_sha256": transition["candidate_sha256"],
        "prior_supported_relation": transition["prior_supported_relation"],
        "target_challenged_relation": transition["target_challenged_relation"],
        "proposed_heading": transition["to_heading"],
        "bounded_move": transition["bounded_move"],
        "preserved": list(transition["preserved"]),
        "claim_limit": (
            "This is a second-contact NAV proposal only. Contact #1 remains history, "
            "not authority, and the challenged path remains live until separately tested."
        ),
    }


def make_admission(candidate, transition, reorientation, admitted_by, accept_proposal):
    validate_candidate(candidate)
    validate_transition(transition)
    expected = make_reorientation(transition)
    if reorientation != expected:
        raise ValueError("residual reorientation differs from transition-derived proposal")
    if accept_proposal is not True:
        raise ValueError("explicit local acceptance is required")
    if not isinstance(admitted_by, str) or not admitted_by:
        raise ValueError("residual admission actor missing")
    if transition["candidate_sha256"] != digest(candidate):
        raise ValueError("residual transition does not address supplied candidate")
    admission = {
        "schema": ADMISSION_SCHEMA,
        "status": "admitted",
        "heading": reorientation["proposed_heading"],
        "original_field_sha256": transition["original_field_sha256"],
        "first_update_sha256": transition["first_update_sha256"],
        "first_contact_sha256": transition["first_contact_sha256"],
        "candidate_sha256": digest(candidate),
        "transition_sha256": digest(transition),
        "reorientation_sha256": digest(reorientation),
        "admitted_by": admitted_by,
        "claim_limit": (
            "This explicitly admits one residual discriminator. It does not make "
            "contact #1 final or authorize deletion of challenged witnesses."
        ),
    }
    return validate_admission(admission)


def validate_admission(value):
    required = {
        "schema","status","heading","original_field_sha256","first_update_sha256",
        "first_contact_sha256","candidate_sha256","transition_sha256",
        "reorientation_sha256","admitted_by","claim_limit",
    }
    if not isinstance(value, dict) or value.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("unsupported residual NAV admission schema")
    if set(value) != required or value.get("status") != "admitted":
        raise ValueError("residual NAV admission shape/status invalid")
    return value


def start_orientation(admission, candidate):
    validate_admission(admission)
    validate_candidate(candidate)
    if admission["candidate_sha256"] != digest(candidate):
        raise ValueError("residual admission candidate mismatch")
    if admission["heading"] != candidate["proposed_heading"]:
        raise ValueError("residual admission heading mismatch")
    return nav.validate_receipt({
        "schema": nav.RECEIPT_SCHEMA,
        "packet_id": "nav-001",
        "status": "oriented",
        "heading": admission["heading"],
        "preserve": list(candidate["preserve"]),
        "aperture": list(candidate["aperture"]),
        "bounded_move": candidate["bounded_move"],
        "stop_condition": candidate["stop_condition"],
        "claim_limit": "Second contact tests residual tension without revising contact #1.",
        "observed": None,
        "delta": None,
        "next_heading": None,
    })


def perform_contact(admission, candidate, orientation, observed_relation, observed, next_heading):
    validate_admission(admission)
    validate_candidate(candidate)
    nav.validate_receipt(orientation)
    if admission["candidate_sha256"] != digest(candidate):
        raise ValueError("residual contact candidate mismatch")
    if orientation["heading"] != admission["heading"]:
        raise ValueError("residual contact starts from wrong heading")
    declared = {
        item["relation"]: item["discriminating_observation"]
        for item in candidate["paths"]
    }
    if observed_relation not in declared:
        raise ValueError("residual observed relation was not predeclared")
    if observed != declared[observed_relation]:
        raise ValueError("residual observation does not match predeclared discriminator")
    contact = nav.record_encounter(
        orientation,
        observed,
        (
            f"Second discriminator matched the predeclared {observed_relation} path. "
            "Contact #1 remains immutable history."
        ),
        next_heading,
    )
    capsule = {
        "schema": CONTACT_SCHEMA,
        "status": "contacted",
        "original_field_sha256": admission["original_field_sha256"],
        "first_update_sha256": admission["first_update_sha256"],
        "first_contact_sha256": admission["first_contact_sha256"],
        "admission_sha256": digest(admission),
        "candidate_sha256": digest(candidate),
        "orientation_sha256": digest(orientation),
        "contact_sha256": digest(contact),
        "observed_relation": observed_relation,
        "observed": observed,
        "next_heading": next_heading,
        "claim_limit": (
            "This is contact #2 in a residual-disagreement sequence. It does not "
            "rewrite contact #1 or establish a final witness verdict."
        ),
    }
    return capsule, contact


def validate_contact(value):
    if not isinstance(value, dict) or value.get("schema") != CONTACT_SCHEMA:
        raise ValueError("unsupported residual witness contact schema")
    if value.get("status") != "contacted":
        raise ValueError("residual witness contact must be contacted")
    return value


def update_history(
    field,
    first_update,
    first_contact,
    candidate,
    admission,
    orientation,
    second_capsule,
    second_contact,
):
    field_runtime.validate_field(field)
    first_cycle.validate_update(first_update)
    first_cycle.validate_contact_capsule(first_contact)
    validate_candidate(candidate)
    validate_admission(admission)
    validate_contact(second_capsule)
    nav.validate_receipt(orientation)
    nav.validate_receipt(second_contact)

    field_sha = digest(field)
    first_update_sha = digest(first_update)
    first_contact_sha = digest(first_contact)
    second_capsule_sha = digest(second_capsule)

    if first_update["original_field_sha256"] != field_sha:
        raise ValueError("residual update field mismatch")
    if first_update["discrimination_contact_sha256"] != first_contact_sha:
        raise ValueError("residual history first contact mismatch")
    if candidate["first_update_sha256"] != first_update_sha:
        raise ValueError("residual history candidate/first-update mismatch")
    if candidate["first_contact_sha256"] != first_contact_sha:
        raise ValueError("residual history candidate/first-contact mismatch")
    if admission["first_update_sha256"] != first_update_sha:
        raise ValueError("residual history admission/first-update mismatch")
    if admission["first_contact_sha256"] != first_contact_sha:
        raise ValueError("residual history admission/first-contact mismatch")
    if second_capsule["first_update_sha256"] != first_update_sha:
        raise ValueError("residual second contact/first-update mismatch")
    if second_capsule["first_contact_sha256"] != first_contact_sha:
        raise ValueError("residual second contact/first-contact mismatch")
    if second_capsule["admission_sha256"] != digest(admission):
        raise ValueError("residual second contact/admission mismatch")
    if second_capsule["candidate_sha256"] != digest(candidate):
        raise ValueError("residual second contact/candidate mismatch")
    if second_capsule["orientation_sha256"] != digest(orientation):
        raise ValueError("residual second contact/orientation mismatch")
    if second_capsule["contact_sha256"] != digest(second_contact):
        raise ValueError("residual second contact receipt mismatch")

    prior = candidate["prior_supported_relation"]
    target = candidate["target_challenged_relation"]
    if first_update["contact_supported_relations"] != [prior]:
        raise ValueError("residual candidate prior relation differs from first update")
    if target not in first_update["contact_challenged_relations"]:
        raise ValueError("residual target is not challenged in first update")

    observed = second_capsule["observed_relation"]
    if observed not in {prior, target}:
        raise ValueError("residual second observation outside targeted tension")

    first_states = {
        item["source_sha256"]: item
        for item in first_update["witness_states"]
    }
    witness_history = []
    for descriptor in field["witnesses"]:
        source = descriptor["source_sha256"]
        original = descriptor["claim_relation"]
        first_state = first_states[source]["contact_state"]
        if original == observed:
            second_state = "aligned_with_contact"
        elif original in {prior, target}:
            second_state = "challenged_by_contact"
        else:
            second_state = "outside_discriminator_scope"
        witness_history.append({
            "source_sha256": source,
            "original_relation": original,
            "first_contact_state": first_state,
            "second_contact_state": second_state,
        })
    witness_history.sort(key=lambda item: item["source_sha256"])

    survives = observed == target
    status = (
        "challenged_path_survives_second_contact"
        if survives
        else "challenged_path_challenged_again"
    )
    historical = sorted(set([prior, observed]))

    update = {
        "schema": UPDATE_SCHEMA,
        "packet_id": "world-001",
        "original_field_sha256": field_sha,
        "first_update_sha256": first_update_sha,
        "contact_history_sha256s": [first_contact_sha, second_capsule_sha],
        "prior_supported_relation": prior,
        "target_challenged_relation": target,
        "second_observed_relation": observed,
        "residual_tension_status": status,
        "historical_supported_relations": historical,
        "witness_history": witness_history,
        "witness_count_before": len(field["witnesses"]),
        "witness_count_after": len(witness_history),
        "all_witnesses_retained": True,
        "first_contact_promoted_to_verdict": False,
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "establishes": [
            "Contact #1 remains an addressed historical contact rather than a verdict.",
            f"Contact #2 produced the predeclared {observed} residual-discriminator observation.",
            (
                "The previously challenged relation survived a separately admitted second contact."
                if survives
                else "The previously challenged relation was challenged again by a separately admitted second contact."
            ),
            "Every original witness remains addressable across both contact states.",
        ],
        "does_not_establish": [
            "Contact #2 rewrites contact #1.",
            "A witness challenged twice is false.",
            "A witness supported on the second contact is true.",
            "Two contacts constitute a final verdict.",
            "Repeated support may be converted into majority authority.",
        ],
        "next_door": (
            "Preserve both contacts as sequence history. "
            + (
                "Because the challenged path survived, design the next move around the condition difference between contacts rather than choosing either contact as final."
                if survives
                else "Because the challenged path was challenged again, preserve it as retained contrary evidence and seek a genuinely different condition or external source before any stronger disposition."
            )
        ),
    }
    return validate_update(update)


def validate_update(value):
    if not isinstance(value, dict) or value.get("schema") != UPDATE_SCHEMA:
        raise ValueError("unsupported residual WORLD update schema")
    if value.get("packet_id") != "world-001":
        raise ValueError("residual WORLD update packet mismatch")
    history = value.get("contact_history_sha256s")
    if not isinstance(history, list) or len(history) != 2 or len(set(history)) != 2:
        raise ValueError("residual WORLD update must preserve exactly two distinct contacts")
    if value.get("prior_supported_relation") == value.get("target_challenged_relation"):
        raise ValueError("residual WORLD update relation pair collapsed")
    expected_status = (
        "challenged_path_survives_second_contact"
        if value.get("second_observed_relation") == value.get("target_challenged_relation")
        else "challenged_path_challenged_again"
    )
    if value.get("second_observed_relation") not in {
        value.get("prior_supported_relation"),
        value.get("target_challenged_relation"),
    }:
        raise ValueError("residual WORLD update second observation outside targeted tension")
    if value.get("residual_tension_status") != expected_status:
        raise ValueError("residual WORLD update tension status mismatch")
    expected_history = sorted(set([
        value["prior_supported_relation"],
        value["second_observed_relation"],
    ]))
    if value.get("historical_supported_relations") != expected_history:
        raise ValueError("residual WORLD update historical relation set mismatch")
    states = value.get("witness_history")
    if not isinstance(states, list) or len(states) < 2:
        raise ValueError("residual WORLD update witness history missing")
    sources = [item.get("source_sha256") for item in states if isinstance(item, dict)]
    if len(sources) != len(states) or len(sources) != len(set(sources)):
        raise ValueError("residual WORLD update witness history duplicates/malformed")
    if value.get("witness_count_before") != len(states):
        raise ValueError("residual WORLD update before count mismatch")
    if value.get("witness_count_after") != len(states):
        raise ValueError("residual WORLD update deleted a witness")
    if value.get("all_witnesses_retained") is not True:
        raise ValueError("residual WORLD update must retain all witnesses")
    if value.get("first_contact_promoted_to_verdict") is not False:
        raise ValueError("first contact cannot be promoted to verdict")
    if value.get("majority_rule_used") is not False:
        raise ValueError("residual WORLD update cannot use majority rule")
    if value.get("verdict_status") != "withheld":
        raise ValueError("residual WORLD update verdict must remain withheld")
    if not value.get("establishes") or not value.get("does_not_establish") or not value.get("next_door"):
        raise ValueError("residual WORLD update claim boundary missing")
    return value


def inspect(value):
    validate_update(value)
    return {
        "schema": "static.world-residual-witness-update-inspection/v0",
        "contact_count": 2,
        "residual_tension_status": value["residual_tension_status"],
        "historical_supported_relations": value["historical_supported_relations"],
        "all_witnesses_retained": True,
        "first_contact_promoted_to_verdict": False,
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "history_rewritten": False,
        "truth_claimed": False,
        "next_door": value["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Residual witness discriminator cycle")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("update")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.update)))
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
