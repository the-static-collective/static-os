# RECOMPOSER-002 — The Haunted Toaster's Memory, in the Recursive Workshop

**Status:** experimental, local, proposal-only. Stacked on RECOMPOSER-001 and APPARATUS-COMPILER-002. This is a generic analogue of Haunted Toaster's memory loop, **not** an import or modification of Haunted Toaster's rendering authority or a deployment to Hello.

## What we found already working in Haunted Toaster

The public `the-static-collective/the-haunted-toaster` main tree has working source for:

- `src/full-measure/src/memory/receipt-archive.cjs` — durable archived render evidence;
- `human-verdict.cjs` — 1–5 rating with KEEP / WEIRD / COMPOST; append-only testimony, not a changed render;
- `memory-projection.cjs` — rebuildable, deterministic experience summary and feature relationships;
- `memory-capsule.cjs` — bounded coverage, relationship, and saturation pressures from a current song and history;
- `influence-trace.cjs` — evidence-addressed reasons for candidate pressure;
- canonical VisualScore / ResolvedTimeline and six-up families under Toaster's separate admission authority.

The crucial sentence in its original design is: **memory can change what the Toaster is inclined to try; it cannot change what actually happened.**

## What 002 adapts

Instead of stealing creative source records or teaching the Toaster to direct volunteers, Static-OS implements the *same architecture over its own generic, consented interaction receipts*:

```
a new person's question
    → RECOMPOSER-001 typed composition plan
    → rebuild witness-memory projection from owner-authorized feedback
      and separately consented, self-attested output-artifact observations
    → bounded influence capsule
       (underexplored / previously helpful / counterexample / overrepeated)
    → a family of distinct source-relevant route proposals (up to six)
    → evidence-addressed influence trace
    → visitor can inspect and choose; nothing executed
    → separate explicit helpful/not helpful feedback, optionally approved macro
    → new source-derived projection on next turn
```

All new code remains pure Python. The module does not write to disk, touch the network, call a model, read private visitor text from history, dispatch GHoT, validate a Haunted Toaster score or render anything.

**Learning from something made (without a thumbs-up).** The added `witness_artifact(plan, topic, output_sha256, consent=True)` constructs a content-addressed **self-attested** observation referring to a materialized output hash supplied by the owning caller. The module does not read the output, validate that it exists, persist the record, or independently authenticate the creator. If the caller deliberately preserves that receipt and supplies it on the next turn, the projection's observed-artifact coverage changes and the machine can recommend an *underexplored* relevant route, without pretending the artifact was good, verified, or socially beneficial. Duplicate or modified receipts are rejected. A third-party receiver or actual Toaster renderer remains the authority over its own deliverables.

A new visitor does not inherit another visitor's observations. The code has no default cross-user memory, and caller choice remains necessary before saving any receipt.

**No fake six-up.** If only one relevant topic exists, exactly one candidate exists. If two exist, we vary scope and ordering without adding unrelated capabilities. Candidates are not new autonomous instruments; they are different route proposals. The earlier Static-OS typed graph still owns the proposed composition.

The evidence ledger is self-reported, and hash-addressing is not cryptographic human identity verification. A "helpful" verdict is not proof that a neighbor was helped.

## Show the change

```python
from question_first.recomposer import genesis, compile_turn, observe_feedback
from question_first.recomposer_witness import compile_candidate_family, witness_artifact

state = genesis()
p0 = compile_turn(state, "music and food")
f0 = compile_candidate_family(state, p0)
print(f0["capsule"]["pressures"])
print(f0["candidates"])

# Only if an actual visitor deliberately reports it useful:
state = observe_feedback(state, p0, "music", "helpful", consent=True)
p1 = compile_turn(state, "music and food")
f1 = compile_candidate_family(state, p1)
assert f0["family_id"] != f1["family_id"]
print(f1["influence_trace"]["evidence_refs"])

# An additional, separately consented observation from an actual output:
receipt = witness_artifact(p1, "music", "a" * 64, consent=True)
# Demonstration only: "a" * 64 is a placeholder, not an observed output digest.
f2 = compile_candidate_family(state, p1, [receipt])
assert f2["family_id"] != f1["family_id"]
```

Tests: `python3 -m unittest tests.test_recomposer_001 tests.test_recomposer_witness_002 -v`.

## Architectural seams and boundaries

1. **Haunted Toaster is the only authority over its VisualScore, ResolvedTimeline, render receipts and creative admission.** Static-OS never writes them or claims Toaster KEEP verdicts are community consensus.
2. **STATIC OS owns only typed computation and the local operator's question/feedback proposal.** A source-owned adapter may export a carefully reviewed influence-only packet, but no Toaster memory data is silently merged with someone's personal use of Hello.
3. **GHoT can be a distinct, source-owned capability observer.** Its readings remain evidence of a claimed offer, not an execution grant. No GHoT integration is wired here.
4. **JAR;VIS is an attendant and user-facing interpreter.** A user should see "Here's one thing I'd try" and can correct it, not a taxonomy or mutable hyper-technical lineage graph.
5. **Any learning persistence is a separate, explicit opt-in.** With no consent, ephemeral recomposition can still work, but it cannot truthfully claim to learn across sessions.
6. **The Next Paper is a consent-aware outcome surface**, not a user-data sink: actual results require independent confirmation and permission before publication.

## Next proof gates

- Replay real consented interaction fixtures into a bounded **six-up variant comparison** using objective held-out evaluation and a known-good fallback; current variants are *choices*, not demonstrated gains in intelligence.
- Add source-pinned capability availability from GHoT without copying its authority.
- Separate memory per voluntary actor and project; no hidden universal store, no cross-user transfer, no leakage of private question text.
- Export only reduced source-owned influence metadata from Toaster *if the Toaster operator explicitly chooses it*; never treat a Toaster memory capsule as authorization to run a community task.
- JAR;VIS/Hello can present a private "this helped / not helpful" control, with clear retention/withdrawal and a reversible policy gate before any persistent learning. The live website is unchanged.

**Laws:** REMEMBERED ≠ OBEYED; PROPOSAL ≠ ACCEPTANCE; INFLUENCE ≠ EXECUTION; CREATIVE KEEP ≠ HUMAN SERVICE; REASSEMBLY ≠ PROVEN IMPROVEMENT; NO HISTORY REWRITTEN.
