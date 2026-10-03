# COMPOSED NAV CONTACT → WITNESS 001

## Status

This slice closes the source boundary for the first NAV cycle whose starting ground was itself composed history.

Input:

`static.nav-composed-cycle-ledger/v0`

Output:

`static.witness-composed-intake/v0`

## Core laws

```
SOURCE ORIGIN ≠ SOURCE CONTENT.
NEW CONTACT ≠ INDEPENDENT CONFIRMATION.
PROVENANCE SIDECAR ≠ OBSERVATION TEXT.
COMPOSED GROUND ≠ SOURCE CLAIM.
```

## Crossing shape

The adapter first verifies the complete composed-origin NAV cycle.

It then extracts the fresh contacted `static.nav-receipt/v0` and sends that receipt through the existing ordinary `WITNESS.intake_nav()` path unchanged.

Only after ordinary WITNESS classification succeeds does the adapter attach a separate addressable provenance sidecar.

The four ordinary NAV claim classes remain exactly:

- source_record
- derivative_interpretation
- orientation_proposal
- source_limit

## Provenance sidecar

The sidecar preserves addresses for:

- composed cycle
- composed origin
- admitted weave generation
- weave admission
- weave capsule
- typed parent set
- weave ledger
- root cycle
- relation kinds

The relation kinds remain:

`branch_continuation + open_branch`

None of those values are inserted into the source observation text.

## What WITNESS may establish

WITNESS may establish that a fresh contacted NAV artifact was ingested, that its ordinary claim classes survived, and that the address of the composed origin remains available beside it.

WITNESS does not establish that the fresh contact independently verifies the composed history, that the composed orientation was correct, that the still-open branch was closed, or that the deeper typed provenance graph has been independently re-audited.

## Hostile controls

The tests require exact equality between the composed intake records and ordinary WITNESS intake records; preservation of all typed provenance addresses; source/generation hash distinction; refusal of incomplete cycle ledgers; refusal of mutated contacts; refusal of origin/generation substitution; preservation of the open branch; and refusal of relation-kind collapse.

## Result

The loop can now produce a genuinely new source from composed ground without letting the source story absorb the ground that oriented it.

```
history
→ braid
→ typed weave
→ explicit admission
→ new NAV ground
→ fresh contact
→ WITNESS
```

The source remains ordinary.

The origin remains addressable.

## Next pressure

Send this `static.witness-composed-intake/v0` into WORLD.

WORLD must answer a harder question than before:

> Is the fresh contact independent of the composed history that oriented the experiment, or only novel relative to it?

That is the next ancestry boundary.
