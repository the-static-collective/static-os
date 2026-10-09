# ALL-PRINTER-FIELD-012 — every printer is a potential address, not a universal driver

**Status: experimental, printer-agnostic discovery and proposal router.**
Stacked on [STATIC-PRINT-011](https://github.com/the-static-collective/static-os/pull/61), the actual PrusaSlicer G-code and verified native CAD source. Do **not** send its generic virtual G-code to physical hardware.

## The inversion

There is no universally safe or meaningful G-code for every 3D printer.
Filament systems may use firmware-specific motion/toolpath variants. Photopolymer systems need machine-specific layer/exposure formats and resin calibration. Powder/industrial systems have entirely different build, material, training and safety requirements.

**Universal object ≠ universal toolpath ≠ universal printer ≠ universal permission.**

So Static OS implements an *open-world addressable family field*, keeping technology, machine identity, verified original source, process preparation, physical operation, inspection, and accounting as distinct states.

```text
Original CAD 005 STEP/STL + signed reLATTE RECEIVED/R3_HOLD
     → Native cold source verifier
     → Real PRINT-011 virtual PrusaSlicer G-code packet (holds, never dispatches)
     → PRINT-FIELD-012 operator-supplied fleet declarations
     → Each printer receives a separate compatibility *proposal*
         ├─ original virtual 180mm FFF: SOFTWARE_TOOLPATH_ONLY
         ├─ real owner-declared FFF: HOLD_MACHINE_PROFILE
         ├─ resin, powder, jetting, metal, DED: HOLD_PROCESS_ADAPTER
         ├─ too small declared envelope: HOLD_DECLARED_ENVELOPE
         └─ unfamiliar process: HOLD_UNKNOWN_PROCESS
     → STOP. No new slicer execution, network, hardware, material or money.
```

### Recognized process families (not production drivers)

| Family | Initial status |
|---|---|
| FFF/FDM material extrusion | **Virtual PrusaSlicer adapter only**, physical machines HOLD |
| MSLA resin | Distinct process adapter required |
| Laser SLA resin | Distinct process adapter required |
| DLP resin | Distinct process adapter required |
| Polymer SLS | Build packing / powder adapter required |
| Polymer MJF | Vendor/process adapter required |
| Binder jetting | Binder/cure/material adapter required |
| Material jetting | Vendor/process adapter required |
| Metal powder-bed fusion | Industrial process and safety qualification required |
| Directed energy deposition (DED) | Industrial machine/robot and safety qualification required |
| Any future/unfamiliar process | Accepted as untrusted declaration; HOLD_UNKNOWN_PROCESS |

The code accepts *arbitrary text vendor/model labels* in owner-declared machine records; these labels are not a vendor database or machine authentication. Source/dimensions are checked against the **actual native signed CAD package**, but machine dimensions are merely supplied claims. They do not demonstrate a printer really exists or that orientations/clearances are mechanically feasible. Physical drivers, upload and start interfaces are explicitly absent.

### Operator usage

From a trusted Static OS 012 branch with the same original signed CAD package and actual held PrusaSlicer 011 packet used in previous experiments:

```sh
python3 scripts/static-printer-field.py catalog

python3 scripts/static-printer-field.py discover \
 --source dist/cad010-real-solid \
 --print-packet dist/print011-held \
 --fleet fixtures/printer-field-012/synthetic-fleet.json \
 --out dist/all-printers-012.json

python3 scripts/static-printer-field.py verify \
 --source dist/cad010-real-solid \
 --print-packet dist/print011-held \
 --fleet fixtures/printer-field-012/synthetic-fleet.json \
 --out dist/all-printers-012.json
```

This example fleet deliberately uses fictional labels and declarations across eleven known/unknown technologies plus one frozen virtual print profile; **it is not a list of real supported devices**. `discover` writes one private output file with O_EXCL; replay is read-only; an existing output is never overwritten. No auto-retries on ambiguous state.

**Executable files:** `question_first/printer_field.py`, `scripts/static-printer-field.py`, immutable `fixtures/printer-field-012/technology-registry.json`, synthetic fleet fixture, dedicated hostile tests and source-native CI.

### Risk and authority

- Source 011 packet is verified against original signed native reLATTE CAD receipts, actual model STEP and real sliced G-code. 012 makes no new claim about the authenticity of a detached JSON report; it can be forged if taken without the complete source files and trusted verifier.
- Every physical machine remains `HOLD_MACHINE_PROFILE` / `HOLD_PROCESS_ADAPTER` / `HOLD_DECLARED_ENVELOPE` / `HOLD_UNKNOWN_PROCESS`. An owner-supplied profile reference is never machine authorization.
- A valid FFF virtual job cannot be recycled into an MSLA/SLS/metal print job; each process needs its *own real native engine and validated machine profile*.
- The geometrical envelope check assumes unchanged CAD axes; an oversize result is a conservative proposal blocker, not proof that a reorientation could never work.
- A discovered printer has no material inventory, operator grant, firmware verification, network credentials, energy/power authorization or physical completion evidence.
- Print jobs, material usage, printing services and physical parts cannot be counted in Jubilee merely through software projections or source signatures. Physical inventory only enters after independent owner-local witness and review.
- Industrial metal/powder machines involve additional hazards. No motor, laser, high-temperature extruder, heater, industrial robot or firmware operations may be inferred from this discovery system.

## Next executable adapters

Keep `prepare`, `slice`, `transfer`, `start`, `observe`, `inspect`, `release` as **separate source-owned capability doors**. A future donor-specific plugin should expose a machine-specific profile with source identity, original manufacturer/firmware documentation, material, byte-level packaging, preflight evidence, explicit owner selection and an independent physical safety case. Never add one global authority bit for all printers.

**Laws:** `SUPPORTABLE != SUPPORTED`; `DISCOVERABLE != CONNECTED`; `FAMILY != MACHINE`; `SOURCE PROOF != TRANSFERABLE RIGHTS`; `TOOLPATH != START`; `SLICED != PRINTED`; `PHYSICAL WORK != ACCOUNTING ENTRY`.
