# Acceptance scenarios

## AC-01 — Four-runtime semantic parity

**Given** the canonical 28-role roster, prompts, capabilities, and tools  
**When** SET-AGENTES generates every supported harness twice  
**Then** OpenCode, Claude Code, Codex, and Pi artifacts are reproducible and preserve the same role semantics.

## AC-02 — Safe managed Pi lifecycle

**Given** a home directory containing unrelated Pi configuration  
**When** Pi is installed, updated, checked for drift, or rolled back  
**Then** only indexed SET-AGENTES-managed files change and unrelated configuration is preserved.

## AC-03 — Fresh bounded children

**Given** an approved Pi route and explicit context pack  
**When** a child is launched  
**Then** it receives fresh context, only the required tools, no delegation capability, and a pinned model/effort.

**And** `pi-subagents` exists only in the parent, maximum child depth is zero, and direct/nested delegation calls
from a child fail before a process is spawned.

## AC-04 — Mandatory Pi hard-denies

**Given** a child command targeting a secret/protected path, `sudo`, broad recursive deletion, force-push, or
repository deletion  
**When** the Pi guard evaluates it  
**Then** execution is denied before the process starts and no sensitive value is logged.

**And** the same denial holds through symlinks, alternate shells/interpreters, file tools, Git aliases, cwd
escaping, environment indirection, and gate IDs; a raw command cannot be supplied to `harness_gate`.

## AC-05 — Deterministic eligibility

**Given** a structured task envelope and provider catalog  
**When** routing runs  
**Then** unauthenticated providers, disallowed models, missing tools/context, role incompatibility, and insufficient
risk coverage are excluded with explainable reason codes.

## AC-06 — Tier and effort selection

**Given** low-risk extraction, normal multi-file work, and critical security/architecture tasks  
**When** each task is routed  
**Then** they select `fast/low`, `balanced/medium`, and `frontier/high` respectively; `max` is never emitted and
`xhigh` appears only on benchmark-enabled auditor/judge routes.

## AC-07 — Parent Sol invariant

**Given** only Claude is authenticated  
**When** Pi parent activation is requested  
**Then** activation fails clearly, while eligible Claude child routes remain explainable and usable.

**And** child routes are execution-disabled through Pi until an eligible Sol/medium parent exists; both
`gpt-5.6` and `gpt-5.6-sol` positively resolve to the same parent family.

## AC-08 — Independent review

**Given** an implemented package and eligible reviewer candidates  
**When** reviewer routing runs  
**Then** the implementer's family is excluded and another provider is preferred when available.

**And** when no independent family is eligible, routing fails closed rather than reusing the implementer family.

## AC-09 — Single fallback

**Given** a selected provider becomes unavailable  
**When** no write has occurred  
**Then** the one preapproved fallback may run once; when partial writing is reported, no automatic retry occurs.

## AC-10 — Proportional low-risk flow

**Given** a project-inventory-to-Obsidian task classified as low-risk documentation  
**When** the orchestration plan is built  
**Then** it contains one specialist spawn and one allowlisted native gate, no SDD/planner/reviewer/judge cycle,
one consolidated notes render, an 18-minute checkpoint, a 20-minute normal-work cutoff, and a 30-minute ceiling.

**Given** envelopes matching each other execution lane or conflicting/ambiguous inputs  
**When** orchestration plans are built  
**Then** `direct`, `scoped`, `feature`, and `incident` follow the contract table, while ambiguity escalates
fail-closed with a reason code.

## AC-11 — Schema compatibility

**Given** valid schema-1 and schema-2 model configuration files  
**When** each is loaded and emitted  
**Then** schema 1 migrates deterministically, existing static mappings remain effective, and schema 2 round-trips.

**And** loading schema 1 does not rewrite it, explicit emission is atomic/idempotent, unknown new-table fields and
invalid enum/range combinations fail, and existing runtime mappings do not change.

## AC-12 — Privacy-preserving telemetry

**Given** a task containing prompt text, source code, PII-like strings, and secret-like values  
**When** routing and spawn telemetry are persisted  
**Then** only task hash/class, route, model, effort, timing, available token/cost metrics, outcome, and fallback
metadata exist in the stored event.

**And** task identity is installation-keyed HMAC, files use private permissions/rotation, aggregate reports contain
no task identity, and a spawn cannot run when its decision cannot be durably persisted.

## AC-13 — CLI observability

**Given** installed, missing, authenticated, and unauthenticated simulated Pi environments  
**When** `--doctor --harness pi`, `--route-explain`, and `--routing-report` are invoked  
**Then** each returns stable machine-testable output without printing or reading credential contents.

**And** JSON output follows the versioned CLI envelope, uses documented exit codes/reason codes, detects dependency
integrity drift, and invalid task classes fail with exit 2.

## AC-14 — Rollout and rollback compatibility

**Given** Pi is opt-in for an IEY project  
**When** primary runtime rollback is requested  
**Then** only the primary runtime changes to OpenCode and durable state/artifacts remain compatible.

**Given** OpenCode preflight fails or rollback is interrupted  
**When** rollback is requested  
**Then** the current primary remains unchanged or the private backup is restored, while unrelated configuration,
Pi state, telemetry, auth, and generated artifacts remain untouched.

## AC-15 — Existing harness regression

**Given** a valid existing configuration and install target  
**When** the canonical verification suite runs  
**Then** all existing OpenCode, Claude Code, and Codex generation, lifecycle, permission, and workflow checks remain
green, and the pre-existing environment-sensitive bootstrap test no longer assumes an installed CLI is missing.
