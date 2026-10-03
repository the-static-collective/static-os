# EXTERNAL WITNESS GATE 001

## Status

This slice introduces the first source that may qualify as a genuinely external witness relative to the composed-history source.

Inputs:

- `static.world-composed-contact-candidate/v0`
- `static.external-witness-source/v0`
- `static.selection-path-audit/v0`
- `static.measurement-path-audit/v0`
- `static.external-witness-comparison/v0`

Output:

- `static.world-external-witness-receipt/v0`

## Core laws

```
INDEPENDENCE ≠ AGREEMENT.
INDEPENDENT WITNESS ≠ CORRECT WITNESS.
QUESTION ORIGIN ≠ ANSWER CHANNEL.
CLAIM RELATION ≠ PROVENANCE CLASS.
```

## Two audits, not one declaration

An external witness cannot simply declare itself independent.

Selection independence is audited through:

- question origin
- assignment origin
- hypothesis exposure
- sampling frame

Measurement independence is audited through:

- channel origin
- capture control
- result selection
- operator relation

Every criterion carries a supporting evidence fingerprint.

The runtime does not claim that those evidence artifacts are externally authenticated. It only enforces structural non-collapse and refuses self-certification.

## Independent witness candidate

A source qualifies only when both axes reach:

```
selection_independence = independent_candidate
measurement_independence = independent_candidate
```

Then WORLD may classify:

```
lineage_class = independent_external_candidate
independent_witness_status = independent_witness_candidate
counts_as_independent_witness = true
```

## Relation is separate

Once provenance status is known, WORLD separately records whether the external source:

- corroborates
- contradicts
- corrects
- is unrelated

A contradiction can therefore be just as independently sourced as corroboration.

For a qualifying external witness:

```
corroborates → independent_corroboration_candidate
contradicts → independent_contradiction_candidate
corrects → independent_correction_candidate
unrelated → independent_unrelated_source
```

None of those roles establish truth.

## Hostile controls

The tests require that:

1. both selection and measurement audits pass before independent-witness status;
2. corroboration cannot manufacture independence;
3. contradiction can remain fully independent;
4. relation type does not change provenance classification;
5. one failed measurement criterion blocks independent-witness status;
6. one unknown selection criterion blocks independent-witness status;
7. source and composed-source fingerprints remain distinct;
8. the external source cannot certify its own audit;
9. composed orientation ancestry cannot impersonate audit evidence;
10. both audits must address the external source;
11. the comparison must address both sources;
12. independent witness status does not establish truth;
13. inspection keeps independence separate from agreement;
14. relation-role laundering is refused.

## Result

WORLD can now represent:

```
composed-history source:
  selection-dependent
  measurement-independent candidate

external witness:
  selection-independent candidate
  measurement-independent candidate
```

without treating either provenance class as a verdict about which claim is true.

The stronger external role comes from provenance, not agreement.

## Claim limit

This is a structural contract specimen. The supporting audit fingerprints are declared rather than independently authenticated by this runtime.

## Next pressure

The next useful problem is plural external witnesses.

One independently selected and measured source is a witness candidate.

Two or more independent witnesses introduce a new question:

> Can WORLD preserve disagreement among independent witnesses without collapsing plurality into majority vote?

That would be the beginning of an external witness field rather than a single comparator.
