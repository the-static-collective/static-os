#!/usr/bin/env python3
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "specimens" / "open-page-001" / "manifest.json"
PAGE = ROOT / "specimens" / "open-page-001" / "open-page.md"

REQUIRED_LAWS = {
    "FILENAME != BYTES",
    "REALITY != STORY",
    "WITNESS != INTERPRETATION",
    "INTERPRETATION != EVIDENCE",
    "AUTHORSHIP != INVENTION",
    "FICTION != FALSEHOOD",
    "MYTHIC TRUTH != HISTORICAL CLAIM",
    "SYMBOL != EVIDENCE",
    "PAGE != LINEAGE",
    "RENDERING MAY CHANGE; ANCESTRY MUST SURVIVE",
}

HEX64 = re.compile(r"^[0-9a-f]{64}$")


def fail(message: str) -> None:
    raise SystemExit(f"REFUSE: {message}")


def main() -> int:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data.get("specimen_id") != "OPEN-PAGE-SPECIMEN-001":
        fail("wrong specimen id")

    particulars = data.get("particulars", [])
    if len(particulars) != 2:
        fail("specimen must preserve exactly two source particulars")

    ids = set()
    for part in particulars:
        pid = part.get("id")
        if not pid or pid in ids:
            fail("particular ids must be unique")
        ids.add(pid)
        if not HEX64.match(part.get("sha256", "")):
            fail(f"invalid sha256 for {pid}")
        if not isinstance(part.get("byte_length"), int) or part["byte_length"] <= 0:
            fail(f"invalid byte length for {pid}")
        if part.get("detected_media_type") != "image/jpeg":
            fail(f"unexpected media type for {pid}")
        if not str(part.get("observed_filename", "")).endswith(".png"):
            fail(f"specimen no longer demonstrates filename/bytes distinction for {pid}")
        if part.get("pixels_vendored") is not False:
            fail(f"pixels_vendored must remain false for {pid}")

    observations = data.get("observations", [])
    observation_ids = {x.get("id") for x in observations}
    for obs in observations:
        if obs.get("particular") not in ids:
            fail(f"observation {obs.get('id')} points to unknown particular")

    interpretations = data.get("interpretations", [])
    interpretation_ids = {x.get("id") for x in interpretations}
    for item in interpretations:
        if item.get("authority") != "human-selected-context":
            fail(f"interpretation {item.get('id')} lacks bounded authority label")
        for parent in item.get("based_on", []):
            if parent not in observation_ids and parent not in interpretation_ids:
                fail(f"interpretation {item.get('id')} has unknown parent {parent}")

    selection = data.get("selection", {})
    if selection.get("authority") != "human":
        fail("selection authority must remain human")
    if not set(selection.get("selected_interpretations", [])).issubset(interpretation_ids):
        fail("selection references unknown interpretation")

    mythic = data.get("presentation", {}).get("mythic_echo", {})
    if mythic.get("mode") != "artistic" or mythic.get("historical_claim") is not False:
        fail("mythic echo must remain artistic and explicitly non-historical")

    if data.get("consequence", {}).get("state") != "OPEN":
        fail("specimen 001 may not invent a downstream consequence")
    if data.get("next", {}).get("state") != "OPEN":
        fail("specimen 001 must preserve an open next edge")

    laws = set(data.get("laws", []))
    missing = REQUIRED_LAWS - laws
    if missing:
        fail(f"missing laws: {sorted(missing)}")

    page = PAGE.read_text(encoding="utf-8")
    for section in [
        "## NOW", "## WITNESSED", "## HELD / UNRESOLVED",
        "## POSSIBLE READINGS", "## AVAILABLE DOORS", "## CHOSEN",
        "## CONSEQUENCE", "## LINEAGE", "## PAGE", "## NEXT"
    ]:
        if section not in page:
            fail(f"open page missing {section}")

    manifest_digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    print("OPEN-PAGE-SPECIMEN-001: PASS")
    print(f"manifest_sha256={manifest_digest}")
    print("source_pixels=external-addressed-not-vendored")
    print("consequence=OPEN")
    print("next=OPEN")
    return 0


if __name__ == "__main__":
    sys.exit(main())
