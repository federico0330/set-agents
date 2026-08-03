---
name: strict-tdd
description: Test-first RED→GREEN→TRIANGULATE→REFACTOR discipline for a package, with a mandatory safety-net baseline run and a banned-assertion-patterns list. Load ONLY when the package declares strict_tdd=true (docs/adr/0022-*.md) -- additive to, never a replacement for, the default test-writer-after-convergence flow.
license: MIT
compatibility: opencode
metadata:
  enabled_for: implementer
---

# Strict TDD

> Load this skill ONLY when the assigned package's state carries `strict_tdd: true`
> (`package-planner` declares it via `create-package --strict-tdd true`). If the package does not declare it,
> follow `implementer.md`'s default procedure instead — writing focused tests as part of the deliverable,
> reviewed but never self-approved, per the project's normal SDD→BDD→implement⇄audit→regression-tests flow.

Ported from `gentle-ai`'s (Gentleman Programming) RDD strict-TDD module, adapted to SET-AGENTES's package
state and output contract (docs/adr/0022-strict-tdd-opt-in.md).

## Philosophy

TDD is not testing — it is **design driven by tests**. A test describes what the code SHOULD do; you then
write the minimum code to make it real. Code is a side effect of the test, not the other way around.

### The Three Laws

1. Do NOT write production code until you have a failing test.
2. Do NOT write more test than is necessary to fail.
3. Do NOT write more code than is necessary to pass.

## The cycle, per task

```
0. SAFETY NET (only when modifying an existing file)
   Run the file's existing tests first. Capture "{N} tests passing" as the baseline.
   If any pre-existing test already fails, STOP and report it as a pre-existing failure --
   do not fix it as part of this task, and do not let it block RED/GREEN below.

1. UNDERSTAND
   Read the task, the acceptance criteria it covers, the context pack's constraints, and the
   existing test patterns in the touched surface (match the repo's style).

2. RED -- write a failing test FIRST
   The test references production code/behavior that does not exist yet, so it fails by
   construction. If the function already exists, write a test for the NEW, not-yet-implemented
   behavior. Do not proceed to GREEN until the test is written.

3. GREEN -- write the MINIMUM code to pass
   Hardcoded/"fake it" values are valid here. Execute the test -- it must pass by running, not by
   inspection. Fix the implementation, never the test, on failure.

4. TRIANGULATE -- mandatory by default
   Add a second test case with different inputs/expected outputs; if GREEN passed trivially
   (hardcoded value), this forces it toward real logic. Minimum: 2 cases per behavior (happy path +
   one edge case). Skip ONLY when the task is purely structural (config constant, type export) with
   literally one possible output -- and note "Triangulation skipped: <reason>" in the evidence table.
   Watch for a GREEN that passes without exercising the code path (a component never rendered, a
   loop over zero items, a setup that never reaches the branch under test) -- that is not a real
   GREEN; triangulate with a setup that DOES exercise it.

5. REFACTOR -- improve without changing behavior
   Extract constants/functions, improve naming, remove duplication, push toward pure functions.
   Re-run tests after EVERY refactor step; revert immediately on any failure instead of chasing it.

6. Mark the task complete and note any deviation.
```

Prefer pure functions in GREEN/TRIANGULATE — deterministic, no side effects, trivially testable.

## Refactoring existing code — approval tests first

Before touching production code you are refactoring (not writing new): write approval tests that assert the
CURRENT output for known inputs (even if it looks wrong), confirm they pass, THEN refactor, then re-run them
— they must still pass. If the spec says behavior should change, update the approval test to the new expected
value first (it now fails, RED), then implement the change (GREEN).

## Test layer and runner

Use the highest test layer available that fits the task (unit for pure logic; integration when the touched
surface needs component/API interaction; E2E only for a critical full user journey) — but never skip a task
because a higher layer is unavailable; degrade to the next one instead. Detect the runner and the relevant
command from the package's own `local_validations` (declared by `package-planner`) or the repo's own tooling
(`package.json`/`pyproject.toml`/`go.mod`/equivalent) — run only the relevant test file during the cycle, not
the full suite; the full suite is `gate-runner`'s job afterward.

## Assertion quality — mandatory, not optional

A test that passes without exercising production logic is worse than no test: it gives false confidence.
Every assertion must (1) call production code, (2) assert a specific expected value derived from the spec,
and (3) actually fail if the implementation were wrong.

**Never write these** (each is worse than no assertion at all):
- Tautologies: `assert True`, `expect(1).toBe(1)`, `assert 1 == 1`.
- An empty-collection assertion (`assert result == []`, `expect(x).toHaveLength(0)`) with no companion test
  that produces a non-empty result from the same setup — you have not proven the emptiness came from real
  logic running, only that nothing ran.
- A type-only assertion used alone (`assert result is not None`, `expect(x).toBeDefined()`) — assert the
  actual value, not just its existence.
- A "ghost loop": an assertion inside a `for`/`forEach` over a collection that can be empty — if it is empty,
  the assertion body never executes and the test always passes regardless of behavior.
- A smoke test (render/call + "it didn't crash") with no assertion on the actual output — accompany it with a
  real behavioral assertion or drop it.
- An assertion coupled to implementation details (CSS class names, internal state, exact mock-call counts)
  instead of user-visible behavior — it breaks on refactors that change nothing observable.

**Mock hygiene**: if a test needs more mocks than assertions, it is testing at the wrong layer. ≤3 mocks is
healthy; 4-6 means consider extracting the logic to a pure function; 7+ means stop and extract — never write
ten mocks to verify a one-line transformation.

## Required output addition

When this skill is active, add a `tdd_evidence` array to `implementer.md`'s existing Output JSON — one entry
per task:
```json
{
  "task_id": "1.1",
  "test_file": "path/to/test.ext",
  "layer": "unit|integration|e2e",
  "safety_net": "5/5 passing | N/A (new file)",
  "red": true,
  "green": true,
  "triangulate": "3 cases | single (structural, no branching)",
  "refactor": "clean | none needed"
}
```
`package-reviewer` (via `strict-tdd-verify`) re-runs the cited RED→GREEN evidence itself — it does not accept
this table as claimed, only as a map of what to re-verify.

## Rules

- Never write production code before its test — the one rule that cannot be broken.
- Never skip the GREEN execution gate — tests must actually run and pass, not be inspected.
- Never skip triangulation when the spec defines multiple scenarios.
- Never write a banned assertion pattern above.
- Always run the safety net before modifying an existing file.
- Always report `tdd_evidence` — the reviewer's audit depends on it existing.
- A test-runner failure for infrastructure reasons (not a real test failure) is a `blocked` stop condition
  per `implementer.md`, not something to work around silently.
