# WITNESS RE-ENTRY → WORLD 001

## Status

This slice tests the first recursion gate after the Bridge Layer loop closed.

The question is:

> Can evidence be genuinely new without pretending it came from nowhere?

Input:

```
static.witness-reentry/v0
```

Intermediate:

```
static.world-recursive-candidate/v0
```

Output:

```
static.world-recursion-receipt/v0
```

## Core law

```
NEW ≠ INDEPENDENT.
FRESH CAPTURE ≠ ANCESTRYLESS CAPTURE.
NEW SOURCE ≠ SECOND WITNESS.
```

The re-entered evidence artifact has:

- its own source fingerprint;
- a fresh capture event;
- new recorded content;
- preserved upstream generation ancestry.

All four can be true at once.

## Why the old two-axis model was no longer enough

The first WORLD crossing separated:

1. lineage;
2. claim relation.

That works for comparing sources already in the world.

The recursive loop introduces another question:

> Is this artifact new?

Newness is not the same thing as independence.

The executable recursive WORLD path therefore tracks:

### Novelty

```
new_artifact
```

### Observation status

```
fresh_capture
```

### Generation lineage

```
generated_downstream
```

### Independence

```
not_independent_by_generation
```

### Relation to upstream evidence

```
aligns_primary
aligns_candidate
mixed
inconclusive
```

The axes are deliberately separate.

## The recursive candidate

WITNESS re-entry already preserves:

- the new evidence artifact fingerprint;
- the MAKE GROUND receipt fingerprint;
- the MAKE GROUND plan fingerprint;
- the original WORLD primary source fingerprint;
- the original WORLD candidate source fingerprint.

WORLD converts that bundle into:

```
static.world-recursive-candidate/v0
```

The durable fixture is:

```
examples/world-recursive-candidate.from-reentry.json
```

For the current example:

```
novelty_status = new_artifact
observation_status = fresh_capture
relation_to_upstream = mixed
independence_status = not_independent_by_generation
independence_claim = false
```

## Why the new hash does not create a second witness

The new evidence artifact has a different SHA-256 from both upstream WORLD sources.

That establishes artifact distinctness.

It does not establish evidentiary independence.

The artifact exists because:

1. the upstream sources disagreed;
2. WORLD preserved that disagreement;
3. MAKE GROUND selected a reversible field intervention;
4. the intervention created conditions for a fresh capture;
5. the capture produced the new artifact.

So the source is new.

The generation path is not unrelated.

WORLD therefore classifies it as:

```
lineage_class = generated_downstream
novelty_status = new_artifact
observation_status = fresh_capture
independence_status = not_independent_by_generation
counts_as_second_witness = false
```

## Run the recursion gate

Create the recursive candidate:

```sh
mkdir -p .build/world-recursion

python3 scripts/world.py candidate-from-reentry \
  examples/make-ground-to-witness.reentry.json \
  -o .build/world-recursion/candidate.json
```

Classify it:

```sh
python3 scripts/world.py classify-recursive \
  .build/world-recursion/candidate.json \
  -o .build/world-recursion/receipt.json
```

Inspect:

```sh
python3 scripts/world.py inspect \
  .build/world-recursion/receipt.json
```

The inspection should report:

```
lineage_axis = generated_downstream
novelty_axis = new_artifact
observation_axis = fresh_capture
independence_status = not_independent_by_generation
counts_as_second_witness = false
upstream_ancestry_preserved = true
truth_claimed = false
```

## What this fixes

Without this gate, a recursive system could accidentally manufacture its own apparent confirmation.

The sequence would look superficially legitimate:

```
old claim
→ experiment
→ new file
→ count new file as new witness
→ confidence rises
```

But if the experiment itself was generated downstream of the old claim, the new source has a meaningful ancestry relationship to that claim.

That does not make the new evidence worthless.

It means its evidentiary role must be described honestly.

## The crucial distinction

A generated-downstream artifact can do real work.

It can:

- expose a condition neither old source recorded;
- narrow a disagreement;
- reveal a mixed result;
- create a better reproduction fixture;
- produce a correction;
- generate a new question;
- become the source of another bounded action.

What it cannot do merely by existing is erase the ancestry that caused it to be generated.

## Hostile controls

The tests require that:

1. WORLD explicitly accepts WITNESS re-entry.
2. re-entry generates the exact durable recursive-candidate fixture.
3. ground-receipt, plan, and both upstream WORLD fingerprints survive automatically.
4. the new artifact keeps its own distinct fingerprint.
5. newness and fresh capture do not create an independence claim.
6. the upstream `mixed` relation survives into WORLD.
7. a recursive candidate claiming independence is refused.
8. collapsed upstream WORLD ancestry is refused.
9. WORLD inspection keeps novelty and independence as different axes.
10. re-entry missing its intervention lineage is refused.
11. the recursive WORLD receipt exactly preserves `counts_as_second_witness = false`.

## The runtime now distinguishes three different ideas

### Same

The identical artifact or source path.

### New

A distinct artifact or observation event.

### Independent

A source whose relevant evidence path does not descend from the thing it is being used to independently check.

These are no longer synonyms.

```
SAME ≠ NEW
NEW ≠ INDEPENDENT
INDEPENDENT ≠ CORRECT
```

## The loop after this gate

```
NAV
  ↓
WITNESS
  ↓
WORLD
  ↓
MAKE GROUND
  ↓
WITNESS RE-ENTRY
  ↓
WORLD RECURSION GATE
      ├─ new artifact: YES
      ├─ fresh capture: YES
      ├─ generated downstream: YES
      └─ independent second witness: NO
```

This lets the loop learn from its own experiments without hallucinating external confirmation.

## Claim limit

The evidence artifact remains an example contract fixture.

This slice does not prove the artifact's substantive claim.

It proves that an executable recursive system can distinguish **novel evidence** from **independent evidence** while preserving the ancestry that generated the novelty.

## Next door

The next move is less architectural and more revealing:

> What happens when the recursive artifact changes the next NAV heading?

That would connect the re-entered, ancestry-aware evidence back to active navigation:

```
WORLD recursion receipt → NAV reorientation
```

The loop would then not merely preserve history.

It would steer differently because of it.
