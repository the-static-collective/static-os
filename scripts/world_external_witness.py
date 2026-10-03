#!/usr/bin/env python3
"""WORLD gate for a genuinely external witness candidate.

External witness status requires independent-candidate selection and measurement
paths. Agreement or contradiction is classified separately and cannot create or
destroy provenance independence.
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


world_composed = _load(
    "static_os_world_composed_for_external_witness",
    "scripts/world_composed.py",
)
measurement_audit = _load(
    "static_os_measurement_audit_for_external_witness",
    "scripts/world_measurement_audit.py",
)

SOURCE_SCHEMA = "static.external-witness-source/v0"
SELECTION_SCHEMA = "static.selection-path-audit/v0"
COMPARISON_SCHEMA = "static.external-witness-comparison/v0"
RECEIPT_SCHEMA = "static.world-external-witness-receipt/v0"

SELECTION_CRITERIA = (
    "question_origin",
    "assignment_origin",
    "hypothesis_exposure",
    "sampling_frame",
)
SELECTION_PASS = {
    "question_origin": "preexisting_or_external",
    "assignment_origin": "independently_assigned",
    "hypothesis_exposure": "unexposed_to_composed_history",
    "sampling_frame": "predeclared_or_external",
}
SELECTION_FAIL = {
    "question_origin": "derived_from_composed_history",
    "assignment_origin": "assigned_by_composed_history",
    "hypothesis_exposure": "exposed_to_composed_history",
    "sampling_frame": "selected_after_composed_result",
}

RELATION_ROLES = {
    "corroborates": "independent_corroboration_candidate",
    "contradicts": "independent_contradiction_candidate",
    "corrects": "independent_correction_candidate",
    "unrelated": "independent_unrelated_source",
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


def validate_source(source):
    if not isinstance(source, dict) or source.get("schema") != SOURCE_SCHEMA:
        raise ValueError("unsupported external witness source schema")
    if set(source) != {"schema", "source_id", "channel", "claim_text", "claim_limit"}:
        raise ValueError("external witness source shape drifted")
    if not isinstance(source.get("source_id"), str) or not source["source_id"]:
        raise ValueError("external witness source id missing")
    if source.get("channel") not in {
        "direct_observation",
        "independent_measurement",
        "document",
    }:
        raise ValueError("external witness channel invalid")
    for key in ("claim_text", "claim_limit"):
        if not isinstance(source.get(key), str) or not source[key]:
            raise ValueError(f"external witness source missing: {key}")
    return source


def validate_selection_audit(audit):
    if not isinstance(audit, dict) or audit.get("schema") != SELECTION_SCHEMA:
        raise ValueError("unsupported selection audit schema")
    if not isinstance(audit.get("audit_id"), str) or not audit["audit_id"]:
        raise ValueError("selection audit id missing")
    digest = audit.get("candidate_source_sha256")
    if not isinstance(digest, str) or len(digest) != 64:
        raise ValueError("selection audit source digest missing")
    criteria = audit.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(SELECTION_CRITERIA):
        raise ValueError("selection audit criteria shape mismatch")

    allowed = {
        name: {SELECTION_PASS[name], SELECTION_FAIL[name], "unknown"}
        for name in SELECTION_CRITERIA
    }
    for name in SELECTION_CRITERIA:
        item = criteria[name]
        if not isinstance(item, dict) or set(item) != {"status", "evidence_sha256"}:
            raise ValueError(f"selection audit criterion shape mismatch: {name}")
        if item.get("status") not in allowed[name]:
            raise ValueError(f"selection audit criterion invalid: {name}")
        evidence = item.get("evidence_sha256")
        if not isinstance(evidence, str) or len(evidence) != 64:
            raise ValueError(f"selection audit evidence digest missing: {name}")

    if not isinstance(audit.get("claim_limit"), str) or not audit["claim_limit"]:
        raise ValueError("selection audit claim limit missing")
    return audit


def summarize_selection(audit):
    validate_selection_audit(audit)
    passed, unknown, failed = [], [], []
    for name in SELECTION_CRITERIA:
        status = audit["criteria"][name]["status"]
        if status == SELECTION_PASS[name]:
            passed.append(name)
        elif status == SELECTION_FAIL[name]:
            failed.append(name)
        else:
            unknown.append(name)
    return {"passed": passed, "unknown": unknown, "failed": failed}


def validate_comparison(comparison):
    if not isinstance(comparison, dict) or comparison.get("schema") != COMPARISON_SCHEMA:
        raise ValueError("unsupported external comparison schema")
    if set(comparison) != {
        "schema",
        "composed_source_sha256",
        "external_source_sha256",
        "claim_relation",
        "relation_basis",
    }:
        raise ValueError("external comparison shape drifted")
    for key in ("composed_source_sha256", "external_source_sha256"):
        value = comparison.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"external comparison digest missing: {key}")
    if comparison.get("claim_relation") not in RELATION_ROLES:
        raise ValueError("external comparison relation invalid")
    if not isinstance(comparison.get("relation_basis"), str) or not comparison["relation_basis"]:
        raise ValueError("external comparison relation basis missing")
    return comparison


def _classify_axis(summary):
    if summary["failed"]:
        return "not_independent"
    if summary["unknown"]:
        return "unknown"
    return "independent_candidate"


def classify(
    composed_candidate,
    external_source,
    selection_audit,
    measurement_path_audit,
    comparison,
):
    world_composed.validate_candidate(composed_candidate)
    validate_source(external_source)
    validate_selection_audit(selection_audit)
    measurement_audit.validate_audit(measurement_path_audit)
    validate_comparison(comparison)

    external_digest = canonical_digest(external_source)
    composed_digest = composed_candidate["source_sha256"]

    if external_digest == composed_digest:
        raise ValueError("external source is the composed source artifact")
    if selection_audit["candidate_source_sha256"] != external_digest:
        raise ValueError("selection audit source does not match external source")
    if measurement_path_audit["candidate_source_sha256"] != external_digest:
        raise ValueError("measurement audit source does not match external source")
    if comparison["external_source_sha256"] != external_digest:
        raise ValueError("comparison external source mismatch")
    if comparison["composed_source_sha256"] != composed_digest:
        raise ValueError("comparison composed source mismatch")

    forbidden_evidence = {
        external_digest,
        composed_digest,
        *[
            value
            for key, value in composed_candidate["orientation_ancestry"].items()
            if key != "relation_kinds" and isinstance(value, str)
        ],
    }
    for audit_name, audit_value in (
        ("selection", selection_audit),
        ("measurement", measurement_path_audit),
    ):
        for criterion in audit_value["criteria"].values():
            if criterion["evidence_sha256"] in forbidden_evidence:
                raise ValueError(
                    f"{audit_name} audit evidence cannot self-certify or impersonate composed ancestry"
                )

    selection_summary = summarize_selection(selection_audit)
    measurement_summary = measurement_audit.summarize(measurement_path_audit)
    selection_status = _classify_axis(selection_summary)
    measurement_status = _classify_axis(measurement_summary)

    fully_external = (
        selection_status == "independent_candidate"
        and measurement_status == "independent_candidate"
    )

    if fully_external:
        lineage_class = "independent_external_candidate"
        witness_status = "independent_witness_candidate"
        relation_role = RELATION_ROLES[comparison["claim_relation"]]
        next_door = (
            "Preserve this as an independent external witness candidate and keep claim "
            "relation separate from provenance. Additional witnesses may strengthen or "
            "challenge the comparison, but agreement is not required for independence."
        )
    elif selection_status == "not_independent" or measurement_status == "not_independent":
        lineage_class = "external_not_independent"
        witness_status = "not_independent_witness"
        relation_role = "relation_without_independent_witness_status"
        next_door = (
            "Do not count this source as an independent witness. Repair or replace the "
            "failed selection or measurement path before assigning an external-witness role."
        )
    else:
        lineage_class = "external_independence_unknown"
        witness_status = "independence_not_established"
        relation_role = "relation_without_independent_witness_status"
        next_door = (
            "Resolve the unknown selection or measurement criteria before assigning "
            "independent external-witness status."
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": "world-001",
        "composed_source_sha256": composed_digest,
        "external_source_sha256": external_digest,
        "selection_audit_sha256": canonical_digest(selection_audit),
        "measurement_audit_sha256": canonical_digest(measurement_path_audit),
        "comparison_sha256": canonical_digest(comparison),
        "lineage_class": lineage_class,
        "selection_independence": selection_status,
        "measurement_independence": measurement_status,
        "independent_witness_status": witness_status,
        "counts_as_independent_witness": fully_external,
        "claim_relation": comparison["claim_relation"],
        "relation_role": relation_role,
        "typed_composed_origin_preserved": True,
        "selection_summary": selection_summary,
        "measurement_summary": measurement_summary,
        "establishes": [
            "The external source has a distinct source fingerprint from the composed-history source.",
            f"Selection-path classification: {selection_status}.",
            f"Measurement-path classification: {measurement_status}.",
            f"Claim relation to the composed source: {comparison['claim_relation']}.",
            (
                "The source qualifies as an independent external witness candidate."
                if fully_external
                else "Independent external-witness status is not established."
            ),
            "The composed source retains its typed orientation ancestry and is not rewritten by this comparison.",
        ],
        "does_not_establish": [
            "The external source is correct.",
            "The composed-history source is correct.",
            "An independent witness must agree with the composed-history source.",
            "Corroboration proves truth.",
            "Contradiction disproves either source.",
            "Declared audit evidence fingerprints have been externally authenticated by this runtime.",
            "Independent provenance determines which claim should win.",
        ],
        "next_door": next_door,
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported external witness receipt")
    if receipt.get("packet_id") != "world-001":
        raise ValueError("external witness WORLD packet mismatch")
    for key in (
        "composed_source_sha256",
        "external_source_sha256",
        "selection_audit_sha256",
        "measurement_audit_sha256",
        "comparison_sha256",
    ):
        value = receipt.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"external witness receipt digest missing: {key}")
    if receipt["composed_source_sha256"] == receipt["external_source_sha256"]:
        raise ValueError("external and composed source fingerprints collapsed")

    selection = receipt.get("selection_independence")
    measurement = receipt.get("measurement_independence")
    if selection not in {"independent_candidate", "unknown", "not_independent"}:
        raise ValueError("external witness selection classification invalid")
    if measurement not in {"independent_candidate", "unknown", "not_independent"}:
        raise ValueError("external witness measurement classification invalid")

    fully_external = (
        selection == "independent_candidate"
        and measurement == "independent_candidate"
    )
    expected_lineage = (
        "independent_external_candidate"
        if fully_external
        else (
            "external_not_independent"
            if "not_independent" in {selection, measurement}
            else "external_independence_unknown"
        )
    )
    expected_status = (
        "independent_witness_candidate"
        if fully_external
        else (
            "not_independent_witness"
            if "not_independent" in {selection, measurement}
            else "independence_not_established"
        )
    )
    if receipt.get("lineage_class") != expected_lineage:
        raise ValueError("external witness lineage contradicts audit axes")
    if receipt.get("independent_witness_status") != expected_status:
        raise ValueError("external witness status contradicts audit axes")
    if receipt.get("counts_as_independent_witness") is not fully_external:
        raise ValueError("external witness count flag contradicts audit axes")

    relation = receipt.get("claim_relation")
    if relation not in RELATION_ROLES:
        raise ValueError("external witness relation invalid")
    expected_role = (
        RELATION_ROLES[relation]
        if fully_external
        else "relation_without_independent_witness_status"
    )
    if receipt.get("relation_role") != expected_role:
        raise ValueError("external witness relation role contradicts provenance status")

    if receipt.get("typed_composed_origin_preserved") is not True:
        raise ValueError("external witness comparison lost composed typed origin")

    for summary_name, expected_criteria in (
        ("selection_summary", SELECTION_CRITERIA),
        ("measurement_summary", measurement_audit.CRITERIA),
    ):
        summary = receipt.get(summary_name)
        if not isinstance(summary, dict) or set(summary) != {"passed", "unknown", "failed"}:
            raise ValueError(f"external witness {summary_name} missing")
        flattened = summary["passed"] + summary["unknown"] + summary["failed"]
        if sorted(flattened) != sorted(expected_criteria) or len(flattened) != len(set(flattened)):
            raise ValueError(f"external witness {summary_name} does not partition criteria")

    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("external witness establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("external witness does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("external witness next door missing")
    return receipt


def inspect(receipt):
    validate_receipt(receipt)
    return {
        "schema": "static.world-external-witness-inspection/v0",
        "packet_id": "world-001",
        "lineage_class": receipt["lineage_class"],
        "selection_independence": receipt["selection_independence"],
        "measurement_independence": receipt["measurement_independence"],
        "independent_witness_status": receipt["independent_witness_status"],
        "counts_as_independent_witness": receipt["counts_as_independent_witness"],
        "claim_relation": receipt["claim_relation"],
        "relation_role": receipt["relation_role"],
        "typed_composed_origin_preserved": receipt["typed_composed_origin_preserved"],
        "independence_collapsed_into_agreement": False,
        "truth_claimed": False,
        "next_door": receipt["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="WORLD external witness gate")
    sub = parser.add_subparsers(dest="command", required=True)

    classify_cmd = sub.add_parser("classify")
    classify_cmd.add_argument("composed_candidate")
    classify_cmd.add_argument("external_source")
    classify_cmd.add_argument("selection_audit")
    classify_cmd.add_argument("measurement_audit")
    classify_cmd.add_argument("comparison")
    classify_cmd.add_argument("-o", "--out")

    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("receipt")

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "classify":
            _write_json(
                classify(
                    _read_json(args.composed_candidate),
                    _read_json(args.external_source),
                    _read_json(args.selection_audit),
                    _read_json(args.measurement_audit),
                    _read_json(args.comparison),
                ),
                args.out,
            )
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
