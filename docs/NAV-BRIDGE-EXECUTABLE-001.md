# NAV BRIDGE EXECUTABLE 001

## Status

This branch proves one MAKE GROUND Bridge Packet can survive several bodies without changing its core distinction.

The invariant is:

> ORIENTATION PRECEDES FORCE.

The executable does **not** take external actions. It produces and extends local receipts so a human or another local process can keep the next consequential act explicit.

## One packet, six bodies

### 1. Book/page view

The full conceptual treatment lives in BRIDGE PACKET 001 — NAV and The Static Textbook chapter “The Loop Must Be Surprised.”

The page explains why recursion is not navigation and why a productive loop still needs an aperture through which consequence can revise its heading.

### 2. Pocket-card view

`cards/NAV-001.md` compresses the packet to seven moves:

1. Name the heading.
2. Protect what matters.
3. Open one aperture.
4. Make one bounded move.
5. Let consequence answer.
6. Record the delta.
7. Reorient.

Compression is allowed because the packet retains a path back to provenance.

### 3. Machine-readable view

`bridge/nav.packet.json` carries the invariant, ancestry labels, doors, card, game action, field experiment, receipt contract and runtime limits.

Validate it:

```sh
python3 scripts/nav.py validate
```

Render the card from the machine object:

```sh
python3 scripts/nav.py card
```

The rendered card is derived from the packet rather than maintained as a second source of truth.

### 4. Game-action view

NAV is represented as a state transition rather than a productivity score.

Before world-contact:

```
ORIENTED → ENCOUNTER
progress_class = awaiting-world-contact
scalar_score = null
```

After world-contact:

```
CONTACTED → REORIENT
progress_class = world-contacted
scalar_score = null
```

Generation alone does not earn “reality” progress. The packet refuses to turn output volume into a proxy for contact.

Inspect the next game event:

```sh
python3 scripts/nav.py game .build/nav/receipt.json
```

### 5. Real-world experiment view

Choose one real change small enough to observe.

Orient it:

```sh
mkdir -p .build/nav

python3 scripts/nav.py orient \
  --heading "Make the next useful change without widening scope." \
  --preserve "reversibility" \
  --preserve "the existing working state" \
  --aperture "one independent observation after the change" \
  --move "Change one bounded thing." \
  --stop "Stop if the preserve set is damaged." \
  --claim-limit "One trial does not establish a final answer." \
  -o .build/nav/receipt.json
```

Then do the bounded move **outside this program**. The runtime deliberately cannot fake that encounter.

After something in the world has answered:

```sh
python3 scripts/nav.py encounter .build/nav/receipt.json \
  --observed "Record only what actually happened." \
  --delta "State the difference between expectation and encounter." \
  --next-heading "Write the heading that follows from where you actually arrived." \
  -o .build/nav/contacted.json
```

### 6. Receipt view

The receipt schema lives at `bridge/nav-receipt.schema.json`.

The runtime has two honest states:

- `oriented`: a heading exists; no world-contact is claimed.
- `contacted`: observed result, delta and next heading are all present.

It refuses a contacted receipt that lacks encounter evidence.

## End-to-end relay

```
PAGE
  ↓ compress
CARD
  ↓ encode
PACKET
  ↓ orient
GAME / RUNTIME
  ↓ bounded move outside runtime
FIELD
  ↓ observe
RECEIPT
  ↓ delta
REORIENT
  ↓
new source material
```

The important test is not whether every body contains identical text.

The test is whether the distinction survives:

- the page may explain;
- the card may compress;
- the runtime may enforce state;
- the game may expose a next verb;
- the field may contradict;
- the receipt may revise the heading.

Different bodies. Same invariant.

## Hostile controls

The proof deliberately refuses several seductive collapses:

- **generation ≠ world-contact** — creating the receipt does not mark it contacted;
- **proposal ≠ effect** — the runtime takes no external action;
- **receipt ≠ score** — game events expose progress classes, not scalar points;
- **orientation ≠ destination** — a contacted receipt may change the next heading;
- **multiple outputs ≠ evidence** — only an explicit encounter can fill observed/delta fields;
- **compression ≠ amnesia** — the machine packet retains ancestry labels.

## Test gate

The existing GENESIS workflow already runs `python3 -m unittest discover -s tests -v`, so `tests/test_nav.py` joins the current hostile contract suite automatically.

The NAV tests assert:

1. the packet keeps its invariant;
2. automatic external effects remain disabled;
3. orientation can become contacted only through an explicit encounter step;
4. fake contact is refused;
5. game state never awards scalar generation points;
6. the pocket card renders from the machine packet.

## What this proves

This is the first executable demonstration of the Bridge Layer rule:

> THE BOOK IS A VIEW, NOT THE CONTAINER.

NAV now exists as prose, card, structured object, state machine, field protocol and receipt without any one representation becoming canonical over all the others.

The canonical continuity lives in the Bridge Packet invariant plus provenance and receipts.

## Next door

If this slice survives review, the strongest second executable packet is probably **WITNESS**, because it can consume a NAV receipt and test whether “what happened,” “what was recorded,” and “what was inferred” remain distinct.

That would make the first genuine packet-to-packet crossing executable:

```
NAV receipt → WITNESS intake
```
