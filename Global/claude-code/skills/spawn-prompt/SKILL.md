---
name: spawn-prompt
description: The orchestrator's fixed spawn-message template (ADR-0026) — context, task, evidence demanded, output format, out-of-scope, budget. Load when composing ANY subagent spawn message; the orchestrator is the harness's PO and its prompt quality is what the whole pipeline inherits.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator
---

# Spawn prompt — the fixed template

Every spawn message follows this shape. The point is not bureaucracy — it is that a worker with a
self-contained, evidence-demanding prompt returns usable work on the first try, and one without it burns a
retry. The sections, always in this order:

```
CONTEXTO
  <feature id> · <package id> · context pack: docs/specs/<fid>/context/<PKG>.md
  <2-4 líneas: qué existe ya, qué decisión/invariante lo restringe (ADRs), por qué este trabajo>

TAREA
  <la tarea concreta, en imperativo, con el resultado observable esperado>

EVIDENCIA EXIGIDA
  <qué debe citar el output: file:line para claims sobre el repo, salida de comandos corridos,
   URL/context7 para claims sobre dependencias externas. "Sin verificar" marcado si no hay fuente.>

FORMATO DE SALIDA
  <el schema/shape exacto del rol (JSON del implementer, findings del reviewer, etc.)>

FUERA DE ALCANCE
  <lo que NO debe tocar: paths ajenos, refactors oportunistas, decisiones que no le pertenecen>

PRESUPUESTO
  <límites que aplican: validaciones locales requeridas, techo de repair, checkpoint si se acerca al corte>
```

## Rules

- **Self-contained, always** — the worker never sees your chat history (orchestrator doctrine). If the
  context pack is missing or stale, route back to `package-planner` first; never say "explore the repo".
- **Evidence demanded up front** (ADR-0026): a spawn message that does not name what evidence the output
  must carry produces an output you cannot audit. The EVIDENCIA EXIGIDA section is never empty.
- **One spawn, batched work**: all scenarios/findings/files for that role in one message (spawn economy).
- **The template compresses, it never pads**: a quick-fix implementer spawn can be 10 lines total; every
  section present, each as short as the truth allows.
