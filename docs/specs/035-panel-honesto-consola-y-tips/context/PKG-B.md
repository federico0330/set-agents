# Context pack — PKG-B · La consola partida (refactor comportamiento-preservante)

Spec: `docs/specs/035-panel-honesto-consola-y-tips/spec.md`
(hash `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`).
Aceptación: `acceptance.md` § PKG-B. Tareas: `tasks.md` T-101..T-105.
**ACs:** AC-B.1 … AC-B.8.

**Objetivo.** Cerrar la **segunda** pasada de extracción de `set_agents_app.py` sin que el
CLI público de `set-agents` cambie superficie ni comportamiento observable, con
caracterización **previa** de tres canales y el residuo **enumerado con experimento propio**.
No es trabajo virgen: la primera pasada ya existe y su bloqueo está medido.

## Paths (qué tocar y por qué)

- `ai/scripts/set_agents_app.py` — 4399 líneas (`wc -l`, 2026-08-20). El módulo a
  descargar. `argparse` público en `:4008-4154` (la lista completa de flags por grupo está
  en `spec.md` § Contratos públicos).
- `ai/scripts/routing_cli.py` (277 líneas) y `ai/scripts/vault_ops.py` (455 líneas) — la
  primera pasada, ya extraída. Sus docstrings (`routing_cli.py:1-31`, `vault_ops.py:1-23`)
  enumeran **qué no se pudo mover y por qué**: globals mutables que solo
  `set_agents_app.main()` reasigna (`PROJECT_KEY`, `PROJECT_ROOT`, `ROOT`,
  `ROUTING_WARNINGS`), `app_config`/`write_app_config`, y el helper `_import()`.
  **Ojo (AC-B.6):** son el **formato** de la matriz de T-104, **no** su contenido.
- `tests/test_harness.py:663-684` — `_import()` carga `set_agents_app.py` con
  `spec_from_file_location` **sin** registrarlo en `sys.modules`: un import inverso arranca
  un segundo exec top-level del módulo desde disco. Es **el** techo de la extracción.
- Residuo de routing, enumerable hoy en `set_agents_app.py`: `cmd_route_explain` (`:550`),
  `cmd_routing_report` (`:575`), `cmd_route_doctor` (`:586`), `cmd_route_decide` (`:671`),
  `cmd_route_dispatched` (`:794`), `cmd_route_quota_exhausted` (`:800`),
  `cmd_route_terminal` (`:833`), `cmd_routing_open_runs` (`:866`),
  `cmd_routing_recent_writers` (`:874`), `cmd_routing_decisions` (`:882`),
  `cmd_routing_migrate` (`:3619`).
- Residuo de vault: `cmd_vault_init` (`:2869`), `find_vault` (`:2900`),
  `vault_link_private` (`:2989`), `cmd_vault_doctor` (`:3146`+), `vault_menu`.
  Banners de sección útiles: `vault` (`:2839`), `mcp` (`:2275`), `providers` (`:2590`),
  `tools discovery` (`:1574`), `menu` (`:3479`).
- `ai/scripts/routing_core/` (`__init__`, `catalog`, `domain`, `gates`, `inference`,
  `service`, `store`, `usage`) — **read-only**. Se mueven llamadores, no contratos (AC-B.7).
- `tests/test_routing.py` y `tests/test_harness.py` — la red. Ningún test cambia de color
  (AC-B.8): un test rojo acá **es el defecto**, no la señal de éxito.
- **No hay espejo:** `PROYECTO/ai/scripts/set_agents_app.py` **no existe** (verificado con
  `ls`, error `No such file or directory`). La paridad `ai/scripts` ↔ `PROYECTO/ai/scripts`
  de PKG-A **no aplica** a este paquete; no crear la copia.

## ADRs / invariantes que constriñen

- **DEC-EXTRACT-TWO-OUTCOMES** (`spec.md:158`): dos cierres legales, los dos `pass` —
  (a) el residuo se movió, o (b) se probó anclado **y** se enumeró en la matriz de T-104.
  Lo que **no** cierra: una mudanza parcial que agregue un tercer docstring de "documented
  deviation" sin bajar líneas ni producir la matriz.
- **AC-B.1 es un gate duro**: la caracterización (comando + `stdout` completo + `stderr`
  completo + exit code) existe **antes** del primer movimiento de código, y la lista de
  normalizadores se escribe **antes** de la primera comparación. Un normalizador agregado
  después de ver un diff es el diff escondiéndose: se registra como **finding**.
- **AC-B.2.4 — mutantes y credenciales aislados.** `--vault-init`, `--vault-link`,
  `--scaffold`, `--update`, `--tools-install`, `--mcp-add`/`--mcp-remove`,
  `--provider-add`/`--provider-remove`, `--plugin-on`/`--plugin-off`,
  `--model-pin-set`/`--model-pin-clear`, `--routing-migrate`, `--prune-dead`,
  `--provider-verify`, `--check-update`, `--quota-failover-e2e`, `--fresh-probes` se corren
  en `HOME`/proyecto **temporal desechable**, con `--dry-run` donde exista. Nunca contra el
  árbol real ni contra credenciales vivas. **Ningún valor de secreto se registra** en la
  evidencia: solo presencia o ausencia. Una flag que no se pueda caracterizar sin efecto
  lateral **se declara así** — declararla cumple el criterio, correrla a ciegas no.
- **AC-B.3:** un bug real encontrado al mover se registra como finding y se repara
  **aparte**; no viaja en el diff del refactor.
- **AC-B.5:** la duplicación no crece. Las existentes (`atomic_write`/`_BACKED_UP` en
  `vault_ops.py`; `_MAX_FEATURE_BYTES`/`_MAX_FEATURE_FILES` en `routing_cli.py`) son el
  techo, no una licencia.
- `--route-decide` sigue **prohibido** en Cursor (no-goal 4): se mueven los comandos de
  routing, no se habilitan acá.

## Validación local

```
wc -l ai/scripts/set_agents_app.py            # 4399 antes (2026-08-20); se REPORTA, no es meta
python3 -m unittest tests.test_routing
python3 -m unittest tests.test_harness
python3 -m unittest tests.test_menu_ui tests.test_provider_registry tests.test_module_docs
./build.sh --check
./ai/scripts/verify.sh
```

Más la comparación de los **tres** canales contra la caracterización de T-101, con los
normalizadores que T-101 declaró y **ninguno** nuevo.

## Reviewers / runtime / tests

- `required_reviewers`: **`["package-reviewer", "security-auditor"]`**. `complexity=medium`
  (cinco tareas, varios módulos, contrato público de CLI) → `FULL_REVIEW_PANEL`
  (`model.py:565-575`). El `security-auditor` no es ceremonia: el paquete caracteriza flags
  que **leen credenciales y tocan red** y escribe evidencia en disco — el riesgo concreto es
  filtrar un valor de secreto en la caracterización (AC-B.2.4), más la semántica de vault.
- `runtime_surface`: **false** — waiver declarado. El paquete es, por contrato, **cero**
  comportamiento observable nuevo (AC-B.3, AC-B.8); la prueba de runtime es la comparación
  de tres canales del propio paquete, más fuerte que un pase de `runtime-verifier`, y el
  techo de 8 despachos no deja lugar para uno.
- test owner: **implementer**. Sin `test-writer`. La caracterización de T-101, la lista de
  normalizadores y la matriz de T-104 se escriben en
  `docs/specs/035-panel-honesto-consola-y-tips/evidence/` (convención medida en 034), que es
  `owned_path` del paquete — nunca en `/tmp` ni pegadas en el chat.
- `strict_tdd`: **false**, a propósito. Un ciclo RED→GREEN exige un test que falle primero,
  y acá un test rojo **es el defecto** (AC-B.8). La disciplina equivalente es la
  caracterización previa de AC-B.1, que es un gate duro.
- `selected_role` / `selected_model`: `implementer` / `composer-2.5`. Pin de host Cursor
  (034/ADR-0063), **no** una lane de routing: `--route-decide` sigue prohibido.

## Fuera de alcance (aunque tiente)

Rediseñar `routing_core/` o la semántica de vault (ADR-0012/ADR-0056) · **tocar el
`_import()` de `tests/test_harness.py:663-684`** (si T-102 concluye que hace falta, se
**registra** y el paquete cierra por el camino (b)) · partir `tests/test_harness.py` ·
desinstalar/scaffold de menú (diferido en 034) · habilitar `--route-decide` · arreglar bugs
"de paso" · todo lo de PKG-A (`feature_state_lib`, `feature-state.py`,
`Global/_canonical/agents/orchestrator.md`) y de PKG-C (`TIPS-USO.md`,
`docs/COMO-FUNCIONA.md`).

## Mordida

**No hay tests que deban ponerse rojos** — la mordida de este paquete es asimétrica y hay
que decirlo (AC-B.8). Lo que sí es entregable verificable: la caracterización fechada antes
del primer commit de movimiento, la matriz de T-104 con la columna **experimento o lectura
hecha** (`file:line` propio) en **todas** sus filas, y el `wc -l` reportado. Una fila
justificada citando `routing_cli.py:1-31` o `vault_ops.py:1-23` **no cierra**.
