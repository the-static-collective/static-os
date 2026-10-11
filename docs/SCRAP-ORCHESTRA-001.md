# SCRAP-ORCHESTRA-001 — The Field Lab We Already Own

**Date:** 2026-10-11
**Status:** inventory-driven preparation only. Model identities, power requirements, operating condition, RF frequencies, software support, and interoperability are NOT YET VERIFIED.
**Parent:** [FIELD-CELL-001](FIELD-CELL-001.md) / [STATIC-OS PR #88](https://github.com/the-static-collective/static-os/pull/88).
**Related:** [FIELD-PROCESSOR-001 PR #87](https://github.com/the-static-collective/static-os/pull/87), [planZ MasterServant PR #12](https://github.com/the-static-collective/planZ/pull/12).

## What the actual owner reports having

- A working multimeter (model/accuracy unreported).
- A soldering iron and substantial assorted salvaged electronics.
- Multiple old routers (model, firmware and power supply unknown).
- Old desktop PCs, including around-2012 equipment (boot status unknown).
- Approximately five or six laptops or laptop part sets (working-condition / battery status unknown).
- An old Bluetooth-capable CD player (exact capabilities unknown).
- Audio amplifiers, mixers and entertainment-center audio/video processors/receivers (individual ports/voltages unknown).
- Wireless doorbells (receiver power type, paired status and carrier frequency unknown).

**Do not silently transform "I have a laptop" into "a Linux server is installed" or "I have a router" into "an OpenWrt-capable mesh node."** All capabilities are provisional until physically inspected.

## First systems architecture (no repairs or purchases required)

~~~text
[Doorbell transmitter] ---normal unmodified RF---> [paired doorbell chime]
                                                         |
                                                       AIR
                                                         |
[Audio player or laptop A] ---- controlled test sound --> [Laptop B mic]
                                                         |
                               local-only recording with explicit participant consent
                                                         |
                                         original WAV / capture SHA256
                                                         |
                                        human classification and result
                                                         |
                             STATIC-OS read-only adapter (separate implementation)
                                                         |
                                          FIELD-SCORE / ROOMTONE HOLD

[Old router, if healthy and supported]
        Optional segregated *private* LAN for two inspected computers;
        no WAN, no port forwarding, no internet service requirement.

[Scrap soil/copper RC cell] ---- measured voltage over time ----> [CSV]
                                                             |
                                            Existing FIELD-CELL analyzer
~~~

**Core idea:** Start with two physically separated intact endpoints plus a real acoustic path before writing a network protocol or soldering into powered consumer equipment. The intact paired doorbell can already make a reproducible sensory event; the computer hears its chime through the air. This is a real *physical observation* if actually recorded, but it does not prove that the laptop decoded RF packets or identified the transmitting hardware.

## Four hardware roles

| Candidate class | Possible role | First safe observation | What must not be claimed |
| --- | --- | --- | --- |
| laptop/PC | STATIC brain, local archive, waveform editor and instrument host | Can boot, use local files, play sound and record WAV? | Installed STATIC-OS, real-time sensing or sensor calibration until earned |
| second PC/laptop | independent physical listener | Can record short sound emitted by first device in one room? | Independent observer if sharing the same input file/clock |
| old router | optional LAN switch/AP, isolated instrument transport | Exact make/model/revision, matching labelled supply, link LEDs with WAN disconnected | Secure OpenWrt compatibility, mesh ability, software-defined radio or safe public WAN |
| CD / Bluetooth / amplifier / mixer | audio source and controlled propagation/processing | Battery/labelled power, basic speaker/headphone-level output; microphone recording through air | Arbitrary digital data link, firmware hackability or safe direct audio-to-mic connection |
| entertainment AV receiver | existing audio DSP routing/equalization + signal effects | Labels reveal recognized line IN/OUT and speaker outputs | General-purpose programmable CPU or safe computer input from amplified speaker output |
| wireless doorbell pair | human-actuated physical event -> its normal chime -> listener | Test original paired set without altering circuitry | Known frequency, security/authentication, exact source RF decoding |
| small passive parts / copper | RC transfer, physical state and voltage data | Battery-removed inventory, verified resistor/capacitor polarity | Free energy, soil intelligence, safe mains or telecom connection |
| multimeter | physical evidence instrument | Known-good leads and DC-voltage test on the AA cells | High-speed oscilloscope, calibrated RF analyzer or data logger |

## Three no-shopping vertical slices

### 0 — AUDIO THROUGH ACTUAL AIR (recommended first)

**Hardware:** one working laptop with a speaker and microphone, preferably a second laptop or separate CD player/speaker as emitter. No soldering.

1. Identify an intact laptop whose microphone records in a normal local audio application.
2. Use a self-created, royalty-cleared short test tone/cue or short permitted audio excerpt; have a clear source file before physical playback.
3. First record *digital loopback* if available, separately classified as SOFTWARE_LOOPBACK. (Audacity supports this on Windows through WASAPI.)
4. Now play audibly through a physically separate speaker at a comfortable volume; record with a physically located microphone, locally and with every nearby person's consent. Classify this as HUMAN_CAPTURED_PHYSICAL_AUDIO, not independent verified sensor calibration.
5. Compare source and captured WAV durations, waveform, silence, clipping and peak. Save exact capture and source hashes. The air and room have now become a measured transfer condition.
6. Move furniture/cloth or change speaker-microphone spacing one declared way and compare. Do not infer unique room identity or a remote person's location from the difference.
7. Feed only self-owned redacted, local extraction results into a future read-only STATIC-OS instrument, never unconsented raw household recordings.

**Pass:** two recordings are independently distinguishable from digital loopback and each has declared physical capture conditions. **Fail honestly:** no mic, mismatched devices, clipping, high background speech, indistinguishable results, uncertain timing.

### 1 — THE BELL TALKS TO THE ROOM

**Hardware:** a working *matched* wireless doorbell transmitter and its intact receiver/chime; one laptop microphone.

1. Inspect whether the receiver uses batteries or plugs into mains. **Do not open a mains-connected receiver** or probe its internal PCB.
2. Run normal manufacturer-intended button press -> original receiver rings. No RF modification or replay.
3. With permission, capture three short known button-press events and three quiet non-event windows using the laptop mic. Record false positives, missed events and environmental noise.
4. A software detector may later propose "chime-like event observed" with known uncertainty. It must not claim an authenticated visitor, the identity of a transmitter, a door opening, physical proximity, or RF packet reception.
5. Keep the chime event entirely local unless the participant intentionally shares a reduced event label.

**Pass:** a person can recreate chime response under test without changing the proprietary receiver. **RF-frequency determination/firmware programming are *not* prerequisites.**

### 2 — TWO COMPUTER BODIES, ONE PRIVATE ROAD

**Hardware:** two verified low-risk computers, one intact compatible router **or one direct Ethernet cable if supported**, correct labelled power supplies.

1. Photograph exact make/model/hardware revision and external power ratings before power. Inspect capacitors, cable insulation, corrosion and laptop battery swelling *without opening any mains supply*.
2. Isolate the router physically from WAN/modem/uplink. No public guest SSID, default open Wi-Fi, port-forwarding or internet-facing services. If firmware is obsolete and insecure, keep testing offline and restrict the LAN to the operator.
3. Attempt file transfer of a **non-sensitive test artifact** through a normal Ethernet LAN. Hash contents on both endpoints. Network transport proves delivery, not human/source authority.
4. For OpenWrt, decide compatibility only after exact device/revision and supported firmware/image are verified using reliable model-specific information. No guessed flashing, JTAG, UART levels or soldered serial ports.
5. Later compose receiver/HOLD semantics via the reLATTE road instead of conflating receipt with permission.

**Pass:** same test bytes locally received on a physically separate machine with separately recorded event information. **Not proof:** mesh internet, public site, remote authenticated identity or RF spectrum sensing.

## Salvage "body passport" — one card per device

Use [SCRAP-BODY-PASSPORT.md](SCRAP-BODY-PASSPORT.md).

Required before powering or changing anything:
- **S###** pseudonymous item ID; category; exact visible brand/model/hardware revision if known.
- Condition: unknown / visually inspected / manufacturer-spec-power / boots safely / repeatable operation / failed.
- Power: battery type, supply label voltage, AC/DC, polarity, rated current and matching original adapter when possible; never guess a connector voltage.
- Available interfaces: ethernet/Wi-Fi/Bluetooth/CD/line-level audio/speaker/microphone/USB/serial only where observable.
- Safety red flags: swelling battery, exposed AC mains, compromised insulation, liquid ingress, suspicious heat/smell, unknown high-voltage capacitors, broken cable.
- Evidence: optional close-up photo of external label and port panel **without serial number, account info, visible home details or other personal data**.
- Candidate new instrument role and one safe independently falsifiable test.
- Exit path: STOP, PARTS-ONLY (only after validated safe), DONOR, MEASUREMENT-WITNESS, CANDIDATE, or ACTIVE with explicit human classification.

No automatic dismantling, forced software updates, firmware flashing, battery disassembly or old-media destruction. Back up personal files before repurposing a PC. Keep old unpatched systems off the internet until security has been assessed.

## Priority inventory, in order

A. One laptop that boots and can play and capture audio.
B. One other intact audio emitter (second laptop, CD player, receiver) with its safe matched power supply.
C. One matched wireless doorbell pair, receiver power type identified.
D. Router external make/model/revision photographs; firmware decision later.
E. The resistors/capacitor/AA holder/copper for the already-prepared soil RC test.

## Critical refusals

- **Speaker outputs are not line outputs.** Never connect an amplifier/receiver speaker output directly to a laptop mic or line input. Powered speaker outputs can destroy audio inputs and potentially injure people.
- **Unknown device power is unsafe power.** A barrel connector looking correct does not establish voltage, polarity or current adequacy.
- **Wireless doorbell receiver may contain mains voltage.** Leave enclosed and use normally until exact hardware verified. No internal probing.
- **Laptop batteries and power supplies may be damaged.** Avoid swelling, punctures, opening power bricks and unprotected lithium cell salvage.
- **Wi-Fi and RF != arbitrary SDR.** Routers' radios do not generally decode all signals in arbitrary bands without hardware/driver support. A doorbell chime is an *acoustic proxy*, not a verified RF decode.
- **Roomtone matching is consent-driven.** Record only during deliberate bounded local tests; do not build a passive household listening network.
- **No connection to mains, household telephone pairs, utility earth, HV Tesla parts, or large charged amplifier capacitors.**

## Exact first earned claim

> One intact salvaged machine generates a declared audio stimulus; a second intact receiver or laptop observes it in the physical room; their original and captured bytes remain distinct and hash attributable; changing one physical condition alters an observed property without creating a machine command.

This is the first bridge from **room tone as an address** to **matter as measurable transfer**. It is earnable with *existing equipment*, even without soldering.

Next: identify exact hardware, then decide whether the sound path, doorbell chime, isolated private router LAN or AA/copper soil RC fixture gives the cleanest physical measurement.
