# Bitácora — 014-model-preference-policy

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-19T18:30:21+00:00

[2026-08-02T15:04:27+00:00] spec-challenger · started
Cliente: Un desafiador independiente esta revisando el contrato de politica de preferencia de modelos antes de pedirte la aprobacion final: busca contradicciones, huecos y decisiones de producto sin definir.
Ingeniería: SPEC_CHALLENGE 014: read-only challenge of contract 3.1.0 against post-015 tree before USER_APPROVAL.

[2026-08-02T22:07:53+00:00] package-planner · started
Cliente: Con tu aprobacion del contrato de politica de modelos, un planificador lo esta partiendo en paquetes de trabajo.
Ingeniería: PACKAGE_PLANNING 014: decompose contract 3.2.0 (9 ACs, 6 live-effect tiered roles) into coherent packages.

[2026-08-02T23:19:16+00:00] P1-model-preference-policy · implementer · started
Cliente: Un implementador construye la politica de preferencia de modelos: el sistema aprende que clase de rol es cada agente (decision, construccion, revision) y sesga que proveedor prefiere cada clase, con efecto real inmediato para seis roles.
Ingeniería: PACKAGE_IMPLEMENTATION 014-P1 (AC-01..09): role-class resolver, sibling config atomic writer + CLI, sort-key position 3, RouteDecision.bias_class observability, ADR-0018. Runs AFTER 016-P2 accepted (shared service.py/test_routing/set_agents_app now clear). No build.sh/verify.sh during development (staging race rule).

[2026-08-02T23:49:29+00:00] P1-model-preference-policy · gate-runner · started
Cliente: Con los dos implementadores terminados, un unico verificador corre todas las pruebas del proyecto en orden, sin carreras.
Ingeniería: PACKAGE_GATES 014 + PACKAGE_TESTING 016-P1: full discover, verify.sh, build.sh --check/--diff, git diff --check, serialized single-runner per build-staging race decision.

[2026-08-02T23:59:53+00:00] P1-model-preference-policy · package-reviewer · started
Cliente: Un revisor independiente lee toda la politica de preferencia de modelos de punta a punta contra el contrato aprobado.
Ingeniería: PACKAGE_REVIEW 014: read-only vs contract 3.2.0; sort-key position, resolver partition, config surface, observability, ADR-0018; targeted tests only.

[2026-08-02T23:59:53+00:00] P1-model-preference-policy · security-auditor · started
Cliente: Un auditor revisa que el sesgo de preferencia no pueda debilitar la independencia de los revisores ni abrir una via de inyeccion por el archivo de configuracion.
Ingeniería: PACKAGE_REVIEW 014: security-auditor read-only on sort-key placement vs REVIEWER_INDEPENDENCE, _model_preference internal-marker injection, TOML parsing fail-closed, atomic writes.

[2026-08-03T00:08:38+00:00] P1-model-preference-policy · finding-verifier · started
Cliente: Antes de reparar, un verificador intenta refutar los ocho hallazgos del panel de la politica de modelos.
Ingeniería: FINDING_VERIFICATION 014: refute/uphold SEC14-01, RF14-01..07 with live reproduction where claimed.

[2026-08-03T00:13:23+00:00] P1-model-preference-policy · repair-agent · started
Cliente: Un reparador cierra en una pasada los ocho detalles confirmados de la politica de modelos: errores que escapaban sin mensaje claro, un archivo editado a mano que se corrompia, la cobertura del camino real de produccion y dos textos de documentacion imprecisos.
Ingeniería: PACKAGE_REPAIR 014 R1: except clauses (show/route-explain), dedicated MODEL_PREFERENCE_INVALID handling in route-decide, production-plumbing test with populated STATE_DIR, service-level role_override + AC-04e tests, full-doc validation before serialize (set AND role-override paths), pop marker in __init__, log-decision for AC-01i deviation. One record-repair call.

[2026-08-03T00:35:25+00:00] P1-model-preference-policy · delta-reviewer · started
Cliente: Un revisor distinto verifica que los ocho arreglos sean reales y esten bien acotados, sin reabrir la revision general.
Ingeniería: DELTA_REVIEW 014 R1: verify except-clause mappings, production-plumbing test bites, full-doc validation both write paths, marker pop, deviation durably recorded.
