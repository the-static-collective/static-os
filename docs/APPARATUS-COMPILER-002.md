# APPARATUS-COMPILER-002 — The Question Invents Its Instrument

Owner: Static-OS userspace. Stacked on QUESTION-FIRST-SESSION-001 (#51).
Experimental; no boot or permanent installation and no effects beyond local
pure mathematical simulation. The new question requires **axial motion**,
which the original two gear-only donors could not provide.

## Actual compilation

    Unknown: Is the expected axial travel from direct screw drive,
             or from a driven gear followed by a screw?
    Input:   12 driver teeth / 36 driven teeth / 6 input turns
             1500 micrometers axial travel per screw turn
    Claimed: 9000 micrometers
                   |
            inventory native GHoT cards
                   |
      original QUESTION-FIRST-001 instrument rack
                   |
     NEEDS_NEW_INSTRUMENT (screw, composite unavailable)
                   |
       opt in additional donor manifest
                   |
              typed candidates
                /          \
    direct screw         external gear -> leadscrew
    one graph node       two graph nodes with typed port
           \                 /
            \               /
              human chooses ONE
                    |
             durable PREPARED
                    |
         native GHoT signed dispatch
                    |
     ONE BOUNDED SIMULATION-ONLY DONOR
                    |
       signed receipt + verified packet
                    |
    independently recomputed rational result
                    |
             next question proposal
                    |
                   STOP

The direct screw model yields +9000 µm. The geared lead screw, with a
standard external gear inversion and an ideal no-slip model, yields
-3000 µm. **The model claim is contradicted in the geared specimen**,
not in the direct specimen. Neither is evidence of an actual mechanism.

The compiler discovers the **actual opt-in GHoT Instrument Rack cards**
for the original gear-forward primitive, the new lead-screw primitive
and the new *composite* apparatus executor. It records all source cards
and typed graph nodes. The composite donor is **one bounded process**
which computes gear ratio then axial travel internally. It DOES NOT
dispatch submodules, assemble physical objects or create permissions.
The v0 grammar is deliberately narrow: no arbitrary generated code,
arbitrary shell, multi-step physical controls or transport.

## Real Leonardo archive, honest source boundary

The Veneranda Biblioteca Ambrosiana catalog identifies
**Codex Atlanticus f. 1069 recto** as containing machinery for lifting,
pumping and gathering water, including two large cochleas for drawing
water from a river. Public catalog:

https://www.ambrosiana.it/en/discover/masterpieces/codex-atlanticus/

Our gear-then-leadscrew model is a MODERN APPARATUS INFERENCE inspired
conceptually by the idea of screw mechanisms. The catalog does NOT
establish that this exact mathematical gear/lead-screw apparatus is
drawn in f.1069 recto.

A frozen source witness binds catalog, folio, source topic, and
CONCEPTUAL_ANALOGY_ONLY. It explicitly records:

    source_image_sha256: null
    source_image_bytes_verified: false
    exact_gear_leadscrew_assembly_depicted: false
    attribution_proof: CURATORIAL_CATALOG_REFERENCE_ONLY

Changing folio, claiming manuscript bytes, inventing an authenticated
reconstruction, or smuggling a new historical assertion is refused.
This means we have a SOURCE-CATALOG-ANCHORED IDEA, **not** an ingested,
byte-verified Leonardo source. A later LemonPRESS origin ingest must
supply exact image bytes, catalog metadata, rights/provenance, and a
separate human-reviewed source interpretation before upgrading claims.

## Native authority / execution

- STATIC OS owns questions, typed assembly candidates, operator selection,
  durable session state and model-level interpretation.
- GHoT owns capability discovery, exact-card freshness, donor dispatch,
  signing and verification of the native reLATTE-shaped crossing and
  portable signed packet.
- The source catalog belongs to Biblioteca Ambrosiana. STATIC OS's frozen
  metadata does not grant authentication, copyrights, or construction authority.
- The operator approves exactly one offered apparatus and exact card.
- A PREPARED session exists before the one GHoT instrument dispatch.
  An ambiguous crash never triggers auto-retry, even on the same approval.
- Completed state is addressed and replayed read-only through GHoT's
  own packet signature verifier. The output is independently recomputed.
- A next question cites the parent plan, packet and observation and
  remains PROPOSAL_ONLY / action NONE.

### What *doesn't* happen

No physical sensor, build/fabrication, 3D printing, actuator, radio TX,
network command, WebZ delivery, actual Leonardo reconstruction, native
Autodisco inference, new OS/ISO boot, or signed Static-OS session root.
No approval boolean is cryptographic proof of human presence. A caller
with local write access may rewrite unsigned session state; the signed
GHoT packet prevents forging that donor's original signed execution
without its private signer key.

## Local operator procedure

Use a trusted, explicitly selected checkout of GHoT with its Instrument
Rack enabled. The pinned CI donor is:

    the-static-collective/GHoT @ 6e4aab6aec3b28f8dd50d01c3d571ae754c653d1

This is an unmerged GHoT experimental source cut, not production release.
Set locally private GHoT state and opt into **this experiment's** manifest:

    export GHOT_SRC=/path/to/pinned/GHoT
    export GHOT_HOME="$HOME/.local/state/static-apparatus-002/ghot"
    export GHOT_ADAPTER_MANIFESTS="$PWD/integrations/apparatus-002/adapter-manifest.json"

First, prove the absence using the original 001 adapter manifest:

    export GHOT_ADAPTER_MANIFESTS="$PWD/integrations/question-first-001/adapter-manifest.json"
    python3 scripts/apparatus-compiler.py compile --ghot-root "$GHOT_SRC" \
      --seed fixtures/apparatus-002/source-grounded-question.json \
      --out /tmp/apparatus-gap.json

The output is NEEDS_NEW_INSTRUMENT with two missing capabilities and
no executable candidates. Restore the new explicit manifest:

    export GHOT_ADAPTER_MANIFESTS="$PWD/integrations/apparatus-002/adapter-manifest.json"
    python3 scripts/apparatus-compiler.py compile --ghot-root "$GHOT_SRC" \
      --seed fixtures/apparatus-002/source-grounded-question.json \
      --out /tmp/apparatus-plan.json

This presents two candidates. Review all typed components and source
claims. For a separate operator selection, author an EXACT JSON object:

    {
      "schema": "static-os.apparatus-selection/v0",
      "plan_id": "<exact plan_id>",
      "candidate_id": "gear-then-screw",
      "executor_card_id": "<exact chosen card ID>",
      "approved": true,
      "owner_id": "local-human"
    }

Then, and only then, invoke the bounded single simulation:

    python3 scripts/apparatus-compiler.py execute --ghot-root "$GHOT_SRC" \
      --plan /tmp/apparatus-plan.json \
      --selection /tmp/apparatus-selection.json \
      --state-dir "$HOME/.local/state/static-apparatus-002/sessions" \
      --out /tmp/apparatus-result.json

This writes a private receipt and next-question candidate. Replay with
the explicit addressed state path:

    python3 scripts/apparatus-compiler.py replay --ghot-root "$GHOT_SRC" \
      --state /path/to/sessions/<plan-id-digest>.json \
      --out /tmp/apparatus-replay.json

No output file is overwritten; the CLI prechecks occupied paths BEFORE
any possible native GHoT dispatch, and writes output files with mode 0600.

## Verification

    GHOT_SRC=/path/to/pinned/GHoT python3 -m unittest tests.test_apparatus_compiler_002 -v

Dedicated CI also executes inherited QUESTION-FIRST-001 regressions.
Tests include:
- original gear-only Rack fails gracefully with a **missing-instrument**
  proposal, not a fabricated answer;
- new opt-in Rack exposes three safe required cards and two typed graphs;
- modified node edges still refuse after a plan is rehashed;
- unsafe or stale capability cards refuse;
- forged approvals and unowned candidate IDs refuse;
- actual native signed GHoT dispatch; independent Fraction recomputation;
- opposing apparatuses give distinct signed outcomes;
- cold replay verifies signed packet and cannot dispatch a second time;
- PREPARED / crash / ambiguous outcome remains HOLD;
- tampered GHoT donor bytes refuse even if local state is rehashed;
- external CLI compiles, requires explicit selection, refuses overwrite,
  writes mode 0600, and cold-replays without running an instrument.

## Limits / next

The **one missing modality** is axial translation in an ideal model.
This is not a generic compiler over all Leonardo machinery. Generalization
requires separate component catalogues, typed material/energy/force
interfaces, constraints, model validation, conflicts in instrument
availability, safe fabrication/verification and independently grounded
source witnesses from LemonPRESS. A next specimen should compare
different physical or simulated instrument families, then require
actual independent observations before asserting information gain.

### Non-collapses

    QUESTION != COMMAND
    REQUIRED INSTRUMENT != EXISTING CAPABILITY
    CATALOG REFERENCE != VERIFIED SOURCE BYTES
    CATALOG DRAWING != OUR DERIVED APPARATUS
    GRAPH != BUILT MACHINE
    COMPOSITE MODEL != AUTOMATIC SUBMODULE EXECUTION
    SIMULATED AXIAL TRAVEL != MEASURED TRAVEL
    CARD != AUTHORIZATION
    OWNER SELECTION != PHYSICAL SAFETY APPROVAL
    SIGNED GHOT PACKET != SIGNED STATIC OS SESSION
    PLAN != EXECUTION
    PREPARED != SAFE RETRY
    NEXT QUESTION != NEXT WORK
