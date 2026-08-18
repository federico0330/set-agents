# Estado del pipeline (feature-state)

<!-- notas:auto -->
## Responsabilidad

Máquina de estados de paquetes/features: fases legales, gates, reviews, findings, y ahora impacto de módulo — la fuente de verdad que STATUS.md/bitácora/notas derivan.

## Posee

- `ai/scripts/feature-state.py`
- `ai/scripts/feature_state_lib/**`
- `ai/scripts/check-feature-state.py`

## Últimos cambios estructurales

- 2026-08-18 010-spawn-provenance/P1-spawn-provenance — spawn provenance node en el grafo de estado: cada spawn queda trazable al paquete que lo originó, con su decision_id de routing
- 2026-08-18 006-execution-graph/P3-graph-view — ai/scripts/check-feature-state.py: nuevo script que genera el grafo de ejecución de features y paquetes
- 2026-08-18 031-registro-correctivo/P1-verbos-correctivos — dos nuevos verbos: cmd_reopen extendido con --from-done, cmd_amend_package nuevo; MUTATING_COMMANDS actualizado
- 2026-08-18 031-registro-correctivo/P1-verbos-correctivos — dos nuevos verbos: cmd_reopen extendido con --from-done (DONE→PACKAGE_PLANNING), cmd_amend_package (agrega tasks a paquetes no-accepted); amend-package y reopen-from-done en MUTATING_COMMANDS
- 2026-08-11 019-harness-evolution/P3-cognitive-module-docs — Se agregaron module_impacts/module_impact_waiver a compact_package, module_impacts_ready() y el gate duro en check_transition/done_ready para INTEGRATION (ADR-0036), más los comandos record-module-im…

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `ai/scripts/feature-state.py` (CLI, `build_parser()` en `:797`) — toda mutación de estado
  pasa por acá: `init`, `transition`, `create-package`, `record-*`, `accept-package`,
  `record-module-impact`, `sync-notes`, `digest`, etc.
- `ai/scripts/check-feature-state.py` — el gate de CI/PACKAGE_GATES que corre
  `validate_state` contra el árbol vivo.

## Componentes

- `feature_state_lib/model.py` — el schema (`compact_package`, `:260`), invariantes
  estáticas (`validate_state`, `:347`), y los predicados de fase
  (`package_review_ready`, `package_accept_ready`, `done_ready`, `module_impacts_ready`).
- `feature_state_lib/transitions.py` — `check_transition` (`:17`, precondiciones duras por
  fase) y `next_transition` (`:54`, el asesor de "próximo paso").
- `feature_state_lib/cli_lifecycle.py`, `cli_review.py`, `cli_repair.py`, `cli_integration.py`,
  `cli_modules.py`, `cli_reporting.py` — un comando por verbo, mismo patrón argparse +
  `model.mutate(path, args, op, updater)`.
- `feature_state_lib/candidate_identity.py` — freeze/re-derive de git tree-hash (ADR-0020/0024).
- `feature_state_lib/graph.py` — `build_execution_graph`/`render_mermaid`, el grafo de
  ejecución que `docs/notas/features/<fid>/grafo.md` renderiza.
- `feature-state.py`'s propio `mutate()` (`:151-174`) — el único lugar que corre
  `render_status`/`render_bitacora`/`render_notes`/`render_modules` tras cada mutación exitosa.

## Flujo

CLI arg → `cmd_<verbo>` → `model.mutate(path, args, op, update)` → `update(data)` aplica el
cambio y llama `model.record_event` → si `changed`, `fail_if_invalid` + `atomic_write` +
re-render (STATUS/bitácora/notas/módulos) → `output_state` imprime `{ok, changed, state,
next}`. `check_transition` es la única puerta dura entre fases; `next_transition` es
consultivo, nunca bloquea.

## Posee / Depende de

Posee: ver "Posee" arriba. Depende de `render_status.py`/`render_bitacora.py`/
`render_notes.py`/`render_modules.py` (el módulo narración-notas) para toda la
proyección legible; nunca al revés.

## Invariantes

- Nunca hay una segunda implementación de `record_event`/`mutate`: viven físicamente en
  `feature-state.py` e inyectan en `model.record_event`/`model.mutate` para que todo
  submódulo los llame calificados (evita ciclos de import, documentado en
  `feature-state.py:82-105`).
- `atomic_write` es siempre tempfile + `os.replace`; ninguna escritura parcial es visible.
- Ningún render (`render_status`/`render_bitacora`/`render_notes`/`render_modules`) puede
  romper una mutación — contrato never-raises compartido con el módulo narración-notas.
- Presupuestos (`max_spawns_per_package`, `max_deep_review_cycles`, etc.) son backstops
  estáticos; el enforcement real vive en el comando que escribe el valor.

## Decisiones

- ADR-0020 a ADR-0024 (RDD: candidate_identity, receipt, repair ceiling, strict TDD,
  integration receipt hook).
- ADR-0027 (narración por hito, digest generado), ADR-0028 (alcance vivo), ADR-0036 (esta
  capa: `docs/modules/`, gate de impacto humano en INTEGRATION).
