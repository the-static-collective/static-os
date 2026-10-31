# RECOMPOSER-001 — The Machine That Rebuilds Its Working Graph

Status: **proof of concept / PROPOSAL_ONLY**, Static-OS userspace experiment stacked on APPARATUS-COMPILER-002. It does not alter OS boot, Debian, GHoT authority, reLATTE, AI models, public websites or physical equipment.

## Answer

A deterministic program can compile a fresh typed working graph on every interaction and can acquire reusable compound operators through **explicit, consented feedback**. This is bounded self-recomposition, not autonomous source-code rewriting and not a guarantee that intelligence rises after every turn.

## One turn

    QUESTION
       ↓
    READ declared safe operators and current preference policy
       ↓
    RANK candidate roles with explicit, integer scores
       ↓
    COMPILE a fresh typed DAG under resource limits
       ↓
    VERIFY port types and bounded graph size
       ↓
    RETURN relevant public destinations as PROPOSAL_ONLY
       ↓
    OPTIONAL HUMAN FEEDBACK (helpful / not_helpful)
       ↓
    CONTENT-ADDRESSED event / cold replay of changed policy
       ↓
    NEXT QUESTION: compile a DIFFERENT graph as appropriate

For "music and food" the first plan uses six operator nodes and proposes a two-route compound. Nothing automatically installs it. If a person explicitly consents, reports a suggestion helpful, and separately authorizes reuse, a later question can use a new *three-node* combined macro. The graph really changes: reassembly and a saved recipe, not just a label.

That proves **structural compression** and the capacity for user-directed adaptation. It does NOT prove more accurate judgments, independently measured usefulness, faster execution, autonomous invention of novel capabilities, or verified real-world outcomes.

## Determinism, custody and safety

- The same input, state and operator catalogue yields the same plan and address.
- Operators are typed, fixed and allowlisted. No arbitrary code generation or shell execution.
- Max eight graph operators, max 320-character question, bounded integer weights.
- Unknown topics remain explicitly uncertain; no forced category.
- Reading a question never mutates the state. An explicit feedback call returns a new state object; **the library never stores it**. No question text appears in event history, and no network is used.
- Self-reported feedback may change local ranking and allow a compound macro, but it is not independently verified evidence of success.
- Feedback is append-only and content-addressed. Replay catches inconsistent edits; **a local hash chain is not a digital signature** against an attacker with write access.
- No actual GHoT process, hardware, AI, person, email, service or community partnership is contacted or authorized.

## Proof

Run from the Static-OS repository root:

    python3 -m unittest tests.test_recomposer_001 -v

Example Python session:

    from question_first.recomposer import genesis, compile_turn, observe_feedback
    state = genesis()
    first = compile_turn(state, "Could food and music share a table?")
    # Inspect first["operators"], first["candidate_recipe"].
    revised = observe_feedback(state, first, first["topics"][0],
                               "helpful", consent=True, promote_recipe=True)
    second = compile_turn(revised, "Could food and music share a table?")
    # second["operator_count"] < first["operator_count"]

The tests cover deterministic compilation, topic-sensitive graph selection, proposal-only compound, explicitly promoted macro, shorter subsequent graph, changed preferences, stale-plan refusal, tamper detection, unknown questions and input budget.

## Existing source-owned neighbors

**Static-OS QUESTION-FIRST-SESSION-001** already has question → two candidate experiments → owner selection → GHoT signed bounded simulation → verified return → next proposed question.

**Static-OS APPARATUS-COMPILER-002** has missing capability → discovery of opted-in native GHoT cards → typed assemblies → human selection → single bounded simulation → replay.

**GHoT FAILURE-AWARE RECOMPOSITION** keeps failed attempt evidence and rebuilds the next plan with an excluded failed node, up to its retry limit.

RECOMPOSER-001 is the missing small piece: the proposal graph can change *with the conversation*, the local preference policy can change after voluntary feedback, and earlier validated compositions can become selectable macro instruments. It does not merge those existing execution systems or import their authority.

For JAR;VIS on hello.abundent.org, an adapter can later use this compilation logic to offer a personally relevant path. The live Hello site is NOT connected to this experiment.

## Next necessary gates

1. Compare new policies against held-out owner-approved cases and the old policy, with a defined metric; reject regressions and do not claim that smaller graphs are smarter.
2. Keep newly generated operators as typed candidates pending tests and explicit owner admission. Do not let a visitor's words become executable code or an automatically authorized external action.
3. Require opt-in, private, revocable persistence before long-term user-specific learning.
4. Let a GHoT owner deliberately supply genuine availability/energy/cost evidence; never infer authorization from discovery.
5. Keep a known-good snapshot, test a challenger in shadow, promote only after evidence and operator choice, and support rollback.

**Law:** RECOMPOSE != REWRITE ROOT; FEEDBACK != VERIFIED OUTCOME; SMALLER GRAPH != GREATER INTELLIGENCE; NEW GRAPH != NEW AUTHORITY; QUESTION != COMMAND.
