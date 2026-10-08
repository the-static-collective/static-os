# QUESTION-FIRST-SESSION-001 — The Machine That Asks

Owner: STATIC OS userspace session. Status: draft, removable experiment.
Stacked on STATIC OS V1; does not modify Debian, boot, ISO, persistent-root
ownership, reLATTE canonical grammar, GHoT's instrument authority, or WebZ.

## What executes

    DECLARED UNKNOWN
       |
    COMPILE QUESTION + TWO DISTINCT EXPERIMENT CANDIDATES
       |
    EXPLICIT OWNER SELECTS EXACTLY ONE
       |
    DURABLE PREPARED CHECKPOINT
       |
    GHoT FRESH INSTRUMENT RACK CARD
       |
    GHoT NATIVE SIGNED reLATTE-SHAPED DISPATCH
       |
    BOUNDED SIMULATION DONOR
       |
    NATIVE SIGNED RECEIPT + PORTABLE SEED PACKET
       |
    VALIDATE + INDEPENDENTLY RECOMPUTE SIMULATED RESULT
       |
    NEXT QUESTION PROPOSAL — NEVER AUTOEXECUTE

This founding question generator is deterministic. It is NOT a claim that
an AI model independently discovered a scientific question. AI authored
questions, independently sealed Autodisco first-listen responses, broad
folio ingestion and physical mechanism construction remain future work.

## Mechanism specimen

The declared source seed describes two external spur gears with 12 and
36 teeth, six driving revolutions, and a claim of minus two driven
revolutions. The question asks whether the claim matches the declared
ideal no-slip external gear model.

The optional GHoT donor offers two bounded capability cards:

- mechanism.gear.forward.simulate
- mechanism.gear.inverse.simulate

Each card is PROPOSAL_ONLY, and the source remains a modern ideal
engineering model. These are two software calculation routes, NOT two
independent physical instruments or independently verified Leonardo
drawings. No Leonardo folio ID is attached or implied.

STATIC OS selects one exact card only through an externally supplied
human selection. The GHoT instrument Rack revalidates the card, signs
its native reLATTE-shaped crossing and execution receipt, and returns
a portable packet. STATIC OS calls GHoT's own packet-signature verifier,
checks the selected payload digest and independently recalculates the
ideal mathematical result. Matching or contradictory model outcomes
determine the wording of the next PROPOSAL_ONLY question.

No radio transmission, mechanical actuation, autonomous question loop,
model-provider inference, source-semantic admission or new core signing.

## The source ownership seam

GHoT is the instrumentation and native execution authority. STATIC OS is
the session owner and operator interaction surface. reLATTE's crossing
format is used by GHoT and is NOT reimplemented or promoted to new
authority by this repository.

Dedicated CI checks out pinned GHoT donor source:

    the-static-collective/GHoT
    6e4aab6aec3b28f8dd50d01c3d571ae754c653d1

This cut belongs to an unmerged draft PR stack. Operator-selected local
GHoT code is not independently attested by the sample CLI.

## Durable HOLD and cold replay

An explicit execution first writes a private PREPARED checkpoint before
calling GHoT. An interrupted attempt stays PREPARED / HOLD; automatic
retry is forbidden even if the native donor possibly completed. GHoT
also independently handles ambiguous outcome denial for exact dispatch.

Completed state is saved atomically and content-addressed with native
packet, source observation and next-question proposal. Cold replay
rechecks the state address, validates the native GHoT packet signature,
recomputes the mathematical result and next question, and NEVER calls
the donor. The signed GHoT packet is cryptographic source evidence;
the STATIC OS local session state is only content-addressed, not
independently signed. A machine with filesystem write authority can
rewrite local state; do not confuse local hashes with authenticated
owner intent.

## Operator commands

Set GHOT_SRC to a trusted checked-out source root. Use a private GHOT_HOME
and explicitly opt into the two donor capabilities:

    export GHOT_SRC=/path/to/trusted/GHoT
    export GHOT_HOME="$HOME/.local/state/static-os-question-first/ghot"
    export GHOT_ADAPTER_MANIFESTS="$PWD/integrations/question-first-001/adapter-manifest.json"

Generate an inert question, no mechanism work:

    python3 scripts/question-first.py ask \
      --ghot-root "$GHOT_SRC" \
      --seed fixtures/question-first-001/gear-seed.json \
      --out /tmp/question-first-proposal.json

Read its exact question_id, candidate_experiments and chosen card_id.
Create human-authored selection JSON with this exact shape:

    {
      "schema": "static-os.question-selection/v0",
      "question_id": "<exact question ID>",
      "candidate_id": "simulate-forward",
      "card_id": "<exact card ID>",
      "approved": true,
      "owner_id": "local-human"
    }

This boolean is explicit software confirmation, NOT cryptographic human
identity evidence. The question generator cannot supply this decision.

One bounded selected instrument execution:

    python3 scripts/question-first.py execute \
      --ghot-root "$GHOT_SRC" \
      --seed fixtures/question-first-001/gear-seed.json \
      --selection /tmp/question-first-selection.json \
      --state-dir "$HOME/.local/state/static-os-question-first/sessions" \
      --out /tmp/question-first-result.json

Read-only cold replay using the explicit session JSON state file:

    python3 scripts/question-first.py replay \
      --ghot-root "$GHOT_SRC" \
      --state /path/to/session/question-digest.json \
      --out /tmp/question-first-replay.json

Output files are exclusive, mode 0600, and never automatically overwritten.
The runtime itself requires no installed OS or boot integration.

## Tests and outstanding gates

    GHOT_SRC=/path/to/pinned/GHoT python3 -m unittest tests.test_question_first_001 -v

Hostile tests require actual native GHoT dispatch, native packet validation,
tampered packet refusal, stale or missing instruments, unapproved choice,
source misattribution rejection, false numerical assumptions, contradiction,
PREPARED HOLD after crash, and zero donor invocation on cold replay.

Future gates: source-grounded Da Vinci folio ingestion via LemonPRESS,
autonomous *question suggestions* via independently sealed Autodisco
observations, multiple instrument modalities, independent physical
verification, safety constraints and fresh owner-local physical authorization.
No bootable ISO, live model insight or physical instrument field is earned.

## Laws

    QUESTION != COMMAND
    QUESTION GENERATOR != EXECUTION AUTHORITY
    HISTORICAL DRAWING != PROVEN MACHINE
    IDEAL SIMULATION != PHYSICAL OBSERVATION
    OFFER != SELECTION
    SELECTION != EXECUTION
    SIGNED GHOT RECEIPT != SEMANTIC TRUTH
    GHOT SIGNATURE != STATIC OS SESSION SIGNATURE
    NEXT QUESTION != NEXT TURN
    PREPARED != SAFE RETRY
    OS SESSION != BOOTED DISTRIBUTION
