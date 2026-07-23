# SET-AGENTS usage

This independent repository is the versioned source for OpenCode, Claude Code, and Codex.

## Control plane

**OpenCode is the orchestration control plane.** Feature work always starts there with `/feature-batch`
(its main session IS the orchestrator, with the model, permissions, and step budgets the harness actually
enforces). The other two harnesses are single-task lanes, not orchestrators:

- **Claude Code**: review/debug lane (`/audit`, `/review-*`, focused debugging sessions).
- **Codex**: second-opinion lane, one bounded task per session. Never orchestrate long features in Codex:
  its native `spawn_agent` inherits the session model (ignoring the per-agent TOML routing) and can fork
  the whole transcript into every subagent — the exact combination that burned a week of quota in two days.

`ai/scripts/check-drift.sh` compares the live install against the repo; a post-commit hook (installed by
`build.sh`) warns when the installation lags. Never leave a `DRIFT_DETECTED` unresolved — the July 2026
incident (orphaned expensive reviewers + an MCP left enabled) was exactly a one-generation-stale install.

Project-level scripts drift too: `ai/scripts/sync-project.sh <project-dir>` copies the generic template
scripts (feature-state.py, mcp.sh, e2e.sh, …) into a project, backing up what it replaces and leaving the
project-specific `run.sh`/`verify.sh` untouched. It ABORTS if the project has an active (non-terminal)
feature whose state does not validate against the new schema — close the feature first, or `--force`.

## Bootstrap / compartir

Repo privado: se comparte invitando collaborators (Read) en GitHub; `gh auth login` +
`gh repo clone` + `./set-agents` abre la app de consola: instalar/reparar, auto-update,
modelos, catálogo de herramientas (`tools.toml`), MCPs por harness detectado y plugins.
Windows va por `install.ps1` (WSL administrado). `./install.sh` y `./setup-models.sh` quedan
como plomería directa de [1] y [3]. CI valida ubuntu+macos+windows en cada push a main.
Detalles en `INSTALACION.md`.

## Source layout

- `roles.tsv`: one row per role — structure only (mode, temperature, capability, duty).
- `models.toml`: subscriptions, model catalog, per-area models with per-role overrides.
  Edit via `./setup-models.sh` (see `COMO-CAMBIAR-MODELO.md`).
- `active-profile`: `go-zen`, `zen`, or `local` (the opencode lane).
- `models.toml [permissions]`: `profile = "yolo" | "guarded"` — OpenCode permission posture
  (yolo = no bash/edit prompts; hard denies and duty separation always survive). Tracked, so
  it applies fleet-wide on the next build/auto-update.
- `Global/_canonical`: canonical prompts, commands, and skills.
- `Global/_shared`: shared policy and disabled MCP configuration.
- `Global/{opencode,claude-code,codex}`: generated, reviewable native output.
- `ai/scripts/verify.sh`: deterministic repository gate.

## Safe generation and installation

```bash
./build.sh --check     # generate in temporary staging and validate
./build.sh --diff      # compare staging with tracked generated output
./build.sh             # refresh tracked generated output
./build.sh --install   # show managed live diff, ask once, back up, install, smoke-test
```

Installation merges only managed configuration keys, preserves unrelated plugins/files, removes legacy Codex
role prompts, and rolls back managed paths if smoke checks fail. Backups live under
`~/.local/state/set-agentes/backups/` (the state dir keeps its historical `set-agentes` spelling on
purpose: migrating it would orphan every machine's manifest and backups).

Profile wrappers change only `active-profile` (per-machine, untracked; fresh clones default to go-zen)
and use the same confirmation flow:

```bash
./use-go-zen.sh
./use-zen.sh
./use-local.sh
```

Runtime gate timeout: `e2e.sh` cuts the runtime-verifier at `E2E_TIMEOUT` seconds (default 600).
If a project's E2E legitimately needs longer, export a bigger `E2E_TIMEOUT` instead of authorizing reruns.

Known debt: `Global/_canonical/opencode-agents/package-gate-runner.md` hardcodes absolute paths from the
original `~/iey/iey-ai` project in its allow-list. Outside that repo those permissions are inert (the agent
is scoped to the `replenishment-v2` feature only), but new machines inherit dead paths until that prompt is
parameterized.

## Required lifecycle

`spec → design → tests → implementation → gate-runner → domain audits → repair → adversarial-judge → GitHub`

The orchestrator is read-only and delegates every write and gate. `adversarial-judge` is mandatory for every
versionable change. `github-release-manager` may prepare a local commit only after green local gates; publication
and merge require separate confirmations, with green remote checks before merge.

## Native agents

- OpenCode: `~/.config/opencode/agents/*.md`
- Claude Code: `~/.claude/agents/*.md`, with Bash guards for read-only roles
- Codex: `~/.codex/agents/*.toml`, with explicit model, reasoning effort, and sandbox

## Measuring consumption

`ai/scripts/cost-report.py` aggregates token usage per project across the three harnesses' own session
stores (OpenCode sqlite, Claude Code transcripts, Codex threads). Tokens only — with subscription plans the
number that matters is quota, not dollars.

```bash
ai/scripts/cost-report.py                                         # everything
ai/scripts/cost-report.py --project ~/iey/ScrappingML --since 2026-07-01
ai/scripts/cost-report.py --project . --md                        # markdown (e.g. into evidence/)
ai/scripts/cost-report.py --deep                                  # Codex cached/reasoning split (slower)
```

Read it after every feature: cost per deliverable is margin. If one role/model dominates without matching
value, that is a roles.tsv routing decision waiting to happen.

## MCP policy

Engram, Context7, Playwright, and Brave CDP remain disabled by default. An eligible agent must ask permission,
enable one temporarily, use it for the scoped task, and disable it again. Memory is local-first; Engram gets at
most one 60-second attempt and never blocks the lifecycle. Engram data repair always requires backup and separate
authorization.
