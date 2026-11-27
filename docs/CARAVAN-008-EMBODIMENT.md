# CARAVAN 008 — EMBODIMENT
Optional community application cartridge for STATIC OS, stacked on GENESIS BOOT 008 PR #97 (exact base b4cf776fae485b9035812196db7abb6553a78972). CARAVAN owner: planZ PR #49, exact original source commit 72f52f8265a388a8eee894df38fc8c858b01db1c; 20 manifest entries plus the pinned manifest. No fork of application logic. Existing five Suitcase planning profiles and old cartridges unchanged; the native Suitcase CLI adds an optional caravan-plan subcommand. The separate CARAVAN plan selects one or more six-vocation advisory presets (all source code included; presets are not access control).

## Existing Linux first (no root)
Obtain an exact checkout of planZ commit above while connected. From STATIC OS checkout:
```sh
python3 scripts/caravan-cartridge.py stage /path/to/planZ/experiments/caravan ./caravan-payload
python3 scripts/suitcase.py caravan-plan church radio library
python3 -m venv .caravan-venv
.caravan-venv/bin/pip install -r caravan-payload/requirements-crossing.txt
mkdir -p "$HOME/.local/state"
.caravan-venv/bin/python scripts/caravan-cartridge.py run --source caravan-payload --data "$HOME/.local/state/caravan" seed found "My Community House"
.caravan-venv/bin/python scripts/caravan-cartridge.py run --source caravan-payload --data "$HOME/.local/state/caravan" caravan serve
```
Open http://127.0.0.1:8765/ . Install dependencies while connected or provide a platform-specific wheelhouse; optional FFmpeg for projection. No synthetic material is shared by founding. Existing node: do not repeat found. Keep data outside source/Git. LAN requires native explicit private interface selection and separate trusted network. No sensitive records; unencrypted keys and HTTP.

## Optional Alpine image build
The original BOOT 005 native mkimage path is extended, not replaced. In its existing disposable container build flow stage the verified CARAVAN payload into /payload/caravan (alongside the original eleven source histories); pass GENESIS_CARAVAN=1 into the container. The existing build-alpine-genesis-iso.sh and apkovl hook verify the exact donor before embedding source and launcher. The profile adds Alpine py3-cryptography and ffmpeg to the local APK repository and world. Default unset leaves the original recipe unchanged. Normal boot does not start CARAVAN, generate identity, enable LAN or install to disk. Use the existing genesis nonroot account; run static-caravan plan church library, static-caravan verify, then static-caravan run seed found NAME (create its state parent first) and static-caravan run caravan serve. Diskless RAM state is ephemeral; explicitly set CARAVAN_DATA to a protected user-owned path on deliberately mounted storage for retention. No automatic mount, partition, format or persistence promise.

## Gates
Separate CI tests source pin, tamper/symlink rejection, staging/overwrite refusal, presets and original 59-test regression; it does not build the ISO. Existing Alpine build/QEMU and physical USB gates must be executed for the exact opt-in image, with guest crypto and FFmpeg verification, explicit foundation, offline localhost and real two-phone LAN checks. No ISO, BIOS/UEFI, real device, physical persistence, partner, deployment, or package closure proof claimed here. No license choice made. No main merge. 
