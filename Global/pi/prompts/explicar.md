---
description: Read-only human trace of a module or a question, from the real code
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Explain this in consult mode (see `request-triage` mode 0 — no init, no state, no pipeline):
$ARGUMENTS

Read-only, no feature state — same posture as `/consult`: NO `init`, NO pipeline, NO mutation anywhere.
The input is a module slug/name or a plain question about how something works.

Delegate to `architect` (read-only): load `docs/modules/modules.toml` and the doc of the named module (or
find the module whose `paths` cover the question's subject), then **follow the real code from its entry
points** — `## Puntos de entrada`, `## Componentes`, `## Flujo` if present — verifying each hop against the
file on disk, not the doc's memory of it. Return the trace in the dual-register narration
(`Cliente:`/`Ingeniería:`), each claim carrying `file:line` evidence (ADR-0026); "sin verificar" for
anything the code does not confirm.

**Staleness check, mandatory, not a footnote.** Before trusting the doc's hand-written sections, compare
`## Últimos cambios estructurales` (inside the doc's machine block) against the module's `paths` in
`modules.toml`: if `git log` on those paths shows structural change since the last recorded entry, or the
doc's sembrada prose (the six sections below the machine block, ADR-0036 decision 3) describes a flow the
code no longer has, say so explicitly in the answer — do not silently prefer the doc over the code. Offer
to regenerate: `record-module-impact <fid> --package-id <P> --module <slug> --cambio "..." --modelo-mental
"..."` for the package that caused the drift (or a dedicated repair if no package owns it). This staleness
check is the mitigant for the five sembradas sections' known limitation — they survive re-renders exactly
because nothing forces them to stay in sync, so `/explicar` is the human's independent read against the
live code, every time it runs, not a cache of the doc.
