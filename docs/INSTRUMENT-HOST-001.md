# STATIC-OS INSTRUMENT HOST 001

Native ELEVEN-HEAP integration candidate, stacked on
`experiment/v1-world-bus-vehicle-ecm` at `405fbbf56f96a32af1ed332e2ad9105c09f073da`.
This branch supplies a reusable, bounded subsystem and local installation entry point.
It does not claim an installed Static-OS image, physical reception, native Autodisco
execution, or RF transmission.

## Import and regression oracle

The original ELEVEN-HEAP implementation was found in the shared workspace,
not reconstructed from the conversation summary. Its implementation, experiment,
33-test file, README, and project metadata are imported unchanged under
`vendor/eleven_heap_001/`. SHA-256 values are pinned in
`manifest/instrument-host-001.json` and checked by tests and installation.

The host imports the original `Address`, `Dial`, `ControlMap`, and rational interval
implementation. The original simulation remains runnable in its own directory:

```bash
cd vendor/eleven_heap_001
python3 -m unittest discover -s tests -v
python3 experiment.py --output /tmp/eleven-heap-oracle
```

Its 25 experiment checks and 33 tests remain green. Its simulation authority gate
does not govern native instruments. The simulated Autodisco wrapper invokes only
the original proposer's method, with no authority service and no oracle execution.

## Generic InstrumentAdapterV0

`instruments/contract.py` defines the runtime-checkable adapter protocol. Its three
instrument-specific methods are `describe`, `observe`, and `select`. The shared
host supplies proposal tracking, native admission, execution receipts, withdrawal,
retirement, and stale-operation rejection for every adapter.

| Contract surface | Representation |
| --- | --- |
| Identity and source provenance | Versioned descriptor; source kind, reference, immutable hash, ordered source history |
| Discoverable controls | Selector and attention descriptors with quantity, unit, range, response policies, and recursive sensitivity |
| Nested addresses | Original radix-11 address and every ancestor PSI interval; public positions 1–11 |
| Response and sensitivity | Original `Dial` tree, context, threshold, fractional remainder; operable response and nested sensitivity selectors |
| Read-only observation | Bounded immutable item set, source reference, content hash, and classification |
| Proposed operation | Exact session/process/instrument incarnation, descriptor, observation, controls, selection, and required capabilities |
| Admission | Native reLATTE owner-local decision for one exact read-only record |
| Execution and denial | Content-addressed host receipts; successful record also names the verified native admission receipt |
| Lifecycle | Installed incarnation, withdrawal, retirement, disappearance, and explicit replacement |

External positions are **1 through 11**, mapped losslessly to the original **0 through
10** encoding. The original mathematics is unchanged. A PSI region is an original
address-prefix interval; zoom enters its next child. A region retains its complete
path, even when an instrument has less output resolution than the address grammar.

V0 limits are 16 instruments, 16 address levels, 8 sensitivity levels, 4,096 source
items, 65,536 bytes per serialized payload/event, and 10,000 events per session.
Native child processes have timeouts; there is no shell-command input. Budget
exhaustion refuses work rather than widening the contract.

## Three organ boundaries

**GHoT:** `GhotSystemAdapter` calls the real owner's `memory_bytes` and `probe_power`
functions at `e35dd470384d864b7b0b629a68dad570875a7df0`. It avoids `body()` because that
method creates identity files. The child process suppresses bytecode writes and
removes manual `GHOT_*` power hints. OS, CPU, memory, load, battery, and temperature
remain typed observations; unavailable sensors return the owner's unavailable values.
The integration does not call GHoT's executor or remote task interface.

**Autodisco:** inspected `the-static-collective/the-autodisco` at
`83f032b438e7264d3dfdfd2f0b3eb2b3f05484d0`. Its owner-authenticated application and
first-listen radio canon expose no compatible bounded sample-region proposal API
in the inspected interfaces. No Supabase session, inference provider, or music
generation endpoint was invoked. The host's proposer is labeled **ELEVEN-HEAP
simulated Autodisco (not native Autodisco)** in every proposal. A proposal cannot
be passed as an executable operation, and changing its producer label is rejected.
The radio-focused `The-AutodiscoV.20.-question-marks-` repository was also inspected
at `7ad77a46debc7e8c05fc7434c9091f3e36870651`. Its real `audio-window.mjs` can extract
caller-selected windows; `audio-look-twice.mjs` can produce textual door-seed questions
after model listening. Neither exposes the narrower sample-region proposal contract
used here. Those helpers and their Gemini inference were not invoked. This does not
rule out future compatible interfaces in other branches.

**reLATTE:** `relatte_bridge.mjs` imports the real owner implementation at
`dcc8cdca84c440aa4294134f020fb7095bf87f24`, the existing CRANKNODE-002 owner cut.
It uses `sealOpaqueOrganCrossing`, `verifyOpaqueOrganCrossing`, `LocalReceiver`, and
`verifyReceipt`. It does not reproduce signing, canonicalization, or receiver semantics.
Every native call verifies the exact donor commit and an unchanged tracked tree.

```text
proposed read-only record
  → native signed opaque-organ crossing
  → native verification and RECEIVE
  → native signed HOLD
  → explicit owner-local command
  → separate owner-local crossing of the same exact operation bytes
  → native ADMIT receipt
  → current host binding + current native admission verification
  → one recorded selection
```

The original proposal stays HOLD. Its receipt never becomes a grant. This respects
the native receiver's immutable disposition: an owner-local decision is a distinct
crossing rather than an invented HOLD-to-ADMIT mutation. Admission covers only one
specific record, with a maximum one-hour lifetime. Execution checks expiry against
current time, consumes the request once, and preserves native receipt attribution.

There is no second native authority gate. Host freshness and consumption checks
constrain already admitted work; they never create admission. If native reLATTE is
unavailable, proposals are visibly **candidate-only**, and execution fails closed.

## Recorded receive path

No USB/audio receiver interface was exposed by this execution host. The receive
adapter therefore uses the explicitly synthetic two-track PCM WAV in
`fixtures/instrument-host-001/`. Its 90 MHz and 106 MHz station tags are fixture
labels, not measured carriers. There is no SDR, sound-device, antenna, or network path.

The demonstrated path is:

```text
SOURCE (content-addressed recorded fixture)
  → OBSERVE (read bounded PCM and retain source lineage)
  → SELECT (frequency map chooses a station track)
  → ATTEND (attention map changes source sample selection within that track)
  → RECORD (one native owner-admitted read-only record)
```

Turning frequency changed both the selected track and its sample content. Switching
to attention preserved the physical dials and the previously selected station;
turning attention changed the sample region and sample value. Neither gesture
changed required capabilities or caused admission. GHoT is a second instrument
using the same generic contract: its selector changes the observed OS field, with
each selected field retaining its own unit.

## Transmission

Default and only V0 state: **DISABLED**. No transmission adapter or RF device API is
shipped. Unsupported operations, transmit maps, capabilities imported in a profile,
and proposals relabeled as grants are rejected. The native bridge itself accepts
only the exact `record` operation with `observe` and `record` requirements.

The standalone regression oracle still tests independent simulated transmit permission
and radio authorization. Those simulation grants cannot enter the native host.
Future RF support must be a separate reviewed adapter with an independent permission
gate, supported-device checks, lawful frequency/mode/power/jurisdiction authorization,
and an independently admitted operation. Native record admission cannot authorize it.

## Durable sessions and cold verification

Owner-local SQLite uses WAL, FULL synchronous commits, and transactions. Its event
chain records descriptors, source references, exact controls, response selectors,
nested sensitivity, observations, proposals, explicit selections, authorized operation
decisions, execution/denial receipts, incarnations, and withdrawals. The materialized
state and request table are checked against that evidence when reopened. reLATTE
separately persists and verifies its own signed receiver journal and identity.

A fresh process restores historical controls, creates a fresh process incarnation,
and installs no live adapter automatically. Historical requests stay nonexecutable,
even when the native receiver retains their signed ADMIT receipts. Fresh adapter
installation creates another instrument incarnation; old requests cannot revive.
Source disappearance or a changed source/calibration/descriptor withdraws the
current binding. Restoring the file alone cannot restore authority or liveness.

The process-death proof sends **SIGKILL** before the child closes SQLite. A separately
started verifier reconstructs exact addresses and recursive sensitivity, verifies the
committed evidence, and refuses the dead process's operation. This proves process
death recovery; it does not prove physical cold boot, power-loss durability on every
filesystem, or continuity of an installed Static-OS image.

Exported evidence contains public crossings and receipts, never private receiver keys.
The SQLite hash chain detects accidental modification, not an attacker rewriting
the entire owner-local store. Native admission verification additionally uses the
real signed reLATTE journal. Owner-only filesystem custody is the V0 local operator
boundary; arbitrary code running as that owner is outside this threat model.

## Install and exercise

Tested locally with Python 3.12 and Node 24. Native reLATTE needs Node's TypeScript
stripping and the donor's dependencies; missing or incompatible runtimes refuse
native operations. The standalone oracle's original project requirement is preserved.

```bash
python3 scripts/install-instrument-host.py --prefix "$PWD/.instrument-prefix"
.instrument-prefix/bin/static-instrument demo --session /tmp/instrument-candidate
```

The default demo performs read-only observation, selection, and proposal creation;
it does not admit or execute a record. Exact native donor checkouts enable the native
proof. `--owner-record` is the explicit local owner's decision to record one selection:

```bash
git clone https://github.com/the-static-collective/GHoT.git /tmp/instrument-ghot
git -C /tmp/instrument-ghot checkout --detach e35dd470384d864b7b0b629a68dad570875a7df0
git clone https://github.com/the-static-collective/reLATTE.git /tmp/instrument-relatte
git -C /tmp/instrument-relatte checkout --detach dcc8cdca84c440aa4294134f020fb7095bf87f24
npm install --ignore-scripts --no-audit --no-fund --prefix /tmp/instrument-relatte
npm run verify --prefix /tmp/instrument-relatte

python3 -m instruments.cli demo --session /tmp/instrument-native \
  --ghot /tmp/instrument-ghot --relatte /tmp/instrument-relatte --owner-record
python3 -m instruments.cli verify --session /tmp/instrument-native --relatte /tmp/instrument-relatte
python3 scripts/instrument-process-death-proof.py --session /tmp/instrument-killed

STATIC_INSTRUMENT_GHOT=/tmp/instrument-ghot \
STATIC_INSTRUMENT_RELATTE=/tmp/instrument-relatte \
python3 -m unittest discover -s tests -v
```

Use fresh session directories for reproducing evidence. The native tests require
the two environment variables; without them, six native-interface tests explicitly
skip. The new CI job provides both exact donors and runs them without skips.

The ISO recipe invokes the same source installer into `/usr/local`; no image was
built or booted during this experiment. Its older whole-body reLATTE source pin is
not silently treated as compatible with this subsystem. Native donor roots remain
explicit. Debian-image runtime/dependency closure and ISO boot are separate gates.

To add a second instrument, implement `InstrumentAdapterV0` and call
`host.install(adapter)`. The same host supplies discoverability, nested controls,
lifecycles, provenance, native record admission, and receipts. The installed-prefix
test installs a second instrument without changing host code. The native GHoT test
also installs GHoT alongside the recorded radio, demonstrating two different
instrument quantities through the same contract.

## Capability matrix

| Capability | Simulated / fixture | Locally demonstrated | Externally verified |
| --- | --- | --- | --- |
| ELEVEN-HEAP mathematics | Original simulation oracle | Exact import; all 25 checks and 33 tests green | No external witness claim |
| Generic host and two instruments | Recorded radio fixture | Local prefix installation; radio + genuine GHoT use one contract | Installed OS/ISO boot NOT_RUN |
| GHoT observations | No substitute in native proof | Real pinned OS/memory/power probes; selected OS and CPU fields match this host | Other physical hosts/sensors NOT_RUN |
| Radio receive | Clearly synthetic recorded PCM | Bounded source read; frequency changes track; attention changes sample | Physical SDR/audio/network reception NOT_RUN |
| Autodisco proposals | Original energy-window proposer, explicitly labeled | Proposal/selection distinction and laundering refusal | Native Autodisco execution NOT_RUN |
| reLATTE crossing/receipts | No substitute in native proof | Real signed crossings, verification, HOLD, owner-local ADMIT, durable journal reopen | No live remote service or independent operator witness |
| Session mortality | Recorded source data | Actual SIGKILL with SQLite left open; separate verifier reconstructs and denies historic requests | Physical boot/power-cut recovery NOT_RUN |
| Transmission | Original independent simulated gate regression | Native host and bridge deny all RF paths; no RF API present | RF transmission NOT_RUN; none claimed |

## Acceptance results

All eight gates are satisfied at their explicitly bounded level: the original oracle
stays green; a genuine local read-only adapter runs; dials alter typed selections
without admission; real GHoT/reLATTE are exercised while Autodisco stays simulated;
no RF path runs; durable evidence survives process death; cold verification passes;
and a second instrument installs through the same contract.

Local results: **180 Static-OS tests pass**, including the wrapper that runs all
**33 original tests and 25 experiment checks**. This adds **37 repository tests**
to the inherited 143-test baseline. The exact native reLATTE donor's own
`npm run verify` passes **119 tests**, type checking, and build.

See `evidence/instrument-host-001/` for native proof, cold proof, SIGKILL proof,
test output, oracle output, source hashes, hardware-interface availability, and the
acceptance matrix. External CI results belong to the PR checks; local test evidence
does not claim remote CI completion.
