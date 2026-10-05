#!/usr/bin/env python3
"""Three-world condition field over a residual witness-history checkpoint.

One verified residual witness history forks into three sovereign, explicitly
admitted one-condition worlds. Each world returns one held result (or honest
refusal). A rankless postbag preserves all returns. Dogram may report
condition-associated outcome splits but cannot claim causality. A compact
multi-parent frontier preserves the three result addresses without embedding
their bodies or selecting a canonical parent.
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


residual = _load(
    "static_os_residual_witness_for_condition_field",
    "scripts/residual_witness_cycle.py",
)
field_runtime = _load(
    "static_os_witness_field_for_condition_field",
    "scripts/world_witness_field.py",
)

BRANCH_SCHEMA = "static.condition-world-branch/v0"
RESULT_SCHEMA = "static.condition-world-result/v0"
POSTBAG_SCHEMA = "static.condition-postbag/v0"
ASSOCIATION_SCHEMA = "static.dogram-condition-association/v0"
FRONTIER_SCHEMA = "static.condition-recombinant-frontier/v0"

RELATIONS = {"corroborates", "contradicts", "corrects"}


def _read_json(path: str | Path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def _write_json(value, path=None):
    rendered = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if path:
        Path(path).write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return value


def validate_branch(value):
    required = {
        "schema","branch_id","original_field_sha256","residual_update_sha256",
        "owner","admission_status","changed_condition","preserved",
        "mineral_want","claim_limit",
    }
    if not isinstance(value, dict) or value.get("schema") != BRANCH_SCHEMA:
        raise ValueError("unsupported condition world branch schema")
    if set(value) != required:
        raise ValueError("condition world branch shape drifted")
    for key in ("branch_id","owner","claim_limit"):
        if not isinstance(value.get(key), str) or not value[key]:
            raise ValueError(f"condition world branch missing: {key}")
    for key in ("original_field_sha256","residual_update_sha256"):
        v = value.get(key)
        if not isinstance(v, str) or len(v) != 64:
            raise ValueError(f"condition world branch digest missing: {key}")
    if value.get("admission_status") != "admitted":
        raise ValueError("condition world branch must be explicitly admitted")
    cond = value.get("changed_condition")
    if not isinstance(cond, dict) or set(cond) != {"name","before","after"}:
        raise ValueError("condition world changed condition shape mismatch")
    if not isinstance(cond["name"], str) or not cond["name"]:
        raise ValueError("condition world changed condition name missing")
    if cond["before"] == cond["after"]:
        raise ValueError("condition world must actually change one condition")
    preserved = value.get("preserved")
    if not isinstance(preserved, list) or not preserved or len(preserved) != len(set(preserved)):
        raise ValueError("condition world preserve set invalid")
    want = value.get("mineral_want")
    if want is not None:
        if not isinstance(want, dict) or set(want) != {
            "request_sha256","mineral_kind","status","authorization"
        }:
            raise ValueError("condition world mineral WANT shape mismatch")
        if len(want["request_sha256"]) != 64:
            raise ValueError("condition world mineral WANT digest invalid")
        if not want["mineral_kind"]:
            raise ValueError("condition world mineral WANT kind missing")
        if want["status"] != "requested" or want["authorization"] != "none":
            raise ValueError("condition world mineral WANT may not carry execution authority")
    return value


def make_branch(
    original_field,
    residual_update,
    branch_id,
    owner,
    condition_name,
    before,
    after,
    accept_branch,
    mineral_want=None,
):
    field_runtime.validate_field(original_field)
    residual.validate_update(residual_update)
    field_sha = digest(original_field)
    update_sha = digest(residual_update)
    if residual_update["original_field_sha256"] != field_sha:
        raise ValueError("residual update does not address supplied original field")
    if accept_branch is not True:
        raise ValueError("explicit local branch admission is required")
    if mineral_want is not None:
        if not isinstance(mineral_want, dict):
            raise ValueError("mineral WANT must be an object or null")
    branch = {
        "schema": BRANCH_SCHEMA,
        "branch_id": branch_id,
        "original_field_sha256": field_sha,
        "residual_update_sha256": update_sha,
        "owner": owner,
        "admission_status": "admitted",
        "changed_condition": {
            "name": condition_name,
            "before": before,
            "after": after,
        },
        "preserved": [
            "original witness field",
            "contact #1 history",
            "contact #2 history",
            "all witness source addresses",
            "majority rule unused",
            "verdict withheld",
        ],
        "mineral_want": mineral_want,
        "claim_limit": (
            "This branch admits one owner-local condition change only. It does not "
            "establish causality, inherit execution authority from sibling branches, "
            "or make an optional Mineral WANT executable."
        ),
    }
    return validate_branch(branch)


def validate_result(value):
    required = {
        "schema","branch_sha256","status","outcome_relation","observation",
        "residue","mineral_artifact_sha256","claim_limit",
    }
    if not isinstance(value, dict) or value.get("schema") != RESULT_SCHEMA:
        raise ValueError("unsupported condition world result schema")
    if set(value) != required:
        raise ValueError("condition world result shape drifted")
    if not isinstance(value.get("branch_sha256"), str) or len(value["branch_sha256"]) != 64:
        raise ValueError("condition world result branch digest invalid")
    if value.get("status") not in {"contacted","refused"}:
        raise ValueError("condition world result status invalid")
    if value["status"] == "contacted":
        if value.get("outcome_relation") not in RELATIONS:
            raise ValueError("contacted condition world requires a relation outcome")
        if not isinstance(value.get("observation"), str) or not value["observation"]:
            raise ValueError("contacted condition world requires an observation")
    else:
        if value.get("outcome_relation") is not None:
            raise ValueError("refused condition world cannot claim an outcome relation")
        if value.get("observation") != "":
            raise ValueError("refused condition world observation must remain empty")
    if not isinstance(value.get("residue"), str) or not value["residue"]:
        raise ValueError("condition world result must preserve residue")
    mineral = value.get("mineral_artifact_sha256")
    if mineral is not None and (not isinstance(mineral, str) or len(mineral) != 64):
        raise ValueError("condition world result mineral artifact digest invalid")
    if not isinstance(value.get("claim_limit"), str) or not value["claim_limit"]:
        raise ValueError("condition world result claim limit missing")
    return value


def make_result(
    branch,
    status,
    outcome_relation,
    observation,
    residue_text,
    mineral_artifact_sha256=None,
):
    validate_branch(branch)
    if mineral_artifact_sha256 is not None and branch["mineral_want"] is None:
        raise ValueError("branch without Mineral WANT cannot return a mineral artifact")
    result = {
        "schema": RESULT_SCHEMA,
        "branch_sha256": digest(branch),
        "status": status,
        "outcome_relation": outcome_relation,
        "observation": observation,
        "residue": residue_text,
        "mineral_artifact_sha256": mineral_artifact_sha256,
        "claim_limit": (
            "This branch return records one local contact or refusal. It does not "
            "rank sibling worlds, prove the changed condition caused the result, or "
            "authorize any downstream consequence."
        ),
    }
    return validate_result(result)


def validate_postbag(value):
    required = {
        "schema","original_field_sha256","residual_update_sha256",
        "returns","return_order_ranked","all_returns_held","claim_limit",
    }
    if not isinstance(value, dict) or value.get("schema") != POSTBAG_SCHEMA:
        raise ValueError("unsupported condition postbag schema")
    if set(value) != required:
        raise ValueError("condition postbag shape drifted")
    returns = value.get("returns")
    if not isinstance(returns, list) or len(returns) != 3:
        raise ValueError("condition postbag requires exactly three returns")
    branches = [item.get("branch_sha256") for item in returns]
    results = [item.get("result_sha256") for item in returns]
    if len(set(branches)) != 3 or len(set(results)) != 3:
        raise ValueError("condition postbag requires three distinct branch/result addresses")
    if value.get("return_order_ranked") is not False:
        raise ValueError("condition postbag return order may not rank worlds")
    if value.get("all_returns_held") is not True:
        raise ValueError("condition postbag must HOLD every return")
    if not value.get("claim_limit"):
        raise ValueError("condition postbag claim limit missing")
    return value


def make_postbag(branches, results):
    if not isinstance(branches, list) or len(branches) != 3:
        raise ValueError("condition postbag requires exactly three branches")
    if not isinstance(results, list) or len(results) != 3:
        raise ValueError("condition postbag requires exactly three results")

    branch_by_sha = {}
    owners = set()
    condition_names = set()
    field_sha = None
    update_sha = None
    for branch in branches:
        validate_branch(branch)
        bsha = digest(branch)
        if bsha in branch_by_sha:
            raise ValueError("duplicate condition world branch")
        branch_by_sha[bsha] = branch
        if branch["owner"] in owners:
            raise ValueError("condition worlds require distinct sovereign owners")
        owners.add(branch["owner"])
        name = branch["changed_condition"]["name"]
        if name in condition_names:
            raise ValueError("each condition world must change a distinct named condition")
        condition_names.add(name)
        field_sha = field_sha or branch["original_field_sha256"]
        update_sha = update_sha or branch["residual_update_sha256"]
        if branch["original_field_sha256"] != field_sha:
            raise ValueError("condition worlds do not share one original field")
        if branch["residual_update_sha256"] != update_sha:
            raise ValueError("condition worlds do not share one residual checkpoint")

    result_by_branch = {}
    for result in results:
        validate_result(result)
        bsha = result["branch_sha256"]
        if bsha not in branch_by_sha:
            raise ValueError("condition result addresses unknown branch")
        if bsha in result_by_branch:
            raise ValueError("duplicate condition result for one branch")
        branch = branch_by_sha[bsha]
        if result["mineral_artifact_sha256"] is not None and branch["mineral_want"] is None:
            raise ValueError("condition result mineral artifact lacks branch WANT")
        result_by_branch[bsha] = result

    if set(result_by_branch) != set(branch_by_sha):
        raise ValueError("condition postbag must contain exactly one return from every branch")

    returns = [
        {"branch_sha256": bsha, "result_sha256": digest(result_by_branch[bsha])}
        for bsha in sorted(branch_by_sha)
    ]
    postbag = {
        "schema": POSTBAG_SCHEMA,
        "original_field_sha256": field_sha,
        "residual_update_sha256": update_sha,
        "returns": returns,
        "return_order_ranked": False,
        "all_returns_held": True,
        "claim_limit": (
            "This postbag holds three sovereign condition-world returns without "
            "ranking, merging, selecting a winner, or converting return order into authority."
        ),
    }
    return validate_postbag(postbag)


def make_association(postbag, branches, results):
    validate_postbag(postbag)
    branch_by_sha = {digest(b): b for b in branches}
    result_by_sha = {digest(r): r for r in results}
    if len(branch_by_sha) != 3 or len(result_by_sha) != 3:
        raise ValueError("condition association requires three distinct branch/result bodies")

    rows = []
    contacted_outcomes = []
    for descriptor in postbag["returns"]:
        branch = branch_by_sha.get(descriptor["branch_sha256"])
        result = result_by_sha.get(descriptor["result_sha256"])
        if branch is None or result is None:
            raise ValueError("condition association missing a postbag-addressed body")
        if result["branch_sha256"] != descriptor["branch_sha256"]:
            raise ValueError("condition association result/branch mismatch")
        row = {
            "condition_name": branch["changed_condition"]["name"],
            "condition_after": branch["changed_condition"]["after"],
            "result_status": result["status"],
            "outcome_relation": result["outcome_relation"],
        }
        rows.append(row)
        if result["status"] == "contacted":
            contacted_outcomes.append(result["outcome_relation"])

    rows.sort(key=lambda row: (row["condition_name"], row["condition_after"]))
    distinct = sorted(set(contacted_outcomes))
    status = "complete" if len(contacted_outcomes) == 3 else "incomplete"
    association = {
        "schema": ASSOCIATION_SCHEMA,
        "postbag_sha256": digest(postbag),
        "status": status,
        "condition_outcomes": rows,
        "distinct_outcomes": distinct,
        "split_detected": len(distinct) > 1,
        "causal_claimed": False,
        "ranking_used": False,
        "claim_limit": (
            "Dogram reports only an association between declared condition variants "
            "and returned relation outcomes. A split does not establish that the "
            "changed condition caused the split, and a refusal is not a failed witness."
        ),
    }
    return validate_association(association)


def validate_association(value):
    if not isinstance(value, dict) or value.get("schema") != ASSOCIATION_SCHEMA:
        raise ValueError("unsupported Dogram condition association schema")
    if value.get("status") not in {"complete","incomplete"}:
        raise ValueError("condition association status invalid")
    rows = value.get("condition_outcomes")
    if not isinstance(rows, list) or len(rows) != 3:
        raise ValueError("condition association requires three condition rows")
    contacted = [
        row["outcome_relation"] for row in rows
        if row.get("result_status") == "contacted"
    ]
    if value["status"] == "complete" and len(contacted) != 3:
        raise ValueError("complete condition association requires three contacted results")
    if value["status"] == "incomplete" and len(contacted) == 3:
        raise ValueError("incomplete condition association contradicts complete returns")
    expected = sorted(set(contacted))
    if value.get("distinct_outcomes") != expected:
        raise ValueError("condition association distinct outcomes mismatch")
    if value.get("split_detected") is not (len(expected) > 1):
        raise ValueError("condition association split flag mismatch")
    if value.get("causal_claimed") is not False:
        raise ValueError("condition association cannot claim causality")
    if value.get("ranking_used") is not False:
        raise ValueError("condition association cannot rank condition worlds")
    if not value.get("claim_limit"):
        raise ValueError("condition association claim limit missing")
    return value


def make_frontier(postbag, association, results):
    validate_postbag(postbag)
    validate_association(association)
    if association["postbag_sha256"] != digest(postbag):
        raise ValueError("condition association does not address supplied postbag")
    result_by_sha = {digest(result): result for result in results}
    parent_result_sha256s = sorted(item["result_sha256"] for item in postbag["returns"])
    if set(parent_result_sha256s) != set(result_by_sha):
        raise ValueError("frontier result bodies do not match postbag parents")

    root_material = {
        "schema": "static.condition-frontier-root-material/v0",
        "original_field_sha256": postbag["original_field_sha256"],
        "residual_update_sha256": postbag["residual_update_sha256"],
        "postbag_sha256": digest(postbag),
        "association_sha256": digest(association),
        "parent_result_sha256s": parent_result_sha256s,
    }
    frontier = {
        "schema": FRONTIER_SCHEMA,
        "original_field_sha256": postbag["original_field_sha256"],
        "residual_update_sha256": postbag["residual_update_sha256"],
        "postbag_sha256": digest(postbag),
        "association_sha256": digest(association),
        "parent_result_sha256s": parent_result_sha256s,
        "frontier_root_sha256": digest(root_material),
        "parent_count": 3,
        "parent_bodies_embedded": False,
        "canonical_parent_selected": False,
        "status": "held",
        "claim_limit": (
            "This compact frontier addresses all three condition-world returns and "
            "their Dogram association without embedding parent bodies or selecting "
            "a canonical world. HOLD is not admission, consensus, or causal proof."
        ),
    }
    return validate_frontier(frontier)


def validate_frontier(value):
    if not isinstance(value, dict) or value.get("schema") != FRONTIER_SCHEMA:
        raise ValueError("unsupported condition recombinant frontier schema")
    parents = value.get("parent_result_sha256s")
    if not isinstance(parents, list) or len(parents) != 3 or len(set(parents)) != 3:
        raise ValueError("condition frontier requires three distinct result parents")
    if value.get("parent_count") != 3:
        raise ValueError("condition frontier parent count mismatch")
    if value.get("parent_bodies_embedded") is not False:
        raise ValueError("condition frontier may not embed parent bodies")
    if value.get("canonical_parent_selected") is not False:
        raise ValueError("condition frontier may not select a canonical parent")
    if value.get("status") != "held":
        raise ValueError("condition frontier must remain held")
    if not value.get("claim_limit"):
        raise ValueError("condition frontier claim limit missing")
    return value


def inspect(frontier, association):
    validate_frontier(frontier)
    validate_association(association)
    if frontier["association_sha256"] != digest(association):
        raise ValueError("frontier/association digest mismatch")
    return {
        "schema": "static.condition-field-inspection/v0",
        "parent_count": frontier["parent_count"],
        "association_status": association["status"],
        "distinct_outcomes": association["distinct_outcomes"],
        "split_detected": association["split_detected"],
        "causal_claimed": False,
        "ranking_used": False,
        "canonical_parent_selected": False,
        "parent_bodies_embedded": False,
        "frontier_status": frontier["status"],
        "claim_limit": frontier["claim_limit"],
    }


def build_parser():
    parser = argparse.ArgumentParser(description="Condition field / world fork")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_cmd = sub.add_parser("inspect")
    inspect_cmd.add_argument("frontier")
    inspect_cmd.add_argument("association")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    try:
        if args.command == "inspect":
            _write_json(inspect(_read_json(args.frontier), _read_json(args.association)))
            return 0
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"REFUSE: {error}", file=sys.stderr)
        return 2
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
