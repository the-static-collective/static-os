# MAKE GROUND → WITNESS RE-ENTRY 001

## Status

This slice closes the first executable Bridge Layer loop:

```
NAV → WITNESS → WORLD → MAKE GROUND → WITNESS
```

Inputs:

```
static.ground-receipt/v0
+
static.evidence-artifact/v0
```

Output:

```
static.witness-reentry/v0
```

The re-entry does not rewrite the loop as a single story.

It preserves a bundle.

## Core law

```
SOURCE ≠ STORY.
RETURN ≠ RESET.
NEW SOURCE ≠ ERASED ANCESTRY.
```

A new field observation becomes source material only if the path that produced it survives the return.

## Carrier correction

The previous MAKE GROUND receipt carried the ground-plan fingerprint but not the two WORLD source fingerprints directly.

That was not enough for self-contained re-entry.

This slice strengthens `static.ground-receipt/v0` with:

```
ancestry.ground_plan_sha256
ancestry.world_primary_source_sha256
ancestry.world_candidate_source_sha256
```

The receipt can now return to WITNESS without a hidden lookup to reconstruct the disagreement that caused the field intervention.

## Why the evidence artifact stays separate

The ground receipt records:

- what the field intervention reported;
- how the result was classified;
- what capability the field gained;
- what claim limit remained.

The evidence artifact carries the captured material itself.

Those are not the same source.

WITNESS fingerprints them separately:

```
ground_receipt.sha256
evidence_artifact.sha256
```

A mutation to either source changes its own fingerprint without rewriting the other.

## Re-entry records

The first re-entry preserves six records:

| Record | Claim class |
| --- | --- |
| ground observation | `source_record` |
| captured evidence artifact | `source_artifact` |
| observation relation | `derivative_interpretation` |
| fertility delta | `derivative_interpretation` |
| intervention / plan ancestry | `intervention_record` |
| combined claim limit | `source_limit` |

The runtime refuses a re-entry whose classes collapse.

In particular:

```
observed text ≠ observation relation
artifact ≠ interpretation
field capability ≠ upstream truth
```

## Declared-artifact gate

MAKE GROUND receipts already list their evidence artifacts.

WITNESS will only re-enter an artifact whose `artifact_id` appears in that list.

That prevents a plausible-looking side artifact from being attached after the fact without the ground receipt ever having declared it.

## Run the re-entry

Validate WITNESS:

```sh
python3 scripts/witness.py validate
```

Re-enter the MAKE GROUND result:

```sh
mkdir -p .build/reentry

python3 scripts/witness.py reenter \
  examples/make-ground.receipt.json \
  examples/reproduction-run.evidence.json \
  -o .build/reentry/witness.json
```

Inspect it:

```sh
python3 scripts/witness.py inspect \
  .build/reentry/witness.json
```

The inspection reports:

```
loop_closed = true
upstream_world_sources_preserved = true
independent_verification_claimed = false
```

That combination is the proof target.

The loop may close without pretending the new artifact has independently settled the old disagreement.

## Durable fixture

The generated re-entry is pinned at:

```
examples/make-ground-to-witness.reentry.json
```

The hostile test suite regenerates the re-entry from the ground receipt plus evidence artifact and requires exact equality with that fixture.

A future change to the crossing semantics therefore has to be explicit.

## What survives the full loop

The re-entry bundle retains:

### From NAV

The original primary source fingerprint that entered the first WITNESS crossing.

### From WITNESS

The principle that source record, interpretation, proposal and claim limit remain distinct.

### From WORLD

Both compared source fingerprints.

The later field intervention therefore still knows which two evidence paths generated the unresolved disagreement.

### From MAKE GROUND

The ground-plan fingerprint, field observation, fertility delta and claim limit.

### From the new field contact

A separately fingerprinted evidence artifact.

The result is not a single flattened history.

It is a traversable ancestry graph.

## Hostile controls

The re-entry tests require that:

1. the WITNESS packet explicitly declares MAKE GROUND re-entry;
2. the complete ground-plan and WORLD ancestry survives;
3. the new observation and its interpretation remain different claim classes;
4. an artifact not declared by the ground receipt is refused;
5. a ground receipt with mismatched plan ancestry is refused;
6. mutating the receipt changes the receipt fingerprint;
7. mutating the artifact changes the artifact fingerprint;
8. the new artifact is not silently upgraded into independent verification;
9. the upstream contradiction is not silently resolved;
10. the generated re-entry exactly matches the durable fixture;
11. inspection reports the recursive loop as closed.

## The first executable recursive composition

The system can now perform this shape:

```
SOURCE
  │
  ▼
NAV
  orient
  bounded move
  world contact
  receipt
  │
  ▼
WITNESS
  preserve source
  separate interpretation
  preserve claim limit
  │
  ▼
WORLD
  compare evidence paths
  separate lineage from agreement
  preserve unresolved contradiction
  │
  ▼
MAKE GROUND
  select reversible lever
  alter evidence-producing conditions
  record fertility delta
  produce new evidence
  │
  ▼
WITNESS
  preserve new source
  preserve old ancestry
  keep observation separate from interpretation
  │
  └──────────────► next comparison / next navigation
```

This is no longer merely a pipeline.

It is Recursive Systems Composition represented as an executable provenance loop.

## Claim limit

The evidence artifact in this slice is an explicitly labeled contract-test example.

This slice does not claim a real-world reproduction result.

It proves the runtime shape by which a real captured artifact can return through WITNESS without losing its ancestry or being promoted beyond its evidence class.

## What changed architecturally

Before re-entry, every packet crossing could be drawn as a line.

After re-entry, the important unit becomes the loop:

```
artifact
→ action
→ witness
→ world contact
→ substrate change
→ new artifact
→ witness
```

The return is not a reset.

The second WITNESS encounter has more ancestry available than the first.

That means the system can accumulate corrigible history without requiring a central narrative to overwrite previous states.

## Next door

The strongest next experiment is to let the re-entered evidence become a fresh WORLD candidate while preserving its ancestry automatically.

That would test whether WORLD can recognize:

```
new artifact
derived through MAKE GROUND from an older disagreement
```

without misclassifying it as an unrelated independent witness.

In other words:

> Can the loop remember that the evidence it generated is new evidence without pretending it came from nowhere?

That is the next recursion gate.
