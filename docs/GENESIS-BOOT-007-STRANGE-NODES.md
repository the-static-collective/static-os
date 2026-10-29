# GENESIS BOOT 007 — six strange devices, one original CANNON

**A console doesn't have to be a computer powerful enough to run the whole world. It can be a doorway into a shared experiment.**

This draft is stacked on [Wii GENESIS BOOT 006](https://github.com/the-static-collective/static-os/pull/95) and keeps **all original experiments on their own Git histories**. It adds actual source ports for Nintendo GameCube, Nintendo DS, original ESP32, Android through Termux, Raspberry Pi, and Python3-capable old Linux laptops.

## Two classes of computer: front doors and executing organs

| Device | Native mechanism | What executes there | Export/crossing |
|---|---|---|---|
| GameCube | devkitPPC + libogc `.dol` | Controller-selected proposal, public-safe text | Compatible external FAT/SD storage adapter **required**, unverified on physical console |
| Nintendo DS | devkitARM + libnds `.nds` | Handheld console-selected proposal | DLDI-compatible FAT cartridge/adapter **required**, unverified on DS |
| Original ESP32 | ESP-IDF native Xtensa firmware | UART0 selection, approval, one printable JSON | USB serial manually captured to a file; *no radio enabled* |
| Android Termux | Python3 interactive terminal | Same human-first text dialogue and create-only JSON | Android local app directory; no root, account, permissions or radio/network calls |
| Raspberry Pi | Python3 fallback or full Linux ARM64 Node24+CANNON | Lightweight prompt **or** exact original 11-root first boot | Local JSON for light mode, source-native plans/receipts in full mode |
| Old laptop | Plain Python3 (including systems that cannot run Node24) | Same text dialogue and create-only JSON | Operator transfers to independent Node24 CANNON machine |

**Physical execution claims are independent.** The GameCube, DS and ESP32 cross-compilers can produce real device-native files without a device being present, and the Pi-class ARM64 CI runner is an ARM64 Linux machine, not an actual Raspberry Pi board. None of these claims to have seen a physical human, an installed building, a registered organization or an actual sensor.

### The smallest possible shared object

`ports/common/genesis_intent.h` creates the exact `static-os.portable-first-boot-intent/v1` format for three completely different native C devices. `scripts/portable-to-cannon.py` independently validates that exact schema before presenting the user with an optional separate **explicit** `--execute` step.

The schema accepts only four fixed public-safe questions (Living House, Community Food, Festival Table, Repair Lab). All of them currently request a **fictional Living House A/B software planning run** with different focus text; these are not four implemented field services.

The file expressly says `network_transmitted=false`, `signed=false`, `independent_witness=false`, `physical_observation=false`, `status=PROPOSAL_ONLY_NOT_EXECUTED`. It is a local input **not a signature, authorization, physical sensor reading or payment receipt**. A real validator rejects changing any of those flags or adding arbitrary code. Receiving original CANNON independently validates its exact original Git source hashes before executing work. Nothing installs, contacts someone, or activates hardware automatically from the intent.

## Actual native builds

**GameCube** — uses devkitPPC `gamecube_rules`, pads and libfat; produces `ports/gamecube/boot.dol`, a real GameCube executable, not a Wii DOL. D-Pad chooses; A approves file export; X exports to a compatible inserted external SD storage adapter; B cancels; START exits. The original GameCube has no built-in SD slot; **do not claim SD export works without a supported adapter**. Launching GameCube homebrew is the owner's separate responsibility; this project does not modify a console's firmware.

**Nintendo DS** — uses devkitARM `ds_rules`, libnds and libfat; produces `ports/nds/genesis.nds`. D-Pad/A/X/B/START replicate the approval model. DLDI flashcart support is a hardware prerequisite that requires independent physical testing. No Wi-Fi.

**ESP32** — uses the official `espressif/idf:v5.5.6` builder for the **original ESP32** target, produces `ports/esp32/build/static_genesis_esp32.bin`. A USB-UART serial terminal sends numbers 1-4, then A, then X to print a JSON envelope bracketed by begin/end markers. Nothing is automatically transmitted over Wi-Fi/Bluetooth, flashed to other devices or driven via GPIO. Flashing the firmware onto a *personally owned development board* is a separate explicit operator step; no physical electronics wiring instructions or real sensor experiments are part of this draft.

### Android, old laptop, or lightweight Raspberry Pi

No privileged installs or cloud dependency are required to run this proposal-only application. The user supplies an **already existing** output folder. It never installs Python, modifies accounts or puts files into someone else's space.

```sh
# From a clone of static-os containing this branch:
mkdir -p "$HOME/genesis-inbox"

# Any Linux laptop with Python3:
sh ports/legacy-linux/genesis.sh "$HOME/genesis-inbox"

# Termux on Android, with Python3 already available:
sh ports/android/genesis-termux.sh "$HOME/genesis-inbox"

# Raspberry Pi with Python3:
sh ports/raspberry-pi/genesis-pi.sh proposal "$HOME/genesis-inbox"
```

Each asks the operator to select a fixed question and type **EXPORT**; it writes only a new 0600-mode numbered `intent-###.json`, without overwriting an older one. To run full CANNON on **ARM64 Raspberry Pi Linux** (not older 32-bit Pis), separately stage the eleven exact reviewed original source checkouts under one directory, install Node24/Python3 from a chosen vetted source, ensure Garden's reviewed TypeScript runtime is already installed, and use:

```sh
export GENESIS_NATIVE_ROOTS=/path/to/your/11-pinned-checkouts
sh ports/raspberry-pi/genesis-pi.sh full "$HOME/genesis-inbox"
```

This reuses the actual CANNON localhost interface and refuses missing checkout roots. **This does not bypass the original CANNON program's own exact Git object/source checks.**

### Carry a portable intent to CANNON

On a trusted computer with Node24 and the *six* original source-owned checkouts pinned by GENESIS BOOT 001, copy an emitted JSON **manually**:

```sh
python3 static-os/scripts/portable-to-cannon.py \
  --intent intent-001.json --validate

python3 static-os/scripts/portable-to-cannon.py \
  --intent intent-001.json --execute \
  --cannon cannon --staticos staticos --webz webz --gro gro \
  --ghot ghot --jarvis jarvis --out genesis-device-result

node cannon/scripts/genesis-boot.mjs verify \
  --staticos staticos --webz webz --gro gro \
  --ghot ghot --jarvis jarvis --out genesis-device-result
```

The importer refuses unknown source devices, authority escalation, private user-supplied strings, arbitrary scripts, unpinned CANNON source, and overwriting an existing result. The outcome is an **actual original source-native software planning artifact** with a fictional house A/B, not actual field construction.

## Verification ladder

The [GENESIS BOOT 007 CI workflow](../.github/workflows/genesis-boot-007-strange-nodes.yml) contains independent native build jobs:
- Compile the original shared native C-format generator and validate all 12 GameCube/DS/ESP32 question variants using original Python importer; test Termux/old laptop/Pi CLI approval/cancel, including a file-only run.
- Compile real GameCube PowerPC ELF/DOL using devkitPro.
- Compile real Nintendo DS ARM9/ARM7 .nds using devkitPro.
- Compile real ESP32 firmware using Espressif official IDF SDK.
- Build original CANNON on **native Linux ARM64** using the verified Alpine ARM64 userland, execute independent original code offline and attach an ARM64 OCI bundle. Not Pi board testing.
- Present GameCube/DS/ESP32 native-C-equivalent exported requests to the portable bridge, then **explicitly execute** the GameCube request through exact-source CANNON and independently cold verify the results.

CI success demonstrates buildability and software crossing only. **Only a real console, ESP32 or Pi hardware trial could establish the next physical-device gate.** We have not performed such a trial.

The ports deliberately illustrate the design law: **every device can be useful without inheriting authority over any other device.**

> A GameCube asks a question. A Nintendo DS carries it. An ESP32 can record a proposed experiment. An old laptop can help compose. A Raspberry Pi can run the whole reviewed software path. CANNON preserves what was actually demonstrated.
