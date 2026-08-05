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
| [0007](0007-pi-lane.md) | Pi lane: CLI-subprocess spawner, guards-as-flags, exact pin, gated flip | Accepted; superseded in part by 0017 | 2026-07-27 | — | 0017 (install.py target + dispatch-lane skills/prompt-templates closure only) |
| [0008](0008-two-roots-portability.md) | Two roots: `HARNESS_HOME` vs `PROJECT_ROOT`, install-time baking, project-scoped routing | Accepted | 2026-07-27 | — | — |
| [0009](0009-finding-verification.md) | Adversarial refutation of review findings before repair | Accepted | 2026-07-27 | — | — |
| [0010](0010-spawn-accounting.md) | Spawn accounting: what a Pi spawn actually cost, persisted and not fabricated | Accepted | 2026-07-29 | — | — |
| [0011](0011-uninterrupted-delegation.md) | Uninterrupted delegation: when a turn may end, and what independence really buys | Accepted | 2026-07-28 | — | — |
| [0012](0012-mandatory-vault.md) | Mandatory vault: topology intent, merge-aware migration, honest multi-OS install | Accepted | 2026-07-29 | — | — |
| [0013](0013-execution-graph-view.md) | Execution graph view: derived-in-read, closed edge vocabulary, fail-open commits | Accepted; superseded in part by 0014 | 2026-07-30 | — | 0014 (spawn node deferral only) |
| [0014](0014-spawn-provenance-node.md) | Spawn provenance node: a package-scoped mint, not a rename of `run_id` | Accepted | 2026-07-30 | 0013 (spawn node deferral only) | — |
| [0015](0015-quota-failover.md) | Quota failover is a new linked dispatch, not fallback-window reuse | Accepted | 2026-07-30 | — | — |
| [0016](0016-discovered-inventory.md) | Discovered inventory: two providers, two maps, four gates, one collision rule | Accepted | 2026-07-31 | — | — |
| [0017](0017-pi-interactive-target.md) | Pi interactive target: fourth generated harness tree, install target, collision guard, dispatch-lane closure | Accepted | 2026-08-02 | 0007 (install.py target + dispatch-lane skills/prompt-templates closure only) | — |
| [0018](0018-model-preference-policy.md) | Model preference policy: a closed role-class taxonomy, one tie-break sort-key element, never a second decision-maker | Accepted | 2026-08-02 | — | — |
| [0019](0019-anthropic-dispatch-parity.md) | Anthropic dispatch parity: the Claude-Code-lane redirect, its tool ceiling, and the day-13 boundary | Accepted | 2026-08-01 | — | — |
| [0020](0020-direct-read-vs-delegated-explore-threshold.md) | Direct-read vs. delegated-explore threshold: a file-count rule for the orchestrator's own reading | Accepted | 2026-08-03 | — | — |
| [0021](0021-readability-resilience-checklists.md) | Readability/resilience as `package-reviewer` checklist dimensions, not new agents | Accepted | 2026-08-03 | — | — |
| [0022](0022-strict-tdd-opt-in.md) | Strict TDD as an opt-in per-package mode, additive to the default flow | Accepted | 2026-08-03 | — | — |
| [0023](0023-bounded-repair-ceiling.md) | Bounded repair: a line-count ceiling frozen once per cycle, tied to the existing retry budget | Accepted | 2026-08-03 | — | — |
| [0024](0024-integration-receipt-hook.md) | Integration receipt: a git tree-hash freeze gating `PACKAGE_ACCEPTED→INTEGRATION` | Accepted | 2026-08-03 | — | — |
| [0025](0025-resolve-first-autonomy.md) | Autonomía "resolver primero, registrar siempre": credenciales, deploy nombrado, auto-instalación de CLIs/MCPs | Accepted | 2026-08-04 | — | — |
| [0026](0026-evidence-over-memory.md) | Evidencia sobre memoria: fuentes obligatorias, WebSearch/WebFetch en análisis, skill spawn-prompt | Accepted | 2026-08-04 | — | — |
| [0027](0027-milestone-narration-digest.md) | Narración por hito, digest matinal generado, notas como entrada | Accepted | 2026-08-04 | — | — |
| [0028](0028-living-scope.md) | Alcance vivo: re-verificación de spec hash, amend-spec, supersede-package | Accepted | 2026-08-04 | — | — |
| [0029](0029-probe-driven-model-selection.md) | "El probe manda": inventario descubierto como fuente de verdad de modelos | Accepted | 2026-08-04 | — | — |
| [0030](0030-decide-always-materialize-per-lane.md) | Decide siempre: una decisión de routing por spawn (28/28 roles), materializada según el lane | Accepted | 2026-08-04 | — | — |
| [0031](0031-per-spawn-routing-observability.md) | Observabilidad por spawn: log de decisiones (simulate incluido), campos estructurados en record-spawn, join route_id | Accepted | 2026-08-05 | — | — |
| [0032](0032-spawn-time-model-materialization-and-pins.md) | Materialización en el spawn para opencode/codex (CLIs de dispatch) y pins de modelo: pin > dinámico > fallback | Accepted | 2026-08-05 | — | — |
