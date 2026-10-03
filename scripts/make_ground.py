#!/usr/bin/env python3
"""MAKE GROUND Bridge Packet 006 runtime.

Consumes an unresolved WORLD receipt plus a human-selected field profile.
Produces a reversible evidence-fertility plan, then a receipt after observation.
The runtime never chooses which witness is true and never performs the field change.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

PACKET_SCHEMA = "static.bridge-packet/v0"
PACKET_ID = "make-ground-001"
EXPECTED_INVARIANT = "TERRAFORMING ≠ TOTAL DESIGN."
WORLD_RECEIPT_SCHEMA = "static.world-receipt/v0"
FIELD_SCHEMA = "static.field-profile/v0"
PLAN_SCHEMA = "static.ground-plan/v0"
RECEIPT_SCHEMA = "static.ground-receipt/v0"

RELATIONS = {"aligns_primary", "aligns_candidate", "mixed", "inconclusive"}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _canonical_bytes(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _sha256(value):
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _write_json(value, path: str | Path | None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def validate_packet(packet):
    if not isinstance(packet, dict) or packet.get("schema") != PACKET_SCHEMA:
        raise ValueError("unsupported packet schema")
    if packet.get("id") != PACKET_ID:
        raise ValueError("unexpected packet id")
    if packet.get("core_distinction") != EXPECTED_INVARIANT:
        raise ValueError("MAKE GROUND invariant changed")
    crossings = packet.get("crossings")
    if not isinstance(crossings, dict):
        raise ValueError("crossing contract missing")
    if crossings.get("accepts") != [WORLD_RECEIPT_SCHEMA, FIELD_SCHEMA]:
        raise ValueError("unexpected MAKE GROUND input contract")
    if crossings.get("emits") != [PLAN_SCHEMA, RECEIPT_SCHEMA]:
        raise ValueError("unexpected MAKE GROUND output contract")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    if runtime.get("commands") != ["validate", "plan", "observe", "inspect"]:
        raise ValueError("unexpected runtime command set")
    return packet


def validate_world_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != WORLD_RECEIPT_SCHEMA:
        raise ValueError("unsupported WORLD receipt")
    if receipt.get("packet_id") != "world-001":
        raise ValueError("unexpected WORLD packet")
    if receipt.get("lineage_class") != "independent_candidate":
        raise ValueError("MAKE GROUND crossing requires an independent candidate")
    if receipt.get("independence_status") != "independent_candidate":
        raise ValueError("WORLD independence status is not sufficient")
    if receipt.get("independence_claim_accepted") is not True:
        raise ValueError("WORLD did not accept the independence claim")
    if receipt.get("claim_relation") not in {"contradicts", "corrects"}:
        raise ValueError("MAKE GROUND crossing requires unresolved contradiction or correction")
    if not receipt.get("does_not_establish"):
        raise ValueError("WORLD uncertainty boundary missing")
    return receipt


def _unique_by_id(items, name):
    if not isinstance(items, list) or not items:
        raise ValueError(f"{name} missing")
    ids = [item.get("id") for item in items if isinstance(item, dict)]
    if len(ids) != len(items) or any(not item_id for item_id in ids):
        raise ValueError(f"{name} id missing")
    if len(ids) != len(set(ids)):
        raise ValueError(f"{name} ids duplicated")
    return {item["id"]: item for item in items}


def validate_field(field):
    if not isinstance(field, dict) or field.get("schema") != FIELD_SCHEMA:
        raise ValueError("unsupported field profile")
    for key in ("field_id", "problem_statement"):
        if not isinstance(field.get(key), str) or not field[key]:
            raise ValueError(f"field profile missing: {key}")
    for key in ("current_capabilities", "constraints", "preserve"):
        value = field.get(key)
        if not isinstance(value, list) or not value or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ValueError(f"field profile missing: {key}")

    levers = _unique_by_id(field.get("reversible_levers"), "reversible levers")
    selected_lever = field.get("selected_lever_id")
    if selected_lever not in levers:
        raise ValueError("selected reversible lever does not exist")
    lever = levers[selected_lever]
    if not lever.get("change") or not lever.get("rollback"):
        raise ValueError("selected lever must declare change and rollback")

    channels = _unique_by_id(field.get("observation_channels"), "observation channels")
    selected_channel = field.get("selected_observation_channel_id")
    if selected_channel not in channels:
        raise ValueError("selected observation channel does not exist")
    channel = channels[selected_channel]
    if not channel.get("description") or not channel.get("capture"):
        raise ValueError("selected observation channel incomplete")
    return field


def make_plan(world_receipt, field):
    validate_world_receipt(world_receipt)
    validate_field(field)

    levers = {item["id"]: item for item in field["reversible_levers"]}
    channels = {item["id"]: item for item in field["observation_channels"]}
    lever = levers[field["selected_lever_id"]]
    channel = channels[field["selected_observation_channel_id"]]

    plan = {
        "schema": PLAN_SCHEMA,
        "packet_id": PACKET_ID,
        "status": "proposed",
        "world_source": {
            "primary_source_sha256": world_receipt["primary_source_sha256"],
            "candidate_source_sha256": world_receipt["candidate_source_sha256"],
            "lineage_class": world_receipt["lineage_class"],
            "claim_relation": world_receipt["claim_relation"],
        },
        "field_id": field["field_id"],
        "question": (
            "What becomes easier to observe, preserve, compare, or repeat if this "
            "reversible substrate change is made without deciding the disagreement in advance?"
        ),
        "intervention": {
            "lever_id": lever["id"],
            "change": lever["change"],
            "rollback": lever["rollback"],
        },
        "preserve": list(field["preserve"]),
        "observation": {
            "channel_id": channel["id"],
            "description": channel["description"],
            "capture": channel["capture"],
        },
        "fertility_target": [
            "produce a reusable evidence artifact",
            "make another comparison easier to repeat",
            "preserve enough context for later WITNESS intake",
        ],
        "success_condition": (
            "The selected observation channel produces and preserves at least one "
            "new comparison artifact without requiring either source to be declared correct."
        ),
        "rollback_condition": (
            "Rollback if any preserve condition is violated, the observation channel "
            "cannot produce the declared capture, or the intervention begins deciding "
            "the disputed outcome by construction."
        ),
        "claim_limit": (
            "This plan changes evidence-producing conditions. It does not establish "
            "which source is true or guarantee that the disagreement will resolve."
        ),
        "truth_claimed": False,
    }
    return validate_plan(plan)


def validate_plan(plan):
    if not isinstance(plan, dict) or plan.get("schema") != PLAN_SCHEMA:
        raise ValueError("unsupported ground plan schema")
    if plan.get("packet_id") != PACKET_ID or plan.get("status") != "proposed":
        raise ValueError("ground plan identity mismatch")
    source = plan.get("world_source")
    if not isinstance(source, dict):
        raise ValueError("ground plan WORLD source missing")
    if source.get("lineage_class") != "independent_candidate":
        raise ValueError("ground plan lost independent-candidate lineage")
    if source.get("claim_relation") not in {"contradicts", "corrects"}:
        raise ValueError("ground plan lost unresolved relation")
    intervention = plan.get("intervention")
    if not isinstance(intervention, dict):
        raise ValueError("ground plan intervention missing")
    if not all(intervention.get(key) for key in ("lever_id", "change", "rollback")):
        raise ValueError("ground plan intervention must remain reversible")
    observation = plan.get("observation")
    if not isinstance(observation, dict) or not all(
        observation.get(key) for key in ("channel_id", "description", "capture")
    ):
        raise ValueError("ground plan observation missing")
    if not isinstance(plan.get("preserve"), list) or not plan["preserve"]:
        raise ValueError("ground plan preserve set missing")
    if not isinstance(plan.get("fertility_target"), list) or not plan["fertility_target"]:
        raise ValueError("ground plan fertility target missing")
    if not plan.get("success_condition") or not plan.get("rollback_condition"):
        raise ValueError("ground plan stop conditions missing")
    if not plan.get("claim_limit"):
        raise ValueError("ground plan claim limit missing")
    if plan.get("truth_claimed") is not False:
        raise ValueError("ground plan must not claim truth")
    return plan


def observe_plan(
    plan,
    relation,
    observed,
    evidence_artifacts,
    new_capabilities,
    repeatability_changed,
    comparison_changed,
    maintenance_note,
    rollback_used,
):
    validate_plan(plan)
    if relation not in RELATIONS:
        raise ValueError("invalid observation relation")
    if not observed:
        raise ValueError("observed result missing")
    if not evidence_artifacts:
        raise ValueError("at least one evidence artifact is required")
    if not new_capabilities:
        raise ValueError("at least one new field capability is required")
    if not maintenance_note:
        raise ValueError("maintenance note missing")

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": PACKET_ID,
        "status": "observed",
        "plan_sha256": _sha256(plan),
        "field_id": plan["field_id"],
        "observation_relation": relation,
        "observed": observed,
        "evidence_artifacts": list(evidence_artifacts),
        "fertility_delta": {
            "new_capabilities": list(new_capabilities),
            "repeatability_changed": bool(repeatability_changed),
            "comparison_changed": bool(comparison_changed),
            "maintenance_note": maintenance_note,
        },
        "rollback_used": bool(rollback_used),
        "claim_limit": (
            "This receipt records one field intervention and its observed fertility "
            "delta. It does not establish which upstream source is true."
        ),
        "truth_claimed": False,
        "next_door": (
            "Return the new evidence artifact and this receipt to WITNESS as new source "
            "material, preserving the WORLD receipt and ground-plan ancestry."
        ),
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported ground receipt schema")
    if receipt.get("packet_id") != PACKET_ID or receipt.get("status") != "observed":
        raise ValueError("ground receipt identity mismatch")
    digest = receipt.get("plan_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("ground receipt plan digest missing")
    if receipt.get("observation_relation") not in RELATIONS:
        raise ValueError("invalid ground observation relation")
    if not receipt.get("observed"):
        raise ValueError("ground observed result missing")
    if not isinstance(receipt.get("evidence_artifacts"), list) or not receipt["evidence_artifacts"]:
        raise ValueError("ground evidence artifacts missing")
    delta = receipt.get("fertility_delta")
    if not isinstance(delta, dict):
        raise ValueError("ground fertility delta missing")
    if not isinstance(delta.get("new_capabilities"), list) or not delta["new_capabilities"]:
        raise ValueError("ground new capabilities missing")
    if not isinstance(delta.get("repeatability_changed"), bool):
        raise ValueError("ground repeatability flag missing")
    if not isinstance(delta.get("comparison_changed"), bool):
        raise ValueError("ground comparison flag missing")
    if not delta.get("maintenance_note"):
        raise ValueError("ground maintenance note missing")
    if not isinstance(receipt.get("rollback_used"), bool):
        raise ValueError("ground rollback flag missing")
    if not receipt.get("claim_limit"):
        raise ValueError("ground claim limit missing")
    if receipt.get("truth_claimed") is not False:
        raise ValueError("ground receipt must not claim truth")
    if not receipt.get("next_door"):
        raise ValueError("ground next door missing")
    return receipt


def inspect_receipt(receipt):
    validate_receipt(receipt)
    delta = receipt["fertility_delta"]
    return {
        "schema": "static.ground-inspection/v0",
        "packet_id": PACKET_ID,
        "field_id": receipt["field_id"],
        "observation_relation": receipt["observation_relation"],
        "new_capability_count": len(delta["new_capabilities"]),
        "repeatability_changed": delta["repeatability_changed"],
        "comparison_changed": delta["comparison_changed"],
        "rollback_used": receipt["rollback_used"],
        "truth_claimed": False,
        "reentry_target": "WITNESS",
        "next_door": receipt["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="MAKE GROUND Bridge Packet 006 runtime")
    parser.add_argument("--packet", default="bridge/make-ground.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    plan = sub.add_parser("plan")
    plan.add_argument("world_receipt")
    plan.add_argument("field_profile")
    plan.add_argument("-o", "--out")

    observe = sub.add_parser("observe")
    observe.add_argument("plan")
    observe.add_argument("--relation", choices=sorted(RELATIONS), required=True)
    observe.add_argument("--observed", required=True)
    observe.add_argument("--evidence-artifact", action="append", required=True)
    observe.add_argument("--new-capability", action="append", required=True)
    observe.add_argument("--repeatability-changed", action="store_true")
    observe.add_argument("--comparison-changed", action="store_true")
    observe.add_argument("--maintenance-note", required=True)
    observe.add_argument("--rollback-used", action="store_true")
    observe.add_argument("-o", "--out")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("receipt")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        packet = validate_packet(_read_json(args.packet))
        if args.command == "validate":
            print(f"VALID {packet['id']}: {packet['core_distinction']}")
            return 0
        if args.command == "plan":
            _write_json(
                make_plan(
                    _read_json(args.world_receipt),
                    _read_json(args.field_profile),
                ),
                args.out,
            )
            return 0
        if args.command == "observe":
            _write_json(
                observe_plan(
                    _read_json(args.plan),
                    args.relation,
                    args.observed,
                    args.evidence_artifact,
                    args.new_capability,
                    args.repeatability_changed,
                    args.comparison_changed,
                    args.maintenance_note,
                    args.rollback_used,
                ),
                args.out,
            )
            return 0
        if args.command == "inspect":
            _write_json(inspect_receipt(_read_json(args.receipt)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
