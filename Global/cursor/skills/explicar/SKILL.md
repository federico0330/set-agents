---
name: explicar
description: Read-only human trace of a module or a question, following the real code from its entry points and flagging when `docs/modules/<slug>.md` is stale against it. Load when the orchestrator runs `/explicar` or when `architect` is delegated the read-only tracing task it implies.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator, architect
---

# Explicar — human trace from the real code

## When to use
The user (or the orchestrator itself) wants to understand how something actually works — a module, a
flow, a "why does X happen when Y" — without changing anything and without opening a feature. This is the
read-only twin of `/consult` for CODE UNDERSTANDING specifically, not general design analysis.

## Contract
- **Read-only, no feature state.** No `init`, no package, no mutation of any kind — same posture as
  `/consult`. `roles.tsv` gains no new role for this: it is a command the orchestrator runs, delegating to
  `architect` in its existing read-only capacity.
- **Input**: a module slug/name from `docs/modules/modules.toml`, or a plain question the entry-point
  search resolves to a module.
- **Procedure**: read `modules.toml` + the module's doc → follow the real code starting from the doc's
  `## Puntos de entrada` (or the module's `paths` if the doc has none yet) → verify each hop against the
  file on disk → return the trace as `Cliente:`/`Ingeniería:` with `file:line` per claim (ADR-0026); mark
  "sin verificar" whatever the code does not confirm.
- **Staleness is the point, not a footnote.** `docs/modules/<slug>.md` splits into a machine block (three
  derived sections, including `## Últimos cambios estructurales`) and six sembradas sections that no
  render ever rewrites (ADR-0036 decision 3 — a documented, accepted limitation, not a bug). That means
  the sembrada prose can silently drift from the code with nothing to catch it automatically. `/explicar`
  IS that catch: every run compares what the doc's hand-written sections claim against what the code at
  `file:line` actually does, and against whether `## Últimos cambios estructurales` looks current for
  the module's `paths` (a quick `git log -- <paths>` since the last recorded entry is enough signal). When
  it finds drift, the answer says so explicitly — never silently prefers the doc's memory over the live
  code — and offers the fix: `record-module-impact <fid> --package-id <P> --module <slug> --cambio "..."
  --modelo-mental "..."` for whichever package caused it, or a dedicated repair task if no package owns
  the gap yet.

## Must NOT
- Write, mutate feature state, or create a package. If the user wants the drift fixed, that is a
  follow-up delegation, not something `/explicar` does itself.
- Trust the doc's sembrada prose as ground truth without checking it against the code the question is
  actually about — that check is the whole reason this command exists (see ADR-0036's decision on the
  partition, and the registered decision it names as the condition for accepting it).

## Output
Dual-register trace (`Cliente:` / `Ingeniería:`), `file:line` evidence per claim, and — whenever it
applies — an explicit staleness note with the regeneration command to run.
