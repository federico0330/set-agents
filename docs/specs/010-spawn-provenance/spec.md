# Feature 010 — spawn-provenance, contract 1.0.0

Status: `SPEC_CHALLENGE` corrió cuatro veces en total: dos heredadas del intento como 006-P3.1 (ver "Origen"
abajo), y dos más sobre este documento ya reestructurado — tercera: 1 bloqueante (atestación de hash de 006
rota por la propia reestructuración) + 3 medios + 3 bajos, todos aplicados; cuarta: verificación,
`ready_for_user_approval`, 5 bajos aceptados como deuda documentada, sin bloqueantes.

## Origen

Este trabajo se intentó abrir primero como "P3.1" de `006-execution-graph` (conectar spawns al grafo de
ejecución — el hueco que la segunda pasada de `SPEC_CHALLENGE` de esa feature dejó reservado a propósito:
*"`--caused-by-spawn` sale de P3... queda registrado como candidato a un P3.1 futuro"*). Dos pasadas de
`spec-challenger` corrieron sobre esa versión (contract 1.3.0 de 006): la primera encontró 9 hallazgos
bloqueantes (mecánicos, todos aplicados); la segunda encontró que **006 no puede alojar este trabajo en
absoluto** — `data["acceptance_criteria"]` a nivel feature de 006 quedó congelado en `AC-20..AC-29` desde su
propio `init`, el único comando que escribe esa lista, que se niega a re-ejecutar sin `--force` destructivo
(borraría el historial de P3 ya aceptado). Decidido con el usuario: este trabajo se abre como su propia
feature en vez de forzar una capacidad nueva de extensión de ACs en `feature-state.py` (que sería alcance
real de mantenimiento del arnés, no parte de conectar spawns al grafo). `docs/specs/006-execution-graph/
spec.md` vuelve a su contrato 1.2.0 tal como quedó al aceptar P3, sin editar — el texto de esa feature
("no spawn nodes in P3") era exacto para su propio alcance y no necesita reescribirse por el trabajo de otra
feature sobre código compartido.

Las ACs de abajo son las mismas AC-30..AC-34 del intento anterior, renumeradas AC-01..AC-05 (convención de
toda feature nueva) con las correcciones de ambas pasadas ya aplicadas — no se repite el desafío desde cero
porque ambas pasadas ya auditaron este contenido exhaustivamente; ver `## Historial de challenge` para el
detalle de qué encontró cada una.

Depends on: `006-execution-graph` (P3-graph-view, `accepted`) — este paquete extiende el mismo `graph`
subcommand y el mismo `_add_package_findings`/`render_mermaid` que P3 ya construyó, en `ai/scripts/
feature-state.py`. No reimplementa nada de 006, y no cambia su contrato ni sus ACs. Design: **ADR-0014**
(nueva; documenta por qué `spawn_id` no reemplaza a `run_id`, y supersede en parte D1/D3 de **ADR-0013**,
que queda `Accepted` con una nota `Superseded in part by ADR-0014` en su propio status line y en
`docs/adr/README.md` — nunca editada de otra forma, per la regla de ese índice de nunca reescribir
retroactivamente una decisión. ADR-0014 también deja una frase registrando el rename: el trabajo que
ADR-0013 D3 difiere como "P3.1" es esta feature, `010-spawn-provenance`, para que las referencias que ya
existen en el repo — `docs/adr/0013-execution-graph-view.md`, la nota de decisión
`2026-07-30 graph-d04-degradation-edge-cases-deferred.md` — resuelvan sin arqueología).

## Contexto

Un nodo de spawn sin edge no es todavía la cadena de proveniencia navegable que motivó este trabajo, pero
compra dos cosas hoy: el gasto de spawns de un paquete se vuelve visible al lado del paquete al que
pertenece en el mismo grafo que ya muestra sus findings/reviews/repairs (hoy invisible del todo), y
`spawn_id` queda acuñado como la clave de join que el edge diferido va a usar cuando exista una razón real
para tocar doctrina en los 3 runtimes — sin esa clave, ese trabajo futuro tendría que resolver primero el
mismo problema de identidad que esta feature ya cierra. Lo que explícitamente no compra todavía: ningún
finding es navegable hasta el spawn que lo causó — eso sigue exactamente donde estaba antes de esta feature.

## Historial de challenge (heredado del intento como 006-P3.1)

**Primera pasada** — `revision_required`, 9 bloqueantes + 6 medios + 3 bajos. Uno era decisión de producto
(si `--caused-by-spawn`/su edge debían entrar), resuelto con el usuario: **salen del alcance**, otra vez, por
la misma razón que la primera vez que se difirieron — sin cambio de doctrina en los 3 runtimes, el flag nunca
tendría un llamador real, y los nodos de spawn quedarían como islas sin conexión en cualquier grafo real. El
resto (guard de `replayed()` faltante en `record-spawn`, id corrido un lugar respecto al precedente de
`panel_id`, label del nodo sin especificar, ausencia de ADR, cobertura de test vacía, etc.) se aplicó
mecánicamente sin volver a preguntar.

**Segunda pasada** — `revision_required`, 5 bloqueantes + 3 medios + 6 bajos. El bloqueante real: **el hogar
mismo del paquete** (`create-package --ac AC-30` fallaría contra `006-execution-graph.json`, ver "Origen"
arriba) — resuelto con el usuario abriendo esta feature nueva. Los demás, todos mecánicos y ya corregidos en
las ACs de abajo:

- El guard de `replayed()` tiene que ser la **primera** sentencia del updater, no solo "antes de acuñar el
  id" — entre medio está el chequeo de presupuesto de spawns, que puede bloquear la feature entera si un
  reintento lo dispara de nuevo. Mismo lugar y motivo que `cmd_start_review_panel` ya documenta.
- Una implementación ingenua (`len(spawns)+1` en vez del contador `attempts["spawns"]`) pasaría toda la
  cobertura propuesta sin violar ninguna aserción, mientras rompe el caso que el propio AC de minteo nombra
  explícitamente (un paquete que ya tenía spawns antes de esta feature, como el propio P3 de 006, con
  `attempts.spawns: 8` y sin lista `spawns[]`) — cobertura ahora explícita para ese caso.
- El rechazo de `spawn_id` duplicado es, igual que el caso "sigue bloqueando" del fix de `blockers`,
  alcanzable solo por fixture (un `spawn_id` no lo provee ningún llamador, solo lo acuña el propio comando) —
  dicho explícitamente en vez de dejarlo implícito.
- `compact_package()` gana `"spawns": []` en su esquema base; el camino `setdefault` sobre un paquete que
  carece de la clave (todo paquete existente hoy) necesita su propia aserción de fixture, no solo prosa.
- La contradicción "no edita ADR-0013" + "queda linkeado desde 0013" se resuelve citando exactamente lo que
  el propio índice de ADRs prescribe: 0013 no se reescribe en su contenido, pero su status line y su fila en
  `docs/adr/README.md` sí ganan la nota de supersesión parcial — eso es lo que el índice pide, no una
  excepción a su regla.
- Errores de cita (el literal del f-string partido por un salto de línea, el nombre del test partido en dos
  líneas) corregidos, manteniendo cada uno en una sola línea.

## Alcance explícitamente excluido

- **`--caused-by-spawn` y el edge que produciría.** Diferido una segunda vez, misma razón que la primera:
  sin cambio de doctrina en los 3 runtimes no hay un llamador real, y el flag nacería ejercitado solo por
  fixtures sintéticos — exactamente el defecto que la primera pasada de challenge sobre este mismo intento
  midió y rechazó. El nodo `spawn` de AC-02 queda sin ningún edge en esta feature: inventario visible, no
  una cadena de proveniencia navegable. Se retoma cuando exista una razón real para tocar la doctrina de los
  3 runtimes, no antes.
- **Un comando genérico para extender `acceptance_criteria` de una feature ya inicializada.** Es la
  capacidad que "Origen" describe como alcance real de mantenimiento del arnés, no de esta feature. Queda
  nombrado como candidato a un paquete futuro propio, no inventado acá para desbloquear este trabajo.
- **D-07/D-08** (deuda de `docs/notas/decisiones/2026-07-30 graph-d04-degradation-edge-cases-deferred.md`,
  que nombraba "un P3.1 futuro o cuando se implemente `--caused-by-spawn`" como su hogar natural). Con el
  flag diferido otra vez, ninguno de los dos disparadores ocurrió — quedan fuera de esta feature también,
  sin nuevo disparador nombrado.

## AC-01..AC-05

- **AC-01** — `record-spawn` (`ai/scripts/feature-state.py`) mints a deterministic, package-scoped
  `spawn_id`. El guard de idempotencia va **primero**, antes de cualquier mutación o evaluación de
  presupuesto — mismo lugar y motivo que `cmd_start_review_panel`'s `replayed()` guard (un reintento con
  `--event-id` que llega después de que el spawn real ya se registró no debe volver a incrementar el
  contador de presupuesto ni acuñar un segundo id). Recién después: `attempts["spawns"] += 1` (ya existente),
  luego `spawn_id = f"SPAWN-{attempts['spawns']:03d}"` (literal completo, sin salto de línea) — de modo que
  el primer spawn de cualquier paquete es `SPAWN-001`, siempre derivado del contador, nunca de
  `len(package["spawns"])`: un paquete que ya tenía spawns registrados antes de esta feature (el propio P3
  de 006, `attempts.spawns: 8`, sin clave `spawns`) continúa el mismo contador — su próximo spawn es
  `SPAWN-009`, no `SPAWN-001`. `compact_package()` gana `"spawns": []` en su esquema base — puramente
  aditivo, mismo precedente ya en el código para `late_reviews` (el propio comentario del código dice "nine
  state files on disk predate it"; hoy el árbol tiene ocho — `002` a `009` —, la cifra exacta no importa, el
  precedente sí: toda lectura usa `.get()`, sin backfill). `record-spawn` sobre un paquete que carece de la clave
  la crea vía `setdefault` en el primer uso. El id se persiste en una entrada de primera clase en
  `package["spawns"]` (`spawn_id`, `role`, `purpose`, `client`, `tech`, `at`) y se espeja como clave nueva
  `spawn_id` en la metadata del evento de historia `record-spawn` (única adición a esa forma; nada existente
  cambia). Un rechazo de `spawn_id` duplicado existe como defensa en profundidad contra un contador
  desincronizado — alcanzable solo por fixture, ya que ningún llamador provee el id, y se documenta como tal
  en vez de implicar que hay un camino de CLI real hacia él.
- **AC-02** — el subcomando `graph` (construido por 006-P3-graph-view, `accepted`; código compartido, sin
  mecanismo de ownership que sobreviva a la aceptación de un paquete) gana un tipo de nodo `spawn`,
  construido desde `package["spawns"]`. Esto extiende, sin editarlo, el inventario que 006's AC-22 declaró
  para su propio alcance (P3 no tenía nodos de spawn — afirmación exacta para lo que P3 construyó; esta
  feature agrega un tipo de nodo nuevo sobre el mismo mecanismo, no reescribe esa afirmación histórica). Un
  paquete sin clave `spawns` (todo paquete que precede a esta feature) renderiza sin nodos de spawn, nunca un
  error — misma postura que la feature 006 ya estableció para historia legada sin `--commit`. El label lleva,
  como mínimo, `spawn_id` y `role`; cuando `purpose` está vacío (el default del CLI), el label lo omite en
  vez de renderizar un segmento vacío. **Este nodo no tiene ningún edge** en esta feature: `GRAPH_EDGE_TYPES`
  no se toca (sigue en exactamente cinco miembros) y nada conecta un nodo de spawn con ningún otro — es
  inventario visible, no una cadena de proveniencia navegable (ver "Alcance explícitamente excluido"). El
  test existente `test_graph_never_emits_spawn_nodes_and_survives_legacy_fixtures_without_commit`
  (`tests/test_harness.py:6004`) fijaba, para el alcance de P3 de 006, que ningún id de nodo empieza con
  `spawn_` — afirmación exacta entonces, falsa desde esta AC. Se renombra y su comentario se repunta a la
  invariante que sigue siendo cierta (un paquete **sin** `spawns[]` sigue sin nodos de spawn; no "los nodos
  de spawn nunca existen"), mismo tratamiento que AC-28 de 006 le da a cada uno de sus grupos de aserciones.
- **AC-03** — esta feature no hace **ningún** cambio de doctrina del orquestador en ninguno de los tres
  runtimes: `Global/_canonical/agents/orchestrator.md` y sus tres copias generadas se declaran
  `--read-only-path Global/**` en el propio paquete (el único lugar donde ese flag existe hoy en el CLI —
  `create-package`; no en `update-package`), lo que le da a `check-owned-paths.py` una señal distinta y
  nombrada (`read_only_violations`), no una violación de ownership genérica después del hecho. Ownership
  positivo (lo que el paquete sí escribe, nombrado explícitamente): `ai/scripts/feature-state.py` y su
  gemelo `PROYECTO/ai/scripts/feature-state.py` (el segundo es la plantilla — `build.sh --check` compara
  `PROYECTO/ai/scripts/<name>` contra `ai/scripts/<name>` y falla `SELF_SCAFFOLD_DRIFT` ante cualquier
  diferencia; se edita la plantilla primero), `tests/test_harness.py`, `docs/adr/0014-*.md` (nueva),
  `docs/adr/README.md` (fila nueva + nota de supersesión parcial en la fila de 0013 — requerida, no
  opcional: `tests/test_harness.py` ya exige una fila por archivo de ADR y ningún link colgante),
  `docs/specs/010-spawn-provenance/**`, el archivo de estado de esta feature, `ai/state/STATUS.md`, los dos
  `.jsonl` de logs, `docs/notas/**`. **`docs/specs/010-spawn-provenance/spec.md` no se edita después del
  `init`**: `verify_spec_hash` solo corre dentro de `cmd_init`, ningún gate lo re-verifica después, y editar
  un spec ya inicializado rompe su atestación en silencio — exactamente lo que le pasó a 006 durante la
  reestructuración de este mismo contrato (reparado, ver "Historial de challenge"). Declarar el path como
  owned cubre evidencia/contexto agregados durante la implementación, nunca el propio `spec.md`.
- **AC-04** — `done_ready()` deja de tratar una lista `blockers` no vacía como descalificante por sí sola:
  aplica el mismo filtro que `summarize_feature()` ya usa en este mismo archivo (`not b.get("resolved_at")`,
  el chequeo por falsy — no "clave ausente", porque un `"resolved_at": null` escrito a mano tiene que seguir
  contando como sin resolver). Una feature cuyos bloqueos tienen todos `resolved_at` puede llegar a `DONE`;
  una con aunque sea uno sin resolver sigue sin poder. Esto **supersede explícitamente** dos decisiones ya
  registradas que nombraron este mismo hueco sin repararlo (`docs/notas/decisiones/2026-07-28
  una-feature-bloqueada-y-reabierta-no-puede-llegar-nunca-a-done.md`, `docs/notas/decisiones/2026-07-29
  done-ready-does-not-filter-resolved-blockers.md`) — registrado con su propio `log-decision`, no
  sobreescrito en silencio. **Tensión nombrada, no implícita**: como `block_with_reason`/`cmd_fail_task`
  siempre ponen `phase = "BLOCKED"` y `cmd_reopen` hace `setdefault` de `resolved_at` sobre todo bloqueo sin
  discriminar, la rama "sigue bloqueando" de este fix no es alcanzable hoy por ningún camino de CLI real —
  `LEGAL_TRANSITIONS["BLOCKED"] = set()` significa que una feature con un bloqueo sin resolver solo puede
  estar en `BLOCKED`, desde donde `DONE` nunca fue legal de todos modos. La cobertura de esa rama es
  necesariamente solo por fixture (un dict de estado armado a mano), no una secuencia de llamadas alcanzable
  vía CLI, y el AC lo dice en vez de sugerir lo contrario. Es un fix de corrección sobre lógica ya
  entregada, no una capacidad nueva, y no cambia qué significa `blockers` ni cómo las entradas ganan
  `resolved_at`. **Distinción explícita con el comando de extensión de ACs excluido más arriba**: éste es
  un fix de una línea sobre lógica ya entregada, con sujeto real en vivo hoy (`005-portable-harness`,
  `INTEGRATION`, 2 blockers, los dos con `resolved_at`) — el comando de extensión de ACs sería, en cambio,
  una **capacidad nueva** con su propia superficie de contrato (qué puede agregar, cuándo, quién). Esa
  diferencia, no el archivo que cada uno toca, es lo que separa lo que entra acá de lo que se excluye.
- **AC-05** — cobertura de regresión para AC-01..AC-04, cada aserción falsificable (nunca un chequeo que
  pasa vacío):
  - determinismo del minteo: `SPAWN-001` primero, secuencial después, **y** un fixture con
    `attempts["spawns"]` ya no-cero y sin clave `spawns` acuña el **siguiente** valor del contador (ej.
    `SPAWN-009`), nunca `SPAWN-001` — distingue explícitamente el contador de `len(spawns)+1`;
  - el guard de replay: un `--event-id` reintentado produce exactamente una entrada en `spawns[]`, sin
    `spawn_id` duplicado, sin evento de historia fantasma;
  - el rechazo de `spawn_id` duplicado disparando contra un fixture con estado desincronizado a propósito;
  - presencia, id y contenido del label del nodo `spawn` para un fixture con `spawns[]` poblado;
  - un fixture de paquete sin clave `spawns` sigue produciendo un grafo estructuralmente válido con cero
    nodos de spawn (mismo tratamiento que la feature 006 ya usa para historia legada sin `--commit`) — el
    test existente `test_graph_never_emits_spawn_nodes_and_survives_legacy_fixtures_without_commit` se
    renombra y su comentario se repunta a esta invariante exacta, per AC-02;
  - las dos ramas de `done_ready()`: todo-resuelto-no-bloquea vía una secuencia de llamadas real, y
    sigue-bloqueando vía fixture (per la propia salvedad de AC-04);
  - una aserción de `check-owned-paths.py` que `Global/**` está declarado `read_only_paths` y que una
    violación sintética contra ese path se reporta distinta de una violación de ownership genérica;
  - `record-spawn` sobre un dict de paquete que carece de la clave `spawns` (fixture de paquete legado) crea
    la lista vía `setdefault` sin levantar.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · `check-owned-paths.py`. Test count rises,
never falls, y ninguno se skipea.
