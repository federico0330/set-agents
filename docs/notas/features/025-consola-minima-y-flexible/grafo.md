# 025-consola-minima-y-flexible · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_025_consola_minima_y_flexible["025-consola-minima-y-flexible"]
  feature_025_consola_minima_y_flexible_1["feature: 025-consola-minima-y-flexible"]
  subgraph sg_025_consola_minima_y_flexible_d1_superficie_humana["D1-superficie-humana"]
    package_025_consola_minima_y_flexible_d1_superficie_humana_1["package: D1-superficie-humana"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_1["D1-F01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_2["D1-F02 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_3["D1-F03 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_4["D1-F04 #40;medium#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_5["D1-F05 #40;medium#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_6["D1-F06 #40;medium#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_7["D1-F07 #40;low#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d1_superficie_humana_8["D1-F09 #40;low#41; verified_by=finding-verifier"]
    review_025_consola_minima_y_flexible_d1_superficie_humana_1["repair_required #40;package-reviewer#41;"]
    verification_025_consola_minima_y_flexible_d1_superficie_humana_1["verified_by=finding-verifier"]
    repair_025_consola_minima_y_flexible_d1_superficie_humana_1["4 changed files"]
    commit_025_consola_minima_y_flexible_d1_superficie_humana_1["2f199d5"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_1["SPAWN-001 implementer Menu sin emoji, flags internas ocultas pero vivas, y salida humana en vez de JSON crudo #91;sonnet#93;"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_2["SPAWN-002 package-reviewer Review independiente de D1 sobre su worktree congelado #91;claude-opus-5#93;"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_3["SPAWN-003 repair-agent Reparacion consolidada de los diez hallazgos de D1 #91;claude-sonnet-5#93;"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_4["SPAWN-004 finding-verifier"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_5["SPAWN-005 delta-reviewer"]
    spawn_025_consola_minima_y_flexible_d1_superficie_humana_6["SPAWN-006 gate-runner Ejecutar pruebas y QA observacional de D1 sobre el árbol integrado, preservando evidencia reprodu…"]
  end
  subgraph sg_025_consola_minima_y_flexible_d2_trabajo_visible["D2-trabajo-visible"]
    package_025_consola_minima_y_flexible_d2_trabajo_visible_1["package: D2-trabajo-visible"]
    finding_025_consola_minima_y_flexible_d2_trabajo_visible_1["D2-F01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d2_trabajo_visible_2["D2-F02 #40;medium#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d2_trabajo_visible_3["D2-DR01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d2_trabajo_visible_4["D2-DR02 #40;low#41;"]
    review_025_consola_minima_y_flexible_d2_trabajo_visible_1["delta: repair_required"]
    review_025_consola_minima_y_flexible_d2_trabajo_visible_2["repair_required #40;orchestrator#41;"]
    verification_025_consola_minima_y_flexible_d2_trabajo_visible_1["verified_by=finding-verifier"]
    verification_025_consola_minima_y_flexible_d2_trabajo_visible_2["verified_by=finding-verifier"]
    repair_025_consola_minima_y_flexible_d2_trabajo_visible_1["4 changed files"]
    commit_025_consola_minima_y_flexible_d2_trabajo_visible_1["489ecff"]
    repair_025_consola_minima_y_flexible_d2_trabajo_visible_2["5 changed files"]
    commit_025_consola_minima_y_flexible_d2_trabajo_visible_2["d30f94f"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_1["SPAWN-001 gate-runner Validar artefacto y evidencia existente de D2 contra el árbol integrado #91;gpt-5.6-luna#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_2["SPAWN-002 package-reviewer Revisión independiente completa de AC-04/05 y evidencia D2 integrada #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_3["SPAWN-003 finding-verifier Refutar o sostener D2-F01 y D2-F02 antes de una reparación consolidada #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_4["SPAWN-004 repair-agent Reparar D2-F01 y D2-F02 en un único pase con regresiones #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_5["SPAWN-005 delta-reviewer Revisar delta 489ecff contra D2-F01/D2-F02 #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_6["SPAWN-006 finding-verifier Verificar independientemente D2-F01 y D2-DR01 antes de reparar el segundo ciclo #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_7["SPAWN-007 repair-agent Reparación consolidada final de D2-F01, D2-DR01 y D2-DR02 #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d2_trabajo_visible_8["SPAWN-008 delta-reviewer Último delta-review focal de D2 y medición de repair ceiling #91;gpt-5.6-sol#93;"]
  end
  subgraph sg_025_consola_minima_y_flexible_d3_posturas_de_autonomia["D3-posturas-de-autonomia"]
    package_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["package: D3-posturas-de-autonomia"]
    finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["D3-F01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["D3-F02 #40;medium#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_3["D3-F03 #40;medium#41; verified_by=finding-verifier"]
    review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["delta: repair_required"]
    review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["repair_required #40;package-reviewer#41;"]
    verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["verified_by=finding-verifier"]
    verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["verified_by=finding-verifier"]
    repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["8 changed files"]
    commit_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["5745537"]
    repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["7 changed files"]
    commit_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["bbed1d3"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1["SPAWN-001 gate-runner Medir D3 integrado: posturas, toggles TDD/SDD/RDD y compatibilidad #91;gpt-5.6-luna#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2["SPAWN-002 package-reviewer Review independiente D3 AC-06..08 sobre árbol integrado #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_3["SPAWN-003 finding-verifier Verificar D3-F01/F02/F03 antes de reparación #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_4["SPAWN-004 repair-agent Reparación consolidada de D3-F01/F02/F03 #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_5["SPAWN-005 delta-reviewer Delta-review D3 repair F01/F02/F03 #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_6["SPAWN-006 finding-verifier Verificar F01 reabierto de D3 antes de segundo repair #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_7["SPAWN-007 repair-agent Segundo repair focal D3-F01: asociación y precedencia inequívocas #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d3_posturas_de_autonomia_8["SPAWN-008 delta-reviewer Delta-review final D3-F01 sobre contrato asociativo y precedencia #91;gpt-5.6-sol#93;"]
  end
  subgraph sg_025_consola_minima_y_flexible_d4_harness_por_cli["D4-harness-por-CLI"]
    package_025_consola_minima_y_flexible_d4_harness_por_cli_1["package: D4-harness-por-CLI"]
    finding_025_consola_minima_y_flexible_d4_harness_por_cli_1["D4-F01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d4_harness_por_cli_2["D4-DR02 #40;low#41;"]
    review_025_consola_minima_y_flexible_d4_harness_por_cli_1["delta: repair_required"]
    review_025_consola_minima_y_flexible_d4_harness_por_cli_2["repair_required #40;package-reviewer#41;"]
    verification_025_consola_minima_y_flexible_d4_harness_por_cli_1["verified_by=finding-verifier"]
    verification_025_consola_minima_y_flexible_d4_harness_por_cli_2["verified_by=finding-verifier"]
    repair_025_consola_minima_y_flexible_d4_harness_por_cli_1["6 changed files"]
    commit_025_consola_minima_y_flexible_d4_harness_por_cli_1["bfe7b2d"]
    repair_025_consola_minima_y_flexible_d4_harness_por_cli_2["4 changed files"]
    commit_025_consola_minima_y_flexible_d4_harness_por_cli_2["8a9f62b"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_1["SPAWN-001 gate-runner Medir D4 install/uninstall aislado por carril #91;gpt-5.6-luna#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_2["SPAWN-002 gate-runner Reintento focal D4 sandbox AC-09..11 tras evidencia incompleta #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_3["SPAWN-003 package-reviewer Review D4 AC09-11 aislamiento y contratos de install/uninstall #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_4["SPAWN-004 package-reviewer Revisión D4 AC-11 sin PoC de rutas tras interrupción de reviewer #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_5["SPAWN-005 finding-verifier Verificar D4-F01 AC-11 diferido antes de reparación #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_6["SPAWN-006 repair-agent Implementar AC-11 one-shot virgin CLI y sustituir falso gate #91;gpt-5.6-terra#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_7["SPAWN-007 delta-reviewer Delta-review D4 one-shot --virgin AC-11 #91;gpt-5.6-sol#93;"]
    spawn_025_consola_minima_y_flexible_d4_harness_por_cli_8["SPAWN-008 repair-agent Último repair D4: --virgin interactivo y ADR AC-11 #91;gpt-5.6-terra#93;"]
    blocker_025_consola_minima_y_flexible_d4_harness_por_cli_1["blocker: resolved"]
    blocker_025_consola_minima_y_flexible_d4_harness_por_cli_2["blocker: resolved"]
  end
  subgraph sg_025_consola_minima_y_flexible_d5_vault_en_todo_spawn["D5-vault-en-todo-spawn"]
    package_025_consola_minima_y_flexible_d5_vault_en_todo_spawn_1["package: D5-vault-en-todo-spawn"]
    spawn_025_consola_minima_y_flexible_d5_vault_en_todo_spawn_1["SPAWN-001 implementer Implementar AC-12 y los cuatro arreglos de spawners sobre el SHA integrado. #91;gpt-5.6-terra#93;"]
  end
  subgraph sg_025_consola_minima_y_flexible_d5_correctiva["D5-correctiva"]
    package_025_consola_minima_y_flexible_d5_correctiva_1["package: D5-correctiva"]
    finding_025_consola_minima_y_flexible_d5_correctiva_1["D5-DR01 #40;high#41; verified_by=finding-verifier"]
    finding_025_consola_minima_y_flexible_d5_correctiva_2["D5-DR02 #40;medium#41; verified_by=finding-verifier"]
    review_025_consola_minima_y_flexible_d5_correctiva_1["repair_required #40;package-reviewer#41;"]
    verification_025_consola_minima_y_flexible_d5_correctiva_1["verified_by=finding-verifier"]
    repair_025_consola_minima_y_flexible_d5_correctiva_1["2 changed files"]
    spawn_025_consola_minima_y_flexible_d5_correctiva_1["SPAWN-001 package-reviewer package-review #91;claude-sonnet-4.6#93;"]
  end
end
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_1
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_2
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_3
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_4
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_5
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_6
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_7
review_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|produjo| finding_025_consola_minima_y_flexible_d1_superficie_humana_8
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|refutó| finding_025_consola_minima_y_flexible_d1_superficie_humana_4
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_1
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_2
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_3
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_5
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_6
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_7
verification_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|verificó| finding_025_consola_minima_y_flexible_d1_superficie_humana_8
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_1
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_2
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_3
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_5
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_6
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_7
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| finding_025_consola_minima_y_flexible_d1_superficie_humana_8
repair_025_consola_minima_y_flexible_d1_superficie_humana_1 -->|reparó| commit_025_consola_minima_y_flexible_d1_superficie_humana_1
review_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|produjo| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
review_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|produjo| finding_025_consola_minima_y_flexible_d2_trabajo_visible_3
review_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|produjo| finding_025_consola_minima_y_flexible_d2_trabajo_visible_4
review_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|produjo| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
review_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|produjo| finding_025_consola_minima_y_flexible_d2_trabajo_visible_2
verification_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|verificó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
verification_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|verificó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_2
verification_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|verificó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
verification_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|verificó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_3
repair_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|reparó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
repair_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|reparó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_2
repair_025_consola_minima_y_flexible_d2_trabajo_visible_1 -->|reparó| commit_025_consola_minima_y_flexible_d2_trabajo_visible_1
repair_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|reparó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_1
repair_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|reparó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_3
repair_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|reparó| finding_025_consola_minima_y_flexible_d2_trabajo_visible_4
repair_025_consola_minima_y_flexible_d2_trabajo_visible_2 -->|reparó| commit_025_consola_minima_y_flexible_d2_trabajo_visible_2
review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|produjo| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|produjo| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|produjo| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2
review_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|produjo| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_3
verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|verificó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|verificó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2
verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|verificó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_3
verification_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|verificó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|reparó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|reparó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|reparó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_3
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1 -->|reparó| commit_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|reparó| finding_025_consola_minima_y_flexible_d3_posturas_de_autonomia_1
repair_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2 -->|reparó| commit_025_consola_minima_y_flexible_d3_posturas_de_autonomia_2
review_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|produjo| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
review_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|produjo| finding_025_consola_minima_y_flexible_d4_harness_por_cli_2
review_025_consola_minima_y_flexible_d4_harness_por_cli_2 -->|produjo| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
verification_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|verificó| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
verification_025_consola_minima_y_flexible_d4_harness_por_cli_2 -->|verificó| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
repair_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|reparó| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
repair_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|reparó| commit_025_consola_minima_y_flexible_d4_harness_por_cli_1
repair_025_consola_minima_y_flexible_d4_harness_por_cli_2 -->|reparó| finding_025_consola_minima_y_flexible_d4_harness_por_cli_1
repair_025_consola_minima_y_flexible_d4_harness_por_cli_2 -->|reparó| finding_025_consola_minima_y_flexible_d4_harness_por_cli_2
repair_025_consola_minima_y_flexible_d4_harness_por_cli_2 -->|reparó| commit_025_consola_minima_y_flexible_d4_harness_por_cli_2
review_025_consola_minima_y_flexible_d5_correctiva_1 -->|produjo| finding_025_consola_minima_y_flexible_d5_correctiva_1
review_025_consola_minima_y_flexible_d5_correctiva_1 -->|produjo| finding_025_consola_minima_y_flexible_d5_correctiva_2
verification_025_consola_minima_y_flexible_d5_correctiva_1 -->|verificó| finding_025_consola_minima_y_flexible_d5_correctiva_1
verification_025_consola_minima_y_flexible_d5_correctiva_1 -->|verificó| finding_025_consola_minima_y_flexible_d5_correctiva_2
repair_025_consola_minima_y_flexible_d5_correctiva_1 -->|reparó| finding_025_consola_minima_y_flexible_d5_correctiva_1
repair_025_consola_minima_y_flexible_d5_correctiva_1 -->|reparó| finding_025_consola_minima_y_flexible_d5_correctiva_2
package_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|bloqueó| blocker_025_consola_minima_y_flexible_d4_harness_por_cli_1
package_025_consola_minima_y_flexible_d4_harness_por_cli_1 -->|bloqueó| blocker_025_consola_minima_y_flexible_d4_harness_por_cli_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
