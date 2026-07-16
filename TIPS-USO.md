# SET-AGENTES usage

This independent repository is the versioned source for OpenCode, Claude Code, and Codex.

## Source layout

- `roles.tsv`: one row per role, capabilities, duties, and quota-first models.
- `active-profile`: `go-zen` or `zen`.
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
`~/.local/state/set-agentes/backups/`.

Profile wrappers change only `active-profile` and use the same confirmation flow:

```bash
./use-go-zen.sh
./use-zen.sh
```

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
