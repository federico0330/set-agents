# Bitácora — 004-adaptive-dispatch

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-03T00:38:55+00:00

[2026-07-26T14:58:25+00:00] orchestrator · done
Cliente: El cliente aprobo el contrato del despacho adaptativo tras dos rondas de challenge independiente: el arnes va a elegir modelo por tarea (nivel rapido/balanceado/frontera) en OpenCode ya, y con eleccion dinamica real en Pi si el estudio de viabilidad da bien.
Ingeniería: USER_APPROVAL contract 1.1.0 (2 challenge rounds: needs-rework -> approve-with-edits, all edits applied). AM-1/AM-2 amendments to 003 logged. Packages P1-dispatch-core -> P2-opencode-lane -> P3-pi-lane(gated T-300). Mode feature budgets.

[2026-07-26T15:00:39+00:00] P1-dispatch-core · implementer · started
Cliente: Un implementador va a construir el nucleo consumible del ruteo: catalogo por niveles, seleccion por riesgo, la CLI de despacho y el cache seguro de autenticacion, con validacion local por tarea.
Ingeniería: PACKAGE_IMPLEMENTATION P1-dispatch-core spawn 1/12 (Claude Fable in-session): T-100 ADR-0006, T-101 catalog v2 single-tier, T-102 tier-aware selection, T-103 SCHEMA 4 + dispatch CLI, T-104 probe cache + fresh-selected, T-105 backlog+suite. Baseline 03939b103ca49f35457529c4cf8f889873ac8068.

[2026-07-27T01:25:41+00:00] P1-dispatch-core · gate-runner · started
Cliente: Una instancia independiente va a repetir todas las validaciones y comprobar que el paquete no salio de su ownership.
Ingeniería: PACKAGE_GATES P1-dispatch-core, gate-runner read-only spawn 2/12: focused suite, harness regressions, setup_models, py_compile, GateSpecs, verify.sh >=120s, CLI matrix, git diff --check, ownership vs 03939b1.

[2026-07-27T01:29:10+00:00] P1-dispatch-core · package-reviewer · started
Cliente: Un revisor independiente va a comprobar que el despacho adaptativo cumple cada criterio aprobado sin romper los invariantes del nucleo de ruteo.
Ingeniería: Panel P1-R1, package-reviewer read-only over 03939b1..WORKTREE, spawn 3/12: AC-00..AC-05 conformance, 003 invariant regressions, AM-1/AM-2 fidelity, tier semantics, structured findings.

[2026-07-27T01:29:10+00:00] P1-dispatch-core · security-auditor · started
Cliente: En paralelo, un auditor va a intentar abusar del descriptor, del cache y del ciclo de vida para conseguir un despacho que no corresponde.
Ingeniería: Panel P1-R1, security-auditor read-only, spawn 4/12: descriptor abuse/tier downgrade, cache poisoning/staleness, abandoned-state abuse, envelope redaction, R3 threat model applies.

[2026-07-27T01:48:42+00:00] P1-dispatch-core · repair-agent · started
Cliente: Un reparador va a cerrar los 14 hallazgos en una sola tanda: arreglar los codigos de salida de la CLI, la auditoria del estado abandonado, la resolucion de contexto, la independencia del reviewer y la cobertura de pruebas.
Ingeniería: PACKAGE_REPAIR R1, repair-agent (Claude in-session) spawn 5/12: reason->exit table (PKG-N01/SEC-002), single-UPDATE abandon+audit (PKG-N02/SEC-A/B), abandoned DDL CHECK+timestamp (PKG-N03), context resolution active-package+freshness+CONTEXT_UNRESOLVED (PKG-N05/N06/SEC-001), independence_verified flag (SEC-A01), uncaught exceptions+latency bounds (SEC-A02), cache dir validation + explain read-onl…

[2026-07-27T09:49:43+00:00] P1-dispatch-core · gate-runner · started
Cliente: Una validacion independiente va a repetir todas las pruebas del paquete reparado antes de entregarlo al revisor delta.
Ingeniería: DELTA_REVIEW R1 gate-runner read-only spawn 6/12: focused 48, harness 2, setup, py_compile incl routing_core, GateSpecs, verify.sh >=300s, CLI matrix, git diff --check, ownership vs 03939b1.

[2026-07-27T09:55:30+00:00] P1-dispatch-core · delta-reviewer · started
Cliente: Un revisor distinto va a reproducir cada uno de los 18 problemas y comprobar que el arreglo sea real, sin reabrir una revision general.
Ingeniería: DELTA_REVIEW R1 delta-reviewer read-only spawn 7/12: decide resolved|open per PKG-N01..N11/SEC-A01..A03 against contract 1.1.0; reproduce each attack; check delta regressions; verify core AM-1/AM-2 untouched.

[2026-07-27T10:01:45+00:00] P1-dispatch-core · orchestrator · done
Cliente: El cerebro del despacho adaptativo quedo aceptado: el arnes ya elige nivel (rapido/balanceado/frontera) y modelo por tarea, con una consulta que pasa de 14 segundos a menos de uno, y cada despacho de escritura queda autorizado y auditado. Tres revisores independientes encontraron 18 detalles y todos se cerraron.
Ingeniería: P1-dispatch-core PACKAGE_ACCEPTED: impl (T-100..T-105) + P1-R1 consolidated repair (18 findings from 2 package-reviewers + 1 security-auditor) + independent gates + delta-review pass. Tests 29->48, verify.sh 146 VERIFY_PASS. Core AM-1/AM-2 confirmed sound by all reviewers. Next: P2-opencode-lane (tier variants + orchestrator decide->spawn doctrine).

[2026-07-27T10:15:12+00:00] P2-opencode-lane · implementer · started
Cliente: Un implementador va a construir el carril que te deja elegir modelo por tarea al delegar en OpenCode: crea las variantes por nivel (rapido/balanceado/frontera) de los cinco roles caros, un chequeo que garantiza que cada variante coincide con el catalogo, y la doctrina para que el orquestador elija la variante segun la decision del ruteo (y degrade con seguridad si no puede).
Ingeniería: PACKAGE_IMPLEMENTATION P2-opencode-lane spawn 1/12 (Claude in-session implementer): T-201 per-role tier tables (models.toml/models_config, activate MODEL_TIERS, lane+subscription validated), T-202 generate.py <role>@<tier> emission + task allowlist + validate() set + build-time variant<->catalog coherence gate + prune verification, T-203 orchestrator decide->variant doctrine + degraded mode + rev…

[2026-07-27T10:35:21+00:00] P2-opencode-lane · gate-runner · started
Cliente: Una instancia independiente va a repetir todas las validaciones del paquete y comprobar que no se salio de su alcance ni rompio nada existente.
Ingeniería: PACKAGE_GATES P2-opencode-lane gate-runner read-only spawn 2/12: unittest discover (harness+routing), build.sh --check incl coherence gate, py_compile incl routing_core, verify.sh drift check, git diff --check, live --route-decide->variant mapping, ownership vs 71abca1.

[2026-07-27T10:43:15+00:00] P2-opencode-lane · package-reviewer · started
Cliente: Un revisor independiente va a comprobar que las variantes por nivel y la doctrina cumplen cada criterio aprobado sin romper el nucleo de ruteo ni los agentes existentes.
Ingeniería: Panel P2-R1 package-reviewer read-only over 71abca1..WORKTREE spawn 3/12: AC-06 variant emission+coherence gate correctness, AC-07 doctrine completeness, AC-08 lifecycle, tier-table/projection fidelity, generate.py set-equality regression, no core/base-agent regressions, structured findings.

[2026-07-27T10:43:15+00:00] P2-opencode-lane · security-auditor · started
Cliente: En paralelo, un auditor va a intentar abusar de la eleccion de variante, del gate de coherencia y de los permisos del coordinador para conseguir un spawn o un modelo que no corresponde.
Ingeniería: Panel P2-R1 security-auditor read-only spawn 4/12: variant-name spoofing/allowlist bypass, coherence gate evasion (projection ambiguity/offline assumption), coord --route-decide/--route-terminal permission scope, degraded-mode as downgrade attack, run_id/review identity abuse, secret redaction; R3 threat model applies.

[2026-07-27T10:54:48+00:00] P2-opencode-lane · repair-agent · started
Cliente: Un reparador va a cerrar tres detalles antes de aceptar: que el orquestador nunca trate un rechazo de seguridad del ruteo como si fuera un simple 'este carril no puede', que la eleccion de variante tenga una unica fuente de verdad, y que un error de configuracion de un rol de al mensaje claro.
Ingeniería: PACKAGE_REPAIR R1 repair-agent (Claude in-session) spawn 5/12: SEC-A01 orchestrator.md degraded-mode must branch on route-decide reason taxonomy (only ok=true off-lane + ROUTING_UNAVAILABLE degrade to base; hard denials AUTHORIZATION_REPLAY/REVIEWER_INDEPENDENCE_UNAVAILABLE/REVIEW_IDENTITY_INVALID/AUTHORIZATION_INVALID/NO_ELIGIBLE_ROUTE/PROVIDER_UNAUTHENTICATED halt/HUMAN_DECISION_REQUIRED); PKG-…

[2026-07-27T11:53:02+00:00] P2-opencode-lane · gate-runner · started
Cliente: Una validacion independiente repite todas las pruebas del paquete reparado antes de entregarlo al revisor final.
Ingeniería: DELTA_REVIEW R1 gate-runner read-only spawn 6/12: unittest 152, build.sh --check incl coherence, py_compile incl routing_core, verify.sh drift, git diff --check, ownership vs 71abca1, doctrine propagation to 3 harnesses.

[2026-07-27T12:32:14+00:00] P3-pi-lane · implementer · started
Cliente: Un implementador va a construir el ultimo tramo: que el arnes pueda delegar tareas al motor Pi eligiendo el modelo exacto de CUALQUIER proveedor por tarea (no solo dentro de una familia), con una instalacion controlada de Pi, un chequeo de salud, y candados para que esos agentes no se desmadren. Es lo que ningun otro runtime permite y ya lo probamos funcionando en vivo.
Ingeniería: PACKAGE_IMPLEMENTATION P3-pi-lane spawn 1/12 (Claude in-session): T-301 ADR-0007 + managed pinned pi install + doctor --harness pi; T-302 minimal pi target generate/install; T-303 set_agents_spawn.py CLI-subprocess spawner (pi --model provider/model --print --mode json --no-session, lifecycle incl crash=>failure, decided-model verification); T-304 spawn guards as flags (fresh ctx, --no-extensions…

[2026-07-27T13:14:18+00:00] P3-pi-lane · gate-runner · started
Cliente: Una instancia independiente repite todas las validaciones del ultimo tramo y comprueba que no rompio nada ni se salio de su alcance.
Ingeniería: PACKAGE_GATES P3-pi-lane gate-runner read-only spawn 2/12: unittest 165, build.sh --check, py_compile incl set_agents_spawn+routing_core, verify.sh drift, git diff --check, ownership vs ced2caa, doctor pi green, openai-codex live decide->spawn->terminal ONLY (Claude quota exhausted -> anthropic via hermetic tests+evidence, no live re-run).

[2026-07-27T13:24:07+00:00] P3-pi-lane · package-reviewer · started
Cliente: Un revisor independiente comprueba que el carril Pi cumple cada criterio aprobado, que el flip de ejecucion es seguro, y que ningun test se debilito.
Ingeniería: Panel P3-R1 package-reviewer read-only over ced2caa..WORKTREE spawn 3/12: AC-09/10/11/11g/12/13 conformance, spawner lifecycle correctness (crash=>failure, decided-model verification), flip safety+fail-closed, probe parser fidelity, model-id map, the 1 deleted test (behavior-change vs weakening), no P1/P2 regressions.

[2026-07-27T13:24:07+00:00] P3-pi-lane · security-auditor · started
Cliente: En paralelo, un auditor intenta hacer que un agente Pi escape sus candados, delegue, corra un modelo no autorizado, o filtre credenciales.
Ingeniería: Panel P3-R1 security-auditor read-only spawn 4/12: guard bypass (--no-extensions/--no-session/read-only allowlist), depth-0/no-delegation escape, decided-model spoof (message.model verification bypass), flip abuse (execute against unverified pi), auth.json token redaction in doctor/probes, crash=>failure integrity, command-injection in pi argv/--append-system-prompt. R3 threat model applies.

[2026-07-27T13:30:55+00:00] P3-pi-lane · repair-agent · started
Cliente: Un reparador cierra los detalles de seguridad antes de aceptar: el mas importante evita que una tarea maliciosa disfrazada de opcion le saque los candados al agente Pi; los demas endurecen el aislamiento y el cierre limpio de cada tarea.
Ingeniería: PACKAGE_REPAIR R1 repair-agent (Claude in-session) spawn 5/12: SEC-A01 HIGH neutralize untrusted task-as-flag (fail closed TASK_LOOKS_LIKE_FLAG or stdin) + hostile-task test; SEC-A02 gate GUARD_TOOLS_CODE_RW behind bash-sandbox story (read-only until green) + --no-context-files unconditional; PKG-N01/SEC-A03 wrap dispatch->spawn->terminal try/finally (no orphan run); SEC-A04 detect modelFallbackM…

[2026-07-27T13:54:31+00:00] P3-pi-lane · gate-runner · started
Cliente: Una validacion independiente repite todas las pruebas del tramo reparado antes del revisor final.
Ingeniería: DELTA_REVIEW R1 gate-runner read-only spawn 6/12: unittest 172, build.sh --check, py_compile, verify.sh drift, git diff --check, ownership vs ced2caa, SEC-A01 hostile-task refusal live openai-codex only.

[2026-07-27T13:54:32+00:00] P3-pi-lane · delta-reviewer · started
Cliente: Un revisor distinto reproduce cada arreglo de seguridad y comprueba que sea real, sin reabrir la revision general.
Ingeniería: DELTA_REVIEW R1 delta-reviewer read-only spawn 7/12: resolved|open per SEC-A01/A02/A04/A05/PKG-N01/N02; reproduce SEC-A01 hostile-task neutralization; check delta regressions; core AM-1/AM-2 + flip untouched.
