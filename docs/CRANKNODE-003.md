# CRANKNODE-003 — physical edge → one turn attempt

## Purpose

Give the crank law an actual hardware boundary without pretending CI owns a hand crank.

CRANKNODE-003 accepts one newline-framed rotary/serial edge through a POSIX TTY, durably consumes that edge, derives one ordinary CRANKNODE turn request, executes at most one capability, optionally derives the already-defined unsigned reLATTE candidate, and exits.

    mechanical detent
          |
          v
    serial JSON edge
          |
          v
    durable one-shot gate
          |
          | edge consumed first
          v
      one TURN attempt
          |
          v
     result + receipt
          |
          v
    optional unsigned
    reLATTE candidate
          |
          X
         STOP

## New hard law

    ONE PHYSICAL EDGE = AT MOST ONE TURN ATTEMPT

This is intentionally stricter than "one edge = one successful turn."

If a provider process fails after the edge is consumed, the same physical edge does not acquire retry authority. A new physical act is required for another attempt.

## Bounce and replay

An edge identity binds:

- device_id
- session_id
- sequence
- direction
- ticks = 1

The host stores the content-addressed edge in an append-only JSONL ledger under an exclusive file lock before work starts.

The same edge presented again is refused.

A reset device must generate a new session_id. A different session can reuse a sequence number without becoming the old physical act.

## Real TTY boundary

The host implementation uses Python stdlib POSIX interfaces:

- os.open
- termios
- select
- fcntl
- fsync

No serial daemon is required.

One invocation reads one newline frame and exits.

The hostile suite exercises this path through a real kernel pseudo-terminal. That proves TTY framing and host behavior, **not physical hardware presence**.

## Reference hardware

hardware/crank-encoder-001/esp32/crank_encoder_001.ino is a minimal ESP32 reference emitter for a quadrature rotary encoder.

The microcontroller only reports a physical event. It cannot choose:

- the AI/model provider;
- the work capability;
- semantic meaning;
- admission;
- destination disposition;
- another turn.

## Existing 002 composition

A physical edge can drive the existing CRANKNODE-002 path without new authority:

    edge
      -> AI.PROPOSE
      -> external provider process
      -> proposal-only result
      -> local receipt
      -> relatte.opaque-organ-spec/v0 candidate
      -> STOP

The candidate is still unsigned until canonical reLATTE acts.

## Explicit non-claims

This repository has not observed:

- a real rotary encoder;
- an actual hand crank;
- a microcontroller connected to this host;
- electrical or mechanical debounce performance;
- crank-generated electrical energy;
- model inference powered by crank energy;
- a signed reLATTE crossing caused by physical hardware;
- destination HOLD / ADMIT / REFUSE / RETURN from such hardware.

Those require a physical execution witness.
