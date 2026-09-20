# GENESIS 001 — executable live-image candidate

## Status and first proof

This branch contains an actual Debian live-build ISO recipe, a pinned HOUSE source,
a per-user loopback service and XFCE login handoff, plus deterministic contract
refusal tests. It is **not** a verified bootable ISO. The optional [manual ELF guest gate](GENESIS-ELF-001.md) pins the Workbench carrier from an experimental draft PR; its contract and host-run fixture are not a guest-boot or live-agent proof. No installer, encrypted
persistent volume, auto-updater, AI privilege, LAN service or self-development
engine is included.

Debian live-build config/package-lists, chroot includes and hooks are documented
in the [Debian Live Manual](https://live-team.pages.debian.net/live-manual/html/live-manual.en.html).

## Safe build environment

Build on a **disposable Debian bookworm amd64 VM** with ample free disk,
RAM, and network access. Do not run this experimental root build script on
your primary Zorin installation. Boot the resulting ISO in an isolated VM
before writing it to removable media.

Inside the build VM:

```sh
sudo apt update
sudo apt install -y live-build debootstrap squashfs-tools xorriso git python3 ca-certificates
git clone https://github.com/the-static-collective/static-os.git
cd static-os
git switch genesis-001-live-iso
python3 scripts/validate-manifest.py manifest/genesis-001.json
python3 -m unittest discover -s tests -v
sudo ./scripts/build-iso.sh
```

The script refuses to overwrite an existing build directory. ISO and SHA-256
receipt are left under `.build/genesis-001/`. The build requires network access
to Debian apt repositories, the pinned GitHub HOUSE commit, and PyPI during
the chroot installation. **Boot-time HOUSE does not need a network call**,
but that is only an intended property until the offline VM gate passes.

The manifest pins the HOUSE Git commit. Apt repository snapshots and Python
wheels are *not* yet pinned by checksum; output is auditable via the embedded
manifest, HOUSE freeze and Debian package inventory, **not bit-identical
reproducibility**. Boot compatibility, accessibility, firmware, and real
hardware operation have not yet been tested.

## Gate card

1. **CONTRACT:** local validator, shell syntax and negative tests pass.
2. **ISO:** root live-build succeeds; record SHA-256, build host, ISO filename
   and source SHA. Output status remains candidate.
3. **VM BIOS/UEFI:** boot ISO in two VM firmware modes; log any failure rather
   than assuming success from ISO creation.
4. **HOUSE OFFLINE:** disconnect VM network; use live desktop, verify
   `systemctl --user status static-workbench.service`, open
   `http://127.0.0.1:13700/`; verify no non-loopback HOUSE listener.
5. **STATE:** create a Workbench-owned note/receipt, restart HOUSE and confirm
   retained state in the same live session. Uninstalled live images do **not**
   provide durable cross-boot persistence; do not present them as installed OS.
6. **RECOVERY:** verify VT/terminal, stop HOUSE service, reboot without it,
   diagnose failure, and boot the original Zorin disk unchanged.
7. **ELF OFFLINE GUEST (separate optional gate):** after independently witnessed VM boot and offline HOUSE, invoke `static-elf-proof` as the ordinary guest user; inspect two distinct deterministic carrier occurrences and their receipts. This fixture does not run OpenManus or prove persistence between boots. See [GENESIS-ELF-001](GENESIS-ELF-001.md).
8. **HARDWARE:** only after VM success, deliberately choose expendable removable
   media; verify boot and TV display/firmware behavior on real machine.

`GENESIS 001` passes only when image, VM boot and offline HOUSE gates have
independent observation receipts. Existing Zorin storage must not be touched by
this recipe. A persistent installer and full self-development engine are later
milestones with their own approval and recovery gates.

## Source ownership

- STATIC OS owns image/build/session handoff, distribution receipts and OS gates.
- Workbench owns its local browser and user-state journal, not OS privilege.
- LOADOUT owns bounded task/capability selection; discovery never grants effects.
- 3rdi owns observer-local projections, not boot truth or historical rewriting.
- ALEX owns provenance/claim witness, not global package or OS authority.
- Foundry may eventually build candidate images in isolated VMs; **candidate
  promotion requires a distinct explicit human act** and a proven rollback path.

Current manifest stages are a dependency DAG for static validation only;
declared relationships neither start processes nor authorize project effects.
