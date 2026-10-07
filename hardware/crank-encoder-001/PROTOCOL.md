# CRANK ENCODER 001 — physical wire protocol

A crank-side device emits one UTF-8 JSON object followed by LF for each **debounced mechanical detent**.

Required frame:

    {
      "schema": "static-os.crank-physical-edge/v0",
      "device_id": "encoder:<stable local hardware id>",
      "session_id": "<fresh id for this device boot/session>",
      "sequence": 42,
      "direction": "CW",
      "ticks": 1
    }

The host accepts exactly one frame, durably consumes its content address, executes at most one turn attempt, and exits.

## Device responsibilities

1. Emit one frame per debounced detent.
2. Keep sequence strictly increasing within a session.
3. Generate a fresh session_id after reset/reboot.
4. Never bundle multiple detents into ticks > 1.
5. Do not encode semantic intent, approval, admission, model choice, or destination authority.

## Host responsibilities

1. Treat the frame as a trigger, not a decision.
2. Refuse duplicate edge identities.
3. Durably consume the edge before invoking work.
4. Never retry a failed turn from the same edge automatically.
5. Keep provider selection outside the physical event payload.
6. Stop after one turn attempt.

## Linux example

A USB microcontroller exposing a serial TTY can be used with:

    python3 scripts/crank-edge.py \
      fixtures/cranknode-002/capabilities-alpha.json \
      AI.PROPOSE \
      fixtures/cranknode-003/payload.json \
      /var/lib/static-os/crank/edge-ledger.jsonl \
      --device /dev/ttyACM0 \
      --baud 115200

That command reads **one** edge and exits. A new invocation is required for another turn.

## Claim boundary

The repository proves the host-side POSIX TTY path with a kernel pseudo-terminal in CI. It does not prove a physical rotary encoder, microcontroller, hand crank, electrical debounce circuit, or power-generation system was attached.
