---
description: Multi-lens engineering analysis of an idea, no pipeline
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Analyze this idea in consult mode (see `request-triage` mode 0 — no init, no state, no pipeline):
$ARGUMENTS

Delegate in parallel to `brainstormer` (options + tradeoffs), `architect` (read-only: relational vs
non-relational vs vector store, API Gateway, deploy platform, design patterns / clean architecture), and
`security-auditor` if the idea touches auth/money/PII/external input. Synthesize ONE multi-lens analysis —
data model, architecture/patterns, security, algorithms/complexity — with a recommendation and a runner-up,
in plain language, closing with a claims→evidence table (`file:line`, command output, or URL per claim;
unverified claims marked "sin verificar" — ADR-0026). End by asking whether to turn it into a spec (feature)
or a scoped package. Never start the pipeline from here.
