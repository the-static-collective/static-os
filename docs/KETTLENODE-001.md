# KETTLENODE-001 — The Boiling Point

**Status: runnable host-only energy-accounting specimen.** Stacked on the CRANKNODE-003 physical-edge branch at commit `7c80ccca540464e6fae8c412bbb6c365ad883366`. **No physical kettle, turbine, thermoelectric device, battery, or inline wattmeter was observed.**

## Question

Can an intermittently heated apparatus propose *capacity* for one bounded computation without allowing its meter to propose *authority*, automatic work, or a claim of physically powered execution?

```text
heat / stove / recovered thermal gradient [NOT CONNECTED]
                |
       instrumented harvest path [FUTURE]
                |
    cumulative source-reported energy sample
                |
       replay-refusing allowance ledger
                |
         operator-selects TURN
                |
       fsynced one-time reservation
                |
      ordinary CRANKNODE execute_turn
                |
       result + local CRANK receipt
                X
               STOP
```

This specimen uses **source-reported energy allowance**, denominated in integer **millijoules** for conservative accounting experiments. The test observations are simulation values, not empirical joule readings. The configured cost is a policy quota, **not** a benchmarked measurement of the CPU's energy use or proof of a powered computer.

## Run locally

Requires Linux/POSIX Python 3 stdlib; reuses CRANKNODE-001 runtime.

```sh
rm -f /tmp/kettlenode-demo.json /tmp/kettlenode-demo.json.lock
python3 scripts/kettlenode.py observe --ledger /tmp/kettlenode-demo.json --sample fixtures/kettlenode-001/baseline.json
python3 scripts/kettlenode.py observe --ledger /tmp/kettlenode-demo.json --sample fixtures/kettlenode-001/warm.json
python3 scripts/kettlenode.py status --ledger /tmp/kettlenode-demo.json
python3 scripts/kettlenode.py turn --ledger /tmp/kettlenode-demo.json --request fixtures/kettlenode-001/turn.json
python3 scripts/kettlenode.py turn --ledger /tmp/kettlenode-demo.json --request fixtures/kettlenode-001/turn.json # REFUSE
python3 -m unittest tests/test_kettlenode_001.py -v
```

The fixture begins at sample 0 / cumulative 0; the next observation reports cumulative 9000 mJ. TEXT.HASH costs 5000 mJ of **allowance**; 1000 mJ is a protected reserve. A single human-requested hash leaves 4000 mJ allowance and a consumed turn id. Another turn requires a new explicit request and enough additional allowance; no action is inferred from a meter update.

## Contracts and invariants

- `static-os.kettlenode-energy-sample/v0`: exact six fields. A meter cannot select a capability, request admission, prescribe semantics, or forge a CRANK receipt.
- `static-os.kettlenode-policy/v0`: operator-owned source/session/observation kind, maximum increment, reserve, and capability allowances; pinned by hash inside the session ledger.
- `static-os.kettlenode-ledger/v0`: source samples strictly sequential and cumulative nondecreasing; state and reservations are content-hashed. The hashes detect accidental changes but **are not cryptographic signatures**, anti-rollback, or trusted hardware attestation.
- `static-os.kettlenode-reservation/v0`: a TURN id is consumed once in an fsynced atomic local ledger **before** the ordinary CRANKNODE handler is invoked. Crash = spent allowance, not success and not retry. The successful runtime result and CRANK receipt are returned separately; the reservation ledger itself does not attest execution.
- `source.kind = human` is required for this 001 gate. A future physical selection may compose with CRANKNODE-003's separate physical one-shot edge, but an energy sample alone does not acquire that property.
- Refuse malformed state, policy drift, replays, gaps, oversized increments, foreign sessions, implicit continuations, unauthorized capabilities, and insufficient allowance.
- `ENERGY != AUTHORITY`; `METER REPORT != INDEPENDENT MEASUREMENT`; `ALLOWANCE != STORED CHARGE`; `RESERVATION != EXECUTION`; `EXECUTION != ADMISSION`.

## Physical path, only after host test

1. Start with a rated thermoelectric-generator module on a manufacturer-approved external heat source, an appropriate heat sink, and a current-/voltage-limited DC harvesting controller. Prefer a supervised **non-pressurized** arrangement; do not drill or seal a household kettle, improvise a pressurized boiler, or alter mains connections.
2. Instrument harvested output voltage and current at a defined observation boundary with independently calibrated equipment. Integrate measured output energy `E_mJ = sum(V * I * dt_seconds * 1000)`. Record timestamp provenance, calibration, uncertainty, and sensor identity; do not treat cumulative output as an accurate battery state-of-charge.
3. Measure **actual load consumption separately**, account for converter efficiency and storage losses, and only then propose a physical-energy claim. Device powering the host must be witnessed separately; sampling alone is insufficient.
4. Add power-fail tests, out-of-order packet handling, source authentication, bounded counter-reset protocol, electrical protection, and independent energy reconciliation before attaching physical device claims. None is proven by this branch.
5. Use reLATTE to transmit evidence only through its owner-defined signed crossing and destination-local disposition. This specimen creates **no** signed crossing and cannot assign node authority, PENNY value, physical asset custody, or human worth.

## What the tests show

The hostile unit tests exercise zero budget, finite allowance, one human-selected turn, replay refusal, duplicate TURN refusal, false meter semantics, source/session mismatch, non-integer/giant readings, policy drift, ledger corruption, post-reservation crash, and concurrent duplicate claims. These are **host/simulation assertions**, not field measurements.

## Boundaries deliberately left open

- source reports can be forged; source attestation/authentication remains future work;
- state hashes are self-consistency checks, not tamper resistance;
- filesystem durability assumes local POSIX fsync semantics and excludes sudden hardware faults;
- ledger is not anti-rollback and must not be treated as financial accounting;
- reserved quota is not the energy consumed by an actual task;
- a measured harvest source does not establish continuous supply to the CPU;
- negative outcomes do not refund energy allowance or authorize automatic retries.

**Boiling is an energy condition, not a decision.**
