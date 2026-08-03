---
name: strict-tdd-verify
description: Independent, read-only audit of an implementer's strict-TDD evidence (RED/GREEN re-run, triangulation adequacy, assertion-quality scan for banned patterns) -- load ONLY when the package declares strict_tdd=true (docs/adr/0022-*.md). Findings fold into package-reviewer's normal structured-findings output, category testing.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer
---

# Strict TDD Verify

> Load this skill ONLY when the reviewed package's state carries `strict_tdd: true`. It does not replace
> `test-gap-analysis` — it adds a specific audit that the claimed RED→GREEN cycle was real, not merely
> reported. Findings from this audit are ordinary structured findings (`category: testing`), consolidated
> into the same report `package-reviewer.md` already returns — this is not a second reviewer role.

Ported from `gentle-ai`'s (Gentleman Programming) RDD strict-TDD verify module, adapted to read
`implementer.md`'s `tdd_evidence` output instead of a separate artifact file
(docs/adr/0022-strict-tdd-opt-in.md).

## Do not trust the report — re-verify it

`implementer` returns a `tdd_evidence` table (one row per task: test file, layer, safety net, red, green,
triangulate, refactor). Your job is to check that evidence against reality, the same read-only,
evidence-checking posture you already use for every other finding:

1. **RED** claimed "written" → the named test file must exist in the diff and must reference the behavior it
   claims to test.
2. **GREEN** claimed "passed" → re-run that exact test file yourself. If it fails now, that is a
   `critical`/`testing` finding: the claimed GREEN was never real, or a later change silently broke it.
3. **TRIANGULATE** → if it claims "N cases", count them in the test file; if it claims "single" for a
   structural/no-branching task, confirm the task really has no branching — a claimed "single" on a task with
   multiple spec scenarios is a `medium`/`testing` finding (insufficient triangulation).
4. **SAFETY NET** → if the task modified an existing file, the row must show a real baseline count, not
   "N/A" — a modified file with no safety net is a `medium`/`testing` finding (the pre-change behavior was
   never captured).
5. **No `tdd_evidence` at all**, on a package declared `strict_tdd: true` → a `high`/`testing` finding: the
   protocol was enabled but not followed, not merely under-documented.

## Assertion quality audit (mandatory whenever this skill is active)

Scan every test file the package touched for the banned patterns `strict-tdd` itself prohibits:

- **Tautology** (`assert True`, `expect(1).toBe(1)`) → `critical`/`testing`: the test proves nothing.
- **Assertion with no production-code call** → `critical`/`testing`: nothing under test actually ran.
- **Ghost loop** (assertion inside a loop over a collection that can be empty, with no prior assertion that
  the collection is non-empty) → `critical`/`testing`: the assertion may never execute.
- **Orphan empty-collection assertion** (no companion non-empty-result test from the same setup) →
  `medium`/`testing`.
- **Type-only assertion used alone** (`toBeDefined()`, `is not None`, with no value assertion) →
  `medium`/`testing`.
- **Smoke-test-only** (render/call with no assertion on actual output) → `medium`/`testing`.
- **Implementation-detail coupling** (CSS class names, internal state, exact mock-call counts instead of
  observable behavior) → `medium`/`testing`.
- **Mock-heavy test** (mock count > 2× assertion count in one test file) → `medium`/`testing`, suggesting
  extraction to a pure function or a higher test layer.

Every violation is a normal structured finding: `id`, `severity`, `category: testing`, `file`, `line`,
`evidence` (the exact assertion text), `reproduction` (why it passes without proving anything),
`required_outcome` (what a real assertion here would need to check), `suggested_scope`.

## What this audit does NOT do

- It does not gate on coverage percentage or linter/type-checker output — those stay informational, folded
  into the ordinary review if `test-gap-analysis` already surfaces them; this skill's own findings are always
  `medium` or above, never a soft "suggestion" bucket SET-AGENTES's finding schema has no room for.
- It does not re-run the whole suite — that is `gate-runner`'s job; re-running the specific cited test files
  is enough to confirm or refute the claimed GREEN.
- It does not replace or duplicate `finding-verifier`'s adversarial refutation — findings this audit raises
  flow into the normal panel → refutation → repair pipeline like any other finding.

## Rules

- Always re-run the cited test file for a claimed GREEN before trusting it.
- Always run the full assertion-quality scan when this skill is active — a skipped scan is itself a finding
  against the reviewer's own report, not a silent pass.
- A missing `tdd_evidence` table on a `strict_tdd: true` package is `high` severity, reported immediately, not
  inferred as "probably fine".
- Do not fix anything — you are read-only, per `package-reviewer.md`'s own Must NOT list. Report only.
