#!/usr/bin/env python3
"""WORLD Bridge Packet 005 runtime.

WORLD compares a provenance-bearing WITNESS intake with one additional source.
It keeps lineage relation separate from claim relation and refuses unsupported
independence claims.
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

DIRECT_CHANNELS = {"direct_observation", "independent_measurement"}
CLAIM_RELATIONS = {"corroborates", "contradicts", "corrects", "unrelated"}


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
    ]:
        raise ValueError("unexpected WORLD input contract")
    if crossings.get("emits") != [RECEIPT_SCHEMA]:
        raise ValueError("unexpected WORLD output contract")
    runtime = packet.get("runtime")
    if not isinstance(runtime, dict):
        raise ValueError("runtime contract missing")
    if runtime.get("proposal_only") is not True:
        raise ValueError("runtime must remain proposal-only")
    if runtime.get("automatic_external_effects") is not False:
        raise ValueError("runtime must not claim automatic external effects")
    if runtime.get("commands") != ["validate", "compare", "inspect"]:
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


def inspect_receipt(receipt):
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


def build_parser():
    parser = argparse.ArgumentParser(description="WORLD Bridge Packet 005 runtime")
    parser.add_argument("--packet", default="bridge/world.packet.json")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate")

    compare_cmd = sub.add_parser("compare")
    compare_cmd.add_argument("witness_intake")
    compare_cmd.add_argument("candidate")
    compare_cmd.add_argument("-o", "--out")

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
            result = compare(
                _read_json(args.witness_intake),
                _read_json(args.candidate),
            )
            _write_json(result, args.out)
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
