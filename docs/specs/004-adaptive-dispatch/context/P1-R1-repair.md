# P1-dispatch-core — paquete de reparación consolidada R1

18 hallazgos únicos de tres revisores independientes (2 package-reviewer + 1 security-auditor) sobre el
diff `03939b1..WORKTREE`. El núcleo AM-1/AM-2 está CONFIRMADO sólido por los tres (no bajar riesgo, no
inyectar facts, no autorizar sin re-probe fresco, SCHEMA-4 fail-closed byte-idéntico, sin fuga de datos).
Todos los defectos están en el borde CLI, el audit trail del estado `abandoned`, la resolución de contexto,
la independencia de reviewer con el catálogo nuevo, y la cobertura. NINGUNO cambia el contrato aprobado;
son reparaciones dentro de AC-00..AC-05. No debilitar tests. Ownership: mismos owned/shared del paquete.

## Reglas de la reparación
- Trazabilidad finding→cambio→verificación en `evidence/P1-repair-R1.md` (tabla como en 003 R1/R2/R3).
- No tocar los 19 comportamientos P1R ni el núcleo AM-1/AM-2 salvo lo que un finding pide explícitamente.
- Correr al cierre: `python3 -m unittest discover -s tests -p 'test_routing.py'`, 2 regresiones HarnessTests,
  `setup_models.py --check`, `py_compile` (incl. routing_core), `./ai/scripts/verify.sh`, `git diff --check`.

## Hallazgos y required_outcome

### BLOQUEANTE
**F01 (high, set_agents_app.py cmd_route_decide ~163)** — `--route-decide` devuelve exit 0/ok=true para TODO
rechazo; la tabla reason→exit está muerta. Es la señal que P2/AC-07 va a consumir para el modo degradado.
→ Mapear: `ok=true`+exit 0 SOLO para decisión ejecutable de writer, decisión de reviewer verificado,
decisión no-ejecutable de otra clase, y `REVIEW_IDENTITY_UNVERIFIED`. `ok=false`+exit 1 para
ROUTING_UNAVAILABLE, FACTS_INCOMPLETE, NO_ELIGIBLE_ROUTE, REVIEW_IDENTITY_INVALID, PROVIDER_UNAUTHENTICATED,
AUTHORIZATION_INVALID, AUTHORIZATION_REPLAY, CATALOG_INVALID, STATE_CONFLICT. Descriptor con risk o
selected_runtime fuera del enum ⇒ validar en el PARSE del descriptor y salir exit 2 ROUTING_INPUT_INVALID
(no llegar al service). Centralizar el mapeo en un helper reusable (así P3 lo hereda). Test CLI del caso
lock (holder BEGIN IMMEDIATE ⇒ exit 1) y de al menos un reason de cada lado.

### ALTOS / MEDIOS de seguridad y datos
**F02 (medium, cmd_route_terminal + store)** — el abandon está implementado como
`try terminal() except STATE_CONFLICT: abandon()`; terminal ya escribió su `_rejection_event` en su propia
unidad de trabajo, así que un abandon EXITOSO deja un `rejected/STATE_CONFLICT` espurio e infla
`exclusion_count`; un failure sobre run inexistente/terminal escribe DOS rejected. → Nuevo
`store.close_run(run_id, outcome)` que en UNA transacción lee el estado y transiciona al destino correcto
(`dispatched`→terminal, `authorized`+failure→abandoned, resto→un solo evento rejected). Un abandon exitoso:
cero rejected. Test de conteo exacto de eventos.

**F03/N05/N06 (medium, _resolve_context_pack ~94-118)** — (a) con `feature_id` explícito se saltea el filtro
de fase ⇒ nombrar una feature BLOCKED/DONE con pack en disco desactiva `CONTEXT_MISSING` (única exclusión
dura que el caller puede voltear — no está sancionado por AM-1); (b) sin chequeo de frescura (spec dice
"existence AND freshness"); (c) `context_present`==`critical_coverage` (sin señal independiente); (d) el
default "exactamente una feature no-terminal" hoy no resuelve (003 PACKAGE_ACCEPTED + 004 PACKAGE_GATES son
dos activas) ⇒ todo decide crítico sin ids cae silencioso a NO_ELIGIBLE_ROUTE. → Aplicar el filtro de fase
no-terminal TAMBIÉN con feature_id; exigir que el paquete sea el `current_package_id` de esa feature (o
status no terminal); implementar frescura (mtime del pack ≥ última mutación del paquete/`updated_at`, stale
⇒ flags false); resolver el default por la feature en banda de ejecución de paquetes; si no se resuelve un
único paquete y la tarea necesita contexto, reason `CONTEXT_UNRESOLVED` distinto de NO_ELIGIBLE_ROUTE.
Emitir en `data` el `(feature_id, package_id, context_ok)` efectivo para auditoría. Tests: feature
BLOCKED/DONE ⇒ flags false; pack stale ⇒ critical_coverage false; abrir SOLO el archivo nombrado cuando
viene feature_id (perf N10).

**F04 (medium, service.route + catálogo)** — repoblar el catálogo con family por modelo (haiku/sonnet/opus)
degradó la independencia de reviewer: con un solo proveedor autenticado, writer=anthropic/sonnet ⇒
reviewer=anthropic/opus (mismo proveedor) con reason_codes vacío; la 003 daba
`REVIEWER_INDEPENDENCE_UNAVAILABLE` fail-closed. La preferencia de proveedor distinto es blanda (sort key),
no exclusión. → Agregar exclusión DURA `REVIEW_PROVIDER_CONFLICT` para role_class review (un reviewer no
comparte proveedor con el writer terminal), restaurando el fail-closed. Test: un solo proveedor autenticado
⇒ reviewer no ejecutable con la razón de independencia.

**SEC-A01 (high, service.route rama unverified + set_agents_app)** — reviewer sin `review_of_run_id` o con
run ajeno rutea a la familia del writer; el envelope verificado y el no-verificado se distinguen solo por
ausencia de un reason code (denylist). → Agregar campo POSITIVO `independence_verified: true|false` en
`data` (true solo cuando hubo writer verificado y pasó exclusión de familia+proveedor). Aditivo, no cambia
AC-03. (La derivación del writer desde el paquete activo se cubre con F03; acá basta el flag + que
unverified nunca marque true.)

**SEC-A02 (medium, cmd_route_decide + cmd_route_terminal + store._transition + parser)** — excepciones sin
capturar rompen el envelope y dejan runs trabados sin auditoría: (a) `context_pack` no-str/absoluto ⇒
TypeError escapa; (b) `--latency-ms` sin cota ⇒ OverflowError deja el run en `dispatched` sin evento; (c)
`--latency-ms` negativo decrementa rollups. → `except (RoutingError, OSError, TypeError, ValueError,
OverflowError)` ⇒ ROUTING_UNAVAILABLE en decide; validar context_pack (isinstance str, no absoluto,
`os.path.commonpath` dentro de ROOT); validar `--latency-ms` a `0 <= n <= 2**31-1` en el CLI ⇒ exit 2
ROUTING_INPUT_INVALID; en `store._transition` capturar `(OverflowError, sqlite3.Error)` con
`_rejection_event` antes de mapear a ROUTING_UNAVAILABLE. Tests por subprocess: latency 2**70 y -5 ⇒ exit 2,
una línea JSON, sin `Traceback`; fallo en `_event` ⇒ evento `rejected` persistido.

**F05 (medium, domain._ObservedTaskFacts.validate)** — la guarda N-1 valida solo `request.required_tools`;
`facts.required_tools` con miembro no-hasheable todavía tira TypeError en `set(facts.required_tools)`. →
Validar que todo elemento de `facts.required_tools` sea str dentro de `validate()` ⇒ FACTS_INCOMPLETE. Test
del lado facts.

**SEC-A03/N09 (medium, catalog._read/_write_probe_cache + service.__init__ + docs)** — el cache no valida el
directorio como el store (`root.is_dir()` sigue symlinks) y el camino simulate (explain) ESCRIBE el cache,
violando el "no mutation" de la 003. → Validar el directorio con la misma disciplina del store (no symlink,
0700, uid) antes de leer/escribir; si no valida ⇒ ignorar cache y probear fresco (nunca crear/chmod ajeno).
En modo simulate/explain el cache es READ-ONLY (lee si existe, no escribe) para preservar explain no-mutante.
Actualizar `docs/architecture/overview.md` (explain ya no es "sin estado"; describir el cache regenerable y
el contrato CLI: modos de routing, exempt-set por modo, tabla reason→exit con REVIEW_IDENTITY_UNVERIFIED,
`--route-decide` de writer es MUTANTE).

### MEDIOS/BAJOS restantes
**F06/N07 (medium, catalog probe cache)** — (a) el root del cache solo se crea en `_connect()`, así que el
carril read-only nunca calienta el cache y paga ~11s por invocación en máquina limpia; (b) el cache guarda
resultados NEGATIVOS por todo el TTL ⇒ un fallo transitorio = 5 min de degradación. → (a) asegurar el root
privado 0700 en composición para que decide/explain read-only puedan cachear (si el root no valida,
degradar a fresh sin crear nada ajeno); (b) cachear SOLO pares positivos; los negativos se re-probean cada
vez. Documentar la política en ADR-0006 Consecuencias. Tests de ambos.

**F09 (low, catalog._read_probe_cache)** — el cache leído no se intersecta con `_configured_models`,
rompiendo la invariante declarada. → Intersectar por par al leer. Aserción en el test de cache.

**F10 (low, service.route cadena elif ~122)** — `TIER_INSUFFICIENT` se evalúa antes que ROLE_INCOMPATIBLE/
TOOLS_MISSING/CONTEXT_MISSING/REVIEW_FAMILY_CONFLICT, enmascarando razones (mismo set de candidatos). →
Mover `TIER_INSUFFICIENT` DESPUÉS de las exclusiones duras.

**N03 (medium, store._create_schema)** — el DDL de `abandoned` no prohíbe una identidad actual ni registra
timestamp de cierre. → `CHECK(state<>'abandoned' OR (actual_route_id IS NULL AND actual_runtime IS NULL AND
actual_provider IS NULL AND actual_model IS NULL AND actual_family IS NULL AND actual_effort IS NULL))` +
timestamp de cierre (relajar el CHECK de orden de `terminal_at` para el caso never-dispatched, o usar
`updated_at` documentado). Sigue en SCHEMA 4 (el bump ya es de este paquete). Test que el CHECK dispara.

**N08 (low, tests test_pi)** — las aserciones son vacuas bajo simulate=True. → Usar tempfile root o agregar
`assertIn('NO_ELIGIBLE_ROUTE', ...)`/`assertIsNone(route_id)`.

**F08/N11 (low, main() detección de modos)** — un valor de modo cadena vacía (`--route-decide ""`) es falsy
y se escapa de la exclusión total, cayendo al menú/help. → Detectar presencia por `is not None`, no
truthiness. Corregir la fila inexacta de la tabla de evidencia (`--route-decide --json --yes` es error de
argparse, no ROUTING_INPUT_INVALID).

**F07/N09 (low, gates.py + _lifecycle_command)** — `v2:python-compile` compila solo `routing.py`; ningún
GateSpec cubre los modos CLI nuevos; `_lifecycle_command` usa `RoutingStore()` hardcodeado sin seam de test.
→ Extender `v2:python-compile` a `routing_core/*.py`; dar seam de root a los comandos de ciclo de vida para
test hermético decide→dispatched→terminal→abandoned via CLI.

**N04 (medium, tests)** — cero cobertura del descriptor `--route-decide` y de la matriz negativa del
catálogo. → Tests herméticos por subprocess: writer/reviewer-unverified/reviewer-verified/docs-rw
(exit/ok/run_id/tier/reasons con valores reales); matriz CATALOG_INVALID (tiers-lista, tier desconocido,
xhigh, effort inválido, anthropic≠medium, runtimes no auditado, duplicado runtime-only).
