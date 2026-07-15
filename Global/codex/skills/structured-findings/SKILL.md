---
name: structured-findings
description: Standard finding format for package reviews, delta reviews, security/performance audits, and repair evidence.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer, delta-reviewer, security-auditor, repair-agent
---

# Structured Findings

## Finding
Required fields:
- `id`
- `severity`: `critical|high|medium|low`
- `category`: `correctness|security|stability|scalability|testing|integration`
- `acceptance_criterion`
- `file`, `line`
- `evidence`
- `reproduction`
- `required_outcome`
- `suggested_scope`

## Rules
- Findings are concrete and blocking for the reviewed scope.
- No style-only findings.
- Return all detectable findings in one report.
- If blocked by missing input, return `blocked` with the exact missing artifact.
