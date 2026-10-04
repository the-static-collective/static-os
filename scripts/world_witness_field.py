#!/usr/bin/env python3
"""Plural external witness field without majority-vote collapse.

Each external witness must first qualify individually. The field then audits
pairwise independence among witnesses. Claim-relation counts are descriptive;
they never become a verdict.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, ROOT / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


external = _load(
    "static_os_world_external_witness_for_field",
    "scripts/world_external_witness.py",
)

PAIR_SCHEMA = "static.external-witness-pair-audit/v0"
FIELD_SCHEMA = "static.external-witness-field/v0"
RECEIPT_SCHEMA = "static.world-external-witness-field-receipt/v0"

PAIR_CRITERIA = (
    "shared_source_ancestry",
    "operator_overlap",
    "capture_coordination",
    "selection_coordination",
)
PAIR_PASS = {
    "shared_source_ancestry": "no_shared_ancestor_evidence",
    "operator_overlap": "distinct_or_automatic",
    "capture_coordination": "not_coordinated",
    "selection_coordination": "independently_selected",
}
PAIR_FAIL = {
    "shared_source_ancestry": "shared_ancestor",
    "operator_overlap": "shared_operator",
    "capture_coordination": "coordinated",
    "selection_coordination": "jointly_selected",
}

RELATIONS = ("corroborates", "contradicts", "corrects", "unrelated")


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


def validate_pair_audit(audit):
    if not isinstance(audit, dict) or audit.get("schema") != PAIR_SCHEMA:
        raise ValueError("unsupported external witness pair audit schema")
    if not isinstance(audit.get("audit_id"), str) or not audit["audit_id"]:
        raise ValueError("external witness pair audit id missing")
    for key in ("source_a_sha256", "source_b_sha256"):
        value = audit.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"external witness pair digest missing: {key}")
    if audit["source_a_sha256"] == audit["source_b_sha256"]:
        raise ValueError("external witness pair collapsed to one source")

    criteria = audit.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(PAIR_CRITERIA):
        raise ValueError("external witness pair criteria shape mismatch")

    allowed = {
        name: {PAIR_PASS[name], PAIR_FAIL[name], "unknown"}
        for name in PAIR_CRITERIA
    }
    for name in PAIR_CRITERIA:
        item = criteria[name]
        if not isinstance(item, dict) or set(item) != {"status", "evidence_sha256"}:
            raise ValueError(f"external witness pair criterion shape mismatch: {name}")
        if item.get("status") not in allowed[name]:
            raise ValueError(f"external witness pair criterion invalid: {name}")
        evidence = item.get("evidence_sha256")
        if not isinstance(evidence, str) or len(evidence) != 64:
            raise ValueError(f"external witness pair evidence digest missing: {name}")
        if evidence in {audit["source_a_sha256"], audit["source_b_sha256"]}:
            raise ValueError("external witness pair cannot self-certify its independence")

    if not isinstance(audit.get("claim_limit"), str) or not audit["claim_limit"]:
        raise ValueError("external witness pair claim limit missing")
    return audit


def summarize_pair(audit):
    validate_pair_audit(audit)
    passed, unknown, failed = [], [], []
    for name in PAIR_CRITERIA:
        status = audit["criteria"][name]["status"]
        if status == PAIR_PASS[name]:
            passed.append(name)
        elif status == PAIR_FAIL[name]:
            failed.append(name)
        else:
            unknown.append(name)
    return {"passed": passed, "unknown": unknown, "failed": failed}


def pair_status(audit):
    summary = summarize_pair(audit)
    if summary["failed"]:
        return "failed"
    if summary["unknown"]:
        return "unknown"
    return "passed"


def validate_field(field):
    if not isinstance(field, dict) or field.get("schema") != FIELD_SCHEMA:
        raise ValueError("unsupported external witness field schema")
    if not isinstance(field.get("field_id"), str) or not field["field_id"]:
        raise ValueError("external witness field id missing")
    composed = field.get("composed_source_sha256")
    if not isinstance(composed, str) or len(composed) != 64:
        raise ValueError("external witness field composed source missing")

    witnesses = field.get("witnesses")
    if not isinstance(witnesses, list) or len(witnesses) < 2:
        raise ValueError("external witness field requires at least two witnesses")
    seen_sources = set()
    seen_receipts = set()
    for witness in witnesses:
        if not isinstance(witness, dict) or set(witness) != {
            "source_sha256",
            "receipt_sha256",
            "claim_relation",
        }:
            raise ValueError("external witness descriptor shape mismatch")
        source = witness["source_sha256"]
        receipt = witness["receipt_sha256"]
        if not isinstance(source, str) or len(source) != 64:
            raise ValueError("external witness source digest invalid")
        if not isinstance(receipt, str) or len(receipt) != 64:
            raise ValueError("external witness receipt digest invalid")
        if source == composed:
            raise ValueError("external witness source collapsed with composed source")
        if witness["claim_relation"] not in RELATIONS:
            raise ValueError("external witness relation invalid")
        if source in seen_sources or receipt in seen_receipts:
            raise ValueError("duplicate external witness descriptor")
        seen_sources.add(source)
        seen_receipts.add(receipt)

    audits = field.get("pair_audits")
    if not isinstance(audits, list) or not audits:
        raise ValueError("external witness field pair audits missing")
    expected_pairs = {
        tuple(sorted(pair))
        for pair in itertools.combinations(seen_sources, 2)
    }
    described_pairs = set()
    seen_audits = set()
    for item in audits:
        if not isinstance(item, dict) or set(item) != {
            "source_a_sha256",
            "source_b_sha256",
            "audit_sha256",
        }:
            raise ValueError("external witness pair descriptor shape mismatch")
        pair = tuple(sorted((item["source_a_sha256"], item["source_b_sha256"])))
        if pair[0] == pair[1]:
            raise ValueError("external witness pair descriptor collapsed")
        if pair not in expected_pairs:
            raise ValueError("external witness pair descriptor references unknown source")
        if pair in described_pairs:
            raise ValueError("duplicate external witness pair descriptor")
        described_pairs.add(pair)
        audit_digest = item["audit_sha256"]
        if not isinstance(audit_digest, str) or len(audit_digest) != 64:
            raise ValueError("external witness pair audit digest invalid")
        if audit_digest in seen_audits:
            raise ValueError("duplicate external witness pair audit")
        seen_audits.add(audit_digest)

    if described_pairs != expected_pairs:
        raise ValueError("external witness field does not cover every witness pair")
    if not isinstance(field.get("claim_limit"), str) or not field["claim_limit"]:
        raise ValueError("external witness field claim limit missing")
    return field


def build_field(composed_source_sha256, witness_receipts, pair_audits):
    if not isinstance(witness_receipts, list) or len(witness_receipts) < 2:
        raise ValueError("plural witness field needs at least two witness receipts")

    witnesses = []
    sources = set()
    for receipt in witness_receipts:
        external.validate_receipt(receipt)
        if receipt["composed_source_sha256"] != composed_source_sha256:
            raise ValueError("witness receipts do not share one composed source")
        if receipt["counts_as_independent_witness"] is not True:
            raise ValueError("field can only admit qualified independent witness candidates")
        source = receipt["external_source_sha256"]
        if source in sources:
            raise ValueError("duplicate external witness source")
        sources.add(source)
        witnesses.append(
            {
                "source_sha256": source,
                "receipt_sha256": canonical_digest(receipt),
                "claim_relation": receipt["claim_relation"],
            }
        )

    witnesses.sort(key=lambda item: item["source_sha256"])

    audit_descriptors = []
    audit_map = {}
    for audit in pair_audits:
        validate_pair_audit(audit)
        pair = tuple(sorted((audit["source_a_sha256"], audit["source_b_sha256"])))
        if pair in audit_map:
            raise ValueError("duplicate pair audit")
        audit_map[pair] = audit

    expected_pairs = {
        tuple(sorted(pair))
        for pair in itertools.combinations(sources, 2)
    }
    if set(audit_map) != expected_pairs:
        raise ValueError("pair audits must cover every external witness pair exactly once")

    for pair in sorted(expected_pairs):
        audit = audit_map[pair]
        audit_descriptors.append(
            {
                "source_a_sha256": pair[0],
                "source_b_sha256": pair[1],
                "audit_sha256": canonical_digest(audit),
            }
        )

    field = {
        "schema": FIELD_SCHEMA,
        "field_id": "external-witness-field-001",
        "composed_source_sha256": composed_source_sha256,
        "witnesses": witnesses,
        "pair_audits": audit_descriptors,
        "claim_limit": (
            "This field stores individually qualified witness candidates and complete "
            "pairwise independence audits. Relation counts remain descriptive and do "
            "not constitute a vote, verdict, or truth score."
        ),
    }
    return validate_field(field)


def classify(field, witness_receipts, pair_audits):
    validate_field(field)

    receipts_by_digest = {}
    for receipt in witness_receipts:
        external.validate_receipt(receipt)
        digest = canonical_digest(receipt)
        if digest in receipts_by_digest:
            raise ValueError("duplicate witness receipt body")
        receipts_by_digest[digest] = receipt

    audit_by_digest = {}
    for audit in pair_audits:
        validate_pair_audit(audit)
        digest = canonical_digest(audit)
        if digest in audit_by_digest:
            raise ValueError("duplicate pair audit body")
        audit_by_digest[digest] = audit

    relation_counts = {relation: 0 for relation in RELATIONS}
    for descriptor in field["witnesses"]:
        receipt = receipts_by_digest.get(descriptor["receipt_sha256"])
        if receipt is None:
            raise ValueError("field witness receipt body missing")
        if receipt["external_source_sha256"] != descriptor["source_sha256"]:
            raise ValueError("field witness source/receipt mismatch")
        if receipt["claim_relation"] != descriptor["claim_relation"]:
            raise ValueError("field witness relation/receipt mismatch")
        if receipt["composed_source_sha256"] != field["composed_source_sha256"]:
            raise ValueError("field witness composed-source mismatch")
        if receipt["counts_as_independent_witness"] is not True:
            raise ValueError("field witness lost independent-witness status")
        relation_counts[descriptor["claim_relation"]] += 1

    pair_counts = {"passed": 0, "unknown": 0, "failed": 0}
    for descriptor in field["pair_audits"]:
        audit = audit_by_digest.get(descriptor["audit_sha256"])
        if audit is None:
            raise ValueError("field pair audit body missing")
        declared_pair = tuple(sorted(
            (descriptor["source_a_sha256"], descriptor["source_b_sha256"])
        ))
        actual_pair = tuple(sorted(
            (audit["source_a_sha256"], audit["source_b_sha256"])
        ))
        if declared_pair != actual_pair:
            raise ValueError("field pair audit descriptor/body mismatch")
        pair_counts[pair_status(audit)] += 1

    if pair_counts["failed"]:
        plurality_status = "shared_external_lineage"
        field_state = "plurality_not_established"
        next_door = (
            "Preserve the individually independent-to-composed witnesses, but do not "
            "treat them as an independent plurality. Repair or replace the pairwise "
            "dependency before using plural-witness reasoning."
        )
    elif pair_counts["unknown"]:
        plurality_status = "inter_witness_independence_unknown"
        field_state = "plurality_not_established"
        next_door = (
            "Resolve the unknown pairwise witness-independence criteria. Do not use "
            "relation counts as a substitute for unresolved plurality provenance."
        )
    else:
        plurality_status = "independent_plurality_candidate"
        active_relations = [
            relation for relation, count in relation_counts.items() if count > 0
        ]
        relevant_relations = [
            relation for relation in active_relations if relation != "unrelated"
        ]
        if len(relevant_relations) >= 2:
            field_state = "disagreement_preserved"
        elif len(relevant_relations) == 1 and relation_counts["unrelated"] == 0:
            field_state = "convergence_without_verdict"
        elif relation_counts["unrelated"] > 0:
            field_state = "mixed_relevance"
        else:
            field_state = "mixed_relevance"
        next_door = (
            "Preserve the independent witness field without majority-vote collapse. "
            "Use relation topology to choose the next discriminating contact, not to "
            "declare a winner from counts alone."
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": "world-001",
        "field_sha256": canonical_digest(field),
        "composed_source_sha256": field["composed_source_sha256"],
        "witness_count": len(field["witnesses"]),
        "plurality_status": plurality_status,
        "field_state": field_state,
        "relation_counts": relation_counts,
        "pair_audit_summary": pair_counts,
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "typed_composed_origin_preserved": True,
        "establishes": [
            f"{len(field['witnesses'])} individually qualified external witness candidates are present.",
            f"Inter-witness plurality classification: {plurality_status}.",
            f"Relation topology is preserved as counts: {relation_counts}.",
            "Witness relation and witness provenance remain separate axes.",
            "The composed-history source retains its typed origin and is not overwritten by the field.",
        ],
        "does_not_establish": [
            "The most common relation is true.",
            "A majority of witnesses determines a verdict.",
            "Independent witnesses must agree.",
            "Disagreement among independent witnesses is a failure of the field.",
            "Equal witness counts imply equal evidentiary weight.",
            "Pairwise structural audits externally authenticate their evidence fingerprints.",
            "The composed-history source is correct or incorrect.",
        ],
        "next_door": next_door,
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported external witness field receipt")
    if receipt.get("packet_id") != "world-001":
        raise ValueError("external witness field WORLD packet mismatch")
    for key in ("field_sha256", "composed_source_sha256"):
        value = receipt.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"external witness field digest missing: {key}")
    if not isinstance(receipt.get("witness_count"), int) or receipt["witness_count"] < 2:
        raise ValueError("external witness field witness count invalid")

    plurality = receipt.get("plurality_status")
    if plurality not in {
        "independent_plurality_candidate",
        "inter_witness_independence_unknown",
        "shared_external_lineage",
    }:
        raise ValueError("external witness field plurality status invalid")

    field_state = receipt.get("field_state")
    if field_state not in {
        "convergence_without_verdict",
        "disagreement_preserved",
        "mixed_relevance",
        "plurality_not_established",
    }:
        raise ValueError("external witness field state invalid")
    if plurality != "independent_plurality_candidate" and field_state != "plurality_not_established":
        raise ValueError("field state overclaims unresolved plurality")

    counts = receipt.get("relation_counts")
    if not isinstance(counts, dict) or set(counts) != set(RELATIONS):
        raise ValueError("external witness field relation counts invalid")
    if any(not isinstance(value, int) or value < 0 for value in counts.values()):
        raise ValueError("external witness field relation counts malformed")
    if sum(counts.values()) != receipt["witness_count"]:
        raise ValueError("external witness field relation counts do not match witness count")

    pair_summary = receipt.get("pair_audit_summary")
    if not isinstance(pair_summary, dict) or set(pair_summary) != {"passed", "unknown", "failed"}:
        raise ValueError("external witness field pair summary invalid")
    if any(not isinstance(value, int) or value < 0 for value in pair_summary.values()):
        raise ValueError("external witness field pair summary malformed")
    expected_pairs = receipt["witness_count"] * (receipt["witness_count"] - 1) // 2
    if sum(pair_summary.values()) != expected_pairs:
        raise ValueError("external witness field pair summary does not cover all pairs")

    if plurality == "independent_plurality_candidate":
        if pair_summary["unknown"] or pair_summary["failed"]:
            raise ValueError("independent plurality requires every pair audit to pass")
    elif plurality == "inter_witness_independence_unknown":
        if pair_summary["failed"] or not pair_summary["unknown"]:
            raise ValueError("unknown plurality requires unknown pair audits and no failures")
    else:
        if not pair_summary["failed"]:
            raise ValueError("shared-lineage plurality requires a failed pair audit")

    if receipt.get("majority_rule_used") is not False:
        raise ValueError("external witness field cannot use majority rule")
    if receipt.get("verdict_status") != "withheld":
        raise ValueError("external witness field verdict must remain withheld")
    if receipt.get("typed_composed_origin_preserved") is not True:
        raise ValueError("external witness field lost composed typed origin")
    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("external witness field establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("external witness field does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("external witness field next door missing")
    return receipt


def inspect(receipt):
    validate_receipt(receipt)
    return {
        "schema": "static.world-external-witness-field-inspection/v0",
        "packet_id": "world-001",
        "plurality_status": receipt["plurality_status"],
        "field_state": receipt["field_state"],
        "witness_count": receipt["witness_count"],
        "relation_counts": receipt["relation_counts"],
        "pair_audit_summary": receipt["pair_audit_summary"],
        "majority_rule_used": False,
        "verdict_status": "withheld",
        "disagreement_allowed": True,
        "typed_composed_origin_preserved": True,
        "truth_claimed": False,
        "next_door": receipt["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Plural external witness field")
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("receipt")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.receipt)), None)
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
