# ADR-0036 — Capa cognitiva: `docs/modules/`, gate de impacto humano en INTEGRATION

- Estado: Accepted (2026-08-10). Feature 019-harness-evolution, PKG-3 (`P3-cognitive-module-docs`).

## Contexto

El harness registra con obsesión el estado del **pipeline** (qué paquete, qué fase, qué hallazgo:
`ai/state/`, `docs/notas/`) y no registra nada del **software construido**. La única documentación
global de "qué hace el sistema" es `docs/architecture/overview.md`, mantenida a mano por `architect`
en fase de diseño (`Global/_canonical/agents/architect.md:41-47`), sin ningún gate — y estaba stale en
este mismo repo: describía "trusted routing P1R" mientras el harness ya llevaba 35 ADRs aceptados
(billing-aware ordering, auto-adopted providers, spawn provenance, etc.). Ningún mecanismo obliga a
que un paquete que cambió comportamiento real dejara algo legible para quien no vivió esa sesión.
Objetivo medible: abrir `docs/modules/<slug>.md` y en 90 segundos recuperar qué hace un módulo, por
dónde fluye, qué invariantes tiene y qué cambió último.

## Decisión

1. **`docs/modules/modules.toml`** es el registro fail-closed de módulos: `[module.<slug>]` con
   exactamente `nombre`, `responsabilidad`, `paths` (lista de globs no vacía). Slug con forma cerrada
   (`^[a-z][a-z0-9-]*$`), clave desconocida = error explícito, igual que el resto del repo (nunca un
   typo silenciosamente ignorado). `paths` es la fuente de la detección de impacto: se matchean contra
   `owned_paths` del paquete y `changed_files` de sus repairs.
2. **`feature_state_lib/render_modules.py`** es el motor de render de `docs/modules/<slug>.md`, mismo
   contrato que `render_notes.py`: never-raises, atómico, `render-failures.log` compartido, y reutiliza
   literalmente `merge_note`/`write_note`/`_short` — no hay una segunda implementación del merge
   máquina/humano. `modules_root()` copia el criterio de `notes_root()`: el marcador de "proyecto
   gestionado" es que exista `ai/state/`, nunca si `docs/modules/` ya existe — un repo sin
   `docs/modules/` (o sin `modules.toml`) simplemente no renderiza, nunca falla.
3. **Qué vive dentro del bloque `<!-- notas:auto -->` vs. fuera, y por qué.** El schema de AC-17 nombra ocho
   secciones: `Responsabilidad`, `Puntos de entrada`, `Componentes`, `Flujo`, `Posee / Depende de`,
   `Invariantes`, `Decisiones`, `Últimos cambios estructurales`. De esas ocho, dos son genuinamente
   re-derivables en cada render sin inventar una segunda fuente de verdad: `## Responsabilidad` (copiada de
   `modules.toml`, cadena corta editable por un humano ahí) y `## Últimos cambios estructurales` (agregado de
   `module_impacts` de TODOS los features/paquetes que tocaron ese slug, capado a 10, más reciente primero —
   la única de las ocho con una fuente de datos que cambia por sí sola). Una tercera, `Posee / Depende de`, se
   **parte en dos** por el mismo motivo: su mitad "Posee" (la lista de `paths` de `modules.toml`) es tan
   derivable como `Responsabilidad`, pero su mitad "Depende de" no tiene ningún campo estructurado que la
   derive. En vez de forzar la sección entera adentro (mintiendo sobre "Depende de") o dejarla entera afuera
   (perdiendo la derivación gratis de "Posee"), `_module_auto_body` (`render_modules.py`) emite un heading
   NUEVO, `## Posee` (sin la ambigüedad del nombre compuesto), dentro del bloque máquina, listando los globs
   literalmente; el heading original del schema, `## Posee / Depende de`, se mantiene íntegro del lado humano,
   con su propia prosa que dice explícitamente "Posee: ver 'Posee' arriba" en vez de duplicar la lista. El
   resultado son **tres secciones del bloque máquina** (`Responsabilidad`, `Posee`, `Últimos cambios
   estructurales` — la cuenta que el código realmente hace, `_module_auto_body:158-182`) cubriendo contenido
   de **tres de las ocho** secciones del schema (`Responsabilidad`, la mitad "Posee" de `Posee / Depende de`,
   `Últimos cambios estructurales`), y **seis secciones sembradas** en `HUMAN_SCAFFOLD_SECTIONS`
   (`Puntos de entrada`, `Componentes`, `Flujo`, `Posee / Depende de` completa — con su prosa de "Depende de"
   irreemplazable —, `Invariantes`, `Decisiones`); de esas seis, cinco no tienen ningún campo estructurado en el
   estado que las derive: forzarlas dentro del bloque auto las condenaría a placeholder eterno o, peor, a
   borrar en cada render cualquier prosa real que alguien escribiera ahí (`merge_note` regenera *solo* lo que
   está entre los marcadores; nada de lo que hay adentro sobrevive a un re-render). Por eso viven **fuera**
   del marcador, sembradas una vez en la creación del doc (scaffold con placeholders `_(completar)_` para
   módulos nuevos sin contenido aún, o con la prosa verificada del seed para AC-24) y preservadas para siempre
   por el mismo mecanismo que ya protege "## Notas propias" en cada nota viva existente del harness. Es la
   aplicación literal del patrón que `_package_body`/`_feature_body` ya establecen: lo que es 100% derivable
   de estado estructurado va adentro; lo que es prosa que solo un humano puede certificar va afuera,
   preservado.

   **Registro formal de la desviación (F-07, repair de P3).** Esta partición del schema de AC-17 (3
   secciones derivadas dentro del bloque máquina, 5 sembradas en zona humana, en vez de las 8 dentro del
   bloque como el context pack original de P3 sugería) fue objetada por la review independiente y resuelta
   por el orquestador con `log-decision` — ver
   [[../notas/decisiones/2026-08-11 el-schema-de-ac-17-se-parte-3-secciones-derivadas-en-el-bloque-maquina-5-sembradas-en-zona-humana|la decisión registrada]]
   (`ai/state/decisions-log.jsonl`, slug
   `el-schema-de-ac-17-se-parte-3-secciones-derivadas-en-el-bloque-maquina-5-sembradas-en-zona-humana`). La
   desviación se acepta **con la condición explícita** de que el documento no falsee esa garantía: F-01
   (reescritura de `docs/architecture/overview.md` para no afirmar que las 8 secciones se regeneran solas)
   y F-04 (línea visible de staleness al final del bloque máquina de cada `docs/modules/<slug>.md`, para
   que el lector vea la frontera incluso en preview de Obsidian, donde los comentarios HTML son invisibles)
   son la condición, no un extra — sin ellas la desviación no queda aceptada porque el paquete reproduciría
   el defecto que existe para arreglar. Ambas están reparadas en este mismo ciclo.
4. **Comandos** (`ai/scripts/feature_state_lib/cli_modules.py`, alcance de import igual al resto de
   `feature_state_lib/`): `record-module-impact <fid> --package-id P --module <slug> --cambio "..."
   --modelo-mental "..."` hace append a `package["module_impacts"]`, regenera el doc del módulo, e
   imprime el bloque `Impacto humano:` listo para la narración (P4 fija el formato exacto de dónde se
   pega). `module-impact-detect <fid> --package-id P` lista candidatos por match de glob, sin mutar.
   `record-module-impact ... --module-impact-waived --reason "<motivo>"` es la válvula: un quick-fix
   trivial no paga un doc entero, registra `package["module_impact_waiver"]` en su lugar. Ambos modos
   son el mismo comando, mutuamente excluyentes, para que la ceremonia de invocación sea una sola.
   `module-impact-detect` además reporta, en una sección `unmatched_paths` separada de `candidates`
   (F-06, repair de P3), los paths del paquete que no matchean ningún patrón de `modules.toml` — la
   señal de que puede convenir un `[module.<slug>]` nuevo. Es puramente advisory, nunca gatea nada.

   **Límite conocido, no reparado (F-06).** La detección (`matching_modules`/`unmatched_candidate_paths`,
   `render_modules.py`) compara cada path candidato contra cada patrón de módulo con `fnmatch`
   path-contra-glob; nunca compara dos globs entre sí para detectar solapamiento semántico. Un
   `owned_path` de paquete más ancho que todo patrón de módulo registrado (p. ej. `ai/scripts/**` cuando
   `modules.toml` solo declara `ai/scripts/routing_core/**`) da cero matches, aunque todo patrón de
   módulo sea subconjunto estricto de ese owned path. Arreglarlo bien exige razonar sobre solapamiento
   glob-contra-glob (o expandir ambos lados contra el árbol real de archivos), que es un rediseño, no un
   repair acotado — queda documentado como limitación conocida, no como TODO silencioso.
5. **El gate de INTEGRATION.** `transitions.check_transition` gana una precondición dura para
   `to_phase == "INTEGRATION"`: cada paquete `accepted` (no `superseded`) necesita `module_impacts` no
   vacío **o** `module_impact_waiver` registrado (`model.module_impacts_ready`). `next_transition`
   deja de recomendar `INTEGRATION` desde `PACKAGE_ACCEPTED` mientras falte cobertura, y `done_ready`
   agrega el mismo chequeo como red de seguridad para quien llegue a `DONE` sin pasar por el hook de
   permisos del orquestador. **Relación explícita con ADR-0024**: esa ADR decidió deliberadamente que
   `integration_ready` (el receipt de git tree-hash) **no** fuera precondición de
   `transitions.check_transition`, porque es una verificación externa (re-derivar contra el repo vivo)
   que puede quedar trabada por causas ajenas al paquete, y porque dos tests inmutables ya ejercían
   `accept-package → transition INTEGRATION → transition DONE` sin receipt — el enforcement real quedó
   exclusivamente en la capa de permisos del orquestador (`integration_gate.py`/`coord_policy.py`). El
   chequeo de este ADR es deliberadamente distinto en las dos dimensiones que hacían inaceptable la
   dureza en `transitions.py`: (a) es sobre documentación **derivable del propio estado del paquete**
   (module_impacts ya vive en `package[...]`, no hay nada externo que re-derivar ni que pueda fallar por
   causas de infraestructura), y (b) tiene una **válvula barata de un solo comando** (`--module-impact-
   waived --reason`) que nunca puede quedar más cara que escribir la documentación misma — al contrario
   del receipt, que exige repetir todo el freeze/re-derive. Por eso SÍ es seguro como precondición dura
   de la máquina de estados genérica: no hay ningún caller legítimo (test, humano, otro rol) para el que
   "documentar el impacto o declarar por qué no aplica" sea un costo desproporcionado, mientras que sí
   lo era para el receipt. Los dos tests inmutables que ADR-0024 protegía
   (`test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle`,
   `test_package_workflow_happy_path_executes_real_transitions`) se actualizan para declarar un waiver
   antes de `transition INTEGRATION`, igual que ya declaran gate/review/testing/runtime-qa — no es una
   flexibilización del gate, es la misma ceremonia extendida al paso nuevo.
6. **`cmd_digest`** suma `## Qué cambió en el software`, derivada de los `module_impacts` con `at` en
   la ventana, mismo estilo que las secciones existentes (una línea por impacto:
   `**<módulo>** — <cambio> (<feature>/<paquete>)`).
7. **AC-24, seed real.** `docs/modules/modules.toml` describe cinco módulos reales de este repo
   (routing, estado/feature-state, generación de árboles, app de consola, narración/notas), con
   contenido verificado `file:line`, no plausible; `docs/architecture/overview.md` se regenera para dejar
   de describir un estado congelado en P1R y señalar `docs/modules/` como la fuente viva de verdad
   por módulo.
8. **AC-25/AC-26 (extensión, P4 — `P4-doctrine-human-layer`), la capa humana del gate.** El mecanismo
   de las decisiones 1-7 es de estado/render/gate; sin un procedimiento que lo alimente y lo muestre,
   `record-module-impact` es una CLI que nadie corre por costumbre y un bloque que nadie ve. Dos piezas
   cierran eso:
   - **`orchestrator.md`'s bloque de cierre de paquete** (`## Narración — protocolo de transparencia`,
     milestone "close of a package") suma un sub-bloque fijo, aditivo a los registros `Cliente:`/
     `Ingeniería:` (ADR-0027) y al bloque de fin de turno (ADR-0033) — ninguno de los dos se toca:
     ```
     Impacto humano:
     Módulo: <slug>
     Cambio de modelo mental: <qué cambió en cómo hay que pensar el sistema>
     Tenés que saber: <lo que el usuario necesita tener presente de ahora en más>
     ```
     El contenido sale literal del `record-module-impact` que el paquete ya corrió antes de `accept-package`
     (o del waiver, en cuyo caso el sub-bloque no aparece) — nunca se improvisa en la narración.
   - **`integrator.md` e `architect.md` ganan el paso que faltaba.** `integrator`, que ya consolida la
     evidencia de entrega, corre `module-impact-detect` y registra `record-module-impact` (o el waiver)
     por cada módulo afectado, y verifica que `docs/architecture/overview.md` y los docs de los módulos
     tocados no queden stale — es el rol natural para esto porque ya es el último paso antes de
     `INTEGRATION`, donde el gate de la decisión 5 lo exige de todos modos. `architect`, al diseñar un
     módulo NUEVO, crea su entrada en `modules.toml` y su doc inicial — así el seed de AC-24 deja de ser
     el techo del inventario. **Ninguna de las dos doctrinas promete regeneración automática de las seis
     secciones sembradas** (decisión 3 de este ADR): documentar el impacto es registrar el cambio
     estructural y la prosa nueva a mano donde corresponda, no invocar un comando que reescriba solo.

## Rejected alternatives

- **Todo el schema (8 secciones) dentro del bloque auto.** Ver decisión 3: sin una fuente de estado
  estructurada para las cinco restantes, esto o las condena a placeholder perpetuo o borra prosa
  humana real en cada render — el peor de los dos mundos, y exactamente el defecto que `merge_note`
  existe para prevenir en primer lugar.
- **`integration_ready` (receipt) como la misma precondición.** Ya decidido en contra por ADR-0024, y
  las razones no cambiaron: sigue siendo una re-derivación externa cara sin válvula barata.
- **Extender `modules.toml` con más claves para las seis secciones narrativas.** Reintroduciría una
  segunda fuente de verdad narrativa fuera de las notas vivas ya establecidas, y el schema fail-closed
  de AC-18 (clave desconocida = error) existe justamente para mantener ese registro angosto.
- **Un comando `waive-module-impact` separado.** Rechazado por ceremonia: dos comandos para un concepto
  (registrar impacto) con dos modos mutuamente excluyentes es más superficie que uno con una válvula.

## Fuera de alcance de este ADR

La question policy (protocolo "Resolvé antes de preguntar") y `/explicar` son ADR-0037, un ADR
independiente — no dependen del mecanismo de módulos de esta ADR. La capa humana del gate de módulos
(bloque `Impacto humano:` en `orchestrator.md`, y los pasos de `integrator`/`architect`) SÍ es de esta
ADR: ver decisión 8.

## Consecuencias

- `docs/modules/<slug>.md` es ahora un artefacto vivo, con historial auditable de qué cambió y cuándo,
  sin depender de que `architect` recuerde actualizar `overview.md` a mano.
- Un paquete que no documenta su impacto y no declara por qué no aplica no puede llegar a `INTEGRATION`
  — pero la válvula asegura que esto nunca se vuelve fricción para un quick-fix real.
- `docs/architecture/overview.md` deja de ser la única fuente de verdad de arquitectura; pasa a ser el
  mapa de alto nivel, con `docs/modules/` como el nivel de detalle por módulo.
