# PKG-C implementer evidence

Feature: `035-panel-honesto-consola-y-tips` · PKG-C · spec hash `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`

## Measurement commands

```bash
ls Global/
# _canonical  _shared  claude-code  codex  cursor  opencode  pi

rg -i cursor ai/scripts/cost-report.py
# :20  Empty on Cursor: native subagents never go through those CLIs.
# :23  Cursor. Token fields are absent there — sessions still count.
# :836-843  "every runtime including Cursor"; routing.db empty on Cursor native subagents

rg -n "control plane" TIPS-USO.md docs/COMO-FUNCIONA.md README.md
# README.md:305  (index — left unchanged)
# docs/COMO-FUNCIONA.md:13  (sibling link — still valid)

git diff -- TIPS-USO.md
# (see Forbidden-line proof below)

git diff --check -- TIPS-USO.md docs/COMO-FUNCIONA.md README.md
# (no whitespace errors)
```

## Claims changed (file:line, before → after)

| Task | Location | Was (measured-false) | Now |
|---|---|---|---|
| T-201 / AC-C.1 | `TIPS-USO.md:7-14` | OpenCode sole control plane; Claude/Codex "single-task lanes, not orchestrators" | Three can orchestrate; ADR-0064 panel caveat explicit; Codex `:15-17` warning preserved |
| T-201 / AC-C.1 | `TIPS-USO.md:18` | (missing) | Cursor bullet added (`~/.cursor/agents/*.md`, no `--route-decide`) |
| T-202 / AC-C.2 | `TIPS-USO.md:3-4` | "OpenCode, Claude Code, and Codex" (3 trees) | Five harness trees + `_canonical` / `_shared` |
| T-202 / AC-C.2 | `TIPS-USO.md:49` | `Global/{opencode,claude-code,codex}` | adds `cursor`, `pi` |
| T-202 / AC-C.2 | `TIPS-USO.md:55` | "four Global/ trees" | "five Global/ trees" (consistency with `ls Global/`) |
| T-202 / AC-C.2 | `TIPS-USO.md:133-134` | Native agents: 3 bullets | Adds Cursor + pi (`~/.pi/agent/agents/*.md`) |
| T-202 / AC-C.3 | `TIPS-USO.md:138-143` | "three harnesses' session stores … fourth pi lane" | Two-section model from `cost-report.py:15-24`, `:836-843`; Cursor empty on routing.db, spawns[] covers Cursor |
| T-203 / AC-C.4 | `docs/COMO-FUNCIONA.md:221` | OpenCode cell cited stale TIPS "control plane histórico" | "lane con hooks generados" |
| T-203 / AC-C.4 | `docs/COMO-FUNCIONA.md:227-229` | "`TIPS-USO.md` todavía dice OpenCode es el control plane…" | Points to spec 035 PKG-C alignment; ADR-0064 panel caveat |
| T-203 / AC-C.4 | `docs/COMO-FUNCIONA.md:442-445` | Item 3 ownerless "Actualizar TIPS-USO.md" | Links [`035-panel-honesto-consola-y-tips`](../spec.md) PKG-C; "Ninguno de los **dos** primeros…" |

## README.md decision (AC-C.6)

**Left unchanged** (`README.md:305`).

Reason: after TIPS correction the doc still covers control-plane topology (multi-runtime orchestration, lanes, drift). The index phrase "control plane, lanes, drift" remains accurate as a pointer — it no longer implies OpenCode is the sole plane.

## Forbidden-line proof (AC-C.5)

`git diff -- TIPS-USO.md` touches only:

- `:3-18` (intro + control plane)
- `:49`, `:55` (Global/ inventory)
- `:133-143` (native agents + measuring consumption intro)

**Untouched sections** (verified by diff absence + file read):

- Bootstrap / compartir (`## Bootstrap / compartir`, lines ~29-36)
- Required lifecycle (`## Required lifecycle`, lines ~120-126)
- MCP policy (`## MCP policy`, lines ~161-166, Engram mention intact)

## README.md

Not modified.

## Local validation

- `git diff --check` on the three files: clean
- `./ai/scripts/verify.sh`: **not run** (gate-runner scope per task)
