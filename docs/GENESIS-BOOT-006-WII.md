# GENESIS BOOT 006 — yes, an actual Nintendo Wii can become a Suitcase *front door*

The Nintendo Wii is a **PowerPC console with only 88 MB total RAM**, not an ordinary Node24 computer. We therefore **do not** pretend our existing x86_64 Linux ISO or six-repo Node/Python runtime boots directly on its original hardware. Instead, we use devkitPro's real Wii toolchain to compile an independent **PowerPC Homebrew Channel DOL application**. The original Wii can ask the same human-first GENESIS question, accept the actual Wii Remote buttons, and write an inert, public-safe intent to an SD card.

The user can physically carry that file to a separate, independently controlled computer running the original source-pinned CANNON GENESIS software. No Wii Wi-Fi or remote service, cloud account, Homebrew Channel modification, Nintendo NAND write, house actuation, identity claim or synthetic witness elevation is involved.

## On the Wii

1. Load `apps/static-genesis/boot.dol` (and `meta.xml`) from an SD card into an already configured Homebrew Channel. Modifying Wii firmware or bypassing a console's normal security is **not** part of this project or an automated step.
2. The screen says **HELLO, WORLD. WHAT SHALL WE BUILD TOGETHER?**
3. Use Wii Remote **UP/DOWN** to choose one of four public-safe questions: Living House, Community Food, Festival Table, Repair Lab. The base software target stays Living House; these are four *focus questions*, not four implemented community systems.
4. Press **A** to approve exporting a proposed question. Press **B** to cancel and **HOME** to exit. Press **PLUS** to write a JSON file only after explicit approval.
5. The app creates `sd:/static-genesis/intent-001.json`, or another unused numbered file, without overwriting existing files. It refuses if SD is unavailable or all 999 proposal filenames are taken. No Wi-Fi, cloud, service, account, microphone, real-person information or arbitrary question input.
6. That JSON has `status=PROPOSAL_ONLY_NOT_EXECUTED`, `transmitted=false`, `signed=false`, `physical_observation=false`, `independent_witness=false`. It is **not** a signature, a human witness, field observation or house building result.

## Cross from Wii SD to original CANNON, manually

Copy the JSON to a separate trusted computer with Node24, Python3 and **the six exact original source checkouts** pinned in `manifest/genesis-boot-003.json` (CANNON, STATIC OS, webZ, GrO, GHoT, JAR;VIS). No network is necessary to run after those sources are staged.

```sh
# check the SD proposal without taking any action:
python3 static-os/scripts/wii-to-cannon.py \
  --intent intent-001.json --validate

# deliberately run the ORIGINAL CANNON branch-native software:
python3 static-os/scripts/wii-to-cannon.py \
  --intent intent-001.json --execute \
  --cannon cannon --staticos staticos --webz webz --gro gro \
  --ghot ghot --jarvis jarvis --out wii-native-output

# independently cold-verify the result from CANNON's exact original code:
node cannon/scripts/genesis-boot.mjs verify \
  --staticos staticos --webz webz --gro gro \
  --ghot ghot --jarvis jarvis --out wii-native-output
```

The importer accepts an **exact, immutable, small schema with only four authorized question strings**. It refuses added fields, higher authority, false witnesses, edited claims, Git source drift, and outputs that already exist. It never executes or evaluates text from the SD; only the operator's separate explicit `--execute` flag runs the fixed original code.

### Build the actual Wii executable

```sh
docker run --rm -v "$PWD:/work" -w /work/ports/wii \
  devkitpro/devkitppc:20261016 make
```

This builds `ports/wii/boot.elf` (big-endian PowerPC), then `ports/wii/boot.dol` suitable for Wii Homebrew Channel. The workflow packages `apps/static-genesis/boot.dol` and `meta.xml` into a ready-to-copy archive, plus an actual SHA-256 and original source-bridge receipts. devkitPro is the official community PowerPC/Wii toolchain; it is independent of Debian, Alpine and Fedora runtimes. The compiler's Docker image may happen to use Linux internally as a *build host*, but the resulting Wii DOL is **a standalone PowerPC Wii native program**, not a container and not Wii-Linux.

### Proof gates

- **Native PowerPC build:** official devkitPro compiles a real ELF/DOL. CI inspects ELF `e_machine=20` and big-endian architecture, and uploads the DOL. This does not prove successful execution on a physical Wii.
- **Offline intent crossing:** separately constructed public-safe Wii SD fixture passes importer validation, is executed only with explicit `--execute`, results in actual native original CANNON House A/B output and independent cold verification, and rejects tampered witnesses.
- **Still unverified:** real Wii/GC controller observation, Wii console screen or SD write, physical device boot via Homebrew Channel, actual human approval, actual house sensors, separately keyed independent peers, actual material circulation, reLATTE wire compatibility, or original CANNON JS/Python running **on the Wii itself**.

The Wii homebrew port is a deliberately tiny native **human interface and source-owned proposal writer**. A Raspberry Pi or laptop remains the CANNON execution node, and the SD card is the air-gapped voluntary crossing. These can be physically co-located but retain independent operational permissions.

### Why this is useful rather than just cute

If this works as a real console UI, the same low-power, independently reviewed protocol could be ported to even stranger machines: GameCube, microcontrollers, old laptops, handhelds and standalone low-power community terminals. Tiny devices need not run every donor repository to participate honestly: they can ask one question, record one proposed act and preserve the operator's freedom to refuse. Their code must not claim evidence it cannot observe.

**MAIN != CANON · NATIVE WII PROGRAM != NODE24 ON WII · SD FILE != EXECUTION AUTHORITY · NO REAL FIELD WITNESS**
