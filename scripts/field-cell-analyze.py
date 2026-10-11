"""FIELD-CELL-001: offline, bounded, non-authoritative low-voltage RC measurement analysis.

No hardware, serial devices, networking or sensor drivers. Synthetic records and
user-reported records are deliberately different evidence classes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from hashlib import sha256
import io
import json
import math
from pathlib import Path
import re
import sys

FIELDS = ("trial_id", "condition", "phase", "time_s", "supply_v", "node_v")
CONDITIONS = frozenset(("fixed", "open", "dry", "damp", "wet"))
CLASSIFICATIONS = frozenset(("SYNTHETIC", "USER_REPORTED_UNVERIFIED"))
MAX_FILE_BYTES = 131072
MAX_ROWS = 2500
LIMIT_SECONDS = 3600.0
T63 = 1.0 - math.exp(-1.0)


class Refuse(ValueError):
    pass


def _finite(value: str, label: str) -> float:
    try:
        n = float(value)
    except (TypeError, ValueError) as exc:
        raise Refuse("invalid numeric field: " + label) from exc
    if not math.isfinite(n):
        raise Refuse("nonfinite numeric field: " + label)
    return n


def _interpolate(points: list[dict], t: float) -> float | None:
    for i, item in enumerate(points):
        if item["time_s"] == t:
            return item["node_v"] / item["supply_v"]
        if i and points[i - 1]["time_s"] < t < item["time_s"]:
            before = points[i - 1]
            fraction = (t - before["time_s"]) / (item["time_s"] - before["time_s"])
            return ((before["node_v"] / before["supply_v"]) * (1.0 - fraction)
                    + (item["node_v"] / item["supply_v"]) * fraction)
    return None


def _rise_threshold(points: list[dict], threshold: float) -> float | None:
    previous = points[0]
    if previous["node_v"] / previous["supply_v"] >= threshold:
        return previous["time_s"]
    for item in points[1:]:
        y0 = previous["node_v"] / previous["supply_v"]
        y1 = item["node_v"] / item["supply_v"]
        if y0 < threshold <= y1:
            if y1 <= y0:
                return None
            f = (threshold - y0) / (y1 - y0)
            return previous["time_s"] + f * (item["time_s"] - previous["time_s"])
        previous = item
    return None


def analyze_bytes(raw: bytes, classification: str = "USER_REPORTED_UNVERIFIED") -> dict:
    if classification not in CLASSIFICATIONS:
        raise Refuse("unsupported evidence classification")
    if not 0 < len(raw) <= MAX_FILE_BYTES:
        raise Refuse("source file exceeds byte limit or is empty")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline=""))
        if reader.fieldnames is None or tuple(reader.fieldnames) != FIELDS:
            raise Refuse("exact expected six-column header required")
        groups = defaultdict(list)
        observed_rows = 0
        for row in reader:
            observed_rows += 1
            if observed_rows > MAX_ROWS:
                raise Refuse("record count exceeds limit")
            if None in row or any(v is None for v in row.values()):
                raise Refuse("missing or extra CSV value")
            trial = row["trial_id"]
            if not re.fullmatch(r"[A-Za-z0-9_-]{1,48}", trial or ""):
                raise Refuse("invalid trial identifier")
            condition, phase = row["condition"], row["phase"]
            if condition not in CONDITIONS or phase != "charge":
                raise Refuse("unsupported condition or phase")
            t = _finite(row["time_s"], "time_s")
            supply = _finite(row["supply_v"], "supply_v")
            node = _finite(row["node_v"], "node_v")
            if not (0 <= t <= LIMIT_SECONDS and 0 < supply <= 3.5):
                raise Refuse("time or supply outside battery-powered profile")
            if not (-0.15 <= node <= supply + 0.15):
                raise Refuse("node voltage outside expected observation range")
            groups[trial].append({
                "trial_id": trial, "condition": condition, "phase": phase,
                "time_s": t, "supply_v": supply, "node_v": node
            })
        if not groups:
            raise Refuse("no measurement rows")
    except (UnicodeError, csv.Error) as exc:
        raise Refuse("CSV could not be decoded or parsed") from exc

    results = []
    global_flags = []
    for trial_id in sorted(groups):
        points = groups[trial_id]
        if len(points) < 4:
            raise Refuse("each trial needs at least four sample points")
        c = points[0]["condition"]
        if any(p["condition"] != c or p["phase"] != "charge" for p in points):
            raise Refuse("trial condition or phase changed during capture")
        if points[0]["time_s"] != 0.0:
            raise Refuse("trial must begin at t=0")
        if any(p["time_s"] <= points[i - 1]["time_s"] for i, p in enumerate(points) if i):
            raise Refuse("trial time must increase strictly")
        if max(p["supply_v"] for p in points) - min(p["supply_v"] for p in points) > 0.15:
            raise Refuse("battery voltage drift exceeds profile limit")
        flags = []
        if points[0]["node_v"] > 0.2:
            flags.append("INITIAL_VOLTAGE_NOT_RESET")
        if any(p["node_v"] < points[i - 1]["node_v"] - 0.1
               for i, p in enumerate(points) if i):
            flags.append("NONMONOTONIC_CHARGE")
        result = {
            "trial_id": trial_id,
            "condition": c,
            "samples": len(points),
            "final_time_s": points[-1]["time_s"],
            "final_fraction_of_supply": round(points[-1]["node_v"] / points[-1]["supply_v"], 6),
            "normalized_voltage_at_10s": None,
            "rise_to_63_percent_s": None,
            "right_censored_63_percent": False,
            "flags": flags
        }
        ten = _interpolate(points, 10.0)
        if ten is not None:
            result["normalized_voltage_at_10s"] = round(ten, 6)
        t63 = _rise_threshold(points, T63)
        if t63 is None:
            result["right_censored_63_percent"] = True
        else:
            result["rise_to_63_percent_s"] = round(t63, 4)
        results.append(result)

    counts = {condition: sum(x["condition"] == condition for x in results)
              for condition in sorted(CONDITIONS)}
    for must_have in ("fixed", "open", "dry", "damp", "wet"):
        if counts[must_have] == 0:
            global_flags.append("MISSING_" + must_have.upper() + "_CONDITION")
        elif counts[must_have] < 3:
            global_flags.append("INSUFFICIENT_REPLICATION_" + must_have.upper())
    if any(result["flags"] for result in results):
        global_flags.append("REVIEW_TRIAL_WARNINGS")
    return {
        "schema": "static-os.field-cell-analysis/v0",
        "source_sha256": sha256(raw).hexdigest(),
        "evidence_classification": classification,
        "physical_measurement_independently_verified": False,
        "physical_processor_proven": False,
        "operation": "READ_ONLY_OFFLINE_ANALYSIS",
        "trial_count": len(results),
        "rows_analyzed": observed_rows,
        "condition_counts": counts,
        "flags": sorted(global_flags),
        "trials": results,
        "claims": ["NORMALIZED_RC_TRACE_ANALYSIS"],
        "nonclaims": ["HARDWARE_INSTRUMENT_VERIFICATION", "SOIL_LOGIC", "THROUGH_EARTH_NETWORK",
                      "FIELD_PROCESSOR_PHYSICAL_PROOF", "SOURCE_AUTHORITY", "CONTROL_AUTHORITY"]
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("--classification", choices=sorted(CLASSIFICATIONS),
                        default="USER_REPORTED_UNVERIFIED")
    args = parser.parse_args()
    try:
        with args.csv.open("rb") as stream:
            raw = stream.read(MAX_FILE_BYTES + 1)
        result = analyze_bytes(raw, args.classification)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (OSError, Refuse) as exc:
        print(json.dumps({"status": "REFUSED", "reason": str(exc)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
