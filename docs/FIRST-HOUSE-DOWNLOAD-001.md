# FIRST-HOUSE-DOWNLOAD-001 — a bounded desktop entry candidate

This **draft** adds a First House mode to the existing STATIC OS desktop-installer
branch. It is an ordinary Linux application for an existing OS, **not** a
bootable STATIC OS, a Full Measure world runtime, a signed release or a tested
install on the receiving machine.

## What this particular package includes

The desktop-only `packaging/desktop/first-house.json` pins the exact current
Workbench main source containing **merged** STATIC ARG First Door, illustrated
House and the persistent four-room World Entry. It is **not** the distinct,
draft whole-house Workbench integration in PR #65. Its source pin is separate
from `manifest/genesis-001.json`, `interop/triad-001.json` and
`interop/flight-003.json`: the package does not imply that the pinned
Workbench main contains the experimental manual ELF carrier. Do not replace
those ISO/ELF pins with this desktop-only source.

The packaged executable is configured to start at the existing `/arg`
First Door, and its existing **Back to Workbench** link opens the full desk.
The user explicitly opts into the ARG and enters their own three Seeds,
one Machine and one World. The resulting local World can be entered and
revisited after restart. No fictional sample World is silently inserted;
no external game, project repository or model service is downloaded on launch.
No cross-project game admission is implied.

## Candidate build, not an available public download

On Ubuntu 22.04 amd64 with Python 3.11+, git, dpkg-deb and network access
**on the builder**, run:

```bash
python3 scripts/validate-first-house.py packaging/desktop/first-house.json
bash scripts/build-desktop-deb.sh --first-house
```

The frozen package embeds the selected source SHA, build-time Python dependency
inventory and the desktop-only release declaration. Its startup self-test
constructs the app, verifies `/arg` and `/arg/world`, and verifies all
declared browser assets. No Python, npm, git checkout or model account is
required on the **receiving** machine. Its package-manager installation may
still require sudo authorization and ordinary distro dependencies.

A passing Actions build, if one is produced, provides a workflow artifact
containing `static-workbench-desktop_amd64.deb` and `SHA256SUMS` for
inspection, **not** a signed or device-tested public release. Open the .deb
with the receiving machine's graphical Software Install application; then
launch **Static Collective · First House** from the application menu.

The original `bash scripts/build-desktop-deb.sh` continues to build the
older GENESIS/desktop pin and use the ordinary Workbench entrypoint. The
first-house build does not modify that pin, its tests or ISO claims.

## Release gates still required

1. Exact pinned Workbench source and all First Door/World Entry tests green.
2. STATIC OS manifest/TRIAD/FLIGHT checks and both desktop build modes green.
3. Inspect Debian artifact source SHA and library floor (Ubuntu 22.04 glibc).
4. On a backed-up/disposable **real** Zorin 17+ or Ubuntu 22.04+ amd64 desktop:
   GUI install; first-launch opt-in; three Seeds → Machine → World → Enter World;
   browser closing and reopening; server restart and local save continuity;
   app-menu repeated clicks, keyboard/mobile-width browser and offline launch;
   package upgrade and removal while preserving journal and configuration.
5. Sign/publish only after the owner reviews the exact head and completed gates.

The existing launcher still runs a local browser-based server; a URL is
not a native full-screen game. There is no Windows/Android installer, no
automatic update, no starter World, no auto-backup and no cross-project hub
in this bounded slice.
