# Bitácora — 004-adaptive-dispatch

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-07-27T10:15:12+00:00

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
Ingeniería: PACKAGE_REPAIR R1, repair-agent (Claude in-session) spawn 5/12: reason->exit table (PKG-N01/SEC-002), single-UPDATE abandon+audit (PKG-N02/SEC-A/B), abandoned DDL CHECK+timestamp (PKG-N03), context resolution active-package+freshness+CONTEXT_UNRESOLVED (PKG-N05/N06/SEC-001), independence_verified flag (SEC-A01), uncaught exceptions+latency bounds (SEC-A02), cache dir validation + explain read-only + positive-only cache (SEC-A03/PKG-N07), CLI+catalog test matrix (PKG-N04/N08), docs+GateSpec (PKG-N09/N11), perf targeted open (PKG-N10).

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
Ingeniería: PACKAGE_IMPLEMENTATION P2-opencode-lane spawn 1/12 (Claude in-session implementer): T-201 per-role tier tables (models.toml/models_config, activate MODEL_TIERS, lane+subscription validated), T-202 generate.py <role>@<tier> emission + task allowlist + validate() set + build-time variant<->catalog coherence gate + prune verification, T-203 orchestrator decide->variant doctrine + degraded mode + reviewer run_id sourcing + coord permission surface (coord_policy.py SAFE + oc_permissions), T-204 hermetic lane lifecycle + worker-death + variant/prune/coherence tests. Baseline 71abca1.
