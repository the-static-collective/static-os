# FLIGHT-003 — composed HOUSE+ELF source and reference-only triad

Status: experimental candidate. This branch composes the previously independent
GENESIS-ELF-001 and TRIAD-001 code trees without declaring an ISO, VM boot,
installed OS, durable cold-boot state, or a self-updating machine.

## Exact source and ownership

The active Genesis manifest now pins the *same single Workbench commit* for
HOUSE and manual ELF. This commit is Workbench draft PR #62, which combines the
rectified carrier / Composition Ecology / MADDlib pure-plan slice with the
source-owned ELF implementation from original PR #60.

The TRIAD-001 evidence-only inventory and the FLIGHT-003 inventory both pin
that exact same HOUSE commit and are checked against the actual manifest.

Storyship PR #5 and TranchNode PR #78 are **reference-only**, with their
exact candidate source SHAs listed in `interop/flight-003.json`. They are not
packaged, executed, started, installed or required for boot by this branch.
Corpus and Jubilee remain TRIAD-001 reference-only handoffs, not runtime
adapters. Candidate Git SHAs document the inspected bytes, not releases.

## Proof and stop conditions

Run:

```sh
python3 scripts/validate-manifest.py manifest/genesis-001.json
python3 scripts/validate-triad.py interop/triad-001.json
python3 scripts/validate-flight-003.py
python3 -m unittest discover -s tests -v
```

The existing CI also runs the exact-pinned ELF two-occurrence smoke on the
source checkout; that is a **host-only fixture**. It does not prove guest boot.

Next independent evidence gates:
1. Confirm combined Workbench exact-head CI, browser, user-state and restart.
2. Build the ISO inside a disposable Debian bookworm VM; do not run the build
   script as root on the user's Zorin installation.
3. Boot the ISO in isolated BIOS and UEFI VMs and prove offline HOUSE and manual
   guest ELF execution while retaining logs outside the guest.
4. Provision disposable persistent media and independently witness the Storyship
   seal, cold boot, receive, and separately verified successor ELF.
5. Only then propose a separately approved TranchNode guest adapter, Corpus/Jubilee
   receipt view, image integration, and installation/recovery flight.

No verified guest run, cross-boot persistence, security sandbox, real OpenManus,
automatic successor generation, source authentication, or human approval can be
inferred from contract checks. A candidate image must never auto-promote.
