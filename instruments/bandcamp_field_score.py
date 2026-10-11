"""BANDCAMP-FIELD-SCORE-001: declared score and synthetic encounters, never audio execution.

This is an InstrumentAdapterV0, not a Bandcamp API client or a signal decoder.
No downloaded recording, QR scan, microphone event, source license, or real
playback is asserted by this synthetic fixture.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re

from vendor.eleven_heap_001.infinite_radio import Address
from .contract import InstrumentDescriptorV0, Refuse, controls, observation, require

SCHEMA = "static-os.bandcamp-score-source/v0"
MAX_BYTES = 65536
MAX_CUES = 8
MAX_OBSERVATIONS = 32
CHANNELS = frozenset({"QR", "AUDIO", "OPTICAL"})
INTEGRITIES = frozenset({"PASS", "FAIL", "AMBIGUOUS"})
DECISIONS = frozenset({"HOLD", "INSPECT", "DECLINE"})
ROLES = frozenset({"SENSE", "ENCOUNTER", "PRESERVE"})
SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")


def _object(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refuse("duplicate JSON object key")
        out[key] = value
    return out


def _short(value, label, limit=128):
    require(type(value) is str and 0 < len(value) <= limit
            and all(31 < ord(c) < 127 or ord(c) >= 160 for c in value),
            "invalid " + label)
    return value


def _read(path: Path):
    try:
        with path.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise Refuse("source unavailable") from exc
    require(0 < len(raw) <= MAX_BYTES, "source exceeds byte budget")
    try:
        data = json.loads(raw, object_pairs_hook=_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(Refuse("nonfinite JSON")))
    except (UnicodeError, ValueError) as exc:
        raise Refuse("invalid source JSON") from exc
    require(type(data) is dict and set(data) == {
        "schema", "classification", "edition", "score", "cues", "observations", "decision"
    }, "source fields changed")
    require(data["schema"] == SCHEMA and data["classification"] == "SYNTHETIC_ONLY",
            "requires synthetic-only source")
    require(type(data["edition"]) is dict and set(data["edition"]) == {
        "artist", "archive_label", "evidence_level"
    }, "edition fields changed")
    _short(data["edition"]["artist"], "artist")
    _short(data["edition"]["archive_label"], "archive label")
    require(data["edition"]["evidence_level"] == "LYRIC_EXPORT_ONLY",
            "recording/source verification unavailable")
    s = data["score"]
    require(type(s) is dict and set(s) == {"id", "referent", "ordered_cues"},
            "score fields changed")
    _short(s["id"], "score id")
    _short(s["referent"], "referent")
    order = s["ordered_cues"]
    require(type(order) is list and 1 <= len(order) <= MAX_CUES,
            "invalid score length")
    require(all(type(x) is str for x in order) and len(set(order)) == len(order),
            "duplicate score cues")
    require(type(data["cues"]) is list and len(data["cues"]) == len(order),
            "cue count mismatch")
    cue_ids = set()
    for c in data["cues"]:
        require(type(c) is dict and set(c) == {
            "id", "track_title", "role", "recording_sha256"
        }, "cue fields changed")
        cue_id = _short(c["id"], "cue id", 48)
        cue_ids.add(cue_id)
        _short(c["track_title"], "track title")
        require(c["role"] in ROLES, "invalid cue role")
        digest = c["recording_sha256"]
        require(digest is None or (type(digest) is str and SHA256_RE.fullmatch(digest)),
                "invalid declared recording digest")
    require(cue_ids == set(order) and len(cue_ids) == len(order),
            "score and cue IDs differ")
    require(type(data["observations"]) is list
            and len(data["observations"]) <= MAX_OBSERVATIONS,
            "observation count over budget")
    obs_ids = set()
    for o in data["observations"]:
        require(type(o) is dict and set(o) == {
            "id", "channel", "cue_id", "referent", "integrity",
            "clock_domain", "sequence", "capture_kind"
        }, "observation fields changed")
        oid = _short(o["id"], "observation ID")
        require(oid not in obs_ids, "duplicate observation occurrence")
        obs_ids.add(oid)
        require(o["channel"] in CHANNELS and o["integrity"] in INTEGRITIES,
                "unknown channel/integrity")
        require(o["cue_id"] in cue_ids, "unknown cue")
        _short(o["referent"], "observation referent")
        _short(o["clock_domain"], "clock domain")
        require(type(o["sequence"]) is int and 0 <= o["sequence"] <= 1000000,
                "invalid local sequence")
        require(o["capture_kind"] == "SIMULATED",
                "no physical observation is supported")
    require(data["decision"] in DECISIONS, "invalid simulated human decision")
    return raw, data


def evaluate(data: dict) -> list[dict]:
    """Called only after strict _read validation. All results are HOLD or REFUSED."""
    score = data["score"]
    target = score["referent"]
    observations = data["observations"]
    valid = [o for o in observations if o["integrity"] == "PASS" and o["referent"] == target]
    qr = sorted((o for o in valid if o["channel"] == "QR"),
                key=lambda o: (o["sequence"], o["id"]))
    audio = sorted((o for o in valid if o["channel"] == "AUDIO"),
                   key=lambda o: (o["sequence"], o["id"]))
    rejected = sorted(o["id"] for o in observations if o not in valid)
    disposition = "REFUSED" if data["decision"] == "DECLINE" else "HOLD"
    paired = bool(qr and audio)
    pair = {
        "type": "BandcampReferentCandidate",
        "score_ref": score["id"],
        "referent": target,
        "status": disposition,
        "match": "SYNTHETIC_SAME_REFERENT" if paired else "MISSING_CHANNEL_HOLD",
        "observation_ids": [qr[0]["id"], audio[0]["id"]] if paired else [],
        "all_matching_occurrence_ids": sorted(o["id"] for o in valid),
        "rejected_or_ambiguous_ids": rejected,
        "independence_claim": "NONE",
        "physical_proof": "NONE",
        "authority": "NONE",
        "consequence": "NONE"
    }
    buckets = [[o for o in audio if o["cue_id"] == cue] for cue in score["ordered_cues"]]
    selected = [group[0] for group in buckets if group]
    if any(not group for group in buckets):
        order_state = "MISSING_CUE_HOLD"
    elif any(len(group) > 1 for group in buckets):
        order_state = "REPEATED_CUE_HOLD"
    elif len({o["clock_domain"] for o in selected}) != 1:
        order_state = "UNCOMPARABLE_CLOCK_HOLD"
    elif any(a["sequence"] >= b["sequence"] for a, b in zip(selected, selected[1:])):
        order_state = "OUT_OF_ORDER_HOLD"
    else:
        order_state = "DECLARED_SYNTHETIC_ORDER"
    sequence = {
        "type": "BandcampScoreSequenceCandidate",
        "score_ref": score["id"],
        "referent": target,
        "status": disposition,
        "evaluation": order_state,
        "declared_cue_ids": list(score["ordered_cues"]),
        "observed_audio_occurrence_ids": [o["id"] for o in selected],
        "not_proved": ["ACTUAL_PLAYBACK", "ACOUSTIC_DECODING", "LISTENER_CONSENT",
                       "RECORDING_IDENTITY", "ORDER_ACROSS_CLOCK_DOMAINS"],
        "authority": "NONE",
        "consequence": "NONE"
    }
    return [pair, sequence]


class BandcampFieldScoreAdapter:
    """A source-bound, local, read-only album-as-instrument experiment."""

    def __init__(self, path: Path, *, instrument_id="synthetic-bandcamp-field-score"):
        self.path = Path(path).resolve()
        self.instrument_id = instrument_id

    def _descriptor(self, raw: bytes):
        source_hash = sha256(raw).hexdigest()
        return InstrumentDescriptorV0(
            self.instrument_id, "static-os.bandcamp-field-score/v0",
            "BANDCAMP FIELD SCORE (SYNTHETIC — NO PLAYBACK)",
            {"kind": "synthetic-album-score", "reference": "fixture-sha256:" + source_hash,
             "history": ["BANDCAMP FIELD SCORE 001", "lyric-export titles only",
                         "no licensed audio, transmission, or listening confirmed"],
             "sha256": source_hash},
            {"revision": "bandcamp-field-score-001", "synthetic_only": True,
             "max_cues": MAX_CUES, "max_observations": MAX_OBSERVATIONS},
            controls("candidate ordinal", "candidate index", [0, 2])
        )

    def describe(self):
        raw, _ = _read(self.path)
        return self._descriptor(raw)

    def observe(self):
        raw, data = _read(self.path)
        return observation(self._descriptor(raw).source, evaluate(data),
                           classification="synthetic Bandcamp sidecar; proposal only")

    def select(self, observed: dict, mode: str, address: Address,
               region: tuple[int, int] | None = None, focus: int | None = None):
        require(mode in ("field", "attention"), "invalid selector mode")
        require(type(observed) is dict and type(observed.get("items")) is list,
                "malformed native observation")
        items = observed["items"]
        require(len(items) == 2, "expected two read-only candidates")
        low, high = region if (mode == "attention" and region is not None) else (0, len(items))
        require(type(low) is int and type(high) is int and 0 <= low < high <= len(items),
                "invalid selection region")
        index = low + min(high - low - 1, int(address.center * (high - low)))
        candidate = items[index]
        require(candidate.get("authority") == "NONE" and candidate.get("consequence") == "NONE",
                "candidate gained authority")
        return {"type": "BandcampFieldScoreSelection", "index": index, "candidate": candidate,
                "may_open_url": False, "may_download": False, "may_connect": False,
                "may_execute": False, "requires_separate_human_choice": True}
