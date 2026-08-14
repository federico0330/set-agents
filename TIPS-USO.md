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
- `active-profile`: `go-zen`, `zen`, or `openai-only` (the opencode lane).
- `models.toml [permissions]`: `profile = "yolo" | "guarded"` — OpenCode permission posture
  (yolo = no bash/edit prompts; hard denies and duty separation always survive). Tracked, so
  it applies fleet-wide on the next build/auto-update.
- `Global/_canonical`: canonical prompts, commands, and skills.
- `Global/_shared`: shared policy and disabled MCP configuration.
- `Global/{opencode,claude-code,codex}`: generated, reviewable native output.
- `ai/scripts/verify.sh`: deterministic repository gate.

## Safe generation and installation

```bash
./build.sh --check     # forced --profile go-zen: diff a fresh build against Global/, fail
                        # naming files on any drift (self-scaffold AND the four Global/ trees;
                        # ADR-0041). Ignores the local active-profile/--profile on purpose:
                        # Global/ is committed under go-zen, and a local lane would break
                        # install.sh's onboarding and every setup-models.sh model change.
./build.sh --diff      # compare staging (local profile) with tracked generated output --
                        # "show me", always exits 0, never a gate
./build.sh             # refresh tracked generated output
./build.sh --install   # show managed live diff, ask once, back up, install, smoke-test
```

**Gate order (ADR-0041, AC-04):** `./build.sh --check` runs SIEMPRE before the full test suite
whenever both are cited as evidence for a gate — `ai/scripts/verify.sh` already has this order
(`--check` at `:6`, the suite at `:17`), because the suite regenerates `Global/` dozens of times
as a side effect of exercising `generate.py` (`tests/test_harness.py`), which papers over real
drift by the time anything looks at it afterward. The same rule applies to standalone citations
(there is real precedent for citing them loose, `HANDOFF-PASO9.md:103`). A CI job that runs the
suite alone without `--check` (`windows-bootstrap` in `.github/workflows/ci.yml`, which cannot
run a bash script) proves the Python scripts and the suite pass on Windows — it is never evidence
that `Global/` has no drift.

Installation merges only managed configuration keys, preserves unrelated plugins/files, removes legacy Codex
role prompts, and rolls back managed paths if smoke checks fail. Backups live under
`~/.local/state/set-agentes/backups/` (the state dir keeps its historical `set-agentes` spelling on
purpose: migrating it would orphan every machine's manifest and backups).

The opencode lane (`active-profile`, per-machine, untracked) is auto-derived from the probe on the
first `./build.sh` run: both opencode pairs authenticated → `go-zen`, only zen → `zen`, no opencode →
`local`. The old `use-go-zen.sh`/`use-zen.sh`/`use-local.sh` wrappers are gone. To override, run
`PROFILE=zen ./build.sh --install` (one-off) or edit/delete `active-profile` and rebuild (delete →
re-derive).

Runtime gate timeout: `e2e.sh` cuts the runtime-verifier at `E2E_TIMEOUT` seconds (default 600).
If a project's E2E legitimately needs longer, export a bigger `E2E_TIMEOUT` instead of authorizing reruns.

## Running long commands without going silent (ADR-0041, AC-06/AC-07/AC-08)

**Never pipe a long-running gate through `| tail -N`.** Without `-f`, `tail` structurally cannot
emit a single byte until it sees EOF, regardless of how the upstream command buffers its own
writes (measured: even an explicitly-flushed writer piped through `stdbuf -oL ... | tail -3`
stays silent for the whole run). An agent watching that pipe looks stalled for the entire
command, which is how multiple agents died mid-session with `Agent stalled: no progress for
600s` — that 600s watchdog belongs to the **agent runtime**, not to this repository, and this
feature cannot change it; what this repo controls is not creating the silence that trips it.

Correct patterns for a command whose own output has real gaps, in order of preference:

1. Let the output flow raw (no pipe at all) — the default and simplest choice.
2. Redirect to a file and read it after the command exits, or poll the file's size/tail while
   the command is still running in the background — never pipe the live command through `tail`.
3. `ai/scripts/heartbeat-run.py --interval N -- <command> [args...]` — streams the child's
   merged stdout/stderr line by line as it arrives and injects its own heartbeat line if `N`
   seconds pass with no real output, so something is always emitted well under any watchdog.
   Default interval 60s. This does not make the command faster; a slow command is a separate
   problem from a silent one.

If a tool needs naming for "make this command's own stdout line-buffered", it is `python3 -u` /
`PYTHONUNBUFFERED=1` — portable. `stdbuf` is GNU coreutils and does not exist on macOS/BSD, where CI
also runs (`.github/workflows/*.yml`, job `verify-macos`); besides being non-portable, it does not
fix the `| tail -N` case above.

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
stores (OpenCode sqlite, Claude Code transcripts, Codex threads), plus a fourth `pi` lane read from the
routing database. Tokens only — with subscription plans the number that matters is quota, not dollars.

```bash
ai/scripts/cost-report.py                                         # everything
ai/scripts/cost-report.py --project ~/iey/ScrappingML --since 2026-07-01
ai/scripts/cost-report.py --project . --md                        # markdown (e.g. into evidence/)
ai/scripts/cost-report.py --deep                                  # Codex cached/reasoning split (slower)
```

The `pi` lane only covers spawns this harness itself dispatched through `set_agents_spawn.py` — a `pi`
session started by hand is invisible to it. Its stored `project_key` is a one-way hash, not invertible to a
directory, so it is only attributed to a project when `--project` is given (the key is recomputed and
matched); without it, the lane is reported unattributed rather than guessed.

Read it after every feature: cost per deliverable is margin. If one role/model dominates without matching
value, that is a roles.tsv routing decision waiting to happen.

## MCP policy

Engram, Context7, Playwright, and Brave CDP remain disabled by default. An eligible agent must ask permission,
enable one temporarily, use it for the scoped task, and disable it again. Memory is local-first; Engram gets at
most one 60-second attempt and never blocks the lifecycle. Engram data repair always requires backup and separate
authorization.
