#!/usr/bin/env python3
"""Explicit field-derived NAV admission, bounded contact, and non-destructive WORLD return.

A selected field discriminator remains only a proposal until explicit local
admission. The fresh contact must match one predeclared discriminating
observation. WORLD then returns an overlay that narrows the current relation
ambiguity without deleting or rewriting any witness.
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


field_nav = _load(
    "static_os_field_dogram_nav_for_cycle",
    "scripts/field_dogram_nav.py",
)
field_runtime = _load(
    "static_os_world_witness_field_for_cycle",
    "scripts/world_witness_field.py",
)
nav = _load(
    "static_os_nav_for_field_cycle",
    "scripts/nav.py",
)

ADMISSION_SCHEMA = "static.nav-field-admission/v0"
CONTACT_SCHEMA = "static.field-discrimination-contact/v0"
UPDATE_SCHEMA = "static.world-witness-field-update/v0"

RELEVANT_RELATIONS = {"corroborates", "contradicts", "corrects"}

ADMISSION_KEYS = {
    "schema",
    "status",
    "heading",
    "field_sha256",
    "field_receipt_sha256",
    "candidate_sha256",
    "transition_sha256",
    "reorientation_sha256",
    "admitted_by",
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


def validate_admission(admission):
    if not isinstance(admission, dict) or admission.get("schema") != ADMISSION_SCHEMA:
        raise ValueError("unsupported field-derived NAV admission schema")
    if set(admission) != ADMISSION_KEYS:
        raise ValueError("field-derived NAV admission shape drifted")
    if admission.get("status") != "admitted":
        raise ValueError("field-derived NAV admission must be admitted")
    for key in ("heading", "admitted_by", "claim_limit"):
        if not isinstance(admission.get(key), str) or not admission[key]:
            raise ValueError(f"field-derived NAV admission missing: {key}")
    for key in (
        "field_sha256",
        "field_receipt_sha256",
        "candidate_sha256",
        "transition_sha256",
        "reorientation_sha256",
    ):
        value = admission.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"field-derived NAV admission digest missing: {key}")
    return admission


def make_admission(
    field,
    field_receipt,
    candidate,
    transition,
    reorientation,
    admitted_by,
    accept_proposal,
):
    field_runtime.validate_field(field)
    field_runtime.validate_receipt(field_receipt)
    field_nav.validate_candidate(candidate)
    field_nav.validate_transition(transition)

    if accept_proposal is not True:
        raise ValueError("explicit local acceptance is required")
    if not isinstance(admitted_by, str) or not admitted_by:
        raise ValueError("field-derived admission actor missing")

    field_digest = canonical_digest(field)
    receipt_digest = canonical_digest(field_receipt)
    candidate_digest = canonical_digest(candidate)
    transition_digest = canonical_digest(transition)
    reorientation_digest = canonical_digest(reorientation)

    if field_receipt["field_sha256"] != field_digest:
        raise ValueError("field receipt does not address supplied field")
    if candidate["field_sha256"] != field_digest:
        raise ValueError("candidate does not address supplied field")
    if transition["field_sha256"] != field_digest:
        raise ValueError("transition does not address supplied field")
    if transition["field_receipt_sha256"] != receipt_digest:
        raise ValueError("transition does not address supplied field receipt")
    if transition["candidate_sha256"] != candidate_digest:
        raise ValueError("transition does not address supplied candidate")

    expected_reorientation = field_nav.make_nav_reorientation(transition)
    if reorientation != expected_reorientation:
        raise ValueError("reorientation differs from transition-derived NAV proposal")
    if reorientation["status"] != "proposed":
        raise ValueError("field-derived NAV proposal must remain proposed before admission")
    if reorientation["proposed_heading"] != candidate["proposed_heading"]:
        raise ValueError("field-derived NAV heading differs from selected candidate")
    if reorientation["candidate_sha256"] != candidate_digest:
        raise ValueError("reorientation candidate address mismatch")

    admission = {
        "schema": ADMISSION_SCHEMA,
        "status": "admitted",
        "heading": reorientation["proposed_heading"],
        "field_sha256": field_digest,
        "field_receipt_sha256": receipt_digest,
        "candidate_sha256": candidate_digest,
        "transition_sha256": transition_digest,
        "reorientation_sha256": reorientation_digest,
        "admitted_by": admitted_by,
        "claim_limit": (
            "This records explicit local admission of one field-derived NAV proposal. "
            "Admission does not prove the discriminator will work, rank witnesses, "
            "or convert the WORLD field into a verdict."
        ),
    }
    return validate_admission(admission)


def start_orientation(admission, candidate):
    validate_admission(admission)
    field_nav.validate_candidate(candidate)
    if admission["candidate_sha256"] != canonical_digest(candidate):
        raise ValueError("admission does not address supplied discriminator candidate")
    if admission["field_sha256"] != candidate["field_sha256"]:
        raise ValueError("admission/candidate field mismatch")
    if admission["heading"] != candidate["proposed_heading"]:
        raise ValueError("admission heading differs from candidate proposal")

    receipt = {
        "schema": nav.RECEIPT_SCHEMA,
        "packet_id": "nav-001",
        "status": "oriented",
        "heading": admission["heading"],
        "preserve": list(candidate["preserve"]),
        "aperture": list(candidate["aperture"]),
        "bounded_move": candidate["bounded_move"],
        "stop_condition": candidate["stop_condition"],
        "claim_limit": (
            "This orientation executes only the explicitly admitted bounded "
            "discriminator. It does not establish a witness verdict."
        ),
        "observed": None,
        "delta": None,
        "next_heading": None,
    }
    return nav.validate_receipt(receipt)


def perform_contact(
    admission,
    candidate,
    orientation,
    observed_relation,
    observed,
    next_heading,
):
    validate_admission(admission)
    field_nav.validate_candidate(candidate)
    nav.validate_receipt(orientation)

    if admission["candidate_sha256"] != canonical_digest(candidate):
        raise ValueError("contact candidate differs from admitted candidate")
    if orientation["status"] != "oriented":
        raise ValueError("field discrimination contact requires oriented NAV receipt")
    if orientation["heading"] != admission["heading"]:
        raise ValueError("field discrimination contact starts from wrong heading")
    if orientation["bounded_move"] != candidate["bounded_move"]:
        raise ValueError("field discrimination contact bounded move drifted")
    if observed_relation not in RELEVANT_RELATIONS:
        raise ValueError("field discrimination observed relation invalid")

    declared = {
        path["relation"]: path["discriminating_observation"]
        for path in candidate["paths"]
    }
    if observed_relation not in declared:
        raise ValueError("observed relation was not a declared discriminator path")
    if observed != declared[observed_relation]:
        raise ValueError("observed result does not match predeclared discriminator observation")
    if not isinstance(next_heading, str) or not next_heading:
        raise ValueError("field discrimination next heading missing")

    contact = nav.record_encounter(
        orientation,
        observed,
        (
            f"The one-contact discriminator matched the predeclared "
            f"{observed_relation} observation. This narrows the current field "
            "comparison without deleting non-aligned witnesses."
        ),
        next_heading,
    )

    capsule = {
        "schema": CONTACT_SCHEMA,
        "status": "contacted",
        "field_sha256": admission["field_sha256"],
        "admission_sha256": canonical_digest(admission),
        "candidate_sha256": canonical_digest(candidate),
        "orientation_sha256": canonical_digest(orientation),
        "contact_sha256": canonical_digest(contact),
        "observed_relation": observed_relation,
        "observed": observed,
        "next_heading": next_heading,
        "claim_limit": (
            "This contact receipts one predeclared discriminator outcome. It does "
            "not erase witnesses on other paths, establish truth, or authorize a verdict."
        ),
    }
    return capsule, contact


def validate_contact_capsule(capsule):
    if not isinstance(capsule, dict) or capsule.get("schema") != CONTACT_SCHEMA:
        raise ValueError("unsupported field discrimination contact schema")
    expected_keys = {
        "schema",
        "status",
        "field_sha256",
        "admission_sha256",
        "candidate_sha256",
        "orientation_sha256",
        "contact_sha256",
        "observed_relation",
        "observed",
        "next_heading",
        "claim_limit",
    }
    if set(capsule) != expected_keys:
        raise ValueError("field discrimination contact shape drifted")
    if capsule.get("status") != "contacted":
        raise ValueError("field discrimination contact must be contacted")
    for key in (
        "field_sha256",
        "admission_sha256",
        "candidate_sha256",
        "orientation_sha256",
        "contact_sha256",
    ):
        value = capsule.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"field discrimination contact digest missing: {key}")
    if capsule.get("observed_relation") not in RELEVANT_RELATIONS:
        raise ValueError("field discrimination observed relation invalid")
    for key in ("observed", "next_heading", "claim_limit"):
        if not isinstance(capsule.get(key), str) or not capsule[key]:
            raise ValueError(f"field discrimination contact missing: {key}")
    return capsule


def update_field(
    field,
    field_receipt,
    candidate,
    admission,
    orientation,
    contact_capsule,
    contact,
):
    field_runtime.validate_field(field)
    field_runtime.validate_receipt(field_receipt)
    field_nav.validate_candidate(candidate)
    validate_admission(admission)
    validate_contact_capsule(contact_capsule)
    nav.validate_receipt(orientation)
    nav.validate_receipt(contact)

    field_digest = canonical_digest(field)
    field_receipt_digest = canonical_digest(field_receipt)

    if field_receipt["field_sha256"] != field_digest:
        raise ValueError("field receipt does not address supplied field")
    if admission["field_sha256"] != field_digest:
        raise ValueError("admission field mismatch")
    if admission["field_receipt_sha256"] != field_receipt_digest:
        raise ValueError("admission field receipt mismatch")
    if admission["candidate_sha256"] != canonical_digest(candidate):
        raise ValueError("admission candidate mismatch")
    if contact_capsule["field_sha256"] != field_digest:
        raise ValueError("contact field mismatch")
    if contact_capsule["admission_sha256"] != canonical_digest(admission):
        raise ValueError("contact admission mismatch")
    if contact_capsule["candidate_sha256"] != canonical_digest(candidate):
        raise ValueError("contact candidate mismatch")
    if contact_capsule["orientation_sha256"] != canonical_digest(orientation):
        raise ValueError("contact orientation mismatch")
    if contact_capsule["contact_sha256"] != canonical_digest(contact):
        raise ValueError("contact receipt mismatch")
    if contact["status"] != "contacted":
        raise ValueError("field update requires contacted NAV receipt")
    if contact["observed"] != contact_capsule["observed"]:
        raise ValueError("contact observation/capsule mismatch")
    if contact["next_heading"] != contact_capsule["next_heading"]:
        raise ValueError("contact next-heading/capsule mismatch")

    live_relations = sorted(
        relation
        for relation in RELEVANT_RELATIONS
        if field_receipt["relation_counts"].get(relation, 0) > 0
    )
    declared_relations = sorted(path["relation"] for path in candidate["paths"])
    if declared_relations != live_relations:
        raise ValueError("candidate no longer covers the original live relation field")

    observed_relation = contact_capsule["observed_relation"]
    if observed_relation not in live_relations:
        raise ValueError("observed relation was not live in original field")

    supported_relations = [observed_relation]
    challenged_relations = [
        relation for relation in live_relations if relation != observed_relation
    ]

    witness_states = []
    for descriptor in field["witnesses"]:
        relation = descriptor["claim_relation"]
        if relation == observed_relation:
            state = "aligned_with_contact"
        elif relation in challenged_relations:
            state = "challenged_by_contact"
        else:
            state = "outside_discriminator_scope"
        witness_states.append(
            {
                "source_sha256": descriptor["source_sha256"],
                "original_relation": relation,
                "contact_state": state,
            }
        )
    witness_states.sort(key=lambda item: item["source_sha256"])

    update = {
        "schema": UPDATE_SCHEMA,
        "packet_id": "world-001",
        "original_field_sha256": field_digest,
        "original_field_receipt_sha256": field_receipt_digest,
        "discrimination_contact_sha256": canonical_digest(contact_capsule),
        "observed_relation": observed_relation,
        "live_relations_before": live_relations,
        "contact_supported_relations": supported_relations,
        "contact_challenged_relations": challenged_relations,
        "witness_states": witness_states,
        "witness_count_before": len(field["witnesses"]),
        "witness_count_after": len(witness_states),
        "all_witnesses_retained": True,
        "ambiguity_before": len(live_relations),
        "ambiguity_after": len(supported_relations),
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "establishes": [
            f"The admitted discriminator produced the predeclared {observed_relation} observation.",
            f"Current relation-path ambiguity narrowed from {len(live_relations)} to {len(supported_relations)} for this discriminator.",
            "Every original witness remains addressable in the returned field overlay.",
            "Witnesses on non-aligned relation paths are challenged by this contact rather than deleted.",
            "The original WORLD field receipt remains verdict-withheld and majority-free.",
        ],
        "does_not_establish": [
            "Aligned witnesses are true.",
            "Challenged witnesses are false.",
            "A challenged witness should be deleted from history.",
            "The contact permanently resolves future witness disagreement.",
            "One discriminating contact establishes a final verdict.",
            "Witness counts may now be used as authority.",
        ],
        "next_door": (
            "Carry the full witness field plus this non-destructive update forward. "
            "If challenged witnesses remain materially live, design the next bounded "
            "contact against the residual disagreement rather than deleting them."
        ),
    }
    return validate_update(update)


def validate_update(update):
    if not isinstance(update, dict) or update.get("schema") != UPDATE_SCHEMA:
        raise ValueError("unsupported WORLD witness field update schema")
    if update.get("packet_id") != "world-001":
        raise ValueError("WORLD witness field update packet mismatch")
    for key in (
        "original_field_sha256",
        "original_field_receipt_sha256",
        "discrimination_contact_sha256",
    ):
        value = update.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"WORLD witness field update digest missing: {key}")
    if update.get("observed_relation") not in RELEVANT_RELATIONS:
        raise ValueError("WORLD witness field update observed relation invalid")
    before = update.get("live_relations_before")
    supported = update.get("contact_supported_relations")
    challenged = update.get("contact_challenged_relations")
    if not isinstance(before, list) or len(before) < 2 or len(before) != len(set(before)):
        raise ValueError("WORLD witness field update live relations invalid")
    if not isinstance(supported, list) or len(supported) != 1:
        raise ValueError("WORLD witness field update requires exactly one supported relation")
    if not isinstance(challenged, list):
        raise ValueError("WORLD witness field update challenged relations invalid")
    if set(supported) | set(challenged) != set(before):
        raise ValueError("WORLD witness field update relation partition incomplete")
    if set(supported) & set(challenged):
        raise ValueError("WORLD witness field update relation partition overlaps")
    if supported[0] != update["observed_relation"]:
        raise ValueError("WORLD witness field update supported relation differs from observation")

    states = update.get("witness_states")
    if not isinstance(states, list) or len(states) < 2:
        raise ValueError("WORLD witness field update witness states missing")
    sources = [item.get("source_sha256") for item in states if isinstance(item, dict)]
    if len(sources) != len(states) or len(sources) != len(set(sources)):
        raise ValueError("WORLD witness field update witness states duplicate or malformed")
    allowed_states = {
        "aligned_with_contact",
        "challenged_by_contact",
        "outside_discriminator_scope",
    }
    for item in states:
        if set(item) != {"source_sha256", "original_relation", "contact_state"}:
            raise ValueError("WORLD witness field update witness state shape mismatch")
        if item["contact_state"] not in allowed_states:
            raise ValueError("WORLD witness field update contact state invalid")

    if update.get("witness_count_before") != len(states):
        raise ValueError("WORLD witness field update before count mismatch")
    if update.get("witness_count_after") != len(states):
        raise ValueError("WORLD witness field update deleted a witness")
    if update.get("all_witnesses_retained") is not True:
        raise ValueError("WORLD witness field update must retain all witnesses")
    if update.get("ambiguity_before") != len(before):
        raise ValueError("WORLD witness field update ambiguity-before mismatch")
    if update.get("ambiguity_after") != len(supported):
        raise ValueError("WORLD witness field update ambiguity-after mismatch")
    if update["ambiguity_after"] >= update["ambiguity_before"]:
        raise ValueError("WORLD witness field update did not reduce current discriminator ambiguity")
    if update.get("majority_rule_used") is not False:
        raise ValueError("WORLD witness field update cannot use majority rule")
    if update.get("verdict_status") != "withheld":
        raise ValueError("WORLD witness field update verdict must remain withheld")
    if not update.get("establishes") or not update.get("does_not_establish"):
        raise ValueError("WORLD witness field update claim boundary missing")
    if not update.get("next_door"):
        raise ValueError("WORLD witness field update next door missing")
    return update


def inspect(update):
    validate_update(update)
    return {
        "schema": "static.world-witness-field-update-inspection/v0",
        "observed_relation": update["observed_relation"],
        "ambiguity_before": update["ambiguity_before"],
        "ambiguity_after": update["ambiguity_after"],
        "ambiguity_reduced": update["ambiguity_after"] < update["ambiguity_before"],
        "witness_count_before": update["witness_count_before"],
        "witness_count_after": update["witness_count_after"],
        "all_witnesses_retained": update["all_witnesses_retained"],
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "witness_deletion_used": False,
        "truth_claimed": False,
        "next_door": update["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="Field-derived NAV admission, contact, and WORLD return"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("update")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.update)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
