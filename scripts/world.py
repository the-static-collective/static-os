#!/usr/bin/env python3
"""WORLD Bridge Packet 005 runtime.

WORLD compares provenance-bearing sources without inflating their evidence class.
It also accepts WITNESS re-entry and can recognize evidence as genuinely new
while preserving that it was generated downstream of an older disagreement.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PACKET_SCHEMA = "static.bridge-packet/v0"
PACKET_ID = "world-001"
EXPECTED_INVARIANT = "MODEL ≠ WORLD."
WITNESS_INTAKE_SCHEMA = "static.witness-intake/v0"
CANDIDATE_SCHEMA = "static.world-candidate/v0"
RECEIPT_SCHEMA = "static.world-receipt/v0"
WITNESS_REENTRY_SCHEMA = "static.witness-reentry/v0"
RECURSIVE_CANDIDATE_SCHEMA = "static.world-recursive-candidate/v0"
RECURSION_RECEIPT_SCHEMA = "static.world-recursion-receipt/v0"

DIRECT_CHANNELS = {"direct_observation", "independent_measurement"}
CLAIM_RELATIONS = {"corroborates", "contradicts", "corrects", "unrelated"}
UPSTREAM_RELATIONS = {"aligns_primary", "aligns_candidate", "mixed", "inconclusive"}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


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
        raise ValueError("WORLD invariant changed")
    crossings = packet.get("crossings")
    if not isinstance(crossings, dict):
        raise ValueError("crossing contract missing")
    if crossings.get("accepts") != [
        WITNESS_INTAKE_SCHEMA,
        CANDIDATE_SCHEMA,
        WITNESS_REENTRY_SCHEMA,
    ]:
        raise ValueError("unexpected WORLD input contract")
    if crossings.get("emits") != [
        RECEIPT_SCHEMA,
        RECURSIVE_CANDIDATE_SCHEMA,
        RECURSION_RECEIPT_SCHEMA,
    ]:
        raise ValueError("unexpected WORLD output contract")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    if runtime.get("commands") != [
        "validate",
        "compare",
        "candidate-from-reentry",
        "classify-recursive",
        "inspect",
    ]:
        raise ValueError("unexpected runtime command set")
    return packet


def validate_witness_intake(intake):
    if not isinstance(intake, dict) or intake.get("schema") != WITNESS_INTAKE_SCHEMA:
        raise ValueError("unsupported WITNESS intake")
    if intake.get("packet_id") != "witness-001":
        raise ValueError("unexpected WITNESS packet")
    source = intake.get("source")
    if not isinstance(source, dict):
        raise ValueError("WITNESS source missing")
    digest = source.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("WITNESS source digest missing")
    if not intake.get("does_not_establish"):
        raise ValueError("WITNESS claim boundary missing")
    return intake


def validate_candidate(candidate):
    if not isinstance(candidate, dict) or candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("unsupported candidate schema")
    if not candidate.get("candidate_id"):
        raise ValueError("candidate id missing")
    digest = candidate.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("candidate digest missing")
    channel = candidate.get("channel")
    if channel not in {
        "direct_observation",
        "independent_measurement",
        "document",
        "retelling",
        "derived_analysis",
    }:
        raise ValueError("invalid candidate channel")
    roots = candidate.get("ancestry_roots")
    if not isinstance(roots, list) or not roots or len(roots) != len(set(roots)):
        raise ValueError("candidate ancestry roots missing or duplicated")
    derives = candidate.get("derives_from")
    if not isinstance(derives, list) or len(derives) != len(set(derives)):
        raise ValueError("candidate derives_from must be a unique list")
    if candidate.get("claim_relation") not in CLAIM_RELATIONS:
        raise ValueError("invalid claim relation")
    if not isinstance(candidate.get("claim_text"), str) or not candidate["claim_text"]:
        raise ValueError("candidate claim text missing")
    if not isinstance(candidate.get("relation_basis"), str) or not candidate["relation_basis"]:
        raise ValueError("candidate relation basis missing")
    if not isinstance(candidate.get("independence_claim"), bool):
        raise ValueError("candidate independence claim missing")
    return candidate


def classify_lineage(primary_digest, candidate):
    if candidate["source_sha256"] == primary_digest:
        return "same_artifact", "not_independent"

    derives = set(candidate["derives_from"])
    roots = set(candidate["ancestry_roots"])

    if primary_digest in derives:
        return "derived_retelling", "not_independent"

    if primary_digest in roots:
        return "shared_ancestor", "not_independent"

    if candidate["channel"] in DIRECT_CHANNELS:
        return "independent_candidate", "independent_candidate"

    return "lineage_unknown", "unknown"


def compare(intake, candidate):
    validate_witness_intake(intake)
    validate_candidate(candidate)

    primary_digest = intake["source"]["sha256"]
    lineage_class, independence_status = classify_lineage(
        primary_digest, candidate
    )

    accepted = independence_status == "independent_candidate"
    if candidate["independence_claim"] and not accepted:
        raise ValueError(
            "candidate claims independence but the declared lineage does not support it"
        )

    establishes = [
        "A WITNESS intake and an additional candidate source were compared.",
        f"Lineage classification: {lineage_class}.",
        f"Claim relation was declared as: {candidate['claim_relation']}.",
    ]
    if accepted:
        establishes.append(
            "The declared source path is a candidate for independent contact because it is direct or measured and does not declare the primary source as an ancestor."
        )
    else:
        establishes.append(
            "The comparison does not currently warrant an independent-contact label."
        )

    does_not = [
        "The candidate source is correct.",
        "The primary source is correct.",
        "Agreement proves truth.",
        "Contradiction proves independence.",
        "A candidate independent path has been externally audited.",
    ]

    if accepted:
        next_door = (
            "Preserve both sources and test the candidate's ancestry declaration or acquire another source without rewriting either record."
        )
    elif independence_status == "not_independent":
        next_door = (
            "Do not count this candidate as a second witness; acquire a source with a distinct evidence path."
        )
    else:
        next_door = (
            "Ancestry remains insufficiently established; gather provenance before claiming independence."
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": PACKET_ID,
        "primary_source_sha256": primary_digest,
        "candidate_source_sha256": candidate["source_sha256"],
        "lineage_class": lineage_class,
        "claim_relation": candidate["claim_relation"],
        "independence_status": independence_status,
        "independence_claim_accepted": accepted,
        "establishes": establishes,
        "does_not_establish": does_not,
        "next_door": next_door,
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported WORLD receipt schema")
    if receipt.get("packet_id") != PACKET_ID:
        raise ValueError("WORLD receipt packet mismatch")
    if receipt.get("lineage_class") not in {
        "same_artifact",
        "derived_retelling",
        "shared_ancestor",
        "independent_candidate",
        "lineage_unknown",
    }:
        raise ValueError("invalid lineage class")
    if receipt.get("claim_relation") not in CLAIM_RELATIONS:
        raise ValueError("invalid claim relation")
    if receipt.get("independence_status") not in {
        "not_independent",
        "independent_candidate",
        "unknown",
    }:
        raise ValueError("invalid independence status")
    accepted = receipt.get("independence_claim_accepted")
    if not isinstance(accepted, bool):
        raise ValueError("independence acceptance flag missing")
    if accepted != (receipt["independence_status"] == "independent_candidate"):
        raise ValueError("independence acceptance contradicts status")
    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("WORLD establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("WORLD does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("WORLD next door missing")
    return receipt


def validate_reentry(reentry):
    if not isinstance(reentry, dict) or reentry.get("schema") != WITNESS_REENTRY_SCHEMA:
        raise ValueError("unsupported WITNESS re-entry")
    if reentry.get("packet_id") != "witness-001":
        raise ValueError("unexpected WITNESS re-entry packet")

    bundle = reentry.get("source_bundle")
    if not isinstance(bundle, dict):
        raise ValueError("WITNESS re-entry source bundle missing")

    ground = bundle.get("ground_receipt")
    artifact = bundle.get("evidence_artifact")
    ancestry = bundle.get("ancestry")
    if not isinstance(ground, dict) or ground.get("schema") != "static.ground-receipt/v0":
        raise ValueError("re-entry ground receipt missing")
    if not isinstance(artifact, dict) or artifact.get("schema") != "static.evidence-artifact/v0":
        raise ValueError("re-entry evidence artifact missing")
    if not isinstance(ancestry, dict):
        raise ValueError("re-entry ancestry missing")

    for value in (
        ground.get("sha256"),
        artifact.get("sha256"),
        ancestry.get("ground_plan_sha256"),
        ancestry.get("world_primary_source_sha256"),
        ancestry.get("world_candidate_source_sha256"),
    ):
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError("re-entry ancestry digest missing")

    records = reentry.get("records")
    if not isinstance(records, list):
        raise ValueError("re-entry records missing")
    by_kind = {record.get("kind"): record for record in records if isinstance(record, dict)}
    required = {
        "ground_observation",
        "evidence_artifact",
        "observation_relation",
        "fertility_delta",
        "intervention_lineage",
        "claim_limit",
    }
    if set(by_kind) != required:
        raise ValueError("unexpected WITNESS re-entry record set")
    if by_kind["evidence_artifact"].get("claim_class") != "source_artifact":
        raise ValueError("re-entry artifact lost source class")
    if by_kind["observation_relation"].get("claim_class") != "derivative_interpretation":
        raise ValueError("re-entry relation lost interpretation class")
    if by_kind["observation_relation"].get("value") not in UPSTREAM_RELATIONS:
        raise ValueError("re-entry upstream relation invalid")
    if by_kind["intervention_lineage"].get("claim_class") != "intervention_record":
        raise ValueError("re-entry intervention lineage missing")
    if not reentry.get("does_not_establish"):
        raise ValueError("re-entry claim limit boundary missing")
    return reentry


def candidate_from_reentry(reentry):
    validate_reentry(reentry)
    bundle = reentry["source_bundle"]
    ancestry = bundle["ancestry"]
    records = {record["kind"]: record for record in reentry["records"]}

    candidate = {
        "schema": RECURSIVE_CANDIDATE_SCHEMA,
        "candidate_id": f"recursive-{bundle['evidence_artifact']['artifact_id']}",
        "source_sha256": bundle["evidence_artifact"]["sha256"],
        "source_schema": bundle["evidence_artifact"]["schema"],
        "novelty_status": "new_artifact",
        "observation_status": "fresh_capture",
        "generation_ancestry": {
            "ground_receipt_sha256": bundle["ground_receipt"]["sha256"],
            "ground_plan_sha256": ancestry["ground_plan_sha256"],
            "world_primary_source_sha256": ancestry["world_primary_source_sha256"],
            "world_candidate_source_sha256": ancestry["world_candidate_source_sha256"],
        },
        "relation_to_upstream": records["observation_relation"]["value"],
        "independence_status": "not_independent_by_generation",
        "independence_claim": False,
        "claim_limit": (
            "This is a new captured artifact generated through a MAKE GROUND intervention "
            "that was itself caused by the upstream WORLD disagreement. Newness does not "
            "make the artifact independent of that generation ancestry."
        ),
    }
    return validate_recursive_candidate(candidate)


def validate_recursive_candidate(candidate):
    if not isinstance(candidate, dict) or candidate.get("schema") != RECURSIVE_CANDIDATE_SCHEMA:
        raise ValueError("unsupported recursive candidate schema")
    if not candidate.get("candidate_id"):
        raise ValueError("recursive candidate id missing")
    digest = candidate.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("recursive candidate source digest missing")
    if candidate.get("source_schema") != "static.evidence-artifact/v0":
        raise ValueError("recursive candidate source schema mismatch")
    if candidate.get("novelty_status") != "new_artifact":
        raise ValueError("recursive candidate lost novelty")
    if candidate.get("observation_status") != "fresh_capture":
        raise ValueError("recursive candidate lost fresh-capture status")
    ancestry = candidate.get("generation_ancestry")
    if not isinstance(ancestry, dict):
        raise ValueError("recursive candidate generation ancestry missing")
    required = (
        "ground_receipt_sha256",
        "ground_plan_sha256",
        "world_primary_source_sha256",
        "world_candidate_source_sha256",
    )
    for key in required:
        value = ancestry.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"recursive candidate ancestry missing: {key}")
    if candidate.get("relation_to_upstream") not in UPSTREAM_RELATIONS:
        raise ValueError("recursive candidate relation invalid")
    if candidate.get("independence_status") != "not_independent_by_generation":
        raise ValueError("recursive candidate independence status invalid")
    if candidate.get("independence_claim") is not False:
        raise ValueError("recursive candidate must not claim independence")
    if not candidate.get("claim_limit"):
        raise ValueError("recursive candidate claim limit missing")
    return candidate


def classify_recursive(candidate):
    validate_recursive_candidate(candidate)
    ancestry = candidate["generation_ancestry"]

    receipt = {
        "schema": RECURSION_RECEIPT_SCHEMA,
        "packet_id": PACKET_ID,
        "candidate_source_sha256": candidate["source_sha256"],
        "lineage_class": "generated_downstream",
        "novelty_status": candidate["novelty_status"],
        "observation_status": candidate["observation_status"],
        "relation_to_upstream": candidate["relation_to_upstream"],
        "independence_status": "not_independent_by_generation",
        "counts_as_second_witness": False,
        "upstream_ancestry_preserved": True,
        "establishes": [
            "A new evidence artifact exists and has its own source fingerprint.",
            "The artifact was produced by a fresh capture step.",
            "The artifact was generated downstream of the prior WORLD disagreement.",
            "Both prior WORLD source fingerprints remain in the generation ancestry.",
            f"Relation to the upstream disagreement is preserved as: {candidate['relation_to_upstream']}.",
        ],
        "does_not_establish": [
            "The new artifact is an unrelated independent witness.",
            "Fresh capture means causal or epistemic independence from the intervention that produced it.",
            "The new artifact is correct.",
            "The prior primary source is correct.",
            "The prior candidate source is correct.",
            "A new artifact may be counted as a second witness merely because it has a new hash.",
        ],
        "next_door": (
            "Use the new artifact as new source material while retaining its generated-downstream "
            "classification. If independent confirmation is needed, acquire a source whose generation "
            "path does not descend from this disagreement."
        ),
    }

    if ancestry["world_primary_source_sha256"] == ancestry["world_candidate_source_sha256"]:
        raise ValueError("recursive ancestry collapsed upstream WORLD sources")

    return validate_recursion_receipt(receipt)


def validate_recursion_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECURSION_RECEIPT_SCHEMA:
        raise ValueError("unsupported WORLD recursion receipt")
    if receipt.get("packet_id") != PACKET_ID:
        raise ValueError("WORLD recursion receipt packet mismatch")
    if receipt.get("lineage_class") != "generated_downstream":
        raise ValueError("recursive lineage class drifted")
    if receipt.get("novelty_status") != "new_artifact":
        raise ValueError("recursive novelty status drifted")
    if receipt.get("observation_status") != "fresh_capture":
        raise ValueError("recursive observation status drifted")
    if receipt.get("relation_to_upstream") not in UPSTREAM_RELATIONS:
        raise ValueError("recursive relation invalid")
    if receipt.get("independence_status") != "not_independent_by_generation":
        raise ValueError("recursive independence status drifted")
    if receipt.get("counts_as_second_witness") is not False:
        raise ValueError("generated-downstream evidence cannot count as a second witness")
    if receipt.get("upstream_ancestry_preserved") is not True:
        raise ValueError("recursive WORLD receipt lost upstream ancestry")
    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("recursive WORLD establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("recursive WORLD does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("recursive WORLD next door missing")
    return receipt


def inspect_receipt(receipt):
    """Backward-compatible inspector for the original WORLD receipt."""
    validate_receipt(receipt)
    return {
        "schema": "static.world-inspection/v0",
        "packet_id": PACKET_ID,
        "lineage_axis": receipt["lineage_class"],
        "claim_axis": receipt["claim_relation"],
        "independence_status": receipt["independence_status"],
        "counts_as_second_witness": receipt["independence_claim_accepted"],
        "truth_claimed": False,
        "next_door": receipt["next_door"],
    }


def inspect_any(value):
    if not isinstance(value, dict):
        raise ValueError("unsupported WORLD inspection input")
    schema = value.get("schema")
    if schema == RECEIPT_SCHEMA:
        return inspect_receipt(value)
    if schema == RECURSION_RECEIPT_SCHEMA:
        validate_recursion_receipt(value)
        return {
            "schema": "static.world-recursion-inspection/v0",
            "packet_id": PACKET_ID,
            "lineage_axis": value["lineage_class"],
            "novelty_axis": value["novelty_status"],
            "observation_axis": value["observation_status"],
            "relation_axis": value["relation_to_upstream"],
            "independence_status": value["independence_status"],
            "counts_as_second_witness": value["counts_as_second_witness"],
            "upstream_ancestry_preserved": value["upstream_ancestry_preserved"],
            "truth_claimed": False,
            "next_door": value["next_door"],
        }
    raise ValueError("unsupported WORLD inspection schema")


def build_parser():
    parser = argparse.ArgumentParser(description="WORLD Bridge Packet 005 runtime")
    parser.add_argument("--packet", default="bridge/world.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    compare_cmd = sub.add_parser("compare")
    compare_cmd.add_argument("witness_intake")
    compare_cmd.add_argument("candidate")
    compare_cmd.add_argument("-o", "--out")

    recandidate = sub.add_parser("candidate-from-reentry")
    recandidate.add_argument("witness_reentry")
    recandidate.add_argument("-o", "--out")

    recursive = sub.add_parser("classify-recursive")
    recursive.add_argument("candidate")
    recursive.add_argument("-o", "--out")

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
        if args.command == "compare":
            _write_json(
                compare(
                    _read_json(args.witness_intake),
                    _read_json(args.candidate),
                ),
                args.out,
            )
            return 0
        if args.command == "candidate-from-reentry":
            _write_json(
                candidate_from_reentry(_read_json(args.witness_reentry)),
                args.out,
            )
            return 0
        if args.command == "classify-recursive":
            _write_json(
                classify_recursive(_read_json(args.candidate)),
                args.out,
            )
            return 0
        if args.command == "inspect":
            _write_json(inspect_any(_read_json(args.receipt)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
