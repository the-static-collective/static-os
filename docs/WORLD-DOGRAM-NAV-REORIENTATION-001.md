# WORLD → DOGRAM → NAV REORIENTATION 001

## Status

This slice extends the executable Bridge loop from recursive evidence back into navigation:

```
NAV → WITNESS → WORLD → MAKE GROUND → WITNESS → WORLD
                                              │
                                              ▼
                                           DOGRAM
                                              │
                                              ▼
                                             NAV
```

The new question is:

> When ancestry-aware evidence changes the next useful heading, how do we preserve the path that caused the reorientation instead of replacing one heading string with another?

## Why Dogram belongs here

Dogram already carries the exact grammar this crossing needs.

From `DELTA-AS-CARRIER-001`:

> **A DERIVED CARRIER MUST NOT IMPERSONATE AN ORIGIN.**

From `LINEAGE-SPINE-001`:

> **KEEP THE PAST ADDRESSABLE, NOT RECURSIVELY EMBEDDED.**

And Dogram already has a `same-surface-different-history` specimen.

This crossing treats a new NAV heading as a derived carrier.

The destination may be concise. The path that produced it stays addressable.

Dogram remains a calculation / receipt instrument. It does not become navigation authority.

## Core laws

```
ENDPOINT ≠ PATH.
PATH ≠ TRACE.
SAME DESTINATION ≠ SAME NAVIGATION.
REORIENTATION ≠ REPLACEMENT.
TRACE ≠ CAUSAL PROOF.
DOGRAM RECEIPT ≠ NAV AUTHORITY.
```

## Storage topology

The path and the heading are deliberately not stored in one giant object.

### Dogram trace ledger

`static.dogram-trace-ledger/v0` stores the declared six-artifact route:

1. contacted NAV receipt
2. WITNESS intake
3. WORLD comparison receipt
4. MAKE GROUND observation receipt
5. WITNESS re-entry
6. WORLD recursion receipt

Every artifact receives a deterministic content address.

Each entry stores:

```
position
kind
artifact_digest
parent_digest
relation
```

The actual artifact bodies live in the ledger's separate content-addressed store.

### Dogram transition capsule

`static.dogram-transition/v0` stays bounded.

It contains:

```
from_heading
to_heading
root_digest
path_head_digest
trace_ledger_sha256
world_recursion_sha256
delta_summary
preserved
status = proposed
claim_limit
```

It does **not** embed the six source artifacts.

The transition therefore carries enough addressable history to explain itself without dragging a recursive copy of the past into every new heading.

## Complete / incomplete / invalid

The trace verifier preserves another useful Dogram distinction.

### complete

Every declared artifact exists and matches its content address.

### incomplete

A referenced witness artifact is missing.

This does not mean the path was disproven.

```
MISSING WITNESS ≠ PROVEN SEVERANCE.
```

### invalid

Available material contradicts the declared trace, for example:

- content changed without its address changing;
- parent link mismatch;
- repeated artifact / cycle;
- root or head mismatch.

Missing and contradictory evidence remain different states.

## Run the path membrane

Build the declared trace:

```sh
mkdir -p .build/dogram-nav

python3 scripts/dogram_nav.py trace \
  examples/nav-contacted.local-test.json \
  examples/nav-to-witness.intake.json \
  examples/world-receipt.independent-contradiction.json \
  examples/make-ground.receipt.json \
  examples/make-ground-to-witness.reentry.json \
  examples/world-recursion-receipt.generated-downstream.json \
  -o .build/dogram-nav/trace.json
```

Inspect it:

```sh
python3 scripts/dogram_nav.py inspect \
  .build/dogram-nav/trace.json
```

A complete trace reports:

```
status = complete
root = original contacted NAV receipt
head = WORLD recursion receipt
```

## Propose a transition

Dogram does not invent the new heading.

A caller supplies the proposed destination and the delta being carried forward:

```sh
python3 scripts/dogram_nav.py transition \
  .build/dogram-nav/trace.json \
  --to-heading "Repeat the disputed behavior under captured conditions before widening the claim." \
  --delta-summary "The recursive artifact is new but generated downstream, so it changes what should be tested next without counting as external confirmation." \
  --preserve "the upstream contradiction" \
  --preserve "the generated-downstream classification" \
  --preserve "the claim that the new artifact is not a second witness" \
  -o .build/dogram-nav/transition.json
```

Dogram emits:

```
status = proposed
```

Nothing is activated.

## NAV receives the path-preserving proposal

NAV now accepts the bounded Dogram transition:

```sh
python3 scripts/nav.py reorient \
  .build/dogram-nav/transition.json \
  -o .build/dogram-nav/reorientation.json
```

NAV emits:

```
static.nav-reorientation/v0
```

with:

```
from_heading
proposed_heading
transition_sha256
trace_ledger_sha256
world_recursion_sha256
preserved
reason
claim_limit
```

The status remains:

```
proposed
```

This is the authority split:

```
WORLD      classifies what the evidence can honestly be
DOGRAM     receipts the path by which that delta arrived
NAV        represents the proposed heading change
HUMAN /
LOCAL ACT  decides whether a consequential move actually occurs
```

## Same destination, different history

This is the central hostile test.

Two paths can both propose:

> Repeat the disputed behavior under captured conditions before widening the claim.

But if their trace ledgers differ, Dogram returns:

```
same_destination = true
same_trace = false
same_navigation = false
```

So destination text no longer collapses route history.

This matters because one route might have passed through:

```
independent contradiction
→ field experiment
→ mixed result
```

while another arrived at the same sentence through:

```
derived retelling
→ no independent contact
```

Those are not equivalent navigational states.

## Hostile controls

The test suite requires that:

1. the six-artifact trace verifies complete;
2. missing artifact material yields `incomplete`, not `invalid`;
3. mutated material with a stale digest yields `invalid`;
4. the transition remains bounded and does not embed the ledger;
5. same destination with different trace yields `same_navigation = false`;
6. identical destination and identical trace can yield `same_navigation = true`;
7. NAV emits a proposal, not a replacement;
8. NAV refuses a Dogram transition falsely marked `activated`;
9. repeated trace artifacts are refused.

## What Dogram is not doing

Dogram does not decide:

- whether the WORLD evidence is true;
- whether the proposed heading is good;
- whether the heading should be activated;
- whether the declared artifact sequence proves external causality.

Its role is narrower:

> **DO THE PATH ACCOUNTING. SHOW THE DELTA. KEEP THE RECEIPT. DO NOT DECIDE WHAT IT MEANS.**

That is why it fits between WORLD and NAV instead of replacing either one.

## The loop after this slice

```
NAV
  ↓
WITNESS
  ↓
WORLD
  ↓
MAKE GROUND
  ↓
WITNESS
  ↓
WORLD
  ↓
DOGRAM
  path ledger
  transition receipt
  ↓
NAV
  reorientation proposal
```

The loop now does more than remember.

It can propose a changed heading **because of what happened**, while keeping the route to that change inspectable.

## Claim limit

The current source chain remains an executable contract example, not a claim about a substantive real-world experiment.

This slice proves a path-preservation mechanism:

> a recursive evidence delta can become a proposed navigational carrier without impersonating an origin and without erasing the path that produced it.

## Next door

The next useful pressure test is not another organ.

It is **two cycles**.

Run the reorientation through a second NAV encounter and ask whether Dogram can preserve:

```
heading A
→ cycle 1
→ heading B
→ cycle 2
→ heading C
```

with bounded local transition capsules and an addressable shared trace ledger.

That would test whether the Bridge runtime can accumulate navigational history without either forgetting the past or recursively copying the whole past into every future move.
