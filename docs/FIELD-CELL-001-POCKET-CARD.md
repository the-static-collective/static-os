# FIELD-CELL-001 — Pocket Build & Observation Card

**STATUS:** PREP ONLY — NOT A CLAIM OF A BUILT OR OPERATING ELECTRICAL DEVICE.

## First pull from the scrap pile
- [ ] Two ordinary AA alkaline cells + isolated two-cell holder, no lithium cells or power adapter
- [ ] 100 kΩ series limiter (measure or reliably identify)
- [ ] 10 kΩ reset resistor (measure or reliably identify)
- [ ] One 47–220 µF **known-good, marked, rated at least 10 V** capacitor; plus and minus confirmed
- [ ] Two similar small copper pieces (clean, identical contact area)
- [ ] Nonmetallic cup, modest soil sample, clean water, ruler and dry insulating base
- [ ] Wires, clips or breadboard, optional soldering iron (only with batteries OUT)
- [ ] DC multimeter for quantitative proof; without it do assembly/preflight only

**NO:** unknown power-supply capacitors, CRT/microwave/flash salvage, outlets/mains, land stakes, house ground, energized phone wires, solar strings, car batteries, Tesla coils, plant roots or an external USB/audio connection.

## Circuit audit

~~~text
AA (+) -- [manual supply switch] -- [100k LIMIT] -- Cu A
                                               small soil cup
VOLTMETER (+) --- capacitor (+) -- Cu B

capacitor (-) -------------------- AA (-) / VOLTMETER (-)

RESET ONLY WHILE SUPPLY OFF:
capacitor (+) -- [10k RESET] -- capacitor (-)
~~~

Voltage read only between capacitor plus and isolated AA minus. Keep capacitor polarity the same for every trial. Confirm R_LIMIT is in series before power is applied. RESET path must not be engaged during CHARGE. No intentional short circuit.

## Part witness
| Field | Value / check |
| --- | --- |
| Date / local run alias | |
| AA voltage at start / end | |
| R_LIMIT actual Ω | |
| R_RESET actual Ω | |
| C µF / voltage rating | |
| Electrode contact area / separation | |
| Cup / soil mass, generic source | |
| Fixed reference resistor Ω | |
| Meter model / input impedance known? | |
| Batteries removed for solder work? | |
| Dry, insulated mounting inspected? | |

## Repeated CHARGE runs

Use 0, 5, 10, 20, 40, 80, 160 seconds as a first sampling schedule, or record precise alternatives. Three trials each; capacitor reset close to 0 V between runs; note real supply readings. Keep electrode geometry consistent. Plain water only. Dry the bench afterward.

| Condition | Three trials | Notes |
| --- | --- | --- |
| FIXED: replace soil with known 47k resistor | ___ ___ ___ | baseline circuit behavior |
| OPEN: disconnected electrode gap | ___ ___ ___ | negative control |
| DRY: first soil condition | ___ ___ ___ | electrical insulation may dominate |
| DAMP: add measured water | ___ ___ ___ | wetting history matters |
| WET: further measured water | ___ ___ ___ | pooling is not desired |

CSV header for later:

    trial_id,condition,phase,time_s,supply_v,node_v

Example **FORMAT ONLY, not a measured row**:

    dry-1,dry,charge,0,3.04,0.00

Run: python3 scripts/field-cell-analyze.py YOUR_READINGS.csv --classification USER_REPORTED_UNVERIFIED

## Refusal gate

Do not power the circuit unless current limiter, capacitor marking and polarity, AA-only isolation, and stable dry bench are all confirmed. Stop for hot batteries, unexpected voltage, damaged components, or unsafe salvage. Never extrapolate this experiment to household electrical, radio transmission or outdoor ground wiring.

**What happened?** _______________________

**What remained unexplained?** _______________________

**What one condition should we change next?** _______________________

**What would disprove our exciting interpretation?** _______________________
