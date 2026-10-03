#!/usr/bin/env python3
"""WORLD classifier for a fresh contact produced from composed navigation ground.

The contact is genuinely new and fresh. Its selection/orientation path is known
to descend from prior composed history. Measurement independence is left
unknown unless separately audited; therefore independent confirmation is not
established by freshness alone.
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


witness_composed = _load(
    "static_os_witness_composed_for_world",
    "scripts/witness_composed.py",
)

WITNESS_SCHEMA = "static.witness-composed-intake/v0"
CANDIDATE_SCHEMA = "static.world-composed-contact-candidate/v0"
RECEIPT_SCHEMA = "static.world-composed-contact-receipt/v0"
RELATION_KINDS = {"branch_continuation", "open_branch"}

CANDIDATE_KEYS = {
    "schema",
    "candidate_id",
    "source_sha256",
    "source_schema",
    "novelty_status",
    "observation_status",
    "orientation_ancestry",
    "selection_independence",
    "measurement_independence",
    "confirmation_status",
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


def candidate_from_witness(intake):
    witness_composed.validate_composed_intake(intake)

    provenance = intake["origin_provenance"]
    source = intake["source"]

    candidate = {
        "schema": CANDIDATE_SCHEMA,
        "candidate_id": f"composed-contact-{source['sha256'][:16]}",
        "source_sha256": source["sha256"],
        "source_schema": source["schema"],
        "novelty_status": "new_source_artifact",
        "observation_status": "fresh_world_contact",
        "orientation_ancestry": {
            "cycle_sha256": provenance["cycle_sha256"],
            "origin_sha256": provenance["origin_sha256"],
            "source_generation_sha256": provenance["source_generation_sha256"],
            "admission_sha256": provenance["admission_sha256"],
            "weave_capsule_sha256": provenance["weave_capsule_sha256"],
            "parent_set_sha256": provenance["parent_set_sha256"],
            "weave_ledger_sha256": provenance["weave_ledger_sha256"],
            "root_cycle_digest": provenance["root_cycle_digest"],
            "relation_kinds": list(provenance["relation_kinds"]),
        },
        "selection_independence": "not_independent_of_orientation",
        "measurement_independence": "unknown",
        "confirmation_status": "independent_confirmation_not_established",
        "claim_limit": (
            "This is a new source artifact from a fresh world-contact event, but the "
            "question, bounded move, and observation opportunity were selected from an "
            "admitted composed history. Freshness therefore does not establish "
            "independence from the history that oriented the contact. Measurement "
            "independence remains unknown until separately audited."
        ),
    }
    return validate_candidate(candidate)


def validate_candidate(candidate):
    if not isinstance(candidate, dict) or candidate.get("schema") != CANDIDATE_SCHEMA:
        raise ValueError("unsupported composed-contact candidate schema")
    if set(candidate) != CANDIDATE_KEYS:
        raise ValueError("composed-contact candidate shape drifted")
    if not candidate.get("candidate_id"):
        raise ValueError("composed-contact candidate id missing")
    digest = candidate.get("source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("composed-contact source digest missing")
    if candidate.get("source_schema") != "static.nav-receipt/v0":
        raise ValueError("composed-contact source schema mismatch")
    if candidate.get("novelty_status") != "new_source_artifact":
        raise ValueError("composed-contact novelty status drifted")
    if candidate.get("observation_status") != "fresh_world_contact":
        raise ValueError("composed-contact observation status drifted")

    ancestry = candidate.get("orientation_ancestry")
    if not isinstance(ancestry, dict):
        raise ValueError("composed-contact orientation ancestry missing")
    for key in (
        "cycle_sha256",
        "origin_sha256",
        "source_generation_sha256",
        "admission_sha256",
        "weave_capsule_sha256",
        "parent_set_sha256",
        "weave_ledger_sha256",
        "root_cycle_digest",
    ):
        value = ancestry.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"composed-contact ancestry missing: {key}")
    kinds = ancestry.get("relation_kinds")
    if not isinstance(kinds, list) or set(kinds) != RELATION_KINDS or len(kinds) != 2:
        raise ValueError("composed-contact relation kinds invalid")

    if candidate.get("selection_independence") != "not_independent_of_orientation":
        raise ValueError("composed-contact selection independence drifted")
    if candidate.get("measurement_independence") != "unknown":
        raise ValueError("measurement independence cannot be inferred from WITNESS intake")
    if candidate.get("confirmation_status") != "independent_confirmation_not_established":
        raise ValueError("composed-contact confirmation status drifted")
    if not candidate.get("claim_limit"):
        raise ValueError("composed-contact claim limit missing")
    return candidate


def classify(candidate):
    validate_candidate(candidate)

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": "world-001",
        "candidate_source_sha256": candidate["source_sha256"],
        "lineage_class": "oriented_downstream",
        "novelty_status": candidate["novelty_status"],
        "observation_status": candidate["observation_status"],
        "selection_independence": candidate["selection_independence"],
        "measurement_independence": candidate["measurement_independence"],
        "confirmation_status": candidate["confirmation_status"],
        "counts_as_independent_confirmation": False,
        "typed_origin_preserved": True,
        "establishes": [
            "A distinct source artifact exists with its own fingerprint.",
            "The source records a fresh world-contact event.",
            "The contact was selected and oriented downstream of an admitted composed navigation history.",
            "The typed composed-origin addresses remain available through WITNESS provenance.",
            "Selection independence is not present because the contact opportunity descends from the composed orientation.",
            "Measurement independence remains unknown because it has not been separately audited.",
        ],
        "does_not_establish": [
            "The fresh contact is an independent confirmation of the history that oriented it.",
            "A new source hash proves epistemic independence.",
            "Fresh observation proves independent measurement conditions.",
            "The composed history is correct.",
            "The fresh contact is correct.",
            "The still-open branch is closed or disfavored.",
            "Unknown measurement independence may be treated as independent measurement.",
        ],
        "next_door": (
            "Preserve the fresh contact as new source material without counting it as "
            "independent confirmation. If independent confirmation matters, audit the "
            "measurement path separately or acquire a source whose selection and "
            "measurement path do not descend from the composed orientation."
        ),
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported composed-contact WORLD receipt")
    if receipt.get("packet_id") != "world-001":
        raise ValueError("composed-contact WORLD packet mismatch")
    digest = receipt.get("candidate_source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("composed-contact WORLD source digest missing")
    if receipt.get("lineage_class") != "oriented_downstream":
        raise ValueError("composed-contact lineage class drifted")
    if receipt.get("novelty_status") != "new_source_artifact":
        raise ValueError("composed-contact novelty drifted")
    if receipt.get("observation_status") != "fresh_world_contact":
        raise ValueError("composed-contact observation drifted")
    if receipt.get("selection_independence") != "not_independent_of_orientation":
        raise ValueError("composed-contact selection independence drifted")
    if receipt.get("measurement_independence") not in {
        "unknown",
        "independent_candidate",
        "not_independent",
    }:
        raise ValueError("composed-contact measurement independence invalid")
    if receipt.get("confirmation_status") not in {
        "independent_confirmation_not_established",
        "independent_confirmation_candidate",
        "not_independent_confirmation",
    }:
        raise ValueError("composed-contact confirmation status invalid")
    if receipt.get("counts_as_independent_confirmation") is not False:
        raise ValueError("fresh composed contact cannot automatically count as independent confirmation")
    if receipt.get("typed_origin_preserved") is not True:
        raise ValueError("composed-contact typed origin lost")
    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("composed-contact establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("composed-contact does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("composed-contact next door missing")
    return receipt


def inspect(receipt):
    validate_receipt(receipt)
    return {
        "schema": "static.world-composed-contact-inspection/v0",
        "packet_id": "world-001",
        "lineage_axis": receipt["lineage_class"],
        "novelty_axis": receipt["novelty_status"],
        "observation_axis": receipt["observation_status"],
        "selection_independence": receipt["selection_independence"],
        "measurement_independence": receipt["measurement_independence"],
        "confirmation_status": receipt["confirmation_status"],
        "counts_as_independent_confirmation": receipt["counts_as_independent_confirmation"],
        "typed_origin_preserved": receipt["typed_origin_preserved"],
        "truth_claimed": False,
        "freshness_collapsed_into_independence": False,
        "next_door": receipt["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(
        description="WORLD classification for composed-origin fresh contact"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    candidate = sub.add_parser("candidate")
    candidate.add_argument("witness_composed_intake")
    candidate.add_argument("-o", "--out")

    classify_cmd = sub.add_parser("classify")
    classify_cmd.add_argument("candidate")
    classify_cmd.add_argument("-o", "--out")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("receipt")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "candidate":
            _write_json(
                candidate_from_witness(_read_json(args.witness_composed_intake)),
                args.out,
            )
            return 0
        if args.command == "classify":
            _write_json(classify(_read_json(args.candidate)), args.out)
            return 0
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.receipt)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
