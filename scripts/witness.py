#!/usr/bin/env python3
"""WITNESS Bridge Packet 003 runtime.

WITNESS ingests provenance-bearing artifacts without upgrading their claims.
It supports the first NAV -> WITNESS crossing and MAKE GROUND -> WITNESS
re-entry while preserving the ancestry that produced the new source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

PACKET_SCHEMA = "static.bridge-packet/v0"
PACKET_ID = "witness-001"
EXPECTED_INVARIANT = "SOURCE ≠ STORY."
NAV_RECEIPT_SCHEMA = "static.nav-receipt/v0"
INTAKE_SCHEMA = "static.witness-intake/v0"
GROUND_RECEIPT_SCHEMA = "static.ground-receipt/v0"
EVIDENCE_ARTIFACT_SCHEMA = "static.evidence-artifact/v0"
REENTRY_SCHEMA = "static.witness-reentry/v0"


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
        raise ValueError("WITNESS invariant changed")
    crossings = packet.get("crossings")
    if not isinstance(crossings, dict):
        raise ValueError("crossing contract missing")
    expected_accepts = [
        NAV_RECEIPT_SCHEMA,
        GROUND_RECEIPT_SCHEMA,
        EVIDENCE_ARTIFACT_SCHEMA,
    ]
    if crossings.get("accepts") != expected_accepts:
        raise ValueError("unexpected WITNESS input contract")
    if crossings.get("emits") != [INTAKE_SCHEMA, REENTRY_SCHEMA]:
        raise ValueError("unexpected WITNESS output contract")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    if runtime.get("commands") != ["validate", "intake", "reenter", "inspect"]:
        raise ValueError("unexpected runtime command set")
    return packet


def validate_nav_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != NAV_RECEIPT_SCHEMA:
        raise ValueError("unsupported source schema")
    if receipt.get("packet_id") != "nav-001":
        raise ValueError("source packet mismatch")
    if receipt.get("status") != "contacted":
        raise ValueError("WITNESS intake requires a contacted NAV receipt")
    for key in (
        "heading",
        "bounded_move",
        "stop_condition",
        "claim_limit",
        "observed",
        "delta",
        "next_heading",
    ):
        if not isinstance(receipt.get(key), str) or not receipt[key]:
            raise ValueError(f"contacted NAV receipt missing: {key}")
    for key in ("preserve", "aperture"):
        if not isinstance(receipt.get(key), list) or not receipt[key]:
            raise ValueError(f"contacted NAV receipt missing: {key}")
    return receipt


def validate_intake(intake):
    if not isinstance(intake, dict) or intake.get("schema") != INTAKE_SCHEMA:
        raise ValueError("unsupported intake schema")
    if intake.get("packet_id") != PACKET_ID:
        raise ValueError("intake packet mismatch")
    source = intake.get("source")
    if not isinstance(source, dict):
        raise ValueError("source record missing")
    if source.get("schema") != NAV_RECEIPT_SCHEMA:
        raise ValueError("unexpected source schema")
    if source.get("packet_id") != "nav-001" or source.get("status") != "contacted":
        raise ValueError("unexpected NAV source identity")
    digest = source.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("source digest missing")
    records = intake.get("records")
    if not isinstance(records, list) or len(records) != 4:
        raise ValueError("expected four source-preserving records")
    expected_classes = [
        "source_record",
        "derivative_interpretation",
        "orientation_proposal",
        "source_limit",
    ]
    if [record.get("claim_class") for record in records] != expected_classes:
        raise ValueError("claim classes drifted or collapsed")
    for record in records:
        if not isinstance(record.get("value"), str):
            raise ValueError("record value must remain text")
        if not record.get("source_field"):
            raise ValueError("record source field missing")
    establishes = intake.get("establishes")
    does_not = intake.get("does_not_establish")
    if not isinstance(establishes, list) or not establishes:
        raise ValueError("establishes boundary missing")
    if not isinstance(does_not, list) or not does_not:
        raise ValueError("does-not-establish boundary missing")
    if not isinstance(intake.get("corrections"), list):
        raise ValueError("corrections must be a list")
    return intake


def intake_nav(receipt):
    validate_nav_receipt(receipt)
    intake = {
        "schema": INTAKE_SCHEMA,
        "packet_id": PACKET_ID,
        "source": {
            "schema": receipt["schema"],
            "packet_id": receipt["packet_id"],
            "status": receipt["status"],
            "sha256": _sha256(receipt),
        },
        "records": [
            {
                "kind": "reported_observation",
                "value": receipt["observed"],
                "source_field": "observed",
                "claim_class": "source_record",
            },
            {
                "kind": "reported_delta",
                "value": receipt["delta"],
                "source_field": "delta",
                "claim_class": "derivative_interpretation",
            },
            {
                "kind": "next_heading",
                "value": receipt["next_heading"],
                "source_field": "next_heading",
                "claim_class": "orientation_proposal",
            },
            {
                "kind": "claim_limit",
                "value": receipt["claim_limit"],
                "source_field": "claim_limit",
                "claim_class": "source_limit",
            },
        ],
        "establishes": [
            "A contacted NAV receipt artifact was ingested.",
            "The source artifact records the preserved observation text.",
            "The source artifact records a delta interpretation and a next-heading proposal.",
            "The source artifact carries an explicit claim limit.",
        ],
        "does_not_establish": [
            "The reported outside event is independently verified by WITNESS.",
            "The source's delta interpretation is correct.",
            "The source's next-heading proposal should be followed.",
            "The source's world-contact claim has been independently reproduced.",
        ],
        "corrections": [],
    }
    return validate_intake(intake)


def validate_ground_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != GROUND_RECEIPT_SCHEMA:
        raise ValueError("unsupported ground receipt schema")
    if receipt.get("packet_id") != "make-ground-001" or receipt.get("status") != "observed":
        raise ValueError("unexpected MAKE GROUND receipt identity")
    if receipt.get("truth_claimed") is not False:
        raise ValueError("ground receipt must not claim truth")
    plan_digest = receipt.get("plan_sha256")
    if not isinstance(plan_digest, str) or len(plan_digest) != 64:
        raise ValueError("ground receipt plan digest missing")
    ancestry = receipt.get("ancestry")
    if not isinstance(ancestry, dict):
        raise ValueError("ground receipt ancestry missing")
    if ancestry.get("ground_plan_sha256") != plan_digest:
        raise ValueError("ground receipt plan ancestry mismatch")
    for key in ("world_primary_source_sha256", "world_candidate_source_sha256"):
        value = ancestry.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"ground receipt ancestry missing: {key}")
    if not receipt.get("observed") or not receipt.get("claim_limit"):
        raise ValueError("ground receipt observation boundary missing")
    if not isinstance(receipt.get("evidence_artifacts"), list) or not receipt["evidence_artifacts"]:
        raise ValueError("ground receipt evidence artifact list missing")
    if not isinstance(receipt.get("fertility_delta"), dict):
        raise ValueError("ground receipt fertility delta missing")
    return receipt


def validate_evidence_artifact(artifact):
    if not isinstance(artifact, dict) or artifact.get("schema") != EVIDENCE_ARTIFACT_SCHEMA:
        raise ValueError("unsupported evidence artifact schema")
    for key in ("artifact_id", "artifact_kind", "capture_channel", "claim_limit"):
        if not isinstance(artifact.get(key), str) or not artifact[key]:
            raise ValueError(f"evidence artifact missing: {key}")
    if not isinstance(artifact.get("content"), dict):
        raise ValueError("evidence artifact content missing")
    return artifact


def validate_reentry(reentry):
    if not isinstance(reentry, dict) or reentry.get("schema") != REENTRY_SCHEMA:
        raise ValueError("unsupported WITNESS re-entry schema")
    if reentry.get("packet_id") != PACKET_ID:
        raise ValueError("WITNESS re-entry packet mismatch")
    bundle = reentry.get("source_bundle")
    if not isinstance(bundle, dict):
        raise ValueError("re-entry source bundle missing")
    ground = bundle.get("ground_receipt")
    artifact = bundle.get("evidence_artifact")
    ancestry = bundle.get("ancestry")
    if not isinstance(ground, dict) or ground.get("schema") != GROUND_RECEIPT_SCHEMA:
        raise ValueError("re-entry ground source missing")
    if not isinstance(artifact, dict) or artifact.get("schema") != EVIDENCE_ARTIFACT_SCHEMA:
        raise ValueError("re-entry evidence source missing")
    if not isinstance(ancestry, dict):
        raise ValueError("re-entry ancestry missing")
    for digest in (
        ground.get("sha256"),
        artifact.get("sha256"),
        ancestry.get("ground_plan_sha256"),
        ancestry.get("world_primary_source_sha256"),
        ancestry.get("world_candidate_source_sha256"),
    ):
        if not isinstance(digest, str) or len(digest) != 64:
            raise ValueError("re-entry digest missing")
    records = reentry.get("records")
    if not isinstance(records, list) or len(records) != 6:
        raise ValueError("expected six re-entry records")
    expected_classes = [
        "source_record",
        "source_artifact",
        "derivative_interpretation",
        "derivative_interpretation",
        "intervention_record",
        "source_limit",
    ]
    if [record.get("claim_class") for record in records] != expected_classes:
        raise ValueError("re-entry claim classes drifted or collapsed")
    for record in records:
        if not isinstance(record.get("value"), str):
            raise ValueError("re-entry record value must remain text")
        if not record.get("source_field"):
            raise ValueError("re-entry record source field missing")
    if not isinstance(reentry.get("establishes"), list) or not reentry["establishes"]:
        raise ValueError("re-entry establishes boundary missing")
    if not isinstance(reentry.get("does_not_establish"), list) or not reentry["does_not_establish"]:
        raise ValueError("re-entry does-not-establish boundary missing")
    if not isinstance(reentry.get("corrections"), list):
        raise ValueError("re-entry corrections must be a list")
    if not reentry.get("next_door"):
        raise ValueError("re-entry next door missing")
    return reentry


def reenter_ground(receipt, artifact):
    validate_ground_receipt(receipt)
    validate_evidence_artifact(artifact)

    artifact_names = set(receipt["evidence_artifacts"])
    if artifact["artifact_id"] not in artifact_names:
        raise ValueError("evidence artifact is not declared by the ground receipt")

    ancestry = receipt["ancestry"]
    fertility = receipt["fertility_delta"]

    reentry = {
        "schema": REENTRY_SCHEMA,
        "packet_id": PACKET_ID,
        "source_bundle": {
            "ground_receipt": {
                "schema": receipt["schema"],
                "packet_id": receipt["packet_id"],
                "status": receipt["status"],
                "sha256": _sha256(receipt),
            },
            "evidence_artifact": {
                "schema": artifact["schema"],
                "artifact_id": artifact["artifact_id"],
                "sha256": _sha256(artifact),
            },
            "ancestry": {
                "ground_plan_sha256": ancestry["ground_plan_sha256"],
                "world_primary_source_sha256": ancestry["world_primary_source_sha256"],
                "world_candidate_source_sha256": ancestry["world_candidate_source_sha256"],
            },
        },
        "records": [
            {
                "kind": "ground_observation",
                "value": receipt["observed"],
                "source_field": "ground_receipt.observed",
                "claim_class": "source_record",
            },
            {
                "kind": "evidence_artifact",
                "value": json.dumps(artifact["content"], sort_keys=True),
                "source_field": f"evidence_artifact:{artifact['artifact_id']}",
                "claim_class": "source_artifact",
            },
            {
                "kind": "observation_relation",
                "value": receipt["observation_relation"],
                "source_field": "ground_receipt.observation_relation",
                "claim_class": "derivative_interpretation",
            },
            {
                "kind": "fertility_delta",
                "value": json.dumps(fertility, sort_keys=True),
                "source_field": "ground_receipt.fertility_delta",
                "claim_class": "derivative_interpretation",
            },
            {
                "kind": "intervention_lineage",
                "value": (
                    f"field={receipt['field_id']}; "
                    f"ground_plan_sha256={ancestry['ground_plan_sha256']}"
                ),
                "source_field": "ground_receipt.ancestry",
                "claim_class": "intervention_record",
            },
            {
                "kind": "claim_limit",
                "value": receipt["claim_limit"] + " " + artifact["claim_limit"],
                "source_field": "ground_receipt.claim_limit + evidence_artifact.claim_limit",
                "claim_class": "source_limit",
            },
        ],
        "establishes": [
            "A MAKE GROUND receipt and its declared evidence artifact were ingested together.",
            "The new observation text is preserved separately from its observation-relation classification.",
            "The evidence artifact is fingerprinted separately from the ground receipt.",
            "The ground-plan fingerprint and both WORLD source fingerprints survive re-entry.",
            "The field intervention and its fertility delta remain distinct from upstream truth claims.",
        ],
        "does_not_establish": [
            "The new evidence artifact independently verifies either upstream source.",
            "A mixed observation relation resolves the upstream contradiction.",
            "The fertility delta proves that the intervention was the best possible intervention.",
            "The preserved ancestry is a complete causal history of the event.",
        ],
        "corrections": [],
        "next_door": (
            "Treat this re-entry as new source material. Compare the new evidence artifact "
            "against prior sources through WITNESS/WORLD without rewriting the preserved ancestry."
        ),
    }
    return validate_reentry(reentry)


def inspect_intake(intake):
    validate_intake(intake)
    classes = Counter(record["claim_class"] for record in intake["records"])
    return {
        "schema": "static.witness-inspection/v0",
        "packet_id": PACKET_ID,
        "source_sha256": intake["source"]["sha256"],
        "record_count": len(intake["records"]),
        "claim_classes": dict(sorted(classes.items())),
        "establishes_count": len(intake["establishes"]),
        "does_not_establish_count": len(intake["does_not_establish"]),
        "correction_count": len(intake["corrections"]),
        "independent_verification_claimed": False,
        "next_door": "Acquire a genuinely independent witness or preserve a correction without rewriting this source.",
    }


def inspect_reentry(reentry):
    validate_reentry(reentry)
    classes = Counter(record["claim_class"] for record in reentry["records"])
    ancestry = reentry["source_bundle"]["ancestry"]
    return {
        "schema": "static.witness-reentry-inspection/v0",
        "packet_id": PACKET_ID,
        "record_count": len(reentry["records"]),
        "claim_classes": dict(sorted(classes.items())),
        "ground_receipt_sha256": reentry["source_bundle"]["ground_receipt"]["sha256"],
        "evidence_artifact_sha256": reentry["source_bundle"]["evidence_artifact"]["sha256"],
        "ancestry_edge_count": len(ancestry),
        "upstream_world_sources_preserved": True,
        "independent_verification_claimed": False,
        "loop_closed": True,
        "next_door": reentry["next_door"],
    }


def inspect_any(value):
    if isinstance(value, dict) and value.get("schema") == INTAKE_SCHEMA:
        return inspect_intake(value)
    if isinstance(value, dict) and value.get("schema") == REENTRY_SCHEMA:
        return inspect_reentry(value)
    raise ValueError("unsupported WITNESS inspection input")


def build_parser():
    parser = argparse.ArgumentParser(description="WITNESS Bridge Packet 003 runtime")
    parser.add_argument("--packet", default="bridge/witness.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    intake = sub.add_parser("intake")
    intake.add_argument("source")
    intake.add_argument("-o", "--out")

    reenter = sub.add_parser("reenter")
    reenter.add_argument("ground_receipt")
    reenter.add_argument("evidence_artifact")
    reenter.add_argument("-o", "--out")

    inspect = sub.add_parser("inspect")
    inspect.add_argument("source")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        packet = validate_packet(_read_json(args.packet))
        if args.command == "validate":
            print(f"VALID {packet['id']}: {packet['core_distinction']}")
            return 0
        if args.command == "intake":
            _write_json(intake_nav(_read_json(args.source)), args.out)
            return 0
        if args.command == "reenter":
            _write_json(
                reenter_ground(
                    _read_json(args.ground_receipt),
                    _read_json(args.evidence_artifact),
                ),
                args.out,
            )
            return 0
        if args.command == "inspect":
            _write_json(inspect_any(_read_json(args.source)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
