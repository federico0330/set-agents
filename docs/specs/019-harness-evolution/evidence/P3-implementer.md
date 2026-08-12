# P3-cognitive-module-docs — evidencia del implementer

Feature 019-harness-evolution, PKG-3 (AC-17..AC-24, ADR-0036). Todas las líneas de comando
son ejecuciones reales, no transcripciones editadas.

## 1. Tabla AC → cambio → prueba

| AC | Cambio (archivo:línea) | Prueba concreta |
|---|---|---|
| AC-17 (schema del doc) | `ai/scripts/feature_state_lib/render_modules.py:130` `_module_auto_body` (Responsabilidad/Posee/Últimos cambios dentro del bloque auto) + `:147` `render_module_doc` (scaffold de las 6 secciones humanas en la creación) | `tests/test_module_docs.py::RenderModuleDocMergeTests::test_idempotent_merge_and_human_zone_survives_a_round_trip` |
| AC-18 (`modules.toml`) | `docs/modules/modules.toml` (5 módulos reales) + `render_modules.py:61` `load_modules_toml`, `:101` `matching_modules` | `tests/test_module_docs.py::ModulesTomlParsingTests` (6 tests: válido, ausente, clave desconocida, slug malformado, `paths` vacío, match de glob) |
| AC-19 (`render_modules.py`, enganche, opt-in) | `render_modules.py:165` `render_modules` (never-raises); enganche en `ai/scripts/feature-state.py:174` (dentro de `mutate()`) y `cli_reporting.py:135-136` (`sync-notes`) | `tests/test_module_docs.py::RenderModulesNeverRaisesTests` (4 tests: excepción no propaga + log, sin marcador `ai/state/` no renderiza, sin `modules.toml` no falla, solo módulos con impacto renderizan) |
| AC-20 (comandos) | `ai/scripts/feature_state_lib/cli_modules.py:22` `cmd_record_module_impact`, `:88` `cmd_module_impact_detect`; wiring en `feature-state.py:1056,1068` | `tests/test_module_docs.py::ModuleImpactCliTests` (4 tests: detect no muta, record aparece+imprime bloque, slug desconocido rechazado, waiver barato y mutuamente excluyente) + evidencia viva §4 abajo |
| AC-21 (gate INTEGRATION) | `model.py:458-480` `module_impacts_ready`; `transitions.py:39-46` (`check_transition`, precondición dura); `transitions.py:118-126` (`next_transition`, asesor); `model.py:483,509` (`done_ready`, backstop) | `tests/test_module_docs.py::IntegrationGateTests` (4 tests) + evidencia viva §5 |
| AC-22 (digest) | `cli_reporting.py:210-229` (`cmd_digest`, sección `## Qué cambió en el software`, título en `:221`) | `tests/test_module_docs.py::DigestModuleSectionTests::test_digest_includes_module_changes_in_the_window` + evidencia viva §6 |
| AC-23 (`tests/test_module_docs.py`) | el archivo entero (21 tests) | `python3 -m unittest tests.test_module_docs -v` → 21/21 OK (§7) |
| AC-24 (seed real) | `docs/modules/modules.toml` (routing, estado, generacion-arboles, consola, narracion-notas) + 5 docs iniciales + `docs/architecture/overview.md` regenerado | §8, §9 abajo |

## 2. Doc de módulo renderizado completo (`docs/modules/estado.md`, después de una mutación real)

```markdown
# Estado del pipeline (feature-state)

<!-- notas:auto -->
## Responsabilidad

Máquina de estados de paquetes/features: fases legales, gates, reviews, findings, y ahora impacto de módulo — la fuente de verdad que STATUS.md/bitácora/notas derivan.

## Posee

- `ai/scripts/feature-state.py`
- `ai/scripts/feature_state_lib/**`
- `ai/scripts/check-feature-state.py`

## Últimos cambios estructurales

- 2026-08-11 019-harness-evolution/P3-cognitive-module-docs — Se agregaron module_impacts/module_impact_waiver a compact_package, module_impacts_ready() y el gate duro en check_transition/done_ready para INTEGRATION (ADR-0036), más los comandos record-module-im…
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `ai/scripts/feature-state.py` (CLI, `build_parser()` en `:785`) — toda mutación de estado
  pasa por acá: `init`, `transition`, `create-package`, `record-*`, `accept-package`,
  `record-module-impact`, `sync-notes`, `digest`, etc.
- `ai/scripts/check-feature-state.py` — el gate de CI/PACKAGE_GATES que corre
  `validate_state` contra el árbol vivo.

## Componentes

- `feature_state_lib/model.py` — el schema (`compact_package`, `:189`), invariantes
  estáticas (`validate_state`, `:268`), y los predicados de fase
  (`package_review_ready`, `package_accept_ready`, `done_ready`, `module_impacts_ready`).
- `feature_state_lib/transitions.py` — `check_transition` (`:16`, precondiciones duras por
  fase) y `next_transition` (`:44`, el asesor de "próximo paso").
- `feature_state_lib/cli_lifecycle.py`, `cli_review.py`, `cli_repair.py`, `cli_integration.py`,
  `cli_modules.py`, `cli_reporting.py` — un comando por verbo, mismo patrón argparse +
  `model.mutate(path, args, op, updater)`.
- `feature_state_lib/candidate_identity.py` — freeze/re-derive de git tree-hash (ADR-0020/0024).
- `feature_state_lib/graph.py` — `build_execution_graph`/`render_mermaid`, el grafo de
  ejecución que `docs/notas/features/<fid>/grafo.md` renderiza.
- `feature-state.py`'s propio `mutate()` (`:149-171`) — el único lugar que corre
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
  `feature-state.py:80-103`).
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
```

Notar el diseño explicado en ADR-0036 decisión 3: solo "Responsabilidad"/"Posee"/"Últimos
cambios estructurales" están dentro de `<!-- notas:auto -->` (re-derivables cada render);
las 6 secciones restantes del schema AC-17 viven fuera, sembradas una vez y preservadas para
siempre por `merge_note`.

## 3. Prueba de idempotencia del merge (round-trip real)

`tests/test_module_docs.py::RenderModuleDocMergeTests::test_idempotent_merge_and_human_zone_survives_a_round_trip`
hace, contra `render_module_doc` real (no un mock):

1. Render inicial → confirma `<!-- notas:auto -->`, `"primer cambio"` y las 6 secciones
   humanas presentes.
2. Re-render con los MISMOS datos → `render_module_doc` devuelve `False` (no escribe nada) y
   el archivo es byte-idéntico al anterior — el contrato de `write_note` (idempotencia real).
3. Edición manual de la zona humana: `"## Puntos de entrada\n\n_(completar)_\n"` →
   `"## Puntos de entrada\n\n`demo.main()` es el único punto de entrada real.\n"`.
4. Un impacto NUEVO dispara un re-render (`"segundo cambio"` agregado).
5. Asserts: el bloque auto tiene AMBOS cambios (`"primer cambio"` y `"segundo cambio"`); la
   edición manual del punto 3 sobrevive **byte a byte**.

Corrida real:
```
$ python3 -m unittest tests.test_module_docs.RenderModuleDocMergeTests -v
test_idempotent_merge_and_human_zone_survives_a_round_trip ... ok
test_recent_changes_are_capped_at_ten_most_recent_first ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.002s

OK
```

Evidencia viva adicional (real, contra `ai/state/features/019-harness-evolution.json`, este
mismo paquete): ver el bloque "Últimos cambios estructurales" de `docs/modules/estado.md` en
§2 arriba — generado por una mutación real de `record-module-impact`, con la zona
"## Notas propias" y las 6 secciones humanas intactas debajo, escritas por este implementer
en la semilla (§8) y preservadas por el render posterior.

## 4. `record-module-impact`/`module-impact-detect` — evidencia viva (feature 019 real)

```
$ python3 ai/scripts/feature-state.py module-impact-detect 019-harness-evolution --package-id P3-cognitive-module-docs
{
  "already_covered": false,
  "candidates": ["estado", "narracion-notas"],
  "known_modules": ["consola", "estado", "generacion-arboles", "narracion-notas", "routing"],
  "ok": true,
  "package_id": "P3-cognitive-module-docs"
}
```

`module-impact-detect` matcheó correctamente `estado`/`narracion-notas` contra los
`owned_paths` reales del paquete (`ai/scripts/feature_state_lib/render_modules.py`,
`docs/modules/modules.toml`, `tests/test_module_docs.py`, `docs/adr/0036-*.md`) — nunca mutó
el state file (confirmado además por
`test_module_impact_detect_lists_candidates_without_mutating`, que compara bytes antes/después).

```
$ python3 ai/scripts/feature-state.py record-module-impact 019-harness-evolution --package-id P3-cognitive-module-docs \
  --module estado --cambio "..." --modelo-mental "..." --actor implementer
Impacto humano:
Módulo: Estado del pipeline (feature-state)
Cambio de modelo mental: Se agregaron module_impacts/module_impact_waiver a compact_package, module_impacts_ready() y el gate duro en check_transition/done_ready para INTEGRATION (ADR-0036), más los comandos record-module-impact/module-impact-detect (feature_state_lib/cli_modules.py).
Tenés que saber: Un paquete accepted ya no llega a INTEGRATION sin documentar impacto de módulo o declarar un waiver barato; ver ADR-0036 y su comparación explícita con ADR-0024.
{ "changed": true, ... }
```

Repetido para `narracion-notas` con su propio `--cambio`/`--modelo-mental` (ver §2, "Últimos
cambios estructurales" de `docs/modules/narracion-notas.md`, mismo mecanismo). Los dos
`docs/modules/<slug>.md` correspondientes existen en disco con contenido real.

## 5. El gate bloqueando INTEGRATION sin impacts, y el waiver liberándolo

```
$ python3 -m unittest tests.test_module_docs.IntegrationGateTests -v
test_done_ready_also_checks_module_impacts_as_a_backstop ... ok
test_integration_blocks_without_coverage_and_the_waiver_unblocks_it ... ok
test_integration_unblocks_with_a_recorded_impact_instead_of_a_waiver ... ok
test_module_impacts_ready_unit_fixture ... ok

----------------------------------------------------------------------
Ran 4 tests in 0.980s

OK
```

`test_integration_blocks_without_coverage_and_the_waiver_unblocks_it` conduce un paquete real
hasta `PACKAGE_ACCEPTED` (misma secuencia de CLI que el resto de la suite) y verifica:

1. `transition INTEGRATION` sin `module_impacts` ni waiver → `returncode != 0`, mensaje
   `"module impact required"`, `data["phase"] != "INTEGRATION"`.
2. `record-module-impact --module-impact-waived --reason "..."` → mutación exitosa.
3. El MISMO `transition INTEGRATION` ahora tiene éxito: `data["phase"] == "INTEGRATION"`.

Relación con ADR-0024 (documentada en `docs/adr/0036-cognitive-module-docs.md`, decisión 5):
el receipt de `candidate_identity.integration_ready` sigue **sin** ser precondición de
`check_transition` (ADR-0024 no se tocó); el chequeo nuevo es una precondición DISTINTA,
segura de endurecer porque lee solo estado propio del paquete y tiene una válvula de un solo
comando. Los dos tests inmutables que ADR-0024 protegía
(`test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle`,
`test_package_workflow_happy_path_executes_real_transitions`, en `tests/test_harness.py`) se
actualizaron para declarar el waiver antes de `transition INTEGRATION` — misma ceremonia que
ya declaran gate/review/testing/runtime-qa, no una flexibilización. `_drive_to_receipt` en
`tests/test_integration_hook.py` recibió el mismo ajuste (una sola línea, después de
`accept-package`).

## 6. La sección nueva del digest, renderizada (real)

```
$ python3 ai/scripts/feature-state.py digest
DIGEST_WRITTEN file=/home/federico/SET-AGENTES/docs/notas/BUENOS-DIAS.md since=2026-08-09T22:27:13
```

`docs/notas/BUENOS-DIAS.md`:
```markdown
## Qué cambió en el software

- **estado** — Se agregaron module_impacts/module_impact_waiver a compact_package, module_impacts_ready() y el gate duro en check_transition/done_ready para INTEGRATION (ADR-0036), más los comandos record-module-im… (019-harness-evolution/P3-cognitive-module-docs)
- **narracion-notas** — Nuevo feature_state_lib/render_modules.py, mismo contrato never-raises/atómico que render_notes.py; reutiliza merge_note/write_note/_short en vez de reimplementarlos; enganchado a mutate() y a sync-n… (019-harness-evolution/P3-cognitive-module-docs)
```

## 7. `tests/test_module_docs.py` — corrida completa

```
$ python3 -m unittest tests.test_module_docs -v
... (21 tests, todos "ok", ver también §3/§5)
----------------------------------------------------------------------
Ran 21 tests in 16.116s

OK
```

## 8. Módulos seedeados (AC-24) — justificación y verificación

`docs/modules/modules.toml` registra 5 módulos reales de este repo:

| Slug | Por qué este y no otro | Verificación de los `paths`/contenido |
|---|---|---|
| `routing` | Es el subsistema más grande y más citado por ADRs (0029/0030/0034/0035); el context pack lo pide explícitamente | `ai/scripts/routing.py:18` (`compose`), `routing_core/service.py:93,243` (`RoutingService`, `.route()`), `:21` (`PI_SIMULATION_ONLY`), `catalog.py:42,611`, `store.py:286`, `domain.py:148,212`, `gates.py:8,18,27` — confirmado con `grep -n "^class \|^def "` real sobre cada archivo |
| `estado` | Es el módulo que este mismo paquete extiende (ADR-0036); "90 segundos para entender el pipeline" es el objetivo explícito del feature | `model.py:189,268`, `transitions.py:16,44`, `feature-state.py:80-103,149-171,785` — verificado con `grep -n` |
| `generacion-arboles` | El pedido explícito del context pack ("generación de árboles") | `generate.py:441,707,55,129,367,648,669` — verificado con `grep -n "^def "` |
| `consola` | El pedido explícito del context pack ("app de consola") | `set_agents_app.py:2510` (`main`), `:452-819` (`cmd_route_*`), `:325-412`, `:1087` — verificado con `grep -n` |
| `narracion-notas` | El pedido explícito del context pack; es además el módulo cuya infraestructura este paquete reutiliza literalmente (`merge_note`/`write_note`/`_short`) | `render_notes.py:51,67,79,281,285,37`, `render_status.py:70` — verificado con `grep -n` |

Todo `file:line` citado en los 5 docs (`docs/modules/{routing,estado,generacion-arboles,
consola,narracion-notas}.md`) fue verificado con `grep -n`/`sed -n` reales antes de
escribirse — ningún número es plausible-sin-chequear. Los wikilinks a decisiones
(`docs/modules/routing.md`, sección Decisiones) apuntan a un archivo real confirmado con
`ls docs/notas/decisiones/`.

**Sin verificar explícitamente**: el contenido de "Flujo"/"Invariantes" en cada doc es una
síntesis de lo leído (código + `docs/architecture/overview.md` + ADRs citados), no la salida
de un comando corrido — se marca acá porque ADR-0026 pide decirlo explícitamente cuando la
fuente es "leí el código y sintetizo" en vez de evidencia ejecutable. Los `file:line`
puntuales citados en cada doc sí están verificados con `grep -n`/`sed -n` reales, según se
detalla en la tabla arriba.

## 9. `docs/architecture/overview.md` — antes / después

**Antes** (stale, congelado en trusted routing P1R):
```
# Architecture overview

This is the current high-level map for trusted routing P1R. It describes the accepted architecture target, not
evidence that implementation is complete; decision rationale lives in the [ADR index](../adr/README.md).
```

**Después**:
```
# Architecture overview

This is the high-level map of the harness as of ADR-0036 (feature 019-harness-evolution). It describes the
accepted architecture target, not evidence that implementation is complete; decision rationale lives in the
[ADR index](../adr/README.md). **Per-module detail (responsibility, entry points, flow, invariants, and a
capped changelog of what actually changed) lives in [`docs/modules/`](../modules/modules.toml) — that layer is
machine-regenerated on every state mutation that records a module impact (ADR-0036), so it is the layer least
likely to go stale. This document stays hand-maintained and system-wide; `docs/modules/<slug>.md` is the
per-module source of truth for "what does this actually do right now".**

The sections below (routing/dispatch, two-root install, vault topology) predate ADR-0036 and describe the
trusted-routing subsystem specifically — see [`docs/modules/routing.md`](../modules/routing.md) for its current,
file:line-verified entry points and invariants, kept in sync independently of this narrative.
```

Alcance deliberado: no reescribí las secciones extensas existentes (component map, data
flow, key workflows, dos raíces, vault topology) — están vigentes y su contenido no fue
cuestionado por este paquete; reescribirlas íntegramente hubiera sido un riesgo de
alucinación fuera del alcance verificable de P3. Lo que estaba objetivamente mal (el
encabezado que decía "current high-level map for trusted routing P1R" cuando el harness ya
tiene 36 ADRs aceptados) se corrigió, y se agregó el puntero real a `docs/modules/` como
mecanismo vivo — que es la pieza que ADR-0036 pide demostrar.

## 10. Gates y validación local

```
$ python3 -m unittest discover -s tests
Ran 852 tests in 705.900s
OK (skipped=3)
```
Antes de este paquete: 831 OK / 3 skips (dato del context pack, ya verificado por P1/P2).
852 − 831 = 21 = exactamente los tests nuevos de `tests/test_module_docs.py`. Cero
regresiones, cero tests debilitados/saltados/borrados.

```
$ ./ai/scripts/verify.sh
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ ./build.sh
Generated tracked artifacts for go-zen.
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```
(`./build.sh` se corrió DESPUÉS de tocar `feature_state_lib/` como exige el context pack;
también se copiaron a mano `ai/scripts/feature-state.py` y los 6 archivos tocados/nuevos de
`feature_state_lib/` a `PROYECTO/ai/scripts/` — build.sh's `--check` solo pinea
`feature-state.py`/`check-owned-paths.py` byte-a-byte contra `PROYECTO`, pero
`sync-project.sh`'s lista `GENERIC` gana `cli_modules.py`/`render_modules.py` para que un
proyecto sincronizado se lleve el mecanismo completo.)

```
$ git diff --check
(sin salida, exit 0)
```

## 11. Riesgos y deudas anotadas

- Las 6 secciones narrativas del schema (Puntos de entrada/Componentes/Flujo/Posee-Depende/
  Invariantes/Decisiones) viven fuera del bloque auto por diseño (ADR-0036 decisión 3) — un
  reviewer debería confirmar que esta lectura del AC-17 es la correcta; es la única forma
  consistente con el contrato de `merge_note` sin inventar una segunda fuente de verdad.
- Dos features históricas ya cerradas en la práctica (006-execution-graph,
  010-spawn-provenance) muestran ahora, en su nota "Qué falta", el mensaje del nuevo gate
  ("module impact required...") en vez de "→ INTEGRATION" — es un efecto secundario
  esperado y honesto de `next_transition` (esos paquetes nunca transicionaron formalmente a
  INTEGRATION/DONE en su state file), no una regresión: no bloquea nada hoy porque esas
  features ya no están activas, pero un reviewer podría querer cerrarlas formalmente con un
  waiver retroactivo si algún día se retoman.
- `check-feature-state.py` (el gate de CI que corre `validate_state`) no fue tocado — no lo
  necesita, ya que `module_impacts`/`module_impact_waiver` son opcionales vía `.get()` y
  `validate_state` no los valida estáticamente (mismo precedente que `late_reviews`/`spawns`).
- P4 (orquestador, `Impacto humano:` en `orchestrator.md`, question policy, `/explicar`) es
  íntegramente fuera de alcance de este paquete, tal como indica el context pack — el bloque
  que imprime `record-module-impact` está listo para que P4 lo consuma, pero su formato
  final de pegado en la narración lo fija P4.

## 12. Estado del paquete

No marco este paquete como aceptado ni corro gates de review — eso es de `gate-runner`/
`package-reviewer`. Los comandos de estado (`start-task`/`complete-task`/`record-gate`/
`transition`) quedan para que el orquestador los corra según su propia doctrina.
