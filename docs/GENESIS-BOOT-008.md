# GENESIS 008 — Universal Cartridge × Museum × Town OS × Arcade × Festival

**Working question:** Can incompatible devices make useful, inspectable offers to one another without becoming one machine, one account system, one authority or one imaginary field success?

This branch turns five interrelated ideas into **executable, source-controlled experiments**, stacked on original GameCube/DS/ESP32/Android/Pi/old-laptop/Wii ports in STATIC OS. The output is not a physical completed festival, a verified human contribution, or a finished cross-media protocol in real acoustic conditions. Existing CANNON original-code execution remains owned by CANNON.

## The universal cartridge is intentionally smaller than its host

`cartridges/genesis008.py` is a Python3-standard-library **content-addressed, strict schema and text codec**. Every `static-os.genesis-cartridge/v1` record has one of exactly five verbs:

| Kind | What the record actually means | What it must never imply |
| --- | --- | --- |
| **ASK** | One fixed public-safe mission question | Human permission to act |
| **OFFER** | An unaccepted fictional offer candidate | Inventory exists or changed hands |
| **PROPOSE** | A bounded proposed gathering | Permission, zoning or site stewardship |
| **WITNESS** | An **unverified claim recorded in a software demonstration** | Independent real-world witnessing or delivery |
| **REPLICATE** | Invitation to reproduce a method | Replication was performed, or original participant approved |

A record carries its exact source-device *claim*, a digest over canonical bytes, parent digests for lineage, an enforced `PUBLIC_SAFE_ONLY` scope and false permission/physical/witness/delivery flags. **Content-addressing is only integrity and relative ordering, not a cryptographic signature or authentic device identity.** An actual independently witnessed result belongs in a future separate protocol with human consent and externally held evidence; this prototype cannot accidentally declare one.

Transport does not change what a record means:

- **Text / SD / USB:** `GC1:` followed by bounded URL-safe base64 of canonical compressed JSON. No network necessary. The original GameCube/Wii/DS/ESP32 port's fixed SD/UART proposal is converted to a universal **ASK**, but no arbitrary code is executed from the file.
- **Paper:** a local printable HTML card with a human-readable digest and encoded text carrier. Printed links work without a web server.
- **QR:** an optional real QR SVG produced by the openly installable `segno` build helper. **The SVG is generated code, not an identification claim**; actual scanner interoperability still requires testing.
- **Audio / possible cassette:** `cartridges/audio.py` implements and strictly round-trip decodes an actual WAV/FSK file: mono 16 kHz, 250 baud, 1000/2000 Hz symbols, sync + length + CRC-32. The checksum catches accidental corruption, not malicious alteration. **No loudspeaker-to-microphone, cassette, radio, fax or noisy-room acoustic roundtrip has been tested.** An ordinary WAV digital roundtrip is useful software proof, not an acoustic transport claim.
- **Fax / dot-matrix / rotary phone:** explicitly present as **future** archaeology candidates in a manually maintained registry, **not implemented or verified ports**.

## 1. The arcade that makes useful proposals

Run:

```sh
# From a checkout containing this experiment; Python 3.11, no cloud or account:
python3 scripts/genesis008.py demo \
  --focus "Festival Table" --out-dir new-genesis008-festival

# Optional build-time SVG QR helper (not needed for normal operation):
python3 -m pip install 'segno==1.6.6'
python3 scripts/genesis008.py demo \
  --focus "Community Food" --out-dir other-new-festival --qr
```

This creates a **new, create-only** local directory with an offline `festival.html` of five proposed stations; five digest-checked `*.gc1` files; five actual FSK `*.wav` audio data files; `cartridges.json`; `chain-replay.json`; a printable `museum.html`; `station-plan.json`; and a `replication-blueprint-candidate.json`. When `--qr` is supplied it also creates a real `ask.svg` QR. Everything works without any actual device, person, venue or network.

This is the experiment loop:

```
01 GameCube/Wii question (ASK)
          |
02 DS/Android unaccepted fictional offer (OFFER)
          |
03 ESP32/laptop bounded site-permission-gated idea (PROPOSE)
          |
04 CANNON-class computational proposal receipt (WITNESS: held claim!)
          |
05 Printer/human proposal for another gathering (REPLICATE)
          |
      Back to 01 with a NEW human question,
      NOT an automatically authorized real festival
```

The generated five-station festival is intentionally **fictional**. It retains `MISSING` site permission and steward permission, `NOT_OBSERVED` devices and 0 real participants, even when the pipeline runs successfully. Each person must independently opt into any real invitation, task or photography. The original CANNON/Full Measure/GrO/PENNY/reLATTE custody and admission boundaries remain intact; a string in a universal cartridge cannot supersede them.

## 2. The town is the operating system

The second artifact is a **field-ready proposal workflow**, not a software authority centralizer:

```
People own their interests and their right to refuse
          ↓
Church / community room / park steward approves venue independently
          ↓
Small machines make only human-readable PUBLIC_SAFE suggestions
          ↓
Local CANNON reads exact independently owned source histories
          ↓
Original project stewards authorize real work outside this demo
          ↓
Independent witnesses retain genuine physical evidence separately
          ↓
The community can propose a new gathering or copy a reviewed method
```

The resulting `replication-blueprint-candidate.json` is honest about the missing external work: no site, no named steward, no budget, no permission, no real helpers or field observations. Its checklist specifies separately obtaining site permission; offering accessible opt-in participation; considering safe power, storage, transport and weather; keeping and checking real source-aware receipts; and reviewing failures before another event.

A potential progression is **small local pop-up → voluntary community table or worship/music gathering → larger collaborative festival**. These are candidate formats; no Courthouse Park/Harmony Park permission or commitment is presumed.

## 3. The museum of unfinished futures

`cartridges/organ-registry.json` is a manually maintained archaeology ledger with eleven potential organs: Wii, GameCube, Nintendo DS, ESP32, Android, Raspberry Pi, old laptop, fax, cassette, dot-matrix printer and rotary telephone. It marks existing software compilations/tests separately from **physical `UNTESTED`**. It does not run unauthorized port scans or inspect personal devices.

Device intake must eventually collect:
- Device owner's permission and volunteer conditions.
- Hardware condition, safe original power supply and available connections.
- Which local interfaces actually function and what output has been observed.
- A reproducible build or repair method and the name of the *person* who independently tried it.
- Unresolved failures, safety constraints and any licensing/distribution questions.

One new independently observed ability may be copied as a proposed blueprint only after real consent and evidence. A downloaded example is not an independently verified machine.

## 4. Cross from an original strange console to the real CANNON software

The new protocol can genuinely cross **the older device-specific source files** using the original validators:

```sh
# GameCube/DS/ESP32/Android/Pi/legacy source-owned JSON:
python3 scripts/genesis008.py import-legacy \
  --input old-gamecube-intent.json --out portable.gc1

# Same for a Wii intent from the independently open Wii PR.
# Inspect the new digest-bearing cartridge WITHOUT executing code:
python3 scripts/genesis008.py bridge --text portable.gc1 --validate
python3 scripts/genesis008.py inspect --text portable.gc1

# A distinct human approval step runs the original pinned CANNON program.
# These six folders must be your exact original Git checkouts, not arbitrary URLs:
python3 scripts/genesis008.py bridge --text portable.gc1 --execute \
  --cannon cannon --staticos staticos --webz webz \
  --gro gro --ghot ghot --jarvis jarvis --out new-output-dir

# CANNON independently checks original Git objects and exact bytes:
node cannon/scripts/genesis-boot.mjs verify \
  --staticos staticos --webz webz --gro gro \
  --ghot ghot --jarvis jarvis --out new-output-dir
```

The bridge **will reject** a synthetic festival `ASK` that pretends to be a real machine, non-`ASK` cartridges, invented fields, forged witness flags, unknown or mutable source versions, missing independently owned code and overwritten output folders. It uses the original `wii-to-cannon.py` or `portable-to-cannon.py` as needed rather than introducing a second incompatible source authority.

The CANNON output is **actual software-generated Living House A/B + other synthetic work-card receipts**, not an actual house, delivery or hospital/shelter/municipal action.

## Verification receipts

`.github/workflows/genesis-boot-008.yml` has two separate proof gates:

**Universal codec/arcade:** unit tests for every source × four focus questions × five verbs, refusal of manufactured witnessing and authority, actual printed museum/festival output, verified deterministic parent-child lineage, digital-FSK WAV roundtrip and malformed-audio refusal, old-Wii/portable-schema import, and generation of an actual QR SVG as a build-time optional renderer. Uploaded artifact: `genesis008-universal-cartridges-museum-festival-qr-wav`.

**Original CANNON:** check out the original CANNON #38 SHA (plus five original donor SHA pins), create a Wii and GameCube format question, convert each to a universal cartridge, independently validate with zero execution, then *explicitly* execute each through the original CANNON GENESIS BOOT 001 runner and cold-replay every result. The test rejects corrupted encoded text and asserts zero real witnesses, zero real actions and distinct scenario outputs. Uploaded artifact: `genesis008-real-original-cannon-wii-gamecube-crossings`.

**This is an executable architecture test, not public deployment or the completion of a festival.** Where a future participant or organization is needed, the correct status stays HOLD.

## Tiny, clear law

**A cartridge can carry a question across incompatible machines. It cannot carry somebody else's consent, authenticated identity, physical testimony or authority.**

If somebody actually makes something work, and an independent person verifies it with meaningful evidence and permission, *that* can eventually become a candidate reusable blueprint in an owner-controlled system such as Full Measure/GRAFT/GrO. Until then, it is an invitation to try—not a success report.

## Next physical gates

One owned GameCube/DS/Wii/ESP32 with verified safe original accessories; one separate CANNON-capable computer; one manual SD/serial handoff; one actual controller-originated fixed question; and a correctly reproduced, non-escalated software artifact. Only afterward: scan a real QR with an independent app, record/play an actual WAV across hardware (or cassette), test a real printer, request a real volunteer steward and permission for a tiny reversible public table. **No real person is signed up or venue reserved by this proposal.**
