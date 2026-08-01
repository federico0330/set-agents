# 002-adaptive-pi-orchestration · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_002_adaptive_pi_orchestration["002-adaptive-pi-orchestration"]
  feature_002_adaptive_pi_orchestration_1["feature: 002-adaptive-pi-orchestration"]
  subgraph sg_002_adaptive_pi_orchestration_p1_routing_core["P1-routing-core"]
    package_002_adaptive_pi_orchestration_p1_routing_core_1["package: P1-routing-core"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_1["P1-R1-001 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_2["P1-R1-002 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_3["P1-R1-003 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_4["P1-R1-004 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_5["P1-R1-005 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_6["P1-R1-006 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_7["P1-R1-007 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_8["P1-R1-008 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_9["P1-R1-009 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_10["P1-R1-010 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_11["P1-R1-011 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_12["P1-R1-012 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_13["SEC-001 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_14["SEC-002 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_15["SEC-003 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_16["SEC-004 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_17["SEC-005 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_18["SEC-006 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_19["SEC-007 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_20["P1-DR1-001 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_21["P1-DR1-002 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_22["P1-DR1-003 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_23["P1-DR1-004 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_24["P1-DR1-005 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_25["P1-DR1-006 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_26["P1-DR1-007 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_27["P1-DR1-008 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_28["P1-DR1-009 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_29["P1-DR2-001 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_30["P1-DR2-002 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_31["P1-DR2-003 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_32["P1-DR2-004 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_33["P1-DR2-005 #40;medium#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_34["P1-DR2-006 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_35["P1-DR2-007 #40;high#41;"]
    finding_002_adaptive_pi_orchestration_p1_routing_core_36["P1-DR2-008 #40;high#41;"]
    review_002_adaptive_pi_orchestration_p1_routing_core_1["package-reviewer: repair_required"]
    review_002_adaptive_pi_orchestration_p1_routing_core_2["security-auditor: repair_required"]
    review_002_adaptive_pi_orchestration_p1_routing_core_3["package-reviewer: repair_required"]
    review_002_adaptive_pi_orchestration_p1_routing_core_4["delta: repair_required"]
    review_002_adaptive_pi_orchestration_p1_routing_core_5["delta: repair_required"]
    repair_002_adaptive_pi_orchestration_p1_routing_core_1["6 changed files"]
    repair_002_adaptive_pi_orchestration_p1_routing_core_2["6 changed files"]
    blocker_002_adaptive_pi_orchestration_p1_routing_core_1["blocker: resolved"]
    blocker_002_adaptive_pi_orchestration_p1_routing_core_2["blocker: open"]
  end
end
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_1
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_2
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_3
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_4
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_5
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_6
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_7
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_8
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_9
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_10
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_11
review_002_adaptive_pi_orchestration_p1_routing_core_1 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_12
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_13
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_14
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_15
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_16
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_17
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_18
review_002_adaptive_pi_orchestration_p1_routing_core_2 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_19
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_29
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_30
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_31
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_32
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_33
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_34
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_35
review_002_adaptive_pi_orchestration_p1_routing_core_3 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_36
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_20
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_21
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_22
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_23
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_24
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_25
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_26
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_27
review_002_adaptive_pi_orchestration_p1_routing_core_4 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_28
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_29
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_30
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_31
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_32
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_33
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_34
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_35
review_002_adaptive_pi_orchestration_p1_routing_core_5 -->|produjo| finding_002_adaptive_pi_orchestration_p1_routing_core_36
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_1
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_2
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_3
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_4
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_5
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_6
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_7
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_8
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_9
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_10
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_11
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_12
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_13
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_14
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_15
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_16
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_17
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_18
repair_002_adaptive_pi_orchestration_p1_routing_core_1 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_19
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_20
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_21
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_22
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_23
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_24
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_25
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_26
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_27
repair_002_adaptive_pi_orchestration_p1_routing_core_2 -->|reparó| finding_002_adaptive_pi_orchestration_p1_routing_core_28
package_002_adaptive_pi_orchestration_p1_routing_core_1 -->|bloqueó| blocker_002_adaptive_pi_orchestration_p1_routing_core_1
package_002_adaptive_pi_orchestration_p1_routing_core_1 -->|bloqueó| blocker_002_adaptive_pi_orchestration_p1_routing_core_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
