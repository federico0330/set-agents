# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-07-26T14:58:34+00:00

## Features

| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |
|---|---|---|---|---|---|---|---|---|---|---|
| 002-adaptive-pi-orchestration | feature | BLOCKED | P1-routing-core (repair_required) | 0/1 | 12/12 | 2/2 | 5 | HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles. Requires redesign of trusted catalog/observations and crash-safe telemetry before further implementation. | - | 2026-07-24T16:16:04+00:00 block |
| 003-trusted-routing-pi-runtime | feature | PACKAGE_ACCEPTED | P1R-trusted-routing (accepted) | 1/1 | 16/16 | 3/3 | 0 | - | INTEGRATION | 2026-07-25T03:01:53+00:00 accept-package |
| 004-adaptive-dispatch | feature | PACKAGE_PLANNING | - | 0/0 | 0/12 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-07-26T14:58:25+00:00 init |

## Quick-fixes recientes

- _sin quick-fixes registrados_

## Bitácora (últimos 15)

[2026-07-26T14:58:25+00:00] orchestrator · done
Cliente: El cliente aprobo el contrato del despacho adaptativo tras dos rondas de challenge independiente: el arnes va a elegir modelo por tarea (nivel rapido/balanceado/frontera) en OpenCode ya, y con eleccion dinamica real en Pi si el estudio de viabilidad da bien.
Ingeniería: USER_APPROVAL contract 1.1.0 (2 challenge rounds: needs-rework -> approve-with-edits, all edits applied). AM-1/AM-2 amendments to 003 logged. Packages P1-dispatch-core -> P2-opencode-lane -> P3-pi-lane(gated T-300). Mode feature budgets.

[2026-07-25T03:02:30+00:00] P1R-trusted-routing · orchestrator · done
Cliente: El paquete de ruteo confiable quedo aceptado: la deteccion de herramientas autenticadas ahora funciona de verdad, la base de datos se valida completa antes de tocarla, cada rechazo queda auditado, y hay pruebas de choque, concurrencia y privacidad. Dos revisores independientes lo verificaron. Queda un paso manual: borrar la base vieja para reactivar el ruteo persistente.
Ingeniería: R3 complete within authorized budget (spawns 14-16, cycle 3/3): FD-001..FD-010 closed (6 resolved, 4 resolved-by-approved-exception per r3-threat-model-amendment); r3-final-verification gate pass (19 focused, verify.sh 117, CLI, ownership no new paths); independent delta review verdict pass; testing + runtime QA recorded; P1R PACKAGE_ACCEPTED. Backlog notes N-1..N-5 in delta review reason. P2/P3 remain paused pending user decision. Operator action: rm -r ~/.local/state/set-agentes/routing-v2 (schema 2 -> 3 fail-closed).

[2026-07-25T02:52:31+00:00] P1R-trusted-routing · delta-reviewer · started
Cliente: Un revisor independiente distinto va a reproducir cada uno de los diez pendientes y decidir si la reparacion es real, sin poder tocar codigo.
Ingeniería: DELTA_REVIEW R3 delta-reviewer read-only, spawn 16/16 (last of authorized budget): decide resolved|open per FD-001..FD-010 against the R3-amended contract (decision r3-threat-model-amendment); approved exceptions apply to the recorded residuals only.

[2026-07-25T02:21:58+00:00] P1R-trusted-routing · gate-runner · started
Cliente: Una instancia independiente va a repetir todas las validaciones con tiempo suficiente y comprobar que la reparacion no toco nada fuera del paquete.
Ingeniería: DELTA_REVIEW R3 gate-runner read-only, spawn 15/16: focused suite, named regressions, setup_models, py_compile, all GateSpecs incl. new v2:routing-unit, verify.sh >=120s window, CLI explain 0 / conflict 2, git diff --check, ownership vs 51b84e3f.

[2026-07-25T02:08:42+00:00] P1R-trusted-routing · repair-agent · started
Cliente: Un unico reparador va a cerrar los diez pendientes: primero hara que la deteccion de herramientas autenticadas funcione de verdad, despues endurecera la base de datos y la auditoria, y dejara pruebas de choque, concurrencia y privacidad.
Ingeniería: PACKAGE_REPAIR R3, spawn 14/16 (Claude Fable in-session): FD-003 per-pair probe parsers with graceful degradation; FD-005 canonical DDL equality; FD-002 conservative risk max; FD-007 rejection audit + lifecycle CHECKs (SCHEMA bump); FD-008 counters + transactional compaction; FD-010 generic non-default-arg exclusion; feasible halves of FD-001/004/006 (sealed composition, recomputed binding, pwd root); infeasible halves -> approved exceptions.

[2026-07-25T02:07:43+00:00] P1R-trusted-routing · orchestrator · started
Cliente: El cliente autorizo una tercera y ultima ronda de reparacion con presupuesto nuevo: tres instancias mas (reparador, verificador y revisor independiente).
Ingeniería: User-authorized fresh budget for R3: max_spawns_per_package 13->16 (repair-agent, gate-runner, delta-reviewer). Direct state edit because the harness exposes no budget command; traceable here and in r3-threat-model-amendment.

[2026-07-24T23:54:28+00:00] P1R-trusted-routing · delta-reviewer · done
Cliente: La revisión independiente final confirmó que R2 mejora el comportamiento, pero deja abiertos los diez outcomes FD-001..FD-010; P1R no puede aceptarse.
Ingeniería: Final delta verdict=repair_required: FD-001 critical, FD-002..FD-009 high, FD-010 medium. Gates pass but counterexamples remain; no scope creep/full review required.

[2026-07-24T23:46:06+00:00] P1R-trusted-routing · delta-reviewer · started
Cliente: Un revisor delta independiente va a validar R2 antes de aceptar P1R.
Ingeniería: Fresh review budget 13/13 authorized by user; delta-reviewer read-only only, no code mutation or self-approval.

[2026-07-24T23:42:45+00:00] P1R-trusted-routing · orchestrator · blocked
Cliente: R2 pasa todos los gates, pero el paquete no se acepta porque falta el revisor delta independiente y ya no quedan spawns disponibles.
Ingeniería: HUMAN_DECISION_REQUIRED: spawn budget 12/12 exhausted; previous delta instance completed/unavailable; implementer cannot approve own repair. Feature remains BLOCKED despite R2 gate pass.

[2026-07-24T23:42:07+00:00] P1R-trusted-routing · gate-runner · done
Cliente: Los gates R2 quedaron verdes: compilación exacta, 107 tests, verify.sh, configuración, negativos de CLI/GateSpec y diff.
Ingeniería: Final gate-runner: py_compile PASS; unittest 107 PASS; setup PASS; VERIFY_PASS; diff PASS; CLI explain exit0/conflict exit2; pytest opcional no instalado; ownership temporal sin violación nueva.

[2026-07-24T23:37:11+00:00] P1R-trusted-routing · gate-runner · started
Cliente: Una última validación independiente va a repetir R2 y comprobar ownership exacto antes del delta reviewer.
Ingeniería: Spawn 12/12 final: gate-runner read-only executes focused/all GateSpecs/verify/CLI and alternate-index ownership from 51b84e3f; no more spawns after this.

[2026-07-24T23:25:29+00:00] P1R-trusted-routing · repair-agent · started
Cliente: Un repair-agent va a corregir los diez hallazgos delta en dos bloques acotados y verificables, preservando P2/P3 pausados.
Ingeniería: PACKAGE_REPAIR R2: bounded trust/catalog block plus SQLite/lifecycle/CLI block; only final repair slot before independent gate and reused delta reviewer; spawn 11/12, no contract weakening.

[2026-07-24T23:25:24+00:00] P1R-trusted-routing · orchestrator · started
Cliente: La autorización reabrió el paquete: la segunda reparación será acotada a DR-001..DR-010 y mantendrá P2/P3 pausados.
Ingeniería: PACKAGE_REPAIR R2 autorizado por user; phase PACKAGE_REPAIR, repair_batches=1, deep_review_cycles=2, spawns=10/12; quedan sólo repair-agent + gate-runner y luego follow-up del delta reviewer existente.

[2026-07-24T23:20:11+00:00] P1R-trusted-routing · repair-agent · started
Cliente: Un único reparador hospedado va a cerrar ahora las diez cadenas pendientes desde la capa más profunda, con pruebas que demuestren cada frontera; no alcanza con mantener verdes los tests anteriores.
Ingeniería: PACKAGE_REPAIR R2, spawn 10/12: remove constructible authorization/facts seams, exact probes/catalog, validate-before-mutate SQLite, complete lifecycle/rollups/compaction/CLI and production-shaped AC tests; no P2/P3, no self-approval.

[2026-07-24T23:16:06+00:00] P1R-trusted-routing · delta-reviewer · done
Cliente: La revisión delta confirmó que sólo 2 de 18 hallazgos cerraron; 16 siguen abiertos aunque los tests pasen, por lo que P1R no puede aceptarse.
Ingeniería: Delta R1 verdict=repair_required; SEC-003/007 resolved; DR-001 critical, DR-002..009 high, DR-010 medium. Sin regresión nueva, pero outcomes originales incompletos. Ciclo profundo final.

