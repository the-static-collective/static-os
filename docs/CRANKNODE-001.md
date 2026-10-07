# CRANKNODE-001 — sovereign turn-based useful-work runtime

## Purpose

CRANKNODE is a small STATIC OS execution primitive. It converts one explicit TURN into one bounded transformation and one durable local receipt.

It is deliberately not a daemon, scheduler, autonomous agent loop, network, authority engine, admission engine, or model host.

The initial stack point is FIVE-DOOR-BOOT-WITNESS-001. Five visible doors may exist at once, but visibility executes nothing. CRANKNODE adds the missing gate between visible possibility and actual work.

## Founding motion

    capability cards
          |
          | inert until selected
          v
    explicit TURN
          |
          | exactly one capability
          v
    bounded handler
          |
          v
    result + receipt
          |
          X STOP

A future turn requires a new request. The runtime contains no automatic continuation path.

## Founding capabilities

- TEXT.HASH — deterministic one-particular digest.
- TEXT.UPPERCASE — deterministic one-particular transformation.
- AI.PROPOSE — replaceable AI-organ seam. The founding handler is intentionally a placeholder and does not call a live model. Its result remains proposal-only.

This makes the authority boundary executable before adding a model provider.

## Run

List capability cards without executing work:

    python3 scripts/crank.py list fixtures/cranknode-001/capabilities.json

Execute the founding single turn:

    python3 scripts/crank.py turn fixtures/cranknode-001/capabilities.json fixtures/cranknode-001/turn.json

Run hostile tests:

    python3 -m unittest tests.test_cranknode -v

## Laws

    TURN != LOOP
    WORK != AUTHORITY
    COMPUTATION != ADMISSION
    INFERENCE != DECISION
    AVAILABLE != SELECTED
    SELECTED != EXECUTED
    EXECUTED != ACCEPTED
    NODE != NETWORK
    TRANSPORT != TRUST
    OFFLINE != DEAD
    PAPER != LOSSY FALLBACK
    HUMAN TURN != HUMAN APPROVAL
    ENERGY != AUTHORITY

## Receipt boundary

The receipt binds the exact canonical JSON request, input payload, result, capability identity, and declared work budget.

The founding receipt is unsigned. It is not a reLATTE crossing and must not be described as one. A later adapter may wrap the exact result/receipt addresses into a reLATTE crossing candidate while preserving destination-local HOLD / ADMIT / REFUSE authority.

The receipt is carrier-neutral canonical JSON. That is the seam for later USB, QR, print, NFC, Bluetooth, LoRa, serial, audio modem, webZ, or ordinary network transport. Carrier support is not claimed until separately executed.

## Physical crank seam

The request schema already accepts source.kind = physical-input. That proves only that a physical event can be represented as the explicit source of a TURN.

CRANKNODE-001 does not claim:

- a rotary encoder was connected;
- crank energy powered computation;
- energy was physically metered;
- a radio or paper carrier moved a receipt;
- a live AI model executed;
- a signed reLATTE crossing occurred;
- any output was admitted locally;
- any next turn occurred automatically.

## Next pressure

The next useful specimen should bind AI.PROPOSE to one replaceable model adapter while keeping the handler contract unchanged, then wrap the resulting unsigned local receipt as a reLATTE crossing candidate. The destination must still make its own disposition.

After that, connect a real rotary encoder or other physical input and prove that one physical tick can authorize one TURN without granting any semantic authority over the result.
