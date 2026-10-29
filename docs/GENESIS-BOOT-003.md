# GENESIS BOOT 003 — put the real first-boot conversation inside a Debian Live ISO

**Purpose:** A read-only-root Debian **Live** amd64 image containing the original experimental CANNON first-boot console, all pinned original source histories it executes, an independently controlled user's local loopback service and a human-facing XFCE/Firefox session. This extends STATIC OS SUITCASE GENESIS #91 on its own branch rather than merging project experiments into `main`.

**Do not claim an installed OS or real-world house.** An ISO *file* is not a booted VM, a VM is not a tested physical Suitcase, and a successful synthetic software test does not verify an actual solar panel, partner, independent human witness, real-world material transformation or physical actuation.

## The live boot path

```text
BIOS/UEFI -> Debian Live kernel -> live desktop user -> XFCE session
                                                  |
                                                  v
                             static-genesis.desktop (no privileged installer)
                                                  |
                                             user systemd service
                                                  |
                                      127.0.0.1:8766 only / no auto run
                                                  |
                             FIRST BOOT: Hello, world.
                                        What shall we build together?
                                      /           |            \
                                   Explore      Build        Witness
                                                  |
                                             CANNON pinned
                                             original sources
                                           /                  \
                                    HOUSE-SEED A/B     Warm Thread (opt-in)
                                     five donors       additional owner roots
                                           \                  /
                                        offline actual
                                     source-native receipts
```

The page itself is inert until the operator deliberately clicks. It doesn't install packages, make network calls, open microphones, create keys, contact organizations or operate any actuator. A sourced plan remains `HOLD`. HOUSE/Workbench survives as an independent manual organ; GENESIS becomes the preferred first browser. Boot-time packages and frozen donor Git objects come from the image, not the internet.

### What this ISO actually bundles

- Debian bookworm live XFCE, Firefox ESR and Workbench's original exact Git source (as in GENESIS 001).
- Node **v24.10.0**, downloaded and checked against its explicitly reviewed official release SHA-256 (the tarball is downloaded *during image build*).
- An explicit **11-source checkout matrix** pinned in `manifest/genesis-boot-003.json`: CANNON #41 first boot; STATIC OS #91 HOUSE-SEED; WebZ HARMONY; GrO unmerged Mattercraft; GHoT Commons; JAR;VIS; plus original CANNON STACK² 027 runner, GHoT Warm Thread, Full Measure, Band Runtime and BananaSpork Garden original source checkouts.
- Git objects and source worktrees to permit **offline exact Git-object integrity checks** at each reviewed invocation. The original checkout origins are recorded as local config, not remote owner authentication or license grant.
- Garden's lockfile-resolved TypeScript runner, installed with lifecycle scripts disabled during **build**, not at boot.
- `static-genesis.service` starts only in the logged-in user's session and is sandboxed as a non-root user. `static-genesis-launch` opens its loopback page, not a public network service. Per-run results reside in `~/.local/state/static-genesis/runs` and are not persistent across ISO reboots unless a separately verified persistence mechanism is later added.

## Build and test, strictly away from your daily computer

**Never run the root image builder on a personal daily-use OS or an attached storage drive you cannot risk.** Use a disposable Debian bookworm amd64 build VM with enough capacity (rough planning allocation: tens of GB scratch disk and several GB RAM; actual measurements must be collected). The first reproducible software build is attempted in a hosted GitHub Actions Ubuntu runner, using Debian live-build/debootstrap and root only in the disposable runner. No OS image or installer is written to a physical disk by the recipe.

```sh
# from an isolated builder VM with live-build, debootstrap, squashfs-tools,
# xorriso, curl, git, python3, xz and network access installed
python3 scripts/validate-manifest.py manifest/genesis-001.json
python3 scripts/validate-boot-image.py manifest/genesis-boot-003.json
python3 -m unittest discover -s tests -v
sudo bash scripts/build-genesis-boot-iso.sh
```

The build refuses to overwrite an existing `.build/genesis-boot-003` directory. The image will be `*.iso` with `image.sha256` and `image-build-receipt.json`; that receipt deliberately says `IMAGE_BUILT_NOT_BOOT_CONFIRMED` even if the file exists. The Node tarball SHA is pinned but Debian apt package closure and Workbench's Python package wheel closure are **not** globally pinned. This is not yet a bit-identical reproducible supply chain.

### Independent VM boot execution

`.github/workflows/genesis-boot-003.yml` has an independent contract job and a heavy **real ISO build** job. The latter stages an explicitly marked **CI-only** serial boot probe into its candidate image. QEMU boots that actual ISO under emulated BIOS without a hard drive. The probe waits for the original source-native first-boot server to answer on guest loopback, then explicitly executes the A/B Living House and Warm Thread through the guest's local HTTP API, separately invokes cold verification, and writes serial markers only if the original programs returned acceptable results. The CI script checks the actual serial proof markers, an exact ISO SHA, and uploads the image and logs.

**Precisely what a green BIOS job proves:** An ISO was built, QEMU reached the booted guest's multi-user service, Node ran from the image, the actual first-boot server started without internet and executed both original-code synthetic crossings, the internal plan/receipt replay succeeded, and a source-linked artifact bundle exists.

**What it doesn't prove:** UEFI boot (separate trial), actual interactive Firefox/XFCE display (manual graphical VM gate), physical hardware compatibility, image-to-removable-media recording, installed or durable cross-boot state, owner-selected canon, a real organizational relationship, live speech, accurate energy capture, house construction, or a separate witnessed physical event. The CI ISO includes a diagnostic service not shipped by normal `sudo bash scripts/build-genesis-boot-iso.sh`; use a normally built image for any subsequent manual pilot.

A separate graphical QEMU run should inspect the literal XFCE page (not just the serial marker) and verify Firefox opens `http://127.0.0.1:8766/` without internet, that the service is non-root, and that user-generated plans survive a **service** restart. No automatic hard-drive installation is included.

## Operator controls and safety

- The default app binds to **127.0.0.1:8766** and requires explicit user approval to execute bounded local donor code. No LAN binding, auto-issued keys, silent partner enrollment or direct building controls.
- The root image build is a trusted-code supply operation; review code, package licenses and downstream usage before any external distribution. Git source pins do not authenticate humans or copyrights.
- This prototype uses HTTP on guest loopback and records the public-safe question in the operator's user-state folder. Don't put personal case documents, household addresses or secrets into its input.
- A failed network/build/source check should **HOLD** and leave already created receipts alone. A malicious or incompatible donor branch is not automatically retried on the next commit.
- GENESIS's **BUILD** is a plan and work-card generator. Its fictional A and B are not two independently acting stewards. Optional Warm Thread preserved an intentionally simulated refusal and an outstanding fictional transport load.
- Before trying physical hardware, confirm a complete BIOS/UEFI VM boot, graphical start, clean shutdown, recovery mechanism, full disk/device inventory and written permissions. Treat lithium batteries, mains electricity, roof and road surfaces as separately qualified work—not actions for JAR;VIS.

## Relationship to independently open PRs

**STATIC OS PR #91** owns the original HOUSE-SEED. **CANNON PR #38** owns the initial six-repo first boot. **CANNON PR #41** owns the interactive and extra source-native Warm Thread lane. This branch combines them **as immutable source dependencies**, without merging those PRs or claiming one branch becomes operational canon for every owner.

The machine's guiding first question remains:

> **Hello, world. What shall we build together?**

The intended result is a **real on-boot conversation whose first act is to help a human decide what is worth building**, not a live AI entrusted with autonomous control of physical society.
