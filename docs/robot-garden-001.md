# ROBOT-GARDEN-001 — the workshop grows an inspection eye

**Status:** experimental, no physical hardware, no photographed part, no machine control.
**Owning repo:** Static OS. Stacked on `FABRICATION-CROSSING-013`.
**Hardware inspiration:** [Machine Agency Jubilee](https://github.com/machineagency/jubilee) and
[Science Jubilee](https://github.com/machineagency/science-jubilee). They are cited
as references, **not** installed Python dependencies or verified hardware integrations.
This experiment is not affiliated with or endorsed by Machine Agency.

## What this slice actually does

```
GHoT-authored question / Static CAD
    → real CAD kernel + native reLATTE signed source CAD
    → held PrusaSlicer G-code (NO printer)
    → exact 012 machine compatibility field
    → source-cold-verified 013 three-node proposal
    → ROBOT-GARDEN simulated Jubilee camera station declaration
    → 2D target dimensions read from verified source solid
    → deterministic locally synthesized P5 grayscale image
    → separately scan the actual image bytes for occupied-pixel bounding box
    → simulated MATCH or MISMATCH report
    → independent replay using original CAD/print/selection + image bytes
```

The vision algorithm measures pixel geometry. It does **not** trust a prewritten
"measured width" fixture, or claim that the image came from a real camera.
The target is the XY bounding envelope of a source-verified solid, **not** a
claim that optical inspection can validate an arbitrary complete 3D geometry.

For readability and reproducibility: the synthetic target is a solid black
rectangle in a white frame. It is intentionally too simple to claim robust
computer vision, industrial metrology, calibration, or robot alignment.

## Run

Requires original successfully generated signed source and held slice from the
upstream 013 CAD pipeline. A detached fabrication JSON cannot authorize a plan.

```bash
python3 -m unittest tests.test_robot_garden_001 -v

python3 scripts/static-robot-garden.py run \
  --source dist/cad010-real-solid \
  --packet dist/print011-held \
  --fleet fixtures/printer-field-012/synthetic-fleet.json \
  --selection fixtures/fabrication-013/three-node-selection.json \
  --request dist/fabrication-request-013.json \
  --station fixtures/robot-garden-001/synthetic-jubilee-station.json \
  --out-dir dist/robot-garden-001

python3 scripts/static-robot-garden.py verify \
  --source dist/cad010-real-solid \
  --packet dist/print011-held \
  --fleet fixtures/printer-field-012/synthetic-fleet.json \
  --selection fixtures/fabrication-013/three-node-selection.json \
  --request dist/fabrication-request-013.json \
  --station fixtures/robot-garden-001/synthetic-jubilee-station.json \
  --out-dir dist/robot-garden-001
```

Try a deliberately undersized synthetic part by adding
`--mock-width-factor 0.75` to `run` with a **different output directory**.
It must yield `SIMULATED_GEOMETRY_MISMATCH`, not a fabricated success.

Outputs: `plan.json`, `mock-frame.pgm`, `report.json`. An output directory
must be absent before run, and is never overwritten on automatic retry.
Cold replay regenerates the plan from signed original data, scans the retained
image independently, and compares the complete reconstructed report.
Content-address hashes check equality; they are **not** digital signatures and
cannot establish provenance of an independently supplied sensor image.

## Hard boundaries

| Demonstrated | Not demonstrated |
|---|---|
| Signed source verification through existing CAD and 013 parent | Real Jubilee authentication |
| Offline synthetic camera pixel measurement | Actual optical capture or calibration |
| Stable IDs, replay and refusal on mutations | Tamper-proof or signed sensor witnesses |
| Simulated dimension failure branch | Actual part inspection |
| Explicit owner permission remains absent | Heater, servo, gripper, toolchange or motion |
| Historical evidence without increased inventory | Physical stock, repair, revenue, or replication |

**Rules:** `SOURCE != PHYSICAL PART`; `IMAGE != SENSOR`;
`SIMULATED MATCH != QA ACCEPTANCE`; `PROPOSAL != MOTION`;
`SLICED != PRINTED`; `DIGEST != SIGNATURE`.

No network clients, HTTP tool endpoints, serial writes, GPIO, printer or robot G-code,
toolchange macros, or firmware paths are imported by the ROBOT-GARDEN runtime.

## Next physical experiment — gated, NOT implemented

1. Select an actual, operator-owned camera and independent physical part fixture.
2. Authenticate the robot controller and station incarnation. Explicitly pin
   its trust and separate source design evidence from local machine authority.
3. Produce calibrated camera intrinsics/extrinsics with traceable target and
   uncertainty. Plan a human-reviewed motion envelope plus collision controls.
4. Require owner-specific admitted, short-lived grants *only for the exact
   proposed action*; hardware e-stop and fail-safe boundaries remain separate.
5. Witness real part manufacture, location, custody and independent
   inspection. Sign the capture with station owner keys before reLATTE transfer.
6. Locally decide acceptance. Never turn a camera image or simulated receipt
   into inventory, production, safety certification, or payment by itself.

A future Science Jubilee adapter is a new **separate** organ with explicit
physical-machine capability review, not an import into this simulator.

The Jubilee name is an independently existing hardware project. The Static
Collective's Jubilee treasury and Jubilee economic experiments are distinct.
