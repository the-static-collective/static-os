"""STATIC OS FABRICATION-013: exact source-bound dispatch *proposal*.

No network transfer, printer API, physical receipt, license or authority.
All source facts cold-recomputed from the original signed CAD, actual sliced
G-code and the independently authored 012 printer-compatibility field.
"""
from __future__ import annotations
from pathlib import Path
from typing import Any
from crank.runtime import digest
from question_first.printer_field import compile_field
from question_first.session import Hold,require

SCHEMA="static-os.fabrication-request/v0"
SELECTION="static-os.fabrication-human-selection/v0"
PARTICIPANT_LIMIT=3

def request_from_original(source:Path,packet:Path,fleet:Any,selection:Any)->dict:
    view=compile_field(source,packet,fleet)
    require(type(selection) is dict and set(selection)=={
        "schema","operator_ref","purpose_ref","requested_machine_ids","authority_effect"},
        "SELECTION_EXACT_FIELDS_REQUIRED")
    require(selection["schema"]==SELECTION and
        isinstance(selection["operator_ref"],str) and 3<=len(selection["operator_ref"])<=100 and
        isinstance(selection["purpose_ref"],str) and 3<=len(selection["purpose_ref"])<=100 and
        selection["authority_effect"]=="PROPOSE_ONLY",
        "SELECTION_MUST_HAVE_EXPLICIT_OPERATOR_WITH_NO_AUTHORITY")
    names=selection["requested_machine_ids"]
    require(type(names) is list and len(names)==PARTICIPANT_LIMIT and
            len(set(names))==PARTICIPANT_LIMIT and
            all(type(n) is str for n in names),
            "THREE_EXPLICIT_DISTINCT_NODES_REQUIRED")
    candidates={m["machine_id"]:m for m in view["machines"]}
    require(all(n in candidates for n in names),"NO_SILENT_MACHINE_DISCOVERY")
    selected=[candidates[n] for n in names]
    require(all(m["physical_execution_authorized"] is False
                and m["machine_connected"] is False
                and m["physical_output_created"] is False for m in selected),
            "MACHINE_CANDIDATE_CANNOT_GRANT_WORK")
    body={
        "schema":SCHEMA,
        "source_repository":"the-static-collective/static-os",
        "original_field_id":view["field_id"],
        "original_signed_cad_crossing_id":__import__("json").loads(
             (Path(packet)/"packet.json").read_text())["source_crossing_id"],
        "source_design_candidate_id":view["source_design_candidate_id"],
        "original_print_packet_id":view["source_print_packet_id"],
        "operator_ref":selection["operator_ref"],
        "purpose_ref":selection["purpose_ref"],
        "requested_node_count":PARTICIPANT_LIMIT,
        "selected_nodes":[{
            "machine_id":m["machine_id"],
            "technology":m["technology"],
            "published_compatibility":m["compatibility_status"],
            "reason":m["blocking_reason"],
            "hardware_authenticated":False,
            "physical_print_permission":False,
        } for m in selected],
        "source_selection_digest":digest(selection),
        "state":"FABRICATION_PROPOSAL_ONLY",
        "owner_machine_grants_included":False,
        "fabrication_occurred":False,
        "physical_parts":0,
        "new_money":0,
    }
    return {**body,"request_id":"static-os-fabrication-013:"+digest(body)}

def verify_request(source:Path,packet:Path,fleet:Any,selection:Any,request:Any)->dict:
    require(type(request) is dict,"REQUEST_OBJECT_REQUIRED")
    expected=request_from_original(source,packet,fleet,selection)
    require(request==expected,"SOURCE_OR_SELECTION_NOT_CURRENT")
    return expected
