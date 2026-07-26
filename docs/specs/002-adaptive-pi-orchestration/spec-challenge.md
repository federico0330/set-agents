# Spec challenge — 2026-07-24

## Result

`revision_required` was returned with findings SC-01 through SC-08. The orchestrator compared each finding to the
user-approved source plan. No new product behavior was required; the draft had under-specified decisions already
present in that plan or safe fail-closed implementation defaults.

## Findings and resolution

| ID | Severity | Finding | Resolution |
|---|---|---|---|
| SC-01 | blocker | model tier and execution lane overloaded `fast`; lane rules incomplete | separate enums, deterministic lane table, authority, budgets, exits, and ambiguity behavior added |
| SC-02 | blocker | command-only Pi deny boundary permitted tool/symlink/interpreter/gate bypass | common fail-closed dispatch guard, normalization, immutable gate IDs, and parent-only subagent extension added |
| SC-03 | blocker | schema 2 fields/migration semantics incomplete | full fields/defaults/validation plus in-memory schema-1 normalization and atomic explicit schema-2 emission added |
| SC-04 | high | Pi parent scope, aliases, Claude-only state, and reviewer independence unclear | Pi-only Sol/medium scope, explain-only behavior, canonical family, positive alias, and fail-closed review added |
| SC-05 | high | direct task hash and telemetry lifecycle insufficiently private | installation-keyed HMAC, private permissions, allowlist schema, rotation, and persistence-failure behavior added |
| SC-06 | high | rollout and xhigh benchmark criteria non-deterministic | five-run minimum over three classes, no auto-promotion, and a separate paired xhigh threshold added |
| SC-07 | high | dependencies, upstream registry, and CLI schemas incomplete | exact packages/locks, parent-only usage, versioned CLI envelope/exit/reason codes, and upstream registry contract added |
| SC-08 | high | rollback preconditions/interruption behavior undefined | OpenCode preflight, atomic selector-only rollback, preserved Pi state, and private backup recovery added |

## Approval

The corrected contract remains version `1.0.0` because the corrections do not change the approved intent. Its new
hash supersedes the draft hash before implementation begins.
