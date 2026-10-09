# ROBOT-GARDEN-003 — GoPro joins the eyes

**Status:** real JPEG/PNG file intake and a generated *nominal* calibration target.
No connected GoPro, camera automation, proof of a physical object, physical
calibration or robot action. Stacked on ROBOT-GARDEN-002 (#70), 001 (#68)
and source-verified fabrication 013 (#66).

## Three donor roles

| Operator-supplied file | Intended observation | Verified by software |
|---|---|---|
| Phone JPEG/PNG | Portable scene and surroundings | Original bytes, decoded image metrics, hash |
| Canon EOS Rebel T3i / 600D JPEG/PNG | Controlled detail | Original bytes, decoded image metrics, hash |
| GoPro JPEG/PNG | Wide-field context or manually extracted video still | Original bytes, decoded image metrics, hash |

Different file digests do **not** guarantee different devices, different
sessions, or photographs of the same physical part. Each device name remains
an operator claim, not an identity attestation. The software neither pairs
cameras nor authenticates capture time from EXIF.

A frame taken from a GoPro MP4 can be processed as PNG or JPEG **only after**
manual extraction, but the frame-to-video relationship is unverified here.
002/003 do not decode or retain an original video recording's hash. A separate
provenance-aware video adapter is required before asserting video ancestry.

## Why GoPro lens mode matters

Digital lens presets (Wide/Linear/etc.) depend on model and processing.
Wide and SuperView are **not** interchangeable with an ordinary pinhole lens.
The optional operator declaration records model and lens mode but no objective
lens intrinsics or geometric correction:

`fixtures/robot-garden-003/gopro-operator-declaration.json`

The default is `UNKNOWN GOPRO MODEL` and `UNKNOWN` lens. Choose another
label **only if you know it**. The declared mode remains unverified. No
photo measurements are in millimeters based on its declaration.

GoPro documentation:
- https://gopro.com/en/us/shop/buy-cameras/mission-1-series
- https://gopro.com/content/dam/help/hero10-black/manuals/HERO10Black_UM_ENG_REVB.pdf

## Nominal chart

Generated `nominal-checkerboard.svg` is:
- 10 squares across by 7 squares down
- 9 by 6 *internal* corner lattice
- nominal 15 mm per square
- nominal 150 by 105 mm actual square pattern, plus 12 mm border per side
- full SVG 174 by 129 mm

This is a **design**, not an actual measured/printed scale. Print at 100%
scale and measure squares physically with a ruler or calipers. Until measured,
actual square dimensions remain `null`. No lens distortion parameters,
reprojection errors, camera extrinsics or accepted measurements are produced.

Future legitimate calibration will require:
1. A physically verified chart with its actual printed square measurements.
2. Multiple actual frames at distinct chart tilts and frame positions per
   camera, retained as original evidence.
3. A real lens-specific calibration routine with holdout reprojection error,
   estimated intrinsics/distortion and uncertainty.
4. Camera-mode and output-resolution-specific calibration validity, with
   clear refusal when unavailable.
5. Separately reviewed action/custody privileges before robot motion.

## Run

Upstream must already have built original source-verified 013 artifacts.
Requires Python Pillow `>=11,<13`.

```bash
python3 -m pip install 'Pillow>=11,<13'
python3 -m unittest tests.test_robot_garden_three_eyes_003 -v

python3 scripts/static-robot-garden-three-eyes.py receive \
  --source dist/cad010-real-solid \
  --packet dist/print011-held \
  --fleet fixtures/printer-field-012/synthetic-fleet.json \
  --selection fixtures/fabrication-013/three-node-selection.json \
  --request dist/fabrication-request-013.json \
  --station fixtures/robot-garden-001/synthetic-jubilee-station.json \
  --phone-photo /local/phone.jpg \
  --t3i-photo /local/t3i.jpg \
  --gopro-photo /local/gopro.jpg \
  --gopro-lens fixtures/robot-garden-003/gopro-operator-declaration.json \
  --chart-spec fixtures/robot-garden-003/nominal-checkerboard.json \
  --out-dir dist/robot-garden-003-three-eyes

# Change receive -> verify, retaining all the original input paths,
# to reconstruct plan, photo hashes, metrics, receipt and exact chart.
```

Output is `receipt.json` and `nominal-checkerboard.svg`. The program
opens originals locally, does **not** upload photos or EXIF/GPS, and writes
only hashes/decoded image metrics to the receipt; hashes can still be sensitive
when correlated externally. Source 013 original CAD, selected fleet and
held slicer are cold verified before receipt issuance. Output directory is
once-only, so interrupted generation requires operator review of remnants
rather than automatic retry.

Current CI creates generated fixture photos in temporary directories; it
never claims real GoPro or real T3i hardware was present.

**Laws:** `GO_PRO_FILE != GOPRO_ATTESTATION`,
`LENS_PRESET != CALIBRATION`, `SVG != MEASURED_CHART`,
`TRIPLE_HASH != INDEPENDENT_PHYSICAL_WITNESS`,
`SOURCE_CAD != PRINTED_PART`, `NO_GRANT != ROBOT_CONTROL`.
