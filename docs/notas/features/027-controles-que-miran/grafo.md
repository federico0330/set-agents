# 027-controles-que-miran · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_027_controles_que_miran["027-controles-que-miran"]
  feature_027_controles_que_miran_1["feature: 027-controles-que-miran"]
  subgraph sg_027_controles_que_miran_p1_alcance_y_aislamiento["P1-alcance-y-aislamiento"]
    package_027_controles_que_miran_p1_alcance_y_aislamiento_1["package: P1-alcance-y-aislamiento"]
    finding_027_controles_que_miran_p1_alcance_y_aislamiento_1["P1-F01 #40;medium#41; verified_by=orchestrator"]
    review_027_controles_que_miran_p1_alcance_y_aislamiento_1["repair_required #40;package-reviewer#41;"]
    verification_027_controles_que_miran_p1_alcance_y_aislamiento_1["verified_by=orchestrator"]
    repair_027_controles_que_miran_p1_alcance_y_aislamiento_1["2 changed files"]
    spawn_027_controles_que_miran_p1_alcance_y_aislamiento_1["SPAWN-001 repair-agent Reparar P1-F01: preservar el estado presente-con-None de sys.modules y documentar la mordida #91;gp…"]
    spawn_027_controles_que_miran_p1_alcance_y_aislamiento_2["SPAWN-002 gate-runner Verificar de forma independiente el delta P1-F01 y los módulos de test aislados #91;gpt-5.6-luna#93;"]
    spawn_027_controles_que_miran_p1_alcance_y_aislamiento_3["SPAWN-003 delta-reviewer Revisión delta independiente de la reparación P1-F01, incluyendo su evidencia y gates incomple…"]
    spawn_027_controles_que_miran_p1_alcance_y_aislamiento_4["SPAWN-004 test-writer Prueba final de regresión de P1 después del delta review #91;gpt-5.6-terra#93;"]
    spawn_027_controles_que_miran_p1_alcance_y_aislamiento_5["SPAWN-005 runtime-verifier Runtime QA del CLI check-owned-paths para P1 antes de su aceptación #91;gpt-5.6-terra#93;"]
  end
  subgraph sg_027_controles_que_miran_p2_nada_escribe_afuera["P2-nada-escribe-afuera"]
    package_027_controles_que_miran_p2_nada_escribe_afuera_1["package: P2-nada-escribe-afuera"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_1["P2-F01 #40;high#41; verified_by=package-reviewer"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_2["P2-F02 #40;high#41; verified_by=package-reviewer"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_3["P2-F03 #40;medium#41; verified_by=package-reviewer"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_4["P2-F04 #40;high#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_5["P2-F05 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_6["P2-F06 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_7["P2-F07 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_8["P2-F08 #40;low#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_9["P2-F09 #40;low#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p2_nada_escribe_afuera_10["P2-F10 #40;low#41; verified_by=orchestrator"]
    review_027_controles_que_miran_p2_nada_escribe_afuera_1["delta: repair_required"]
    review_027_controles_que_miran_p2_nada_escribe_afuera_2["repair_required #40;package-reviewer#41;"]
    verification_027_controles_que_miran_p2_nada_escribe_afuera_1["verified_by=package-reviewer"]
    verification_027_controles_que_miran_p2_nada_escribe_afuera_2["verified_by=orchestrator"]
    repair_027_controles_que_miran_p2_nada_escribe_afuera_1["5 changed files"]
    repair_027_controles_que_miran_p2_nada_escribe_afuera_2["4 changed files"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_1["SPAWN-001 package-planner Completar context packs operativos para P2, P3 y P4 antes de sus implementaciones encadenadas…"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_2["SPAWN-002 implementer Implementación acotada de AC-04/05 de P2. #91;gpt-5.6-terra#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_3["SPAWN-003 gate-runner Gates independientes de P2 para AC-04/05. #91;gpt-5.6-luna#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_4["SPAWN-004 local-gate-runner Reintento interactivo único de gates P2 interrumpidos. #91;gpt-5.6-luna#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_5["SPAWN-005 gate-runner Reintento de gates P2 con runner habilitado para suite completa. #91;gpt-5.6-terra#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_6["SPAWN-006 repair-agent Reparar fixture de build check que escribe en repo real y viola AC-04. #91;gpt-5.6-terra#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_7["SPAWN-007 gate-runner Gate post-reparación de P2: fixture sandbox, guardia focal y chequeos rápidos. #91;gpt-5.6-luna#93;"]
    spawn_027_controles_que_miran_p2_nada_escribe_afuera_8["SPAWN-008 package-reviewer Revisión independiente del paquete P2 tras gates y reparación. #91;gpt-5.6-sol#93;"]
    blocker_027_controles_que_miran_p2_nada_escribe_afuera_1["blocker: resolved"]
    blocker_027_controles_que_miran_p2_nada_escribe_afuera_2["blocker: resolved"]
  end
  subgraph sg_027_controles_que_miran_p3_gates_que_preguntan_antes["P3-gates-que-preguntan-antes"]
    package_027_controles_que_miran_p3_gates_que_preguntan_antes_1["package: P3-gates-que-preguntan-antes"]
    finding_027_controles_que_miran_p3_gates_que_preguntan_antes_1["P3-F01 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p3_gates_que_preguntan_antes_2["P3-F02 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p3_gates_que_preguntan_antes_3["P3-F03 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p3_gates_que_preguntan_antes_4["P3-F04 #40;low#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p3_gates_que_preguntan_antes_5["P3-F05 #40;low#41; verified_by=orchestrator"]
    review_027_controles_que_miran_p3_gates_que_preguntan_antes_1["repair_required #40;package-reviewer#41;"]
    verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1["verified_by=orchestrator"]
    repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1["5 changed files"]
    spawn_027_controles_que_miran_p3_gates_que_preguntan_antes_1["SPAWN-001 implementer AC-06 y AC-07 en worktree aislado, en paralelo con P2 y P4 #91;claude-sonnet-5#93;"]
    spawn_027_controles_que_miran_p3_gates_que_preguntan_antes_2["SPAWN-002 package-reviewer Review independiente de P3 sobre su worktree congelado #91;claude-opus-5#93;"]
    spawn_027_controles_que_miran_p3_gates_que_preguntan_antes_3["SPAWN-003 repair-agent Reparacion consolidada de los cinco hallazgos en alcance de P3 #91;claude-sonnet-5#93;"]
  end
  subgraph sg_027_controles_que_miran_p4_owned_paths_matchea_directorios["P4-owned-paths-matchea-directorios"]
    package_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["package: P4-owned-paths-matchea-directorios"]
    finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["P4-F01 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_2["P4-F02 #40;medium#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_3["P4-F03 #40;low#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_4["P4-F04 #40;low#41; verified_by=orchestrator"]
    finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_5["P4-F06 #40;low#41; verified_by=orchestrator"]
    review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["repair_required #40;package-reviewer#41;"]
    verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["verified_by=orchestrator"]
    repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["6 changed files"]
    spawn_027_controles_que_miran_p4_owned_paths_matchea_directorios_1["SPAWN-001 implementer AC-08 y AC-09 en worktree aislado, en paralelo con P2 y P3 #91;claude-sonnet-5#93;"]
    spawn_027_controles_que_miran_p4_owned_paths_matchea_directorios_2["SPAWN-002 package-reviewer Review independiente de P4 sobre su worktree congelado #91;claude-opus-5#93;"]
    spawn_027_controles_que_miran_p4_owned_paths_matchea_directorios_3["SPAWN-003 repair-agent Reparacion consolidada de los cinco hallazgos en alcance de P4 #91;claude-sonnet-5#93;"]
  end
end
review_027_controles_que_miran_p1_alcance_y_aislamiento_1 -->|produjo| finding_027_controles_que_miran_p1_alcance_y_aislamiento_1
verification_027_controles_que_miran_p1_alcance_y_aislamiento_1 -->|verificó| finding_027_controles_que_miran_p1_alcance_y_aislamiento_1
repair_027_controles_que_miran_p1_alcance_y_aislamiento_1 -->|reparó| finding_027_controles_que_miran_p1_alcance_y_aislamiento_1
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_4
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_5
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_6
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_7
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_8
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_9
review_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_10
review_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_1
review_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_2
review_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|produjo| finding_027_controles_que_miran_p2_nada_escribe_afuera_3
verification_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_1
verification_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_2
verification_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_3
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_4
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_5
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_6
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_7
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_8
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_9
verification_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|verificó| finding_027_controles_que_miran_p2_nada_escribe_afuera_10
repair_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_1
repair_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_2
repair_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_3
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_4
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_5
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_6
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_7
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_8
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_9
repair_027_controles_que_miran_p2_nada_escribe_afuera_2 -->|reparó| finding_027_controles_que_miran_p2_nada_escribe_afuera_10
review_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|produjo| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_1
review_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|produjo| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_2
review_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|produjo| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_3
review_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|produjo| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_4
review_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|produjo| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_5
verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|verificó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_1
verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|verificó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_2
verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|verificó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_3
verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|verificó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_4
verification_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|verificó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_5
repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|reparó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_1
repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|reparó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_2
repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|reparó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_3
repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|reparó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_4
repair_027_controles_que_miran_p3_gates_que_preguntan_antes_1 -->|reparó| finding_027_controles_que_miran_p3_gates_que_preguntan_antes_5
review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|produjo| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_1
review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|produjo| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_2
review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|produjo| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_3
review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|produjo| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_4
review_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|produjo| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_5
verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|verificó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_1
verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|verificó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_2
verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|verificó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_3
verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|verificó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_4
verification_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|verificó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_5
repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|reparó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_1
repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|reparó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_2
repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|reparó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_3
repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|reparó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_4
repair_027_controles_que_miran_p4_owned_paths_matchea_directorios_1 -->|reparó| finding_027_controles_que_miran_p4_owned_paths_matchea_directorios_5
package_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|bloqueó| blocker_027_controles_que_miran_p2_nada_escribe_afuera_1
package_027_controles_que_miran_p2_nada_escribe_afuera_1 -->|bloqueó| blocker_027_controles_que_miran_p2_nada_escribe_afuera_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
