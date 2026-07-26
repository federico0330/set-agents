# Design

## Components

- `models_config.py` owns backward-compatible schema loading and normalized schema-2 emission.
- A pure routing module owns task envelopes, catalog eligibility, risk tiering, ranking, reviewer independence,
  fallback policy, proportional flow plans, and privacy-safe event serialization.
- `set_agents_app.py` exposes doctor, route explanation, and routing reports without embedding routing logic.
- The generator renders Pi artifacts from the same canonical role and capability inputs as the other harnesses.
- The installer manages Pi below a SET-AGENTES-owned directory using an indexed manifest and atomic rollback.
- A Pi command guard evaluates process requests before execution; the child runner never exposes delegation tools.
- The common Pi dispatch guard wraps shell/process/file/gate/cwd operations and resolves paths/symlinks before
  applying protected-path and destructive-operation policy.

## Scale / Data / Security decisions

- **Scale:** local deterministic evaluation over bounded catalogs and local append-only aggregate metrics. No queue,
  cache, API gateway, replica, or sharding is introduced. Reconsider only if routing catalogs exceed 10,000
  candidates or local reports exceed a measured one-second p90.
- **Data:** versioned TOML configuration plus bounded JSON/JSONL operational records fit existing file-first
  access patterns. No SQL, NoSQL, graph, or vector store is justified. Reconsider a relational store only if
  multi-process writes require transactional coordination across projects.
- **Deploy:** SET-AGENTES remains a local CLI/runtime manager. No PaaS, VPS, managed service, or remote control
  plane is added.
- **Security:** provider credentials remain provider-owned; SET-AGENTES checks status but never reads credential
  contents. Least privilege is enforced by tool minimization, no child delegation, one writer, protected paths,
  command hard-denies, output redaction, and atomic managed-file rollback.

## Public contracts

- `TaskEnvelope`: role, operation, risk, estimated size, required tools, read/write mode, affected surface, SLA,
  success criteria, and context artifact references.
- `RouteDecision`: route ID, role, model, family, provider, effort, rationale/reason codes, budget, SLA, and at
  most one fallback route ID.
- `models.toml` schema 2: `[runtime]`, `[orchestrator.pi]`, and `[routing]`, while retaining existing static
  mappings for OpenCode, Claude Code, and Codex.
- Routing telemetry is allowlist-only and excludes raw task content by construction.
- Execution lanes and model tiers are distinct enums; harness-observed facts override envelope claims.

## Failure behavior

- Invalid/unknown route IDs and model IDs fail closed.
- Missing parent Sol eligibility rejects Pi primary activation with a specific diagnostic.
- Provider failure consumes at most one approved fallback.
- Partial write suppresses automatic fallback and creates a safe checkpoint.
- Doctor failures report capability/state reason codes without secret material.
- `harness_gate` resolves a repository-owned ID to immutable argv; it never executes caller-provided shell text.

## Rollout

Pi is opt-in for one IEY project. After 5–10 representative successful runs, a separate decision may make it the
default. Rollback changes only the primary runtime selector to OpenCode.

The MVP never auto-promotes Pi. Five successful runs across the three benchmark classes are the minimum evidence
for that later decision; additional runs up to ten improve the sample. `xhigh` uses the stricter paired benchmark
threshold defined in `spec.md`.
