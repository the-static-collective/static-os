# ELEVEN-HEAP-001 — The Infinite Radio Console

PASS: 25 experiment checks. Simulation only; no RF emitted.

| Check | Result |
| --- | --- |
| tune one exact nested address | PASS |
| reconstruct exact address and source history | PASS |
| reconstruction imports no authority | PASS |
| same physical dials, different typed quantities | PASS |
| Autodisco proposes without moving controls or granting authority | PASS |
| explicit acceptance narrows the listening region | PASS |
| withdraw affordance without changing dials or settings | PASS |
| previously prepared operation denied after withdrawal | PASS |
| fresh preparation cannot restore withdrawn affordance | PASS |
| old request stays stale after a separate regrant | PASS |
| recursive sensitivity and every response curve leave authority unchanged | PASS |
| dial motion still cannot restore attention | PASS |
| zoom makes one physical tick progressively finer | PASS |
| transmit dial prepares only a typed request | PASS |
| transmit request cannot grant its affordance | PASS |
| transmit affordance alone is insufficient | PASS |
| radio authorization alone is insufficient | PASS |
| permission alone is insufficient | PASS |
| both grants must cover this device | PASS |
| expired grants denied at execution time | PASS |
| both valid grants allow only the simulated transmission | PASS |
| successful requests cannot be replayed | PASS |
| separate transmission permission is revocable | PASS |
| full instrument microscope survives handoff | PASS |
| initial reception remains intact after every later operation | PASS |

Exact initial address: `11:[7,3,10,2,8,4]`.
Exact frequency: `179595858000000/1771561 Hz`.
Autodisco proposed source samples `[13,16)`; acceptance changed only the typed map.
Full source lineage, map definitions, response context, nested sensitivity, and
fractional motion remainders are retained in `history.json`.
