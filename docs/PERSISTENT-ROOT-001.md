# PERSISTENT-ROOT-001 — cold-boot continuity floor

Status: mount-and-lineage candidate, stacked above WHOLE-BODY-001.

This slice gives STATIC OS one deliberately prepared removable filesystem that may survive power loss and cold reboot without pretending persistent bytes are a continuously living process.

## Physical contract

The human prepares an **ext4** filesystem with the exact label:

```text
STATIC_STATE
```

STATIC OS does **not** format a disk, repartition a device, or select internal storage.

At boot, the image may mount that exact label at:

```text
/var/lib/static-os
```

If no such filesystem exists, the OS still boots; persistence is simply unavailable.

```text
NO FORMAT WITHOUT HUMAN ACTION
MISSING PERSISTENCE != FAILED BOOT
```

## Durable layout

The first initialized root is versioned and gets one random durable `root_id`.

```text
/var/lib/static-os/
├── root.json
├── users/
│   └── <uid>/static-workbench/
├── organs/
│   ├── ghot/
│   ├── relatte/
│   ├── jubilee/
│   ├── corpus/
│   └── tranchnode/
├── crossing-exports/
└── lineage/
    ├── boots/
    └── shutdowns/
```

There is intentionally **no** `organs/supabardo/`.

SupaBardo is allowed to forget. Only a crossing artifact or receipt that explicitly escapes into durable custody belongs under `crossing-exports/`.

## Every boot is new

When the mounted root opens, `static-persist boot` creates a fresh boot occurrence receipt.

It records:

- durable root identity;
- fresh boot identity;
- previous boot identity, if any;
- whether the predecessor left an orderly shutdown receipt;
- hashes of the current STATIC OS composition manifests;
- the explicit nonclaim that this is the same process.

So:

```text
ROOT IDENTITY != BOOT IDENTITY
PERSISTENT BYTES != CONTINUOUS PROCESS
MISSING SHUTDOWN != CLEAN DEATH
```

An unclean power loss is not rewritten into an orderly shutdown.

## HOUSE attachment

Before HOUSE starts, the launcher may call:

```sh
static-persist attach-user
```

When persistence is mounted and initialized, this creates a per-UID durable Workbench state directory and symlinks the otherwise-ephemeral live-user state path to it.

It refuses to replace an existing real state directory or an unrelated symlink.

If no persistent root is mounted, HOUSE remains usable with ephemeral state.

## Organ roots

The paths under `organs/` are durable custody locations, not proof that an organ knows how to reconstruct itself from them yet.

Each integration must separately prove its adapter:

```text
ghot       /var/lib/static-os/organs/ghot
relatte    /var/lib/static-os/organs/relatte
jubilee    /var/lib/static-os/organs/jubilee
corpus     /var/lib/static-os/organs/corpus
tranchnode /var/lib/static-os/organs/tranchnode
```

PERSISTENT-ROOT-001 therefore proves the floor beneath reconstruction, not reconstructed Corpus/Jubilee/reLATTE semantics.

## Cold-death proof shape

The intended physical gate is:

```text
BOOT A
  ↓
STATIC_STATE mounted
  ↓
root_id = R
boot_id = A
  ↓
write one bounded particular
  ↓
orderly shutdown receipt OR abrupt death
  ↓
POWER OFF

BOOT B
  ↓
same STATIC_STATE mounted
  ↓
root_id = R
boot_id = B
B != A
  ↓
predecessor closure state visible
  ↓
particular bytes still present
  ↓
reconstruction layers may now attempt replay
```

The host test proves this lineage logic against one retained directory. VM and physical cold-boot evidence remain separate gates.

## Preparing media

Use a trusted partitioning tool outside this experiment to create an ext4 filesystem on deliberately chosen removable media and label it `STATIC_STATE`.

PERSISTENT-ROOT-001 intentionally provides no destructive formatting command. The image must never turn a guessed block device into persistence merely because it exists.
