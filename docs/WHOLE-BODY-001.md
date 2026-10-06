# WHOLE-BODY-001 — STATIC OS around the crossing field

Status: source-bundle candidate, stacked above GIT-BRIDGE-001.

WHOLE-BODY-001 makes the live image carry one exact inspected source cut for the organs that surround the unresolved crossing interval:

```text
STATIC OS
  wakes the world
      │
      ▼
GHoT
  body / capability / liveness
      │
      ▼
Jubilee
  bounded occurrence + reproducible ancestry
      │
      ▼
reLATTE
  signed crossing grammar + receipts
      │
      ▼
SupaBardo
  LEFT A / NOT YET LOCAL B
      │
      ▼
Corpus
  receiver-local constitution / causal present
      │
      ▼
TranchNode
  addressed durable particulars
```

This is an ownership map, not a claim that every organ runs automatically at boot.

## SupaBardo boundary

The bundled Human-Witness source contains the accepted SupaBardo design specimen. STATIC OS treats it as a boundary contract only.

```text
ENTER → FORM → WITNESS → WAIT → EXIT → DECAY
```

The OS must preserve:

```text
UNRESOLVED != ABSENT
SUPABARDO STATE != CANON
RECEIVED != ADMITTED
CROSSING MAY BE SHARED; MEANING REMAINS RECEIVER-LOCAL
```

SB-001 remains an external Human-Witness specimen. STATIC OS does not implement, emulate, or silently complete that ceremony.

## What goes into the image

During ISO construction the builder fetches each exact SHA in `manifest/whole-body-001.json`, verifies `FETCH_HEAD`, and archives the source tree into:

```text
/opt/static-os/organs/ghot
/opt/static-os/organs/relatte
/opt/static-os/organs/jubilee
/opt/static-os/organs/corpus
/opt/static-os/organs/tranchnode
/opt/static-os/organs/supabardo
```

The exact composition manifest and one SHA witness per organ are installed under:

```text
/usr/share/static-os/whole-body-001.json
/usr/share/static-os/organs/<id>.commit
```

Bundling source does not imply runtime readiness or authority.

## Boot posture

The candidate wake order is:

```text
STATIC OS boot
→ HOUSE
→ verify source bundle
→ inspect durable particulars
→ GHoT body
→ reLATTE receiver
→ Jubilee verification
→ Corpus WorldCut
→ SupaBardo boundary
→ operator surface
```

Only the already-existing HOUSE startup is automatic in this slice.

No foreign organ is auto-started. That is deliberate: persistent state paths, runtime versions, migration policy, and recovery gates are not yet jointly proven.

## Operator diagnostic

Inside the image:

```sh
static-whole-body status
```

reports whether the exact source cuts and commit witnesses are physically present in the current image and shows each organ's declared runtime posture.

This diagnostic never starts an organ or crosses a network boundary.

## Why source-bundle first

Corpus currently requires a newer Node runtime than Debian bookworm supplies by default, and the other organs have independent runtime/dependency contracts. Installing every dependency merely to make the image look integrated would confuse source presence with executable readiness.

WHOLE-BODY-001 therefore first proves:

```text
EXACT SOURCES CAN SHARE ONE BOOT ARTIFACT
WITHOUT SHARING AUTHORITY
```

The next gate may add one runtime seam at a time.

## Cross-boot boundary

This slice does not add a persistence partition.

Therefore:

```text
SOURCE PRESENT != PERSISTENT BODY
BOOT != CONTINUITY
REMOTE GIT DURABILITY != LOCAL FILESYSTEM PERSISTENCE
```

A later persistence experiment must establish the durable state root before GHoT identity, reLATTE journals, Corpus present, Jubilee receipts, or TranchNode particulars may be claimed to survive cold boot.
