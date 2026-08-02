# 006-execution-graph · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_006_execution_graph["006-execution-graph"]
  feature_006_execution_graph_1["feature: 006-execution-graph"]
  subgraph sg_006_execution_graph_p3_graph_view["P3-graph-view"]
    package_006_execution_graph_p3_graph_view_1["package: P3-graph-view"]
    finding_006_execution_graph_p3_graph_view_1["PR-01 #40;high#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_2["PR-02 #40;medium#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_3["PR-03 #40;medium#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_4["PR-04 #40;low#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_5["PR-05 #40;low#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_6["PR-06 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_7["PR-07 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_8["PR-08 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_9["SEC-001 #40;critical#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_10["SEC-002 #40;critical#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_11["SEC-003 #40;medium#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_12["SEC-004 #40;medium#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_13["SEC-005 #40;low#41; verified_by=repair-agent"]
    finding_006_execution_graph_p3_graph_view_14["D-01 #40;medium#41; verified_by=orchestrator"]
    finding_006_execution_graph_p3_graph_view_15["D-02 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_16["D-03 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_17["D-04 #40;low#41;"]
    finding_006_execution_graph_p3_graph_view_18["D-05 #40;low#41;"]
    review_006_execution_graph_p3_graph_view_1["package-reviewer: repair_required"]
    review_006_execution_graph_p3_graph_view_2["security-auditor: repair_required"]
    review_006_execution_graph_p3_graph_view_3["delta: repair_required"]
    verification_006_execution_graph_p3_graph_view_1["verified_by=repair-agent"]
    verification_006_execution_graph_p3_graph_view_2["verified_by=orchestrator"]
    repair_006_execution_graph_p3_graph_view_1["5 changed files"]
    repair_006_execution_graph_p3_graph_view_2["3 changed files"]
    repair_006_execution_graph_p3_graph_view_3["10 changed files"]
    spawn_006_execution_graph_p3_graph_view_1["SPAWN-009 integrator Integration validation of accepted P3-graph-view against approved contract before global gate"]
  end
end
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_1
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_2
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_3
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_4
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_5
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_6
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_7
review_006_execution_graph_p3_graph_view_1 -->|produjo| finding_006_execution_graph_p3_graph_view_8
review_006_execution_graph_p3_graph_view_2 -->|produjo| finding_006_execution_graph_p3_graph_view_9
review_006_execution_graph_p3_graph_view_2 -->|produjo| finding_006_execution_graph_p3_graph_view_10
review_006_execution_graph_p3_graph_view_2 -->|produjo| finding_006_execution_graph_p3_graph_view_11
review_006_execution_graph_p3_graph_view_2 -->|produjo| finding_006_execution_graph_p3_graph_view_12
review_006_execution_graph_p3_graph_view_2 -->|produjo| finding_006_execution_graph_p3_graph_view_13
review_006_execution_graph_p3_graph_view_3 -->|produjo| finding_006_execution_graph_p3_graph_view_14
review_006_execution_graph_p3_graph_view_3 -->|produjo| finding_006_execution_graph_p3_graph_view_15
review_006_execution_graph_p3_graph_view_3 -->|produjo| finding_006_execution_graph_p3_graph_view_16
review_006_execution_graph_p3_graph_view_3 -->|produjo| finding_006_execution_graph_p3_graph_view_17
review_006_execution_graph_p3_graph_view_3 -->|produjo| finding_006_execution_graph_p3_graph_view_18
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_9
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_10
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_1
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_2
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_3
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_11
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_12
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_13
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_4
verification_006_execution_graph_p3_graph_view_1 -->|verificó| finding_006_execution_graph_p3_graph_view_5
verification_006_execution_graph_p3_graph_view_2 -->|verificó| finding_006_execution_graph_p3_graph_view_14
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_9
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_10
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_1
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_2
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_3
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_11
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_12
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_13
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_4
repair_006_execution_graph_p3_graph_view_1 -->|reparó| finding_006_execution_graph_p3_graph_view_5
repair_006_execution_graph_p3_graph_view_2 -->|reparó| finding_006_execution_graph_p3_graph_view_6
repair_006_execution_graph_p3_graph_view_2 -->|reparó| finding_006_execution_graph_p3_graph_view_7
repair_006_execution_graph_p3_graph_view_2 -->|reparó| finding_006_execution_graph_p3_graph_view_8
repair_006_execution_graph_p3_graph_view_3 -->|reparó| finding_006_execution_graph_p3_graph_view_14
repair_006_execution_graph_p3_graph_view_3 -->|reparó| finding_006_execution_graph_p3_graph_view_15
repair_006_execution_graph_p3_graph_view_3 -->|reparó| finding_006_execution_graph_p3_graph_view_16
repair_006_execution_graph_p3_graph_view_3 -->|reparó| finding_006_execution_graph_p3_graph_view_17
repair_006_execution_graph_p3_graph_view_3 -->|reparó| finding_006_execution_graph_p3_graph_view_18
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
