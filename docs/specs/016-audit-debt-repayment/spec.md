# Feature 016 — audit-debt-repayment, contract 1.1.0

Status: `SPEC_DRAFT v2` — amendment pass after `SPEC_CHALLENGE` round 1 against contract 1.0.0 (verdict
`approve-with-amendments`, 8 findings, no user decisions required). See `## Historial de challenge` at the
end of this file for the full disposition table.

## Origen

Este contrato repara una parte de la deuda registrada explícitamente en
`docs/notas/decisiones/2026-07-28 audit-debt-006-p2.md` (hallazgos PR-06..PR-11 de la auditoría final de
`006-execution-graph`/`P2`, dejados sin reparar a propósito) más dos hallazgos menores registrados por separado:
el bloque "Deuda registrada, sin paquete" de `docs/notas/BUENOS-DIAS.md` §5 (paths absolutos y nombres de
módulos de negocio de un cliente en `Global/_canonical/opencode-agents/package-gate-runner.md`) y
`docs/notas/decisiones/2026-08-01 redirect-de-effective-runtime-es-silencioso-sin-reason-code.md` (el redirect
de `_effective_runtime` en `015-anthropic-dispatch-parity` no deja rastro de auditoría).

**Alcance decidido por el usuario (2026-08-02):** de los 6 hallazgos de la deuda de 006, entran PR-07, PR-08 y
PR-09. PR-06 (doble contador de budget), PR-10 (forma del test suite) y PR-11 (mutate sin compare-and-swap)
quedan explícitamente fuera — PR-11 en particular se difiere a un paquete propio futuro por ser la única
invariante de atomicidad del arnés. Se agregan dos ítems de limpieza menor (P2 de este contrato, no confundir
con el "P2" de la auditoría de 006): el archivo de permisos muerto y el reason_code del redirect.

## Objetivo

Cerrar, sin reabrir alcance, la deuda de arquitectura priorizada por el usuario sobre `ai/scripts/feature-state.py`
(PR-07, PR-08, PR-09) y dos ítems de higiene documental/observabilidad de bajo riesgo (limpieza de
`package-gate-runner.md`, reason_code del redirect en `service.py`) — sin cambiar ningún comportamiento externo
observable de `feature-state.py` ni de `routing_core.service.route()` salvo el agregado explícito de un código de
razón no bloqueante.

## Alcance

**Nota de ownership (amendment 1.1.0, hallazgo F-01):** `PROYECTO/ai/scripts/feature-state.py` es un gemelo
byte-idéntico de `ai/scripts/feature-state.py`, verificado (`./build.sh --check`, función que compara ambos
archivos y emite `SELF_SCAFFOLD_DRIFT file=... reason=differs` si divergen, `SELF_SCAFFOLD_SYNC_OK files=2` si
coinciden). Todo cambio de PR-07/PR-08/PR-09 sobre `ai/scripts/feature-state.py` se replica idéntico en
`PROYECTO/ai/scripts/feature-state.py` — no son dos ediciones independientes, es un solo cambio de contenido
aplicado a los dos paths nombrados; el paquete que implemente P1 posee (owns) ambos.

### P1 — deuda priorizada de `ai/scripts/feature-state.py` (PR-07, PR-08, PR-09)

**PR-07 — `repair_entry` autoritativo, con fallback de compatibilidad.**
`_repair_entered_from_review` (`ai/scripts/feature-state.py:2701-2719`) hoy INFIERE si un paquete entró a
`PACKAGE_REPAIR` desde revisión recorriendo `data["history"]` hacia atrás y comparando `event.get("event")`
contra el conjunto `{"record-review", "finalize-review-panel", "record-delta-review"}` — una lista de nombres de
evento que ya se desincronizó dos veces (ver ADR-0009 D8 y D8 corregido/DR-02). Los 5 sitios de asignación de una
línea que fijan `data["phase"] = "PACKAGE_REPAIR"` son: `cmd_record_review` (`:2315`), la rama `verdict ==
"repair_required"` de `cmd_finalize_review_panel` (`:2472`), `cmd_record_delta_review` (`:3078`),
`cmd_record_testing` con `args.status == "fail"` (`:3118`) y `cmd_record_runtime_qa` con `args.status == "fail"`
(`:3149`).

### P2 — higiene de bajo riesgo, fuera de la deuda de 006

**Limpieza de `package-gate-runner.md`.** `Global/_canonical/opencode-agents/package-gate-runner.md` es una
plantilla de subagente que hoy contiene, cableados en `permission.read`/`permission.edit`/
`permission.external_directory`/`permission.bash`, paths absolutos de una máquina concreta
(`/home/federico/iey/iey-ai/...`) y nombres de módulos de negocio de un proyecto cliente
(`contabilium-ingestion`, `replenishment-v2`, `RPL-P0A`). El archivo se copia a cada máquina que instala el
arnés (repo privado, pero portado); esas entradas de permiso son código muerto en cualquier máquina que no sea
la que originó ese paquete puntual.

**Reason_code del redirect silencioso.** `RoutingService._effective_runtime` (`ai/scripts/routing_core/service.py:133-159`)
puede devolver un runtime distinto del solicitado (`redirect`) cuando el par `(runtime, provider)` pedido no
tiene entrada de inventario. Hoy ese redirect nunca se refleja en `RouteDecision.reasons`. **Corrección
1.1.0 (hallazgo F-08):** la afirmación original de que "la decisión exitosa siempre construye `reasons=()`"
es imprecisa — la rama writer durable (`service.py:297`, `execution_enabled=True`) sí construye siempre
`reasons=()` hoy, pero la rama review/simulate (`service.py:251-257`, `execution_enabled=False` en esa rama)
ya construye `reasons=("REVIEW_IDENTITY_UNVERIFIED",)` cuando el reviewer es `unverified`, precedente
favorable de que `RouteDecision.reasons` ya transporta un código no bloqueante junto a una selección
exitosa de candidato en ese mismo objeto. Lo que sigue siendo cierto, y es el gap real que PR-09/AC-09 cierra:
ninguna rama hoy expone el hecho de que `_effective_runtime` sustituyó el runtime pedido — ni la writer
(`reasons=()` fijo) ni la review/simulate (su único código hoy es `REVIEW_IDENTITY_UNVERIFIED`, no relacionado
con el redirect) — así que el rastro de auditoría solo muestra el runtime final, nunca el hecho de que hubo
una sustitución.

Se establece que cada requisito autoritativo sobre `package["repair_entry"]` se escribe en el mismo assignment
de una línea que ya fija `data["phase"] = "PACKAGE_REPAIR"` en esos 5 sitios, con el valor `"review"` en los dos
primeros (record-review, finalize-review-panel) y `"delta_review"` en el tercero (record-delta-review) — los
tres casos que hoy califican como "entrada desde revisión" — y `"testing"` / `"runtime_qa"` respectivamente en
los dos últimos, que hoy NO califican. `_repair_entered_from_review` pasa a leer
`package.get("repair_entry") in {"review", "delta_review"}` cuando el campo está presente. Cuando el campo está
AUSENTE — todo estado de features grabado antes de este contrato, dato verificado: `ai/state/features/*.json`
existentes no tienen la clave `repair_entry` en ningún paquete, `grep -rl repair_entry ai/state/features/` no
devuelve nada hoy — la función cae al mecanismo de inferencia por log exactamente como existe hoy, sin cambio de
comportamiento para ningún estado ya grabado. `repair_entry` es un campo de bookkeeping de ciclo, análogo en
disciplina a `VERIFICATION_AXIS`: se fija en la entrada a `PACKAGE_REPAIR` y no necesita limpieza explícita
porque el próximo `record-review`/`record-delta-review`/etc. que reintroduzca al paquete en `PACKAGE_REPAIR`
lo vuelve a escribir.

**Amendment 1.1.0 (hallazgo F-03) — `cmd_transition` es un sexto sitio de entrada a `PACKAGE_REPAIR`, sin
escritura de `repair_entry`.** `cmd_transition` (`ai/scripts/feature-state.py:2005`) permite, vía
`LEGAL_TRANSITIONS`, una transición directa a `PACKAGE_REPAIR` desde `PACKAGE_REVIEW`, `DELTA_REVIEW`,
`PACKAGE_TESTING` o `PACKAGE_RUNTIME_QA` (operador manual, no uno de los 5 comandos de dominio nombrados
arriba) sin pasar por ninguno de los 5 sitios de asignación de una línea. Sin corrección, esta sexta vía deja
`package["repair_entry"]` con el valor STALE de la entrada anterior (o ausente, si nunca se fijó) — un valor
viejo invertiría la lectura de `_repair_entered_from_review` respecto de la entrada real que se acaba de
producir. Se establece que `cmd_transition`, en la rama que fija `data["phase"] = "PACKAGE_REPAIR"`, hace
`package.pop("repair_entry", None)` (nunca escribe un valor nuevo, porque un transition manual no tiene un
"desde revisión/delta/testing/runtime QA" autoritativo propio) — de forma que `_repair_entered_from_review`,
al no encontrar la clave, cae al mecanismo de inferencia por log exactamente como hoy: comportamiento
byte-idéntico al actual para esta vía, y ya no arrastra un valor stale de una entrada previa a `PACKAGE_REPAIR`
del mismo paquete. Un test nuevo cubre esto: paquete con `repair_entry` fijado por una entrada anterior,
`cmd_transition` lo mueve manualmente a `PACKAGE_REPAIR` de nuevo, se confirma que la clave queda ausente
después y que `_repair_entered_from_review` cae a inferencia.

**Amendment 1.1.0 (hallazgo F-08, nota de universo) — `ai/scripts/feature-state.py:3389`.** El bloque de
auto-demostración `dry-run` del propio arnés (ejercitado por `--dry-run`/self-test, no por un comando de CLI
real) fija `data["phase"] = "PACKAGE_REPAIR"` directamente sin pasar por ninguno de los 5 sitios ni por
`cmd_transition`. Este es un sexto sitio de asignación en el código fuente, pero está explícitamente FUERA del
universo de AC-01/AC-02: es un fixture de demostración que construye un objeto `data` sintético desde cero
dentro de la misma función que lo consume, nunca pasa por un comando real ni por `_repair_entered_from_review`
en un contexto donde el valor de `repair_entry` importe. Se nombra aquí para que el conteo de AC-01 no se
malinterprete como "6 sitios en el código, 5 en el contrato" — son 5 sitios de comando más 1 sitio de
`cmd_transition` (pop, sin escritura) más 1 sitio de demostración fuera de universo, y el grep de AC-01 debe
filtrar este último explícitamente.

**PR-08 — extraer `_apply_verification_waiver` y `_apply_verdicts` de `cmd_record_verification`.**
`cmd_record_verification` (`ai/scripts/feature-state.py:2767-2879`, ~112 líneas dentro de su `update()`
anidado) tiene dos ramas casi enteramente disjuntas: la rama de waiver (`args.skip_reason`, líneas 2791-2816,
termina en `return True`) y la rama de verdictos (líneas 2818-2876). Todo guard agregado después del `return`
de la rama de waiver queda exento de esa rama sin que el lector lo note — la misma clase de agujero de PR-01
(ADR-0009 D8). Se extraen dos funciones puras sobre `(data, package, attempts, budget, args)` — o la firma que
architecture verifique contra el código real — que preserven exactamente la secuencia de validaciones,
mutaciones de estado (`package["verifications"]`, `attempts[...]`, `data["metrics"]["verifications"]`,
`finding[...]`, `record_event`, el gate de budget con `block_with_reason`) y valores de retorno de las dos
ramas actuales, byte-por-byte en comportamiento observable — línea `if not has_open_findings(package) and
_repair_entered_from_review(...)` (`:2867`) incluida, que pertenece a la rama de verdictos, nunca a la de
waiver. `cmd_record_verification` queda como el despachador: valida la actor/fase/replay compartidos, decide
cuál de las dos funciones invocar y devuelve su resultado. [UNVERIFIED for architecture: firma exacta de las
dos funciones extraídas — nombres de parámetros, si reciben `data` completo o solo `package`/`attempts`; el
requisito es equivalencia de comportamiento observable con el código de las líneas 2767-2879 tal como existe
hoy, no una firma específica.]

**PR-09 — corregir el docstring que contradice AC-17, y el puntero en ADR-0009 D7.**
El docstring de `_repair_entered_from_review` (`:2702-2707`) dice: *"PACKAGE_REPAIR has four entry points —
review, delta review, a failed testing run and a failed runtime QA. Only the first is a findings problem; the
other three carry an obligation the finding set cannot see."* — "only the first" da a entender que solo
`review` (sin `delta review`) califica como problema de findings. Eso contradice tanto el código real (`return
event.get("event") in {"record-review", "finalize-review-panel", "record-delta-review"}`, línea 2718, que
incluye `record-delta-review`) como `docs/specs/006-execution-graph/spec.md:180-181` (AC-17: *"the
skip-to-testing transition fires only when the package entered PACKAGE_REPAIR from review **or delta
review**, never from a failed testing run or runtime QA"*). El docstring se corrige para nombrar los DOS casos
que califican (`review` y `delta review`) contra los DOS que no (`testing` y `runtime QA`), sin cambiar código
ejecutable. Adicionalmente, `docs/adr/0009-*.md` sección D7 (línea ~139, *"`max_verifications_per_package` (2
for feature/scoped, 1 for quick-fix/incident) blocks the package when exhausted"*) enuncia el budget viejo
2/1 sin puntero hacia su corrección posterior a 6/3 (sección "D7 corrected again", líneas ~178-186, que fija
`DEFAULT_MAX_VERIFICATIONS = 6`). Se agrega, al final de la sección D7 original, una línea puntero explícita
hacia "D7 corrected again" — sin reescribir el valor 2/1 original, que documenta correctamente la decisión tal
como se tomó en su momento; ADR-0009 ya tiene el patrón de "D7 corrected"/"D7 corrected again" como entradas
separadas, este contrato solo cierra el enlace faltante entre la primera y la corrección final.

## No-objetivos

- **PR-06** (el modelo de budget de verificación es un compromiso de dos contadores independientes bajo un
  mismo valor de configuración) — deuda explícitamente aceptada, no se toca `metrics.verifications` ni el
  nombre/semántica de ningún contador.
- **PR-10** (forma del test suite: un test subsumido por otro, una aserción sobre constantes dentro de un test
  de comportamiento, `create_ready_package` codificando tres estados en dos booleanos) — ningún test existente
  se reestructura, renombra ni se fusiona con otro más allá de lo estrictamente necesario para probar PR-07/
  PR-08 (ver criterios de aceptación).
- **PR-11** (mutate es last-writer-wins sin lock ni compare-and-swap) — diferido a un paquete propio futuro,
  tal como registra la decisión de 006-P2. Ningún cambio a `mutate()`, `--expect-revision` ni al mecanismo de
  escritura de `feature-state.py`.
- Ningún refactor oportunista más allá de las dos extracciones nombradas en PR-08 y la escritura del campo
  nombrado en PR-07. `cmd_record_verification` no cambia su firma pública de CLI (flags, nombres de argumento,
  exit codes, formato de `output_state`).
- Ningún cambio a `_PROVIDER_RUNTIME_REDIRECTS`, `_NEVER_REDIRECT_FROM_RUNTIMES` ni a la lógica de exclusión de
  `_effective_runtime` — solo se agrega observabilidad del hecho de que un redirect ocurrió, nunca se cambia
  cuándo ocurre ni a qué runtime redirige.
- Ninguna reescritura de `RouteDecision` como estructura (no se agregan/quitan campos posicionales) más allá de
  lo que arquitectura determine necesario para transportar el nuevo código no bloqueante dentro del campo
  `reasons` ya existente. [UNVERIFIED for architecture: si el código de redirect vive en `reasons` junto a los
  códigos de exclusión existentes, o requiere un campo nuevo — el requisito observable es que el hecho quede
  expuesto en la `RouteDecision` devuelta o en su rastro de auditoría, sin bloquear la ruta ni cambiar
  `success`/`runtime` resultante.]
- Ninguna reescritura general de `package-gate-runner.md` más allá de quitar los paths absolutos y los nombres
  de módulo de negocio del cliente — la plantilla conserva su estructura, sus gates nombrados y su disciplina
  de permisos denegados por defecto.
- Ningún cambio a ADR-0019 ni a los ACs de `015-anthropic-dispatch-parity` más allá de lo que el reason_code de
  auditoría requiera nombrar; esta feature no reabre el contrato de 015.

## Riesgos

- **Regresión de comportamiento en `_repair_entered_from_review` para estados viejos.** Mitigado por el
  fallback explícito a inferencia por log cuando `repair_entry` está ausente (**AC-02**, corregido en 1.1.0 —
  antes citaba AC-01 por error), y por un test que corre el fixture de un estado pre-existente (sin el campo)
  contra la función y confirma resultado idéntico al de hoy.
- **PR-08 cambia comportamiento observable al extraer funciones.** Mitigado exigiendo que el test suite
  existente para `record-verification` (los tests listados en AC-04) siga pasando sin modificación de sus
  aserciones, más un test nuevo de equivalencia línea-a-línea de las dos ramas.
- **El reason_code del redirect se confunde con un código de exclusión real y bloquea rutas que hoy pasan.**
  Mitigado por los ACs explícitos **AC-09/AC-10** (corregido en 1.1.0 — antes citaba AC-06 por error) que
  exigen que el `success`/`runtime` de una decisión redirigida sea idéntico al de hoy, y que el único campo
  nuevo sea aditivo.
- **La limpieza de `package-gate-runner.md` rompe la plantilla para el próximo paquete real que la necesite.**
  Mitigado exigiendo (**AC-08**, corregido en 1.1.0 — antes citaba AC-07 por error) que el archivo siga siendo
  YAML/frontmatter válido y que la estructura de secciones de permiso (`read`/`edit`/`glob`/... /`bash`)
  permanezca, solo con las entradas muertas quitadas o genericizadas — arquitectura decide el mecanismo exacto
  (placeholder vs. eliminación).
- **`cmd_transition`'s sexta vía de entrada a `PACKAGE_REPAIR` deja `repair_entry` stale.** (Amendment 1.1.0,
  hallazgo F-03.) Mitigado por el `pop("repair_entry", None)` descrito en P1 y el test nuevo asociado — el
  valor stale nunca sobrevive a un `cmd_transition` manual hacia `PACKAGE_REPAIR`.

## Supuestos

- `ai/state/features/*.json` es el universo completo de estados de feature grabados hoy; el fallback de
  **AC-02** (corregido en 1.1.0 — antes citaba AC-01 por error) se verifica contra al menos uno de esos
  archivos reales, no solo contra un fixture sintético.
- El "package-gate-runner.md" no tiene ningún otro consumidor automatizado que dependa de las rutas absolutas
  actuales (es una plantilla de subagente leída por el orquestador al instanciar, no un script parseado por
  código propio del arnés) — arquitectura confirma esto antes de tocar el archivo.
- `docs/adr/0009-*.md` es editable como documentación viva (no es un ADR "Accepted" congelado por convención del
  repo) — se agrega el puntero D7→D7-corrected-again sin abrir una nueva sección de decisión.

## ACs (criterios de aceptación verificables)

- **AC-01** — `package["repair_entry"]` se ESCRIBE en 6 sitios de asignación de una línea: los 5 sitios de
  dominio nombrados en P1 (`:2315`, `:2472`, `:3078`, `:3118`, `:3149`, con valores `"review"`
  (record-review), `"review"` (finalize-review-panel), `"delta_review"` (record-delta-review), `"testing"`
  (record-testing fail), `"runtime_qa"` (record-runtime-qa fail)) más el sitio de `cmd_transition` (`:2005`,
  amendment 1.1.0, hallazgo F-03) que hace `package.pop("repair_entry", None)` — un `pop`, no una escritura de
  valor, en la rama que fija `data["phase"] = "PACKAGE_REPAIR"` vía transición manual. `ai/scripts/feature-state.py:3389`
  (bloque de auto-demostración `dry-run`, hallazgo F-08) es un séptimo sitio de código que fija
  `data["phase"] = "PACKAGE_REPAIR"` pero está explícitamente FUERA de este universo — no pasa por ningún
  comando real ni ejercita `_repair_entered_from_review` de forma que el valor de `repair_entry` importe, y no
  cuenta ni como sitio de escritura ni de pop a los efectos de AC-01. Verificable:
  `grep -n 'repair_entry' ai/scripts/feature-state.py` muestra exactamente 6 sitios de mutación de la clave (5
  escrituras de valor + 1 pop en `cmd_transition`) más los sitios de lectura de AC-02, filtrando explícitamente
  el sitio dry-run de `:3389` (que no menciona `repair_entry` en absoluto — no requiere filtro adicional en la
  práctica, pero el conteo de "5" del contrato 1.0.0 debe leerse como "5 de dominio + 1 de `cmd_transition`" en
  1.1.0).
- **AC-02** — `_repair_entered_from_review` lee `package.get("repair_entry")` primero; si el valor está en
  `{"review", "delta_review"}` devuelve `True` sin tocar `data["history"]`; si está en `{"testing",
  "runtime_qa"}` devuelve `False` sin tocar `data["history"]`; si la clave está AUSENTE, cae exactamente al
  mecanismo actual de inferencia por log (sin modificar esa rama). **Amendment 1.1.0 (hallazgo F-03) — valor
  no reconocido:** si la clave está PRESENTE pero su valor no es ninguno de los 4 strings conocidos (p. ej. un
  estado corrupto o de una versión futura del campo), la función cae al mismo mecanismo de inferencia por log
  que el caso AUSENTE — nunca lanza, nunca asume `True`/`False` por default. Verificable con 4 tests nuevos: uno
  por cada valor reconocido del campo (sin fixture de history), uno que reproduce el fixture actual de
  `test_harness.py` para el camino de inferencia (sin el campo) y confirma resultado idéntico al de antes de
  este contrato, y uno con un valor no reconocido (p. ej. `"bogus"`) que confirma que también cae a inferencia.
- **AC-03** — Ningún test existente de `_repair_entered_from_review`/`cmd_record_verification` cambia su
  aserción. **Corrección 1.1.0 (hallazgo F-07):** `git diff --stat` reporta solo el conteo de líneas
  agregadas/eliminadas por archivo, no PUEDE mostrar si una línea eliminada estaba dentro de un `def test_`
  existente o era, por ejemplo, un comentario — es insuficiente por sí solo para probar este AC. Verificable
  con AMBOS: (a) revisión completa y manual de `git diff tests/test_harness.py` (el diff con contenido, no
  `--stat`) antes del cierre del paquete, confirmando que ninguna línea eliminada cae dentro del cuerpo de un
  `def test_` que ya existía antes del paquete; y (b) un chequeo de conteo de aserciones dirigido — por cada
  uno de los 9 tests nombrados en AC-04, el número de statements `assert*`/`self.assert*` dentro de su cuerpo
  no baja respecto del valor medido antes del paquete (script o `grep -c` acotado al rango de líneas del
  `def` correspondiente).
- **AC-04** — `cmd_record_verification` queda dividido en un despachador más `_apply_verification_waiver` y
  `_apply_verdicts` (o los nombres/firmas que arquitectura confirme contra el código real), preservando
  byte-por-byte el comportamiento observable de las dos ramas actuales: mismos `StateError` en los mismos
  puntos con los mismos mensajes, mismas mutaciones de `package["verifications"]`/`attempts`/
  `data["metrics"]["verifications"]`/`finding[...]`, mismo `record_event` (mismo `event`, `from_phase`,
  `to_phase`, payload), mismo comportamiento de `_repair_entered_from_review` dentro de la rama de verdictos.
  Verificable: la suite completa de los 9 tests listados a continuación por nombre sigue pasando sin
  modificación de aserciones (AC-03) después de la extracción —
  `test_verification_does_not_consume_a_review_cycle`, `test_only_the_verifier_may_refute_and_never_its_own_finding`,
  `test_upheld_is_sticky_and_verification_has_a_physical_budget`, `test_verification_is_required_in_code_not_only_in_prose`,
  `test_verification_rejects_bad_shapes_and_replays_idempotently`, `test_verification_budget_survives_two_review_cycles`,
  `test_every_reader_of_the_verification_budget_defaults_alike`, `test_graph_verification_edges_and_waived_verification_node`,
  `test_graph_waived_verification_actor_never_fabricated_when_history_desyncs`. **Corrección 1.1.0 (hallazgo
  F-07):** esta lista de 9 nombres es la AUTORIDAD — el AC no se verifica por selector de grep. El grep
  `grep -n "def test_" tests/test_harness.py | grep -i verif` que el contrato 1.0.0 citaba como equivalente
  fue re-ejecutado en vivo en esta sesión y devuelve 16 coincidencias, no 9: además de los 9 nombrados arriba
  incluye tests sin relación con `record-verification` que contienen "verif" en otro sentido (p. ej.
  `test_obsidian_catalog_has_verified_pm_identifiers_plus_doc`,
  `test_apply_vault_migration_pure_move_copy_verify_then_delete_and_links`,
  `test_guest_copy_scaffolds_and_verifies_portably`, `test_runtime_verifier_can_manage_browser_mcp_gate`,
  `test_init_refuses_to_attest_a_spec_it_did_not_verify`,
  `test_next_names_verification_instead_of_recommending_a_refused_command`,
  `test_record_repair_commit_accepted_when_git_verifies_it`) y no debe usarse como criterio de verificación.
- **AC-05** — **reescrito en 1.1.0 (hallazgo F-02): el AC original era intestable tal como estaba redactado**
  (el código pre-extracción deja de existir una vez aplicado PR-08, así que no hay "función original" contra
  la cual comparar en el árbol final; y un deep-equal crudo sobre `data` es frágil porque varios campos llevan
  timestamps `now()` que difieren entre dos invocaciones aunque el comportamiento sea idéntico). Se divide en
  dos obligaciones de naturaleza distinta:
  - **AC-05(a) — tests de comportamiento permanentes, viven en el suite después del merge.** Para cada rama
    (waiver y verdictos), invocar directamente `_apply_verification_waiver`/`_apply_verdicts` sobre los 4
    fixtures nombrados (waiver con budget disponible, waiver con budget agotado, verdictos con `refuted` que
    vacía los findings abiertos, verdictos con `upheld` que no los vacía) y pinnear los resultados observables
    esperados explícitamente en el test, no por comparación contra una función que ya no existe: el mensaje
    exacto de `StateError` en cada camino de rechazo (waiver con budget agotado; verdicto sobre un finding ya
    cerrado; actor no autorizado), las mutaciones exactas a `package["verifications"]` (entrada agregada, con
    qué claves), `attempts[...]` (contador incrementado o no), `data["metrics"]["verifications"]` (incrementado
    o no), `finding[...]` (status/verified_by/verified_verdict fijados o no), y el payload exacto pasado a
    `record_event` (`event`, `from_phase`, `to_phase`, y el dict de metadata). Todo timestamp (`now()`) se
    normaliza antes de comparar (freeze o inyección de reloj determinístico) o se excluye explícitamente del
    assert de igualdad — nunca se compara un timestamp real contra otro capturado en una invocación distinta.
  - **AC-05(b) — obligación de una sola vez, cerrada en el gate de revisión del paquete, no en el suite de
    tests permanente.** El reviewer del paquete que implementa PR-08 confirma, leyendo el diff real de
    `cmd_record_verification` contra la versión pre-PR-08 (línea por línea, no por muestreo), que cada línea de
    guard/validación de las dos ramas actuales (líneas 2791-2876 de la versión pre-extracción) aparece en
    EXACTAMENTE una de las dos funciones extraídas — nunca duplicada, nunca perdida, y ningún guard queda
    alcanzable únicamente antes del `return` de una rama y no de la otra. Esta confirmación se registra como
    hallazgo de revisión cerrado (no como test de código, porque no hay invariante de runtime que un test
    futuro pueda re-verificar una vez que el código pre-extracción ya no existe) — la línea `if not
    has_open_findings(package) and _repair_entered_from_review(...)` (`:2867`) queda explícitamente confirmada
    dentro de `_apply_verdicts`, nunca en `_apply_verification_waiver`.
- **AC-06** — el docstring de `_repair_entered_from_review` nombra explícitamente los dos casos que califican
  (`review`, `delta review`) y los dos que no (`testing`, `runtime QA`), sin usar la frase "only the first".
  Verificable: `grep -n "Only the first is a findings problem" ai/scripts/feature-state.py` no devuelve
  resultados después del cambio; el docstring corregido es consistente palabra por palabra con
  `docs/specs/006-execution-graph/spec.md:180-181` (AC-17).
- **AC-07** — `docs/adr/0009-*.md`, sección "D7 (new)" (la que enuncia `max_verifications_per_package` "2 for
  feature/scoped, 1 for quick-fix/incident"), termina con una línea puntero explícita hacia la sección "D7
  corrected again" que fija `DEFAULT_MAX_VERIFICATIONS = 6`. Verificable: `grep -n "D7 corrected again"
  docs/adr/0009-*.md` aparece también referenciado desde dentro del cuerpo de la sección "D7 (new)" original,
  no solo como título de sección posterior.
- **AC-08** — `Global/_canonical/opencode-agents/package-gate-runner.md` no contiene ningún path absoluto de
  una máquina de usuario (`/home/`, `/Users/`, `/tmp/opencode/`), ningún hash de baseline/worktree derivado de
  ese path (`4ef70b0ab6da`), ni los identificadores de módulo de negocio de cliente (`contabilium-ingestion`,
  `replenishment-v2`, `RPL-P0A` — en cualquier capitalización, incluida la forma en minúsculas usada dentro de
  paths como `rpl-p0a-gates-...`, y la forma en mayúsculas usada en el frontmatter `description:` de la línea
  2 — `iey-ai`). **Corrección 1.1.0 (hallazgo F-04):** el grep original era case-sensitive y no detectaba las
  variantes en minúsculas verificadas en vivo contra el archivo real: los 4 paths
  `/tmp/opencode/rpl-p0a-gates-4ef70b0ab6da/{opencode.json,CLAUDE.md,docs/replenishment-v2/packages.md,docs/replenishment-v2/adr/0013-gate-local-rls-y-produccion-separados.md}`
  (líneas 11-14), el hash `4ef70b0ab6da` (aparece también suelto en la línea de `check-owned-paths.py
  --baseline`, línea 64), y `"RPL-P0A"` en el frontmatter `description:` (línea 2). Verificable:
  `grep -inE "/home/|/Users/|/tmp/opencode/|4ef70b0ab6da|contabilium-ingestion|replenishment-v2|RPL-P0A|iey-ai" Global/_canonical/opencode-agents/package-gate-runner.md`
  (nótese el flag `-i`, case-insensitive, respecto del grep case-sensitive del contrato 1.0.0) no devuelve
  resultados. El archivo sigue siendo YAML frontmatter válido (`python3 -c "import yaml,
  re,sys; ..."` o el parser que arquitectura ya use para validar agentes) y conserva las mismas claves de
  primer nivel de `permission` (`read`, `edit`, `glob`, `grep`, `list`, `task`, `question`, `webfetch`,
  `websearch`, `lsp`, `skill`, `todowrite`, `doom_loop`, `external_directory`, `bash`) con el mismo default
  `deny` en `"*"` donde ya existía.
- **AC-09** — cuando `RoutingService._effective_runtime` devuelve un valor distinto del `runtime` solicitado
  (`redirect`), la `RouteDecision` resultante (o el evento de auditoría que la acompaña — arquitectura decide
  el mecanismo exacto por AC-10) expone un código no bloqueante distinguible (p. ej. dentro de `reasons`) que
  identifica el redirect, el runtime solicitado y el runtime efectivo, sin cambiar `success`, `runtime` final
  ni `identity`/`fallback` resultantes frente al comportamiento de hoy. Verificable con un test que fuerza
  `identity_allowed`/inventario de forma que `_effective_runtime` redirija (mismo fixture que ya prueba AC-01
  de `015-anthropic-dispatch-parity` en `tests/test_routing.py -k test_ac01`), y compara la `RouteDecision`
  devuelta antes/después: `success` y `runtime` idénticos, y un elemento nuevo presente que no estaba antes en
  el lugar donde arquitectura decida exponerlo.
- **AC-10** — **corregido en 1.1.0 (hallazgo F-06): el universo real es 5 shapes, no 4, más un test de
  colisión de nombre que el selector `-k test_ac01` también arrastra.** Verificado en vivo contra
  `tests/test_routing.py`: `python3 -m unittest tests.test_routing -v -k test_ac01` selecciona por prefijo de
  nombre, y el árbol real tiene 5 tests `test_ac01_shape_*` — shape (a) `test_ac01_shape_a_no_redirect_target_credential_still_hard_halts_review`
  (`:759`), shape (b) `test_ac01_shape_b_pair_absent_redirects_anthropic_review_to_claude_code` (`:787`), shape
  (c) `test_ac01_shape_c_pi_already_authenticated_pair_is_never_redirected` (`:817`), shape (d)
  `test_ac01_shape_d_pi_present_but_model_incomplete_pair_stays_excluded_not_redirected` (`:834`), y shape (e)
  `test_ac01_shape_e_pi_pair_genuinely_absent_never_redirects_pi_is_lane_exempt` (`:861`) — más
  `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only` (`:2988`, de `012-discovered-inventory`,
  sin relación con el redirect de 015/016 más allá de compartir el prefijo `test_ac01`), que el mismo selector
  `-k test_ac01` también ejecuta y que debe seguir pasando sin modificación. Ningún redirect real cambia de
  comportamiento: los 5 shapes (a/b/c/d/e) siguen pasando sin modificación de sus aserciones sobre
  `runtime`/`success`, y `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only` sigue pasando sin
  modificación (no toca el redirect, pero confirma que el selector no se rompió). **La aserción de "el caso
  `pi` no emite código nuevo" se fija sobre AMBOS shapes donde `pi` está involucrado y no debe redirigir:**
  shape (c) (`pi` ya autenticado, el par está presente — no hay redirect que emitir código porque no hay
  redirect) y shape (e) (`pi` es categóricamente exento por `_NEVER_REDIRECT_FROM_RUNTIMES` aunque el par esté
  genuinamente ausente — tampoco emite código nuevo, precisamente porque está exento, no porque el par esté
  presente). Ambos shapes deben confirmar ausencia del código nuevo en `decision.reasons`/exclusiones, por
  motivos distintos, y el test no debe confundir uno con el otro. [UNVERIFIED for architecture: si el código
  nuevo vive en el campo `reasons` posicional 6 de `RouteDecision` (hoy vacío `()` en toda decisión exitosa de
  la rama writer, y con el precedente de `REVIEW_IDENTITY_UNVERIFIED` ya poblándolo en la rama review/simulate
  — ver P2, hallazgo F-08) o requiere extender la tupla — la firma exacta de `RouteDecision` es propiedad de
  arquitectura, no de este contrato.]
- **AC-11 (regresión global)** — `python3 -m unittest discover -s tests -v` corre sin fallar y sin ningún test
  saltado; el conteo de tests sube desde la baseline medida en vivo en esta sesión (558,
  `grep -rhoE "^\s*def test_" tests/*.py | wc -l`) en al menos los tests nuevos descritos en AC-02/AC-05/AC-09,
  nunca baja. `./ai/scripts/verify.sh` (si existe y aplica al alcance tocado) reporta `VERIFY_PASS` o el
  equivalente que ya usa el resto del repo para paquetes de este arnés.

## Auditoría (autorrevisión)

- **Universo nombrado:** para AC-01/AC-02, el universo son exactamente los 5 sitios de asignación de
  `data["phase"] = "PACKAGE_REPAIR"` verificados por grep en el código actual — no una estimación, los 5 fueron
  leídos con contexto (`cmd_record_review`, `cmd_finalize_review_panel`, `cmd_record_delta_review`,
  `cmd_record_testing`, `cmd_record_runtime_qa`). Para AC-08, el universo de paths/nombres a remover se
  verificó por grep exhaustivo sobre el archivo real, no sobre una muestra.
- **Comportamiento de ausencia definido:** sí — AC-02 define explícitamente que la ausencia de `repair_entry`
  (todo estado grabado antes de este contrato) cae al mecanismo de inferencia actual, verificado contra el
  hecho medido de que ningún `ai/state/features/*.json` real tiene la clave hoy.
- **Fuente de datos probada de cargar la señal:** sí para AC-01/AC-02 (los 5 call sites leídos directamente,
  con línea y contenido citados); sí para AC-09/AC-10 (el fixture que ya ejercita `_effective_runtime` en
  `test_routing.py -k test_ac01` es el mismo que prueba el redirect real, no uno sintético nuevo que podría no
  ejercitar el camino real).
- **Pase de conflicto par a par:** AC-01/AC-02 (repair_entry) y AC-04/AC-05 (extracción de
  cmd_record_verification) tocan el mismo comando (`cmd_record_verification` invoca
  `_repair_entered_from_review` en la línea `:2867`, dentro de la rama que PR-08 mueve a `_apply_verdicts`) —
  se verificó que AC-05 exige explícitamente que esa línea permanezca dentro de `_apply_verdicts` y nunca migre
  a `_apply_verification_waiver`, precedencia ya explícita en el texto de P1. AC-09 (reason_code) y las ACs de
  `015-anthropic-dispatch-parity` (fuera de este contrato) no compiten: AC-10 fija que ningún shape existente
  cambia de resultado, solo se agrega un campo aditivo.
- **Supuestos de nivel HOW marcados:** firma exacta de `_apply_verification_waiver`/`_apply_verdicts` (P1,
  AC-04, AC-05); mecanismo exacto para exponer el reason_code del redirect en `RouteDecision`/auditoría (P2,
  AC-09, AC-10); mecanismo exacto de limpieza de `package-gate-runner.md` (placeholder vs. eliminación directa,
  Riesgos, AC-08).
- **Qué no pude verificar:** no corrí el test suite completo dentro de esta sesión de producto (no me
  corresponde ejecutar el paquete); los conteos de tests y los grep citados sí se corrieron en vivo contra el
  código real del repo en el momento de escribir este contrato. No verifiqué si `package-gate-runner.md` tiene
  algún consumidor automatizado fuera del propio orquestador — queda como supuesto explícito para arquitectura.

## Verificación

`python3 -m unittest discover -s tests -v` (0 fallos, 0 saltados, conteo ≥ 558 + tests nuevos) ·
`grep -n "repair_entry" ai/scripts/feature-state.py` (6 sitios de mutación: 5 escrituras de valor + 1 pop en
`cmd_transition`, más lectura en `_repair_entered_from_review`) ·
`grep -n "Only the first is a findings problem" ai/scripts/feature-state.py` (sin resultados) ·
`grep -n "D7 corrected again" docs/adr/0009-*.md` (referenciado también desde D7 original) ·
`grep -inE "/home/|/Users/|/tmp/opencode/|4ef70b0ab6da|contabilium-ingestion|replenishment-v2|RPL-P0A|iey-ai" Global/_canonical/opencode-agents/package-gate-runner.md`
(sin resultados, grep case-insensitive per hallazgo F-04) · `python3 -m unittest tests.test_routing -v -k
test_ac01` (los 5 shapes a/b/c/d/e más `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only`
siguen OK, sin regresión) · `git diff tests/test_harness.py tests/test_routing.py` (revisión completa de
contenido, no solo `--stat`, per hallazgo F-07) antes de cerrar el paquete (ninguna aserción de test existente
eliminada) · `./build.sh --check` reporta `SELF_SCAFFOLD_SYNC_OK files=2` (hallazgo F-01 — confirma que
`ai/scripts/feature-state.py` y `PROYECTO/ai/scripts/feature-state.py` quedan byte-idénticos después del
cambio, sin `SELF_SCAFFOLD_DRIFT`).

## Changelog

- **1.1.0** (2026-08-02) — amendment pass tras `SPEC_CHALLENGE` round 1 (verdict `approve-with-amendments`, 8
  hallazgos, 0 decisiones de usuario requeridas). Cambios: (F-01) nombrado explícito del gemelo
  `PROYECTO/ai/scripts/feature-state.py` en `## Alcance` y en `## Verificación` (`./build.sh --check`); (F-02)
  AC-05 dividido en obligación de test permanente (a) y obligación de revisión de una sola vez (b); (F-03)
  `cmd_transition` documentado como sexto sitio de entrada a `PACKAGE_REPAIR` con `pop("repair_entry", None)`,
  AC-01 recontado a 6 sitios de mutación, AC-02 extendido con el caso de valor no reconocido; (F-04) AC-08
  corregido a grep case-insensitive (`-i`) y universo de remoción ampliado con los 4 paths `/tmp/opencode/...`,
  el hash `4ef70b0ab6da` y `"RPL-P0A"` en el frontmatter; (F-05) referencias cruzadas corregidas en `##
  Riesgos`/`## Supuestos` (AC-01→AC-02, AC-06→AC-09/AC-10, AC-07→AC-08); (F-06) universo de AC-10 corregido de
  4 a 5 shapes (a/b/c/d/e) más `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only`, aserción de
  "pi no emite código nuevo" fijada explícitamente sobre los shapes (c) y (e); (F-07) AC-04 fijado a la lista
  de 9 nombres como autoridad (el grep citado devuelve 16, no 9, ni 17), AC-03 extendido a requerir revisión
  completa de `git diff` más chequeo de conteo de aserciones; (F-08) corregida la afirmación de que
  `reasons=()` siempre en decisión exitosa (la rama review/simulate ya puebla `REVIEW_IDENTITY_UNVERIFIED`),
  y nombrado `feature-state.py:3389` como sitio de demostración `dry-run` fuera del universo de AC-01/AC-02.
  Ver `## Historial de challenge` para el detalle completo.
- **1.0.0** — versión inicial del contrato, alcance decidido por el usuario el 2026-08-02 (PR-07/PR-08/PR-09 de
  la deuda de `006-execution-graph` más los dos ítems de higiene menor).

## Historial de challenge

### Round 1 (contract 1.0.0) — verdict `approve-with-amendments`, 8 hallazgos, 0 decisiones de usuario

| Hallazgo | Severidad | Asunto | Disposición bajo contract 1.1.0 |
|---|---|---|---|
| F-01 | High | `PROYECTO/ai/scripts/feature-state.py` es un gemelo byte-idéntico enforzado por `./build.sh --check` (`SELF_SCAFFOLD_DRIFT`), no nombrado en el alcance/ownership original | **FIXED** — ambos paths nombrados explícitamente en `## Alcance`; `./build.sh --check` reportando `SELF_SCAFFOLD_SYNC_OK` agregado a `## Verificación` |
| F-02 | High | AC-05 tal como estaba redactado es intestable: el código pre-extracción deja de existir tras PR-08, y comparar `data` por deep-equal se rompe por timestamps `now()` no determinísticos | **FIXED** — AC-05 dividido en AC-05(a) (tests de comportamiento permanentes sobre los 4 fixtures nombrados, con resultados pinneados explícitamente — mensajes de `StateError`, mutaciones de campo, payload de `record_event` — y timestamps normalizados/inyectados) y AC-05(b) (obligación de revisión de una sola vez: el reviewer confirma vía el diff de extracción que cada línea de guard vive en exactamente una función) |
| F-03 | High | `cmd_transition` (`:2005`; `LEGAL_TRANSITIONS` permite `REVIEW`/`DELTA_REVIEW`/`TESTING`/`RUNTIME_QA` → `PACKAGE_REPAIR`) es un sexto sitio de entrada a `PACKAGE_REPAIR` que no escribe `repair_entry` — un valor stale invertiría la inferencia | **FIXED** — `cmd_transition` hace `package.pop("repair_entry", None)` en la rama que fija `PACKAGE_REPAIR` (comportamiento byte-idéntico al de hoy vía fallback a inferencia), con test nuevo; AC-01 recontado a 6 sitios de mutación; AC-02 extendido con el caso de valor no reconocido cayendo a inferencia |
| F-04 | Medium | El grep de AC-08 es case-sensitive y no detecta identificadores en minúsculas: los 4 paths `/tmp/opencode/rpl-p0a-gates-4ef70b0ab6da/...` (líneas 11-14), el hash `4ef70b0ab6da`, y `"RPL-P0A"` en el frontmatter (línea 2) | **FIXED** — AC-08 usa `grep -inE`; universo de remoción ampliado con los paths `/tmp/opencode/...`, el hash de baseline y la variante de frontmatter |
| F-05 | Medium | Referencias cruzadas rotas: Riesgos b1 + Supuestos b1 citan AC-01 (debería ser AC-02); Riesgos b3 cita AC-06 (debería ser AC-09/AC-10); Riesgos b4 cita AC-07 (debería ser AC-08) | **FIXED** — las 4 referencias corregidas en `## Riesgos`/`## Supuestos`, anotadas inline como corrección 1.1.0 |
| F-06 | Medium | El universo de AC-10 son 5 shapes (a/b/c/d/e — shape (e) es el caso `pi` lane-exempt, `tests/test_routing.py:861`) más `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only` (`:2988`), no 4 shapes | **FIXED** — AC-10 reescrito citando los 5 shapes con línea exacta cada uno, más el test de colisión de nombre; la aserción de "pi no emite código nuevo" fijada explícitamente sobre shapes (c) y (e), por motivos distintos (par presente vs. exención categórica) |
| F-07 | Low | AC-04's grep selector devuelve 16 tests (verificado en vivo), no 9; AC-03's `git diff --stat` no puede mostrar líneas eliminadas dentro de un `def test_` existente | **FIXED** — AC-04 fija la lista de 9 nombres como autoridad, grep citado solo a título informativo con conteo corregido; AC-03 requiere revisión completa de `git diff` (no `--stat`) más un chequeo de conteo de aserciones por test |
| F-08 | Low | La afirmación "la decisión exitosa siempre construye `reasons=()`" es incorrecta — la rama review/simulate de `service.py` ya emite `REVIEW_IDENTITY_UNVERIFIED` en éxito de selección; `feature-state.py:3389` (fixture `dry-run`) es un sexto sitio de asignación de fase fuera del universo de AC-01 | **FIXED** — párrafo de P2 corregido con el precedente favorable citado explícitamente; `:3389` nombrado y excluido explícitamente del universo de AC-01/AC-02 |

No se requirió ninguna decisión de usuario para cerrar este round — los 8 hallazgos se resuelven todos dentro
del contrato existente, sin cambio de alcance ni de las decisiones ya tomadas por el usuario en `## Origen`.
