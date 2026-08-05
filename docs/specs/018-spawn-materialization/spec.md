# 018 — Materialización en el spawn (opencode/codex) y pins de modelo

- **Estado**: implementado (2026-08-05); diseño y racional completo en
  `docs/adr/0032-spawn-time-model-materialization-and-pins.md` (relacionado: ADR-0018,
  ADR-0030, ADR-0031).

## Objetivo

A. Que los lanes opencode y codex apliquen el modelo (+ effort donde el CLI lo soporta)
decidido por `--route-decide` EN EL SPAWN, para cualquier rol del roster — igual que pi
(`--model … --thinking …`) y claude-code (`--model data.model`). `MODEL_STATIC_FALLBACK`
deja de ser el camino normal de los ~22 roles no tiered y queda como degrade residual.

B. Que la consola declare la política en vez de pedir asignación manual: "Automático
(recomendado)" (el router decide por spawn) o "Fijar modelo" (pin por rol o global `*`),
con el origen de cada valor visible (pin / decisión dinámica / fallback curado).

## Criterios de aceptación

- AC-01: `ai/scripts/opencode_spawn.py` y `ai/scripts/codex_spawn.py` componen los argv
  verificados en vivo (opencode 1.18.10: `run -m provider/model [--variant e] --agent
  <role> --format json`; codex 0.146.0: `exec --ephemeral --sandbox <mode> -m <model>
  [-c model_reasoning_effort=e] -c developer_instructions=<role.md> -o <f> -`), con
  mapeo catálogo→id por lane y effort advisory (conjunto cerrado, nunca fatal).
- AC-02: tres modos por role_class — writer (consume run_id, dispatched→spawn→terminal,
  nunca re-decide, nunca deja un run abierto), review (cero bookkeeping, supplementary
  nonce-fenced), simulate (SOLO role_class `other`; rechaza writer/review; cero
  bookkeeping — "Never fabricate enforcement" por construcción).
- AC-03: precedencia pin > dinámico > fallback curado. `[model_pin]` en
  `model-preference.toml` (infra ADR-0018; `load_model_preference` conserva su shape
  público de dos claves), CLI `--model-pin-set/--model-pin-clear`, pin como override
  BLANDO en el sort del router (nunca saltea auth/independencia/tier floor), reason
  codes aditivos `MODEL_PINNED`/`MODEL_PIN_UNAVAILABLE`, `selection_path`
  (`pin|dynamic`) en el envelope y en `decisions-v1.jsonl` (ADR-0031).
- AC-04: wizard/panel de Modelos declara la política y los pins con su origen; conserva
  los marcadores "DEFAULTS CURADOS" y "ADR-0030"; acción nueva "Routing: fijar modelo /
  automático" (índices 0-4 del wizard intactos).
- AC-05: allowlist — dos entradas enumeradas nuevas en `coord_policy.SAFE_ARGV`
  (gramática == `main()` real de cada módulo) y líneas pareadas en
  `generate.py::oc_permissions`; doctrina "Decide siempre" actualizada en el canonical y
  regenerada a los 5 espejos con `./build.sh`.
- AC-06: contratos congelados intactos (roster tiered = 6, frase de doctrina verbatim,
  DDL de routing.db, marcadores de test_decide_always); `record-spawn` sigue recibiendo
  `--model/--provider/--effort/--route-id`; degrades registrados como hoy.
- AC-07: `tests/test_spawn_materialization.py` (argv por lane, precedencia, config
  round-trip, allowlist, panel, doctrina) + `ai/scripts/verify.sh` completo en verde.

## No-goals

- No se amplía el roster tiered ni se borran las variantes `@tier` (camino aditivo).
- No hay replacement automático de quota en los módulos nuevos (firmas anthropic-only
  del rail 011/029); el orquestador aplica su retry budget.
- Sin verificación post-hoc de modelo en opencode (límite del CLI, documentado en el ADR).
