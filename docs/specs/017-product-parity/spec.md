# Feature 017 — Product parity: autonomía, evidencia, transparencia, alcance vivo y selección dinámica

- Estado: **Approved** (aprobación explícita del dueño vía plan review, 2026-08-04; decisiones de producto
  registradas en `## Decisiones del usuario`). Origen: auditoría completa del harness contra la visión de
  producto, disparada por la comparación con `gentle-ai`.
- ADRs asociadas: 0025 (autonomía), 0026 (evidencia), 0027 (narración por hito + digest), 0028 (alcance
  vivo), 0029 (probe-manda).

## Visión de producto (palabras del dueño, condensadas)

1. **Cero configuración**: el usuario no instala ni configura nada más allá del install; el harness se
   adapta a los modelos que la herramienta tiene disponibles y elige inteligentemente (caros para
   planificar/spec/review, costo-rendimiento para implementar). Dar de baja/alta una suscripción no debe
   requerir tocar nada.
2. **Autonomía tipo Claude Code**: "le doy una tarea y me trae el problema resuelto" — no frenar por
   credenciales resolubles, no darle comandos al usuario para que corra él, instalar CLIs/MCPs que la
   tarea necesita. Balance con time-to-production de pyme.
3. **Evidencia siempre**: ninguna respuesta "de memoria"; líneas de código, salidas de comandos, docs
   actuales de internet. El orquestador es el PO del harness y domina el prompt engineering hacia sus
   subagentes.
4. **Transparencia sin ruido**: narración entendible por un cliente, pero por hito, no por cada paso
   interno; un digest matinal ("cafecito") generado desde el estado, apto Obsidian/graph.
5. **Continuidad de objetivo**: sesiones nuevas recuperan la idea original; todo cambio de alcance se
   refleja y se consulta ANTES de implementar, en ambas direcciones (usuario→harness y harness→usuario).
6. **Mínimo consumo de tokens** sin que la calidad lo note: máximo jugo a los modelos baratos, los caros
   solo donde rinden.

## Diagnóstico verificado (2026-08-04, exploración con archivo:línea)

1. **Modelos mayormente hardcodeados**: routing dinámico solo para 6/28 roles; probe solo resta del
   catálogo manual (`catalog.py:157`); frontmatter con `model:` literal (`generate.py:415,433,452,486,510`);
   `[subscriptions]` manual rompe el build al cancelar (`models_config.py:286-294`); failover solo lane Pi.
2. **Autonomía auto-neutralizada**: Question policy autoriza frenar por "missing credentials"
   (`orchestrator.md:464`); deploy carve-out frena aunque el usuario nombró la plataforma; `tools.toml` +
   instalación multi-gestor existen (`set_agents_app.py:900-961`) pero son humano-only.
3. **Evidencia ausente en consulta**: `brainstormer.md` sin regla de evidencia; ningún subagente Claude
   Code con WebSearch/WebFetch; context7 apagado + pedir permiso; sin plantilla de spawn-prompt.
4. **Narración todo-o-nada; notas write-only**: 2 bloques por spawn en todos los modos; `BUENOS-DIAS.md`
   manual (se pudrió 2 veces); nadie lee `docs/notas/` al arrancar.
5. **Alcance sin mecanismo**: `verify_spec_hash` solo en init; sin `amend-spec`/`supersede-package`;
   única salida `init --force` destructiva.
6. **Onboarding**: `install.sh` instala los 3 CLIs siempre; `e2e.sh`/`mcp.sh` hardcodeados a OpenCode.

## Decisiones del usuario (registradas, 2026-08-04)

- Prioridad: **todo hoy**, aunque algo quede a medias; fases de doctrina primero, modelos en paquetes.
- Selección de modelos: diseño delegado al harness → se adopta **"el probe manda"**: `models.toml` /
  `routes.v1.toml` NO se borran; se invierten a capa opcional de preferencias/pins/curación. La family
  curada se conserva porque sostiene la independencia writer/reviewer (ADR-0011/0016).
- Autonomía: **"resolver primero, registrar siempre"** — instalar/usar CLIs y MCPs del catálogo sin
  preguntar, registrando con `log-decision`; frenar solo por sudo, secretos inconseguibles y destructivo.
- Narración: **por hito + digest matinal generado + notas leídas al arrancar sesión**.

## Alcance (fases → paquetes)

- **F — Onboarding solo-Claude-Code**: `install.sh --harness`, `build.sh --install --target`, `e2e.sh`
  fallback claude, `set-agents --doctor`.
- **B — Autonomía**: Question policy de credenciales (intentar flujo interactivo del CLI antes de
  frenar), deploy carve-out plataforma-nombrada, prod-pedido vs credencial-inconseguible,
  `--tools-install`/`--mcp-add` expuestos al orquestador (argv-walker estricto, sin sudo), MCP
  discipline encender→usar→apagar sin preguntar, `mcp.sh` multi-harness.
- **C — Evidencia**: regla transversal anti-memoria, WebSearch/WebFetch para roles de análisis,
  `brainstormer` con evidencia, consult con tabla claims→evidencia, skill `spawn-prompt`.
- **D — Narración por hito + digest**: doctrina de hitos, `feature-state.py digest`, hub honesto,
  notas como entrada (`resume-feature` + apertura de sesión sin exigir vault).
- **E — Alcance vivo**: re-verificación de spec hash (aviso en resume/next, bloqueante en
  accept-package), `amend-spec`, `supersede-package`, doctrina de drift bidireccional.
- **A — Selección dinámica** (A1/A2 hoy; C1/B1/B2/C2/D en la semana): autodetección de suscripciones
  con degradación que nunca rompe el build, frontmatter claude con aliases universales u omisión,
  failover cross-lane, rutas sintetizadas desde el probe con tier/family inferidos (curación gana,
  `MODEL_METADATA_INFERRED` auditable, lo inferido solo quita independencia), cobertura por role-class.

El detalle técnico completo (arquitectura, archivos, riesgos) vive en el plan aprobado y en las ADRs
0025-0029 — no se duplica acá.

## Criterios de aceptación

- AC-01 `install.sh --harness claude` instala/configura/autentica SOLO Claude Code y `build.sh --install`
  recibe `--target claude-code`; un usuario solo-Claude queda operativo sin OpenCode/Codex.
- AC-02 `set-agents --doctor` reporta harnesses/CLIs/modelos detectados y qué usará el harness.
- AC-03 Un pedido con plataforma nombrada ("deployá a Vercel") NO dispara pregunta de plataforma: se
  registra con `log-decision` y avanza; credenciales se piden solo tras fallar el flujo interactivo del CLI.
- AC-04 El orquestador puede listar/instalar CLIs del catálogo (`--tools`, `--tools-install <name> --yes`)
  y togglear MCPs del catálogo vía `coord_policy` sin abrir superficie extra (argv-walker estricto; sudo
  siempre delegado al humano con el comando exacto).
- AC-05 MCPs del catálogo (`context7`, `playwright`, `brave-cdp`, `engram`) se encienden/usan/apagan sin
  preguntar, registrando; solo credenciales de terceros preguntan.
- AC-06 Roles de análisis (architect, brainstormer, package-reviewer, security-auditor, debugger,
  product-analyst) tienen WebSearch/WebFetch en Claude Code y webfetch en OpenCode; regla transversal
  anti-memoria en la doctrina compartida; consult produce claims→evidencia.
- AC-07 Existe la skill `spawn-prompt` y el orquestador la referencia como formato obligatorio de spawn.
- AC-08 La narración Cliente/Ingeniería ocurre solo en hitos (inicio de feature/paquete, review/delta,
  bloqueo/inesperado, cierre, fin de turno); los spawns intermedios solo persisten JSONL. Una feature
  chica produce ≤6 bloques.
- AC-09 `feature-state.py digest [--since ...]` regenera `docs/notas/BUENOS-DIAS.md` entre marcadores
  `notas:auto` preservando texto humano; secciones: qué quedó listo / en curso / qué falta / decisiones /
  cola.
- AC-10 `resume-feature` y la apertura de sesión del orquestador leen las notas (`## Qué falta` del hub,
  `## Approach y decisiones` de la feature) sin exigir vault linkeado.
- AC-11 `resume`/`next` avisan `SPEC_DRIFT` si el spec aprobado cambió de hash; `accept-package` bloquea
  con instrucción de pasar por `amend-spec`. `amend-spec` registra path+hash+motivo+actor en
  `spec_amendments[]` sin destruir historia; `supersede-package` deja `done_ready` alcanzable con
  paquetes `accepted|superseded`. `init --force` deja de ser el camino para cambios de alcance.
- AC-12 Con una suscripción dada de baja (probe no la ve) y sin editar TOML: el build completa,
  degrada las celdas afectadas con `WARN degraded`, re-verifica separación writer/reviewer, y con cero
  providers imprime un único mensaje accionable. `[subscriptions]` explícito (`true`/`false`) sigue
  ganando (test inmutable intacto).
- AC-13 Todo frontmatter `model:` del lane claude-code es un alias universal (`sonnet|opus|haiku`) o se
  omite; nunca un id que pueda no existir en la cuenta.
- AC-14 (semana) Un modelo descubierto no curado es elegible para implementer con reason code
  `MODEL_METADATA_INFERRED`, y nunca cuenta como independiente de un writer del mismo vendor-stem.
- AC-15 `bash ai/scripts/verify.sh` verde tras cada paquete; tests inmutables sin ediciones.

## No-objetivos

- No se reescribe la máquina de estados ni el modelo de paquetes.
- No se elimina la curación (`models.toml`/`routes.v1.toml`): se vuelve opcional, no se borra.
- No se agregan providers fuera del closed set de `_PAIR_COMMANDS` (superficie auditada, SEC-001).
- No se toca la tríada de release ni el receipt de integración (feature 016/ADR-0024, recién entregados).
- No se debilita ninguna separación de deberes: reviewers read-only, orquestador no implementa; la
  autonomía nueva amplía QUÉ puede resolverse solo, no QUIÉN aprueba qué.

## Riesgos

- Ampliar `SAFE_ARGV` del orquestador es superficie de permisos: cada allow nuevo con argv-walker
  estricto y test negativo (precedente: `coord_policy.py:62-63`, hallazgo real).
- Degradación de modelos puede romper separación writer/reviewer si se hace ingenua: re-check
  obligatorio post-degradación, fallback a omitir `model:` con warning.
- Relajar frenos de credenciales/prod exige mantener el freno para operaciones destructivas y datos de
  producción: la distinción es "pedido explícito del usuario" vs "decisión propia del harness".
