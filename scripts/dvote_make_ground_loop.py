#!/usr/bin/env python3
"""MAKE GROUND -> DVOTE -> STATIC OS canonical loop.

Consumes a portable DVOTE witness receipt from the MAKE GROUND campaign.
TAKE/HOLD/PASS are preserved as human dispositions. Only TAKE plus a non-empty
witness may become NAV world-contact. The rest remain durable returns.

For an eligible TAKE, this adapter composes the existing Bridge runtimes:
NAV -> WITNESS -> WORLD -> MAKE GROUND -> WITNESS -> WORLD -> DOGRAM -> NAV,
then emits candidate material for a later book edition without editing the book.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import nav
import witness
import world
import make_ground
import dogram_nav

DVOTE_SCHEMA = "dvote.witness-receipt.v1"
FIELD_RETURN_SCHEMA = "static.dvote-field-return/v0"
EDITION_RETURN_SCHEMA = "static.edition-return/v0"
CAMPAIGN_ID = "make-ground-001"
ENCOUNTER_ID = "better-hole-001"
DISPOSITIONS = {"take", "hold", "pass"}

START_HEADING = (
    "Change the representation of one ordinary unresolved problem and test "
    "whether a genuinely new question becomes reachable."
)
PRESERVE = [
    "NEW REACHABILITY ≠ TRUTH.",
    "reader-local TAKE / HOLD / PASS authority",
    "the original DVOTE witness receipt",
]


def canonical_digest(value):
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(value, path=None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def validate_dvote_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != DVOTE_SCHEMA:
        raise ValueError("unsupported DVOTE receipt schema")
    if receipt.get("campaignId") != CAMPAIGN_ID:
        raise ValueError("unexpected DVOTE campaign")
    if receipt.get("encounterId") != ENCOUNTER_ID:
        raise ValueError("unexpected DVOTE encounter")
    disposition = receipt.get("disposition")
    if disposition not in DISPOSITIONS:
        raise ValueError("DVOTE disposition must be take, hold, or pass")
    if receipt.get("doorId") != disposition:
        raise ValueError("canonical campaign door and disposition must agree")
    for key in ("id", "date", "encounter", "door"):
        if not isinstance(receipt.get(key), str) or not receipt[key]:
            raise ValueError(f"DVOTE receipt missing: {key}")
    if not isinstance(receipt.get("note"), str):
        raise ValueError("DVOTE witness note must be text")
    if receipt.get("object") is not None and not isinstance(receipt.get("object"), str):
        raise ValueError("DVOTE carried object must be text or null")
    return receipt


def make_field_return(receipt):
    validate_dvote_receipt(receipt)
    disposition = receipt["disposition"]
    note = receipt["note"].strip()
    if disposition == "take":
        status = "contacted" if note else "awaiting_witness"
    elif disposition == "hold":
        status = "held"
    else:
        status = "passed"

    return {
        "schema": FIELD_RETURN_SCHEMA,
        "source_schema": DVOTE_SCHEMA,
        "source_sha256": canonical_digest(receipt),
        "campaign_id": receipt["campaignId"],
        "encounter_id": receipt["encounterId"],
        "door_id": receipt["doorId"],
        "disposition": disposition,
        "status": status,
        "witness_note": receipt["note"],
        "carried_object": receipt.get("object") or None,
        "may_contact_nav": status == "contacted",
        "claim_limit": (
            "This return preserves a reader-local disposition and self-reported witness. "
            "It does not establish that the reported event occurred as described, that the "
            "reader's interpretation is correct, or that HOLD/PASS constitute world-contact."
        ),
    }


def make_nav_contact(receipt, field_return, delta, next_heading):
    validate_dvote_receipt(receipt)
    if field_return != make_field_return(receipt):
        raise ValueError("field return does not match DVOTE source")
    if not field_return["may_contact_nav"]:
        raise ValueError("only TAKE with a non-empty witness may contact NAV")
    if not delta or not next_heading:
        raise ValueError("NAV delta and next heading remain explicit local inputs")

    oriented = {
        "schema": "static.nav-receipt/v0",
        "packet_id": "nav-001",
        "status": "oriented",
        "heading": START_HEADING,
        "preserve": list(PRESERVE),
        "aperture": [
            f"DVOTE receipt sha256={field_return['source_sha256']}",
            "a contradictory or corrective source may revise the next heading",
        ],
        "bounded_move": (
            "Run the MAKE GROUND Better Hole encounter through DVOTE and return "
            "with the reader's own witness."
        ),
        "stop_condition": (
            "Stop if the crossing upgrades self-report into independent verification "
            "or treats HOLD/PASS as failed participation."
        ),
        "claim_limit": (
            "A portable DVOTE witness is a source artifact, not proof that its report "
            "is externally verified or that newly reachable questions are true."
        ),
        "observed": None,
        "delta": None,
        "next_heading": None,
    }
    nav.validate_receipt(oriented)
    return nav.record_encounter(oriented, receipt["note"].strip(), delta, next_heading)


def make_evidence_artifact(receipt, field_return, world_receipt):
    return witness.validate_evidence_artifact(
        {
            "schema": "static.evidence-artifact/v0",
            "artifact_id": "dvote-make-ground-comparison-001",
            "artifact_kind": "comparison_worksheet",
            "capture_channel": "static-os canonical contract fixture",
            "content": {
                "dvote_receipt_sha256": field_return["source_sha256"],
                "human_disposition": receipt["disposition"],
                "primary_witness": receipt["note"],
                "world_candidate_sha256": world_receipt["candidate_source_sha256"],
                "claim_relation": world_receipt["claim_relation"],
                "note": (
                    "The comparison is preserved as a new downstream artifact; "
                    "it is not an unrelated second witness."
                ),
            },
            "claim_limit": (
                "This comparison worksheet is generated downstream from the DVOTE witness "
                "and WORLD comparison. A new hash does not make it independent evidence."
            ),
        }
    )


def make_edition_return(receipt, field_return, bundle):
    reorientation = bundle["nav_reorientation"]
    ground = bundle["ground_receipt"]
    return {
        "schema": EDITION_RETURN_SCHEMA,
        "status": "candidate_material",
        "source": {
            "book": "MAKE GROUND — A Field Manual for Growing Possible Futures",
            "campaign_id": receipt["campaignId"],
            "encounter_id": receipt["encounterId"],
            "dvote_receipt_sha256": field_return["source_sha256"],
        },
        "human_disposition": receipt["disposition"],
        "witness": {
            "reported_observation": receipt["note"],
            "carried_object": receipt.get("object") or None,
        },
        "field_delta": ground["fertility_delta"],
        "navigation_return": {
            "from_heading": reorientation["from_heading"],
            "proposed_heading": reorientation["proposed_heading"],
            "reason": reorientation["reason"],
            "transition_sha256": reorientation["transition_sha256"],
        },
        "editorial_return": {
            "survived": [
                "NEW REACHABILITY ≠ TRUTH.",
                "SOURCE ≠ STORY.",
                "MODEL ≠ WORLD.",
                "REORIENTATION ≠ REPLACEMENT.",
            ],
            "next_edition_question": (
                "What should the next edition teach differently after a reader witness "
                "meets an independent contradiction and the disagreement itself becomes "
                "material for a better experiment?"
            ),
        },
        "automatic_book_edit": False,
        "claim_limit": (
            "This packet is candidate editorial material. It does not authorize an edit, "
            "rank the reader's experience, or convert a contract fixture into empirical proof."
        ),
    }


def run_loop(receipt, candidate, field, nav_delta, nav_next_heading, final_heading):
    field_return = make_field_return(receipt)
    nav_contact = make_nav_contact(
        receipt, field_return, nav_delta, nav_next_heading
    )

    witness_intake = witness.intake_nav(nav_contact)
    world_receipt = world.compare(witness_intake, candidate)
    ground_plan = make_ground.make_plan(world_receipt, field)

    evidence = make_evidence_artifact(receipt, field_return, world_receipt)
    ground_receipt = make_ground.observe_plan(
        ground_plan,
        "mixed",
        (
            "The two bounded field reports remain in tension. Preserving both as separate "
            "sources made the disagreement repeatable and exposed a better comparison question."
        ),
        [evidence["artifact_id"]],
        [
            "portable reader witness can enter the provenance loop without becoming authority",
            "contradictory field reports can be retained as fertile material",
        ],
        True,
        True,
        "Repeat with a live exported DVOTE receipt before treating the specimen as field evidence.",
        False,
    )

    witness_reentry = witness.reenter_ground(ground_receipt, evidence)
    recursive_candidate = world.candidate_from_reentry(witness_reentry)
    world_recursion = world.classify_recursive(recursive_candidate)

    ledger = dogram_nav.build_trace(
        [
            nav_contact,
            witness_intake,
            world_receipt,
            ground_receipt,
            witness_reentry,
            world_recursion,
        ]
    )
    transition = dogram_nav.make_transition(
        ledger,
        final_heading,
        (
            "The first witness did not become truth by surviving the crossing; a contradictory "
            "second source changed the useful next question while the generated comparison "
            "artifact remained classified as downstream rather than independent."
        ),
        [
            "the original reader witness",
            "the independent contradiction",
            "generated-downstream evidence classification",
            "human authority over the next consequential move",
        ],
    )
    reorientation = nav.make_reorientation(transition)

    bundle = {
        "schema": "static.make-ground-dvote-loop/v0",
        "field_return": field_return,
        "nav_contact": nav_contact,
        "witness_intake": witness_intake,
        "world_receipt": world_receipt,
        "ground_plan": ground_plan,
        "ground_receipt": ground_receipt,
        "evidence_artifact": evidence,
        "witness_reentry": witness_reentry,
        "world_recursive_candidate": recursive_candidate,
        "world_recursion_receipt": world_recursion,
        "dogram_trace": ledger,
        "dogram_transition": transition,
        "nav_reorientation": reorientation,
    }
    bundle["edition_return"] = make_edition_return(receipt, field_return, bundle)
    return bundle


def build_parser():
    parser = argparse.ArgumentParser(description="MAKE GROUND DVOTE canonical crossing")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("receipt")

    run = sub.add_parser("run")
    run.add_argument("receipt")
    run.add_argument("candidate")
    run.add_argument("field")
    run.add_argument("--nav-delta", required=True)
    run.add_argument("--nav-next-heading", required=True)
    run.add_argument("--final-heading", required=True)
    run.add_argument("-o", "--out")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        receipt = read_json(args.receipt)
        if args.command == "inspect":
            write_json(make_field_return(receipt))
            return 0
        if args.command == "run":
            write_json(
                run_loop(
                    receipt,
                    read_json(args.candidate),
                    read_json(args.field),
                    args.nav_delta,
                    args.nav_next_heading,
                    args.final_heading,
                ),
                args.out,
            )
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
