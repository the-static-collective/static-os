"""GENESIS-008 / universal cartridge: a *bounded, inert* trans-device envelope.

One small portable public-safe proposal can travel by SD, text, printed
cartridge or a WAV data experiment. The envelope carries no command, identity,
permission, signed receipt, actual field observation, site location or funds.

WITNESS means a RECORD OF A CLAIM, not confirmation of a real-world fact.
REPLICATE means an INVITATION to repeat a method, not replication completed.
"""
from __future__ import annotations
import base64
import hashlib
import json
import re
import zlib

SCHEMA = "static-os.genesis-cartridge/v1"
TEXT_PREFIX = "GC1:"
KINDS = ("ASK", "OFFER", "PROPOSE", "WITNESS", "REPLICATE")
FOCI = ("Living House", "Community Food", "Festival Table", "Repair Lab")
SOURCES = frozenset((
    "NINTENDO_WII_SD", "NINTENDO_GAMECUBE_SD", "NINTENDO_DS_DLDI",
    "ESP32_USB_SERIAL", "ANDROID_TERMUX_LOCAL", "RASPBERRY_PI_LOCAL",
    "LEGACY_LINUX_PYTHON3", "FESTIVAL_SYNTHETIC_DEMO",
))
MAX_JSON = 4096
MAX_TEXT = 8192
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
TOPICS = {
    "Living House": "Can one Suitcase help an ordinary house become cooperative infrastructure?",
    "Community Food": "Can one Suitcase help a house coordinate a fictional community food table?",
    "Festival Table": "Can one Suitcase help a house plan a fictional cooperative festival?",
    "Repair Lab": "Can one Suitcase help a house plan a fictional repair workshop?",
}
STATEMENTS = {
    "ASK": TOPICS,
    "OFFER": {x: "A fictional steward offers a temporary table for " + x.lower() +
              "; availability and permission are unverified." for x in FOCI},
    "PROPOSE": {x: "Proposal only: hold a small, reversible " + x.lower() +
                " gathering, pending site and steward approval." for x in FOCI},
    "WITNESS": {x: "Software demonstration claims a " + x.lower() +
                " planning receipt exists. No real site or independent person observed." for x in FOCI},
    "REPLICATE": {x: "Request to repeat the " + x.lower() +
                  " planning experiment elsewhere; no physical replication completed." for x in FOCI},
}
DISTINCTIONS = {
    "ASK": "QUESTION_ONLY",
    "OFFER": "OFFER_UNACCEPTED",
    "PROPOSE": "PROPOSAL_UNAUTHORIZED",
    "WITNESS": "RECORDED_UNVERIFIED_CLAIM",
    "REPLICATE": "REPLICATION_INVITATION_ONLY",
}


def canonical(value):
    return json.dumps(value, ensure_ascii=True, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("ascii")


def _require(valid, reason):
    if not valid:
        raise ValueError("CARTRIDGE_REFUSED_" + reason)


def mint(kind, focus, source, parents=()):
    _require(isinstance(kind, str) and kind in KINDS, "KIND")
    _require(isinstance(focus, str) and focus in FOCI, "FOCUS")
    _require(isinstance(source, str) and source in SOURCES, "SOURCE")
    _require(isinstance(parents, (list, tuple)) and len(parents) <= 3, "PARENTS")
    _require(all(isinstance(x, str) and DIGEST.fullmatch(x) for x in parents), "PARENT_DIGEST")
    _require(len(set(parents)) == len(parents), "DUPLICATE_PARENT")
    _require((kind == "ASK" and len(parents) == 0) or
             (kind != "ASK" and len(parents) >= 1), "LINEAGE_REQUIRED")
    body = {
        "schema": SCHEMA, "kind": kind, "focus": focus,
        "statement": STATEMENTS[kind][focus],
        "parents": list(parents), "source": source,
        "disposition": DISTINCTIONS[kind], "scope": "PUBLIC_SAFE_ONLY",
        "authority": "NONE", "human_permission": False,
        "physical_observation": False, "signed": False,
        "independent_witness": False, "delivered": False,
    }
    digest = "sha256:" + hashlib.sha256(canonical(body)).hexdigest()
    return {**body, "digest": digest}


def validate(value):
    _require(isinstance(value, dict) and
             set(value) == {
                 "schema", "kind", "focus", "statement", "parents", "source",
                 "disposition", "scope", "authority", "human_permission",
                 "physical_observation", "signed", "independent_witness",
                 "delivered", "digest",
             }, "SHAPE")
    _require(value["schema"] == SCHEMA, "SCHEMA")
    _require(isinstance(value["kind"], str) and isinstance(value["focus"], str) and
             value["kind"] in KINDS and value["focus"] in FOCI, "KIND_OR_FOCUS")
    _require(isinstance(value["source"], str) and value["source"] in SOURCES, "SOURCE")
    _require(isinstance(value["parents"], list), "PARENTS_LIST")
    expected = mint(value["kind"], value["focus"],
                    value["source"], value["parents"])
    _require(value == expected, "TAMPER_OR_ESCALATED_AUTHORITY")
    _require(len(canonical(value)) <= MAX_JSON, "OVERSIZED")
    return value


def encode(value):
    valid = validate(value)
    blob = canonical(valid)
    body = zlib.compress(blob, level=9)
    text = TEXT_PREFIX + base64.urlsafe_b64encode(body).decode("ascii").rstrip("=")
    _require(len(text) <= MAX_TEXT, "TEXT_OVERFLOW")
    return text


def decode(text):
    _require(isinstance(text, str) and text.startswith(TEXT_PREFIX), "TEXT_PREFIX")
    _require(len(text) <= MAX_TEXT and len(text) > len(TEXT_PREFIX), "TEXT_LENGTH")
    payload = text[len(TEXT_PREFIX):]
    _require(re.fullmatch(r"[A-Za-z0-9_-]+", payload) is not None, "TEXT_CHARS")
    try:
        compressed = base64.b64decode(
            payload + "=" * (-len(payload) % 4), altchars=b"-_", validate=True)
        inflater = zlib.decompressobj()
        original = inflater.decompress(compressed, MAX_JSON + 1)
        _require(inflater.eof and not inflater.unused_data and
                 not inflater.unconsumed_tail and len(original) <= MAX_JSON,
                 "COMPRESSED_BOUNDARY")
        value = json.loads(original.decode("utf-8"))
    except (ValueError, UnicodeError, zlib.error, json.JSONDecodeError) as error:
        raise ValueError("CARTRIDGE_REFUSED_INVALID_ENCODING") from error
    _require(canonical(value) == original, "NONCANONICAL_ENCODING")
    valid = validate(value)
    _require(encode(valid) == text, "NONCANONICAL_TEXT")
    return valid


def validate_chain(items):
    """Ordered, locally derived lineage; does NOT confirm any outside event."""
    _require(isinstance(items, list) and 1 <= len(items) <= 64, "CHAIN_SIZE")
    seen = {}
    for item in items:
        value = validate(item)
        key = value["digest"]
        _require(key not in seen, "CHAIN_DUPLICATE")
        for parent in value["parents"]:
            _require(parent in seen, "MISSING_OR_FORWARD_PARENT")
            _require(seen[parent]["focus"] == value["focus"], "CROSS_FOCUS_PARENT")
        seen[key] = value
    _require(items[0]["kind"] == "ASK", "FIRST_NOT_ASK")
    return {"count": len(items), "root": items[0]["digest"],
            "last": items[-1]["digest"],
            "has_real_field_witness": False,
            "has_physical_work": False,
            "source": "SOFTWARE_LINEAGE_ONLY"}
