# ROBOT-GARDEN-002 — phone + Canon EOS Rebel T3i as the first real image donors

**Status: executable image-file intake.** It decodes genuinely supplied local
JPEG/PNG files but has **never claimed connected camera hardware**. The included
CI images are generated fixtures, not phone/T3i photographs. The opening
experiment is designed to accept owner-supplied camera originals locally.

**Parent:** [ROBOT-GARDEN-001](robot-garden-001.md), stacked on signed
FABRICATION-CROSSING-013. Owns no printer, robot, toolchanger, actual camera,
independent witness, verified part, or granted control interface.

## What is implemented

- Two fixed operator-declared roles: `PHONE_OPERATOR_IMPORT` and
  `CANON_EOS_REBEL_T3I_600D_OPERATOR_IMPORT`.
- JPEG and PNG magic sniff + Pillow decode verification; image side, pixel and
  compressed-byte limits. Cropped/scanned thumbnails processed offline.
- SHA-256 of original encoded bytes, source-role tag, byte length, dimensions,
  EXIF-oriented dimensions (orientation itself is not authenticated), mean
  brightness, low/high exposure fractions, average local luminance delta.
- A paired, content-addressed JSON dossier. It refuses the *same file bytes*
  masquerading as two camera witnesses, and replays its calculations against
  the original files.
- Explicit nonclaims: unverified camera names, no authentic timestamps or
  independent device attestations, no real part or shared capture identity,
  no measurement calibration, custody, stock, machine effects, or signed
  sensor outputs.

The metrics are **image quality heuristics**, not focus certification or
physical metrology. Distinct byte hashes do **not** prove different cameras:
someone could re-encode or modify one image. Both camera roles are labels
provided by the operator, not authenticated device identities.

## Physical image acquisition

**Phone:** Photograph the test object and its environment. Prefer original
JPEG, no messenger recompression, filters or screenshot, and transfer it
to your local workstation via USB/file copy.

**Canon EOS Rebel T3i (EOS 600D):** Shoot a separately framed JPEG, ideally
with stable support, deliberate manual focus and fixed lighting. Bring the
JPEG to the workstation from the SD card or using standard Canon USB photo
transfer. A Canon `CR2` RAW original may also be preserved separately, but
RAW decoding and sidecar linking are **not implemented** in 002.

A useful physical next step is to place a *known dimension checkerboard or
fiducial* in both views. However, the present code does **not** use a
checkerboard to derive physical dimensions or prove the photos depict the
same object. Camera-on-robot controls are intentionally absent.

Canon documentation: https://www.usa.canon.com/support/p/eos-rebel-t3i .
Photo import is used instead of gphoto2 or EOS Utility remote capture; either
could be evaluated by a separate owner-reviewed adapter later.

## Run

Requires original native CAD, held slicer packet, source-verified 013 proposal
from upstream. Python `Pillow>=11,<13` is the only new image decoder.

```bash
python3 -m pip install 'Pillow>=11,<13'
python3 -m unittest tests.test_robot_garden_photos_002 -v

python3 scripts/static-robot-garden-photos.py receive \
  --source dist/cad010-real-solid \
  --packet dist/print011-held \
  --fleet fixtures/printer-field-012/synthetic-fleet.json \
  --selection fixtures/fabrication-013/three-node-selection.json \
  --request dist/fabrication-request-013.json \
  --station fixtures/robot-garden-001/synthetic-jubilee-station.json \
  --phone-photo /path/to/phone-original.jpg \
  --t3i-photo /path/to/t3i-original.jpg \
  --out dist/robot-garden-002-pair.json

# Change receive to verify to replay with the exact original photos.
```

**Privacy:** The local program reads the two photos; it does not copy, upload,
or persist their bytes. Only hashes and basic metrics are written to the JSON
dossier. EXIF GPS tags and embedded camera serials are neither trusted nor
reproduced. **Do not** commit personal image originals to Git. The generated
receipt *does* reveal that a particular file hash was processed, so treat it
as potentially identifying when sharing publicly.

The repository CI creates its own synthetic JPEGs and PNGs and runs the
actual decoder; the CI artifacts do not contain original human photographs.

## What next

1. Capture real phone and T3i originals as a sample set for local ingestion.
2. Repeat scenes under controlled lighting, put a measured scale artifact in
   each view, and establish fiducial detection with uncertainty reporting.
3. Add separated import/measurement provenance and independent signatures,
   never treating JPEG EXIF, digest, or camera brand as a source identity.
4. Test a **stationary camera-only** physical workflow with separately reviewed
   consent and any applicable hardware safety grants, before mobile robotics.

**Rules:**
`PHOTO_FILE != CAMERA_AUTHENTICATION`;
`EXIF != TRUSTED_TIME`;
`PIXEL_QUALITY != PHYSICAL_GEOMETRY`;
`DIFFERENT_DIGESTS != DIFFERENT_DEVICES`;
`HASH != SIGNATURE`;
`CAPTURE != CUSTODY`;
`NO_PHYSICAL_PART != ADD_INVENTORY`.
