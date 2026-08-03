# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-03T00:38:55+00:00

## Features

| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |
|---|---|---|---|---|---|---|---|---|---|---|
| 002-adaptive-pi-orchestration | feature | BLOCKED | P1-routing-core (repair_required) | 0/1 | 12/12 | 2/2 | 5 | HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles… | - | 2026-07-24T16:16:04+00:00 block |
| 003-trusted-routing-pi-runtime | feature | DONE | P1R-trusted-routing (accepted) | 1/1 | 16/16 | 3/3 | 0 | - | - | 2026-07-29T17:13:45+00:00 transition |
| 004-adaptive-dispatch | feature | DONE | P3-pi-lane (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-27T14:04:38+00:00 transition |
| 005-portable-harness | feature | DONE | P3-tui (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-30T16:16:18+00:00 transition |
| 006-execution-graph | feature | PACKAGE_ACCEPTED | P3-graph-view (accepted) | 1/1 | 9/12 | 1/2 | 0 | - | INTEGRATION | 2026-08-02T14:44:35+00:00 record-spawn |
| 007-quota-visibility | feature | DONE | P3-correct-record (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 008-dynamic-selection | feature | DONE | P1-uninterrupted-delegation (accepted) | 1/1 | 6/12 | 1/2 | 0 | - | - | 2026-08-02T14:53:39+00:00 transition |
| 009-self-application | feature | DONE | P3-panel-integrity (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 010-spawn-provenance | feature | PACKAGE_ACCEPTED | P1-spawn-provenance (accepted) | 1/1 | 11/12 | 1/2 | 0 | - | INTEGRATION | 2026-08-02T14:44:35+00:00 record-spawn |
| 011-quota-failover | feature | BLOCKED | P1-quota-failover (package_gates) | 0/1 | 3/12 | 0/2 | 0 | HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está v… | - | 2026-07-30T17:04:39+00:00 block |
| 012-discovered-inventory | feature | DONE | P1-discovered-inventory (accepted) | 1/1 | 8/12 | 1/2 | 0 | - | - | 2026-08-02T15:00:53+00:00 transition |
| 013-pi-interactive-target | feature | DONE | P1-pi-interactive-target (accepted) | 1/1 | 9/12 | 1/2 | 0 | - | - | 2026-08-02T22:40:39+00:00 transition |
| 014-model-preference-policy | feature | DONE | P1-model-preference-policy (accepted) | 1/1 | 7/12 | 1/2 | 0 | - | - | 2026-08-03T00:38:12+00:00 transition |
| 015-anthropic-dispatch-parity | feature | DONE | P1-anthropic-dispatch-parity (accepted) | 1/1 | 0/12 | 1/2 | 0 | - | - | 2026-08-01T22:46:55+00:00 transition |
| 016-audit-debt-repayment | feature | DONE | P1-harness-debt (accepted) | 2/2 | 10/12 | 1/2 | 1 | - | - | 2026-08-03T00:02:59+00:00 transition |

## Quick-fixes recientes

- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

[2026-08-03T00:35:25+00:00] P1-model-preference-policy · delta-reviewer · started
Cliente: Un revisor distinto verifica que los ocho arreglos sean reales y esten bien acotados, sin reabrir la revision general.
Ingeniería: DELTA_REVIEW 014 R1: verify except-clause mappings, production-plumbing test bites, full-doc validation both write paths, marker pop, deviation durably recorded.

[2026-08-03T00:13:23+00:00] P1-model-preference-policy · repair-agent · started
Cliente: Un reparador cierra en una pasada los ocho detalles confirmados de la politica de modelos: errores que escapaban sin mensaje claro, un archivo editado a mano que se corrompia, la cobertura del camino real de produccion y dos textos de documentacion imprecisos.
Ingeniería: PACKAGE_REPAIR 014 R1: except clauses (show/route-explain), dedicated MODEL_PREFERENCE_INVALID handling in route-decide, production-plumbing test with populated STATE_DIR, service-level role_override + AC-04e tests, full-doc validation before serialize (set AND role-override paths), pop marker in __init__, log-decision for AC-01i deviation. One record-repair call.

[2026-08-03T00:08:38+00:00] P1-model-preference-policy · finding-verifier · started
Cliente: Antes de reparar, un verificador intenta refutar los ocho hallazgos del panel de la politica de modelos.
Ingeniería: FINDING_VERIFICATION 014: refute/uphold SEC14-01, RF14-01..07 with live reproduction where claimed.

[2026-08-03T00:02:59+00:00] integrator · done
Cliente: El integrador confirmo que las dos piezas de la feature de deuda conviven sin acoplarse y que el contrato quedo cubierto por completo: de las seis deudas originales, tres quedan saldadas y tres siguen diferidas por decision explicita.
Ingeniería: Integration validation PASS: P1/P2 disjoint (grep zero cross-hits), 11/11 ACs mapped, non-goals untouched (PR-06/10/11 verified), no lifecycle restriction. Housekeeping: remaining-debt log-decision + BUENOS-DIAS update.

[2026-08-03T00:00:33+00:00] P1-harness-debt · integrator · started
Cliente: Un integrador valida que las dos piezas de la feature de deuda (motor de estado y higiene) funcionen juntas y cierren lo que la deuda original registraba.
Ingeniería: INTEGRATION 016: read-only validation of P1-harness-debt + P2-hygiene together vs contract 1.1.0, debt ledger closure check (audit-debt-006-p2), no re-run of heavy gates (already recorded green).

[2026-08-02T23:59:53+00:00] P1-model-preference-policy · security-auditor · started
Cliente: Un auditor revisa que el sesgo de preferencia no pueda debilitar la independencia de los revisores ni abrir una via de inyeccion por el archivo de configuracion.
Ingeniería: PACKAGE_REVIEW 014: security-auditor read-only on sort-key placement vs REVIEWER_INDEPENDENCE, _model_preference internal-marker injection, TOML parsing fail-closed, atomic writes.

[2026-08-02T23:59:53+00:00] P1-model-preference-policy · package-reviewer · started
Cliente: Un revisor independiente lee toda la politica de preferencia de modelos de punta a punta contra el contrato aprobado.
Ingeniería: PACKAGE_REVIEW 014: read-only vs contract 3.2.0; sort-key position, resolver partition, config surface, observability, ADR-0018; targeted tests only.

[2026-08-02T23:49:29+00:00] P1-model-preference-policy · gate-runner · started
Cliente: Con los dos implementadores terminados, un unico verificador corre todas las pruebas del proyecto en orden, sin carreras.
Ingeniería: PACKAGE_GATES 014 + PACKAGE_TESTING 016-P1: full discover, verify.sh, build.sh --check/--diff, git diff --check, serialized single-runner per build-staging race decision.

[2026-08-02T23:42:51+00:00] P1-harness-debt · package-reviewer · started
Cliente: Un revisor independiente lee toda la cirugia del motor de estado, incluida la obligacion contractual de verificar en el diff que cada guardia quedo en exactamente una de las dos funciones extraidas.
Ingeniería: PACKAGE_REVIEW P1: package-reviewer read-only vs AC-01..07/11; AC-05b: every guard line of old cmd_record_verification lands in exactly one extracted function; targeted tests only (014 edits test_routing concurrently).

[2026-08-02T23:37:06+00:00] P1-harness-debt · gate-runner · started
Cliente: Un verificador independiente repite las pruebas del motor de estado sin confiar en las corridas del implementador.
Ingeniería: PACKAGE_GATES P1: test_harness full module, 8 new tests + 9 AC-04 tests by name, twin byte-diff, build.sh --check, git diff --check. Full suite/verify.sh deferred to integration (test_routing under concurrent edit by 014).

[2026-08-02T23:19:16+00:00] P1-harness-debt · implementer · started
Cliente: Un implementador salda la deuda mas valiosa del motor de estado: la fase de reparacion pasa a registrarse con un campo autoritativo en vez de inferirse del historial, y la funcion mas enredada se parte en dos piezas claras, sin cambiar ningun comportamiento.
Ingeniería: PACKAGE_IMPLEMENTATION P1-harness-debt (AC-01..07, AC-11): 6 repair_entry sites + cmd_transition pop + fallback, extract _apply_verification_waiver/_apply_verdicts with pinned behavioral tests, ADR-0009 D7 pointer, twin sync. Self-modification protocol: incremental syntactically-valid edits.

[2026-08-02T23:19:16+00:00] P1-model-preference-policy · implementer · started
Cliente: Un implementador construye la politica de preferencia de modelos: el sistema aprende que clase de rol es cada agente (decision, construccion, revision) y sesga que proveedor prefiere cada clase, con efecto real inmediato para seis roles.
Ingeniería: PACKAGE_IMPLEMENTATION 014-P1 (AC-01..09): role-class resolver, sibling config atomic writer + CLI, sort-key position 3, RouteDecision.bias_class observability, ADR-0018. Runs AFTER 016-P2 accepted (shared service.py/test_routing/set_agents_app now clear). No build.sh/verify.sh during development (staging race rule).

[2026-08-02T23:15:20+00:00] P2-hygiene · delta-reviewer · started
Cliente: Un revisor distinto verifica que el arreglo del contrato del CLI sea real y no haya tocado nada mas.
Ingeniería: DELTA_REVIEW P2 R1: verify structural filter in _decide_status (scope: only _decide_status), CLI-boundary matrix rows, hard-failure rows untouched, no collateral edits.

[2026-08-02T23:02:06+00:00] P2-hygiene · repair-agent · started
Cliente: Un reparador hace que la nueva senal de redirect sea de verdad informativa: el CLI vuelve a responder igual que antes, la senal queda visible, y un test en la frontera lo garantiza.
Ingeniería: PACKAGE_REPAIR P2 R1: structural classification in _decide_status (RUNTIME_REDIRECTED* neutral, subset matching, covers co-occurrence) under approved exception + CLI-boundary tests for redirect-only and unverified+redirect shapes. One record-repair call.

[2026-08-02T23:00:13+00:00] P2-hygiene · finding-verifier · started
Cliente: Antes de reparar, un verificador intenta refutar los dos hallazgos del panel, incluida la reproduccion del corte en el contrato del CLI.
Ingeniería: FINDING_VERIFICATION P2: refute/uphold P2F-01 (exact-tuple _decide_status regression) and P2F-02 (CLI-boundary test gap); reproduce live.

