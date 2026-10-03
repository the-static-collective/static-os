# MEASUREMENT PATH AUDIT 001

## Status

This slice audits the unresolved measurement-independence axis for a fresh WORLD contact whose experiment is already known to be selection-dependent on composed prior history.

Inputs:

- `static.world-composed-contact-candidate/v0`
- `static.measurement-path-audit/v0`

Output:

- `static.world-measurement-audit-receipt/v0`

## Core laws

```
MEASUREMENT INDEPENDENCE ≠ SELECTION INDEPENDENCE.
AUDIT PASS ≠ FULLY INDEPENDENT SOURCE.
EVIDENCE ADDRESS ≠ EVIDENCE AUTHENTICATION.
QUESTION ORIGIN ≠ ANSWER CHANNEL.
```

## Known before the audit

The source is already classified as:

```
new source artifact = yes
fresh world contact = yes
selection independence = not independent of orientation
measurement independence = unknown
independent confirmation = not established
```

The measurement audit is not allowed to rewrite that known selection ancestry.

## Criterion-based audit

The audit does not accept a bare declaration such as:

```
measurement_independent = true
```

Instead it requires four separately evidence-addressed criteria:

1. channel origin
2. capture control
3. result selection
4. operator relation

Passing statuses are:

```
channel_origin = preexisting_or_external
capture_control = not_controlled_by_orientation
result_selection = result_blind_capture
operator_relation = independent_or_automatic
```

Each criterion carries an evidence SHA-256.

The runtime does not claim those evidence artifacts are externally authenticated. It only refuses to treat the candidate source itself, or one of its orientation-ancestry artifacts, as self-certifying audit evidence.

## Three possible measurement outcomes

### All criteria pass

```
selection_independence = not_independent_of_orientation
measurement_independence = independent_candidate
evidence_role = selection_dependent_measurement_independent_candidate
counts_as_independent_confirmation = false
```

### No failures, one or more unknowns

```
measurement_independence = unknown
evidence_role = selection_dependent_measurement_unknown
```

### Any criterion fails

```
measurement_independence = not_independent
evidence_role = selection_and_measurement_dependent
```

In every case, known selection dependence survives unchanged.

## Why a passing audit is not full confirmation

A measurement path may be independent even though the experiment was selected because of prior composed history.

That is useful evidence, but it is not the same thing as a source whose question-selection path and measurement path are both independent.

So even the strongest current audit result keeps:

```
counts_as_independent_confirmation = false
```

## Hostile controls

The tests require that:

- all four criteria pass before measurement independence becomes an independent candidate;
- unknown criteria preserve the unknown state;
- a failed criterion marks measurement dependence;
- known selection dependence cannot be upgraded;
- the audit source must match the candidate source;
- the source cannot certify its own audit;
- orientation ancestry cannot impersonate audit evidence;
- a passing measurement audit still cannot count as fully independent confirmation;
- receipt role and independence classification must agree;
- relabeling an unknown audit as independent is refused;
- typed origin remains preserved;
- no truth claim is introduced.

## Result

The runtime can now represent:

```
selection-dependent
+
measurement-independent candidate
```

without collapsing that state into either:

```
fully independent
```

or:

```
fully dependent
```

This separates how the question arose from how the answer entered the world.

## Claim limit

The current audit specimen is a contract fixture. Evidence fingerprints are declared, not externally authenticated by this runtime.

## Next pressure

The remaining stronger evidence role would require independent selection as well as independently audited measurement.

That means the next boundary is not another upgrade of this source.

It is a comparison against a source whose question-selection path did not descend from the composed history at all.
