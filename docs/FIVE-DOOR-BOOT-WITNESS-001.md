# FIVE-DOOR-BOOT-WITNESS-001

Status: synthetic executable contract harness, stacked on STATIC OS PR #42 `BARDO-BOOT-WITNESS-001`.

This slice defines the first human-visible STATIC OS session grammar around one particular and five sibling capability doors:

```text
YOU ARE HERE.

PARTICULAR
  [ exact admitted thing ]

AVAILABLE DOORS
  PRESENT
  MOTION
  SOUND
  VOICE
  PRINT

Nothing has happened yet.

Choose a door.
Or choose several.
Each leaves separately.
Each comes home separately.
```

The founding fixture deliberately uses a synthetic admitted parent. It does **not** claim that the locally reported adapter-harvest head `043e89a` is available on GitHub, bound into STATIC OS, or executed by this branch.

## LIFE, not a success funnel

The fixture exercises all five doors as sibling branches:

```text
PRESENT -> RETURNED -> ADMIT
MOTION  -> RETURNED -> HOLD
SOUND   -> IN_FLIGHT
VOICE   -> RETURNED -> REFUSE
PRINT   -> RETURNED -> HOLD
```

No branch becomes the canonical successor. A sibling cannot mutate another sibling. An in-flight branch remains visible at shutdown.

```text
SIBLING != SUCCESSOR
UNFINISHED != ERROR
IN FLIGHT != LOST
UNOBSERVED != FAILED
```

The Return Tray records returned siblings but does not admit them automatically.

```text
RETURN != ADMISSION
ADMISSION != EXECUTION
```

## Shutdown and reboot grammar

The fixture freezes the exact branch-state constellation at shutdown. The expected reboot behavior is to reconstruct that unresolved constellation without inventing completion or same-process continuity.

This branch does not claim that a shutdown or reboot actually happened. It proves only that the contract can represent the unfinished world without erasing it.

```text
REBOOT != NEW WORLD
THE HOUSE REMEMBERS RECEIPTS, NOT ASSUMPTIONS
```

A later real witness must replace expectation with durable receipts and a real cold reconstruction.

## TranchNOSE observer

TranchNOSE is attached as a comparison observer only.

The parent identity, source admission, and human intent are held constant. The varied dimension is the selected door / field configuration:

```text
same X
same admission
same intent
different door-field configuration
        ->
comparison-ready evidence
```

The observer has no session authority and this synthetic fixture proves no causal attribution.

```text
G_field != G_local
COMPARISON != CAUSAL PROOF
OBSERVER != AUTHORITY
```

The point is to reserve the causal seam now so a later real five-door run can ask which relational/configuration change actually altered the result without allowing the observer to become the controller.

## Adapter-harvest boundary

The current conversation reports local adapter-harvest commit `043e89a`, including PRESENT, MOTION, SOUND, VOICE, and PRINT. That commit was not GitHub-addressable when this harness was created.

Accordingly the contract records:

```text
github_verifiable = false
bound_into_this_contract = false
door.binding = unbound
```

When the adapter work is pushed, the next slice may replace the synthetic fixture with exact pinned card identities and real dispatch/return receipts. It must not simply flip claim booleans.

## Machine-enforced laws

- `VISIBLE POSSIBILITY != EXECUTION`
- `SESSION != AUTHORITY`
- `CONSTELLATION != MERGE`
- `SIBLING != SUCCESSOR`
- `RETURN != ADMISSION`
- `ADMISSION != EXECUTION`
- `IN FLIGHT != LOST`
- `UNFINISHED != ERROR`
- `UNOBSERVED != FAILED`
- `REBOOT != NEW WORLD`
- `THE HOUSE REMEMBERS RECEIPTS, NOT ASSUMPTIONS`
- `G_field != G_local`

## Run

```sh
python3 scripts/validate-five-door-boot-witness.py \
  manifest/five-door-boot-witness-001.json \
  fixtures/five-door-boot-witness-001/session.json

python3 -m unittest tests.test_five_door_boot_witness -v
```

The next earned claim is not another capability. It is one real admitted particular surviving explicit multi-door dispatch, independent returns, local dispositions, shutdown, and cold reconstruction without sibling collapse.
