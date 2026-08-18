# 028-narracion-que-ensena · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_028_narracion_que_ensena["028-narracion-que-ensena"]
  feature_028_narracion_que_ensena_1["feature: 028-narracion-que-ensena"]
  subgraph sg_028_narracion_que_ensena_n1_campos_que_obligan["N1-campos-que-obligan"]
    package_028_narracion_que_ensena_n1_campos_que_obligan_1["package: N1-campos-que-obligan"]
    finding_028_narracion_que_ensena_n1_campos_que_obligan_1["N1-F01 #40;high#41; verified_by=finding-verifier"]
    finding_028_narracion_que_ensena_n1_campos_que_obligan_2["N1-F02 #40;high#41; verified_by=finding-verifier"]
    finding_028_narracion_que_ensena_n1_campos_que_obligan_3["N1-F03 #40;medium#41; verified_by=finding-verifier"]
    review_028_narracion_que_ensena_n1_campos_que_obligan_1["repair_required #40;package-reviewer#41;"]
    verification_028_narracion_que_ensena_n1_campos_que_obligan_1["verified_by=finding-verifier"]
    repair_028_narracion_que_ensena_n1_campos_que_obligan_1["1 changed files"]
    spawn_028_narracion_que_ensena_n1_campos_que_obligan_1["SPAWN-001 package-reviewer package-review #91;sonnet#93;"]
    blocker_028_narracion_que_ensena_n1_campos_que_obligan_1["blocker: resolved"]
  end
  subgraph sg_028_narracion_que_ensena_n2_doctrina_que_explica["N2-doctrina-que-explica"]
    package_028_narracion_que_ensena_n2_doctrina_que_explica_1["package: N2-doctrina-que-explica"]
    finding_028_narracion_que_ensena_n2_doctrina_que_explica_1["N2-F01 #40;high#41; verified_by=finding-verifier"]
    review_028_narracion_que_ensena_n2_doctrina_que_explica_1["repair_required #40;package-reviewer#41;"]
    verification_028_narracion_que_ensena_n2_doctrina_que_explica_1["verified_by=finding-verifier"]
    repair_028_narracion_que_ensena_n2_doctrina_que_explica_1["1 changed files"]
    spawn_028_narracion_que_ensena_n2_doctrina_que_explica_1["SPAWN-001 package-reviewer package-review #91;sonnet#93;"]
  end
  subgraph sg_028_narracion_que_ensena_n3b_los_campos_donde_se_leen["N3b-los-campos-donde-se-leen"]
    package_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["package: N3b-los-campos-donde-se-leen"]
    finding_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["N3b-F01 #40;medium#41; verified_by=finding-verifier"]
    review_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["repair_required #40;package-reviewer#41;"]
    verification_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["verified_by=finding-verifier"]
    repair_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["2 changed files"]
    spawn_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1["SPAWN-001 package-reviewer package-review #91;sonnet#93;"]
  end
end
review_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|produjo| finding_028_narracion_que_ensena_n1_campos_que_obligan_1
review_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|produjo| finding_028_narracion_que_ensena_n1_campos_que_obligan_2
review_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|produjo| finding_028_narracion_que_ensena_n1_campos_que_obligan_3
verification_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|verificó| finding_028_narracion_que_ensena_n1_campos_que_obligan_1
verification_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|verificó| finding_028_narracion_que_ensena_n1_campos_que_obligan_2
verification_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|verificó| finding_028_narracion_que_ensena_n1_campos_que_obligan_3
repair_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|reparó| finding_028_narracion_que_ensena_n1_campos_que_obligan_1
repair_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|reparó| finding_028_narracion_que_ensena_n1_campos_que_obligan_2
repair_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|reparó| finding_028_narracion_que_ensena_n1_campos_que_obligan_3
review_028_narracion_que_ensena_n2_doctrina_que_explica_1 -->|produjo| finding_028_narracion_que_ensena_n2_doctrina_que_explica_1
verification_028_narracion_que_ensena_n2_doctrina_que_explica_1 -->|verificó| finding_028_narracion_que_ensena_n2_doctrina_que_explica_1
repair_028_narracion_que_ensena_n2_doctrina_que_explica_1 -->|reparó| finding_028_narracion_que_ensena_n2_doctrina_que_explica_1
review_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1 -->|produjo| finding_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1
verification_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1 -->|verificó| finding_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1
repair_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1 -->|reparó| finding_028_narracion_que_ensena_n3b_los_campos_donde_se_leen_1
package_028_narracion_que_ensena_n1_campos_que_obligan_1 -->|bloqueó| blocker_028_narracion_que_ensena_n1_campos_que_obligan_1
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
