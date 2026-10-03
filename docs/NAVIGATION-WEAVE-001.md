# NAVIGATION WEAVE 001

## Status

This slice composes two lawful navigation relations without erasing which grammar produced each parent.

Starting braid:

Heading B -> Branch C1
Heading B -> Branch C2

Then:

Branch C1 -> continued Heading D
Branch C2 remains open

The weave may now refer to both D and the still-open C2 while preserving that one parent relation is a branch continuation and the other is an open branch.

## Core laws

HEAD ADDRESS ≠ RELATION TYPE.
CONTINUATION ≠ OPEN BRANCH.
COMPOSITION ≠ MERGE.
WEAVE ≠ RANKING.
WEAVE PROPOSAL ≠ ADMISSION.
HASH CONSISTENCY ≠ RELATION-TYPE VALIDITY.

## Typed parents

The weave parent set has exactly two relation kinds in this first specimen:

branch_continuation
open_branch

Each descriptor carries kind, head digest, heading, and root-cycle digest.

The descriptor set is canonically sorted by (kind, head_digest). Canonical ordering is serialization only; it is not priority or temporal precedence.

## Verifier dispatch

A branch_continuation parent must verify through the continuation grammar and retain the branch digest it continued from.

An open_branch parent must verify through the braid grammar and still exist as an admitted branch in the original braid.

If a digest is present under the opposite relation grammar, the verifier returns parent_kind_mismatch rather than treating the address as sufficient.

This imports Dogram's LINEAGE-WEAVE law:

THE ADDRESS TELLS YOU WHERE. THE TYPE TELLS YOU HOW TO READ THE LINK.

## Bounded weave capsule

The weave result remains a proposal with only:

schema
weave_id
parent_set_sha256
root_cycle_digest
proposed_heading
relation_kinds
status
claim_limit

It does not embed either branch, the braid, the continuation history, or the base navigation spine.

## First specimen

Continued parent:

Use the external observation to test whether the captured condition split generalizes.

Still-open sibling:

Hold the claim narrow and reproduce the condition split in a second environment.

Proposed weave heading:

Compare the continued external-observation path with the still-open second-environment path before choosing another move.

The weave does not close either parent and does not activate the proposed heading.

## Hostile controls

The tests require that:

1. both typed parents verify under their own relation grammar;
2. relation kinds survive inspection;
3. base spine and braid remain unchanged;
4. swapping relation types and correctly re-hashing still fails with parent_kind_mismatch;
5. missing continuation material is incomplete, not invented as severance;
6. mutated continuation material is invalid;
7. a continued branch cannot simultaneously impersonate the still-open sibling;
8. the typed parent set is canonical;
9. the weave capsule stays bounded;
10. the weave remains proposed, not admitted;
11. collapsing both parents to one relation kind is invalid.

## Why this matters

A graph can preserve addresses and still erase grammar.

If a later system sees only two head hashes, it cannot know whether each head arrived through ordinary continuation, branching, correction, merge, or some other relation.

Typed weave preserves the grammar of each edge while allowing later composition across them.

That means plural history can become material for a new possibility without rewriting all prior relations as the same kind of parenthood.

## Claim limit

This is a structural navigation specimen. It does not rank branches, prove either parent correct, establish causal history from graph topology, or activate the proposed weave heading.

## Next pressure

The next useful test is typed re-entry into NAV: can the weave proposal become an explicitly admitted heading while retaining the typed parent set as its provenance carrier?

That would make composition itself navigable without flattening the relations it composed.