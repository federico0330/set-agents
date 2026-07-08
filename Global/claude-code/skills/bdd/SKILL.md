---
name: bdd
description: Behavior-Driven Development — the behavioral validation layer between SDD (architectural intent) and the implement⇄audit loop. Turn business rules into Given-When-Then scenarios in acceptance.md, the bridge between product and technology, and verify the system as a whole satisfies them. Load when writing acceptance criteria or verifying that the running system behaves.
license: MIT
compatibility: opencode
metadata:
  enabled_for: product-analyst, test-writer, orchestrator, runtime-verifier
---

# Behavior-Driven Development (BDD)

## When to use
After SDD has fixed the WHAT (spec + rules + contracts), before the implementation is built. BDD validates the
BEHAVIOR: does the system, as a whole, do what the business and the user need? It is the bridge between product
and technology. Order of the stack: **SDD → BDD → implement⇄audit loop → regression tests**.

## Flow
1. For each business rule in `spec.md`, write one or more scenarios in `acceptance.md` as **Given / When / Then**
   in plain business language (not implementation terms): the precondition, the action, the observable outcome.
2. Keep it outside-in and whole-system: describe what the user/actor observes, not internal calls or fields.
3. Cover the happy path AND the behavior that matters to the business (conflict, expiry, empty, unauthorized,
   limits) — each as its own scenario with an expected result/status.
4. Hand the scenarios down: they drive the implement⇄audit loop (the auditor checks the implementation against
   them) and, once the implementation converges, `test-writer` derives the end-stage regression tests from them;
   `runtime-verifier` confirms them against the running app.

## BDD vs SDD vs regression tests (keep the layers distinct)
- **SDD** = intent: rules, contracts, invariants, security constraints, architecture. The what and the why.
- **BDD** = observable behavior of the whole system, in business language. Given-When-Then. The bridge.
- **Regression tests** = technical correctness of the converged implementation, written at the end (never as a
  guardrail to implement). A green test does not prove correctness — it can pass without returning what the spec
  expects; the auditor is the guardrail. The tests lock in behavior once it is already correct.

## The connection point — walk the human through it
The BDD phase is where you and the user **co-imagine the flow before any code**. Be richly descriptive here —
this is the deliberate exception to "terse in execution":
- Narrate each Given-When-Then as a short journey: who acts, what they do, what they observe — in plain language.
- Draw the flow as a portable **ASCII/Unicode diagram** (one lane per scenario: actor → action → observable
  outcome; or a vertical step/state flow). It renders in any console. Add a mermaid block only where the
  surface renders it. Persist the diagram inside `acceptance.md` so it is durable, not just chat.
- **Preview the road ahead** so the user knows what to expect and what each step decides: BDD sign-off →
  implement⇄audit loop → regression tests → verify → audit panel → judge → release.
- Invite the user to reshape the scenarios ("¿es este el flujo que imaginabas? ¿falta un caso?"). Descend to
  implementation only once they are aligned. This is a genuine sync, not a status dump.

Example (portable, renders anywhere):

    Actor        Action                          Observable outcome
    ─────        ──────                          ──────────────────
    User  ──▶ submit a reservation          ──▶ 201, seat held for 10 min
    User  ──▶ pay after the hold expired    ──▶ 409, "hold expired", seat released
    Guest ──▶ open another user's booking   ──▶ 403, nothing leaked

## Verification (close the loop)
A scenario that is written but never checked does not count. Every Given-When-Then must be verified against the
system: `runtime-verifier` drives the running app and checks the observable outcome (rendered result, HTTP
status code) for UI/runtime behavior; a deterministic gate covers non-UI behavior. Unverified behavior is a
gap, not a pass.

## Rules
- Each scenario traces back to a named business rule in `spec.md` and forward to at least one end-stage
  regression test.
- Business language, observable outcomes — no internal method names, field types, or return shapes.
- Never invent behavior the spec does not state; a scenario that contradicts the spec is a defect to resolve.

## Inputs / Outputs
- In: `spec.md` (business rules) + the SDD acceptance criteria. Out: Given-When-Then scenarios in
  `acceptance.md`, ready to drive the implement⇄audit loop, the end-stage `test-writer` regression tests, and
  `runtime-verifier` (end-to-end confirmation).
