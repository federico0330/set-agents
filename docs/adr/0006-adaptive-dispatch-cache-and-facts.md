# ADR-0006 — Despacho adaptativo: derivación híbrida de facts y cache de probes

- Estado: Aceptado (2026-07-26, decisión del usuario; ver `decisions-log` slugs `am1-hybrid-facts` y
  `am2-probe-cache-fresh-selected`). Enmienda acotada a la feature 003 (contrato 2.0.0) y a ADR-0005.
- Contexto: feature 004-adaptive-dispatch, contract 1.1.0.

## Contexto

La 003 dejó un núcleo de ruteo confiable sin consumidores. Para que el orquestador lo consuma por spawn
hacen falta dos cosas que la 003 prohibía en su forma literal: (1) que el caller aporte la clase de la
tarea, y (2) que la decisión no pague ~14 segundos de probes de autenticación por invocación.

## Decisión AM-1 — derivación híbrida de facts, risk solo-subir

Por campo de `ObservedTaskFacts`, la fuente es:

| Campo | Fuente | Regla |
|---|---|---|
| `role` | descriptor, validado contra roster | inexistente ⇒ `FACTS_INCOMPLETE` |
| `operation` | derivado | `inspection` si task_class=inspection, si no `change` |
| `task_class` | **descriptor (única intención estructural)** | enum cerrado |
| `read_write` | derivado de capability del rol | `write` ⇔ capability `code-rw` |
| `required_tools` | derivado de capability | code-rw ⇒ (read,shell,write); resto ⇒ (read,) |
| `criticality` | derivado | task_class si ∈ CRITICAL, si no "" |
| `risk` base | derivado | CRITICAL o incident ⇒ high; resto low |
| `risk` efectivo | base ⊕ descriptor | descriptor SOLO puede subir (max); menor se ignora |
| context flags | derivado del context-pack del paquete activo (`feature_id`/`package_id` del descriptor o feature activa) | pack existente ⇒ present/coverage true; sin paquete resoluble ⇒ false (conservador) |
| `selected_runtime` | descriptor opcional, default de composición | enum cerrado |
| `facts_version`/`observed_at`/`_scope` | emisor interno (003, sin cambios) | — |

El descriptor es intención no confiable; la degradación respecto de la 003 es exactamente una: `task_class`
viene del orquestador. Todo lo demás se deriva o solo puede endurecer.

## Decisión AM-2 — cache de probes filtering-only + re-probe del seleccionado

- **Ubicación**: `<root del store routing-v2>/probe-cache.json` (el root fijo de ADR-0005, derivado de
  `pwd`, nunca de `$SET_AGENTS_STATE` ni de `$HOME`). Modo 0600 bajo el root 0700.
- **Clave de invalidación**: `(uid, sha256(dump canónico de models.toml [catalog]+[routing]), par)`.
  Cambio de catálogo/config o de uid ⇒ cache inválido entero.
- **TTL**: 300 segundos por escritura completa. `--fresh-probes` lo saltea.
- **Escritura**: atómica (`tmp` + `rename`), contenido = únicamente `par → lista de modelos` ya
  intersectada con el catálogo canónico (redactado por construcción; jamás output crudo de un CLI).
- **Lectura**: clave distinta, JSON corrupto, tipo inesperado, o mode/dueño incorrecto ⇒ se ignora
  fail-closed y se probea fresco. El directorio raíz se valida con la MISMA disciplina que el store
  (`lstat`, no symlink, 0700, dueño = uid actual) antes de leer o escribir — no basta `Path.is_dir()`,
  que sigue symlinks (repair R1, SEC-A03). Cada par leído se re-intersecta en el momento con
  `_configured_models` (repair R1, F09): incluso un documento con clave coincidente nunca puede ampliar
  el set más allá del catálogo vigente.
- **Autoridad**: el cache SOLO filtra candidatos. Antes de cualquier autorización durable de writer, el
  par seleccionado (y el del fallback, si difiere) se re-probea FRESCO; si el probe fresco no confirma el
  modelo, la decisión es `PROVIDER_UNAUTHENTICATED`. Un cache stale puede, a lo sumo, hacer considerar un
  candidato que el re-probe va a rechazar — nunca autorizar contra un proveedor no verificado, y nunca
  ampliar el set de modelos más allá de models.toml.
- **Política de negativos (repair R1, F06)**: el documento de cache SOLO contiene pares POSITIVOS
  (`par → modelos`); un par cuyo probe falló (transitorio o no) simplemente está AUSENTE del documento —
  nunca se persiste un negativo. En cada lectura, todo par ausente del documento cacheado se re-probea
  FRESCO en el acto (nunca se asume "no disponible" por el resto del TTL) y el resultado combinado
  (cacheados positivos + recién probados) se vuelve a escribir. Consecuencia: un fallo transitorio cuesta,
  como máximo, un reintento por invocación — nunca los 300s completos de degradación que costaba cachear
  el negativo. El costo es simétrico al beneficio: un par persistentemente no autenticado se reprueba en
  cada invocación (mismo costo que sin cache para ESE par), mientras los pares ya confirmados siguen
  sirviéndose del cache.
- **Modo simulate/explain — solo lectura (repair R1, SEC-A03)**: la composición de `RoutingService`
  siempre intenta crear/validar el directorio raíz privado del cache (nunca adoptar/chmodear uno ajeno —
  `RoutingStore.ensure_cache_root`), incluso en modo simulate, para que el carril read-only (explain,
  decide de rol no-writer) pueda SERVIRSE de un cache calentado por una decisión real previa. Pero ese
  mismo carril nunca ESCRIBE `probe-cache.json` (`cache_write=False`): lee si hay un documento válido,
  y si no, prueba fresco en memoria sin persistir — preservando el contrato "explain no muta" de la 003
  incluso cuando su probe interno corre subprocesos.

## Consecuencias

- Decisiones read-only con cache caliente: <1s (presupuesto informativo, no gating). Autorizaciones de
  writer pagan el re-probe del par elegido (~segundos), a cambio de cero autorizaciones stale.
- El archivo de cache es estado regenerable: borrarlo solo cuesta un probe completo.
- ADR-0005 queda enmendado en su "no cache until profiling": el perfil llegó (14,5s/decisión medidos en
  P1R, N-3) y la clave de invalidación está definida acá.
- La 003 queda enmendada en "probed fresh per invocation": vale para la autorización (fresh-selected),
  no para el filtrado de candidatos.
- (repair R1) Explain deja de ser "sin estado" en sentido literal: puede LEER `probe-cache.json` (el
  único archivo que puede tocar) para servir una decisión simulada sin pagar el probe completo; nunca
  escribe ese archivo ni crea/muta la base SQLite. `docs/architecture/overview.md` documenta esta
  distinción explícitamente.
