# WITNESS FIELD DISCRIMINATION CYCLE 001

## Status

This slice closes the loop from unresolved independent witness disagreement to an explicitly admitted discriminator contact and back into WORLD.

Flow:

```
witness field
→ Dogram minimum discriminator
→ NAV proposal
→ explicit local admission
→ one bounded NAV contact
→ WORLD non-destructive field update
```

## Core laws

```
NAV PROPOSAL ≠ ADMISSION.
AMBIGUITY REDUCTION ≠ WITNESS ERASURE.
CHALLENGED WITNESS ≠ FALSE WITNESS.
CONTACT SUPPORT ≠ FINAL VERDICT.
```

## Admission

The selected `static.nav-field-reorientation/v0` cannot execute by itself.

The admission adapter requires:

- the original witness field
- the WORLD field receipt
- the exact selected discriminator candidate
- the exact Dogram transition
- the exact NAV proposal
- an explicit local actor
- explicit acceptance

It then emits `static.nav-field-admission/v0`.

## Bounded contact

The admitted candidate becomes an ordinary NAV orientation and then an ordinary contacted NAV receipt.

A contact only counts as a discriminator result when its observation exactly matches one of the candidate's predeclared relation-path observations.

That prevents retrospective fitting of arbitrary observations to whichever witness path looks convenient afterward.

The bounded contact is additionally receipted as:

`static.field-discrimination-contact/v0`

## Non-destructive WORLD return

WORLD does not rewrite the original field.

Instead it emits:

`static.world-witness-field-update/v0`

The update preserves every original witness source digest and assigns only a contact-local state:

- `aligned_with_contact`
- `challenged_by_contact`
- `outside_discriminator_scope`

No witness is deleted.

The original claim relation is preserved beside the contact-local state.

## Ambiguity

The first specimen begins with two live relation paths:

```
corroborates
contradicts
```

The selected discriminator has one predeclared observable for each.

When one observation is encountered:

```
ambiguity_before = 2
ambiguity_after = 1
```

This is a narrowing of the current discriminator state, not a truth verdict.

Witness count is invariant:

```
witness_count_before = witness_count_after
all_witnesses_retained = true
```

## Majority inversion

The suite runs the return logic against both:

```
2 corroborate / 1 contradict
```

and:

```
1 corroborate / 2 contradict
```

If the observed discriminator relation is `contradicts`, both fields support `contradicts` for that contact.

The majority never controls the update.

## Preserved boundaries

The field update hard-codes:

```
majority_rule_used = false
verdict_status = withheld
```

It explicitly does not establish that:

- aligned witnesses are true
- challenged witnesses are false
- challenged witnesses should be deleted
- one contact permanently resolves the field
- witness counts may become authority

## Result

The loop can now actually learn from disagreement without rewriting its history.

A fresh contact may reduce what is currently ambiguous while preserving the witnesses that made the ambiguity visible in the first place.

```
DISAGREEMENT
→ DISCRIMINATING CONTACT
→ NARROWER FIELD
≠ DELETED HISTORY
```

## Claim limit

This is an executable contract specimen. The world-contact observation is supplied as a fixture and must match a predeclared discriminator outcome. The runtime does not prove that the contact was externally performed or that the observed path is substantively true.

## Next pressure

The next question is residual disagreement.

A challenged witness is still present.

Can the updated field generate a second discriminator targeted specifically at the challenged path, while preserving the first contact as history rather than treating it as a final answer?
