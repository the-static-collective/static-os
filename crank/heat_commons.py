"""KETTLENODE-002 / HEAT COMMONS: an inert thermodynamic routing specimen.

It models bounded thermal transfers, not plumbing, generated electricity,
hardware control, or verified physical measurements. No actuator interfaces.
Thermal-energy state and signed authority remain external to this simulation.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from crank.runtime import digest, Refuse

WORLD_SCHEMA = "static-os.heat-commons-world/v0"
REQUEST_SCHEMA = "static-os.heat-route-request/v0"
RECEIPT_SCHEMA = "static-os.heat-route-receipt/v0"
MEDIUMS = {"sealed-thermal", "fish-water", "nutrient-water", "compost-side",
           "potable-water", "air-side", "ground-side"}
KINDS = {"store", "producer", "load", "sink"}
MAX_VALUE = 10**15


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise Refuse(reason)


def integer(x: Any, label: str, *, minimum: int = 0) -> int:
    require(type(x) is int and minimum <= x <= MAX_VALUE, f"{label} out of bounds")
    return x


def validate_world(world: Any) -> dict[str, Any]:
    require(isinstance(world, dict) and set(world) == {
        "schema", "evidence_kind", "nodes", "exchangers", "spent_request_ids",
        "receipts"}, "world fields changed")
    require(world["schema"] == WORLD_SCHEMA, "unsupported world schema")
    require(world["evidence_kind"] == "simulation-only", "unearned measurement claim")
    nodes = world["nodes"]
    require(isinstance(nodes, dict) and len(nodes) >= 2, "at least two nodes required")
    for name, node in nodes.items():
        require(isinstance(name, str) and bool(name) and isinstance(node, dict),
                "invalid thermal node")
        require(set(node) == {"kind", "medium", "heat_capacity_j_per_centidegree",
                "thermal_energy_j", "min_centi_c", "max_centi_c", "circulation_ok",
                "oxygen_ok"}, "node fields changed")
        require(node["kind"] in KINDS, "invalid node kind")
        require(node["medium"] in MEDIUMS, "invalid medium")
        capacity = integer(node["heat_capacity_j_per_centidegree"], "heat capacity",
                           minimum=1)
        energy = integer(node["thermal_energy_j"], "thermal energy")
        minimum = integer(node["min_centi_c"], "minimum centi-c")
        maximum = integer(node["max_centi_c"], "maximum centi-c")
        require(minimum < maximum, "node temperature limits inverted")
        require(minimum * capacity <= energy <= maximum * capacity,
                "node exceeds temperature limits")
        require(type(node["circulation_ok"]) is bool and
                type(node["oxygen_ok"]) is bool, "invalid life-support flags")
    exchangers = world["exchangers"]
    require(isinstance(exchangers, dict), "exchanger registry required")
    for ex_id, ex in exchangers.items():
        require(isinstance(ex_id, str) and bool(ex_id) and isinstance(ex, dict),
                "invalid exchanger")
        require(set(ex) == {"media", "max_transfer_j", "isolated", "simulation_only"},
                "exchanger fields changed")
        require(isinstance(ex["media"], list) and len(ex["media"]) == 2 and
                all(isinstance(v, str) and v in MEDIUMS for v in ex["media"]) and
                ex["media"] == sorted(ex["media"]) and ex["media"][0] != ex["media"][1],
                "exchanger must join two distinct declared media")
        integer(ex["max_transfer_j"], "exchanger max transfer", minimum=1)
        require(ex["isolated"] is True and ex["simulation_only"] is True,
                "only isolated simulated exchangers allowed")
    spent = world["spent_request_ids"]
    receipts = world["receipts"]
    require(isinstance(spent, list) and all(isinstance(t, str) and t for t in spent)
            and len(spent) == len(set(spent)), "spent request ids invalid")
    require(isinstance(receipts, list) and len(receipts) == len(spent),
            "receipt count mismatch")
    for index, receipt in enumerate(receipts):
        require(isinstance(receipt, dict) and set(receipt) == {
            "schema", "request_id", "route_sha256", "transfer_j",
            "world_before_sha256", "authority_effect", "actual_heat_moved",
            "fluid_interconnection", "electrical_energy_generated",
            "actuator_command_emitted", "signature_status", "receipt_sha256",
        }, "receipt fields changed")
        require(receipt["schema"] == RECEIPT_SCHEMA and
                receipt["request_id"] == spent[index], "receipt identity mismatch")
        body = {k: v for k, v in receipt.items() if k != "receipt_sha256"}
        require(receipt["receipt_sha256"] == digest(body), "receipt hash mismatch")
        require(receipt["authority_effect"] == "none" and
                receipt["actual_heat_moved"] is False and
                receipt["fluid_interconnection"] is False and
                receipt["electrical_energy_generated"] is False and
                receipt["actuator_command_emitted"] is False and
                receipt["signature_status"] == "unsigned-simulation",
                "receipt exceeds simulated evidence")
    return world


def temperature_centi_c(node: dict[str, Any]) -> int:
    return node["thermal_energy_j"] // node["heat_capacity_j_per_centidegree"]


def evaluate(world: dict[str, Any], request: Any) -> dict[str, Any]:
    """Inert feasibility check, never performs simulated or physical transfer."""
    validate_world(world)
    require(isinstance(request, dict) and set(request) == {
        "schema", "request_id", "source", "destination", "transfer_j",
        "exchanger_id", "selection", "authority_request", "admission_request",
    }, "route request fields changed")
    require(request["schema"] == REQUEST_SCHEMA, "unsupported route request")
    require(isinstance(request["request_id"], str) and bool(request["request_id"]),
            "request id required")
    require(request["request_id"] not in world["spent_request_ids"],
            "request already spent")
    require(request["selection"] == "human" and
            request["authority_request"] == "none" and
            request["admission_request"] == "none", "route cannot gain authority")
    a_id, b_id = request["source"], request["destination"]
    require(isinstance(a_id, str) and isinstance(b_id, str) and
            a_id in world["nodes"] and b_id in world["nodes"] and a_id != b_id,
            "unknown or identical endpoint")
    a, b = world["nodes"][a_id], world["nodes"][b_id]
    require(a["circulation_ok"] and b["circulation_ok"],
            "circulation unavailable; fail closed")
    for node in (a, b):
        if node["medium"] == "fish-water":
            require(node["oxygen_ok"], "fish life-support condition unavailable")
    require(temperature_centi_c(a) > temperature_centi_c(b),
            "uphill or isothermal passive heat route refused")
    q = integer(request["transfer_j"], "transfer", minimum=1)
    require(q <= a["thermal_energy_j"], "energy cannot be fabricated")
    ca, cb = a["heat_capacity_j_per_centidegree"], b["heat_capacity_j_per_centidegree"]
    # From E_a / C_a >= E_b / C_b after transfer, without fractions or floats.
    max_equalize = (a["thermal_energy_j"] * cb -
                    b["thermal_energy_j"] * ca) // (ca + cb)
    require(q <= max_equalize, "route would invert thermal gradient")
    require(a["thermal_energy_j"] - q >= a["min_centi_c"] * ca,
            "source would undercool")
    require(b["thermal_energy_j"] + q <= b["max_centi_c"] * cb,
            "destination would overheat")
    ex_id = request["exchanger_id"]
    if a["medium"] != b["medium"]:
        require(isinstance(ex_id, str) and ex_id in world["exchangers"],
                "isolating exchanger required for distinct media")
        ex = world["exchangers"][ex_id]
        require(ex["media"] == sorted([a["medium"], b["medium"]]),
                "exchanger media incompatible")
        require(q <= ex["max_transfer_j"], "exchanger throughput exceeded")
    else:
        require(a["medium"] == "sealed-thermal" and ex_id is None,
                "direct connection forbidden except sealed-thermal to sealed-thermal")
    return {
        "feasible": True,
        "proposed_heat_j": q,
        "source_before_centi_c": temperature_centi_c(a),
        "destination_before_centi_c": temperature_centi_c(b),
        "isolation": "modeled-separate-fluid-circuits" if ex_id is not None
                     else "modeled-sealed-thermal",
        "physical_actuation": False,
    }


def simulate_route(world: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    """Returns a NEW simulation world and an unsigned receipt; no hardware I/O."""
    feasible = evaluate(world, request)
    updated = deepcopy(world)
    a = updated["nodes"][request["source"]]
    b = updated["nodes"][request["destination"]]
    q = feasible["proposed_heat_j"]
    total_before = sum(n["thermal_energy_j"] for n in world["nodes"].values())
    a["thermal_energy_j"] -= q
    b["thermal_energy_j"] += q
    require(total_before == sum(n["thermal_energy_j"] for n in updated["nodes"].values()),
            "heat balance changed in routing")
    receipt = {
        "schema": RECEIPT_SCHEMA, "request_id": request["request_id"],
        "route_sha256": digest(request), "transfer_j": q,
        "world_before_sha256": digest(world),
        "authority_effect": "none",
        "actual_heat_moved": False, "fluid_interconnection": False,
        "electrical_energy_generated": False,
        "actuator_command_emitted": False,
        "signature_status": "unsigned-simulation",
    }
    receipt["receipt_sha256"] = digest(receipt)
    updated["spent_request_ids"].append(request["request_id"])
    updated["receipts"].append(receipt)
    validate_world(updated)
    return {"world": updated, "receipt": receipt, "feasibility": feasible}
