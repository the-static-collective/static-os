"""STATIC-CAD-006: one selected feature branch -> OCCT -> reLATTE -> GOATnote.

GOATnote owns the journal projection and its browser's note/margin lifecycle.
STATIC OS owns engineering evidence and explicit software selection. reLATTE
owns native signatures and receiving world's HOLD. All readback is cold and
never reconstructs solids or reissues crossings.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from crank.runtime import digest
from question_first.session import Hold, require, _sealed, _check_seal
from question_first.feature_tree import (
    TREE, SELECTION, verify_tree, choose, compile_selected,
    branch_witness, verify_branch_result,
)
from question_first.solid_body import build_solid,verify_files
from question_first.solid_relatte import cross, verify_native

ROOT=Path(__file__).resolve().parents[1]
HANDOFF="goatnote.cad-journal-handoff/v0"
PREVIEW="static-os.goatnote-journal-preview/v0"
MANIFEST="static-os.cad-goatnote-branch-package/v0"
WRITTEN=["tree.json","selection.json","branch-sketch.json",
         "branch-provenance.json","goatnote-handoff.json",
         "goatnote-preview.json"]
PRIVATE=["receiver-key.json"]


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write(path: Path, payload: dict) -> None:
    fd=os.open(str(path),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"w",encoding="utf-8") as out:
        json.dump(payload,out,sort_keys=True,indent=2)
        out.write("\n")
        out.flush()
        os.fsync(out.fileno())


def _native_goatnote(handoff_file: Path) -> dict:
    program=ROOT/"scripts/goatnote-cad-bridge.mjs"
    native=ROOT/"external/GOATnote/cad-journal.mjs"
    require(program.is_file() and native.is_file(),
            "PINNED_GOATNOTE_SOURCE_NOT_PRESENT")
    try:
        run=subprocess.run(
            ["node",str(program),str(handoff_file)],
            text=True,capture_output=True,cwd=ROOT,timeout=20,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        raise Hold("NATIVE_GOATNOTE_JOURNAL_NOT_AVAILABLE") from exc
    require(run.returncode==0,"NATIVE_GOATNOTE_JOURNAL_REFUSED:"+run.stderr[:180])
    try:
        value=json.loads(run.stdout)
    except json.JSONDecodeError as exc:
        raise Hold("GOATNOTE_BAD_PROJECTION_JSON") from exc
    require(value.get("schema")==PREVIEW
            and value.get("browser_notebook_modified") is False
            and value.get("import_status")=="CANDIDATE_ONLY"
            and value.get("source_note",{}).get("cadJournal",{}).get(
                "goatnote_signature_verified") is False,
            "GOATNOTE_JOURNAL_SILENT_ADMISSION")
    return value


def handoff_from_native(folder: Path, witness: dict) -> dict:
    manifest,trace,report=verify_files(folder)
    verification=verify_native(folder)
    relatte=json.loads((folder/"relatte-evidence.json").read_text())
    envelope=relatte["result"]["crossing"]
    require(verification["source_trace_id"]==trace["trace_id"]
            and verification["crossing_id"]==envelope["crossing_id"]
            and envelope["created_at"].endswith("Z"),
            "SIGNED_RELATTE_SOURCE_DOES_NOT_MATCH_CAD")
    require(witness["selected_revision_sketch_id"]==trace["source_sketch_id"],
            "SELECTED_BRANCH_NOT_SOURCE_OF_SIGNED_CROSSING")
    return {
        "schema":HANDOFF,
        "evidence":{
            "created_at":envelope["created_at"],
            "crossing_id":verification["crossing_id"],
            "receive_receipt_id":verification["receive_receipt_id"],
            "disposition_receipt_id":verification["disposition_receipt_id"],
            "native_verification":verification["status"],
            "manifest_id":manifest["manifest_id"],
            "trace_id":trace["trace_id"],
            "source_sketch_id":trace["source_sketch_id"],
            "disposition":verification["disposition"],
            "fabrication_grant":verification["fabrication_grant"],
        },
        "trace":trace,
        "branch":witness,
    }


def _manifest(directory: Path, tree: dict, choice: dict,
              branch: dict, native: dict, preview: dict) -> dict:
    body={
        "schema":MANIFEST,
        "tree_id":tree["tree_id"],
        "selected_candidate_id":choice["id"],
        "branch_sketch_id":branch["sketch_id"],
        "parent_sketch_id":tree["parent_sketch_id"],
        "relatte_crossing_id":native["evidence"]["crossing_id"],
        "goatnote_source_note_id":preview["source_note"]["id"],
        "artifact_sha256":{name:_sha(directory/name) for name in sorted(WRITTEN)},
        "native_relatte_signature_checked":True,
        "native_goatnote_module_checked":True,
        "browser_imported":False,
        "unselected_branch_executed":False,
        "physical_fabrication":False,
        "status":"SOURCE_BRANCH_REVIEW_CANDIDATE_ONLY",
    }
    return _sealed(body,"manifest_id","static-os-cad-goatnote-package-v0:")


def execute_branch(tree: Any, selection: Any, *, output_root: Path,
                   private_relatte_root: Path) -> dict:
    p=verify_tree(tree)
    candidate=choose(p,selection)
    branch=compile_selected(p,selection)
    witness=branch_witness(p,candidate,branch)
    folder=Path(output_root).expanduser().resolve()
    private=Path(private_relatte_root).expanduser().resolve()
    require(not folder.exists() and not private.exists(),
            "FEATURE_BRANCH_OCCURRENCE_EXISTS_NO_AUTORETRY")
    require(private != folder
            and not str(private).startswith(str(folder)+os.sep)
            and not str(folder).startswith(str(private)+os.sep),
            "RELATTE_PRIVATE_KEY_ROOT_MUST_BE_SEPARATE")
    folder.parent.mkdir(parents=True,exist_ok=True)
    folder.mkdir(mode=0o700,exist_ok=False)
    _write(folder/"tree.json",p)
    _write(folder/"selection.json",selection)
    _write(folder/"branch-sketch.json",branch)
    _write(folder/"branch-provenance.json",witness)
    # No CAD/GHoT execution occurs before exactly one explicit selection.
    build_solid(branch,folder/"solid")
    cross(folder/"solid",private)
    handoff=handoff_from_native(folder/"solid",witness)
    _write(folder/"goatnote-handoff.json",handoff)
    preview=_native_goatnote(folder/"goatnote-handoff.json")
    _write(folder/"goatnote-preview.json",preview)
    manifest=_manifest(folder,p,candidate,branch,handoff,preview)
    _write(folder/"manifest.json",manifest)
    return {"manifest":manifest,"handoff":handoff,"preview":preview}


def verify_branch(output_root: Path) -> dict:
    folder=Path(output_root).expanduser().resolve()
    stored=json.loads((folder/"manifest.json").read_text())
    _check_seal(stored,"manifest_id","static-os-cad-goatnote-package-v0:")
    require(stored.get("schema")==MANIFEST
            and stored.get("browser_imported") is False
            and stored.get("unselected_branch_executed") is False
            and stored.get("physical_fabrication") is False,
            "INVALID_FEATURE_JOURNAL_PACKAGE")
    p=json.loads((folder/"tree.json").read_text())
    selection=json.loads((folder/"selection.json").read_text())
    branch=json.loads((folder/"branch-sketch.json").read_text())
    witness=json.loads((folder/"branch-provenance.json").read_text())
    result=verify_branch_result(p,selection,branch,witness)
    handoff=handoff_from_native(folder/"solid",witness)
    require(handoff==json.loads((folder/"goatnote-handoff.json").read_text()),
            "GOATNOTE_HANDOFF_DOES_NOT_MATCH_SIGNED_SOURCE")
    preview=_native_goatnote(folder/"goatnote-handoff.json")
    require(preview==json.loads((folder/"goatnote-preview.json").read_text()),
            "GOATNOTE_NATIVE_PROJECTION_DIFFERS")
    require(_manifest(folder,p,result["choice"],branch,handoff,preview)==stored,
            "GOATNOTE_PACKAGE_MANIFEST_CHANGED")
    return stored
