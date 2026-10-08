# STATIC-CAD-005 — The Solid Body, Through reLATTE

**Status:** draft userspace Static-OS experiment, stacked on CAD-004 PR #55
→ CAD-003 → APPARATUS-002 → QUESTION-FIRST-001 → V1.

## What changed

STATIC-CAD-004 produces a constraint-solved, content-addressed two-dimensional
profile. STATIC-CAD-005 runs a **real CAD geometric kernel** against it,
then carries the engineering evidence and declared design decisions through
**native reLATTE R14**.

    Question / APPARATUS-002 source proposal
       → CAD-003 parent parametric design
       → CAD-004 constraint-solved sketch and exact source history
       → OCCT via CadQuery 2.8.0 (actual BRep)
       → actual pad, exact arc wire, through-hole subtraction
       → OCCT validity and one connected solid check
       → actual STEP and STL export
       → independent STEP reimport and volume comparison
       → declared decision ledger (6 events)
       → native reLATTE opaque-organ crossing
       → signed RECEIVE
       → independently owned signed R3_HOLD
       → immutable public evidence bundle + cold replay
       → STOP

The software kernel actually executes in hosted CI. This is NOT just
an inert generated macro, as 003/004 were.

## The design process that can be inspected

The request to “track the thought process” is implemented as an
**inspectable declared design-decision and evidence journal**, not an
attempt to access or store an AI model's hidden chain-of-thought.

Each event includes:
- a content-addressed identifier and hash-linked previous event;
- the exact source sketch ID;
- a named operation and alternatives that were considered;
- an explicit, human-readable rationale **code**;
- checkable kernel outputs, dimensions and export hashes;
- no claim of model-private reasoning or transferred authority.

The six founding events are:
1. SOURCE: verify the solved CAD-004 profile and its original source graph;
2. SKETCH_TO_SOLID: select exact circular arc boundary (not polyline mesh);
3. PAD: extrude the sketch as a geometric solid;
4. POCKET: subtract the declared through-bores;
5. NEUTRAL_EXPORT: export real STEP and STL with recorded SHA-256;
6. REIMPORT: independently reopen STEP and compare solid volume.

This is a documentary account of observable decisions, **not a proof
that an AI subject thought in this way**. A human or model's later
selected design proposals can attach their own transparent declared
reason codes, uncertainty and evidence without exposing private
reasoning traces.

## Native reLATTE, not a copied signer

Pinned canonical reLATTE source:

    the-static-collective/reLATTE @ dcc8cdca84c440aa4294134f020fb7095bf87f24

A small Node bridge directly imports that code's
runOpaqueOrganRoundTrip, verifyOpaqueOrganCrossing and verifyReceipt
APIs. It generates a genuine v0 opaque organ spec including four
exact SHA-256 payload references: SKETCH, DECISION TRACE, STEP, STL.

Native reLATTE signs the donor crossing, transports it through the
file-bundle path, and the separately owned receiver issues real
RECEIVED and R3_HOLD receipts with semantic effect **none**.

The crossing's source-history-head is the hash of the entire
declared design trace. The exact signed payload references bind
the original bytes. Cold verification validates:
- all local manifest and content-addressed source records;
- all six decision events, order and source identity;
- true native reLATTE crossing and receipt signatures;
- exact source trace and artifact byte hash matches;
- unchanged requested effect PRESENT_FOR_LOCAL_REVIEW;
- independent owner HOLD;
- no physical construction, release or admitted consequence.

reLATTE verifies attribution, not truth. The engineering meaning of
the observation remains with STATIC OS / CAD reviewers; ownership of
local disposition stays with the receiver.

A native receiver's private key is written **outside the publishable
CAD directory**, under an explicit operator-private runtime root.
The public artifact includes only verifiable crossing/receipt evidence.
The GitHub Actions artifact must never collect private signing keys.

## Commands

Use a trusted pinned GHoT checkout, generate the 002/003 source and
004 sketch using their existing instructions, then:

    python3 scripts/static-solid.py build \
      --sketch /path/to/static-cad-004/sketch.json \
      --out-dir /tmp/solid-005

This invokes the actual CadQuery/OpenCASCADE kernel; it produces
real solid.step and solid.stl alongside feature-verification.json,
design-trace.json, source sketch, and evidence-manifest.json.

To make a real native reLATTE crossing, first check out the pinned
reLATTE source at external/reLATTE and run npm install there (Node 24):

    python3 scripts/static-solid.py cross \
      --out-dir /tmp/solid-005 \
      --private-relatte-root /private/new/relatte-runtime-005

A private fresh local receiver root is required; an existing output or
ambiguous prior crossing is not silently repeated. Crossings and receipts
remain separately verifiable if the originating process dies.

    python3 scripts/static-solid.py verify --out-dir /tmp/solid-005

Verify is **read only**: rechecks all byte commitments, STEP geometric
readback, each declared decision hash, native reLATTE crossing signature,
native receive and HOLD receipts, and owner-local effect boundary.
It dispatches no new instrument, runs no fabrication and creates no
new crossing.

## Tests

Hosted workflow: .github/workflows/static-cad-005.yml

The workflow pins GHoT, pins the native reLATTE source and installs
CadQuery 2.8.0. It exercises actual OCCT pad and pocket, exports STEP
and STL, reimports STEP, verifies independent source ancestry, produces
a signed reLATTE crossing and independent RECEIVE/HOLD receipts, then
cold-replays. Hostile tests corrupt the STEP bytes, the declared trace,
the crossing signature and source payloads; all must refuse.

It then reruns the inherited question, apparatus, CAD-003 and CAD-004
test suites. A separate source-to-solid run uploads a **public**
evidence package containing the CAD solid and cryptographic witnesses,
excluding native reLATTE receiver private-key material.

## Limits

- This does not deliver a general AutoCAD / FreeCAD clone. It supports
  one bounded closed sketch family with circular arcs and through-pockets.
- OCCT validity and STEP readback are **geometric tests**, not complete
  proof of structural safety, dimensions, tolerance, interoperability,
  load capacity or manufacturability.
- STL is exported and byte-hashed, but its mesh watertightness has not
  been independently certified in the founding slice.
- No actual fabrication, CNC, 3D printer, motor, procurement or physical
  authorization is performed.
- Signed reLATTE provenance attests only the crossing/receipt bytes
  and signing keys, not that a named human physically approved them.
- Local STATIC OS decision events use content addressing, not independent
  signatures per event. Their aggregate is committed to by the native
  reLATTE crossing; forging all events requires a fresh crossing, whose
  signer would then differ unless the key is compromised.
- The experimental donor signer is not pre-registered as an
  institutionally trusted identity. Trust in source-world identity is
  separate from verifying its cryptographic signature.

## Constitutional laws

    EXPLANATION != PRIVATE CHAIN OF THOUGHT
    DESIGN RATIONALE != MODEL IDENTITY
    ENGINE PASS != ENGINEERING CERTIFICATION
    REAL STEP != APPROVED FABRICATION
    RECONSTRUCTIBLE HISTORY != HISTORICAL TRUTH
    SIGNED CROSSING != HUMAN CONSENT
    RECEIVED != ADMITTED
    HOLD != PERMISSION
    CAD DESIGN != PHYSICAL AUTHORITY
    NEXT QUESTION != NEXT TURN
    SOURCE SKETCH != SOURCE LEONARDO MANUSCRIPT

The next useful experiment is multibody assembly with independently
checked geometric tolerances, or an owner-selected CAD feature tree
where separate proposals are each signed and crossed at boundaries.
