# 012-discovered-inventory · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_012_discovered_inventory["012-discovered-inventory"]
  feature_012_discovered_inventory_1["feature: 012-discovered-inventory"]
  subgraph sg_012_discovered_inventory_p1_discovered_inventory["P1-discovered-inventory"]
    package_012_discovered_inventory_p1_discovered_inventory_1["package: P1-discovered-inventory"]
    finding_012_discovered_inventory_p1_discovered_inventory_1["F-01 #40;high#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_2["F-02 #40;high#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_3["F-03 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_4["F-04 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_5["F-05 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_6["F-06 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_7["F-07 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_8["F-08 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_9["F-09 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_10["F-10 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_11["F-11 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_12["F-12 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_13["F-13 #40;low#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_14["SEC-001 #40;critical#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_15["SEC-002 #40;medium#41; verified_by=delta-reviewer"]
    finding_012_discovered_inventory_p1_discovered_inventory_16["N-02 #40;low#41; verified_by=delta-reviewer"]
    review_012_discovered_inventory_p1_discovered_inventory_1["package-reviewer: repair_required"]
    review_012_discovered_inventory_p1_discovered_inventory_2["security-auditor: repair_required"]
    review_012_discovered_inventory_p1_discovered_inventory_3["delta: repair_required"]
    verification_012_discovered_inventory_p1_discovered_inventory_1["verified_by=delta-reviewer"]
    verification_012_discovered_inventory_p1_discovered_inventory_2["verified_by=delta-reviewer"]
    repair_012_discovered_inventory_p1_discovered_inventory_1["7 changed files"]
    repair_012_discovered_inventory_p1_discovered_inventory_2["3 changed files"]
    spawn_012_discovered_inventory_p1_discovered_inventory_1["SPAWN-001 implementer Implementar el catálogo dinámico sondeado #40;AC-01..AC-12#41; contra routing_core/catalog.py, models.t…"]
    spawn_012_discovered_inventory_p1_discovered_inventory_2["SPAWN-002 package-reviewer Revisión independiente del paquete P1-discovered-inventory completo"]
    spawn_012_discovered_inventory_p1_discovered_inventory_3["SPAWN-003 security-auditor Auditoría de seguridad de la regla de colisión de family y el mapa de doble traducción"]
    spawn_012_discovered_inventory_p1_discovered_inventory_4["SPAWN-004 repair-agent Reparación consolidada de 14 hallazgos del panel RP-01 #40;1 critical, 2 high, 4 medium, 7 low#41;"]
    spawn_012_discovered_inventory_p1_discovered_inventory_5["SPAWN-005 delta-reviewer Delta-review acotado a los archivos tocados en la reparación de los 14 hallazgos de RP-01"]
    spawn_012_discovered_inventory_p1_discovered_inventory_6["SPAWN-006 repair-agent Reparación ronda 2: SEC-002 #40;medium, mismo patrón que SEC-001 pero con claude-fable-5#41;, F-10 rea…"]
    spawn_012_discovered_inventory_p1_discovered_inventory_7["SPAWN-007 delta-reviewer Confirmación final de la ronda 2 #40;SEC-002, F-10, N-02#41;"]
    spawn_012_discovered_inventory_p1_discovered_inventory_8["SPAWN-008 integrator Integration validation of accepted P1-discovered-inventory before global gate"]
  end
end
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_1
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_2
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_3
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_4
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_5
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_6
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_7
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_8
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_9
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_10
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_11
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_12
review_012_discovered_inventory_p1_discovered_inventory_1 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_13
review_012_discovered_inventory_p1_discovered_inventory_2 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_14
review_012_discovered_inventory_p1_discovered_inventory_3 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_15
review_012_discovered_inventory_p1_discovered_inventory_3 -->|produjo| finding_012_discovered_inventory_p1_discovered_inventory_16
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_14
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_1
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_2
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_3
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_4
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_5
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_6
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_7
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_8
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_9
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_10
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_11
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_12
verification_012_discovered_inventory_p1_discovered_inventory_1 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_13
verification_012_discovered_inventory_p1_discovered_inventory_2 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_15
verification_012_discovered_inventory_p1_discovered_inventory_2 -->|verificó| finding_012_discovered_inventory_p1_discovered_inventory_16
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_14
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_1
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_2
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_3
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_4
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_5
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_6
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_7
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_8
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_9
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_11
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_12
repair_012_discovered_inventory_p1_discovered_inventory_1 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_13
repair_012_discovered_inventory_p1_discovered_inventory_2 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_15
repair_012_discovered_inventory_p1_discovered_inventory_2 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_10
repair_012_discovered_inventory_p1_discovered_inventory_2 -->|reparó| finding_012_discovered_inventory_p1_discovered_inventory_16
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
