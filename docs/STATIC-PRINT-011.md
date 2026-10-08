# STATIC-PRINT-011 — Real FDM slicing from signed CAD, printer operations STOP

**Experiment: actual CAD/actual slicer/actual G-code; NO physical printer execution.**

This is the next step after [STATIC-ECONOMICS-010](https://github.com/the-static-collective/static-os/pull/59), stacked on the same native CAD-005/006/reLATTE sources.

## Actual path

```text
question and source-grounded apparatus
  → real solved CAD sketch
  → actual CadQuery/OpenCASCADE solid and STEP + STL
  → native reLATTE signed crossing and RECEIVED / R3_HOLD
  → cold Static OS source/signature/STEP verification
  → choose one frozen virtual FFF PLA profile
  → actual PrusaSlicer --export-gcode --load profile --center 90,90
  → real G-code toolpath from the source STL
  → byte hashes and bounded G-code preflight
  → PRINT_JOB_CANDIDATE_NOT_AUTHORIZED (HOLD)
  → stop, no network, USB, serial, temperature or motor operations
```

This is not a mock slicer or a hand-written fabricated toolpath. The frozen generic virtual machine profile is for a **hypothetical** 180 × 180 × 180 mm FDM printer, Marlin-flavored G-code and generic PLA at 205 °C nozzle / 55 °C bed. **It is not a valid calibrated profile for anyone's actual hardware. Do not send this demonstration G-code to a printer.** Each real machine's firmware, dimensions, offsets, extruder, filament, mesh, heater protection, bed leveling, print surface and maker instructions need explicit review and fresh locally selected configuration.

### Executable

The source already must contain the original signed CAD-005 `solid.step`, `solid.stl`, `sketch.json`, `design-trace.json`, `evidence-manifest.json`, `relatte-evidence.json`.

```sh
# PrusaSlicer installed and available as prusa-slicer in PATH
python3 scripts/static-print.py slice \
  --source dist/cad010-real-solid \
  --packet dist/print011-held

# Cold source and output verification (does not rerun slicer):
python3 scripts/static-print.py verify \
  --source dist/cad010-real-solid \
  --packet dist/print011-held
```

On Linux without an active graphical display, a suitable local virtual display can be used for this **software-only** experiment, e.g. `xvfb-run -a python3 scripts/static-print.py slice ...`.

Output is one new folder with:
- `PREPARED.json`: written before invoking slicer; no ambiguous automatic retry.
- `source-design.json`: exact source-owned 010 design candidate.
- `profile.ini`: a copy of the frozen virtual printer settings.
- `toolpath.gcode`: actual PrusaSlicer output from the verified STL.
- `preflight.json`: conservative G-code bounds/opcode review and motion/extrusion evidence count; **not** a firmware interpreter or safety certification.
- `packet.json`: exact digests, source crossing, slicer version claim, all hardware flags false, content-addressed packet ID.

No full physical printer command path, OctoPrint API, Moonraker, USB serial adapter or GHoT actuation is implemented. A transferred G-code file is potentially executable on hardware, but this experiment **does not transfer it**. Print-source authentication and cryptographic owner identity are distinct from the content hashes in the packet; no new reLATTE signature is claimed for the slicer output.

### Not yet allowed

- Actual printer setup, machine selection or electrical/thermal safety review
- Loading actual material, reserving spool stock or purchasing equipment
- Upload to OctoPrint/Moonraker, streaming G-code, serial connect or printer start
- Engineering strength/fit, food/medical/vehicle safety or load-bearing guarantees
- A physical machine/part inventory credit in Jubilee Treasury
- Autonomously multiplying prints because one digital design exists

The **physical reality loop** would require a particular printer and owner-authorized machine profile; human thermal/fire/ventilation review; material identity and confirmed inventory; operator-selected toolpath; one bounded actual print attempt; independent completion/inspection; separately signed receipts; then human-admitted physical resource capacity. A print attempt, successful G-code generation or signed design alone cannot mint finished objects.

### CI acceptance

The dedicated workflow installs real CadQuery/OCCT and Ubuntu PrusaSlicer, constructs an actual CAD-005 solid, performs native reLATTE signed RECEIVE/R3_HOLD, cold-exports 010 design evidence, slices it with the actual native slicer, checks input/output hashes and runs adversarial tests. Hostile tests reject changed G-code bytes, forged packet claims, arbitrary firmware operations, exceeding nozzle/bed temperatures, bounds escapes, untrusted profile changes and a second automatic slice occurrence.

**Laws:** `MODEL != PART`; `SLICED != PRINTED`; `GCODE != MACHINE PERMISSION`; `SIGNATURE != SAFETY`; `SIMULATED BOUNDS != COLLISION PROOF`; `DESIGN REUSE != MATERIAL CREATION`; `AUTORETRY != RECOVERY`.
