# FABRICATION-CROSSING-013 — printers as separately sovereign reLATTE participants

**Cross-repository executable experiment.** Native Static OS 010→011→012 source, plus reLATTE's actual independently keyed local-world publication and grants from DYNAMIC-INTERFACE-FIELD-001. Stacked on ALL-PRINTER-FIELD-012. No printer connection or physical part has been created.

## Source authorization boundary

1. A real OpenCASCADE model has a source sketch, signed CAD and reLATTE original RECEIVE/R3_HOLD receipts.
2. A *real* PrusaSlicer process makes a virtual machine's FFF G-code packet; G-code is not sent to hardware.
3. Source verifies that CAD + G-code, then replays the open-world 012 field (which itself admits only a virtual FFF software toolpath; every owner-declared physical machine remains HOLD).
4. An explicit three-machine selection yields one `static-os.fabrication-request/v0`, exact source and printer-field references, all physical permissions false, zero material stock asserted.
5. reLATTE consumes only that bounded request (no remote network). Three independent experimental LocalWorld actors publish signed offers. They issue independent owner-signed hold/proposal decisions. The third owner withdraws, its former grant fails, and a new world of that descriptive machine name needs a fresh permission before emitting a **propose-only** ticket.
6. Cold verifier independently reconstructs signed owner histories, history heads, gate-scope, old/new world IDs, signatures and terminal inventory 0. The original CAD's native reLATTE crossing was genuine; the new 013 printer-node decisions are locally signed **experimental** receipts, not new normative reLATTE RemoteReceiver transfers.

## Source CLI

```sh
python3 scripts/static-fabrication-request.py propose \
 --source dist/cad010-real-solid \
 --packet dist/print011-held \
 --fleet fixtures/printer-field-012/synthetic-fleet.json \
 --selection fixtures/fabrication-013/three-node-selection.json \
 --out dist/fabrication-request-013.json

python3 scripts/static-fabrication-request.py verify \
 --source dist/cad010-real-solid \
 --packet dist/print011-held \
 --fleet fixtures/printer-field-012/synthetic-fleet.json \
 --selection fixtures/fabrication-013/three-node-selection.json \
 --out dist/fabrication-request-013.json
```

Both operations **require the original native signed source and output package on disk**; the returned `request_id` is a content digest, **not a signature** or independent evidence that the source was cold-verified. `propose` is write-new with no overwrite. Downstream requests based on detached JSON can be forged: the trusted integration CI invokes this native source verifier before passing the result to reLATTE.

The subsequent reLATTE command from its own repo:

```sh
node experiments/fabrication-crossing-013/run.mjs \
 /path/to/dist/fabrication-request-013.json /new/output/fabrication-relatte-013
node experiments/fabrication-crossing-013/verify-run.mjs \
 /new/output/fabrication-relatte-013/proof.json \
 /new/output/fabrication-relatte-013/trust-pins.json
```

Native CI constructs its **own** original CAD/real G-code, then runs everything in sequence with pinned reLATTE donor SHA and distinct owner-process cold verification. The test selection and three machines are synthetic: they are **not vendor profiles, user printer identities or licensed jobs**.

## Acceptance

- Machine A: FFF machine in compatibility HOLD; local simulation says material not verified, signed HOLD.
- Machine B: MSLA machine in compatibility HOLD; native resin-layer adapter missing, signed HOLD.
- Machine C: 011 virtual FFF test device, one simulated local `propose` grant. After withdrawal, stale old grant rejected *before local proposal*.
- Reborn C: same descriptive machine identity, different world cryptographic identity, new offer and one-use `propose` grant. A signed proposal **cannot enable printer I/O** or create a part.
- Independent cold re-check of each native history and receipt, retaining the original reLATTE R3_HOLD source crossing, while creating zero locally owned physical inventory.

## Scope limits

The source signer and content-addressed IDs do **not** establish real machine profile attestation, legal ownership, manufacturer safety qualification, print-job execution, custody of material or economic yield. The reLATTE laboratory's decision signer is a separate Ed25519 principal from the native LocalWorld signer; externally pinned public anchors are needed to interpret the two as belonging to the same node. The demonstration's emitted self-contained pins permit cold cryptographic consistency, not independent identity trust. No globally stable node ID or authenticated remote transit is implemented.

There is no physical safety override. Real production would require fresh model-specific slicer and printer-host adapters, a particular owner's consent and physical material/energy, independent observation of print completion, and owner-local admission before any Jubilee physical stock could be proposed.

**Laws**: `ADVERTISED != AUTHORIZED`, `SIGNED != REAL`, `REQUEST != ROUTE`, `PROPOSE_GRANT != PRINT_GRANT`, `WITHDRAWN != REVOKED_HISTORY`, `REAPPEARED_NAME != RECOVERED_AUTHORITY`, `VIRTUAL GCODE != PHYSICAL PART`, `REPLAY != RE-EXECUTION`.
