"""SINGING-SIGIL F1: deterministic standalone DTMF/QR test coupon.

No Bandcamp connection; no captured audio claim; no execution path.
Only device-local evidence from actual trials may establish physical success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import wave
import zlib

SCHEMA = "static-os.singing-sigil-f1/v0"
ARTIFACT = "artifact:singing-sigil-companion-001"
CODE = "SS001"
CORE = "SCF1:" + CODE
PAYLOAD = CORE + ":" + f"{zlib.crc32(CORE.encode('ascii')) & 0xffffffff:08X}"
# Mapping 0..F -> actual 16-key DTMF keypad; E/F map to */#.
DTMF_KEYS = "0123456789ABCD*#"
ROWS = (697, 770, 852, 941)
COLS = (1209, 1336, 1477, 1633)
PAD = (("1", "2", "3", "A"),
       ("4", "5", "6", "B"),
       ("7", "8", "9", "C"),
       ("*", "0", "#", "D"))
FREQUENCIES = {symbol: (ROWS[i], COLS[j]) for i, row in enumerate(PAD)
               for j, symbol in enumerate(row)}
FS = 48000
TONE_S = 0.10
GAP_S = 0.04
LEAD_S = 0.5
REPEAT_S = 0.7
DECODER_MAX_SECONDS = 90


def payload_to_keys(payload: str) -> str:
    raw = payload.encode("ascii")
    if not (1 <= len(raw) <= 80):
        raise ValueError("payload too long")
    return "".join(DTMF_KEYS[int(nib, 16)] for nib in raw.hex().upper())


def keys_to_payload(keys: str) -> str | None:
    if len(keys) % 2:
        return None
    try:
        hexstr = "".join(format(DTMF_KEYS.index(key), "X") for key in keys)
        return bytes.fromhex(hexstr).decode("ascii")
    except (UnicodeDecodeError, ValueError):
        return None


def verify_payload(payload: str) -> bool:
    match = re.fullmatch(r"(SCF1:[A-Z0-9]{3,12}):([0-9A-F]{8})", payload)
    if not match:
        return False
    expected = f"{zlib.crc32(match.group(1).encode('ascii')) & 0xffffffff:08X}"
    return expected == match.group(2)


def synthesize(payload: str = PAYLOAD, repeats: int = 2) -> bytes:
    if not verify_payload(payload) or not (1 <= repeats <= 3):
        raise ValueError("invalid F1 token or repeat count")
    keys = payload_to_keys(payload)
    result = bytearray()

    def silent(seconds: float):
        result.extend(b"\x00\x00" * round(seconds * FS))

    silent(LEAD_S)
    n = round(TONE_S * FS)
    fade = round(0.008 * FS)
    for r in range(repeats):
        for key in keys:
            a, b = FREQUENCIES[key]
            for i in range(n):
                # Per-key window makes the coupon playable without sharp clicks.
                edge = min(1.0, i / fade, (n - 1 - i) / fade)
                sample = 0.20 * edge * (math.sin(2 * math.pi * a * i / FS) +
                                         math.sin(2 * math.pi * b * i / FS))
                value = max(-32768, min(32767, round(sample * 32767)))
                result.extend(struct.pack("<h", value))
            silent(GAP_S)
        if r != repeats - 1:
            silent(REPEAT_S)
    silent(0.5)
    return bytes(result)


def write_wav(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(FS)
        writer.writeframes(pcm)


def goertzel(samples: list[int], freq: int) -> float:
    # Evaluate a known DTMF frequency; not a general-purpose audio fingerprint.
    n = len(samples)
    coeff = 2 * math.cos(2 * math.pi * freq / 8000)
    s1 = s2 = 0.0
    for x in samples:
        s0 = x + coeff * s1 - s2
        s2, s1 = s1, s0
    return max(0.0, s1 * s1 + s2 * s2 - coeff * s1 * s2)


def classify(samples: list[int]) -> str | None:
    if len(samples) != 200 or max(abs(x) for x in samples) < 170:
        return None
    low = sorted(((goertzel(samples, f), f) for f in ROWS), reverse=True)
    high = sorted(((goertzel(samples, f), f) for f in COLS), reverse=True)
    # Require a dominant single row and column, rejecting silence and ambiguity.
    if low[0][0] < 2.1 * max(low[1][0], 1.0):
        return None
    if high[0][0] < 2.1 * max(high[1][0], 1.0):
        return None
    if min(low[0][0], high[0][0]) < 0.13 * max(low[0][0], high[0][0]):
        return None
    pair = (low[0][1], high[0][1])
    return next((k for k, v in FREQUENCIES.items() if v == pair), None)


def decode_wav(path: Path) -> dict:
    with wave.open(str(path), "rb") as reader:
        channels, width, rate = reader.getnchannels(), reader.getsampwidth(), reader.getframerate()
        duration = reader.getnframes() / rate
        if channels != 1 or width != 2 or not (8000 <= rate <= 96000):
            raise ValueError("decoder needs 16-bit mono PCM WAV at 8–96 kHz")
        if duration > DECODER_MAX_SECONDS:
            raise ValueError("WAV duration exceeds lab budget")
        raw = reader.readframes(reader.getnframes())
    pcm = struct.unpack("<" + "h" * (len(raw) // 2), raw)
    # Resample to ~8 kHz with nearest-point selection; production audio decoding
    # will need an anti-aliasing front-end and calibrated SNR measurements.
    down = [pcm[min(len(pcm) - 1, round(i * rate / 8000))]
            for i in range(int(len(pcm) * 8000 / rate))]
    frames = [classify(down[i:i+200]) for i in range(0, len(down) - 199, 200)]
    runs = []
    prev = None
    start = 0
    for i, key in enumerate(frames + [None]):
        if key != prev:
            if prev is not None and i - start >= 2:
                runs.append({"symbol": prev, "start": start / 40,
                             "end": i / 40})
            start = i
            prev = key
    # Split sequences at long gaps, but tolerate shorter losses as uncertainty.
    groups = []
    current = []
    for run in runs:
        if current and run["start"] - current[-1]["end"] > 0.30:
            groups.append(current)
            current = []
        current.append(run)
    if current:
        groups.append(current)
    receipts = []
    for group in groups:
        keys = "".join(x["symbol"] for x in group)
        found = None
        # Scan bounded subranges; never silently repair a dropped nibble.
        for first in range(0, len(keys) - 1):
            for last in range(first + 2, min(len(keys) + 1, first + 160), 2):
                guess = keys_to_payload(keys[first:last])
                if guess and verify_payload(guess):
                    found = {"payload": guess, "start_s": group[first]["start"],
                             "end_s": group[last-1]["end"],
                             "crc32_checked": True, "authenticity": "UNVERIFIED"}
                    break
            if found:
                break
        if found:
            receipts.append(found)
    return {"schema": "static-os.singing-sigil-f1-decode/v0",
            "input_sha256": hashlib.sha256(raw).hexdigest(),
            "source_kind": "SUPPLIED_PCM_WAV",
            "valid_packets": receipts,
            "status": "CANDIDATE_ONLY" if receipts else "NO_VALID_PACKET",
            "authority": "NONE", "physical_playback_witness": "NOT_ESTABLISHED",
            "note": "CRC validates transport corruption only, not speaker/issuer identity"}


def manifest() -> dict:
    return {"schema": SCHEMA, "classification": "LAB_COUPON_ONLY",
            "display_title": "The Singing Sigil — F1 Transport Coupon",
            "artist_context": "The Static Collective",
            "artifact_ref": ARTIFACT,
            "short_id": CODE,
            "payload": PAYLOAD,
            "crc32_is_authentication": False,
            "transport": {"qr": "plain-text QR", "audio": "16-key DTMF, mono PCM WAV 48kHz"},
            "source_lyrics_are_not_encoded": True,
            "auto_execution": False,
            "crossing_disposition": "HOLD",
            "experimental_status": "LAB FILE GENERATED; HUMAN PRINT/PLAY/CAPTURE UNTESTED"}


def make_coupon(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    audio = directory / "singing-sigil-f1-dtmf.wav"
    write_wav(audio, synthesize())
    m = manifest()
    m["wav_sha256"] = hashlib.sha256(audio.read_bytes()).hexdigest()
    (directory / "singing-sigil-f1-manifest.json").write_text(json.dumps(m, indent=2) + "\n")
    (directory / "singing-sigil-f1-payload.txt").write_text(PAYLOAD + "\n")
    try:
        import qrcode
        from qrcode.image.svg import SvgPathImage
        qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_H,
                           box_size=12, border=4)
        qr.add_data(PAYLOAD)
        qr.make(fit=True)
        qr.make_image(fill_color="black", back_color="white").save(directory / "singing-sigil-f1-qr.png")
        qr.make_image(image_factory=SvgPathImage).save(directory / "singing-sigil-f1-qr.svg")
    except ImportError:
        print("QR generation unavailable: install qrcode[pil] or use any standard QR generator with payload.txt")
    return m


def main():
    p = argparse.ArgumentParser(description="Stand-alone read-only F1 DTMF/QR coupon test")
    sub = p.add_subparsers(dest="command", required=True)
    build = sub.add_parser("make", help="generate WAV + QR + manifest")
    build.add_argument("--out", type=Path, default=Path("singing-sigil-f1-kit"))
    dec = sub.add_parser("decode", help="inspect supplied 16-bit mono WAV")
    dec.add_argument("wav", type=Path)
    args = p.parse_args()
    if args.command == "make":
        print(json.dumps(make_coupon(args.out), indent=2))
    else:
        print(json.dumps(decode_wav(args.wav), indent=2))


if __name__ == "__main__":
    main()
