"""STATIC-CAD-006: owner-selected alternative solid feature branches.

A bounded feature tree, not a general-purpose editable FreeCAD feature DAG.
Each variation is derived from the same frozen solved sketch. The nonselected
branch stays a proposal, never silently built or sent to reLATTE.
"""
from __future__ import annotations

import copy
import re
from pathlib import Path
from typing import Any

from question_first.session import Hold, require, _sealed, _check_seal
from question_first.sketch_solver import compile_sketch,verify_sketch
from question_first.solid_body import build_solid, verify_files
from question_first.solid_relatte import cross, verify_native

TREE="static-os.cad-feature-tree/v0"
SELECTION="static-os.cad-feature-selection/v0"
BRANCH="static-os.cad-feature-branch-provenance/v0"
IDENT=re.compile(r"^[A-Za-z0-9._:-]{1,100}$")
CANDIDATES=[
    {"id":"pad-deeper","feature":"pad","operation":"SET_DEPTH",
     "delta_um":2000,"authority":"none"},
    {"id":"bore-wider","feature":"pocket_through",
     "operation":"INCREASE_FIRST_BORE_RADIUS",
     "delta_um":500,"authority":"none"},
]


def plan_tree(sketch: Any) -> dict:
    parent=verify_sketch(sketch)
    require(parent["constraint_report"]["state"]=="SOLVED"
            and parent["status"]=="SKETCH_CANDIDATE_ONLY"
            and parent["seed"]["revision_parent_id"] is None,
            "FEATURE_TREE_REQUIRES_FROZEN_ROOT_SKETCH")
    require(len(parent["features"])==2 and parent["features"][0]["kind"]=="pad"
            and parent["features"][1]["kind"]=="pocket_through"
            and len(parent["seed"]["holes"])>0,
            "BOUND_FEATURE_TREE_PAD_POCKET_REQUIRED")
    body={
        "schema":TREE,
        "root_sketch":parent,
        "parent_sketch_id":parent["sketch_id"],
        "feature_nodes":[
            {"node_id":"sketch-source","kind":"SOLVED_SKETCH",
             "parents":[],"source_id":parent["sketch_id"]},
            {"node_id":"pad","kind":"PAD","parents":["sketch-source"],
             "depth_um":parent["features"][0]["depth_um"]},
            {"node_id":"pocket_through","kind":"POCKET",
             "parents":["pad"],"hole_ids":[h["id"] for h in parent["seed"]["holes"]]},
        ],
        "candidate_revisions":copy.deepcopy(CANDIDATES),
        "selected_candidate":"NONE",
        "branches_constructed":0,
        "branch_permission":"EXPLICIT_SOFTWARE_ONLY",
        "fabrication_permission":False,
        "source_mutation":False,
        "status":"PROPOSAL_ONLY",
    }
    return _sealed(body,"tree_id","static-os-cad-feature-tree-v0:")


def verify_tree(value: Any) -> dict:
    tree=_check_seal(value,"tree_id","static-os-cad-feature-tree-v0:")
    require(tree==plan_tree(tree["root_sketch"]),
            "FEATURE_TREE_NOT_RECONSTRUCTIBLE")
    return tree


def choose(tree: Any, selection: Any) -> dict:
    p=verify_tree(tree)
    require(type(selection) is dict and set(selection)=={
        "schema","tree_id","candidate_id","owner_id","approved",
        "execution_scope",
    },"EXACT_FEATURE_SELECTION_REQUIRED")
    require(selection["schema"]==SELECTION
            and selection["tree_id"]==p["tree_id"]
            and selection["approved"] is True
            and type(selection["owner_id"]) is str
            and IDENT.fullmatch(selection["owner_id"])
            and selection["execution_scope"]=="SOFTWARE_CAD_KERNEL_AND_SIGNED_HOLD",
            "OWNER_APPROVAL_DOES_NOT_AUTHORIZE_THIS_FEATURE")
    found=[item for item in p["candidate_revisions"]
           if item["id"]==selection["candidate_id"]]
    require(len(found)==1,"UNOWNED_FEATURE_BRANCH")
    return found[0]


def compile_selected(tree: Any, selection: Any) -> dict:
    p=verify_tree(tree)
    target=choose(p,selection)
    base=p["root_sketch"]
    seed=copy.deepcopy(base["seed"])
    seed["revision_parent_id"]=base["sketch_id"]
    if target["id"]=="pad-deeper":
        new=seed["features"][0]["depth_um"]+target["delta_um"]
        require(new <= 30_000, "FEATURE_PAD_DEPTH_OUT_OF_BOUNDS")
        seed["features"][0]["depth_um"]=new
    elif target["id"]=="bore-wider":
        new=seed["holes"][0]["radius_um"]+target["delta_um"]
        require(new<=25_000,"FEATURE_HOLE_RADIUS_OUT_OF_BOUNDS")
        seed["holes"][0]["radius_um"]=new
    else:
        raise Hold("UNKNOWN_FEATURE_OPERATION")
    revision=compile_sketch(seed,base["cad_parent"])
    require(revision["constraint_report"]["state"]=="SOLVED"
            and revision["status"]=="SKETCH_CANDIDATE_ONLY"
            and revision["sketch_id"]!=base["sketch_id"]
            and revision["seed"]["revision_parent_id"]==base["sketch_id"],
            "FEATURE_BRANCH_NOT_GEOMETRICALLY_SOLVED")
    return revision


def branch_witness(tree: dict, choice: dict, revision: dict) -> dict:
    return {
        "schema":BRANCH,
        "tree_id":tree["tree_id"],
        "selected_candidate_id":choice["id"],
        "parent_sketch_id":tree["parent_sketch_id"],
        "selected_revision_sketch_id":revision["sketch_id"],
        "alternatives_not_executed":[c["id"] for c in tree["candidate_revisions"]
                                     if c["id"]!=choice["id"]],
        "owner_choice":"EXPLICIT_LOCAL_SOFTWARE_SELECTION",
        "construction_authorized":False,
    }


def verify_witness(witness: dict, tree: dict, choice: dict, revision: dict) -> dict:
    expected=branch_witness(tree,choice,revision)
    require(witness==expected,"CAD_BRANCH_WITNESS_NOT_RECONSTRUCTIBLE")
    return witness


def verify_branch_result(tree: Any, selection: Any,
                         revision: Any, witness: Any) -> dict:
    p=verify_tree(tree)
    c=choose(p,selection)
    expected=compile_selected(p,selection)
    require(revision==expected,"CAD_FEATURE_REVISION_CHANGED")
    verify_witness(witness,p,c,revision)
    return {"tree":p,"choice":c,"revision":expected,"witness":witness}
