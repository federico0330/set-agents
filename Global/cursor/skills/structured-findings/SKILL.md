---
name: structured-findings
description: Standard finding format for package reviews, delta reviews, security/performance audits, and repair evidence.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer, delta-reviewer, security-auditor, finding-verifier, repair-agent
---

# Structured Findings

## Finding
Required fields:
- `id`
- `severity`: `critical|high|medium|low`
- `category`: `correctness|security|data-integrity|scalability|readability|resilience|testing|integration`
  (`data-integrity` reconciles a pre-existing naming drift with this same field's `stability` spelling —
  `package-reviewer.md`'s own data-integrity checklist was always the enforced one; `readability`/`resilience`
  are new, added alongside the checklists of the same name — ADR-0021)
- `acceptance_criterion`
- `file`, `line`
- `evidence`
- `reproduction`
- `required_outcome`
- `suggested_scope`

## Verdict (finding-verifier only)
A finding leaves the open set three ways: repaired (`closed`), explicitly accepted as won't-fix (`accepted`),
or refuted before repair (`refuted`). A verdict has:
- `id` — the finding it judges
- `verdict`: `upheld|refuted`
- `reason` — required for `refuted`
- `evidence` — required for `refuted`: the `file:line` that contradicts the finding, the command run and its
  actual output, or the acceptance criterion that sanctions the behaviour

A refutation carries the same evidentiary burden the finding did. Without both `reason` and `evidence` it is
not a refutation and the finding stands. When in doubt, `upheld` — killing a real defect is worse than one
unnecessary repair. A refuted finding is never deleted; it keeps its verdict in the package record.

## Rules
- Findings are concrete and blocking for the reviewed scope.
- No style-only findings.
- Return all detectable findings in one report.
- If blocked by missing input, return `blocked` with the exact missing artifact.
