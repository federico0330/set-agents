# Narración y notas vivas

<!-- notas:auto -->
## Responsabilidad

Deriva STATUS.md, bitácora y docs/notas/ (Obsidian-ready) del estado en cada mutación; digest matinal y el propio render never-raises que docs/modules/ reutiliza.

## Posee

- `ai/scripts/feature_state_lib/render_notes.py`
- `ai/scripts/feature_state_lib/render_bitacora.py`
- `ai/scripts/feature_state_lib/render_status.py`
- `ai/scripts/feature_state_lib/render_modules.py`
- `docs/notas/**`

## Últimos cambios estructurales

- 2026-08-12 020-honest-dashboard/P2-anclas-verificables — Nuevo motor check_anchors.py y comando feature-state.py check-anchors: extrae las referencias file:line de docs/modules/, resuelve el basename SOLO dentro de los paths que el modulo declara en module…
- 2026-08-12 020-honest-dashboard/P1-digest-no-esconde — Un unico predicado compartido en model.py (feature_is_live, open_blocker, blocked_days, stale_days, feature_is_stale, STALE_THRESHOLD_DAYS) reemplazo las dos copias mal escritas que tenian cmd_digest…
- 2026-08-11 019-harness-evolution/P3-cognitive-module-docs — Nuevo feature_state_lib/render_modules.py, mismo contrato never-raises/atómico que render_notes.py; reutiliza merge_note/write_note/_short en vez de reimplementarlos; enganchado a mutate() y a sync-n…

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- Nunca se invoca directo: `feature-state.py`'s `mutate()` (módulo `estado`, no citamos
  línea acá: cruza de módulo, ver SC-01) llama
  `render_status`/`render_bitacora`/`render_notes`/`render_modules` después de cada
  mutación exitosa. `sync-notes` (`cli_reporting.cmd_sync_notes`) es el punto de
  consolidación manual (`--no-render` deferido, siempre corre acá).
- `digest` (`cli_reporting.cmd_digest`, módulo `estado`) — el resumen matinal derivado.
- `log-quickfix`/`log-narrative`/`log-decision` (`cli_reporting.py`) — los tres logs JSONL
  que alimentan bitácora/notas/decisiones.

## Componentes

- `render_notes.py:51` `merge_note(existing, title, body)` — regenera solo el bloque
  `<!-- notas:auto -->`; `:67` `write_note` — escritura atómica idempotente; `:80`
  `_short(text, limit)` — neutraliza `<!--`/`-->`, colapsa whitespace, trunca. TODO campo
  que viene de estado pasa por acá antes de tocar disco.
  `:37` `notes_root(state_file)` — el marcador es `ai/state/`, nunca "¿ya existe
  `docs/notas/`?".
- `render_status.py:70` `render_status(state_file)` — `STATUS.md`, la tabla multi-feature.
- `render_bitacora.py` — la bitácora por feature (registros Cliente/Ingeniería, ADR-0027).
- `render_modules.py` (este mismo paquete, ADR-0036) — reutiliza `merge_note`/`write_note`/
  `_short` de acá; nunca reimplementa el merge.
- `RENDER_FAILURE_LOG = "render-failures.log"` (`render_notes.py:281`) + `_log_render_failure`
  (`:285`) — el log compartido de todo render never-raises de este módulo, por proyecto
  (`out_dir` es siempre el `ai/state/` del proyecto que renderiza).

## Flujo

Mutación de estado (cualquier verbo de `feature-state.py`) → `mutate()` escribe el JSON
atómicamente → re-render: `render_status` (tabla), `render_bitacora` (narración por hito),
`render_notes` (hub + feature + paquete + decisiones, todo con `[[wikilinks]]`),
`render_modules` (`docs/modules/<slug>.md` para módulos con impacto) → cada render es
best-effort: una excepción se captura, se anota en `render-failures.log` y la mutación de
estado ya persistida NUNCA se revierte.

## Posee / Depende de

Posee: ver "Posee" arriba, más `docs/notas/**` (la salida generada). Depende del módulo
`estado` (lee `ai/state/features/*.json`) pero nunca al revés — el módulo `estado` solo
LLAMA a este, nunca importa su output.

## Invariantes

- El bloque `<!-- notas:auto -->`/`<!-- /notas:auto -->` es la única frontera
  máquina/humano; todo lo de afuera se preserva byte a byte en cada regeneración
  (probado por round-trip en `tests/test_harness.py` y, para módulos, en
  `tests/test_module_docs.py`).
- Ningún render puede romper una mutación (contrato never-raises, compartido con
  `render_modules.py`).
- Un repo sin `ai/state/` nunca genera `docs/notas/` ni `docs/modules/` — opt-in por la
  existencia de `ai/state/`, nunca por "¿ya existe el directorio de salida?" (ADR-0012 AC-13,
  extendido por ADR-0036 a `docs/modules/`).

## Decisiones

- ADR-0012 (vault topology, el criterio `ai/state/`), ADR-0027 (narración por hito, digest
  generado), ADR-0036 (`docs/modules/`, mismo motor de merge, nunca una segunda
  implementación).
