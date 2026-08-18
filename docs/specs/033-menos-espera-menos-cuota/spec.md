# 033 — Menos espera, menos cuota

> Este spec está escrito para que lo implemente **Cursor**. Cada paquete es autónomo, tiene
> criterios de aceptación verificables y nombra los archivos y líneas donde vive el problema.
> Todo lo que dice acá fue **medido el 2026-08-18**, no recordado. Donde no pude medir, lo digo.

## Contexto

Federico paga USD 20 de OpenAI, USD 40 de Copilot y USD 10 de OpenCode, y aun así el harness se
vuelve inusable a mitad de sesión. Además, la consola tiene tres defectos concretos de uso: el
menú de modelos congela, la lista de modelos es inmanejable, y quedaron tres "lanes" de OpenCode
que existían para cambiar de proveedor a mano cuando se agotaba una cuota — algo que ya no se
hace a mano.

Este spec ataca cuatro cosas separables y una transversal:

1. Colapsar las tres lanes de OpenCode en una sola.
2. Que el menú "Modelos" no congele y que elegir un modelo sea agradable.
3. Cerrar lo que queda roto en Windows.
4. Que los gates se puedan mirar mientras corren.
5. **Transversal:** que las cuotas alcancen, con estrategias medidas y no con fe.

---

## Estado medido (2026-08-18)

### Lo que tarda

| medición | valor | dónde |
|---|---|---|
| `models_config.detect_subscriptions()` | **13.12 s**, sin ningún indicador de progreso | `ai/scripts/setup_models.py:357` |
| `opencode models` | **2.9 s**, **125 modelos** | `ai/scripts/setup_models.py:303-317` |
| primera pantalla útil del menú "Modelos" | **≈16 s de congelamiento** | suma de las dos anteriores |
| `verify.sh` completo | **1237 s** (1286 tests) | `ai/scripts/verify.sh:22` |

Los 125 modelos vienen de cinco proveedores y se muestran en **una sola lista plana ordenada
alfabéticamente**, que mezcla todo:

```
62  opencode/…        28  github-copilot/…     19  opencode-go/…
13  openai/…           3  ollama/…
```

### Lo que se gasta

`ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10`:

| | |
|---|---|
| sesiones (despachos) | **246** en 8 días |
| input | 252.9M |
| output | 14.9M |
| **cache_read** | **5.9G — 92% del total de 6.4G** |

Y del registro propio del harness (`ai/state/features/*.json`, 29 features / 66 paquetes,
158 spawns registrados):

| rol | spawns | |
|---|---|---|
| implementer | 40 | |
| package-reviewer | 33 | |
| repair-agent | 22 | |
| delta-reviewer | 21 | |
| gate-runner | 16 | ← **deterministas: no necesitan modelo** |
| finding-verifier + security-auditor | 12 | |

**Los roles de revisión son 66 de 158 spawns: el 42%.**

Fuente externa consultada el 2026-08-18:
[GitHub — About premium requests](https://docs.github.com/en/copilot/managing-copilot/monitoring-usage-and-entitlements/about-premium-requests)
dice que Copilot cobra **por request, no por token**, que Pro trae **300 premium requests al mes**
y Pro+ **1500**, y que las acciones autónomas dentro de una sesión **no** cuentan aparte.

**De ahí sale el diagnóstico central de este spec:** el harness no gasta de más por prompt —
**multiplica prompts**. Cada spawn despachado por CLI es, para el proveedor, un prompt nuevo
iniciado por el usuario, no una tool call interna. 246 despachos contra un techo de 300 mensuales
explica exactamente "dos prompts míos = un mes de cuota".

### Las tres lanes, y dónde las ve el usuario

`models_config.py:31` → `LANES = ("go-zen", "zen", "openai-only")`.

| superficie | qué muestra hoy |
|---|---|
| `setup_models.py:378` | el picker "Campo" ofrece `opencode.go-zen`, `opencode.zen`, `opencode.openai-only` |
| `setup_models.py:230` | el panel encabeza con `lane: go-zen (auto)` |
| `setup_models.py:275` | la tabla de áreas tiene la columna `OPENCODE[go-zen]` |
| `models.toml` | **38 mapas `opencode = { "go-zen" = …, "zen" = …, "openai-only" = … }`** |
| `active-profile` | archivo en la raíz con la lane activa |
| `build.sh` | `--profile go-zen\|zen\|openai-only` |

Superficie de código a tocar: `models_config.py` (46 referencias), `setup_models.py` (34),
`generate.py` (16), `build.sh` (23), `models.toml` (53), y **7 archivos de test**
(`test_auto_profile.py`, `test_decide_always.py`, `test_harness.py` ×29,
`test_models_wizard_ui.py` ×8, `test_probe_subscriptions.py`, `test_routing.py` ×11,
`test_spawn_materialization.py`).

### Windows, después del arreglo de 032

CI run **32153232496** (`1b7ad41`): `windows-bootstrap` pasó de
`failures=21, errors=82, skipped=361` a **`failures=7, errors=1, skipped=654`**. El probe de
toolchain ahora sí se activa. Lo que queda son ocho casos y **no son todos el mismo problema**:

| # | test | causa medida |
|---|---|---|
| 1-4 | `test_build_check_detects_global_drift_and_names_the_file`, `test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook`, `test_guest_copy_scaffolds_and_verifies_portably`, `test_install_sh_yes_terminates_the_opencode_auth_loop` | llaman `subprocess.run(["bash", …])` **directo**, sin pasar por el helper `run()` que tiene la guarda. En el runner, `bash` resuelve al lanzador de WSL: `Windows Subsystem for Linux has no installed distributions.` |
| 5 | `test_cmd_tools_install_rejects_a_hand_edited_local_catalog_entry_with_a_disallowed_command` | esperaba `TOOL_REJECTED backdoor`, obtuvo `TOOL_UNKNOWN backdoor`. **No es un problema de bash**: el catálogo local hand-editado no se está leyendo. Hay que diagnosticarlo, no saltearlo. |
| 6 | `test_stdin_from_dev_null_exits_2_with_help_never_entering_the_menu` | exit `1` en vez de `2`. |
| 7 | `test_vault_migration_plan_merge_with_nested_dirs_and_zero_collisions` | separadores: `features\replenishment-v2.md` vs `features/replenishment-v2.md`. **Defecto real de portabilidad** en el planificador del vault, o el test debe normalizar. Decidir cuál, con evidencia. |
| 8 | `test_adr_0017_and_0007_amendment_and_superseding_decision_recorded` | ERROR, sin diagnosticar todavía. |

Y **macOS regresó**: `test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout`
falló con `'· verificando proveedores…\n' not found in 'verificando proveedores: listo\n'`. Es un
test dependiente de tiempo de pared: en ese runner el trabajo terminó antes del primer frame del
spinner. **No lo arregles subiendo el sleep** — eso lo vuelve más lento y sigue siendo flaky.

---

## Paquetes

### PKG-1 — `una-sola-lane-opencode`

**Objetivo.** Que exista una sola dimensión OpenCode. El usuario elige un modelo por área, no una
lane por área.

**Qué NO es.** Esto **no** elimina los prefijos de proveedor. `openai/gpt-5.5`,
`opencode/kimi-k2.7-code` y `opencode-go/grok-4.5` siguen existiendo y siguen siendo distintos.
Lo que se elimina es el *preset* que elegía cuál de los tres usar por área.

**Premisa del usuario, y qué se pudo verificar.** Federico dice que el gateway descarta un
proveedor sin cuota y sigue con otro, y que por eso la distinción sobra. Lo que el repo verifica
por sí mismo es parcial: hay clasificación de agotamiento (`routing_core/domain.py:27-52`) y el
store marca el despacho como terminal (`routing_core/store.py:847-897`), y la doctrina manda
relanzar una vez con otro modelo. Pero la feature **011-quota-failover está BLOCKED** y su AC-06
nunca se verificó en vivo. **Conclusión honesta: el failover automático NO está probado.** Por eso
AC-1.6 abajo no es opcional.

- **AC-1.1** `models_config.LANES` desaparece. Cada `opencode = { … }` de `models.toml` (38 mapas)
  pasa a ser un string: `opencode = "openai/gpt-5.5"`. La migración se hace **conservando el valor
  de la lane `go-zen`**, que es la activa hoy (`active-profile`), y cada cambio de valor respecto
  de esa lane queda listado en la evidencia del paquete.
- **AC-1.2** El archivo `active-profile` y el flag `build.sh --profile` desaparecen, junto con
  `auto_profile()` y `detect_subscriptions()`-como-selector-de-lane. `detect_subscriptions()`
  sigue existiendo para el panel de suscripciones (tri-estado), que **no** se toca.
- **AC-1.3** El picker "Campo" (`setup_models.py:378`) ofrece exactamente
  `["claude", "codex", "codex_effort", "opencode"]`. El panel ya no imprime `lane:` y la columna
  pasa a titularse `OPENCODE`.
- **AC-1.4** `[session].opencode_small_model` deja de ser un mapa de tres lanes y pasa a ser un
  string.
- **AC-1.5** Las 18 tablas `[roles.<rol>.tiers.<tier>].opencode` colapsan sin decisión: hoy las
  tres lanes ya llevan **el mismo** modelo a propósito (comentario en `models.toml`), así que la
  migración es mecánica y un test debe **probar** que los tres valores eran idénticos antes de
  colapsar, no asumirlo.
- **AC-1.6** **Un modelo cuyo proveedor está sin cuota no puede fallar en silencio.** Antes de que
  esto se dé por cerrado, tiene que existir una prueba que simule agotamiento del proveedor de un
  área y demuestre **una** de estas dos cosas, la que sea verdad: (a) el router elige otro
  proveedor y lo registra, o (b) el harness falla ruidosamente nombrando el proveedor agotado y la
  acción concreta que el usuario tiene que tomar. Lo que no se acepta es un cuelgue, un stack trace
  crudo, o un fallback silencioso a un modelo que el usuario no eligió.
- **AC-1.7** Ningún test se borra para hacer pasar esto. Los 7 archivos de test que hoy fijan las
  tres lanes se **reescriben** contra la dimensión única, y cada reescritura conserva la propiedad
  que el test original protegía (ver `tests/test_auto_profile.py`, que existe entero para probar la
  detección de lane: si la lane desaparece, ese archivo se elimina **con una nota en el commit que
  diga qué invariante dejó de existir y por qué ya no puede romperse**).

**Riesgo nombrado.** `auto_profile()` era la degradación automática cuando faltaba una suscripción.
Al sacarlo, una máquina sin la suscripción del modelo configurado ya no se "acomoda" sola. Eso es
justamente lo que AC-1.6 tiene que volver visible.

---

### PKG-2 — `el-menu-no-congela`

**Objetivo.** Que "Modelos" pinte algo útil en menos de 300 ms, siempre.

- **AC-2.1** El wizard nunca bloquea antes de su primer render. El panel se dibuja de inmediato con
  lo que ya está en disco, y los datos vivos (suscripciones, modelos) llegan después y **refrescan
  el panel en su lugar**.
- **AC-2.2** Mientras un dato vivo está en vuelo, se ve qué se está esperando y hace cuánto —
  reutilizando `tui.with_progress`, que ya existe y ya se usa en el menú principal
  (`set_agents_app.py:3845`). Nada de un cursor titilando sin explicación durante 13 segundos.
- **AC-2.3** Ambos resultados se cachean en disco con TTL y sello de tiempo, y el panel muestra la
  antigüedad (`suscripciones: hace 4 min`). Hay una tecla para forzar refresco. El TTL arranca en
  10 minutos para suscripciones y 60 para el catálogo de modelos; si alguno resulta corto en uso,
  se ajusta con la medición, no de memoria.
- **AC-2.4** Un probe que falla o expira **degrada visiblemente** ("suscripciones: no se pudo
  medir — mostrando pins") y nunca deja el wizard inutilizable. Hoy `setup_models.py:356-359` se
  come la excepción con un `except Exception` mudo: eso se reemplaza por una degradación con
  nombre.
- **AC-2.5** Prueba de mordida obligatoria: un test que congela el probe 5 segundos y demuestra que
  el primer frame igual salió antes de 300 ms.

---

### PKG-3 — `elegir-modelo-sin-scrollear`

**Objetivo.** Que elegir entre 125 modelos sea una decisión, no una búsqueda del tesoro.

Lo que **ya funciona** y no hay que reinventar: el picker tiene viewport con clamp
(`tui.py:731-745`), tiene modo búsqueda con `/` (`tui.py:797-812`) y tiene texto libre. El problema
no es que falte scroll: es que la lista **no dice nada** sobre lo que muestra.

- **AC-3.1 Agrupada por proveedor.** La lista se rinde con encabezados de sección
  (`opencode-go (19)`, `opencode (62)`, `openai (13)`, `github-copilot (28)`, `ollama (3)`), no
  alfabética global. Los encabezados no son seleccionables: las flechas los saltan.
- **AC-3.2 Contador y posición.** Se ve siempre `‹n› de ‹total›` y, cuando hay filtro activo,
  `‹n› de ‹coincidencias› (de ‹total›)`.
- **AC-3.3 Indicadores de scroll.** `▲`/`▼` cuando hay contenido fuera del viewport arriba o abajo.
  Hoy no hay forma de saber que la lista sigue.
- **AC-3.4 El valor actual, marcado.** El modelo que esa celda tiene hoy aparece marcado (`●`) y el
  cursor arranca **sobre él**, no en el índice 0.
- **AC-3.5 Anotaciones útiles, atenuadas.** Cada fila puede llevar sufijos cortos en `dim()`:
  `free` cuando el id termina en `-free`, y el rol/área que ya lo usa (`← implementer`), para que se
  vea de un golpe qué está en uso.
- **AC-3.6 Búsqueda al tipear.** Escribir una letra entra en modo búsqueda directamente, sin
  requerir `/` primero. `/` sigue funcionando (contrato viejo intacto), y Esc sigue volviendo.
- **AC-3.7 Sin parpadeo.** `tui.py:818` hace `\x1b[H\x1b[2J` — borra la pantalla entera en **cada**
  pulsación, y eso es el parpadeo. Reemplazar por reposicionar + borrar-hasta-el-final
  (`\x1b[H\x1b[J`) o, mejor, redibujar sólo las filas que cambiaron. El test de esto es de bytes:
  que la secuencia de borrado total no aparezca más en el camino de redibujo.
- **AC-3.8** Todo lo anterior tiene que seguir siendo **puro y testeable sin TTY**: `tui.py` ya
  separa el reductor del render, y `test_menu_ui.py` / `test_models_wizard_ui.py` ya prueban contra
  streams falsos. Ninguna capacidad nueva puede depender de tener terminal de verdad.

---

### PKG-4 — `windows-sin-mentiras`

**Objetivo.** `windows-bootstrap` verde, sin que "verde" signifique "no probamos nada".

- **AC-4.1** Los cuatro tests que llaman `subprocess.run(["bash", …])` directo pasan a usar el
  helper `run()` de `tests/test_harness.py` (que ya tiene la guarda) o llaman
  `tests.require_posix_toolchain()` ellos mismos. **No se toca el probe**: `bash` resolviendo al
  lanzador de WSL sin distro es exactamente el caso que el probe ya detecta bien.
- **AC-4.2** Los casos 5, 6, 7 y 8 se **diagnostican uno por uno** y cada uno recibe la respuesta
  que corresponda: arreglo de portabilidad si el defecto es del harness, o salto con razón nombrada
  si de verdad es una capacidad ausente en Windows. **Ningún salto sin la razón medida escrita en
  el código.** El caso 7 (separadores `\` vs `/`) huele a defecto real del planificador del vault,
  no a limitación de la plataforma: si lo es, se arregla, no se saltea.
- **AC-4.3** El número de skips en `windows-bootstrap` se imprime y **se fija con un techo** en el
  propio job: si los skips suben sin que un commit lo declare, el job falla. Un salto es aceptable;
  un salto que crece solo, no. Hoy son 654 de 1276.
- **AC-4.4** macOS: `test_slow_liveness_reports_stderr_progress_without_changing_provider_stdout` se
  vuelve determinista inyectando el reloj o el stream en vez de depender del tiempo de pared. Subir
  el `sleep` no se acepta como arreglo.
- **AC-4.5** Los tres jobs verdes en una misma corrida, y el SHA de esa corrida citado en la
  evidencia del paquete.

---

### PKG-5 — `el-gate-se-ve`

**Objetivo.** Que 20 minutos de gate sean mirables, y que una falla se encuentre sin scrollear.

`ai/scripts/verify.sh:22` corre `python3 -m unittest discover -s tests -v`: 1286 tests, 1237 s,
verbose, sin progreso agregado, sin resumen, y las fallas quedan enterradas entre miles de líneas.

- **AC-5.1** Salida en vivo de una sola línea que se reescribe: `‹hechos›/‹total› · ‹elapsed› ·
  ETA ‹estimado› · ✗‹fallas›`. La ETA sale del ritmo real medido, no de una constante.
- **AC-5.2** Un test que falla imprime **su bloque completo apenas falla**, no al final. Hoy hay que
  esperar los 20 minutos para saber qué se rompió.
- **AC-5.3** Bloque final único y copiable: total, fallas con nombre completo, skips agrupados por
  razón, y **los 10 tests más lentos con su tiempo** — sin eso no hay forma de saber dónde se van
  los 1237 s.
- **AC-5.4** El modo verbose completo sigue disponible detrás de una variable de entorno; el default
  es el resumen. Nada de perder información: cambiar dónde vive.
- **AC-5.5** Ni un solo test se salta, se afloja ni se marca xfail para que el gate se vea mejor.
  Esto es un cambio de **presentación**, y un test debe probar que el conjunto de tests ejecutados
  es idéntico antes y después.
- **AC-5.6** *(opcional, sólo si se puede medir)* Paralelizar por shards. Antes de intentarlo hay
  que demostrar que el aislamiento aguanta: `tests/__init__.py` instala un sandbox de escritura y
  un boundary de subprocesos, y ADR-0051 existe por aislamiento de tests. Si la paralelización no
  puede probar aislamiento, **no se hace** — 20 minutos legibles valen más que 5 minutos mentirosos.

---

### PKG-6 — `cuotas-que-alcanzan`

**Objetivo.** Bajar despachos y contexto por paquete sin bajar calidad. Cada punto acá es
implementable y medible; las ideas que quedan en consejo están en la sección siguiente.

- **AC-6.1 El context pack deja de ser opcional.** El prompt del implementer ya dice "leelo PRIMERO
  si existe" (`Global/_canonical/agents/implementer.md`) — pero *si existe*. Sin él, cada spawn
  re-explora el repo desde cero, y eso es el 92% de `cache_read` medido. Un paquete no puede entrar
  en `PACKAGE_IMPLEMENTATION` sin `docs/specs/<feature>/context/<PKG>.md`, con la misma guarda de
  fase que ya usan los demás requisitos del state machine.
- **AC-6.2 Los gates deterministas no gastan modelo.** `gate-runner` acumuló 16 spawns. Cuando
  todos los comandos del gate están en la allowlist P001, el trabajo lo hace `local-gate-runner`
  (sin modelo). El state machine rechaza un spawn de `gate-runner` cuyos comandos son todos P001,
  nombrando el rol correcto.
- **AC-6.3 El panel de revisión escala con el riesgo.** Los roles de revisión son el 42% de los
  spawns. Un paquete `complexity=small` y `risk=low` cierra con **un** revisor; el panel completo
  queda para `medium`/`high`. La regla vive en el state machine y queda registrada en la evidencia
  del paquete, no en el criterio del orquestador del día.
- **AC-6.4 Presupuesto de despachos visible mientras se consume.** El techo ya existe y ya se
  valida (`feature_state_lib/model.py:108-113`, `MODE_BUDGETS`), pero sólo aparece cuando **ya se
  pasó**: `validate_state` lo rechaza después del hecho. El estado del paquete tiene que exponer
  `spawns usados / techo del modo` en `status` y en la narración, y avisar al 80%, para que el
  modo se pueda corregir antes de chocar y no después.
- **AC-6.5 El registro propio deja de mentir por omisión.** `cost-report.py` mide 246 sesiones en
  la Sección 1 (los stores nativos de cada CLI) y **cero** en la Sección 2 (el registro del propio
  harness). O sea: el harness no está registrando lo que despacha. Se puede optimizar lo que se
  mide; hoy no se mide. Cerrar esa brecha es requisito de todo lo demás de este paquete.
- **AC-6.6 Ningún ahorro puede tocar la separación de deberes.** Reducir el panel no habilita que
  el implementer se apruebe solo, ni que el revisor parchee. Un test tiene que fijarlo.

---

## Estrategias de cuota (consejo medido, no todo es código)

Ordenadas por relación ahorro/riesgo. Las tres primeras son las que mueven la aguja.

1. **Usar Cursor como anfitrión para el trabajo de paquete.** En Cursor la delegación es por
   subagentes nativos **dentro de la misma sesión**: un prompt tuyo sigue siendo un prompt del
   proveedor, en vez de convertirse en doce. Esto es lo que ya quedó instalado en la feature 032, y
   es el cambio de mayor impacto disponible hoy sin tocar código.
2. **Escribir el context pack antes de implementar, siempre.** 5.9G de `cache_read` sobre 252.9M de
   input real significa que los spawns releen contexto en vez de recibirlo. Un context pack que
   nombra archivos, contratos y comandos de validación reemplaza una exploración entera por spawn.
3. **Elegir el modo por tamaño real del trabajo.** `feature-state.py init --mode` acepta
   `feature`, `scoped`, `incident` y `quick-fix`, y cada uno trae su propio techo de despachos
   por paquete (`ai/scripts/feature_state_lib/model.py:108-113`):

   | modo | spawns/paquete | ciclos de review |
   |---|---|---|
   | `feature` | 12 | 2 |
   | `scoped` | 8 | 2 |
   | `incident` | 6 | 1 |
   | `quick-fix` | 4 | 1 |

   Hoy casi todo entra como `feature`. Un arreglo de tres líneas en modo `feature` habilita el
   triple de despachos que en `quick-fix`, y el techo habilitado es el que se termina usando.
4. **Usar las variantes `@fast` para trabajo mecánico.** Ya existen `<rol>@fast`, `@balanced` y
   `@frontier` emitidas para OpenCode. Renombrar un símbolo o propagar un cambio mecánico no
   necesita el modelo frontier.
5. **No correr el gate completo por tarea.** 1237 s por corrida. Validación local focalizada por
   tarea, gate completo una vez al cierre del paquete — que es lo que la doctrina ya dice y lo que
   en la práctica no siempre se respeta.
6. **Consolidar reparaciones.** `repair-agent` acumuló 22 spawns contra 40 del implementer. La
   doctrina ya manda consolidar hallazgos en **una** reparación por ciclo; el número sugiere que se
   está reparando de a poco. Vale medirlo antes de cambiar nada.
7. **Ordenar los spawns para que el caché pegue.** Spawns consecutivos del mismo rol sobre el mismo
   contexto reutilizan el prompt cacheado; alternar roles lo tira. Es un cambio de orden, no de
   contenido.
8. **Cuidado con el techo por request.** Con Copilot Pro son 300 requests al mes: **10 por día**.
   Un paquete completo del harness, con panel de revisión, se los come en una sesión. Si Copilot va
   a ser la lane de trabajo, hay que bajar despachos por paquete o subir a Pro+ (1500); no hay una
   tercera opción, y decirlo es más útil que optimizar alrededor.

**Lo que NO recomiendo**, para que quede escrito: bajar `max_deep_review_cycles`, sacar el
finding-verifier, o dejar que el implementer apruebe su propio trabajo. Son los ahorros más
tentadores y los únicos que cambian la calidad en vez del costo.

---

## No-goals

- No se toca el contrato de datos del estado (`ai/state/features/*.json`).
- No se agrega un runtime nuevo ni se toca el target `cursor` de la feature 032.
- No se implementa soporte nativo de Windows como runtime: sigue vigente la decisión
  `docs/notas/decisiones/2026-08-18 windows-nativo-es-bootstrap-no-runtime.md`.
- No se cambia el modelo de permisos ni las guardas de comandos.

## Riesgos

| riesgo | mitigación |
|---|---|
| PKG-1 saca la degradación automática por suscripción faltante | AC-1.6: el fallo tiene que ser ruidoso y nombrado |
| PKG-1 toca 7 archivos de test | AC-1.7: reescribir conservando el invariante, y justificar por escrito cualquier eliminación |
| PKG-3 cambia `tui.py`, que tiene contrato fijado por dos suites | AC-3.8: reductor puro, tests sin TTY, contrato viejo de `/` intacto |
| PKG-5 puede degenerar en "el gate se ve mejor porque prueba menos" | AC-5.5: mismo conjunto de tests ejecutados, probado |
| PKG-6 puede degenerar en "ahorramos sacando revisión" | AC-6.6: la separación de deberes es intocable |

## Gates

Cada paquete cierra con: `./build.sh --check` en verde, `ai/scripts/verify.sh` completo en verde,
`git diff --check` limpio, y **prueba de mordida ejecutada para cada test nuevo** — romper la
implementación, ver el test en rojo, restaurar, verlo en verde. Un test que nunca se vio rojo no
prueba nada.

## Criterio de cierre

Los seis paquetes aceptados con revisión independiente, los tres jobs de CI verdes en una misma
corrida, y una medición posterior de `cost-report.py` sobre un paquete real completo que se pueda
comparar contra los 246 despachos / 6.4G de la línea base de este spec.
