# LIVING-CODEX-ENDPOINT-001

Status: executable host-level integration candidate

This is the first bounded composition of the old Living Codex / Solar Seed Node / TranchNode trajectory into one two-house proof.

It does not create a new monolith. STATIC OS pins and composes independently governed organs:

- **ROroomOM** produces a human-governed Room Score / Play Memory / Guest Port decision.
- **TranchNode** preserves the exact material artifacts in local content-addressed stores.
- **reLATTE** signs crossings, carries them through a file-bundle road, and records receiver-local RECEIVE / HOLD / ADMIT history.
- **STATIC OS** owns only the composition manifest and acceptance proof.

## The specimen

    HOUSE A
      local Room Score
          ↓
      conduct
          ↓
      Play Memory
          ↓
      Human Offer
          ↓
      Guest Port
          ↓
      guest proposal
          ↓
      HUMAN ACCEPT
          ↓
      local Room receipt
          ↓
      TranchNode artifact persistence
          ↓
      signed reLATTE crossing
          ↓
      House A local ADMIT
          ↓
      file-bundle carrier + addressed attachments
                  │
                  ▼
    HOUSE B
      verify crossing signature
          ↓
      verify every attachment address
          ↓
      ingest exact bytes into local TranchNode store
          ↓
      RECEIVE
          ↓
      HOLD foreign crossing
          ↓
      HUMAN local admission intent
          ↓
      fresh House B signed re-crossing
          ↓
      RECEIVE local crossing
          ↓
      local consequence artifact
          ↓
      ADMIT local crossing

The foreign crossing itself remains HOLD at House B.

The local consequence is attached to a **new House B crossing** created after explicit human acceptance.

That is deliberate:

    FOREIGN CROSSING != LOCAL CONSEQUENCE
    HOLD != ADMIT
    HUMAN ACCEPTANCE REQUIRES LOCAL RE-CROSSING

## Why the re-crossing matters

A simpler implementation could have:

    House A sends
    → House B verifies
    → House B directly admits

That would technically work but would blur transport, verification, foreign proposal, and receiver-local authority.

LIVING-CODEX-ENDPOINT-001 instead freezes:

    foreign crossing
    → verified
    → held

    human at destination
    → local intent
    → fresh signed crossing
    → local admit

The destination therefore cannot accidentally inherit the source house's authority merely because the payload was valid.

## The carrier

The proof uses reLATTE's existing `file-bundle` transport frame.

STATIC OS adds only a carrier specimen around it:

    carrier/
      crossing.frame.json
      bundle.json
      objects/
        <sha256>.bin
        <sha256>.bin
        ...

The crossing signature binds the payload addresses.

Each attachment is independently hashed again on receipt and must match its declared `sha256:<digest>` address before entering House B's TranchNode store.

The carrier manifest is transport-only.

    TRANSPORT != AUTHORITY
    ATTACHMENT PRESENCE != ADMISSION
    CONTENT ADDRESS != LOCAL CONSEQUENCE

A later USB, QR, LAN, Bluetooth or LoRa adapter may carry the same semantic objects without changing admission law.

## Distinct houses

The executable proof creates:

    static-house:a / static-world:a
    static-house:b / static-world:b

House A and House B have separate:

- reLATTE receiver roots;
- receiver journals;
- local receiver keys;
- source / human crossing signing keys;
- TranchNode artifact roots;
- state refs;
- local consequences.

The test explicitly proves the House A source signing key and House B human re-crossing signing key differ.

It also proves House B-only human intent and consequence artifacts are absent from House A's artifact store.

## Shared history without shared state

Both houses retain attributable relation to the same foreign crossing.

But their receiver state differs:

    HOUSE A
    foreign crossing → ADMIT

    HOUSE B
    foreign crossing → HOLD
    local human re-crossing → ADMIT

The proof requires:

    house_a.state_ref != house_b.state_ref

So:

    SHARED HISTORY != SHARED GLOBAL STATE

This is the recovered TranchNode goal without the old assumption that peer sync should merge every node into one ledger.

## Durable restart

The House B receiver is reopened from its on-disk reLATTE receiver root.

After replay:

- the exact snapshot must match;
- the foreign crossing must still be HOLD;
- the local human re-crossing must still be ADMIT;
- journal length must match.

The House B TranchNode store must independently return the imported Play Memory bytes and its local consequence bytes by content address.

## Exact donor pins

The manifest freezes exact donor commits:

- reLATTE: `9b4b7be38e67c8e9c3e43328ef0a940c08f7f2ca`
- ROroomOM: `5e93843ceae80a2bca94ff438f0bc24dc49a4b85`
- TranchNode: `1d731fbb228f68bbefc008d18c48d6be001935be`

CI checks out those exact commits and runs their own proof surfaces before running this composition.

## What this proves

LIVING-CODEX-ENDPOINT-001 proves, at host level:

1. a human-governed AI crossing can become an attributable Room consequence;
2. that consequence and its Play Memory can persist as TranchNode artifacts;
3. a source house can sign an exact reLATTE crossing over those addresses;
4. a file road can carry the signed crossing plus exact addressed bytes;
5. a second house can verify and persist those bytes without admitting them;
6. the foreign crossing can remain HOLD;
7. explicit destination-human action can create a fresh local re-crossing;
8. only that destination-local crossing becomes ADMIT;
9. both receiver journals survive replay;
10. both houses share verifiable history while retaining different local state.

## Claims deliberately not made

This is **not yet**:

- an ISO boot proof;
- an installed-system proof;
- a physical USB-device proof;
- LAN peer discovery;
- Bluetooth or LoRa transport;
- encrypted private payload transport;
- authenticated external AI-provider identity;
- automatic replication or promotion;
- global consensus.

Those remain later doors.

## Recovered endpoint law

> **A house may carry another house's history without carrying its authority.**

And the older TranchNode idea is now typed more precisely:

> **Many sovereign histories may share verifiable crossings without sharing one global state.**
