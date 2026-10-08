"""Recorded-input and native GHoT read-only adapters. No physical receiver claim."""
from __future__ import annotations

from fractions import Fraction
from hashlib import sha256
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import wave

from vendor.eleven_heap_001.infinite_radio import Address, ControlMap, digest
from .contract import InstrumentDescriptorV0, Refuse, controls, observation, require

GHOT_COMMIT = "e35dd470384d864b7b0b629a68dad570875a7df0"
RELATTE_COMMIT = "dcc8cdca84c440aa4294134f020fb7095bf87f24"


def verify_donor(root: Path, commit: str) -> None:
    """Exact existing owner cut, with no tracked working-tree modifications."""
    require(root.is_dir(), "native donor disappeared")
    try:
        head = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"],
                                       stderr=subprocess.DEVNULL, timeout=5).decode().strip()
        clean = subprocess.run(["git", "-C", str(root), "diff", "--quiet", "HEAD", "--"], timeout=5).returncode == 0
    except (OSError, subprocess.SubprocessError) as error:
        raise Refuse("native donor unavailable") from error
    require(head == commit and clean, "native donor pin or source changed")


class RecordedRadioAdapter:
    """A bounded stereo PCM recording: two explicitly synthetic station tracks.

    Frequency selects a track by its declared fixture frequency; attention selects
    a window within that track. No tuner, antenna, network, audio device, or RF I/O.
    """

    def __init__(self, path: Path, *, instrument_id: str = "recorded-radio", calibration: str = "fixture-v1"):
        self.path = path.resolve()
        self.instrument_id, self.calibration = instrument_id, calibration

    def _read(self) -> tuple[bytes, list[list[int]], int]:
        try:
            with self.path.open("rb") as stream:
                data = stream.read(65537)
            require(0 < len(data) <= 65536, "recording byte budget exceeded")
            import io
            with wave.open(io.BytesIO(data)) as wav:
                require(wav.getnchannels() == 2 and wav.getsampwidth() == 2
                        and wav.getnframes() <= 4096 and wav.getcomptype() == "NONE", "unsupported recording")
                rate = wav.getframerate()
                raw = wav.readframes(wav.getnframes())
            values = struct.unpack("<" + "h" * (len(raw) // 2), raw)
            require(bool(values), "empty recording")
            return data, [list(values[0::2]), list(values[1::2])], rate
        except (OSError, EOFError, wave.Error, struct.error) as error:
            raise Refuse("recorded source disappeared or is malformed") from error

    def describe(self) -> InstrumentDescriptorV0:
        data, channels, rate = self._read()
        return InstrumentDescriptorV0(self.instrument_id, "recorded-radio/v0", "RECORDED SYNTHETIC FIXTURE",
            {"kind": "recorded-fixture", "reference": self.path.as_uri(),
             "history": ["synthetic PCM generator:v1", "two station tracks:90MHz/106MHz", "no physical capture"],
             "sha256": sha256(data).hexdigest()},
            {"revision": self.calibration, "sample_rate_hz": rate, "frames": len(channels[0]),
             "station_frequencies_hz": [90000000, 106000000], "band_hz": [88000000, 108000000]},
            controls("frequency", "Hz", [88000000, 108000000]))

    def observe(self) -> dict:
        descriptor = self.describe()
        _, channels, _ = self._read()
        return observation(descriptor.source,
                           [{"station": i, "frequency_hz": hz, "samples": channels[i]}
                            for i, hz in enumerate(descriptor.calibration["station_frequencies_hz"])],
                           classification="recorded synthetic fixture; physical reception NOT_RUN")

    def select(self, observed: dict, mode: str, address: Address,
               region: tuple[int, int] | None = None, focus: int | None = None) -> dict:
        mapped = ControlMap("recorded-frequency", 1, "frequency").interpret(address)
        station = min(observed["items"], key=lambda item: abs(Fraction(item["frequency_hz"]) - mapped.frequency_hz))
        if mode == "frequency":
            return {"type": "FrequencySelection", "unit": "Hz", "frequency_hz": str(mapped.frequency_hz),
                    "fixture_station_hz": station["frequency_hz"], "station": station["station"],
                    "samples": station["samples"], "physical_reception": False}
        require(mode == "attention", "unsupported radio control map")
        require(type(focus) is int and focus in (0, 1), "attention requires a selected station")
        station = observed["items"][focus]
        low, high = region or (0, len(station["samples"]))
        require(0 <= low < high <= len(station["samples"]), "attention outside source")
        selected = ControlMap("recorded-attention", 1, "attention", signal_id=str(station["station"]),
                              sample_region=(low, high)).interpret(address)
        start, end = selected.sample_region
        return {"type": "AttentionSelection", "unit": "source sample index", "station": station["station"],
                "sample_region": [start, end], "samples": station["samples"][start:end],
                "physical_reception": False}


class GhotSystemAdapter:
    """Invoke real pinned GHoT pure probes in a bounded child process.

    Avoid reference_node.body(): it creates identity files. memory_bytes() and
    probe_power() only read the OS. Manual power hints are removed from the child.
    """

    FIELDS = (("os", "name"), ("architecture", "name"), ("cpu_count", "count"),
              ("memory_bytes", "bytes"), ("load_1m", "load"), ("load_5m", "load"),
              ("load_15m", "load"), ("battery_percent", "percent"), ("temperature_c", "degC"),
              ("source", "name"), ("thermal_state", "name"))

    def __init__(self, donor: Path, *, instrument_id: str = "ghot-local-system"):
        self.donor, self.instrument_id = donor.resolve(), instrument_id

    def describe(self) -> InstrumentDescriptorV0:
        verify_donor(self.donor, GHOT_COMMIT)
        files = [self.donor / "ghot" / name for name in ("reference_node.py", "power_field.py")]
        hashes = [sha256(path.read_bytes()).hexdigest() for path in files]
        return InstrumentDescriptorV0(self.instrument_id, "ghot-readonly/v0", "NATIVE GHOT LOCAL OS PROBES",
            {"kind": "local-os", "reference": f"ghot:{GHOT_COMMIT}:memory_bytes+probe_power",
             "history": [f"the-static-collective/GHoT@{GHOT_COMMIT}", *hashes], "sha256": digest(hashes)},
            {"revision": "ghot-readonly-v0", "fields": list(self.FIELDS)}, controls("OS field", "typed field", [1, 11]))

    def observe(self) -> dict:
        descriptor = self.describe()
        code = """import json, os, platform, sys
sys.path.insert(0, sys.argv[1])
from reference_node import memory_bytes
from power_field import probe_power
p = probe_power()
print(json.dumps(dict(p, os=platform.system(), architecture=platform.machine(),
                     cpu_count=os.cpu_count(), memory_bytes=memory_bytes())))
"""
        env = {k: v for k, v in os.environ.items() if not k.startswith("GHOT_")}
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        try:
            child = subprocess.run([sys.executable, "-c", code, str(self.donor / "ghot")],
                                   env=env, capture_output=True, timeout=10, check=True)
            require(len(child.stdout) <= 65536, "GHoT output byte budget exceeded")
            data = json.loads(child.stdout)
        except (OSError, subprocess.SubprocessError, ValueError) as error:
            raise Refuse("native GHoT observation failed") from error
        return observation(descriptor.source, [{"field": field, "unit": unit, "value": data[field]}
                                               for field, unit in self.FIELDS], classification="locally demonstrated native GHoT read-only OS probe")

    def select(self, observed: dict, mode: str, address: Address,
               region: tuple[int, int] | None = None, focus: int | None = None) -> dict:
        require(mode in ("field", "attention"), "unsupported GHoT map")
        low, high = region or (0, len(observed["items"]))
        require(0 <= low < high <= len(observed["items"]), "attention outside source")
        index = low + int(address.center * (high - low))
        return {"type": "OSFieldSelection" if mode == "field" else "AttentionSelection",
                "source_item": index, **observed["items"][index]}
