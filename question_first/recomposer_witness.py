"""RECOMPOSER-002: Toaster-inspired evidence -> memory -> family -> witness.

Source-inspired generic contract, NOT an import of Haunted Toaster's execution
or creative authority. All outputs are typed local PROPOSAL_ONLY suggestions;
no network, storage, model inference, render, approval or external operation.
"""
from __future__ import annotations

from collections import Counter
import re
from copy import deepcopy
from typing import Any

from question_first.recomposer import (
    CATALOGUE, PLAN, _digest, verify_state,
)

PROJECTION = "static-os.witness-memory-projection/v0"
CAPSULE = "static-os.witness-memory-capsule/v0"
FAMILY = "static-os.witness-candidate-family/v0"
TRACE = "static-os.witness-influence-trace/v0"
ARTIFACT = "static-os.artifact-observation/v0"
RECENT_WINDOW = 12
MAX_CANDIDATES = 6
PRESSURE_CEILING = 12


def _require(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def witness_artifact(plan: dict, topic: str, output_sha256: str,
                     *, consent: bool = False) -> dict:
    """Build a *self-attested* output receipt supplied by an explicit caller.

    The caller computes the output hash from actual materialized bytes.
    We cannot independently authenticate that assertion and do not store it.
    """
    _require(consent is True, "HOLD_ARTIFACT_MEMORY_NOT_AUTHORIZED")
    _require(isinstance(plan, dict) and plan.get("schema") == PLAN and
             topic in plan.get("topics", []) and
             isinstance(plan.get("plan_id"), str),
             "HOLD_UNOWNED_ARTIFACT")
    _require(isinstance(output_sha256, str) and
             bool(re.fullmatch(r"[a-f0-9]{64}", output_sha256)),
             "INVALID_ARTIFACT_DIGEST")
    body = {
        "schema": ARTIFACT, "source_plan_id": plan["plan_id"],
        "topic": topic, "output_sha256": output_sha256,
        "status": "SELF_ATTESTED_MATERIALIZED_OUTPUT",
        "authority": "none", "verified_service": False,
    }
    return {**body, "observation_id": "artifact-observation:" + _digest(body)}


def _validate_artifacts(receipts: object) -> list[dict]:
    _require(isinstance(receipts, (tuple, list)) and len(receipts) <= 1000,
             "INVALID_ARTIFACT_RECEIPT_COLLECTION")
    distinct = {}
    for receipt in receipts:
        _require(isinstance(receipt, dict) and
                 set(receipt) == {"schema", "source_plan_id", "topic",
                                  "output_sha256", "status", "authority",
                                  "verified_service", "observation_id"} and
                 receipt["schema"] == ARTIFACT and
                 receipt["status"] == "SELF_ATTESTED_MATERIALIZED_OUTPUT" and
                 receipt["authority"] == "none" and
                 receipt["verified_service"] is False and
                 receipt["topic"] in CATALOGUE and
                 isinstance(receipt["source_plan_id"], str) and
                 bool(re.fullmatch(r"[a-f0-9]{64}", str(receipt["output_sha256"]))),
                 "INVALID_ARTIFACT_RECEIPT")
        body = {k: v for k, v in receipt.items() if k != "observation_id"}
        _require(receipt["observation_id"] == "artifact-observation:" + _digest(body),
                 "ARTIFACT_CONTENT_ADDRESS_MISMATCH")
        _require(receipt["observation_id"] not in distinct,
                 "DUPLICATE_ARTIFACT_RECEIPT")
        distinct[receipt["observation_id"]] = deepcopy(receipt)
    return [distinct[key] for key in sorted(distinct)]


def _sorted_counts(counter: Counter) -> dict:
    return {name: int(counter.get(name, 0)) for name in sorted(CATALOGUE)}


def project_receipt_memory(state: dict, artifact_receipts=()) -> dict:
    """Rebuild from attributable *self-reported* consent events, never mutate."""
    verify_state(state)
    events = state["events"]
    artifacts = _validate_artifacts(artifact_receipts)
    produced = Counter(x["topic"] for x in artifacts)
    tried = Counter(x["selected"] for x in events)
    helpful = Counter(x["selected"] for x in events if x["outcome"] == "helpful")
    refused = Counter(x["selected"] for x in events if x["outcome"] == "not_helpful")
    recent = Counter(x["selected"] for x in events[-RECENT_WINDOW:])
    core = {
        "schema": PROJECTION,
        "source_schema": state["schema"],
        "archive_cut": state["head"],
        "revision": state["revision"],
        "total_verdicts": len(events),
        "total_artifact_observations": len(artifacts),
        "observed_artifacts": _sorted_counts(produced),
        "tried": _sorted_counts(tried),
        "helpful": _sorted_counts(helpful),
        "not_helpful": _sorted_counts(refused),
        "recent": _sorted_counts(recent),
        "sources": {
            name: sorted([x["hash"] for x in events if x["selected"] == name] +
                         [x["observation_id"] for x in artifacts if x["topic"] == name])
            for name in sorted(CATALOGUE)
        },
        "policy": "witness-learning-not-service-verification",
    }
    return {**core, "projection_id": "witness-projection:" + _digest(core)}


def _verify_plan(state: dict, plan: dict) -> None:
    _require(isinstance(plan, dict) and plan.get("schema") == PLAN,
             "PROPOSAL_PLAN_REQUIRED")
    body = {k: v for k, v in plan.items() if k != "plan_id"}
    _require(plan.get("plan_id") == "recomposer-plan:" + _digest(body),
             "PLAN_CONTENT_ADDRESS_MISMATCH")
    _require(plan.get("state_revision") == state["revision"] and
             plan.get("state_head") == state["head"], "STALE_PLAN")
    topics = plan.get("topics")
    _require(isinstance(topics, list) and 1 <= len(topics) <= 2 and
             len(set(topics)) == len(topics) and
             all(t in CATALOGUE for t in topics), "INVALID_TOPIC_SET")
    _require(plan.get("doors") == [CATALOGUE[t]["url"] for t in topics] and
             plan.get("status") == "PROPOSAL_ONLY" and
             plan.get("external_effect") is False and
             plan.get("public_input_saved") is False, "INVALID_PROPOSAL_AUTHORITY")


def compile_memory_capsule(state: dict, plan: dict, artifact_receipts=()) -> dict:
    """Only topics the question's source-owned plan actually offered are legal."""
    _verify_plan(state, plan)
    projection = project_receipt_memory(state, artifact_receipts)
    topics = plan["topics"]
    pressures = []
    low_count = min(projection["tried"][x] + projection["observed_artifacts"][x] for x in topics)
    for topic in topics:
        refs = projection["sources"][topic] or [projection["archive_cut"]]
        observed = projection["tried"][topic] + projection["observed_artifacts"][topic]
        recent = projection["recent"][topic]
        liked = projection["helpful"][topic]
        disliked = projection["not_helpful"][topic]
        if observed == low_count:
            pressures.append({"kind": "coverage-explore", "target": topic,
                              "strength": 1, "evidence_refs": refs})
        if liked:
            pressures.append({"kind": "relationship-favor", "target": topic,
                              "strength": min(liked, 6), "evidence_refs": refs})
        if disliked:
            pressures.append({"kind": "counterexampled", "target": topic,
                              "strength": min(disliked, 6), "evidence_refs": refs})
        if recent >= 2 and len(topics) > 1:
            pressures.append({"kind": "saturation-avoid", "target": topic,
                              "strength": min(recent, 6), "evidence_refs": refs})
    order = {"coverage-explore": 0, "relationship-favor": 1,
             "counterexampled": 2, "saturation-avoid": 3}
    pressures.sort(key=lambda x: (order[x["kind"]], -x["strength"], x["target"]))
    core = {
        "schema": CAPSULE, "plan_id": plan["plan_id"],
        "projection_id": projection["projection_id"],
        "archive_cut": projection["archive_cut"],
        "allowed_topics": topics[:],
        "pressures": pressures[:PRESSURE_CEILING],
        "status": "INFLUENCE_ONLY",
        "authority": "none",
    }
    return {**core, "capsule_id": "witness-capsule:" + _digest(core)}


def compile_candidate_family(state: dict, plan: dict, artifact_receipts=()) -> dict:
    """A constrained candidate family, up to six distinct path compositions.

    Unlike Toaster's visual six-up, this may produce fewer than six candidates
    when source-grounded topic diversity is insufficient. No fake diversity.
    """
    _verify_plan(state, plan)
    capsule = compile_memory_capsule(state, plan, artifact_receipts)
    projection = project_receipt_memory(state, artifact_receipts)
    topics = plan["topics"]
    candidates = []
    seen = set()

    def offer(tag: str, sequence: list[str], why: str) -> None:
        if len(candidates) >= MAX_CANDIDATES:
            return
        if not sequence or not set(sequence).issubset(topics):
            return
        key = tuple(sequence)
        if key in seen:
            return
        seen.add(key)
        # A route sequence is a *proposed* bounded display plan, not a
        # GHoT execution graph or Haunted Toaster ResolvedTimeline.
        body = {
            "index": len(candidates), "policy": tag, "routes": sequence[:],
            "doors": [CATALOGUE[t]["url"] for t in sequence],
            "why": why, "status": "PROPOSAL_ONLY",
            "external_effect": False, "requires_separate_choice": True,
        }
        candidates.append({**body, "candidate_id": "route-proposal:" + _digest(body)})

    offer("baseline", topics, "Follow the present question and current policy.")
    least = min(topics, key=lambda t: (projection["tried"][t] + projection["observed_artifacts"][t], t))
    offer("coverage-explore", [least], "A source-grounded route used least in consented feedback.")
    liked = [t for t in topics if projection["helpful"][t]]
    if liked:
        favorite = max(liked, key=lambda t: (projection["helpful"][t], -projection["not_helpful"][t], t))
        offer("relationship-favor", [favorite], "Past voluntary verdicts reported helpful.")
    if len(topics) > 1:
        offer("counterpoint", [topics[1], topics[0]],
              "Try the same two relevant doors in a different order.")
        offer("small-first", [topics[0]],
              "Start with a single bounded route instead of combining two.")
        offer("second-first", [topics[1]],
              "Start with the other relevant route and let the human decide.")
    trace = {
        "schema": TRACE, "plan_id": plan["plan_id"],
        "capsule_id": capsule["capsule_id"],
        "parent_archive_cut": capsule["archive_cut"],
        "evidence_refs": sorted({e for p in capsule["pressures"]
                                 for e in p["evidence_refs"]}),
        "pressure_kinds": [p["kind"] for p in capsule["pressures"]],
        "candidate_ids": [c["candidate_id"] for c in candidates],
        "authority": "none",
    }
    trace["trace_id"] = "witness-trace:" + _digest(trace)
    core = {
        "schema": FAMILY, "source_plan_id": plan["plan_id"],
        "capsule": capsule, "influence_trace": trace,
        "candidates": candidates, "status": "PROPOSAL_ONLY",
        "accepted_candidate": None, "external_effect": False,
        "toaster_execution_authority": False,
    }
    return {**core, "family_id": "witness-family:" + _digest(core)}
