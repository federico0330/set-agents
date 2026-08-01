# ADR Index

> One row per ADR, no exceptions. `architect` updates this on every new ADR. An ADR is never deleted or
> edited retroactively — a superseded decision gets a new ADR (`Accepted`) and the old one is marked
> `Superseded by ADR-XXXX` here and in the file itself.

| ADR | Title | Status | Date | Supersedes | Superseded by |
|---|---|---|---|---|---|
| [0002](0002-generated-multi-harness.md) | Generate three harnesses from one roster | Accepted | 2026-07-08 | — | — |
| [0003](0003-models-toml-source-of-truth.md) | Use `models.toml` as the model source of truth | Accepted | 2026-07-24 | — | — |
| [0004](0004-adaptive-routing-pi-runtime.md) | Deterministic adaptive routing with opt-in Pi runtime | Superseded in part by 0005 | 2026-07-24 | — | 0005 (routing journal only) |
| [0005](0005-trusted-routing-sqlite-lifecycle.md) | Trusted routing lifecycle in local SQLite | Accepted | 2026-07-24 | 0004 (routing journal only) | — |
| [0006](0006-adaptive-dispatch-cache-and-facts.md) | Adaptive dispatch: hybrid fact derivation and probe cache (AM-1/AM-2) | Accepted | 2026-07-26 | — | — |
| [0007](0007-pi-lane.md) | Pi lane: CLI-subprocess spawner, guards-as-flags, exact pin, gated flip | Accepted | 2026-07-27 | — | — |
| [0008](0008-two-roots-portability.md) | Two roots: `HARNESS_HOME` vs `PROJECT_ROOT`, install-time baking, project-scoped routing | Accepted | 2026-07-27 | — | — |
| [0009](0009-finding-verification.md) | Adversarial refutation of review findings before repair | Accepted | 2026-07-27 | — | — |
| [0010](0010-spawn-accounting.md) | Spawn accounting: what a Pi spawn actually cost, persisted and not fabricated | Accepted | 2026-07-29 | — | — |
| [0011](0011-uninterrupted-delegation.md) | Uninterrupted delegation: when a turn may end, and what independence really buys | Accepted | 2026-07-28 | — | — |
| [0012](0012-mandatory-vault.md) | Mandatory vault: topology intent, merge-aware migration, honest multi-OS install | Accepted | 2026-07-29 | — | — |
| [0013](0013-execution-graph-view.md) | Execution graph view: derived-in-read, closed edge vocabulary, fail-open commits | Accepted; superseded in part by 0014 | 2026-07-30 | — | 0014 (spawn node deferral only) |
| [0014](0014-spawn-provenance-node.md) | Spawn provenance node: a package-scoped mint, not a rename of `run_id` | Accepted | 2026-07-30 | 0013 (spawn node deferral only) | — |
| [0015](0015-quota-failover.md) | Quota failover is a new linked dispatch, not fallback-window reuse | Proposed | 2026-07-30 | — | — |
| [0016](0016-discovered-inventory.md) | Discovered inventory: two providers, two maps, four gates, one collision rule | Accepted | 2026-07-31 | — | — |
| [0019](0019-anthropic-dispatch-parity.md) | Anthropic dispatch parity: the Claude-Code-lane redirect, its tool ceiling, and the day-13 boundary | Accepted | 2026-08-01 | — | — |
