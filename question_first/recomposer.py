"""RECOMPOSER-001: deterministic, bounded, typed self-reassembly proof.

No AI model, generated code, network calls, I/O, tracking or silent memory.
Input text is held only for this call; state persists solely when a separate
caller explicitly records a user-approved feedback event.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import re

SCHEMA = "static-os.recomposer/v0"
PLAN = "static-os.recomposer-plan/v0"
EVENT = "static-os.recomposer-feedback/v0"
MAX_TEXT = 320
MAX_OPERATORS = 8
WEIGHT_LIMIT = 6

# Named capabilities are a small, fixed operator catalogue; destinations
# are options, not promises of available people, services or permission.
CATALOGUE = {
    "food": {"terms": ("food", "garden", "farm", "grocery", "vegetables", "produce", "bread", "soup", "milk"), "url": "https://garden.abundent.org/"},
    "music": {"terms": ("music", "song", "guitar", "worship", "festival", "beat", "sing", "concert"), "url": "https://abundent.org/jubilee/"},
    "table": {"terms": ("table", "neighbors", "meet", "potluck", "gather", "community", "dinner"), "url": "https://table.abundent.org/"},
    "paper": {"terms": ("paper", "newspaper", "story", "write", "publish", "news"), "url": "https://abundent.org/paper/"},
    "question": {"terms": ("question", "idea", "what if", "wonder", "invent", "make", "build"), "url": "https://connections.abundent.org/"},
}
DEFAULT = ("question", "paper")


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _digest(value: object) -> str:
    return sha256(_canonical(value)).hexdigest()


def genesis() -> dict:
    return {"schema": SCHEMA, "revision": 0,
            "weights": {name: 0 for name in CATALOGUE},
            "recipes": [], "events": [], "head": "GENESIS"}


def _fail_if(condition: bool, message: str) -> None:
    if condition:
        raise ValueError(message)


def _validate_recipe(recipe: object) -> tuple[str, str]:
    _fail_if(not isinstance(recipe, list) or len(recipe) != 2 or
             any(not isinstance(x, str) or x not in CATALOGUE for x in recipe) or
             recipe != sorted(set(recipe)), "INVALID_RECIPE")
    return recipe[0], recipe[1]


def verify_state(state: dict) -> None:
    """Cold-replay feedback; hash chain detects accidents, not owner forgery."""
    _fail_if(not isinstance(state, dict) or set(state) !=
             {"schema", "revision", "weights", "recipes", "events", "head"} or
             state["schema"] != SCHEMA, "INVALID_STATE")
    weights = {name: 0 for name in CATALOGUE}
    recipes: list[list[str]] = []
    head = "GENESIS"
    _fail_if(not isinstance(state["events"], list) or len(state["events"]) > 1000,
             "INVALID_EVENT_HISTORY")
    for number, event in enumerate(state["events"], 1):
        _fail_if(not isinstance(event, dict) or set(event) !=
                 {"schema", "revision", "plan_id", "selected", "outcome", "joined", "promoted", "prev", "hash"}
                 or event["schema"] != EVENT or event["revision"] != number or
                 event["prev"] != head or event["outcome"] not in ("helpful", "not_helpful") or
                 event["selected"] not in CATALOGUE or
                 type(event["promoted"]) is not bool or not isinstance(event["plan_id"], str),
                 "INVALID_EVENT")
        body = {k: v for k, v in event.items() if k != "hash"}
        _fail_if(event["hash"] != _digest(body), "EVENT_DIGEST_MISMATCH")
        if event["joined"] is not None:
            _validate_recipe(event["joined"])
        _fail_if(event["promoted"] and
                 (event["outcome"] != "helpful" or event["joined"] is None or
                  event["selected"] not in event["joined"]), "INVALID_PROMOTION")
        delta = 2 if event["outcome"] == "helpful" else -2
        who = event["selected"]
        weights[who] = max(-WEIGHT_LIMIT, min(WEIGHT_LIMIT, weights[who] + delta))
        if event["promoted"] and event["joined"] not in recipes:
            recipes.append(event["joined"])
        head = event["hash"]
    _fail_if(state["revision"] != len(state["events"]) or state["head"] != head or
             state["weights"] != weights or state["recipes"] != recipes,
             "STATE_REPLAY_MISMATCH")


def _terms(text: str, topic: str) -> int:
    return sum(bool(re.search(r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])", text))
               for term in CATALOGUE[topic]["terms"])


def compile_turn(state: dict, words: str) -> dict:
    """A new *runtime graph* on every turn, without rewriting its kernel."""
    verify_state(state)
    _fail_if(not isinstance(words, str) or len(words) > MAX_TEXT, "INVALID_INPUT_LENGTH")
    text = words.strip().lower()
    _fail_if(not text, "EMPTY_INPUT")
    hits = {topic: _terms(text, topic) for topic in CATALOGUE}
    matched = [topic for topic in CATALOGUE if hits[topic]]
    # Do not invent certainty from preference alone on an unknown question.
    eligible = matched or list(DEFAULT)
    ranked = sorted(eligible, key=lambda t: (-hits[t] * 10 - state["weights"][t], t))
    chosen = ranked[:2]
    # A proven, approved two-route macro can replace a longer assembly.
    # It changes the *graph*, not the executable kernel or anyone's authority.
    joined = sorted(chosen) if len(chosen) == 2 and len(matched) > 1 else None
    reused = joined if joined in state["recipes"] else None
    variant = bool(joined and reused is None)
    nodes = [{"id": "normalize", "accepts": "visitor-text", "emits": "tokens"}]
    edges: list[list[str]] = []
    if reused:
        macro = "join:" + "+".join(reused)
        nodes.extend((
            {"id": macro, "accepts": "tokens", "emits": "door-pair"},
            {"id": "present-pair", "accepts": "door-pair", "emits": "response"},
        ))
        edges.extend((["normalize", macro], [macro, "present-pair"]))
    else:
        for topic in chosen:
            nodes.extend((
                {"id": "detect:" + topic, "accepts": "tokens", "emits": "topic:" + topic},
                {"id": "route:" + topic, "accepts": "topic:" + topic, "emits": "door"},
            ))
            edges.extend((["normalize", "detect:" + topic], ["detect:" + topic, "route:" + topic]))
        nodes.append({"id": "present", "accepts": "door", "emits": "response"})
        for topic in chosen:
            edges.append(["route:" + topic, "present"])
    _fail_if(len(nodes) > MAX_OPERATORS or any(
        next(n for n in nodes if n["id"] == a)["emits"] !=
        next(n for n in nodes if n["id"] == b)["accepts"]
        for a, b in edges), "TYPE_OR_BUDGET_HOLD")
    body = {
        "schema": PLAN, "state_revision": state["revision"], "state_head": state["head"],
        "operators": nodes, "edges": edges, "topics": chosen,
        "operator_count": len(nodes),
        "ranked_scores": {topic: hits[topic] * 10 + state["weights"][topic] for topic in chosen},
        "doors": [CATALOGUE[t]["url"] for t in chosen],
        "candidate_recipe": joined if variant else None,
        "reused_recipe": reused,
        "uncertain": not bool(matched), "status": "PROPOSAL_ONLY",
        "public_input_saved": False, "external_effect": False,
    }
    return {**body, "plan_id": "recomposer-plan:" + _digest(body)}


def observe_feedback(state: dict, plan: dict, selected: str, outcome: str,
                     *, consent: bool = False, promote_recipe: bool = False) -> dict:
    """Record voluntary feedback, not independently verified usefulness.

    This is a state *proposal* returned to a caller; no I/O or persistence.
    """
    verify_state(state)
    _fail_if(consent is not True or outcome not in ("helpful", "not_helpful") or
             not isinstance(plan, dict), "HOLD_FEEDBACK_NOT_AUTHORIZED")
    plan_id = plan.get("plan_id")
    body = {k: v for k, v in plan.items() if k != "plan_id"}
    _fail_if(plan.get("schema") != PLAN or
             plan_id != "recomposer-plan:" + _digest(body) or
             plan.get("state_revision") != state["revision"] or
             plan.get("state_head") != state["head"] or
             selected not in plan.get("topics", []), "HOLD_STALE_OR_INVALID_PLAN")
    joined = plan.get("candidate_recipe") or plan.get("reused_recipe")
    if joined is not None:
        _validate_recipe(joined)
    _fail_if(promote_recipe and
             (outcome != "helpful" or plan.get("candidate_recipe") is None or
              selected not in joined), "HOLD_UNSUPPORTED_PROMOTION")
    data = {"schema": EVENT, "revision": state["revision"] + 1,
            "plan_id": plan_id, "selected": selected, "outcome": outcome,
            "joined": joined, "promoted": promote_recipe, "prev": state["head"]}
    event = {**data, "hash": _digest(data)}
    new = deepcopy(state)
    new["events"].append(event)
    new["revision"] += 1
    new["head"] = event["hash"]
    delta = 2 if outcome == "helpful" else -2
    new["weights"][selected] = max(-WEIGHT_LIMIT, min(WEIGHT_LIMIT, new["weights"][selected] + delta))
    if promote_recipe and joined not in new["recipes"]:
        new["recipes"].append(joined)
    verify_state(new)
    return new
