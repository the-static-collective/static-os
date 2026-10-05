# CONDITION FIELD / WORLD FORK 001

## Status

This slice turns PR #33's two-contact residual witness tension into a three-world experimental field.

The input is one verified `static.world-residual-witness-update/v0` in which contact history remains plural and verdict remains withheld.

The output is not a third linear contact.

It is a fork:

```
                         condition alpha -> result alpha
                       /
residual checkpoint --- condition beta  -> result beta
                       \
                         condition gamma -> result gamma
```

Each branch is owner-local, explicitly admitted, and changes exactly one named condition.

## Core laws

```
EXPERIMENT != LINE.
CONDITION SPLIT != CAUSE.
FORK != CONFLICT.
RECOMBINATION != CONSENSUS.
RESULT != ENDPOINT.
```

## Sovereign condition worlds

Each `static.condition-world-branch/v0` binds:

- the exact original witness field;
- the exact residual two-contact update;
- one branch identity;
- one sovereign owner;
- one explicit local admission;
- exactly one named condition change;
- the history that must remain preserved;
- an optional non-executable Mineral WANT.

The three-world postbag requires distinct owners and distinct condition names.

No branch inherits authority from a sibling.

A no-op condition change is refused.

## Optional Mineral WANT

A condition branch may carry a bounded request-shaped reference:

```
status = requested
authorization = none
```

This is deliberately compatible with the newer GHoT Mineral direction without pretending Static OS can execute GHoT work.

A branch without a Mineral WANT cannot later attach a Mineral artifact address.

```
WANT != AUTHORIZATION.
```

## Returns and refusal

A branch may return:

```
status = contacted
outcome_relation = corroborates | contradicts | corrects
observation = ...
residue = ...
```

or honestly refuse:

```
status = refused
outcome_relation = null
observation = ""
residue = ...
```

Refusal is returned to the field as residue.

It is not ranked below successful contact and it is not erased.

## Rankless postbag

The three returns enter `static.condition-postbag/v0`.

The postbag requires exactly one result from every condition world and hard-codes:

```
return_order_ranked = false
all_returns_held = true
```

Serialization is deterministic and independent of input order.

This mirrors the newer reLATTE post-office law structurally:

```
HOLD ALL.
RANK NONE.
```

but this branch does not claim a real reLATTE crossing.

## Dogram condition association

Dogram receives the postbag plus the addressed branch/result bodies.

It emits `static.dogram-condition-association/v0`.

For each world it preserves only:

- condition name;
- changed-to value;
- contacted/refused status;
- returned relation outcome.

It then reports the distinct observed relation set.

Example first specimen:

```
ambient_temperature -> corroborates
sampling_interval   -> contradicts
observer_blinding   -> corrects
```

Dogram may therefore state:

```
split_detected = true
```

but must also state:

```
causal_claimed = false
ranking_used = false
```

The runtime is explicitly forbidden from converting:

```
condition changed
+
outcome changed
```

into:

```
condition caused outcome
```

## Incomplete field

If one condition world refuses, the postbag still contains all three returns.

Dogram then marks:

```
status = incomplete
```

rather than deleting the refusal or ranking the remaining two worlds.

A recombinant frontier can still preserve all three parent returns in HOLD.

## Recombinant frontier

The three return artifacts are compacted into:

`static.condition-recombinant-frontier/v0`

The frontier carries:

- original field address;
- residual update address;
- postbag address;
- Dogram association address;
- exactly three parent result addresses;
- deterministic frontier root.

It hard-codes:

```
parent_count = 3
parent_bodies_embedded = false
canonical_parent_selected = false
status = held
```

This borrows the grammar of GrO's newer recombinant graph frontier without claiming GrO room admission.

The three parents remain parents.

No result is promoted to canon.

## Hostile controls

The tests require that:

1. three sovereign worlds use distinct owners;
2. each world changes one distinct named condition;
3. branch admission is explicit;
4. no-op condition changes are refused;
5. the postbag holds exactly three returns and ranks none;
6. postbag identity is invariant to return ordering;
7. duplicate owners are refused;
8. duplicate condition names are refused;
9. Mineral WANT carries no execution authority;
10. a branch without WANT cannot claim a Mineral artifact;
11. Dogram may report a split but never causality;
12. causal-claim laundering is refused;
13. refusal remains a held incomplete return rather than failure or erasure;
14. the recombinant frontier carries exactly three distinct parents;
15. no canonical parent is selected;
16. no parent body is embedded;
17. frontier identity is invariant to input ordering;
18. missing world returns are refused;
19. results cannot address unknown branches.

## First specimen

The first executable specimen deliberately returns three different relation outcomes.

That is not treated as experimental failure.

It is a richer field.

```
same residual history
+
three one-condition worlds
+
three different returned relations
=
condition-associated split
```

not:

```
three votes
```

and not:

```
three causal proofs
```

## Cross-project boundary

This slice is designed to compose with the newer growth but does not impersonate it.

- GHoT compatibility: optional Mineral WANT/artifact addresses only.
- reLATTE compatibility: rankless postbag grammar only.
- GrO compatibility: compact multi-parent frontier grammar only.

Live cross-repository execution remains a separately owned crossing.

## Result

The witness architecture is no longer forced into a linear sequence of increasingly authoritative contacts.

It can fork one unresolved history into multiple lawful experimental worlds, preserve divergent outcomes, and recombine them as new held ground.

```
CONTRADICTION
-> WORLD FORK
-> DIFFERENT CONDITIONS
-> DIFFERENT CONTACTS
-> HOLD ALL
-> DOGRAM ASSOCIATION
-> MULTI-PARENT FRONTIER
-> NEW GROUND
```

The experiment becomes a graph.

## Claim limit

All branch contacts and Mineral artifact references in this specimen are contract fixtures. The runtime verifies structure, lineage, non-ranking, and non-collapse. It does not prove external execution, external verification, or causal truth.

## Next pressure

The frontier is now a new multi-parent ground object.

The next question is whether three sovereign localities can independently admit that same frontier and project different lawful affordances without changing the frontier itself.

That would connect this Static OS condition field directly to the newer GrO law:

```
SAME SEED != SAME LOCAL AFFORDANCE.
```
