# NAV → WITNESS CROSSING 001

## Status

This slice proves the first executable **Bridge Packet to Bridge Packet** crossing.

Input:

```
static.nav-receipt/v0
```

Output:

```
static.witness-intake/v0
```

The crossing is intentionally narrow.

NAV says:

> I made a bounded move, recorded what I observed, interpreted a delta, and proposed a next heading.

WITNESS says:

> I can preserve that source exactly enough to inspect it without silently upgrading any of those fields into a stronger evidence class.

## The seam

The key law is:

> NAV WORLD-CONTACT CLAIM ≠ WITNESS INDEPENDENT VERIFICATION.

A contacted NAV receipt may honestly record an encounter. When WITNESS receives that receipt, the source artifact itself is what WITNESS can directly attest to.

WITNESS can establish that:

- the contacted NAV receipt exists as an ingested artifact;
- it contains a recorded observation;
- it contains a delta interpretation;
- it contains a next-heading proposal;
- it contains a claim limit.

That does **not** by itself establish that:

- the outside event occurred exactly as reported;
- the observation has been independently reproduced;
- the delta interpretation is correct;
- the proposed next heading should be followed.

This is not distrust of NAV. It is preservation of evidence class.

## Source preservation

`scripts/witness.py intake` computes a canonical SHA-256 digest of the complete parsed NAV receipt.

The WITNESS intake then preserves four fields as four claim classes:

| NAV source field | WITNESS record kind | Claim class |
| --- | --- | --- |
| `observed` | `reported_observation` | `source_record` |
| `delta` | `reported_delta` | `derivative_interpretation` |
| `next_heading` | `next_heading` | `orientation_proposal` |
| `claim_limit` | `claim_limit` | `source_limit` |

The runtime refuses an intake whose claim classes collapse.

## Run the crossing

Validate the WITNESS packet:

```sh
python3 scripts/witness.py validate
```

Cross the example contacted NAV receipt:

```sh
mkdir -p .build/witness

python3 scripts/witness.py intake \
  examples/nav-contacted.local-test.json \
  -o .build/witness/nav-intake.json
```

Inspect what crossed:

```sh
python3 scripts/witness.py inspect \
  .build/witness/nav-intake.json
```

The inspection reports claim-class counts, source digest, correction count and the explicit fact that WITNESS has **not** claimed independent verification.

## Why WITNESS refuses an oriented receipt

An `oriented` NAV receipt has not recorded world-contact yet.

WITNESS could archive it as a planning artifact, but this first crossing is specifically testing the handoff of a claimed encounter.

Therefore the runtime refuses:

```
status = oriented
```

for this crossing.

That refusal keeps the experiment legible:

```
NAV ORIENT
  ↓
real bounded move
  ↓
NAV CONTACTED RECEIPT
  ↓
WITNESS INTAKE
```

A later WITNESS intake class can accept planning artifacts without confusing them with encounter receipts.

## Crossing receipt

The example output lives at:

```
examples/nav-to-witness.intake.json
```

Its source digest binds it to:

```
examples/nav-contacted.local-test.json
```

The crossing therefore has both semantic provenance and a deterministic source fingerprint.

## Hostile controls

The tests require that the crossing refuses or exposes:

- **uncontacted input** — an oriented NAV receipt cannot masquerade as an encounter;
- **invariant drift** — WITNESS must keep `SOURCE ≠ STORY`;
- **claim-class collapse** — delta may not be upgraded into source record;
- **fake independence** — WITNESS inspection always reports that independent verification has not been claimed;
- **source mutation** — changing the NAV source changes its digest;
- **automatic effects** — WITNESS remains proposal-only and local.

## The first packet relay

We can now express an actual two-organ pipeline:

```
NAV
  heading
  bounded move
  world-contact
  delta
  next heading
     │
     │ static.nav-receipt/v0
     ▼
WITNESS
  source fingerprint
  claim-class separation
  explicit support boundary
  explicit non-support boundary
  correction berth
     │
     ▼
new provenance-bearing source
```

The important change is that the second packet does not merely read the first.

**It changes what can honestly be claimed about the first.**

That is the first real semantic crossing in the Bridge Layer.

## What this does not prove

This slice does not independently reproduce the NAV encounter.

It does not establish that SHA-256 identity alone is sufficient provenance.

It does not yet implement correction append operations, external witness acquisition, event/record/discovery clocks, or cross-node signatures.

It does not make WITNESS a judge of NAV.

It proves one smaller thing:

> A Bridge Packet receipt can cross into a different packet runtime and retain its source boundary, interpretation boundary and claim limit.

## Next door

The strongest next extension is not another packet yet.

It is to let WITNESS acquire **one additional witness** for a NAV source while preserving whether that witness is:

- derived from the same ancestor;
- independently observed;
- contradictory;
- corrective;
- or merely another retelling.

That would connect this crossing directly to CONSTANT / WORLD:

```
NAV → WITNESS → WORLD
```

The relay would then have its first executable independent-contact gate.
