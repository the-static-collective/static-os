"""An experimental audio *file* carrier for GENESIS cartridges.

FSK: 16 kHz mono signed 16-bit PCM, 250 bits/s, bit tones 1000/2000 Hz.
No microphone, sound card, actual radio or room-noise reliability is claimed.
Decode is intentionally strict and rejects modified/noisy samples or CRC drift.
"""
import io
import math
import struct
import wave
import zlib

from .genesis008 import decode, encode

RATE = 16000
SAMPLES_PER_BIT = 64
PREAMBLE = b"\x55" * 8 + b"\xd3\x91"
MAX_MESSAGE = 2048


def _bits(data):
    for byte in data:
        for shift in range(7, -1, -1):
            yield (byte >> shift) & 1


def to_wav(cartridge):
    text = encode(cartridge).encode("ascii")
    if len(text) > MAX_MESSAGE:
        raise ValueError("AUDIO_REFUSED_MESSAGE_TOO_LARGE")
    message = len(text).to_bytes(2, "big") + text
    frame = PREAMBLE + message + (zlib.crc32(message) & 0xffffffff).to_bytes(4, "big")
    buf = bytearray()
    for bit in _bits(frame):
        freq = 2000 if bit else 1000
        for i in range(SAMPLES_PER_BIT):
            sample = int(10500 * math.sin(2 * math.pi * freq * i / RATE))
            buf.extend(struct.pack("<h", sample))
    memory = io.BytesIO()
    with wave.open(memory, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(RATE)
        writer.writeframes(bytes(buf))
    return memory.getvalue()


def from_wav(data):
    if not isinstance(data, bytes) or len(data) > 3_000_000:
        raise ValueError("AUDIO_REFUSED_SIZE")
    try:
        with wave.open(io.BytesIO(data), "rb") as reader:
            if (reader.getnchannels(), reader.getsampwidth(),
                    reader.getframerate(), reader.getcomptype()) != (1, 2, RATE, "NONE"):
                raise ValueError("AUDIO_REFUSED_WAVE_FORMAT")
            samples = reader.readframes(reader.getnframes())
    except (wave.Error, EOFError, OSError) as error:
        raise ValueError("AUDIO_REFUSED_WAVE_DATA") from error
    if len(samples) % (2 * SAMPLES_PER_BIT * 8):
        raise ValueError("AUDIO_REFUSED_TRUNCATED_BITS")
    if len(samples) < (len(PREAMBLE) + 2 + 4) * 8 * SAMPLES_PER_BIT * 2:
        raise ValueError("AUDIO_REFUSED_TRUNCATED_FRAME")
    samples_view = memoryview(samples)
    result = bytearray()
    for pos in range(0, len(samples), 2 * SAMPLES_PER_BIT * 8):
        byte = 0
        for n in range(8):
            start = pos + n * 2 * SAMPLES_PER_BIT
            block = samples_view[start:start + 2 * SAMPLES_PER_BIT]
            values = struct.unpack("<64h", block)
            powers = []
            for freq in (1000, 2000):
                sine = sum(v * math.sin(2 * math.pi * freq * i / RATE)
                           for i, v in enumerate(values))
                cosine = sum(v * math.cos(2 * math.pi * freq * i / RATE)
                             for i, v in enumerate(values))
                powers.append(sine*sine + cosine*cosine)
            if max(powers) < 1e8 or min(powers) * 4 > max(powers):
                raise ValueError("AUDIO_REFUSED_UNCLEAR_TONE")
            byte = (byte << 1) | (powers[1] > powers[0])
        result.append(byte)
    frame = bytes(result)
    if not frame.startswith(PREAMBLE):
        raise ValueError("AUDIO_REFUSED_SYNC")
    length = int.from_bytes(frame[len(PREAMBLE):len(PREAMBLE)+2], "big")
    if length <= 0 or length > MAX_MESSAGE or len(frame) != len(PREAMBLE) + 2 + length + 4:
        raise ValueError("AUDIO_REFUSED_LENGTH")
    body = frame[len(PREAMBLE): -4]
    if zlib.crc32(body) & 0xffffffff != int.from_bytes(frame[-4:], "big"):
        raise ValueError("AUDIO_REFUSED_CRC")
    try:
        return decode(body[2:].decode("ascii"))
    except UnicodeError as error:
        raise ValueError("AUDIO_REFUSED_TEXT") from error
