# STATIC-CAD-006 — Feature Trees Through GOATnote

Status: experimental, draft, stacked on STATIC-CAD-005 (#56), CAD-004
(#55), CAD-003 (#53), Apparatus-002 (#52), Question-First-001 (#51).

This is a **real owner-selected CAD revision and GOATnote journal
integration**, not a new journaling implementation hidden inside Static-OS.

## Architecture: what belongs where

STATIC OS owns the question, feature-tree composition, owner-selected
one-turn CAD execution and read-only local reconstruction.

CAD-005 owns actual CadQuery/OpenCASCADE pad/pocket B-rep construction,
STEP/STL output and six declared decision events. The ledger records
a source, selected feature operations, alternatives, rationale codes,
and observable evidence, NOT private AI chain-of-thought.

reLATTE owns portable signed crossings, transport and independent
receiver dispositions. An R14 native roundtrip binds exact SKETCH,
DESIGN TRACE, STEP and STL payload hashes. Receiver issues signed
RECEIVED then R3_HOLD, with zero semantic/physical authority.

**GOATnote owns the journal**, implemented as native GOATnote source note,
saved immutable source version, version-anchored margins, and a Return
Thread. Static-OS does not duplicate its source semantics. It runs the
exact pinned GOATnote adapter and creates a proposed import handoff;
the user's offline browser notebook is not touched until the person
explicitly clicks GOATnote's Import CAD journal control.

## The feature-tree experiment

A source-verified CAD-004 sketch contains a pad and through-pocket.
The frozen feature tree has a typed DAG:

    source solved sketch
         |
        PAD
         |
      POCKET_THROUGH

It proposes exactly two independent design variations:

    pad-deeper : increase PAD depth 2000 micrometres
    bore-wider : increase first circular hole radius 500 micrometres

Each candidate remains inert until an explicit separate owner selection
for software CAD and signed HOLD (not fabrication). This is a deliberately
narrow *editable feature revision model*, not a general-purpose associative
parametric kernel or fully interactive CAD editor.

Only the selected variation is constructed within that occurrence. The
other is recorded as NOT EXECUTED. It may be selected in a separate
explicit occurrence, producing a distinct solved-sketch ID, exact CAD
solid, signed reLATTE crossing, native GOATnote journal, and source
history. Both branches retain the original unchanged sketch as
revision_parent_id, so they never silently rewrite their ancestor.

## GOATnote journal contents

After native reLATTE verification, Static-OS constructs a bounded
GOATnote handoff carrying:
- exact six-event declared design trace with no hidden reasoning claim;
- verified crossing, RECEIVE and HOLD receipt IDs;
- source sketch and solid manifest IDs;
- branch tree, selected branch and explicitly unexecuted alternative;
- the precise signed crossing timestamp (not purported event time);
- explicit fabrication grant FALSE.

A pinned GOATnote module takes the handoff and produces one canonical
source note with one frozen source version, twelve anchored margins
(six witness, six question), and a two-entry Return Thread (question
and carry). The original human notebook is never auto-edited.

The resulting JSON file is IMPORTABLE by GOATnote's own opt-in browser
button (GOATnote PR #13). That project currently stores plain-text
notes in browser localStorage, without production-grade durability,
encryption or cloud backup. The proposal itself is public design
evidence; never put private notes into a public GitHub Actions artifact.

This is an adapter contract, not a live OAuth or cloud sync connector.
GOATnote's browser does NOT independently cryptographically validate
native reLATTE signatures. Static-OS performs that check before
emitting the selected handoff. A forged external file should never
be mistaken for a prevalidated native source unless it passed
the donor's actual signature and byte evidence checks.

## Runtime pins used by CI

- native GHoT Instrument Rack:
  6e4aab6aec3b28f8dd50d01c3d571ae754c653d1
- native reLATTE:
  dcc8cdca84c440aa4294134f020fb7095bf87f24
- GOATnote CAD Journal 001 adapter:
  64fee0380bf10d68c9885ccfd6b5632567892704

All are reviewed as explicitly selected source versions. GOATnote's
branch is an unmerged experiment; no production roll-out is claimed.

## Operator steps

With a trusted source checkout containing external/GOATnote,
external/reLATTE (installed), and external/GHoT, follow the
Question-First 001 → Apparatus 002 → CAD 003 → CAD 004
instructions to prepare one bounded original source sketch.

Plan possible feature revisions only (zero instrument effects):

    python3 scripts/static-cad-goatnote.py plan \
      --source-sketch /path/to/original/sketch.json \
      --out /tmp/cad006-feature-tree.json

The output lists candidate IDs pad-deeper and bore-wider plus exact
tree_id. Prepare a separate human-authored JSON decision:

    {
      "schema": "static-os.cad-feature-selection/v0",
      "tree_id": "<exact source tree ID>",
      "candidate_id": "pad-deeper",
      "owner_id": "local-human",
      "approved": true,
      "execution_scope": "SOFTWARE_CAD_KERNEL_AND_SIGNED_HOLD"
    }

Then explicitly execute one bounded **software** CAD experiment:

    python3 scripts/static-cad-goatnote.py execute \
      --tree /tmp/cad006-feature-tree.json \
      --selection /tmp/cad006-selection.json \
      --out-dir /tmp/cad006-selected \
      --private-relatte-root /private/new/relatte-cad006

The private reLATTE root must not be inside the exported CAD package.
It holds signing keys and native receiver journal. Do not publish it.

Cold verify original bytes, real OCCT STEP, signed reLATTE receipts,
exact revised feature tree and GOATnote-native source/margins without
running the kernel or creating another crossing:

    python3 scripts/static-cad-goatnote.py verify \
      --out-dir /tmp/cad006-selected

Selected output includes:
- tree.json, selection.json, branch-sketch.json, branch-provenance.json
- solid/ with actual STEP, STL, CAD trace and signed reLATTE evidence
- goatnote-handoff.json — selected exact GOATnote import payload
- goatnote-preview.json — output of genuine GOATnote journal module
- manifest.json — source/branch/receipt IDs and exact hashes

In GOATnote experimental app, choose **Import CAD journal**, select
goatnote-handoff.json, then confirm. It appends a source note, never
replaces the notebook. The person can add corrections, interpretations,
questions and Return Threads while keeping the original version intact.

## CI and hostile tests

The dedicated workflow pins the three actual repository sources,
runs the real OCCT kernel and native signed reLATTE roundtrip for
BOTH candidate branches in separate occurrences, verifies the native
GOATnote projection, and tests:
- no selected branch permits no execution;
- wrong owner/grant/candidate/schema refuses;
- the original source sketch survives both revisions byte-for-byte;
- two alternatives become distinct reLATTE crossings and GOATnote notes;
- GOATnote margins quote exact saved source ranges;
- only the selected branch executes within a given occurrence;
- cold replay never reconstructs geometry or reissues reLATTE receipts;
- fake GOATnote source text, grant escalation, rehashed fake feature
  nodes and forged native signatures refuse;
- private signing keys stay outside the uploaded design package.

All 005/004/003/002/001 regressions run afterward. Workflow emits
one selected branch's public artifact as a GitHub Actions zip.

## Non-collapse laws

    GOATNOTE SOURCE != ANNOTATION
    RETURN THREAD != SOURCE MUTATION
    DESIGN ALTERNATIVE != EXECUTED RESULT
    HISTORICAL REVISION != CURRENT AUTHORITY
    CAD FEATURE TREE != PHYSICAL CONTROLLER
    PRIVATE THOUGHT != DECLARED EVIDENCE
    SIGNED CROSSING != SEMANTIC TRUTH
    RECEIVED != ADMITTED
    HOLD != FABRICATION PERMISSION
    GOATNOTE IMPORT CANDIDATE != IMPORTED HUMAN NOTEBOOK
    CAD SOLID != ENGINEERING CERTIFICATION
