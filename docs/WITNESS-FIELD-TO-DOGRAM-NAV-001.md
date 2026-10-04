# WITNESS FIELD → DOGRAM → NAV 001

## Status

This slice turns a healthy independent witness field with unresolved disagreement into a bounded NAV reorientation proposal without choosing a majority side.

Inputs:

- `static.external-witness-field/v0`
- `static.world-external-witness-field-receipt/v0`
- one or more `static.field-discriminator-candidate/v0`

Dogram output:

- `static.dogram-field-transition/v0`

NAV output:

- `static.nav-field-reorientation/v0`

## Core laws

```
DISAGREEMENT ≠ SIDE SELECTION.
RELATION COUNT ≠ NAVIGATION WEIGHT.
SMALLEST NEXT MOVE ≠ MOST POPULAR CLAIM.
DISCRIMINATOR PROPOSAL ≠ PROOF OF DISCRIMINATION.
NAV PROPOSAL ≠ ADMISSION.
```

## Input gate

Dogram accepts only a field already classified by WORLD as:

```
plurality_status = independent_plurality_candidate
field_state = disagreement_preserved
majority_rule_used = false
verdict_status = withheld
```

Convergence, unresolved pairwise independence, shared lineage, or an already-issued verdict are refused at this crossing.

## Live relation paths

The runtime derives live relevant relation classes from the field topology.

Relevant classes are:

- corroborates
- contradicts
- corrects

Unrelated sources remain preserved in the field but are not treated as competing claim paths for this discriminator.

A candidate must cover every currently live relevant relation class.

Each path must declare a distinct observable result.

Two relation labels pointing to the same declared observation do not count as a discriminator.

## Structural minimization

Dogram does not invent the experiment.

Candidate moves are supplied locally and must declare:

- proposed heading
- bounded move
- relation paths and distinguishing observations
- preserve set
- aperture
- stop condition
- structural cost vector

The first cost vector is:

```
irreversible_steps
changed_variables
world_contacts
external_dependencies
```

Current boundedness requires:

```
irreversible_steps = 0
world_contacts = 1
```

Among qualifying candidates, Dogram selects lexicographically by the declared structural cost vector, with canonical content digest as the final deterministic tie-breaker.

Witness counts never enter the selection key.

## First hostile specimen

Witness field:

```
2 corroborate
1 contradicts
```

Candidate A:

```
changed_variables = 2
external_dependencies = 0
```

Candidate B:

```
changed_variables = 1
external_dependencies = 0
```

Candidate C:

```
changed_variables = 1
external_dependencies = 2
```

Dogram must select candidate B.

Then the witness majority is inverted:

```
1 corroborates
2 contradict
```

with structurally equivalent candidates addressing the new field.

Dogram must still select the same candidate identity.

Therefore:

```
2–1 and 1–2 do not steer NAV.
```

## Preserved invariants

The Dogram transition carries forward:

- independent witness disagreement
- majority rule remains unused
- WORLD verdict remains withheld
- typed composed origin remains addressable

The transition remains:

```
status = proposed
```

It does not execute the contact or establish that the declared discriminator will work in reality.

## NAV boundary

NAV receives only the selected Dogram transition and emits a bounded reorientation proposal.

The proposal carries:

- field address
- WORLD field receipt address
- Dogram transition address
- selected candidate address
- live relation classes
- proposed heading
- bounded move
- preserved invariants

NAV does not admit the heading automatically.

## Hostile controls

The test suite requires that:

1. the minimum structural-cost candidate is selected;
2. candidate order cannot alter selection;
3. flipping a 2–1 witness split to 1–2 cannot alter structural candidate identity;
4. every live relevant relation must be covered;
5. duplicated observations do not qualify as discrimination;
6. convergent witness fields are refused at the disagreement discriminator;
7. unresolved pairwise independence is refused;
8. candidates cannot smuggle majority weights;
9. WORLD's withheld verdict and no-majority laws survive the transition;
10. NAV output remains proposal-only;
11. candidates must address the exact field;
12. irreversible moves are refused.

## Result

A witness field can now do something more useful than converge or deadlock.

Independent disagreement becomes an aperture for a smaller question.

```
WORLD FIELD
   ↓
preserve disagreement
   ↓
DOGRAM
find minimum declared discriminator
   ↓
NAV
propose one bounded next contact
```

The minority does not lose.

The majority does not win.

The disagreement changes what is useful to ask next.

## Claim limit

Candidate costs and discriminating observations are declared structural contract inputs. This runtime does not externally prove their real-world cost or discriminating power.

## Next pressure

The next crossing is explicit admission and execution of the selected field-derived heading.

The harder question after that is whether the resulting fresh contact actually reduces the witness-field ambiguity without erasing witnesses whose path it fails to support.
