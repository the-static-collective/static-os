#!/usr/bin/env python3
"""Evidence-addressed audit of measurement independence.

Known selection dependence is immutable here. The audit may classify only the
measurement path, and even a passing measurement audit does not turn the source
into fully independent confirmation.
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
    "static_os_world_composed_for_measurement_audit",
    "scripts/world_composed.py",
)

AUDIT_SCHEMA = "static.measurement-path-audit/v0"
RECEIPT_SCHEMA = "static.world-measurement-audit-receipt/v0"

CRITERIA = (
    "channel_origin",
    "capture_control",
    "result_selection",
    "operator_relation",
)

PASS = {
    "channel_origin": "preexisting_or_external",
    "capture_control": "not_controlled_by_orientation",
    "result_selection": "result_blind_capture",
    "operator_relation": "independent_or_automatic",
}
FAIL = {
    "channel_origin": "derived_from_orientation",
    "capture_control": "controlled_by_orientation",
    "result_selection": "outcome_selected",
    "operator_relation": "orientation_participant",
}
UNKNOWN = "unknown"


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


def validate_audit(audit):
    if not isinstance(audit, dict) or audit.get("schema") != AUDIT_SCHEMA:
        raise ValueError("unsupported measurement audit schema")
    if not isinstance(audit.get("audit_id"), str) or not audit["audit_id"]:
        raise ValueError("measurement audit id missing")

    source_digest = audit.get("candidate_source_sha256")
    if not isinstance(source_digest, str) or len(source_digest) != 64:
        raise ValueError("measurement audit source digest missing")

    criteria = audit.get("criteria")
    if not isinstance(criteria, dict) or set(criteria) != set(CRITERIA):
        raise ValueError("measurement audit criteria shape mismatch")

    allowed = {
        "channel_origin": {PASS["channel_origin"], FAIL["channel_origin"], UNKNOWN},
        "capture_control": {PASS["capture_control"], FAIL["capture_control"], UNKNOWN},
        "result_selection": {PASS["result_selection"], FAIL["result_selection"], UNKNOWN},
        "operator_relation": {PASS["operator_relation"], FAIL["operator_relation"], UNKNOWN},
    }
    for name in CRITERIA:
        item = criteria[name]
        if not isinstance(item, dict) or set(item) != {"status", "evidence_sha256"}:
            raise ValueError(f"measurement audit criterion shape mismatch: {name}")
        if item.get("status") not in allowed[name]:
            raise ValueError(f"measurement audit criterion invalid: {name}")
        evidence = item.get("evidence_sha256")
        if not isinstance(evidence, str) or len(evidence) != 64:
            raise ValueError(f"measurement audit evidence digest missing: {name}")

    if not isinstance(audit.get("claim_limit"), str) or not audit["claim_limit"]:
        raise ValueError("measurement audit claim limit missing")
    return audit


def summarize(audit):
    validate_audit(audit)
    passed = []
    unknown = []
    failed = []
    for name in CRITERIA:
        status = audit["criteria"][name]["status"]
        if status == PASS[name]:
            passed.append(name)
        elif status == FAIL[name]:
            failed.append(name)
        else:
            unknown.append(name)
    return {
        "passed": passed,
        "unknown": unknown,
        "failed": failed,
    }


def classify(candidate, audit):
    world_composed.validate_candidate(candidate)
    validate_audit(audit)

    if audit["candidate_source_sha256"] != candidate["source_sha256"]:
        raise ValueError("measurement audit source does not match candidate")

    ancestry_digests = {
        value
        for key, value in candidate["orientation_ancestry"].items()
        if key != "relation_kinds" and isinstance(value, str)
    }
    for name in CRITERIA:
        evidence = audit["criteria"][name]["evidence_sha256"]
        if evidence == candidate["source_sha256"]:
            raise ValueError("measurement audit cannot use the candidate source as its own audit evidence")
        if evidence in ancestry_digests:
            raise ValueError("measurement audit evidence cannot impersonate orientation ancestry")

    summary = summarize(audit)

    if summary["failed"]:
        measurement_independence = "not_independent"
        evidence_role = "selection_and_measurement_dependent"
        establishes_measurement = (
            "At least one declared measurement-path criterion is incompatible with "
            "measurement independence."
        )
        next_door = (
            "Preserve the source as selection-dependent and measurement-dependent for "
            "this audit. Acquire a differently controlled measurement path if a more "
            "independent measurement is needed."
        )
    elif summary["unknown"]:
        measurement_independence = "unknown"
        evidence_role = "selection_dependent_measurement_unknown"
        establishes_measurement = (
            "No declared measurement-path criterion failed, but at least one remains "
            "unknown, so measurement independence is not established."
        )
        next_door = (
            "Resolve the unknown measurement-path criteria without changing the known "
            "selection ancestry."
        )
    else:
        measurement_independence = "independent_candidate"
        evidence_role = "selection_dependent_measurement_independent_candidate"
        establishes_measurement = (
            "All four declared measurement-path criteria support an independent-"
            "measurement candidate classification."
        )
        next_door = (
            "Carry this as a selection-dependent but measurement-independent candidate. "
            "Do not count it as fully independent confirmation; seek a source whose "
            "selection path is also independent if that stronger role is required."
        )

    receipt = {
        "schema": RECEIPT_SCHEMA,
        "packet_id": "world-001",
        "candidate_source_sha256": candidate["source_sha256"],
        "measurement_audit_sha256": canonical_digest(audit),
        "lineage_class": "oriented_downstream",
        "selection_independence": "not_independent_of_orientation",
        "measurement_independence": measurement_independence,
        "evidence_role": evidence_role,
        "counts_as_independent_confirmation": False,
        "typed_origin_preserved": True,
        "criteria_summary": summary,
        "establishes": [
            "The source remains selected downstream of composed orientation history.",
            establishes_measurement,
            "Each measurement-path criterion is backed by a declared evidence fingerprint.",
            "The typed composed-origin ancestry remains unchanged by the measurement audit.",
        ],
        "does_not_establish": [
            "The source is fully independent evidence.",
            "A measurement-independent candidate is independent of the process that selected the question or experiment.",
            "The measurement audit proves the source claim is correct.",
            "Declared audit evidence fingerprints have been externally authenticated by this runtime.",
            "The still-open branch is closed or disfavored.",
        ],
        "next_door": next_door,
    }
    return validate_receipt(receipt)


def validate_receipt(receipt):
    if not isinstance(receipt, dict) or receipt.get("schema") != RECEIPT_SCHEMA:
        raise ValueError("unsupported measurement audit receipt")
    if receipt.get("packet_id") != "world-001":
        raise ValueError("measurement audit WORLD packet mismatch")
    for key in ("candidate_source_sha256", "measurement_audit_sha256"):
        value = receipt.get(key)
        if not isinstance(value, str) or len(value) != 64:
            raise ValueError(f"measurement audit receipt digest missing: {key}")
    if receipt.get("lineage_class") != "oriented_downstream":
        raise ValueError("measurement audit lineage drifted")
    if receipt.get("selection_independence") != "not_independent_of_orientation":
        raise ValueError("measurement audit selection independence drifted")

    measurement = receipt.get("measurement_independence")
    role = receipt.get("evidence_role")
    expected_roles = {
        "independent_candidate": "selection_dependent_measurement_independent_candidate",
        "unknown": "selection_dependent_measurement_unknown",
        "not_independent": "selection_and_measurement_dependent",
    }
    if measurement not in expected_roles:
        raise ValueError("measurement audit independence invalid")
    if role != expected_roles[measurement]:
        raise ValueError("measurement audit evidence role contradicts independence")

    if receipt.get("counts_as_independent_confirmation") is not False:
        raise ValueError("selection-dependent source cannot count as fully independent confirmation")
    if receipt.get("typed_origin_preserved") is not True:
        raise ValueError("measurement audit lost typed origin")

    summary = receipt.get("criteria_summary")
    if not isinstance(summary, dict) or set(summary) != {"passed", "unknown", "failed"}:
        raise ValueError("measurement audit criteria summary missing")
    flattened = summary["passed"] + summary["unknown"] + summary["failed"]
    if sorted(flattened) != sorted(CRITERIA) or len(flattened) != len(set(flattened)):
        raise ValueError("measurement audit criteria summary does not partition criteria")

    if measurement == "independent_candidate":
        if summary["unknown"] or summary["failed"] or set(summary["passed"]) != set(CRITERIA):
            raise ValueError("independent measurement candidate requires all criteria to pass")
    elif measurement == "unknown":
        if summary["failed"] or not summary["unknown"]:
            raise ValueError("unknown measurement classification requires unknown criteria and no failures")
    else:
        if not summary["failed"]:
            raise ValueError("dependent measurement classification requires a failed criterion")

    if not isinstance(receipt.get("establishes"), list) or not receipt["establishes"]:
        raise ValueError("measurement audit establishes boundary missing")
    if not isinstance(receipt.get("does_not_establish"), list) or not receipt["does_not_establish"]:
        raise ValueError("measurement audit does-not-establish boundary missing")
    if not receipt.get("next_door"):
        raise ValueError("measurement audit next door missing")
    return receipt


def inspect(receipt):
    validate_receipt(receipt)
    return {
        "schema": "static.world-measurement-audit-inspection/v0",
        "packet_id": "world-001",
        "selection_independence": receipt["selection_independence"],
        "measurement_independence": receipt["measurement_independence"],
        "evidence_role": receipt["evidence_role"],
        "counts_as_independent_confirmation": receipt["counts_as_independent_confirmation"],
        "typed_origin_preserved": receipt["typed_origin_preserved"],
        "criteria_summary": receipt["criteria_summary"],
        "selection_axis_upgraded": False,
        "measurement_axis_audited": True,
        "truth_claimed": False,
        "next_door": receipt["next_door"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="WORLD measurement-path audit")
    sub = parser.add_subparsers(dest="command", required=True)

    classify_cmd = sub.add_parser("classify")
    classify_cmd.add_argument("candidate")
    classify_cmd.add_argument("audit")
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
                    _read_json(args.candidate),
                    _read_json(args.audit),
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
