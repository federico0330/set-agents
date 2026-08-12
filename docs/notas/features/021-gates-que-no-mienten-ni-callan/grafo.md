# 021-gates-que-no-mienten-ni-callan · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_021_gates_que_no_mienten_ni_callan["021-gates-que-no-mienten-ni-callan"]
  feature_021_gates_que_no_mienten_ni_callan_1["feature: 021-gates-que-no-mienten-ni-callan"]
  subgraph sg_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica["P1-check-que-verifica"]
    package_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["package: P1-check-que-verifica"]
    finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["P1-F01 #40;medium#41; verified_by=orchestrator"]
    finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2["P1-F02 #40;low#41; verified_by=orchestrator"]
    finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3["P1-F03 #40;low#41; verified_by=orchestrator"]
    finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4["P1-F04 #40;low#41; verified_by=orchestrator"]
    review_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["repair_required #40;orchestrator#41;"]
    verification_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["verified_by=orchestrator"]
    repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["1 changed files"]
    repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2["1 changed files"]
    repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3["2 changed files"]
    repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4["2 changed files"]
    spawn_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1["SPAWN-001 implementer Implementar ADR-0041: que build.sh --check compare de verdad contra Global/ #91;gpt-5.6-sol#93;"]
    spawn_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2["SPAWN-002 package-reviewer Review independiente de P1: el gate que ahora si verifica #91;sonnet#93;"]
  end
  subgraph sg_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan["P2-gates-que-no-callan"]
    package_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["package: P2-gates-que-no-callan"]
    finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["B-01 #40;medium#41; verified_by=orchestrator"]
    finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2["B-02 #40;medium#41; verified_by=orchestrator"]
    finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3["A-01 #40;low#41; verified_by=orchestrator"]
    review_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["repair_required #40;orchestrator#41;"]
    review_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2["repair_required #40;orchestrator#41;"]
    verification_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["verified_by=orchestrator"]
    repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["3 changed files"]
    repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2["3 changed files"]
    repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3["3 changed files"]
    spawn_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1["SPAWN-001 implementer Que los gates no dejen mudo al que los corre, y que la doctrina deje de recomendar el patron que …"]
    spawn_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2["SPAWN-002 package-reviewer Review independiente de P2: latido, doctrina y el limite del watchdog #91;sonnet#93;"]
    spawn_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3["SPAWN-003 package-reviewer Review A de P2 #40;partido en dos#41;: el latido y sus bordes #91;sonnet#93;"]
    spawn_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_4["SPAWN-004 package-reviewer Review B de P2 #40;partido en dos#41;: doctrina, test del antipatron y residuos #91;sonnet#93;"]
  end
end
review_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1
review_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2
review_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3
review_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4
verification_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1
verification_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2
verification_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3
verification_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4
repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_1
repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_2
repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_3
repair_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p1_check_que_verifica_4
review_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1
review_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2
review_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2 -->|produjo| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3
verification_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1
verification_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2
verification_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|verificó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3
repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2
repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_2 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_1
repair_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3 -->|reparó| finding_021_gates_que_no_mienten_ni_callan_p2_gates_que_no_callan_3
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
