# TRIAD-001 — evidence-only composition candidate

Status: **contract-only**. Target: \`genesis-001-live-iso\`. No runtime, package, VM, live-image or hardware integration is implemented by this change.

## Why these boundaries

STATIC OS owns the live image, local OS session and independent boot gates. HOUSE / Workbench owns its local user interface and state. Corpus OS owns *its own* code-owned declaration adoption, genuine in-process Action Warrant, Session admission/consumption, terminal receipt, reconciliation, and constituted-world derivation. Jubilee Engine VM owns *its own* ParticularActV0 review, compilation and verifiable ActReceiptV0. An imported Corpus terminal receipt **cannot** become a genuine Corpus warrant or, without an independently reviewed particular, a Jubilee act receipt.

This is a **reference-only source inventory**, not an instruction to fetch, install or start the referenced projects. Source SHAs pin what was inspected; they do not prove cross-repository compatibility, successful builds, security, or any boot result. The current candidate's ELF and HOUSE pins are equal and independently checked against this reference-only source inventory.

## Narrow proposed handoffs

1. Corpus -> Jubilee: a newly designed, **data-only candidate-particular** carrier may reference an independently presented Corpus terminal receipt and its causal binding. Explicit human review must supply/accept any actual act's subject, participants, evidence classes, constraint, disposition, temporal relation and residual fog. Copying Corpus evidence never transfers an Action Warrant or proves a human occurrence. No adapter exists yet.
2. Jubilee -> Workbench: a **read-only receipt view** may display an independently verified ActReceiptV0 and its source references. A displayed receipt is not an OS permission, Corpus adoption handle, executable warrant, proof of legal validity, proof of human authorship, or automatic permission to disclose or train.
3. STATIC OS: only after the present ISO, BIOS/UEFI, offline HOUSE, state and recovery gates have independently passed should separately approved integration packaging be considered. A read-only integration contract does not alter \`manifest/genesis-001.json\`, the live-build image recipe, or the running Zorin installation.

## Non-transferable authority

No Corpus Action Warrant, private adoption handle, operation input, capability-owner host binding, identity/authentication claim, or mutation permission crosses the bridge. A receipt is evidence of a bounded computation under its verifier's stated assumptions; an OS build receipt is **not** an act receipt. Unverified, reported and inferred events remain distinguishable. Missing evidence remains unresolved, not backfilled by a neighboring projection. Automated background execution, new listeners, image inclusion and auto-promotion all remain out of scope.

## Contract checks and later acceptance

Run \`python3 scripts/validate-triad.py interop/triad-001.json\` and \`python3 -m unittest discover -s tests -v\`. The new validator intentionally accepts **only** this restrictive shape and tests the boundaries of the proposal. It does **not** inspect upstream source content or validate runtime payloads.

Later independently gated slices: (A) import and independently verify one *synthetic* Corpus terminal receipt without executable handles; (B) build a human-reviewed candidate particular, preserving irreducible uncertainties; (C) use Jubilee's actual verifier to show an independently compiled receipt in an isolated Workbench view; (D) test local persistence, offline behavior, failure and restart without expanding the OS privileges. Each slice needs its own fixtures, negative tests and observed result before any packaging/promotion.

## Inspected source boundaries

- [GENESIS-001](https://github.com/the-static-collective/static-os/blob/genesis-001-live-iso/docs/GENESIS-001.md)
- [Corpus OS architecture](https://github.com/the-static-collective/corpus-os/blob/main/docs/architecture.md)
- [Jubilee Book of Acts v0](https://github.com/the-static-collective/Jubilee-Engine-VM/blob/main/docs/book-of-acts-v0.md)

## FLIGHT-003 reconciliation

This copy retains TRIAD-001's evidence-only handoffs but now lives beside the experimental ELF guest candidate. Its Workbench source pin is checked against the *current candidate manifest* rather than the earlier plain Genesis pin. The ELF guest proof is a separate manual fixture; it is not a Corpus warrant, Jubilee ActReceipt, Storyship continuity witness, or image boot proof. No component is automatically installed by importing this contract.
