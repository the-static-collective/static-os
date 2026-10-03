# WITNESS → WORLD CROSSING 001

## Status

This slice extends the executable Bridge relay:

```
NAV → WITNESS → WORLD
```

Input:

```
static.witness-intake/v0
+
static.world-candidate/v0
```

Output:

```
static.world-receipt/v0
```

WORLD's job is not to decide which source is true.

Its first job is smaller:

> Determine whether the additional source has an evidence path distinct enough to count as a candidate second witness, without collapsing that question into whether the source agrees or disagrees.

## The two-axis correction

The original intuitive list mixed two different questions:

- same ancestor
- derived retelling
- independent observation
- contradiction
- correction

The executable version separates them.

### Axis A — lineage

```
same_artifact
derived_retelling
shared_ancestor
independent_candidate
lineage_unknown
```

This axis asks:

> Where did this source come from?

### Axis B — claim relation

```
corroborates
contradicts
corrects
unrelated
```

This axis asks:

> How does this source's claim relate to the primary claim?

These axes must remain separate.

An independent source can contradict.

A derived retelling can corroborate.

A derivative source can correct wording without becoming independent.

A distinct file can still have unknown ancestry.

## Core laws

```
MODEL ≠ WORLD.
SELF-CHECK ≠ INDEPENDENT CHECK.
MULTIPLE SOURCES ≠ MULTIPLE WITNESSES.
INDEPENDENCE ≠ CORRECTNESS.
CONTRADICTION ≠ INDEPENDENCE.
```

## Primary source

The primary side of this comparison is the WITNESS intake produced from the contacted NAV receipt:

```
examples/nav-to-witness.intake.json
```

WORLD uses the WITNESS intake's preserved source digest as the primary lineage anchor.

The runtime does not reinterpret NAV's observation text to decide independence.

It compares declared source paths.

## Candidate source contract

A WORLD candidate declares:

- its own source digest;
- channel type;
- ancestry roots;
- explicit derivation links;
- claim relation;
- claim text;
- basis for that relation classification;
- whether it is claiming independence.

The first supported channels are:

```
direct_observation
independent_measurement
document
retelling
derived_analysis
```

A direct observation or independent measurement with no declared dependency on the primary source may become:

```
independent_candidate
```

That word **candidate** is intentional.

WORLD still does not claim that the ancestry declaration is true.

## Example A — derived agreement

```
examples/world-candidate.derived-corroboration.json
```

This candidate agrees with the NAV source.

But it explicitly derives from that source.

WORLD therefore emits:

```
lineage_class = derived_retelling
claim_relation = corroborates
independence_status = not_independent
```

Agreement does not manufacture another witness.

## Example B — independent contradiction

```
examples/world-candidate.independent-contradiction.json
```

This candidate declares a direct observation through a different evidence path and contradicts the primary claim.

WORLD emits:

```
lineage_class = independent_candidate
claim_relation = contradicts
independence_status = independent_candidate
```

That does **not** mean the contradictory claim is true.

It means the system now has a candidate second evidence path capable of genuinely disagreeing.

The corresponding receipt is preserved at:

```
examples/world-receipt.independent-contradiction.json
```

## Run the crossing

Validate WORLD:

```sh
python3 scripts/world.py validate
```

Compare the derived corroboration:

```sh
mkdir -p .build/world

python3 scripts/world.py compare \
  examples/nav-to-witness.intake.json \
  examples/world-candidate.derived-corroboration.json \
  -o .build/world/derived.json
```

Compare the independent contradiction:

```sh
python3 scripts/world.py compare \
  examples/nav-to-witness.intake.json \
  examples/world-candidate.independent-contradiction.json \
  -o .build/world/independent.json
```

Inspect the result:

```sh
python3 scripts/world.py inspect \
  .build/world/independent.json
```

The inspection explicitly reports:

```
counts_as_second_witness = true
truth_claimed = false
```

Those two fields should be able to coexist.

That coexistence is the point.

## Refusal behavior

WORLD refuses a candidate that claims independence while declaring direct ancestry from the primary source.

It does not silently downgrade or politely ignore the contradiction.

The invalid claim is surfaced.

The runtime also preserves:

```
does_not_establish
```

including:

- the candidate source is correct;
- the primary source is correct;
- agreement proves truth;
- contradiction proves independence;
- the candidate ancestry has been externally audited.

## Hostile controls

The tests require that:

1. WORLD keeps `MODEL ≠ WORLD`.
2. A derived corroboration does not count as a second witness.
3. An independent candidate may contradict.
4. Contradiction does not create independence.
5. Correction does not create independence.
6. A false independence claim over a derived source is refused.
7. The same artifact cannot count twice.
8. Insufficient lineage remains unknown rather than being optimistically promoted.
9. Even a candidate second witness does not make WORLD claim truth.

## The executable relay now

```
NAV
  orient
  bounded move
  encounter
  receipt
      │
      ▼
WITNESS
  fingerprint
  classify source record
  preserve interpretation
  preserve claim limit
      │
      ▼
WORLD
  compare lineage
  compare claim relation
  refuse fake independence
  preserve truth uncertainty
      │
      ▼
independent-contact candidate
```

The first runtime asked:

> Did the loop encounter something?

The second asked:

> What can we honestly claim from the record of that encounter?

The third asks:

> Is this additional answer actually another evidence path?

That is a functioning reality mechanic.

## What this does not prove

This first WORLD slice does not cryptographically prove ancestry.

It relies on explicit lineage declarations and source digests.

It does not adjudicate which contradictory source is correct.

It does not yet recurse through arbitrary provenance graphs.

It does not automatically fetch outside evidence.

It does not promote a candidate source into truth.

It proves a narrower and necessary thing:

> Independence and agreement can be represented separately and enforced separately across an executable packet relay.

## Next door

The next strong move is **not another epistemic packet**.

The relay has enough evidence structure to cross into **MAKE GROUND**.

WORLD can hand forward a result such as:

```
independent_candidate + contradiction
```

MAKE GROUND can then ask:

> What is the smallest reversible change to the field that would make the disagreement easier to resolve?

That would connect truth-seeking back to action without letting uncertainty become paralysis:

```
NAV → WITNESS → WORLD → MAKE GROUND
```
