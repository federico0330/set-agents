# ADR-0066 — El cargador del golden suite es el techo de extracción de `set_agents_app.py`

- Estado: **Accepted** (2026-08-20). Feature `035-panel-honesto-consola-y-tips`, PKG-B.
  Aprobado con el Feature Contract (hash
  `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`), DEC-EXTRACT-TWO-OUTCOMES
  (`spec.md:158`), AC-B.4 y AC-B.6. Resuelve las assumptions 6, 7 y 9 (`spec.md:553-569`).
- **Decisión de arquitectura, no bugfix ni refactor.** No cambia una sola línea de
  comportamiento observable: fija **dónde está el techo** de la extracción de
  `ai/scripts/set_agents_app.py` (4399 líneas, `wc -l` 2026-08-20), **por qué** está ahí, y
  **qué haría falta** para moverlo. Diseño completo: `docs/specs/035-panel-honesto-consola-y-tips/design.md` § 11.
- **Corrige una razón técnica falsa** que hoy repiten el propio criterio de aceptación
  (`docs/specs/035-panel-honesto-consola-y-tips/acceptance.md:458-461`) y tres docstrings de
  producción (`ai/scripts/vault_ops.py:13-17`, `ai/scripts/project_identity.py:11-13`,
  `ai/scripts/routing_cli.py:14`). La conclusión de esos docstrings sigue siendo correcta; el
  mecanismo que nombran, no.
- No enmienda ni supersede ningún ADR previo. ADR-0012/ADR-0056 (semántica de vault) y
  `ai/scripts/routing_core/` quedan intactos: se discuten llamadores, nunca contratos (AC-B.7).
- **Ejes store / API Gateway / deploy: n/a.** Ya registrados como `n/a` en el `axes_log` de la
  feature (`spec.md:13-15`). Cero persistencia nueva, cero superficie de red nueva, cero cambio
  de despliegue. No se difiere ninguno con umbral: no existen en este paquete.

## Contexto

`set_agents_app.py` ya pasó por una primera pasada de extracción: `routing_cli.py` (277
líneas) y `vault_ops.py` (455) existen y funcionan. Sus docstrings enumeran qué **no** se pudo
mover, y atribuyen el bloqueo a que el helper `_import()` del golden suite carga el módulo
"sin registrarlo en `sys.modules`", de modo que un import inverso arrancaría un segundo exec
top-level del archivo.

Esa afirmación **quedó desactualizada**. El helper vigente es
`tests/test_harness.py:745-797` y hace lo contrario: registra `sys.modules[name] = module`
(`:789`) **antes** de `spec.loader.exec_module(module)` (`:791`). Es precisamente por eso que
el `sys.modules.setdefault("set_agents_app", sys.modules[__name__])` de
`set_agents_app.py:33` no explota — razón escrita en el comentario del propio helper
(`:749-759`).

El techo real es el `finally` (`:792-796`): al salir, el helper **restaura** el estado previo
de `sys.modules` — saca el nombre si estaba ausente (sentinela `_SYS_MODULES_ABSENT`,
`tests/test_harness.py:40`), lo repone si estaba presente, y distingue el tercer estado
(`None` explícito). Y ese comportamiento **es un contrato afirmado por un test**:
`test_import_helper_leaves_sys_modules_exactly_as_it_found_it`
(`tests/test_harness.py:12275-12335`) lo asegura en los tres estados previos posibles
(`:12298-12299`, `:12309-12310`, `:12327-12330`), con un test de regresión por subproceso al
lado (`:12266-12273`). El historial de `:12280-12289` documenta qué se rompió cuando una
primera versión dejó el módulo registrado: los `test_resolve_context_pack_*` de
`tests/test_routing.py` empezaron a resolver contra el `ROOT` real en vez del temp de cada test.

## Decisión

**1. El cargador del golden suite es una restricción arquitectónica de primera clase sobre el
grafo de módulos de producción.** Después de que `_import` retorna,
`sys.modules["set_agents_app"]` **no** es el objeto que el test tiene en la mano. Hay **139**
call sites de `self._import("set_agents_app")` y **35** targets distintos de
`patch.object(app, "…")`. Por lo tanto: una función que se muda fuera de `set_agents_app.py`
pierde la identidad de `__globals__` con el objeto que el test parchea. Re-exportar no
arregla nada — `from routing_cli import (…)` (`:621`) y `from vault_ops import (…)` (`:2851`)
mantienen `app.<nombre>` resoluble; lo que se rompe es el `__globals__`, no el nombre.

**2. El techo se mide en dos familias, no en una regla vaga.**

- **Vault, anclado por el parche de test.** `cmd_vault_doctor` (`:3192`) llega a `STATE_DIR`
  por `_vault_doctor_marker_path` (`:3160-3162`), y siete tests parchean `app.STATE_DIR`
  (`tests/test_harness.py:4577`, `:4638`, `:4662`, `:4678`, `:4691`, `:4711`, `:5207`).
  `vault_menu` (`:3339`) llama `cmd_vault_init`/`cmd_vault_link` por nombre global, y cinco
  tests los parchean (`:3702-3703`, `:3717-3718`, `:3733-3734`, `:3749-3750`, `:3768`).
  Mudar `vault_menu` pone rojos `:3720`, `:3736` y `:3752`, y —peor— deja **verde en falso**
  el `assert_not_called()` de `:3705-3706` mientras el `cmd_vault_init` real se ejecuta. Un
  verde en falso sobre un comando mutante es peor resultado que un rojo.
- **Routing, anclado por el global mutable.** `PROJECT_ROOT`, `PROJECT_KEY` y
  `ROUTING_WARNINGS` se reasignan en **un solo** sitio del repo: el `global` de `main()`
  (`set_agents_app.py:4241`). `_routing_store()` (`:68-73`) lee `PROJECT_KEY`,
  `_routing_output()` (`:524-527`) lee `ROUTING_WARNINGS`, `_project_root_or_harness()`
  (`:92-95`) lee `PROJECT_ROOT`/`ROOT`. `tests/test_routing.py` parchea `ROOT`/`PROJECT_ROOT`
  por asignación directa sobre el módulo canónico (`:3337-3338`, `:3688`, `:3715`, `:3750`) y
  `STATE_DIR`/`APP_CONFIG` con `patch.object` (`:6314-6316`). `_routing_output` **sí** se
  ejercita bajo `_import` (`tests/test_harness.py:5480-5494`, con
  `patch.object(app, "_term_width")` en `:5493`; `_term_width` vive en `:3726`). Y un tercer
  sitio que el context pack no nombraba: `tests/test_menu_ui.py` parchea
  `app.ROUTING_WARNINGS` (`:241`) y llama `app.cmd_route_doctor(human=human)` in-process
  (`:246`) sobre un `import set_agents_app as app` plano (`:22`) — ese archivo **tampoco**
  está en `owned_paths`, así que es read-only para PKG-B.
- **Asimetría que decide el caso más riesgoso:** `PROJECT_KEY` **no tiene ni un sitio de
  parche en todo `tests/`** (medido). Se setea solo en `main()`. Los nueve comandos que llegan
  a `_routing_store()` son por eso el residuo **más** peligroso de mover, no el más libre: una
  mudanza que les rompa la resolución no tiene test que la ponga roja — se descubriría en
  producción, contra el store equivocado.

**3. Arreglar el helper queda fuera de este slice, y por eso el cierre es el (b) de
DEC-EXTRACT-TWO-OUTCOMES.** Las tres formas de arreglarlo chocan con una regla del paquete:
dejar el módulo registrado (el patrón de `TuiTests._import`, `:13918-13933`) pone en rojo las
tres aserciones de `:12275-12335` y reintroduce la regresión de `tests/test_routing.py`
(AC-B.8: un test rojo es el defecto); reescribir los doce sitios de parche cambia qué afirma
el golden suite en un archivo que no está en `owned_paths`
(`docs/notas/features/035-panel-honesto-consola-y-tips/PKG-B.md:10`, y la excepción vigente es
explícita en `docs/notas/decisiones/2026-08-20 035-pkg-b-owned-exceptions-uncommitted-a.md:13`);
inyectar una referencia al módulo en tiempo de exec es un seam de producción nuevo, o sea
comportamiento observable nuevo (AC-B.3). Se **registra** y el paquete cierra enumerando.

**4. Cero módulos nuevos en este slice.** Los dos destinos posibles ya existen
(`routing_cli.py`, `vault_ops.py`, ambos en `owned_paths`). Un archivo nuevo bajo
`ai/scripts/` además entraría a dos gates que hoy no lo miran: el `py_compile` de
`ai/scripts/*.py` (`ai/scripts/verify.sh:24`) y el guardián de encoding sobre
`(ROOT / "ai/scripts").rglob("*.py")` (`tests/test_harness.py:11677-11689`).

**5. La caracterización de tres canales vive en un runner propio del paquete, bajo
`evidence/`, no en el golden suite.** `docs/specs/035-panel-honesto-consola-y-tips/evidence/PKG-B-characterization/`,
con `stdout`/`stderr`/exit en archivos separados y la lista de normalizadores cerrada **por
construcción** (una función nombrada ⇔ una fila en `NORMALIZERS.md`; sin la biyección el
runner se niega a comparar). El golden suite queda descartado por una razón medida, no de
gusto: `tests/__init__.py` instala un audit hook process-wide que rechaza escrituras fuera de
su sandbox (`:271-284`, `:362`) y reemplaza `subprocess.Popen` por una frontera bwrap
(`:119-167`, `:195`) — una caracterización corrida ahí mide el CLI **bajo ese runtime**, no el
CLI; y AC-B.2.4 exige flags que tocan red y credenciales, que volverían el suite no hermético.

**6. El umbral que movería el techo, escrito ahora para que no se re-derive.** Un slice propio
con `tests/test_harness.py` en `owned_paths` y ACs que cubran (i) la semántica nueva de
`_import`, (ii) la reescritura de los doce sitios de parche al módulo dueño, y (iii) la
conservación de las tres aserciones de `:12275-12335` o su reemplazo argumentado.

## Consecuencias

- **PKG-B entrega dos activos durables en vez de líneas movidas:** la matriz
  comando→dependencia→experimento→resultado (16 filas, AC-B.6) y la caracterización previa de
  tres canales con su lista de normalizadores sellada. El slice del umbral (punto 6) los
  hereda gratis.
- **La lista de normalizadores se vuelve verificable, y eso es un efecto del cierre (b).** Como
  no se mueve código, `baseline/` y `after/` corren contra el mismo árbol y el mismo binario:
  todo diff que aparezca es, por definición, ruido corrida-a-corrida, la única cosa que
  AC-B.2.3 acepta normalizar. Bajo el cierre (a) no se puede separar el ruido de "la mudanza
  cambió algo".
- **`wc -l ai/scripts/set_agents_app.py`:** T-105 reportó **4399** antes del movimiento (path (b), sin extracción). El repair F005 borró la copia sombra AST-idéntica de `vault_link_private` (−59 líneas); el archivo queda en **4340** (`wc -l` 2026-08-21). Eso no es cumplir una meta de conteo borrando comentarios — AC-B.6 solo pide reportar el número — y **no** cambia el cierre (b): cero comandos movidos.
- **Costo aceptado:** el módulo grande sigue grande, y el harness sigue teniendo un archivo de
  **4340** líneas. Se paga a cambio de no romper doce aserciones del golden suite ni introducir un
  verde en falso sobre un comando mutante.
- **Deuda nombrada, no silenciada:** `ai/scripts/project_identity.py:11-13` conserva la razón
  desactualizada porque el archivo está fuera de `owned_paths` de PKG-B. Queda como finding.

## Opciones rechazadas

| opción | por qué no |
|---|---|
| Dejar el módulo registrado al salir de `_import` (patrón `TuiTests._import`, `:13918-13933`) | pone en rojo las tres aserciones de `tests/test_harness.py:12275-12335` y reintroduce la regresión de `tests/test_routing.py` documentada en `:12280-12289`. AC-B.8: un test rojo es el defecto |
| Mudar los comandos y agregar un `import set_agents_app` lazy de vuelta | invierte la dirección de la dependencia (el módulo extraído importaría al monolito en tiempo de llamada) y es el "tercer docstring de documented deviation" que AC-B.6 nombra como **no** cierre |
| Re-exportar el comando mudado desde `set_agents_app.py` | mantiene el nombre resoluble y **no** arregla nada: lo que el test parchea es el `__globals__`, no el nombre |
| Reescribir los doce sitios de parche para que apunten al módulo dueño | cambia qué afirma el golden suite, en un archivo fuera de `owned_paths`; es el slice del punto 6, con sus propios ACs |
| Un módulo nuevo (`routing_lifecycle.py`, `vault_doctor.py`) | no hay residuo que alojar bajo el cierre (b), y los dos destinos posibles ya existen y ya están en `owned_paths` |
| Caracterizar extendiendo `tests/test_routing.py` | el suite corre con audit hook y `Popen` reemplazado (`tests/__init__.py:195`, `:362`): mediría el CLI bajo un runtime modificado. Y las flags de red/credenciales de AC-B.2.4 lo volverían no hermético |
| Capturar archivos y compararlos a mano | los normalizadores se aplicarían a ojo, que es exactamente el modo de falla que AC-B.2.3 convierte en finding |
| Bajar el `--complexity` de PKG-B para esquivar el panel | no-goal del harness; y no es el problema: el techo es técnico, no de ceremonia |
