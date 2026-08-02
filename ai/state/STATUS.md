# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-02T15:03:09+00:00

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
| 013-pi-interactive-target | feature | PACKAGE_PLANNING | - | 0/0 | 0/12 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-07-31T14:26:21+00:00 init |
| 015-anthropic-dispatch-parity | feature | DONE | P1-anthropic-dispatch-parity (accepted) | 1/1 | 0/12 | 1/2 | 0 | - | - | 2026-08-01T22:46:55+00:00 transition |

## Quick-fixes recientes

- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

[2026-08-02T15:00:53+00:00] P1-discovered-inventory · integrator · done
Cliente: El integrador confirmo que el inventario de modelos descubiertos quedo bien integrado: los 16 hallazgos de revision estan cerrados y verificados, y las compuertas de seguridad siguen cerradas como se acordo (se puede sondear, no rutear).
Ingeniería: Integration validation PASS: AC-01..AC-12 verified in tree (pair commands, dual maps, lockstep allowlists, CANONICAL_MODEL aliasing closing SEC-001/002, billing kinds, ADR-0016 Accepted). Live gates: unittest 558 OK, verify.sh VERIFY_PASS. Non-goals honored: enabled_providers/ROUTING_PROVIDERS stay closed.

[2026-08-02T14:54:59+00:00] P1-spawn-provenance · integrator · done
Cliente: El integrador confirmo que el registro de procedencia de cada delegacion funciona y quedo bien conectado: las cinco condiciones acordadas se cumplen y los pendientes del traspaso anterior ya estaban ejecutados. Igual que con la vista de grafo, esta ficha queda cerrada sin sello final, tal como se decidio en su momento.
Ingeniería: Integration validation PASS: AC-01..AC-05 verified in tree (replay guard first, spawn nodes edge-free, ownership clean, done_ready resolved_at filter, 5/5 regression tests green). HANDOFF-PASO9 5.2/5.3 executed (ADR-0013 superseded note + log-decision ac-04). Per HANDOFF 5.5 + spec Origen, 010 stays PACKAGE_ACCEPTED; INTEGRATION/DONE never invoked. Non-blocking observation: exceptions field absen…

[2026-08-02T14:53:45+00:00] orchestrator · done
Cliente: La seleccion dinamica de modelos quedo oficialmente terminada: todas las pruebas del proyecto pasaron y la pieza convive bien con el resto. La parte que depende de medir cuotas reales queda en pausa hasta que eso sea posible.
Ingeniería: 008 DONE: transition PACKAGE_ACCEPTED->INTEGRATION->DONE with global gate feature-008-integration pass (verify.sh 558 OK, build check). P3 budget-aware-selection remains deferred behind 011 (BLOCKED by design).

[2026-08-02T14:53:27+00:00] P1-uninterrupted-delegation · integrator · done
Cliente: El integrador reviso la pieza que evita pausas innecesarias al delegar trabajo: las diez condiciones acordadas estan cumplidas y conviven bien con lo entregado despues. Solo falta la corrida final de pruebas globales antes del sello de terminado.
Ingeniería: Integration validation PASS: AC-01..AC-10 verified in current tree (doctrine in 3 shared runtimes, build.sh --check CHECK_PASS SELF_SCAFFOLD_SYNC_OK, ADR-0011 linked, no conflict with 015 lane logic). P3 budget-aware-selection out of scope (blocked on 011). Pending: feature-level global gate (full verify.sh + unittest) before transition DONE.

[2026-08-02T14:47:21+00:00] P3-graph-view · integrator · done
Cliente: El integrador confirmo que la vista de grafo funciona y encaja con todo lo entregado: las diez condiciones acordadas se cumplen y no aparecio ningun problema nuevo. La ficha de esta pieza queda cerrada tal como se acordo: completa, sin marcarla con un sello final que prometeria mas de lo que se rastreo.
Ingeniería: Integration validation PASS: AC-20..AC-29 verified in tree (graph subcommand, mermaid oracle 0 violations, skeleton exit 0, grafo.md 8/8 clean, WAIVED retired, twin byte-identical). Per spec.md:198-204 006 stays PACKAGE_ACCEPTED; transition DONE is never invoked (P1/P2 delivered under waiver, only P3's 9 ACs tracked). Integration evidence recorded; no findings.

[2026-08-02T14:44:35+00:00] P1-discovered-inventory · integrator · started
Cliente: Un integrador comprueba que el inventario descubierto se integra sin romper nada de lo existente.
Ingeniería: INTEGRATION entry: read-only validation of P1-discovered-inventory against approved spec 012.

[2026-08-02T14:44:35+00:00] P1-spawn-provenance · integrator · started
Cliente: Un integrador verifica que el registro de procedencia de cada delegacion quedo bien conectado con el tablero y las notas.
Ingeniería: INTEGRATION entry: read-only validation of P1-spawn-provenance against approved spec 010, including the ownership exception granted in HANDOFF-PASO9.

[2026-08-02T14:44:35+00:00] P1-uninterrupted-delegation · integrator · started
Cliente: Un integrador confirma que la seleccion dinamica de modelos convive bien con el resto del sistema antes de darla por terminada.
Ingeniería: INTEGRATION entry: read-only validation of P1-uninterrupted-delegation against approved spec 008; P3 budget-aware-selection stays blocked on 011 and is out of scope.

[2026-08-02T14:44:35+00:00] P3-graph-view · integrator · started
Cliente: Un integrador revisa que la vista de grafo terminada encaje con todo lo ya entregado antes de declararla lista: nada se marca como completo sin esa mirada de conjunto.
Ingeniería: INTEGRATION entry: read-only validation of P3-graph-view (ACs 20-29) against approved spec 006, cross-package deps and vault artifacts; produces integration verdict for global gate.

[2026-07-31T00:22:55+00:00] P1-discovered-inventory · delta-reviewer · started
Cliente: Última verificación antes de cerrar el paquete.
Ingeniería: delta-reviewer, contexto limpio, acotado a los 3 fixes de la ronda 2.

[2026-07-30T23:59:05+00:00] P1-discovered-inventory · repair-agent · started
Cliente: El mismo agujero de seguridad que se cerró para Opus/Sonnet/Haiku se filtró para Fable, el modelo más nuevo. Se cierra ahora, acotado.
Ingeniería: repair-agent, segunda ronda, alcance mínimo: 3 hallazgos.

[2026-07-30T23:35:12+00:00] P1-discovered-inventory · delta-reviewer · started
Cliente: Un tercer revisor, que no vio ni la implementación original ni el panel, confirma que las reparaciones cierran los problemas sin abrir otros nuevos.
Ingeniería: delta-reviewer, contexto limpio, acotado al diff de la reparación (catalog.py, service.py, models.toml, models_config.py, ADR-0016, README, test_routing.py).

[2026-07-30T22:39:33+00:00] P1-discovered-inventory · repair-agent · started
Cliente: El panel de revisión encontró un agujero real de seguridad (un modelo podría revisarse a sí mismo bajo dos nombres de proveedor) y varios problemas menores. Se repara todo en una sola pasada.
Ingeniería: repair-agent consolidado, orden por severidad: SEC-001 (critical) primero, F-01/F-02 (high, tests que no discriminan) segundo, resto después.

[2026-07-30T20:53:58+00:00] P1-discovered-inventory · security-auditor · started
Cliente: Un segundo revisor, de seguridad, audita específicamente si la lógica que evita que un modelo se revise a sí mismo bajo dos nombres de proveedor es realmente sólida.
Ingeniería: security-auditor, contexto limpio, panel RP-01, concurrente con package-reviewer.

[2026-07-30T20:53:58+00:00] P1-discovered-inventory · package-reviewer · started
Cliente: Un revisor que nunca vio la implementación audita si el catálogo dinámico está bien construido.
Ingeniería: package-reviewer, contexto limpio, panel RP-01.

