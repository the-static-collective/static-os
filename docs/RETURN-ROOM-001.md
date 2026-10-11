# RETURN ROOM 001 — STATIC OS as a local question-custody workbench

**Status:** removable, offline userspace experiment. **Not a bootable STATIC OS claim**. Stacked only on [STATIC OS QUESTION-FIRST-SESSION-001 PR #51](https://github.com/the-static-collective/static-os/pull/51); makes no change to its GHoT execution, boot image, launch services, installation or source authority.

## The new bounded ability

A human can bring a manually exported **redacted** MEMENTO Crazy Slots proposal, native signed reLATTE `RECEIVED → R3_HOLD → PAYLOAD_BYTES_VERIFIED` evidence, a source-local UNDERSTORY contact + unresolved association, and a minimal Question Box seed to an **independent** local STATIC OS session.

STATIC OS *does not originate* those source-world records. It verifies the cryptographic crossing using an exact, separately installed **real reLATTE implementation**, and invokes the **actual National Treasure Question Box** on the redacted seed. It does not fetch or package private MEMENTO source or replicate its private compiler.

```text
MEMENTO (private source owner)        not accessed by STATIC OS
   -> voluntary redacted portable carrier
   -> signed reLATTE receiving receipts (HOLD)
   -> local UNDERSTORY contact + unresolved association (claimed observer)
   -> National Treasure redacted question seed
                  |
            STATIC OS RETURN ROOM
             read-only INSPECT
             check source/receipt/proposal addresses
             check native reLATTE P-256 receipts and signer continuity
             check owner-local association boundary without authenticating observer
             call native National Treasure question engine (SOURCE OBJECT)
                  |
           human SELECTS local docket?
             no -> STOP
             yes -> PREPARED checkpoint → create-only HELD_QUESTION session
                  |
              read-only REPLAY
             source bytes must still match
             signature reverified; no source execution or next turn
```

## Exact donor pins used by CI

- reLATTE `dcc8cdca84c440aa4294134f020fb7095bf87f24` — native `verifyOpaqueOrganCrossing` and `verifyReceipt`; never vendored signer.
- National Treasure `d6ff149a7a2d59dcb41c2c61606204b20b56a2fa` — the real `fromMementoHeldSeed` / Question Box engine from [PR #85](https://github.com/the-static-collective/national-treasure/pull/85), stacked on native Question Box [PR #70](https://github.com/the-static-collective/national-treasure/pull/70).
- MEMENTO source is **PRIVATE** and **NOT** checked out, mirrored or used in the public CI. The CI donor generates ONLY synthetic portable data in a temporary directory. The corresponding MEMENTO owner workflow remains under private [PR #52](https://github.com/the-static-collective/MEMENTO/pull/52).

## Local use

Requires Node 22+ with `--experimental-strip-types`, explicitly installed donor checkouts, and five operator-supplied JSON files exported locally by the source owner's vetted scripts.

```sh
COMMON="--carrier /private/path/public-carrier.json \
 --review /private/path/public-receipts.json \
 --seed /private/path/question-seed.json \
 --contact /private/path/understory/contacts/contact-id.json \
 --association /private/path/understory/associations/association-id.json \
 --relatte-root /trusted/reLATTE \
 --treasure-root /trusted/national-treasure"

# Inspect with zero local source-world writes and no next action:
node --experimental-strip-types scripts/return-room.mjs inspect $COMMON

# Separate, human-selected bounded local session:
node --experimental-strip-types scripts/return-room.mjs open $COMMON \
 --out "$HOME/.local/state/static-os/return-room/session001" \
 --reviewer local-operator --at 2026-10-11T14:06:00.000Z \
 --select-local-question

# After process restart, independently reverify exact input bytes and evidence.
node --experimental-strip-types scripts/return-room.mjs replay $COMMON \
 --out "$HOME/.local/state/static-os/return-room/session001"
```

The `--out` final directory must not yet exist and its *parent* must exist. Its contents are local private 0600 files under a 0700 directory. The operator's `--reviewer` is a software assertion, **not independently authenticated human identity**. No new source repo files, memory canon, questions, or instrument turns are written. The CLI does not expose a service or send outbound network requests.

## Durable checkpoint / interruption

`open` reserves the directory and writes `checkpoint.json` with `PREPARED` and SHA-256 of each **entire source file's raw bytes**, *before* executing any donor verification. On complete independent verification and explicit selection, it writes `session.json` with `HELD_QUESTION`, content-addressed local session identity, exact reLATTE receipt IDs, the next Question Box question, and explicit no-authority claims.

An interrupted `PREPARED` may be **replayed** as `PREPARED_HOLD` and cannot be retried automatically, mutated into an admission, or used to call the source donor again. No auto-repair / auto-next-question follows. Completed replays recompute source byte fingerprints, native cryptographic signatures, correspondence of UNDERSTORY contact/association and deterministic Question Box output. A changed original file or modified session refuses.

This local digest is **not** a cryptographic operator signature and an attacker with writable filesystem access could rewrite local files together. Persisted original bytes remain under the source operator's custody; verification requires them still present.

## What this proves (synthetic donor)

The CI test creates a real native reLATTE P-256 signed crossing and native local receiver HOLD/custody. The source material is only two synthetic opaque slots, not copied from private MEMENTO. It verifies:

- exact content-bound redacted proposal, no ancestry or owner authorization;
- three native signed local receipts from one independent receiver;
- local contact and unresolved association match receipt IDs and opaque commitments;
- actual National Treasure Question Box insists original-source recovery remains an open question;
- mandatory separate human-local `open` selection, never implied by import;
- `PREPARED_HOLD` upon interrupted output, refusing automatic retry;
- cold replay in a second Node process with no re-execution;
- mutated signatures, changed byte content, false ADMIT, forged witness date/source, or inflated evidence refuse.

No guest OS boot, physical disk persistence after boot, physical user attendance, private corpus admission, remote transport, historical ancestry, durable replicated storage, or sender-owner identity is established by the synthetic CI.

## Next doors (separately selected)

1. Local HOUSE UI that imports these five files through an operator-selected file picker, **without** surfacing private paths on Abundent.
2. Optional `question_first` bridge that offers *candidate* apparatuses to human selection. `HELD_QUESTION != EXECUTE`, and old checkpoints cannot become new instrument grants.
3. Source-owner signed public key binding and media-independent backup/mirror for a future post-author reader, with explicit privacy/custody review.

### Laws

```text
OPERATING SYSTEM != OWNER OF MEMORY
RECEIPT != READER
SIGNED HOLD != SOURCE TRUTH
CONTACT != ANCESTRY
QUESTION != COMMAND
PREPARED != SAFE RETRY
HELD_QUESTION != NEXT TURN
SESSION DIGEST != OWNER SIGNATURE
INSTALLATION != VERIFIED BOOT
PRIVATE SOURCE != PUBLIC ROUTE
```

**STATIC OS owns the desk. Other worlds own their history.**
