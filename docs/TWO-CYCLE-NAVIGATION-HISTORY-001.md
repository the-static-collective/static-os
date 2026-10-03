# TWO-CYCLE NAVIGATION HISTORY 001

## Status

This slice pressure-tests the first repeated navigation loop:

Heading A → cycle 1 → Heading B → cycle 2 → Heading C

The question is whether two navigational generations can remain reconstructible without either forgetting cycle 1 or recursively embedding cycle 1 inside every object in cycle 2.

## Core laws

PROPOSAL ≠ ADMISSION.
ADMISSION ≠ TRUTH.
CONTINUITY ≠ RECURSIVE EMBEDDING.
NEW CYCLE ≠ REWRITTEN OLD CYCLE.
MISSING HISTORY ≠ PROVEN SEVERANCE.

## The admission seam

The previous slice ended at WORLD → DOGRAM transition → NAV reorientation proposal. A proposal is not automatically the next active heading. This slice therefore adds an explicit local admission artifact: static.nav-heading-admission/v0.

The history runtime does not mint that authority. It only verifies that the supplied admission matches the Dogram transition and NAV proposal exactly.

Authority split:

DOGRAM receipts the path.
NAV proposes the heading.
LOCAL authority admits the heading.
HISTORY receipts continuity.

## Fixed-shape cycle capsules

Each admitted generation becomes static.navigation-cycle-capsule/v0 with exactly ten fields: schema, cycle_index, from_heading, admitted_heading, root_cycle_digest, parent_cycle_digest, trace_ledger_sha256, transition_sha256, reorientation_sha256, admission_sha256.

Cycle 0 has ten keys. Cycle 1 has ten keys. Cycle 200 would still have ten keys.

The growing past lives in a separate content-addressed navigation-history ledger with buckets for cycles, traces, transitions, reorientations, and admissions.

## Continuity rule

When cycle 2 is appended, the runtime requires:

cycle_2.from_heading == cycle_1.admitted_heading

A proposed Heading B is insufficient. Cycle 2 must be able to show that Heading B was explicitly admitted at the end of cycle 1.

## Contract specimen

Cycle 1 runs the existing six-artifact path through NAV → WITNESS → WORLD → MAKE GROUND → WITNESS → WORLD, then Dogram proposes Heading B and a test-local authority admits it.

Cycle 2 uses a distinct six-artifact contract path beginning from Heading B, then Dogram proposes Heading C and a second explicit admission records it.

The verified history therefore reconstructs A → B → C while both cycle capsules keep the same fixed shape.

## Verification states

complete: all declared capsules and referenced artifacts are present and internally consistent.

incomplete: witness material is absent. Missing history is not treated as disproven history.

invalid: available material contradicts the declared history, such as stale digests, heading continuity mismatch, or a changed admission.

## Hostile controls

The tests require: two cycles verify complete; the heading path reconstructs A → B → C; local capsules stay fixed-shape; cycle 2 cannot begin anywhere except cycle 1's admitted heading; proposal without admission is refused; admission cannot change the proposed heading; missing parent history is incomplete; mutated transition is invalid; cycle traces are distinct; the root-cycle address remains stable; and appending cycle 2 does not rewrite cycle 1.

## Why this matters

One-cycle navigation can say where it went. Two-cycle navigation must prove that the second move actually began where the first move left it.

That is the beginning of navigational continuity.

## Claim limit

Both cycles are executable contract specimens, not claims of real-world experimental success. This slice proves a storage and verification contract for repeated navigation.

## Next pressure

The natural next pressure test is branching navigation: two lawful headings from the same admitted history. That would move the ledger from a lineage spine toward the Dogram braid problem.