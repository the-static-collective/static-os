# WORLD → MAKE GROUND CROSSING 001

## Status

This slice extends the executable Bridge relay:

```
NAV → WITNESS → WORLD → MAKE GROUND
```

Inputs:

```
static.world-receipt/v0
+
static.field-profile/v0
```

Outputs:

```
static.ground-plan/v0
static.ground-receipt/v0
```

MAKE GROUND does not decide which witness is correct.

It accepts an unresolved independent contradiction or correction and asks a different question:

> What reversible change to the substrate would make better evidence easier to produce, preserve, compare, and repeat?

## Core laws

```
TERRAFORMING ≠ TOTAL DESIGN.
UNCERTAINTY ≠ PARALYSIS.
INTERVENTION ≠ VERDICT.
FERTILITY ≠ CONFIRMATION.
GROUND ≠ OUTCOME.
```

## Why this crossing exists

WORLD can now identify a candidate second evidence path without claiming truth.

That creates a practical problem.

A system can preserve uncertainty perfectly and still become inert.

MAKE GROUND exists to keep uncertainty from becoming paralysis without allowing action to masquerade as adjudication.

Its move is not:

> choose a side.

Its move is:

> change the field so another useful observation becomes cheaper, clearer, more repeatable, or easier to preserve.

## The field profile

MAKE GROUND does not autonomously invent an intervention.

A human or local process supplies a field profile containing:

- the live problem;
- current capabilities;
- constraints;
- a preserve set;
- reversible levers;
- a selected lever;
- observation channels;
- a selected observation channel.

That means the runtime transforms an explicitly selected local possibility.

It does not silently become a planner with broad external authority.

## Reversibility is structural

Every selectable lever must contain both:

```
change
rollback
```

If the selected lever has no rollback path, the runtime refuses the plan.

This is the first protection against using uncertainty as justification for uncontrolled redesign.

## Evidence fertility

The plan is evaluated by what the field becomes able to do, not by which source appears to win.

The current fertility targets are:

- produce a reusable evidence artifact;
- make another comparison easier to repeat;
- preserve enough context for later WITNESS intake.

That means all four observation relations remain valid:

```
aligns_primary
aligns_candidate
mixed
inconclusive
```

None of them automatically becomes a truth verdict.

## Example crossing

The upstream WORLD receipt is:

```
examples/world-receipt.independent-contradiction.json
```

The example field profile is:

```
examples/make-ground.field-profile.json
```

The field contains a software reproduction disagreement.

The selected reversible lever is:

> Add a test-only reproduction fixture that records environment, exact inputs, raw outputs and exit status.

Rollback:

> Remove the fixture and workflow hook while preserving the resulting evidence artifacts and receipts.

The selected observation channel is a fresh isolated run whose environment manifest is captured with the result.

The generated example plan is:

```
examples/make-ground.plan.json
```

## Run the crossing

Validate the packet:

```sh
python3 scripts/make_ground.py validate
```

Create a plan:

```sh
mkdir -p .build/ground

python3 scripts/make_ground.py plan \
  examples/world-receipt.independent-contradiction.json \
  examples/make-ground.field-profile.json \
  -o .build/ground/plan.json
```

The program stops there.

It does not install the fixture, edit the field, run the experiment, or claim a result.

A person or another explicitly authorized local process performs the bounded field change.

After observation:

```sh
python3 scripts/make_ground.py observe \
  .build/ground/plan.json \
  --relation mixed \
  --observed "The fresh fixture reproduced part of each report under different captured conditions." \
  --evidence-artifact raw-run-001.json \
  --evidence-artifact environment-001.json \
  --new-capability "repeat the disputed behavior with an environment manifest" \
  --new-capability "compare raw outputs across declared environments" \
  --repeatability-changed \
  --comparison-changed \
  --maintenance-note "The fixture adds a small test-only maintenance burden." \
  -o .build/ground/receipt.json
```

Inspect:

```sh
python3 scripts/make_ground.py inspect \
  .build/ground/receipt.json
```

The inspection reports:

```
truth_claimed = false
reentry_target = WITNESS
```

## The loop closes

This is the important part.

MAKE GROUND does not terminate the evidence process.

Its output is deliberately designed to become new source material:

```
NAV
  ↓
WITNESS
  ↓
WORLD
  ↓
MAKE GROUND
  ↓
new evidence artifact + ground receipt
  ↓
WITNESS
```

The relay is therefore no longer linear.

It has become a corrigible loop.

The field can change.

The changed field can answer.

The answer becomes source.

The source can be witnessed without erasing its ancestry.

## Hostile controls

The test suite requires that:

1. MAKE GROUND keeps `TERRAFORMING ≠ TOTAL DESIGN`.
2. A derived source cannot trigger this independent-disagreement crossing.
3. Agreement alone cannot trigger this crossing.
4. The selected reversible lever must actually exist.
5. A plan must include rollback.
6. A plan must keep `truth_claimed = false`.
7. An observation must preserve at least one evidence artifact.
8. A ground receipt measures new capability rather than truth.
9. The plan fingerprint changes if the intervention changes.
10. The resulting receipt explicitly returns to WITNESS.

## What the example means

The example observation is intentionally:

```
mixed
```

That is not a compromise answer.

It demonstrates something stronger:

> The intervention remains useful even when reality refuses to choose one of the source stories cleanly.

The field gained two capabilities:

- repeat the disputed behavior with an environment manifest;
- compare raw outputs across declared environments.

That is a fertility gain independent of whether either original source becomes vindicated.

## Claim limit

This slice does not perform the field intervention.

It does not prove that the example reproduction fixture would resolve the disagreement.

It does not make MAKE GROUND an experiment designer with unrestricted authority.

It does not turn a WORLD independent candidate into established truth.

It proves one narrower crossing:

> An unresolved independent disagreement can be transformed into a reversible evidence-fertility plan whose success is measured by increased field capability rather than confirmation of a preferred claim.

## The architecture now

```
NAV          asks: Where are we going, and what can surprise us?
WITNESS      asks: What did the source actually record?
WORLD        asks: Is this another evidence path?
MAKE GROUND  asks: What small field change would make the next answer easier to obtain?
```

Then the field answers and the result returns to WITNESS.

The executable Bridge Layer now has its first full re-entry cycle.

## Next door

The next powerful test is **re-entry**, not another new packet.

Take:

```
static.ground-receipt/v0
```

plus one captured evidence artifact and feed it back into WITNESS.

If WITNESS can preserve:

- the original NAV ancestry;
- the WORLD disagreement;
- the MAKE GROUND intervention;
- the new observation;
- the new interpretation;
- and the claim limit

without flattening them,

then the system will have completed one entire executable recursive composition:

```
source → action → witness → world → ground → new source
```
