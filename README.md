# STATIC OS

A project-owned, Linux-based computational habitat for the Static Collective.

**Status:** GENESIS 001 / bootstrap under review. This repository does not yet contain a verified bootable ISO or installed OS.

The distribution integrates independently governed organs without absorbing their identity or authority. Debian supplies the kernel, boot, packages, and hardware support; STATIC OS owns its image composition, HOUSE session entry, provenance manifest, test gates, and operator documentation.

**Non-collapses:** installed != ready; discovered != authorized; build receipt != boot proof; image != installed persistence; candidate != admitted; source SHA != reproducible package closure.

See the GENESIS-001 proposal branch and PR for the executable first slice. Until its image and boot gates are run, claims of a working STATIC OS are premature.

## Workbench desktop installer preview

[LAUNCHPAD-002](docs/LAUNCHPAD-002.md) packages the pinned Workbench with its own
Python runtime for Zorin 17+/Ubuntu 22.04+ amd64. The **Desktop installer preview**
workflow produces a native `.deb`: install it through Software Install, then
open **Static Workbench** from the application menu. See the linked document for
build status boundaries, compatibility, logs and removal behavior.

## Living Codex endpoint

[LIVING-CODEX-ENDPOINT-001](docs/LIVING-CODEX-ENDPOINT-001.md) is the first host-level two-house composition of ROroomOM, TranchNode, reLATTE, and STATIC OS.

The candidate proves:

```text
House A human/AI Room consequence
→ TranchNode persistence
→ signed reLATTE crossing
→ file-bundle road
→ House B verify + HOLD
→ House B human local re-crossing
→ House B local ADMIT
```

The same foreign crossing is locally **ADMIT** at House A and **HOLD** at House B. House B consequence occurs only through a fresh locally signed human re-crossing.

```text
FOREIGN CROSSING != LOCAL CONSEQUENCE
HOLD != ADMIT
SHARED HISTORY != SHARED GLOBAL STATE
```

CI pins and independently verifies exact reLATTE, ROroomOM Guest Port, and TranchNode commits before executing the composition.

This remains a host-level integration proof. It does not claim a booted ISO, installed-system proof, physical USB test, network mesh discovery, or global consensus.

## Road Desk

[ROAD-DESK-001](docs/ROAD-DESK-001.md) pins a green Road Desk build from the same whole-house Workbench lineage already used by STATIC OS.

Road Desk observes one explicitly configured ROADKIT House—identity, foreign crossings, HOLDs, and local ADMIT receipts—through a GET-only Workbench surface. It does not expose RoadKit execution actions.

```text
OBSERVATION != AUTHORITY
VISIBLE HOLD != ACCEPTANCE
UI != ROADKIT EXECUTION
RECEIPT PARSED != SIGNATURE VERIFIED
```

House selection remains opt-in; STATIC OS does not choose or initialize a sovereign RoadKit House automatically.



## GHoT idle operator

[GHOT-IDLE-OPERATOR-001](docs/GHOT-IDLE-OPERATOR-001.md) pins the first game-shaped Workbench control shell on top of the Road Desk lineage.

GHoT makes the idle-clicker/RPG board the default operator view while preserving the existing desks as the actual owners of authority. Observed facts become resources; existing desks become quests; explicit human decisions remain boss gates.

```text
GAME STATE != CLAIMED REALITY
QUEST READY != AUTHORIZED
XP == WITNESS COUNT, NOT CAPABILITY
```

The Polsia STATICJACK quest is present but HELD: this candidate grants it no credentials, budget, repository access or execution authority.


## First physical boot

[FIRST-PHYSICAL-BOOT-001](docs/FIRST-PHYSICAL-BOOT-001.md) adds the first explicit cold-USB human witness gate above the GENESIS live-image candidate.

The helper hashes the exact built ISO and source lineage, then leaves physical observation fields unset until a human actually observes BIOS/UEFI prerequisites and a real removable-media boot with offline HOUSE on loopback. CI may test the receipt contract but cannot produce the physical witness.

```text
ISO BUILD != BOOT
HARDWARE BOOT != INSTALLED OS
HOUSE OPENED != PERSISTENCE
HUMAN OBSERVATION != CI ASSERTION
```


## Git bridge

[GIT-BRIDGE-001](docs/GIT-BRIDGE-001.md) adds explicit Git ingress and egress for project working trees under `~/static`.

```text
FETCH != APPLY
COMMIT != PUSH
PUSH != ADMISSION
SOURCE UPDATE != RUNNING OS UPDATE
REMOTE PERSISTENCE != LOCAL PERSISTENCE
```

The live image includes `git`, `openssh-client`, and the `static-git` command. RECEIVE is clean-tree, fast-forward-only; COMMIT stages only named paths; SEND requires a fresh fetch and refuses when the remote is ahead. STATIC OS does not create or embed Git credentials and does not auto-update itself.


## Whole body

[WHOLE-BODY-001](docs/WHOLE-BODY-001.md) makes the live-image recipe carry exact source cuts for GHoT, reLATTE, Jubilee Engine VM, Corpus OS, TranchNode, and the Human-Witness SupaBardo design specimen.

```text
GHoT      -> body / capability / liveness
Jubilee   -> bounded occurrence / ancestry
reLATTE   -> crossing grammar / receipts
SupaBardo -> unresolved interval
Corpus    -> receiver-local constituted present
TranchNode-> addressed durable particulars
```

The image vendors these sources without auto-starting or auto-authorizing the foreign organs. `static-whole-body status` verifies their presence and exact commit witnesses inside a built image.

```text
SOURCE PRESENT != RUNTIME READY
UNRESOLVED != ABSENT
SUPABARDO STATE != CANON
BOOT != CONTINUITY
```


## Persistent root

[PERSISTENT-ROOT-001](docs/PERSISTENT-ROOT-001.md) adds a cold-boot continuity floor using one deliberately prepared ext4 filesystem labeled `STATIC_STATE`.

STATIC OS never formats or chooses a disk automatically. When that exact labeled filesystem is present, the image mounts it at `/var/lib/static-os`, initializes or verifies one durable `root_id`, and emits a **fresh boot occurrence** on every wake.

```text
ROOT IDENTITY != BOOT IDENTITY
PERSISTENT BYTES != CONTINUOUS PROCESS
MISSING SHUTDOWN != CLEAN DEATH
SUPABARDO INTERIOR != DURABLE ROOT
```

HOUSE may attach its user state into the durable root before launching. Durable custody paths are reserved for GHoT, reLATTE, Jubilee, Corpus, and TranchNode, while SupaBardo receives no permanent interior directory; only explicit crossing exports may escape into durable custody.

The host-level proof preserves one particular across two simulated boot occurrences while keeping the boot identities distinct. VM and physical cold-boot proof remain unearned.


## Bardo bridge

[BARDO-BRIDGE-001](docs/BARDO-BRIDGE-001.md) pins the completed destructive SB-001 ceremony from reLATTE PR #57 into the whole-body image while keeping Human-Witness as the canonical architecture owner.

`static-bardo status` is an offline, read-only operator surface. It verifies that the exact SB-001 evidence commitment, verifier, and proof documentation are bundled, reports durable crossing exports, and refuses a persistent SupaBardo interior.

```text
LIVE SERVICE != HISTORICAL AUTHORITY
SERVICE DEATH != HISTORY DEATH
DURABLE RECEIPT != IMMORTAL BARDO
OPEN != ADMITTED
EXIT != ADMISSION
```

STATIC OS does not start Supabase or infer current live crossings. Live unresolved state is reported as **not observed**, not zero.


## Bardo generality

[BARDO-GENERALITY-002](docs/BARDO-GENERALITY-002.md) records the second materially different successful SupaBardo specimen.

```text
SB-001  STATIC-OS world receipt        -> ADMIT
SB-002  Haunted Toaster proposal       -> HOLD
```

Both specimens passed through an OPEN unresolved interval, received an independent receiver-local disposition, exited, lost the temporary membrane, and remained reconstructible from durable evidence.

The live image carries the exact SB-002 reLATTE proof separately under `/opt/static-os/bardo-proofs/sb002-relatte`; `static-bardo status` verifies both evidence commitments offline.

```text
EXPERIMENT AUTHORIZATION != CREATIVE KEEP
SECOND FAMILY PROVEN != STANDALONE REPO REQUIRED
GENERALITY EVIDENCE != UNIVERSAL PROTOCOL
```

The historical second-family gate is now satisfied only as **eligible for reconsideration**. STATIC OS does not promote a SupaBardo repository, permanent service, central event bus, or destination authority.
