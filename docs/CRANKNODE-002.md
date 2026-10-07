# CRANKNODE-002 — replaceable provider → reLATTE crossing candidate

## Purpose

CRANKNODE-001 made the turn law executable.

CRANKNODE-002 makes the AI-shaped organ replaceable without allowing provider identity, inference, crossing, admission, or continuation to collapse into one event.

    explicit TURN
        |
        v
    AI.PROPOSE
        |
        v
    operator-configured provider process
        |
        | one JSON request / one JSON response
        v
    proposal-only result
        |
        v
    CRANK receipt
        |
        v
    relatte.opaque-organ-spec/v0 CANDIDATE
        |
        X
       STOP

The candidate is not signed here.

reLATTE remains the owner of canonical crossing construction, signatures, transport, RECEIVE and destination-local disposition.

## Replaceable provider seam

Registry v1 allows an AI.PROPOSE capability to bind an external process through:

    transport = stdio-json
    command   = operator-owned argv
    shell     = false

The turn payload cannot select or rewrite the command.

The provider receives exactly one request:

    static-os.ai-provider-request/v0

and must return exactly one response:

    static-os.ai-provider-response/v0

A protocol-valid response proves that the configured process returned a conforming message. It does not independently prove model identity, remote service identity, model weights, provider honesty, or proposal correctness.

The committed Alpha and Beta providers are deterministic fixtures. They prove process replacement, not live AI inference.

## reLATTE ownership

This branch targets the already-merged R14 generic opaque-organ aperture and pins:

- repository: the-static-collective/reLATTE
- commit: dcc8cdca84c440aa4294134f020fb7095bf87f24
- src/organ.ts blob: f53e3b8bb2cb2770ad6803ed0ff4287b103ae0ca
- src/roundtrip.ts blob: c459106d60f0760dd065bf1d158834b8cab20238

STATIC OS emits the exact donor-side relatte.opaque-organ-spec/v0 shape expected by that owner.

It does not copy reLATTE signing code.

## Critical laws

    TURN != LOOP
    PROVIDER != AUTHORITY
    PROVIDER RESPONSE != VERIFIED MODEL IDENTITY
    PROVIDER ATTESTATION != INDEPENDENT VERIFICATION
    INFERENCE != DECISION
    COMPUTATION != CROSSING
    CANDIDATE != SIGNED CROSSING
    PROPOSAL != ADMISSION
    DONOR SEMANTICS != SUBSTRATE SEMANTICS
    DESTINATION MEANING REMAINS LOCAL

## Run

Execute Alpha:

    python3 scripts/crank.py turn       fixtures/cranknode-002/capabilities-alpha.json       fixtures/cranknode-002/turn.json       --out /tmp/crank-turn.json

Build a crossing candidate:

    python3 scripts/crank.py candidate       fixtures/cranknode-002/capabilities-alpha.json       /tmp/crank-turn.json       2026-10-07T21:55:00Z

Replace Alpha with Beta by changing only the registry file:

    python3 scripts/crank.py turn       fixtures/cranknode-002/capabilities-beta.json       fixtures/cranknode-002/turn.json

## Explicit non-claims

CRANKNODE-002 does not claim:

- the committed fixture providers are AI models;
- any external SaaS or local model runtime was contacted;
- provider-reported model identity was independently authenticated;
- the proposal is correct;
- a signed reLATTE crossing exists;
- transport occurred;
- a destination received the candidate;
- HOLD, ADMIT, REFUSE, or RETURN occurred;
- a physical crank was used;
- a second TURN occurred automatically.

The next physical/system step can now happen without changing the crank law: point the provider binding at a real local model wrapper, or pass the emitted opaque-organ spec into canonical reLATTE R14.
