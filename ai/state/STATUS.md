# Estado del desarrollo

_Generado por `feature-state.py` en cada mutación de estado. No editar a mano._

Actualizado: 2026-08-01T22:46:55+00:00

## Features

| Feature | Modo | Fase | Paquete | Aceptados | Spawns | Reviews | Findings abiertos | Blocker | Próximo paso | Último evento |
|---|---|---|---|---|---|---|---|---|---|---|
| 002-adaptive-pi-orchestration | feature | BLOCKED | P1-routing-core (repair_required) | 0/1 | 12/12 | 2/2 | 5 | HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhausted 12 spawns plus 2 deep-review cycles… | - | 2026-07-24T16:16:04+00:00 block |
| 003-trusted-routing-pi-runtime | feature | DONE | P1R-trusted-routing (accepted) | 1/1 | 16/16 | 3/3 | 0 | - | - | 2026-07-29T17:13:45+00:00 transition |
| 004-adaptive-dispatch | feature | DONE | P3-pi-lane (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-27T14:04:38+00:00 transition |
| 005-portable-harness | feature | DONE | P3-tui (accepted) | 3/3 | 20/12 | 1/2 | 0 | - | - | 2026-07-30T16:16:18+00:00 transition |
| 006-execution-graph | feature | PACKAGE_ACCEPTED | P3-graph-view (accepted) | 1/1 | 8/12 | 1/2 | 0 | - | INTEGRATION | 2026-07-30T07:38:47+00:00 accept-package |
| 007-quota-visibility | feature | DONE | P3-correct-record (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 008-dynamic-selection | feature | PACKAGE_ACCEPTED | P1-uninterrupted-delegation (accepted) | 1/1 | 5/12 | 1/2 | 0 | - | INTEGRATION | 2026-07-28T14:49:14+00:00 accept-package |
| 009-self-application | feature | DONE | P3-panel-integrity (accepted) | 3/3 | 13/12 | 1/2 | 0 | - | - | 2026-07-29T17:10:45+00:00 transition |
| 010-spawn-provenance | feature | PACKAGE_ACCEPTED | P1-spawn-provenance (accepted) | 1/1 | 10/12 | 1/2 | 0 | - | INTEGRATION | 2026-07-30T16:15:59+00:00 accept-package |
| 011-quota-failover | feature | BLOCKED | P1-quota-failover (package_gates) | 0/1 | 3/12 | 0/2 | 0 | HUMAN_DECISION_REQUIRED: AC-06 exige una suscripción Anthropic controlada y genuinamente agotada junto a un proveedor alterno usable; la precondición no está v… | - | 2026-07-30T17:04:39+00:00 block |
| 012-discovered-inventory | feature | PACKAGE_ACCEPTED | P1-discovered-inventory (accepted) | 1/1 | 7/12 | 1/2 | 0 | - | INTEGRATION | 2026-07-31T00:53:17+00:00 accept-package |
| 013-pi-interactive-target | feature | PACKAGE_PLANNING | - | 0/0 | 0/12 | 0/2 | 0 | - | PACKAGE_IMPLEMENTATION | 2026-07-31T14:26:21+00:00 init |
| 015-anthropic-dispatch-parity | feature | DONE | P1-anthropic-dispatch-parity (accepted) | 1/1 | 0/12 | 1/2 | 0 | - | - | 2026-08-01T22:46:55+00:00 transition |

## Quick-fixes recientes

- [2026-07-30T01:22:42+00:00] P2-vault-mandatory (accepted): exclude_notes_from_git/_notes_currently_excluded chequeaban (project/'.git').is_dir(), falso para un git worktree enlazado (.git es archivo ahi) -- docs/notas quedaba trackeado por git en vez de excluido, contradiciendo DEC-5. Fix: resolver via 'git rev-parse --show-toplevel/--git-common-dir' anclado a que el proyecto SEA el top-level (no solo estar dentro de un repo), con env purgado de GIT_DIR/GIT_WORK_TREE/GIT_COMMON_DIR/GIT_INDEX_FILE, timeout y manejo de git ausente. Bono: vault_doctor_report ahora distingue dangling de un symlink cuyo target fue borrado (antes reportaba healthy). Encontrado migrando ~/iey de verdad; revisado por un segundo agente (package-reviewer) que encontro 7 hallazgos adicionales sobre el primer fix, todos reparados y re-verificados con pass. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass (2da pasada) — resultado: done
- [2026-07-30T01:22:33+00:00] P2-vault-mandatory (accepted): write_vault_registry_entry resolvía el vault_path a través del symlink recién creado, guardando el directorio real del repo en vez del symlink del lado del vault. vault_doctor_report reportaba health=drift para siempre en todo proyecto hybrid recién linkeado. Fix: normalizar resolviendo solo el padre (parent.resolve()/name), nunca el componente final. Encontrado migrando ~/iey de verdad. — archivos: ai/scripts/set_agents_app.py, tests/test_harness.py — gate: 331 tests verdes, verify.sh VERIFY_PASS, build.sh --check SELF_SCAFFOLD_SYNC_OK, git diff --check limpio, package-reviewer pass — resultado: done

## Bitácora (últimos 15)

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

[2026-07-30T20:07:45+00:00] P1-discovered-inventory · implementer · started
Cliente: Arranca la implementación del catálogo dinámico de modelos.
Ingeniería: implementer sobre P1-discovered-inventory, contrato ya verificado en 3 rondas de spec-challenge, ready_for_user_approval.

[2026-07-30T19:46:48+00:00] started
Cliente: Última vuelta del contrato de P2: el único punto flojo que quedaba era cómo evitar que el mismo modelo, ofrecido bajo dos proveedores con nombres distintos, se revisara a sí mismo creyendo que era independiente.
Ingeniería: product-analyst reescribió AC-17/AC-18 quirúrgicamente (contract 1.3.0): family pasa a ser curada con regla de colisión para ids compartidos entre providers, subscription/metered pasa a mapa curado por provider en vez de columna de fila (evita el esquema cerrado de catalog.py). Tercera pasada del mismo spec-challenger, acotada.

[2026-07-30T19:29:30+00:00] started
Cliente: El contrato de P2 volvió corregido: el mapa de nombres estaba al revés (el par nuevo hubiera quedado invisible en toda máquina), dos afirmaciones 'verificadas en vivo' resultaron mal medidas, y se agregó el campo que distingue suscripción de pago-por-uso que me confirmaste vos.
Ingeniería: product-analyst entregó contract 1.2.0 resolviendo los 3 bloqueantes + 4 highs + 6 mediums + 6 lows del primer challenge. Mando al mismo spec-challenger (contexto ya cargado) a una segunda pasada, acotada a verificar que las correcciones sean reales y no haya nada nuevo.

[2026-07-30T17:58:01+00:00] done
Cliente: El contrato de P2 (catálogo dinámico) ya está escrito con reglas concretas — incluida una fricción real que encontró al probar en vivo: el nombre de la credencial de OpenCode no coincide con el id que pide su propio comando para listar modelos.
Ingeniería: product-analyst entregó AC-11..AC-20 en docs/specs/008-dynamic-selection/spec.md (1.0.0->1.1.0), verificado contra catalog.py/domain.py/service.py y una corrida real de 'opencode auth list'/'opencode models'. No tocó P1/P1b/P3. Mando un spec-challenger de contexto limpio antes de iniciar el paquete.

[2026-07-30T17:57:23+00:00] P1-quota-failover · started
Cliente: Antes de seguir, encontré que la suite completa tiene 2 pruebas rojas que la verificación acotada de la sesión anterior no corrió.
Ingeniería: verify.sh (suite completa, 473 tests) -> FAILED (failures=2): test_routing_migrate_uses_harness_identity_and_test_store espera 'to=6' y el schema real ya es 7; test_the_usage_columns_sit_exactly_where_alter_table_puts_them compara contra un DDL canónico que no incluye replacement_of_run_id. Ambos son literales desactualizados por el propio paquete P1-quota-failover (SCHEMA=7, columna agregada cor…

[2026-07-30T17:44:00+00:00] started
Cliente: Arrancamos el catálogo dinámico de modelos: hoy el orquestador solo conoce dos proveedores escritos a mano, y no ve los modelos propios de OpenCode ni los que agregues en el futuro.
Ingeniería: product-analyst redacta P2-discovered-inventory como enmienda real de 008 (hoy es un párrafo sin ACs). No depende de 007-P2 ni de 011/P1b — solo de sondear el entorno. Ownership acotado a docs/specs/008-dynamic-selection/spec.md; sin tocar código todavía.

[2026-07-30T17:04:50+00:00] P1-quota-failover · runtime-verifier · blocked
Cliente: La prueba real no puede hacerse de forma segura sin una suscripción agotada controlada; el sistema quedó detenido sin gastar ni modificar nada.
Ingeniería: AC-06 requiere precondición externa verificable. Runner validado devuelve BLOCKED/HUMAN_DECISION_REQUIRED antes de abrir DB o invocar Pi; feature state quedó BLOCKED.

[2026-07-30T17:02:28+00:00] P1-quota-failover · implementer · done
Cliente: El reemplazo seguro y su comprobación real quedaron implementados; sin precondición controlada, el sistema informa un bloqueo seguro.
Ingeniería: Core schema-7, transición atómica, adaptador Pi, pruebas AC-01..05 y runner AC-06 documentados; cinco pruebas focalizadas PASS.

[2026-07-30T16:58:41+00:00] P1-quota-failover · implementer · started
Cliente: Se completa la comprobación real que debe bloquearse honestamente si falta la precondición controlada.
Ingeniería: Instancia focalizada para runner credencial-gated AC-06 y evidencia, sin expandir el núcleo de routing.

