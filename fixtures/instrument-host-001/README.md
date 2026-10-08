# Recorded input fixture

`two-stations.wav` is a 128-frame stereo, signed-16-bit little-endian PCM WAV at
8,000 samples/second. Its left track is a 16,000-amplitude 440 Hz sine and its right
track a 12,000-amplitude 880 Hz sine. Samples are truncated to integers.

The adapter labels the tracks as synthetic stations at 90 MHz and 106 MHz.
These are declared fixture labels, not measured RF carrier frequencies.
Frequency selection chooses the nearest declared station; attention selects a
sample in the previously selected station's track.

There was no microphone, tuner, antenna, network stream, or physical capture.
The fixture demonstrates bounded input selection and provenance without claiming
real radio reception. Its SHA-256 is pinned in `manifest/instrument-host-001.json`.
