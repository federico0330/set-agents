# Adaptive orchestration and Pi runtime

## Supersession notice

This feature's approved `1.0.0` contract and blocked P1 evidence remain historical records. Its routing behavior is
superseded by [003-trusted-routing-pi-runtime](../003-trusted-routing-pi-runtime/spec.md), drafted after the P1
trusted-catalog, observations, writer-identity, and crash-safe telemetry issues required a replacement contract.
P2 and P3 remain paused pending acceptance of 003/P1R. This notice does not alter the approval or evidence below.

## Approval

- Version: `1.0.0`
- Status: `Approved`
- Approval source: user-provided implementation plan, 2026-07-24
- Contract hash: recorded in `ai/state/features/002-adaptive-pi-orchestration.json`

## Problem

SET-AGENTES currently generates and manages three harnesses but lacks a first-class runtime that can use existing
OpenAI Pro and Claude Max OAuth subscriptions. Its orchestration flow also applies more LLM ceremony than simple,
low-risk tasks require, which increases latency and cost without increasing correctness.

## Users

- SET-AGENTES maintainers operating the harness across IEY projects.
- Project teams that need explainable, proportional orchestration without new API keys.
- Auditors who need deterministic evidence for routing, permissions, gates, and rollback.

## In scope

- Add Pi as a fourth generated, installable, updatable, drift-detectable, status-visible, and rollback-safe
  harness beside OpenCode, Claude Code, and Codex.
- Generate all 28 Pi roles from the existing canonical roster, prompts, capabilities, and tool policy.
- Pin audited Pi runtime dependencies with integrity data and install them into a SET-AGENTES-managed directory.
- Run Pi children with fresh context, an explicit context pack, minimum tools, no nested delegation, and mandatory
  hard-denies for secrets, protected paths, privilege escalation, broad recursive deletion, force-push, and
  repository deletion.
- Add a deterministic `route_task` implementation over a structured `TaskEnvelope` and produce explainable
  `RouteDecision` values from an approved route catalog.
- Evolve `models.toml` to schema 2 while accepting and migrating schema 1.
- Add proportional `direct`, `fast`, `scoped`, `feature`, and `incident` execution lanes plus a deterministic
  allowlisted `harness_gate`.
- Record privacy-preserving local routing telemetry and aggregated metrics.
- Add Pi doctor, route explanation, and routing report CLI surfaces.
- Record the Gentle-AI upstream reference and deliberate SET-AGENTES deviations.
- Keep the Pi/OpenCode bridge present only as a disabled future integration point.

## Observable behavior

1. A reproducible generation run produces semantically equivalent role, capability, and tool policy artifacts
   for OpenCode, Claude Code, Codex, and Pi.
2. Managed Pi install/update/drift/status/rollback operations never overwrite unrelated user configuration.
3. Pi children cannot delegate and denied operations are blocked before process execution.
4. Routing rejects ineligible providers/models/tools/contexts and returns only catalog-owned route identifiers.
5. Parent Pi activation fails clearly unless the catalog resolves GPT-5.6 Sol or the official `gpt-5.6` alias.
6. Reviewer routing excludes the implementer's model family and prefers another provider when both are usable.
7. A low-risk documentation task resolves to one specialist plus one native gate, without the full SDD/review
   pipeline, and obeys its 18/20/30-minute timing policy.
8. Telemetry contains task hashes/classes and operational metrics but no raw prompts, code, secrets, credentials,
   or PII.
9. Existing schema-1 configuration and all three existing runtimes continue to work.

## Model tiers and execution lanes

`model_tier` and `execution_lane` are separate enums. The task envelope never uses the bare word `fast` for both:

| `model_tier` | Deterministic trigger | Effort |
|---|---|---|
| `fast` | extraction, inspection, documentation, or mechanical transformation without a critical surface | `low` |
| `balanced` | ordinary implementation or multi-file documentation without a critical surface | `medium` |
| `frontier` | architecture, security, money, migration, concurrency, public contract, or high ambiguity | `high` |

| `execution_lane` | Entry rule | Spawn/gate budget | Exit |
|---|---|---|---|
| `direct` | read-only consult/status/known local inspection; no delegated context needed | 0 spawns; no LLM gate | answer/evidence |
| `fast` | low-risk, bounded, one-role task with an allowlisted deterministic gate | 1 normal spawn; 1 eligible fallback; 1 native gate | pass, safe checkpoint, or blocked |
| `scoped` | bounded existing-code change; scout only when required context is absent | scout optional + 1 writer + conditional reviewer; max 4 spawns; native gates | accepted, repair checkpoint, or blocked |
| `feature` | new module, multi-package dependency, architecture axis, or critical/high-risk change | approved SDD/package budgets (max 12 spawns/package) | package workflow `DONE/BLOCKED` |
| `incident` | production/user path is currently broken and speed is material | 1 debugger + native verification; one evidence-backed escalation | verified recovery or blocked |

Lane classification is fail-closed: an unknown value, conflicting critical surface, missing success criterion, or
ambiguous read/write declaration escalates to `feature` and returns an explanation; it never silently selects a
lighter lane. Harness-owned facts (authenticated provider catalog, role capability, actual tools, write state,
critical surface, and route family) override caller claims.

The fast timing contract uses monotonic elapsed time: checkpoint at 18 minutes, do not start ordinary new work at
20 minutes, and allow at most one preapproved continuation/fallback ending by 30 minutes. Partial writes prohibit
automatic fallback.

## Schema-2 configuration contract

Schema 2 retains every existing `[subscriptions]`, `[catalog]`, `[session]`, `[permissions]`, `[providers]`,
`[families]`, `[areas.*]`, and `[roles.*]` field with its schema-1 meaning and adds:

```toml
schema = 2

[runtime]
primary = "opencode" # enum: opencode|claude-code|codex|pi
fallbacks = ["opencode"] # unique runtime IDs; never includes primary

[orchestrator.pi]
model = "gpt-5.6" # only gpt-5.6 or gpt-5.6-sol
effort = "medium" # fixed in MVP

[routing]
enabled_providers = ["openai-codex", "anthropic"]
xhigh_benchmarked = false
max_enabled = false # must remain false in MVP
fallback_limit = 1
single_writer = true

[routing.sla.fast]
checkpoint_minutes = 18
cutoff_minutes = 20
ceiling_minutes = 30

[routing.budgets]
direct_spawns = 0
fast_spawns = 1
scoped_spawns = 4
feature_spawns_per_package = 12
incident_spawns = 2
```

All fields above have the shown defaults when schema 1 is loaded. Unknown keys under the new tables, invalid
enums/types/ranges, duplicate fallbacks, `max_enabled=true`, a fallback containing the primary runtime, or a Pi
primary without an eligible Sol parent are errors. Loading schema 1 normalizes in memory without rewriting the
source. Deterministic `emit()` and any explicit setup-model mutation write schema 2 atomically; a failed write
leaves the prior file intact. Re-loading emitted schema 2 is idempotent.

Only Pi parent configuration uses the Sol/medium invariant. Existing OpenCode, Claude Code, and Codex area/role
mappings retain their current behavior. With no eligible Pi parent, route explanation remains available for all
providers but execution through Pi is disabled. Model IDs and aliases canonicalize through catalog-owned
`provider`, `model`, and `family` fields; no independent reviewer means a fail-closed route error.

## Security boundary

- `@earendil-works/pi-coding-agent` and `pi-subagents` are exact-version, integrity-locked dependencies.
- `pi-subagents` is loaded only into the parent. Child agent definitions omit `subagent`, intercom, and every
  delegation/extension tool and set maximum subagent depth to zero.
- One common fail-closed policy wraps every Pi tool dispatch, including process, shell, file read/write/edit,
  native gate, and working-directory selection. A deny cannot be bypassed through symlinks, alternate shells,
  interpreters, environment expansion, Git aliases/variants, or nested tool adapters.
- Executable, argv, cwd, environment names, and filesystem paths are normalized before policy evaluation.
  Protected-path checks use resolved real paths while also rejecting broken/escaping symlink components.
- `harness_gate` accepts only a versioned gate ID whose immutable argv/cwd template is repository-owned. It never
  accepts raw shell text, redirections, pipelines, substitutions, or arbitrary environment values.
- Provider credential files may be existence/stat-checked only; their bytes are never opened, printed, copied,
  hashed, or persisted by doctor/telemetry.

## Telemetry and retention

Task identity is `HMAC-SHA256(installation_salt, canonical_task_class_and_shape)`, not a direct hash. The random
installation salt and event files are local mode `0600`; parent directories are `0700`. Events use a versioned
allowlist schema and contain only task HMAC/class, route ID, provider/model/family, effort, budget/SLA, timestamps,
elapsed time, available token/cost counters, outcome/reason codes, and the single fallback ID/outcome.

Raw prompts, code, paths supplied as context, credentials, provider output, secrets, and PII have no serialization
field. Events rotate at 10,000 records or 90 days, whichever comes first; aggregate counters retain no task ID.
Failure to persist a spawn decision blocks dispatch before execution. Failure to append a terminal outcome emits
a redacted local diagnostic and safe checkpoint, never a retry.

## Rollout and rollback contract

- Pi remains opt-in. A future default change requires a separate human-approved config mutation after at least five
  successful runs covering all three benchmark classes in `plan.md`; no code path auto-promotes it.
- A representative run succeeds only when its artifact is correct, required gates pass, no hard-deny bypass or
  privacy leak occurs, and it meets its lane checkpoint/ceiling. Metrics include p50/p90 duration, spawns, tool
  calls, available tokens/cost, fallback count, and artifact correctness.
- `xhigh_benchmarked` may change only through a separately reviewed benchmark artifact with at least ten paired
  auditor/judge runs, a >=10% absolute task-success improvement, no correctness/security regression, and <=25%
  p90 latency increase. `max_enabled` remains false.
- Rollback preflights an installed, authenticated, generated OpenCode target. If preflight fails, configuration is
  unchanged. Success atomically changes only `runtime.primary` to `opencode`; Pi installation, auth, telemetry,
  feature state, and generated artifacts are preserved. Interrupted/corrupt writes restore the private backup or
  fail without replacing the current config.

## CLI machine contract

`--doctor --harness pi`, `--route-explain <task-class>`, and `--routing-report` support a versioned JSON result
(`schema_version`, `ok`, `command`, `data`, `reason_codes`) and stable human text. Exit `0` means usable/success,
`1` means a diagnosed unavailable/unhealthy state, and `2` means invalid input/config.

Built-in explain classes are `inspection`, `documentation`, `mechanical`, `implementation`, `architecture`,
`security`, `money`, `migration`, `concurrency`, `public-contract`, and `incident`. Doctor reason codes cover
install, exact dependency/integrity drift, OAuth status, catalog/Sol resolution, extension presence, and guard
policy. It checks OAuth status without reading credential contents.

## Domain invariants and public contracts

- `roles.tsv`, canonical prompts, and canonical capabilities remain the role source of truth.
- The 28-role roster is unchanged in the MVP.
- The orchestrator remains GPT-5.6 Sol at medium effort; critical architecture, security, money, migration,
  concurrency, public-contract, or high-ambiguity work routes to a focused frontier model at high effort.
- `xhigh` is restricted to auditor/judge routes backed by benchmark evidence; `max` is disabled.
- One writer is the default. Parallel mutation requires explicit approval and isolated worktrees.
- A child never receives a delegation tool or permission.
- A retry is never automatic after a partial write.
- A route has at most one eligible fallback.
- A reviewer never uses the implementer's model family.
- The Pi/OpenCode bridge and unbenchmarked GLM/Qwen-style providers remain disabled.
- Route choices use only catalog-issued `route_id` values. Choosing an eligible route other than rank 1 requires a
  reason code in the persisted decision.

## Non-goals

- Forking Gentle-AI or adopting its complete RDD workflow.
- Adding, removing, merging, or renaming roles.
- Enabling Pi as the default runtime before 5–10 representative successful opt-in runs.
- Persisting raw task text, prompts, source code, credentials, OAuth tokens, secrets, or PII in telemetry.
- Adding a general-purpose sandbox to Pi; SET-AGENTES supplies mandatory process guards instead.
- Introducing new model identifiers outside the configured, authenticated catalog.

## Risks and mitigations

- **Process-level Pi permissions:** mandatory pre-execution policy checks and regression tests cover all current
  hard-denies and protected secret paths.
- **OAuth exposure:** doctor checks only presence/status through provider commands and redacts all output.
- **Configuration loss:** managed manifests index only SET-AGENTES-owned paths and rollback restores compatible
  state without touching unrelated files.
- **Routing regressions:** a pure deterministic router, simulated catalogs, golden cases, and explanation output
  make decisions reproducible.
- **Telemetry leakage:** strict allowlist serialization plus tests that inject sensitive-looking inputs.
- **Provider outage:** exactly one precomputed fallback; partial mutation suppresses retry.

## Assumptions

- Pi provider OAuth support remains available for OpenAI Pro and Claude Max.
- Exact package versions will be selected and integrity-locked from authoritative package metadata during the
  implementation package; no floating `pnpm dlx` execution remains.
- Benchmark evidence and live OAuth smoke tests may be environment-gated; deterministic simulated coverage is
  mandatory in CI.
