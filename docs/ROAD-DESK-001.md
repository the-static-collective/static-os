# ROAD-DESK-001

Status: integration candidate

ROAD-DESK-001 composes the green ROADKIT-001 deployment roads into the exact whole-house Workbench lineage already used by STATIC OS.

## Exact lineage

STATIC OS previously pinned:

    static-workbench
    integration/first-use-whole-house-20260920
    f3829fa8767961f8993fda241715f49b06d7b29d

Road Desk was added on top of that exact lineage and proven at:

    d7ec75ed7ab6fe8a92805875091fe20754821960

Workbench PR:

    the-static-collective/static-workbench#88

The same Road Desk feature was also replayed and proven on current Workbench mainline in PR #87. STATIC OS intentionally pins PR #88's lineage because current main is not an automatic superset of the whole-house branch.

    NEWER MAIN != AUTOMATIC SUPERSET
    PIN CHANGE != SAFE UPGRADE

## What appears in HOUSE

Workbench now exposes a **Road Desk** navigation surface.

It may observe one explicitly configured ROADKIT House:

- House id;
- world id;
- label;
- content-addressed House identity;
- identity SHA-256 integrity;
- inbox foreign crossings;
- foreign HOLD receipts;
- local ADMIT receipts;
- outbox count.

The API is read-only:

    GET /api/roadkit

There is no Workbench RoadKit POST action.

An attempted POST to `/api/roadkit` is covered by Workbench tests and returns 405.

## What Road Desk cannot do

Road Desk cannot:

- initialize a House;
- read the RoadKit private crossing key;
- start a peer;
- send a crossing;
- pull remote bytes;
- accept a crossing;
- create a destination-local re-crossing.

Those actions remain in the explicit ROADKIT operator layer.

    UI != ROADKIT EXECUTION
    VISIBLE HOLD != ACCEPTANCE

## Receipt honesty

Road Desk independently verifies the SHA-256 address of the House identity artifact.

It parses receiver journal receipts for display, but it does not duplicate reLATTE's cryptographic receipt verifier.

It therefore reports:

    identity_content_address_checked;
    receipt_signatures_not_reverified

and freezes:

    RECEIPT PARSED != SIGNATURE VERIFIED

## House selection remains explicit

STATIC OS does not choose a RoadKit House path by default.

The skeleton Workbench config contains only a commented example:

    # roadkit_house_root = "~/.local/state/static-roadkit/my-house"

If no root is configured, Road Desk renders an explicit unconfigured state.

This is intentional:

    NO DEFAULT HOUSE != NO ROAD DESK

Installing the habitat does not silently declare which sovereign House represents the operator.

## Existing ROADKIT operator flow

ROADKIT remains the effectful layer:

    bash scripts/roadkit-setup.sh --install
    bash scripts/roadkit.sh init ...
    bash scripts/roadkit.sh file-offer ...
    bash scripts/roadkit.sh file-import ...
    bash scripts/roadkit.sh peer ...
    bash scripts/roadkit.sh lan-send ...
    bash scripts/roadkit.sh pull ...
    bash scripts/roadkit.sh accept ...

Workbench is the window onto that state, not the hand that silently changes it.

## Composition

    ROADKIT
      owns roads + material movement + explicit human acceptance
            ↓
    ROAD DESK
      observes House identity + HOLD/ADMIT history
            ↓
    STATIC OS
      pins the exact Workbench and transport substrate

Stable law:

> **Moving the crossing is not making the decision. Seeing the crossing is not making the decision either.**

## Claims still not made

This integration remains host-level evidence. It does not prove:

- physical removable-drive operation;
- two separately installed machines;
- encrypted LAN transport;
- automatic peer discovery;
- authenticated human/network peer identity;
- hardware boot;
- installed persistence.

The next empirical gate is physical: initialize two real Houses on separate machines and perform the already-green file and HTTP contracts across an actual removable drive / LAN.
