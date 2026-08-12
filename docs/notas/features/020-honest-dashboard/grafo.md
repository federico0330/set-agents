# 020-honest-dashboard · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_020_honest_dashboard["020-honest-dashboard"]
  feature_020_honest_dashboard_1["feature: 020-honest-dashboard"]
  subgraph sg_020_honest_dashboard_p1_digest_no_esconde["P1-digest-no-esconde"]
    package_020_honest_dashboard_p1_digest_no_esconde_1["package: P1-digest-no-esconde"]
    finding_020_honest_dashboard_p1_digest_no_esconde_1["F-01 #40;high#41; verified_by=orchestrator"]
    finding_020_honest_dashboard_p1_digest_no_esconde_2["F-02 #40;medium#41; verified_by=orchestrator"]
    finding_020_honest_dashboard_p1_digest_no_esconde_3["F-03 #40;medium#41; verified_by=orchestrator"]
    review_020_honest_dashboard_p1_digest_no_esconde_1["repair_required #40;orchestrator#41;"]
    verification_020_honest_dashboard_p1_digest_no_esconde_1["verified_by=orchestrator"]
    repair_020_honest_dashboard_p1_digest_no_esconde_1["3 changed files"]
    repair_020_honest_dashboard_p1_digest_no_esconde_2["3 changed files"]
    repair_020_honest_dashboard_p1_digest_no_esconde_3["3 changed files"]
    spawn_020_honest_dashboard_p1_digest_no_esconde_1["SPAWN-001 implementer Implementar ADR-0040: predicado compartido y tablero que no esconde lo bloqueado #91;gpt-5.6-sol#93;"]
    spawn_020_honest_dashboard_p1_digest_no_esconde_2["SPAWN-002 package-reviewer Review independiente de P1: tablero honesto y predicado compartido #91;sonnet#93;"]
  end
  subgraph sg_020_honest_dashboard_p2_anclas_verificables["P2-anclas-verificables"]
    package_020_honest_dashboard_p2_anclas_verificables_1["package: P2-anclas-verificables"]
    finding_020_honest_dashboard_p2_anclas_verificables_1["F-01 #40;medium#41; verified_by=orchestrator"]
    finding_020_honest_dashboard_p2_anclas_verificables_2["F-02 #40;medium#41; verified_by=orchestrator"]
    finding_020_honest_dashboard_p2_anclas_verificables_3["F-03 #40;low#41;"]
    finding_020_honest_dashboard_p2_anclas_verificables_4["F-04 #40;low#41;"]
    finding_020_honest_dashboard_p2_anclas_verificables_5["F-05 #40;medium#41; verified_by=orchestrator"]
    review_020_honest_dashboard_p2_anclas_verificables_1["delta: repair_required"]
    review_020_honest_dashboard_p2_anclas_verificables_2["repair_required #40;orchestrator#41;"]
    verification_020_honest_dashboard_p2_anclas_verificables_1["verified_by=orchestrator"]
    verification_020_honest_dashboard_p2_anclas_verificables_2["verified_by=orchestrator"]
    repair_020_honest_dashboard_p2_anclas_verificables_1["3 changed files"]
    repair_020_honest_dashboard_p2_anclas_verificables_2["3 changed files"]
    repair_020_honest_dashboard_p2_anclas_verificables_3["3 changed files"]
    repair_020_honest_dashboard_p2_anclas_verificables_4["3 changed files"]
    spawn_020_honest_dashboard_p2_anclas_verificables_1["SPAWN-001 implementer Implementar el verificador de anclas file:line de docs/modules/ #91;gpt-5.6-sol#93;"]
    spawn_020_honest_dashboard_p2_anclas_verificables_2["SPAWN-002 implementer Relanzamiento tras stall: verificador de anclas file:line #91;gpt-5.6-sol#93;"]
  end
end
review_020_honest_dashboard_p1_digest_no_esconde_1 -->|produjo| finding_020_honest_dashboard_p1_digest_no_esconde_1
review_020_honest_dashboard_p1_digest_no_esconde_1 -->|produjo| finding_020_honest_dashboard_p1_digest_no_esconde_2
review_020_honest_dashboard_p1_digest_no_esconde_1 -->|produjo| finding_020_honest_dashboard_p1_digest_no_esconde_3
verification_020_honest_dashboard_p1_digest_no_esconde_1 -->|verificó| finding_020_honest_dashboard_p1_digest_no_esconde_1
verification_020_honest_dashboard_p1_digest_no_esconde_1 -->|verificó| finding_020_honest_dashboard_p1_digest_no_esconde_2
verification_020_honest_dashboard_p1_digest_no_esconde_1 -->|verificó| finding_020_honest_dashboard_p1_digest_no_esconde_3
repair_020_honest_dashboard_p1_digest_no_esconde_1 -->|reparó| finding_020_honest_dashboard_p1_digest_no_esconde_1
repair_020_honest_dashboard_p1_digest_no_esconde_2 -->|reparó| finding_020_honest_dashboard_p1_digest_no_esconde_2
repair_020_honest_dashboard_p1_digest_no_esconde_3 -->|reparó| finding_020_honest_dashboard_p1_digest_no_esconde_3
review_020_honest_dashboard_p2_anclas_verificables_1 -->|produjo| finding_020_honest_dashboard_p2_anclas_verificables_5
review_020_honest_dashboard_p2_anclas_verificables_2 -->|produjo| finding_020_honest_dashboard_p2_anclas_verificables_1
review_020_honest_dashboard_p2_anclas_verificables_2 -->|produjo| finding_020_honest_dashboard_p2_anclas_verificables_2
review_020_honest_dashboard_p2_anclas_verificables_2 -->|produjo| finding_020_honest_dashboard_p2_anclas_verificables_3
review_020_honest_dashboard_p2_anclas_verificables_2 -->|produjo| finding_020_honest_dashboard_p2_anclas_verificables_4
verification_020_honest_dashboard_p2_anclas_verificables_1 -->|verificó| finding_020_honest_dashboard_p2_anclas_verificables_1
verification_020_honest_dashboard_p2_anclas_verificables_1 -->|verificó| finding_020_honest_dashboard_p2_anclas_verificables_2
verification_020_honest_dashboard_p2_anclas_verificables_2 -->|verificó| finding_020_honest_dashboard_p2_anclas_verificables_5
repair_020_honest_dashboard_p2_anclas_verificables_1 -->|reparó| finding_020_honest_dashboard_p2_anclas_verificables_1
repair_020_honest_dashboard_p2_anclas_verificables_2 -->|reparó| finding_020_honest_dashboard_p2_anclas_verificables_2
repair_020_honest_dashboard_p2_anclas_verificables_3 -->|reparó| finding_020_honest_dashboard_p2_anclas_verificables_3
repair_020_honest_dashboard_p2_anclas_verificables_4 -->|reparó| finding_020_honest_dashboard_p2_anclas_verificables_5
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
