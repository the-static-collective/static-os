# KETTLENODE-002 — THE HEAT COMMONS

**An executable routing hypothesis for water, heat, life support, and computing.**

**Status:** simulation only. This branch is stacked directly upon KETTLENODE-001, PR #78, commit `99d3a12faf1cd5502793091a0ac99754a75d39fc`. It has not operated a pump, valve, fish farm, hydroponic system, photovoltaic array, battery, boiler, generator, or thermometer.

## The critical discovery: the cold side is an organ

A harvested thermal watt cannot be promised twice. A thermoelectric generator needs a sustained hot/cold gradient; a greenhouse needs reliably comfortable temperature; an aquaponics tank needs stable oxygenation and water quality. The useful composition is a directed heat cascade with physically independent fluid domains.

```text
                   SUN   /   COMPOST   /   COMPUTE WASTE HEAT
                    |          |                 |
          [collector / HX] [isolating HX]   [closed coolant loop]
                    \          |                 /
                       CLEAN THERMAL MANIFOLD
                               |
                       INSULATED HEAT BANK
                       /       |         \
                 [HX]         [HX]       [cold sink / heat pump]
                  |            |                   |
             FISH WATER     ROOT ZONE          GROUND / AIR
                |               |
          aeration/filter     plant nutrients
                |               |
           independent bio water loops; never joined to manure,
           compost leachate or potable supply through a valve
```

The diagram is a *logical* arrangement of components, not a complete engineered schematic, permitted potable-water interconnection, or permission to construct an untested pressure vessel.

## Candidate organ inventory

| Organ | Why it matters | First witness |
| --- | --- | --- |
| Hot and cold banks | Store heat or a cold sink across time; sizing/insulation matter | measured temperature change vs tank mass |
| Exchanger manifold | Transfer heat without mixing contaminated/biological fluids | independent inlet/outlet temperatures and flow |
| Photovoltaic + solar thermal / PVT | Direct electric supply plus heat recovery, not serially multiplying energy | separately meter electricity and useful heat |
| Compost source | Variable, unreliable biological low-grade heat | insulated test bed and detached sensors; no fish exposure |
| Heat pump | Spend electricity to raise or lower thermal grade | separately meter electrical input and transferred heat |
| Fish/aquaponics loop | Life support first, thermal loads second | dissolved oxygen, temperature, water chemistry, backup aeration |
| Hydroponic root zone | Plant thermal, water, and nutrient targets differ from fish | root temperature, EC, pH, recirculation |
| Computer coolant | Reject waste heat and maintain hardware safe limits | CPU power and coolant inlet/outlet |
| Humidity and ventilation | Transpiration, condensation, fungus prevention and latent heat | dew point, airflow, condensate analysis |
| Ground/air cold side | Where rejected heat can actually go | seasonally varying sink temperature and impact |
| Insulation and freeze protection | Avoid losing captured energy through piping or storage | monitored losses and freeze contingencies |
| Controls and manual bypass | Fail safe when a sensor, pump, or network breaks | unplug and fault drills |

### Biological guarantees

- FISH IS NOT A HEAT DUMP. Monitor dissolved oxygen, aeration/flow, ammonia/nitrite, pH and temperature independently. Independent emergency aeration and pump power take priority over optional computation. FAO aquaponics guidance: https://www.fao.org/newsroom/story/Seven-rules-of-thumb-to-follow-in-aquaponics/en
- Do not directly circulate compost fluid, glycol, machine coolant, potable water or hydroponic nutrients into fish water. Separation needs engineered, application-approved exchangers and appropriate contamination controls.
- Tap/domicile potable hot-water circuits are separate and subject to building/plumbing rules and water-management controls. Temperature, stagnation and Legionella hazards are not removed simply by using a sealed thermal loop. CDC: https://www.cdc.gov/control-legionella/php/toolkit/potable-water-systems-module.html
- Elevated temperature can reduce fish-water oxygen solubility. Changing water temperature is *not* a substitute for proper biological management.

### Actual heat accounting, never perpetual-motion accounting

The present model uses `heat_capacity_j_per_centidegree` and `thermal_energy_j` as a deliberately simple **lumped simulation**. It does not model heat exchanger approach temperatures, stratification, pump electrical energy, thermoelectric conversion efficiency, pipe losses, transient flow, species-dependent temperatures, gas phase changes, or calibration.

For a simulated transfer `Q`:
- source `E_A_after = E_A_before - Q`
- destination `E_B_after = E_B_before + Q`
- `sum(E_after) == sum(E_before)`
- source temperature must initially exceed destination temperature
- equality gradient inversion is prohibited
- temperature and transfer limits must survive the proposed operation
- separate fluids require an approved *simulated* isolating exchanger

This is an intentionally **lossless** bookkeeping specimen, a conservative upper bound on what real heat moving hardware can do. It cannot be mistaken for measured performance. Real exchanger and piping losses would be characterized separately.

A bank that is warm but not hot enough for a desired consumer **cannot** heat that consumer passively. A heat pump could make that crossing by expending separately metered electricity; this simulator deliberately refuses it.

### Executable proof

```sh
python3 scripts/heat-commons.py inspect
python3 scripts/heat-commons.py evaluate
python3 scripts/heat-commons.py simulate
python3 -m unittest discover -s tests -p 'test_kettlenode_002.py' -v
```

The fixture tests a solar-fed sealed thermal bank at 50 C transferring a nominal 100,000 J to an isolated 22 C fish tank through the `hx-fish` proposal. Those temperatures and transfers are **fictional model values**. The simulated thermal balance is exact; no pipe, fish, water pump, power plant or sensor was touched.

Simulation world is immutable across the step; the result contains a new world and an unsigned receipt. Duplicate requests are rejected **inside this simulated world history**; this does not provide durable replay security across manipulated files, distinct process snapshots, or physical actuators.

### Proposed first bench hardware: TWO-WATER-BOTTLE THERMAL-CROSSING-001

First prove transfer, not an electrical miracle:

1. Use two appropriately rated, non-pressurized water reservoirs at modest different temperatures, insulated from mains electricity and biological systems.
2. Use an ordinary rated low-temperature external heat exchanger/coil appropriate for the media, a low-voltage approved circulation pump where required, calibrated temperature sensors, and optional volumetric flow measurement.
3. Keep the reservoirs distinct. Document startup mass/volume, temperature, sensor uncertainty, time and pumping energy.
4. Record source thermal loss versus destination gain and surroundings losses. A lower total heat capture is expected due to losses and uncertainty. Do not claim conservation measurement solely from two point temperature sensors.
5. Exercise no-flow, wrong exchanger, excess destination temperature, and unplugged-controller cases **with a non-living dummy load**.
6. Only after that, measure an approved heat-harvest device and separately meter the electricity powering a microcontroller. Genuine fish/aquaponics integration requires independent species-specific safety design and redundant life support.

No DIY sealed steam pressure vessels, improvised mains installations, open cooling towers, or connecting food systems to uncertified machine coolant.

## Integration boundary

`KETTLENODE-001` tracks *simulated source-reported electrical-energy allowance*. `KETTLENODE-002` separately models *thermal energy* and eligible destinations. **The units, evidence types, and claims may not be casually exchanged.** A future thermal-to-electrical converter organ would need independently measured input heat, output electricity, temperature gradient, conversion efficiency, heat rejection and load receipts.

reLATTE may carry exact evidence and disposition receipts; only reLATTE owners can sign crossings, and receiving nodes retain local authority. No signed crossing is produced here.

**Thermal possibility is not a command. Heat is not authority. Fish survival outranks computation.**
