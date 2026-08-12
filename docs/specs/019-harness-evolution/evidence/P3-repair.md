# P3-cognitive-module-docs — repair evidence (findings F-01..F-07)

Repair consolidado, una sola pasada, ceiling de un intento por ciclo (ADR-0023). Ownership respetado:
`ai/scripts/feature_state_lib/{render_modules.py,cli_modules.py,cli_reporting.py}`, `docs/modules/**`,
`docs/architecture/overview.md`, `docs/adr/0036-cognitive-module-docs.md`, `tests/test_module_docs.py`.
No se tocó `routing_core/`, `models.toml`, `set_agents_app.py`, `setup_models.py` ni
`Global/_canonical/agents|commands|skills` (esos cambios que aparecen en `git status` son de otros
paquetes ya aceptados, preexistentes en el árbol de trabajo, no de este repair).

## Tabla hallazgo → cambio → verificación

| # | Severidad | Cambio | Archivo:línea | Verificación |
|---|---|---|---|---|
| F-01 | alto | Reescritas las dos frases de `docs/architecture/overview.md` que afirmaban que las 8 secciones (incl. entry points/flow/invariants) se regeneran solas: ahora dicen explícitamente que solo `## Responsabilidad`, `## Posee`/`## Posee / Depende de` y `## Últimos cambios estructurales` son machine-regenerated, y que el resto es prosa humana sembrada que puede envejecer. | `docs/architecture/overview.md:5-13` | Lectura directa del párrafo reescrito; `git diff --check` limpio; suite completa sigue en verde (ningún test pinea la redacción vieja). |
| F-02 | medio | 6 anclas `file:line` de `docs/modules/estado.md` corregidas contra el árbol actual (`build_parser` 785→788, `compact_package` 189→190, `validate_state` 268→277, `check_transition` 16→17, `next_transition` 44→54, `mutate` 149-171→151-174); + 2 anclas de `docs/modules/narracion-notas.md` corregidas (`mutate` 149-171→151-174, `cmd_digest` 152→154) y `_short` 79→80. Resto de anclas de ambos docs re-verificadas y confirmadas correctas (ver sección abajo). | `docs/modules/estado.md:25,33-37,44`; `docs/modules/narracion-notas.md:27,31,38` | `grep -n "^def <nombre>"` contra cada archivo real, comandos pegados abajo. |
| F-03 | medio | `feature_id`/`package_id` (y `module` en el digest) pasan por `_short(...)` antes de entrar al bloque máquina, en `render_modules.py` (`_module_auto_body`) y `cli_reporting.py` (`cmd_digest`). Test nuevo que prueba la neutralización con un `package_id` conteniendo newlines y un `<!-- notas:auto -->` forjado. | `ai/scripts/feature_state_lib/render_modules.py:138-150`; `ai/scripts/feature_state_lib/cli_reporting.py:221-229` | `tests/test_module_docs.py::RenderModuleDocInjectionTests::test_a_newline_carrying_package_id_cannot_inject_a_fake_heading` — pasa. |
| F-04 | medio | Línea visible (texto normal, no comentario HTML) al final del bloque máquina de cada `docs/modules/<slug>.md`: `STALENESS_NOTICE`, emitida por `render_module_doc`/`_module_auto_body`, nunca escrita a mano. | `ai/scripts/feature_state_lib/render_modules.py:130-155,158-166` | `tests/test_module_docs.py::RenderModuleDocMergeTests` (round-trip) sigue en verde con la línea nueva presente en el body; inspección visual del contenido generado. |
| F-05 | bajo | `test_no_ai_state_marker_means_no_render_no_failure` ahora assertea `rm.modules_toml_path(state) is None` directamente, no solo el efecto observable (que el fallback "toml ausente → `{}}`" enmascaraba). | `tests/test_module_docs.py:240-261` | Prueba de mordida pegada abajo: falla con la regresión inyectada, pasa restaurado. |
| F-06 | bajo | `module-impact-detect` reporta `unmatched_paths` (paths que no matchearon ningún módulo) en una sección aparte de `candidates`, vía `unmatched_candidate_paths()` nuevo en `render_modules.py`. Advisory, no gatea nada. Límite conocido (glob-vs-glob) documentado en el docstring de `matching_modules` y en ADR-0036 decisión 4, explícitamente NO reparado (rediseño). | `ai/scripts/feature_state_lib/render_modules.py:101-136`; `ai/scripts/feature_state_lib/cli_modules.py:17-19,95-111`; `docs/adr/0036-cognitive-module-docs.md` (decisión 4) | `tests/test_module_docs.py::ModuleImpactCliTests::test_module_impact_detect_reports_unmatched_paths_advisory_only` y `::ModulesTomlParsingTests::test_unmatched_candidate_paths_reports_orphans_only` — pasan. |
| F-07 | bajo (proceso) | ADR-0036 decisión 3 gana un párrafo con el puntero explícito a la decisión registrada por el orquestador (`ai/state/decisions-log.jsonl`, slug `el-schema-de-ac-17-se-parte-...`) y a la condición que la acompaña (F-01 + F-04 reparados). No se reargumenta el fondo. | `docs/adr/0036-cognitive-module-docs.md` (decisión 3, párrafo nuevo) | Lectura directa; el wikilink apunta a `docs/notas/decisiones/2026-08-11 el-schema-de-ac-17-se-parte-...md`, que existe en disco. |

## F-02 — anclas re-verificadas, con el comando exacto

```
$ grep -n "^def build_parser" ai/scripts/feature-state.py
788:def build_parser() -> argparse.ArgumentParser:

$ grep -n "^def compact_package" ai/scripts/feature_state_lib/model.py
190:def compact_package(package_id: str, objective: str) -> dict[str, Any]:

$ grep -n "^def validate_state" ai/scripts/feature_state_lib/model.py
277:def validate_state(data: dict[str, Any]) -> list[str]:

$ grep -n "^def check_transition" ai/scripts/feature_state_lib/transitions.py
17:def check_transition(data: dict[str, Any], to_phase: str, package_id: str | None, actor: str) -> None:

$ grep -n "^def next_transition" ai/scripts/feature_state_lib/transitions.py
54:def next_transition(data: dict[str, Any]) -> dict[str, Any]:

$ grep -n "^def mutate" ai/scripts/feature-state.py
151:def mutate(
# función completa hasta el return, confirmada por lectura directa: 151-174
#   174:    return data, before != data

$ grep -n "^def merge_note\|^def write_note\|^def _short\|^def notes_root\|^def _log_render_failure\|^RENDER_FAILURE_LOG" \
    ai/scripts/feature_state_lib/render_notes.py
37:def notes_root(state_file: Path, notes_dir: str | None = None) -> Path | None:
51:def merge_note(existing: str | None, title: str, body: str) -> str:
67:def write_note(path: Path, title: str, body: str) -> bool:
80:def _short(text: Any, limit: int = 120) -> str:
281:RENDER_FAILURE_LOG = "render-failures.log"
285:def _log_render_failure(out_dir: Path, context: str, exc: BaseException) -> None:

$ grep -n "^def cmd_digest" ai/scripts/feature_state_lib/cli_reporting.py
154:def cmd_digest(args: argparse.Namespace) -> int:

$ grep -n "^def render_status" ai/scripts/feature_state_lib/render_status.py
70:def render_status(state_file: Path) -> None:
```

Resultado: 6 anclas de `estado.md` corregidas (785→788, 189→190, 268→277, 16→17, 44→54, 149-171→151-174).
2 anclas de `narracion-notas.md` corregidas (149-171→151-174, 152→154), 1 más corregida (`_short` 79→80).
El resto de las anclas de ambos docs (`merge_note:51`, `write_note:67`, `notes_root:37`,
`RENDER_FAILURE_LOG:281`, `_log_render_failure:285`, `render_status:70`, y el rango de docstring
`feature-state.py:80-103`) fueron re-corridas contra el árbol actual y confirmadas correctas —
ningún número quedó sin verificar ahora mismo.

## F-05 — prueba de mordida (inyecté la regresión, verifiqué la falla, restauré, verifiqué el pase)

**1. Regresión inyectada** en `ai/scripts/feature_state_lib/render_modules.py::modules_toml_path`
(se quitó el check `ai/state/`):

```python
    _, out_dir = status_root(state_file)
    return out_dir.parent.parent / "docs" / "modules" / MODULES_TOML
```

**2. Test corrido con la regresión — falla:**

```
$ python3 -m unittest tests.test_module_docs.RenderModulesNeverRaisesTests.test_no_ai_state_marker_means_no_render_no_failure -v
test_no_ai_state_marker_means_no_render_no_failure ... FAIL

FAIL: test_no_ai_state_marker_means_no_render_no_failure
AssertionError: PosixPath('/var/docs/modules/modules.toml') is not None

Ran 1 test in 0.002s
FAILED (failures=1)
```

**3. Árbol restaurado** (`cp` desde el backup tomado antes de inyectar) y **re-corrido — pasa:**

```
$ python3 -m unittest tests.test_module_docs.RenderModulesNeverRaisesTests.test_no_ai_state_marker_means_no_render_no_failure -v
test_no_ai_state_marker_means_no_render_no_failure ... ok

Ran 1 test in 0.002s
OK
```

`git status --short ai/scripts/feature_state_lib/render_modules.py` después de restaurar: sin diferencias
respecto del estado post-repair (archivo untracked, sin huellas de la inyección).

## Sincronización de árboles (build.sh)

`render_modules.py`/`cli_modules.py`/`cli_reporting.py` cambiaron → copiados también a
`PROYECTO/ai/scripts/feature_state_lib/` (mismo criterio que el resto de `feature_state_lib/`, ya que
`tests/test_module_docs.py` ejecuta el CLI real vía `PROYECTO/ai/scripts/feature-state.py` en subprocess).
`./build.sh` regeneró los 4 árboles de `Global/` desde la fuente. `./build.sh --check` confirmó cero
drift.

## Gates

```
$ python3 -m unittest discover -s tests
Ran 855 tests in 871.549s
OK (skipped=3)
```

(852 antes del repair + 3 tests nuevos de este repair: la inyección F-03, y los dos de F-06 —
`test_unmatched_candidate_paths_reports_orphans_only` y
`test_module_impact_detect_reports_unmatched_paths_advisory_only`. F-05 modificó un test existente sin
sumar uno nuevo.)

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
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
```

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida — limpio)
```

## Findings NO tocados / fuera de alcance de este repair

- La limitación glob-vs-glob de `matching_modules`/`unmatched_candidate_paths` (parte de F-06) se deja
  documentada, no reparada — es rediseño, según lo pedido.
- No se reargumenta la desviación de AC-17 (F-07): el registro del orquestador (`log-decision`) queda
  como la fuente de verdad de esa decisión; este repair solo agrega el puntero desde el ADR.

---

# Ciclo 2 (delta review) — hallazgos D-01..D-04

Segundo y último ciclo de repair, ceiling de un intento (ADR-0023). D-01 reabre F-04, condición explícita
de la aceptación de la desviación de AC-17 registrada en `ai/state/decisions-log.jsonl` — sin cerrarlo el
paquete no se acepta. Ownership respetado: `ai/scripts/feature_state_lib/render_modules.py`,
`docs/modules/**`, `docs/architecture/overview.md`, `docs/adr/0036-cognitive-module-docs.md`,
`tests/test_module_docs.py`. No se tocó `routing_core/`, `models.toml`, `set_agents_app.py`,
`setup_models.py` ni `Global/_canonical/agents|commands|skills`.

## Tabla hallazgo → cambio → verificación

| # | Severidad | Cambio | Archivo:línea | Verificación |
|---|---|---|---|---|
| D-01 | medio (reabre F-04) | Defecto de diseño de raíz: el `continue` incondicional de `render_modules()` saltaba TODO módulo sin impacts, incluso bajo `force` — un módulo sembrado antes de tener un impact nunca podía volver a regenerarse, ni siquiera para adoptar un cambio de formato del bloque máquina (exactamente lo que pasó con la línea de staleness de F-04). Arreglo mínimo: el `continue` ahora es condicional a `not force`; la pasada incremental (mutation-time, sin `force`) sigue saltando módulos sin impacts tal cual antes (AC-19, nunca 30 scaffolds vacíos en cada mutación); la pasada full-regen de `sync-notes` (`force=True`, único caller real) SÍ los regenera. `_module_auto_body` ya emitía el body correcto ("sin cambios registrados todavía") para `changes=[]`, así que no hizo falta tocar el body. Corrida `sync-notes` real: regeneró `routing.md`, `consola.md`, `generacion-arboles.md` (los 3 que le faltaban). | `ai/scripts/feature_state_lib/render_modules.py:269-278` | `python3 ai/scripts/feature-state.py sync-notes` → `{"written": ["routing.md", "generacion-arboles.md", "consola.md"]}`; `grep -n "Debajo de esta línea" docs/modules/*.md` da 5/5 (antes 2/5); diff línea por línea contra el contenido leído pre-render confirma que la ÚNICA diferencia en los 3 docs es la línea de staleness insertada antes del cierre de marcador — prosa humana (Puntos de entrada/Componentes/Flujo/Posee-Depende de/Invariantes/Decisiones) byte-idéntica. Test nuevo de mordida abajo. |
| D-02 | bajo | `docs/architecture/overview.md` decía que `## Posee / Depende de` es machine-regenerated; el motor solo emite `## Posee` (heading distinto, sin "Depende de"). Reescritas ambas menciones (párrafo de apertura + nota sobre `routing.md`) para nombrar exactamente las 3 secciones que el código emite (`Responsabilidad`, `Posee`, `Últimos cambios estructurales`) y aclarar que `## Posee / Depende de` (con su mitad "Depende de") es la sección del scaffold humano. | `docs/architecture/overview.md:3-19` | Lectura directa del párrafo reescrito; `grep -n "## Posee" ai/scripts/feature_state_lib/render_modules.py` confirma que el código solo emite `"## Posee"` (línea 160), nunca `"## Posee / Depende de"`. |
| D-03 | bajo | Reconciliada la decisión 3 del ADR: el conteo previo se contradecía entre "dos de ocho... seis restantes" (párrafo original) y "3 derivadas/5 sembradas" (párrafo F-07 agregado en el ciclo 1, y la decisión registrada del orquestador). Reescrita la decisión 3 completa con la cuenta que el código REALMENTE hace: el schema nombra 8 secciones; `Responsabilidad` y `Últimos cambios estructurales` son íntegramente derivadas; `Posee / Depende de` se PARTE — su mitad "Posee" gana un heading máquina nuevo (`## Posee`, distinto del heading de schema `## Posee / Depende de`) mientras su mitad "Depende de" queda íntegra del lado humano bajo el heading original; las 5 restantes (`Puntos de entrada`, `Componentes`, `Flujo`, `Posee / Depende de` completa, `Invariantes`, `Decisiones`) quedan íntegramente sembradas. Resultado: 3 secciones del bloque máquina, cubriendo contenido de 3 de las 8 del schema, 5 íntegramente sembradas — una sola cuenta, consistente con el párrafo F-07 y con la decisión del orquestador, y sin ambigüedad de qué heading (`## Posee` vs. `## Posee / Depende de`) vive de qué lado. También corregido "seis de las ocho" → "las cinco restantes" en Rejected alternatives (mismo conteo). El docstring de `render_modules.py` (que hacía la misma afirmación "eight sections" listando 9 ítems) se corrigió en paralelo, mismo archivo que ya está en ownership de este repair. | `docs/adr/0036-cognitive-module-docs.md:30-58,120`; `ai/scripts/feature_state_lib/render_modules.py:1-11` | Lectura directa; conteo de paréntesis balanceado (`python3 -c` script, 45 open / 45 close) pegado abajo; cita `_module_auto_body:158-182` verificada contra el archivo real (ver D-04 abajo, misma metodología). |
| D-04 | bajo | Ancla `feature-state.py:80-103` (`estado.md:68`) corregida a `:82-105` — línea 80 es un import, no el comentario; el comentario real (`# \`replayed\`/\`record_event\`/\`mutate\` stay physically defined...`) va de 82 a 105 (105 es `# would otherwise silently stop seeing a test's patch.`). Verificado con `sed -n`, no con memoria ni con la evidencia del ciclo anterior. Re-verificadas TODAS las anclas de los 5 docs (tabla completa abajo): 0 adicionales incorrectas encontradas. | `docs/modules/estado.md:68` | `sed -n '82p;105p' ai/scripts/feature-state.py` (salida pegada abajo). |

## D-01 — prueba de mordida del test nuevo

Test nuevo: `RenderModulesNeverRaisesTests.test_force_still_renders_a_module_with_no_impacts`
(`tests/test_module_docs.py`), que declara un módulo con `owned_paths=[]` (cero `module_impacts`) y
verifica que `render_modules(state, force=True)` SÍ lo regenera (`written == ["demo.md"]`), con el body
"sin cambios registrados todavía" + `STALENESS_NOTICE` presentes.

**1. Test corrido contra el código reparado — pasa:**

```
$ python3 -m unittest tests.test_module_docs.RenderModulesNeverRaisesTests.test_force_still_renders_a_module_with_no_impacts -v
test_force_still_renders_a_module_with_no_impacts ... ok

Ran 1 test in 0.004s

OK
```

**2. Regresión inyectada** (revertido el fix: `if not changes and not force:` → `if not changes:`,
exactamente el defecto original de D-01) — **el test nuevo falla:**

```
$ python3 -m unittest tests.test_module_docs.RenderModulesNeverRaisesTests.test_force_still_renders_a_module_with_no_impacts -v
FAIL: test_force_still_renders_a_module_with_no_impacts
AssertionError: Lists differ: [] != ['demo.md']

Ran 1 test in 0.005s

FAILED (failures=1)
```

**3. Fix restaurado** (`cp` desde backup tomado antes de inyectar) y **re-corrido — pasa** (ver paso 1).
`grep -n "not force" ai/scripts/feature_state_lib/render_modules.py` tras restaurar confirma las dos
apariciones esperadas (`RENDER_SKIP and not force` preexistente + `not changes and not force` nuevo),
ninguna huella de la inyección.

## D-04 — re-verificación completa de anclas, los 5 docs, comando por comando

| Archivo:línea citada | Comando corrido | Resultado |
|---|---|---|
| `estado.md:27` `feature-state.py` `build_parser()` `:788` | `sed -n '788p' ai/scripts/feature-state.py` | `def build_parser() -> argparse.ArgumentParser:` — OK |
| `estado.md:35` `compact_package` `:190` | `sed -n '190p' ai/scripts/feature_state_lib/model.py` | `def compact_package(package_id: str, objective: str) -> dict[str, Any]:` — OK |
| `estado.md:36` `validate_state` `:277` | `sed -n '277p' ai/scripts/feature_state_lib/model.py` | `def validate_state(data: dict[str, Any]) -> list[str]:` — OK |
| `estado.md:38` `check_transition` `:17` | `sed -n '17p' ai/scripts/feature_state_lib/transitions.py` | `def check_transition(...)` — OK |
| `estado.md:39` `next_transition` `:54` | `sed -n '54p' ai/scripts/feature_state_lib/transitions.py` | `def next_transition(data: dict[str, Any]) -> dict[str, Any]:` — OK |
| `estado.md:46` `mutate()` `:151-174` | `sed -n '151p;174p' ai/scripts/feature-state.py` | `def mutate(` / `    return data, before != data` — OK, rango correcto |
| `estado.md:68` `feature-state.py:80-103` | `sed -n '80p;103p'` (antes de corregir) | `80`=línea en blanco, `103`=línea de comentario intermedia, NO el cierre — mal. Corregido a `:82-105`: `sed -n '82p;105p'` → `# \`replayed\`/\`record_event\`/\`mutate\` stay physically defined...` / `# would otherwise silently stop seeing a test's patch.` — OK tras la corrección |
| `narracion-notas.md:29` `mutate()` `:151-174` | (mismo comando que arriba) | OK |
| `narracion-notas.md:33` `cmd_digest` `:154` | `sed -n '154p' ai/scripts/feature_state_lib/cli_reporting.py` | `def cmd_digest(args: argparse.Namespace) -> int:` — OK |
| `narracion-notas.md:39` `merge_note` `render_notes.py:51` | `sed -n '51p' ai/scripts/feature_state_lib/render_notes.py` | `def merge_note(existing: str \| None, title: str, body: str) -> str:` — OK |
| `narracion-notas.md:40` `write_note` `:67` | `sed -n '67p' ai/scripts/feature_state_lib/render_notes.py` | `def write_note(path: Path, title: str, body: str) -> bool:` — OK |
| `narracion-notas.md:40` `_short` `:80` | `sed -n '80p' ai/scripts/feature_state_lib/render_notes.py` | `def _short(text: Any, limit: int = 120) -> str:` — OK |
| `narracion-notas.md:43` `notes_root` `:37` | `sed -n '37p' ai/scripts/feature_state_lib/render_notes.py` | `def notes_root(state_file: Path, notes_dir: str \| None = None) -> Path \| None:` — OK |
| `narracion-notas.md:45` `render_status` `render_status.py:70` | `sed -n '70p' ai/scripts/feature_state_lib/render_status.py` | `def render_status(state_file: Path) -> None:` — OK |
| `narracion-notas.md:49` `RENDER_FAILURE_LOG` `render_notes.py:281` | `sed -n '281p' ai/scripts/feature_state_lib/render_notes.py` | `RENDER_FAILURE_LOG = "render-failures.log"` — OK |
| `narracion-notas.md:50` `_log_render_failure` `:285` | `sed -n '285p' ai/scripts/feature_state_lib/render_notes.py` | `def _log_render_failure(out_dir: Path, context: str, exc: BaseException) -> None:` — OK |
| `routing.md:26-27` `routing.compose` `ai/scripts/routing.py:18` | `sed -n '18p' ai/scripts/routing.py` | `def compose(config, roster, *, simulate=False, fresh_probes=False, store=None):` — OK |
| `routing.md:28-30` `set_agents_app.py:452-488` | `sed -n '452p;488p' ai/scripts/set_agents_app.py` | `def cmd_route_explain(...)` / `def cmd_route_doctor(...)` — dentro del bloque de comandos de routing, rango razonable — OK |
| `routing.md:31-32` `RoutingService.route` `service.py:243` | `sed -n '243p' ai/scripts/routing_core/service.py` | `def route(self, request: TaskRequest, ...)` — OK |
| `routing.md:36-37` `TaskRequest:148`/`RouteDecision:212`/`CatalogSnapshot:200`/`RoutingError:9` | `sed -n '148p;212p;200p;9p' ai/scripts/routing_core/domain.py` | `class TaskRequest:` / `class RouteDecision:` / `class CatalogSnapshot:` / `class RoutingError(ValueError):` — las 4 OK |
| `routing.md:38-40` `build_snapshot:611`/`pi_pinned_argv:42` | `sed -n '611p;42p' ai/scripts/routing_core/catalog.py` | `def build_snapshot(...)` / `def pi_pinned_argv(*args: str) -> tuple[str, ...]:` — OK |
| `routing.md:41-42` `RoutingService:93`/`PI_SIMULATION_ONLY:21` | `sed -n '93p;21p' ai/scripts/routing_core/service.py` | `class RoutingService:` / `PI_SIMULATION_ONLY = False` — OK |
| `routing.md:43-44` `RoutingStore:286` | `sed -n '286p' ai/scripts/routing_core/store.py` | `class RoutingStore:` — OK |
| `routing.md:45-46` `gates.py:8-27` | `sed -n '8p;27p' ai/scripts/routing_core/gates.py` | `class GateSpec:` / `def run_gate(...)` — OK, rango correcto |
| `routing.md:69` `service.py:315` | `sed -n '310,320p' ai/scripts/routing_core/service.py` | línea 315 = `elif route.model not in ... reason="PROVIDER_UNAUTHENTICATED"` — coincide exactamente con la prosa ("un par no probado/no autenticado falla cerrado") — OK |
| `consola.md:24` `set_agents_app.py:2510` `main()` | `sed -n '2510p' ai/scripts/set_agents_app.py` | `def main():` — OK |
| `consola.md:32` `set_agents_app.py:452-819` | `sed -n '452p;819p' ai/scripts/set_agents_app.py` | `def cmd_route_explain(...)` / `def cmd_doctor_all():` — rango razonable, `cmd_doctor_all` es el último `cmd_route_*/cmd_doctor*` antes de 819 — OK |
| `consola.md:34-35` `set_agents_app.py:325-412` | `sed -n '325p;412p' ai/scripts/set_agents_app.py` | `def cmd_model_preference_set(...)` / `def cmd_model_pin_clear(role):` — OK |
| `consola.md:36` `set_agents_app.py:1087` `cmd_status` | `sed -n '1087p' ai/scripts/set_agents_app.py` | `def cmd_status(human=False):` — OK |
| `generacion-arboles.md:25` `generate.py:441` `generate()` | `sed -n '441p' ai/scripts/generate.py` | `def generate(out, profile, roles_path=None, models_path=None, routes_path=None):` — OK |
| `generacion-arboles.md:27` `generate.py:707` `main()` | `sed -n '707p' ai/scripts/generate.py` | `def main():` — OK |
| `generacion-arboles.md:33-34` `generate.py:55` `load_roles` | `sed -n '55p' ai/scripts/generate.py` | `def load_roles(profile, roles_path=None, models_path=None):` — OK |
| `generacion-arboles.md:35-37` `generate.py:129` `oc_permissions` | `sed -n '129p' ai/scripts/generate.py` | `def oc_permissions(capability, roles, role=None, yolo=False, variant_names=()):` — OK |
| `generacion-arboles.md:38-39` `generate.py:367` `generate_pi_prompts` | `sed -n '367p' ai/scripts/generate.py` | `def generate_pi_prompts(out):` — OK |
| `generacion-arboles.md:40-41` `generate.py:648`/`669` `validate_pi_target`/`validate` | `sed -n '648p;669p' ai/scripts/generate.py` | `def validate_pi_target(roles):` / `def validate(out, roles=None, ...)` — OK |
| `docs/adr/0036...:45` `_module_auto_body:158-182` (nueva cita, agregada en este ciclo por D-03) | `sed -n '158p;182p' ai/scripts/feature_state_lib/render_modules.py` | `def _module_auto_body(...)` / `    return "\n".join(lines)` — OK, rango correcto de la función completa |

**Resultado**: 1 ancla mal (D-04, `estado.md:68`, corregida a `:82-105`). Las 33 restantes, corridas de
nuevo contra el árbol actual (no memoria, no la evidencia del ciclo anterior), confirmadas correctas.

## D-03 — balanceo de paréntesis de la decisión 3 reescrita

```
$ python3 -c "
s = open('docs/adr/0036-cognitive-module-docs.md').read()
seg = s[s.index('## Decisión'):s.index('## Rejected')]
print('open parens', seg.count('('), 'close parens', seg.count(')'))
"
open parens 45 close parens 45
```

## Sincronización de árboles (build.sh)

`render_modules.py` cambió (D-01 + docstring de D-03) → copiado a `PROYECTO/ai/scripts/feature_state_lib/`
(mismo criterio de siempre, ya que `tests/test_module_docs.py` ejecuta el CLI real vía
`PROYECTO/ai/scripts/feature-state.py` en subprocess). `./build.sh` regeneró los 4 árboles de `Global/`
(incluye el hooks-copy de `feature_state_lib/`). `./build.sh --check` confirmó cero drift en los 4 árboles
+ `PROYECTO/` (`SELF_SCAFFOLD_SYNC_OK files=2`).

## Gates

```
$ python3 -m unittest discover -s tests
Ran 856 tests in 472.389s

OK (skipped=3)
```

(855 tests pre-existentes al cierre del ciclo 1 + 1 test nuevo de este ciclo —
`test_force_still_renders_a_module_with_no_impacts` — = 856; 3 skips preexistentes sin cambios.)

```
$ ./ai/scripts/verify.sh
...
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
...
Ran 856 tests in 421.855s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
```

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida — limpio)
```

## Findings NO tocados / fuera de alcance de este ciclo

- `generacion-arboles.md`'s Invariantes claim ("un test de la suite pinea esa igualdad" [byte-identidad
  `feature_state_lib/` vs. `Global/*/hooks/`/`PROYECTO/`]) no es una cita `archivo:línea` — es prosa
  humana sin ancla puntual, fuera del alcance explícito de D-04 (que pide re-verificar citas
  `archivo:línea`). Búsqueda (`grep -rn feature_state_lib tests/test_harness.py`) no encontró un test así
  de nombrado; queda como observación, no como hallazgo reparado — corregirlo sería tocar prosa humana
  sembrada fuera del alcance de los 4 hallazgos asignados a este ciclo.

---

# Ciclo 3 (delta review) — hallazgo N-01

Repair de un solo hallazgo, ceiling de un intento (ADR-0023). Ownership respetado:
`docs/adr/0036-cognitive-module-docs.md` (decisión 3) y `ai/scripts/feature_state_lib/render_modules.py`
(solo el docstring). Nada más tocado.

## Conteo hecho antes de escribir (pedido explícito de la asignación)

```
$ python3 - <<'EOF'
sections = [
    "Puntos de entrada",
    "Componentes",
    "Flujo",
    "Posee / Depende de",
    "Invariantes",
    "Decisiones",
]
print(len(sections))
EOF
6
```

`HUMAN_SCAFFOLD_SECTIONS` (`ai/scripts/feature_state_lib/render_modules.py:36-43`) tiene **6** entradas.
Ambos textos (ADR decisión 3, docstring de `render_modules.py`) decían "cinco"/"five" y enumeraban esas
mismas 6 entradas — la incoherencia residual que N-01 señala. Cuenta coherente aplicada: **6 headings
sembrados en total; 5 de ellos sin ningún campo estructurado que los derive; el 6º (`Posee / Depende de`)
es la mitad humana de una sección cuya mitad máquina el motor sí emite por separado como `## Posee`**.

## Tabla hallazgo → cambio → verificación

| # | Severidad | Cambio | Archivo:línea | Verificación |
|---|---|---|---|---|
| N-01 | bajo | `docs/adr/0036-cognitive-module-docs.md` decisión 3: "cinco secciones íntegramente sembradas" (enumerando 6 ítems) → "**seis** secciones sembradas... de esas seis, **cinco** no tienen ningún campo estructurado... que las derive" (corregido también el pronombre "la"→"las", plural). `render_modules.py` docstring: "the remaining **five** (...)" (listando 6 ítems) → "**six** headings total (...); five of them with no machine-derived half at all, the sixth being the human half of the split above". | `docs/adr/0036-cognitive-module-docs.md:47,49`; `ai/scripts/feature_state_lib/render_modules.py:8-11` | Conteo con `python3` pegado arriba (6). Lectura directa del texto corregido en ambos archivos (pegado abajo). |

### Texto corregido — ADR, decisión 3 (líneas 46-50)

```
de **tres de las ocho** secciones del schema (`Responsabilidad`, la mitad "Posee" de `Posee / Depende de`,
`Últimos cambios estructurales`), y **seis secciones sembradas** en `HUMAN_SCAFFOLD_SECTIONS`
(`Puntos de entrada`, `Componentes`, `Flujo`, `Posee / Depende de` completa — con su prosa de "Depende de"
irreemplazable —, `Invariantes`, `Decisiones`); de esas seis, cinco no tienen ningún campo estructurado en el
estado que las derive: forzarlas dentro del bloque auto las condenaría a placeholder eterno o, peor, a
```

### Texto corregido — `render_modules.py` docstring (líneas 7-11)

```
a third (Posee / Depende de) is split -- its "Posee" half gets its own machine heading
here, its "Depende de" half stays seeded prose -- and six headings total (Puntos de
entrada, Componentes, Flujo, Posee / Depende de, Invariantes, Decisiones; five of them
with no machine-derived half at all, the sixth being the human half of the split above)
are seeded once and then preserved as human-owned content -- forcing narrative-only
```

## Gates

```
$ python3 -m unittest tests.test_module_docs
Ran 25 tests in 8.205s

OK
```

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
```

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida — limpio)
```

`pytest` no está instalado en este entorno (confirmado, no se corrió).

## Findings NO tocados / fuera de alcance de este ciclo

- Otras menciones de "cinco"/"seis" en el mismo ADR (línea 61: "3 secciones derivadas... 5 sembradas en
  zona humana" dentro del párrafo F-07; líneas 64/66: el slug literal del wikilink al decision-log) no se
  tocaron: describen el conteo de 8 secciones del schema (3 con alguna derivación + 5 sin ninguna = 8),
  que es una cuenta distinta y ya coherente consigo misma, y el slug es el nombre de archivo real de
  `docs/notas/decisiones/`, no editable sin romper el enlace. Fuera del ownership de N-01 (decisión 3
  específicamente) y no forma parte de la incoherencia señalada.

---

# Ciclo 4 (delta review) — hallazgo N-03

Repair de un solo hallazgo, ceiling de un intento (ADR-0023). Ownership respetado:
`PROYECTO/ai/scripts/feature_state_lib/render_modules.py` (template de scaffold; copia canónico →
`PROYECTO/`, dirección correcta -- `sync-project.sh` no aplica acá, sincroniza en sentido opuesto). Nada
más tocado.

## Tabla hallazgo → cambio → verificación

| # | Severidad | Cambio | Archivo:línea | Verificación |
|---|---|---|---|---|
| N-03 | bajo | `PROYECTO/ai/scripts/feature_state_lib/render_modules.py` conservaba el docstring pre-repair ("the remaining five (...)" listando seis ítems, exactamente el texto que N-01 corrigió en el canónico y en los tres espejos de `Global/*/hooks/`, pero no en el template de scaffold). Copiado el canónico sobre el archivo del template. | `PROYECTO/ai/scripts/feature_state_lib/render_modules.py:1-11` | `cmp` byte-a-byte contra el canónico y contra los tres espejos de `Global/*/hooks/` (comandos abajo); `cmp` de los 16 archivos restantes de `feature_state_lib/` confirma que el resto del directorio ya era byte-idéntico (no tocado). |

## Comando de copia y verificación

```
$ cp ai/scripts/feature_state_lib/render_modules.py PROYECTO/ai/scripts/feature_state_lib/render_modules.py

$ cmp ai/scripts/feature_state_lib/render_modules.py PROYECTO/ai/scripts/feature_state_lib/render_modules.py && echo OK
OK

$ for f in Global/opencode/hooks/feature_state_lib/render_modules.py Global/claude-code/hooks/feature_state_lib/render_modules.py Global/codex/hooks/feature_state_lib/render_modules.py; do
  cmp ai/scripts/feature_state_lib/render_modules.py "$f" && echo "OK: $f"
done
OK: Global/opencode/hooks/feature_state_lib/render_modules.py
OK: Global/claude-code/hooks/feature_state_lib/render_modules.py
OK: Global/codex/hooks/feature_state_lib/render_modules.py
```

## Resto de `feature_state_lib/` re-verificado byte-idéntico (canónico vs. `PROYECTO/`)

```
$ for f in ai/scripts/feature_state_lib/*.py; do
  base=$(basename "$f")
  cmp "$f" "PROYECTO/ai/scripts/feature_state_lib/$base" && echo "OK: $base"
done
OK: candidate_identity.py
OK: cli_integration.py
OK: cli_lifecycle.py
OK: cli_modules.py
OK: cli_repair.py
OK: cli_reporting.py
OK: cli_review.py
OK: graph.py
OK: __init__.py
OK: model.py
OK: parser.py
OK: render_bitacora.py
OK: render_modules.py
OK: render_notes.py
OK: render_status.py
OK: transitions.py
```

## Gates

```
$ python3 -m unittest tests.test_module_docs
Ran 25 tests in 8.258s

OK
```

```
$ python3 -m unittest tests.test_integration_hook
Ran 10 tests in 5.949s

OK
```

```
$ ./build.sh --check
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

```
$ git diff --check
(sin salida -- limpio)
```

`pytest` no está instalado en este entorno (confirmado por la propia asignación, no se corrió).
