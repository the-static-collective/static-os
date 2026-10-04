# EXTERNAL WITNESS FIELD 001

## Status

This slice extends one independently qualified external witness into a plural external witness field without collapsing plurality into majority vote.

Inputs:

- individually qualified `static.world-external-witness-receipt/v0`
- complete pairwise `static.external-witness-pair-audit/v0`

Outputs:

- `static.external-witness-field/v0`
- `static.world-external-witness-field-receipt/v0`

## Core laws

```
PLURAL WITNESSES ≠ MAJORITY VERDICT.
INDIVIDUAL INDEPENDENCE ≠ INTER-WITNESS INDEPENDENCE.
COUNT ≠ WEIGHT.
DISAGREEMENT ≠ FAILURE.
CONVERGENCE ≠ TRUTH.
```

## Why individual witness status is not enough

Two sources may each be independent of the composed-history source and still depend on each other.

Examples:

- shared upstream source
- shared operator
- coordinated capture
- jointly selected sample

Therefore a plural witness field requires a second layer of provenance audit between every pair of admitted external witnesses.

For N witnesses, the field requires:

```
N × (N - 1) / 2
```

pair audits.

Three witnesses require three pair audits.

Four require six.

No missing pair may be inferred.

## Pairwise criteria

Each pair audit separately checks:

- shared source ancestry
- operator overlap
- capture coordination
- selection coordination

A pair passes only when all four support separation.

Unknown evidence keeps pairwise independence unknown.

Any failed criterion prevents the field from being classified as an independent plurality.

## Field states

### independent plurality + one relevant relation

If all pair audits pass and all relevant witnesses have the same relation:

```
field_state = convergence_without_verdict
```

### independent plurality + conflicting relevant relations

If all pair audits pass and the field contains, for example, corroboration plus contradiction:

```
field_state = disagreement_preserved
```

### independent plurality + unrelated material

```
field_state = mixed_relevance
```

### pairwise independence unresolved or failed

```
field_state = plurality_not_established
```

The individually qualified source receipts remain valid; only the stronger plural-independence claim is withheld.

## No voting rule

Relation counts are stored:

```
corroborates
contradicts
corrects
unrelated
```

But the runtime hard-codes:

```
majority_rule_used = false
verdict_status = withheld
```

A 2–1 split is not a verdict.

A 3–0 split is not a truth claim.

The counts describe field topology only.

## First hostile specimen

Three individually qualified, pairwise independent witnesses:

- witness A: corroborates
- witness B: corroborates
- witness C: contradicts

WORLD returns:

```
plurality_status = independent_plurality_candidate
field_state = disagreement_preserved
relation_counts.corroborates = 2
relation_counts.contradicts = 1
majority_rule_used = false
verdict_status = withheld
```

This is a healthy field, not a failed consensus.

## Hostile controls

The tests require that:

1. three pairwise independent witnesses may disagree without a verdict;
2. unanimous corroboration remains convergence without truth;
3. shared operator or ancestry blocks independent-plurality status;
4. unknown pairwise ancestry blocks independent-plurality status;
5. every unordered witness pair must be audited;
6. an individually unqualified source cannot enter the field;
7. relation-count majority cannot be relabeled as a verdict;
8. unrelated evidence remains visible as mixed relevance;
9. pair audits cannot self-certify;
10. field serialization is order invariant;
11. duplicate witness sources are refused;
12. inspection allows disagreement and claims no truth;
13. relation counts must exactly match witness count.

## Result

WORLD can now preserve a field where genuinely independent witnesses disagree.

That is stronger than either:

```
consensus = truth
```

or:

```
disagreement = failure
```

The field remains corrigible because disagreement is carried forward as structure rather than crushed into a score.

## Claim limit

This is a structural contract specimen.

Individual and pairwise audit evidence fingerprints are declared, not externally authenticated by this runtime.

No witness count determines truth, evidentiary weight, or final authority.

## Next pressure

The next useful question is not more witnesses.

It is:

> What should navigation do with a healthy independent witness field that contains unresolved disagreement?

That suggests a new crossing:

```
external witness field → DOGRAM / NAV
```

not to choose the majority, but to identify the smallest next move capable of discriminating between live independent witness paths.
