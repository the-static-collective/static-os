# FIELD-CELL-001 — Scrap-Bench Physical Compute Specimen

**Status:** operator build preparation / documentation and analysis code. No assembled circuit, actual measurement, orchard installation, real sensor or electrically field-proven processor claimed.
**Parent:** [FIELD-PROCESSOR-001 in STATIC-OS PR #87](https://github.com/the-static-collective/static-os/pull/87); [GO.STATIC master planZ PR #12](https://github.com/the-static-collective/planZ/pull/12).
**Physical objective:** demonstrate a small measurable material-dependent analog transformation under controlled input, then decide whether the substrate meets a declared *circuit* or *processor* threshold.

## 1. First principle

A wet copper/soil/capacitor test is not "free energy," through-earth telecommunication, a geophone, or proof that soil computes. It can be a *modulated physical path* in an honest RC timing/filtering circuit, with the **capacitor** providing physical short-term electrical state and the soil path providing a condition-sensitive conductance. That is already a meaningful physical-computation study, but a computer-like processor claim requires independent controls showing that matter contributes a repeatable requested operation, not merely a sensor value.

## 2. Salvage inventory — find, don't buy yet

| Item | Low-risk source / use | Strict gate |
|---|---|---|
| 2× AA battery holder and two ordinary alkaline AA cells | 3-V-class isolated supply | **No salvaged loose lithium-ion cells, wall adapters, car batteries, mains, solar string or high voltage** |
| 100 kΩ resistor | hard series current limit | Visually identify/measure first; do not bypass |
| 10 kΩ resistor | reset/discharge resistor across capacitor, only while isolated from supply | Never short capacitor with bare metal; **charge off before reset** |
| 47–220 µF known-good electrolytic capacitor, ≥10 V rating | stores charge / physical state; 100 µF preferred | Polarity marked, no swelling/leakage; choose verified low-voltage provenance, not power-supply bulk capacitor |
| Breadboard or isolated scrap wood/cardboard mounting | dry holder for electrical connections | Do not assemble on grounded metal chassis |
| Two similar copper scraps or insulated wires with exposed clean ends | electrodes for finite sample | Similar area and spacing; no plumbing/utility/earth-ground connections |
| Small plastic cup or tray with identical soil sample | controlled physical cell | Keep fluids below electronics, away from outlets and food |
| Toggle/button or manually detachable insulated battery wire | finite CHARGE pulse | Disconnect power before soldering or editing circuit |
| Basic DC voltmeter/multimeter (high-impedance input preferred) | reproducible capacitor node voltages | Without one, qualitative observations are possible but not an earned quantitative proof |
| Optional alligator clips, ruler, measuring spoon, scale, notebook | stable repeatable geometry and moisture | Photograph only bench—not identifying domestic scenes or other people |

**If missing a meter:** complete a clean layout, continuity/polarity review and a no-power physical prototype. Do not claim voltage, threshold crossing, measurement or success from an LED alone. A simple known-safe data logger can be separately substituted after checking its input voltage ratings.

### Explicit exclusions for scavenging

Do not open or scavenge microwave ovens, CRT televisions, defibrillators, UPS power packs, flash capacitor assemblies, unknown power supply capacitors, sealed batteries or mains-connected appliances for this experiment. Such equipment can retain dangerously high voltage when unplugged. Do not connect anything to building power, telephone wiring, ground rods, electric fences, utility ground, trees, buried lines, water piping, outside soil stakes, Tesla coils or high-voltage transformers.

## 3. First circuit: finite electrical memory

All nodes are part of a single isolated battery-powered bench apparatus; never connect to USB, computer audio input, powered test equipment earth, or any other external supply.

~~~text
        2 × ordinary AA cells (~3.0 V total)
                 +
                 |
           SW-CHARGE (normally open)
                 |
           R_LIMIT 100 kΩ
                 |
          ELECTRODE A
           [plastic cup]
        soil bridge sample
           [plastic cup]
          ELECTRODE B
                 |
                 +---------> VOLTMETER + (read-only, high impedance)
                 |
              C (+)   100 µF, rated >=10 V
              C (-)
                 |
                 +---------> VOLTMETER - / BATTERY -
                 |
              BATTERY -

RESET PATH (SW-CHARGE OPEN; BATTERIES ISOLATED FIRST):
       C (+) ---- R_RESET 10 kΩ ---- C (-)
       Hold until the measured C voltage returns near 0 V,
       then remove reset path before the next CHARGE trial.
~~~

**No resistor means no test.** With a verified 100 kΩ series limiter and 3.2 V battery voltage, the ideal maximum battery-limited current from that path is at most 32 µA even if the soil electrodes accidentally contact. Copper electrodes may create their own galvanic potential or electrochemical polarization; measure an unpowered open-circuit control and note any offset. Brief tests only; no salt, acid, electroplating, plant/root insertion or long-lasting buried electrode.

**Important:** this topology demonstrates soil-dependent *charge delivery through an RC network*. The capacitor stores physical memory, not the soil. Later isolate and independently test any claimed soil hysteresis; don't infer such memory from residual capacitor charge.

## 4. Test protocol

1. **Catalog** a parts card: resistance values verified, capacitor rating/polarity, battery voltage under the same measurement instrument, electrode sizes and spacing, soil source (generic label only), container dimensions; photograph the isolated layout.
2. **Dry run without supply:** inspect cap polarity, bare copper and wire ends, physical insulation, current-limit resistor in series, no accidental path to powered equipment. Clamp/tape loose wires. Do not solder while batteries are inserted.
3. **FIXED resistor control:** replace *only* the soil cup path with a known 47 kΩ resistor. Record CHARGE voltage at t=0, 5, 10, 20, 40, 80, 160 seconds. Begin each trial with C reset near 0 V through R_RESET, supply disconnected; perform three repetitions.
4. **OPEN control:** replace soil path with physically disconnected electrodes. Expected near-no-rise; unexpected rise is important evidence of leakage/meter coupling/wiring mistakes.
5. **DRY soil:** keep electrode depth and spacing fixed; record three repeated charging curves with the same timings. Never presume a dry sample has infinite resistance.
6. **DAMP and WET:** add measured small quantities of plain water in increments to the *same* soil; keep geometry, supply and wiring unchanged, record three repetitions each. Avoid pooling and splashing. Allow settling; note it.
7. **Optional reversal test:** briefly reverse which copper electrode is the positive side, preserving capacitor orientation and R_LIMIT. Charge/discharge independently; look for electrochemical asymmetry. Treat any reversal effect as possible electrode behavior, not computation proof.
8. **Measure a RESET trace**, independently, only with supply disconnected and R_RESET connected. That traces the capacitor's actual memory decay.
9. Stop if wires heat, parts discolor/leak/swell, the meter reading exceeds the battery unexpectedly, polarization causes persistent drift, batteries get hot, or any part of the circuit touches an unverified powered system. At this microamp design there should be no noticeable heating.

**Record every trial, including zeros, failures and anomalies.** Never fabricate missing points and never smooth away unexpected effects.

## 5. Data columns / reproducible analysis

CSV: trial_id,condition,phase,time_s,supply_v,node_v

- condition: fixed, open, dry, damp, wet.
- phase: charge for the first accepted analyzer profile.
- time_s begins at 0 after reset and is strictly increasing.
- supply_v is independently measured and steady within a narrow tolerance; node_v is the positive capacitor node relative to the isolated battery negative.
- No actual location, full audio, personal identity or material origin disclosure required.

Use the stdlib-only analyzer:

~~~sh
python3 scripts/field-cell-analyze.py fixtures/field-cell-001/synthetic-rc.csv --classification SYNTHETIC
python3 scripts/field-cell-analyze.py my-benchtop-measurements.csv --classification USER_REPORTED_UNVERIFIED
python3 -m unittest discover -s tests -v
~~~

The analyzer reports SHA-256 of exact source bytes, per-trial normalized voltage at 10s, interpolated 63.2%-of-supply rise time if crossed, censored thresholds, monotonicity warnings, repeated trial counts, controls and refusal flags. It does not infer field physics, independently certify user readings, convert a receipt into proof of material causation, or actuate anything.

## 6. What would earn which claim?

**Bench wiring:** insulated, no accidental short, known values, correct polarity; a human checked it. NOT YET DONE.

**Physical observation:** real voltage measurements under declared conditions with instrument identity and exact CSV evidence. NOT YET DONE.

**Material-dependent transfer function:** damp/dry vs fixed/open produce reproducibly different charging behavior, with at least three trials per condition and a separately identified noise/error model. NOT YET DONE.

**Physical state / analog operation:** a defined input pulse yields a delayed or integrated output in C; observe charge/reset/threshold response versus a matched non-soil electrical control. The capacitor provides state; soil modulates the effective path. NOT YET DONE.

**Processor-level assertion:** a declared logic or stateful task depends on independently measured physical response and remains reproducible through held-out trials; substitute an inert circuit or software-only simulation to test whether the claimed environment-driven computation actually adds something. NOT YET DONE.

**Field network:** unrelated future radio/light/copper communications, with separate consent/permission and hardware results; not inferred from this cell.

## 7. The next weird composition (not wired yet)

After quantitative bench proof, follow the same one-way read-only data path:

~~~text
scrap copper + soil + two AA + RC state
  -> voltmeter or safely rated isolated low-voltage logger
  -> exact finite CSV with operator witness
  -> hashed analysis / anomaly and negative-control results
  -> optional read-only STATIC-OS FieldProcessorAdapter successor
  -> eleven-dial *selection* and local HOLD
  -> no automatic transmit, messaging or power control
~~~

A piezo pickup could later measure traffic-like mechanical vibration on an isolated tabletop (not ground truth about a public road); piezo elements may generate surprisingly high transients when struck. Do **not** wire an unclamped piezo directly into a microcontroller ADC. A separate protection/circuit review must precede that expansion.

## 8. Work split

**Human with soldering iron + scrap:** physical parts inspection, photography, bench isolation and manually measured test points, when ready. There is no need to solder the first fixture permanently; removable clips and a breadboard simplify controls.

**STATIC-OS experiment:** printable build plan, synthetic test data, strict offline analysis and adversarial tests.

**GHoT/tranchNOSE future:** independent source/witness adapters and controlled perturbation only after the first real measured circuit exists.

**PlanZ:** chronology, ownership, exact proposal/field evidence distinction and remaining test gates.

> The first triumph is not a living soil computer. It is a measurable, falsifiable handshake between ordinary material conditions and a real computational state.
