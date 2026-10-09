# ROBOT-GARDEN-004 — GoPro HERO3 (2012), provisionally targeted

**Status:** operator-imported local H.264 MP4 → reproducible decoded PNG frame
→ 003 three-camera observation receipt → 001 signed-source inspection plan.
**Not** a GoPro connection or a tested camera. The user only tentatively
identified the GoPro as possibly a 2012 HERO3. Black, Silver, White, firmware,
serial, camera ownership, and even the exact generation remain UNKNOWN.

**Branch stacks:** 004 → [003](robot-garden-003.md) → [002](robot-garden-002.md)
→ [001](robot-garden-001.md) → native signed fabrication 013.

## Why the 2012 HERO3 is a good reference

Official GoPro 2012 HERO3 manuals identify a microSD slot, mini-USB, Micro HDMI
and the original HERO3 generation; the three editions have distinct firmware
releases. A manually copied H.264 `.MP4` is a pragmatic offline video input.
No claim that newer GoPro Open GoPro APIs work on the HERO3. The initial target
does not require Wi-Fi (older Wi-Fi protocols should be reviewed separately).

References:
- GoPro HERO3 Black manual:
  https://static.gopro.com/content/dam/help/hero3-black-edition/manuals/HERO3_UM_Black_ENG_REVD_WEB.pdf
- All editions' GoPro HERO3 software versions:
  https://gopro.com/en/us/update/hero3

## Exact behavior

1. Cold verify the original signed native CAD, real held virtual G-code, exact
   synthetic machine fleet and human-chosen 013 fabrication request.
2. Derive the 001 plan from source-verified CAD dimensions. A detached JSON
   source can't claim it crossed.
3. Read an operator-selected local MP4 (up to 512 MiB, accepted only as a local
   file). Compute SHA-256 over original file bytes.
4. Locally probe first video stream. Require H.264 in MP4, bounded dimensions.
   Select an explicit **zero-based decoded frame index** with a fixed ffmpeg
   command and file-only source protocol.
5. Decode exactly that frame to PNG, hash bytes, rehash original MP4 afterward.
6. Feed the decoded PNG through the 003 third-camera role while separately
   distinguishing `derived video frame` from `original GoPro still image`.
   Phone and Canon T3i originals still enter 002 as distinct JPEG/PNG sources.
7. Retain a content-addressed JSON receipt and decoded frame. Verification
   replays all input media, frame extraction, target/plan and original source
   from scratch. The image cannot remain a witness after its source changes.

A frame number is **not** a trustworthy time, exposure/synchronization
measurement, camera serial, or GPS claim. The original MP4 file is **not copied**
into the output directory; only the frame and JSON are saved there. Do not
upload private media, frame PNG or receipts without considering privacy.

ffmpeg processing is bounded but remains an attack surface for malformed,
untrusted media. This is an experimental local importer, not a hardened
unattended media service. Use a sandbox for externally obtained files.

## Bring one old GoPro recording into the garden

Record a **short** video with the actual GoPro, once found; transfer the
original `.MP4` file from the microSD card. No Wi-Fi or USB camera control.
Capture one normal phone photo and a T3i JPEG for the same scene if possible.
Those labels are operator-provided and the software does not authenticate the
cameras or assert they photographed the same object.

Python `Pillow>=11,<13`, local `ffmpeg` and `ffprobe` required.

```bash
python3 -m unittest tests.test_robot_garden_hero3_video_004 -v

python3 scripts/static-robot-garden-hero3-video.py receive \
  --source dist/cad010-real-solid \
  --packet dist/print011-held \
  --fleet fixtures/printer-field-012/synthetic-fleet.json \
  --selection fixtures/fabrication-013/three-node-selection.json \
  --request dist/fabrication-request-013.json \
  --station fixtures/robot-garden-001/synthetic-jubilee-station.json \
  --phone-photo /local/phone.jpg \
  --t3i-photo /local/t3i.jpg \
  --gopro-video /local/GOPR0001.MP4 \
  --hero3-profile fixtures/robot-garden-004/provisional-hero3-2012.json \
  --gopro-lens fixtures/robot-garden-003/gopro-operator-declaration.json \
  --chart-spec fixtures/robot-garden-003/nominal-checkerboard.json \
  --frame-index 0 \
  --out-dir dist/robot-garden-004

# Repeat with 'verify' instead of 'receive' to cold-redecode exact originals.
```

`receive` refuses to replace an existing output directory. Output files are
`video-frame-receipt.json` and `gopro-derived-frame-000000.png`. Changing
frame index changes the output frame path; use a fresh output directory.
The full source chain must exist; this adapter is not a shortcut around 013.

To visually inspect the calibration target, see
[`nominal-checkerboard.svg`](../fixtures/robot-garden-003/nominal-checkerboard.svg).
It is **uncalibrated** until the physical chart is measured.

## Boundaries and next hardware door

| This experiment does | It explicitly does **not** do |
|---|---|
| Inspect true bytes from local MP4 | Authenticate original capture device |
| Require H.264 and first video stream | Auto-discover actual GoPro model/edition |
| Select a reproducible frame index | Trust media time, lens, GPS or EXIF |
| Retain MP4↔PNG source hash relation | Digitally sign a real camera capture |
| Preserve 003 photo roles separately | Infer physical object identity from 3 files |
| Replay signed CAD and paper chart | Perform measured lens calibration |
| Emit no camera/robot commands | Connect GoPro Wi-Fi or drive toolchanger |

Even if a HERO3 Black can be connected over Wi-Fi, Wi-Fi reachability does not
create permission or a secure authenticated session. A future *physical*
GoPro controller must separately identify exact edition, firmware, electrical
power, access permission and safety boundaries.

`HERO3_PROVISIONAL != IDENTIFIED_DEVICE`;
`VIDEO_DECODED != CAMERA_AUTHENTICATED`;
`DERIVED_FRAME != ORIGINAL_STILL`;
`FRAME_INDEX != TRUSTED_CAPTURE_TIME`;
`VIDEO_FILE_SHA != VIDEO_SIGNED_AT_CAPTURE`;
`LENS_MODE != MEASURED_OPTICS`;
`CAMERA_REACHABLE != ROBOT_AUTHORIZED`.
