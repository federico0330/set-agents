# 004-adaptive-dispatch · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_004_adaptive_dispatch["004-adaptive-dispatch"]
  feature_004_adaptive_dispatch_1["feature: 004-adaptive-dispatch"]
  subgraph sg_004_adaptive_dispatch_p1_dispatch_core["P1-dispatch-core"]
    package_004_adaptive_dispatch_p1_dispatch_core_1["package: P1-dispatch-core"]
    finding_004_adaptive_dispatch_p1_dispatch_core_1["PKG-N01 #40;high#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_2["PKG-N02 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_3["PKG-N03 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_4["PKG-N04 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_5["PKG-N05 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_6["PKG-N06 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_7["PKG-N07 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_8["PKG-N08 #40;low#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_9["PKG-N09 #40;low#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_10["PKG-N10 #40;low#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_11["PKG-N11 #40;low#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_12["SEC-A01 #40;high#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_13["SEC-A02 #40;medium#41;"]
    finding_004_adaptive_dispatch_p1_dispatch_core_14["SEC-A03 #40;medium#41;"]
    review_004_adaptive_dispatch_p1_dispatch_core_1["package-reviewer: repair_required"]
    review_004_adaptive_dispatch_p1_dispatch_core_2["security-auditor: repair_required"]
    repair_004_adaptive_dispatch_p1_dispatch_core_1["11 changed files"]
  end
  subgraph sg_004_adaptive_dispatch_p2_opencode_lane["P2-opencode-lane"]
    package_004_adaptive_dispatch_p2_opencode_lane_1["package: P2-opencode-lane"]
    finding_004_adaptive_dispatch_p2_opencode_lane_1["PKG-N01 #40;low#41;"]
    finding_004_adaptive_dispatch_p2_opencode_lane_2["PKG-N02 #40;low#41;"]
    finding_004_adaptive_dispatch_p2_opencode_lane_3["SEC-A01 #40;medium#41;"]
    finding_004_adaptive_dispatch_p2_opencode_lane_4["SEC-A02 #40;low#41;"]
    review_004_adaptive_dispatch_p2_opencode_lane_1["package-reviewer: repair_required"]
    review_004_adaptive_dispatch_p2_opencode_lane_2["security-auditor: repair_required"]
    repair_004_adaptive_dispatch_p2_opencode_lane_1["7 changed files"]
  end
  subgraph sg_004_adaptive_dispatch_p3_pi_lane["P3-pi-lane"]
    package_004_adaptive_dispatch_p3_pi_lane_1["package: P3-pi-lane"]
    finding_004_adaptive_dispatch_p3_pi_lane_1["PKG-N01 #40;low#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_2["PKG-N02 #40;low#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_3["PKG-N03 #40;low#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_4["PKG-N04 #40;low#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_5["SEC-A01 #40;high#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_6["SEC-A02 #40;medium#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_7["SEC-A04 #40;low#41;"]
    finding_004_adaptive_dispatch_p3_pi_lane_8["SEC-A05 #40;low#41;"]
    review_004_adaptive_dispatch_p3_pi_lane_1["package-reviewer: repair_required"]
    review_004_adaptive_dispatch_p3_pi_lane_2["security-auditor: repair_required"]
    repair_004_adaptive_dispatch_p3_pi_lane_1["6 changed files"]
  end
end
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_1
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_2
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_3
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_4
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_5
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_6
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_7
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_8
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_9
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_10
review_004_adaptive_dispatch_p1_dispatch_core_1 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_11
review_004_adaptive_dispatch_p1_dispatch_core_2 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_12
review_004_adaptive_dispatch_p1_dispatch_core_2 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_13
review_004_adaptive_dispatch_p1_dispatch_core_2 -->|produjo| finding_004_adaptive_dispatch_p1_dispatch_core_14
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_1
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_2
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_3
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_4
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_5
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_6
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_7
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_8
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_9
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_10
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_11
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_12
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_13
repair_004_adaptive_dispatch_p1_dispatch_core_1 -->|reparó| finding_004_adaptive_dispatch_p1_dispatch_core_14
review_004_adaptive_dispatch_p2_opencode_lane_1 -->|produjo| finding_004_adaptive_dispatch_p2_opencode_lane_1
review_004_adaptive_dispatch_p2_opencode_lane_1 -->|produjo| finding_004_adaptive_dispatch_p2_opencode_lane_2
review_004_adaptive_dispatch_p2_opencode_lane_2 -->|produjo| finding_004_adaptive_dispatch_p2_opencode_lane_3
review_004_adaptive_dispatch_p2_opencode_lane_2 -->|produjo| finding_004_adaptive_dispatch_p2_opencode_lane_4
repair_004_adaptive_dispatch_p2_opencode_lane_1 -->|reparó| finding_004_adaptive_dispatch_p2_opencode_lane_3
repair_004_adaptive_dispatch_p2_opencode_lane_1 -->|reparó| finding_004_adaptive_dispatch_p2_opencode_lane_1
repair_004_adaptive_dispatch_p2_opencode_lane_1 -->|reparó| finding_004_adaptive_dispatch_p2_opencode_lane_2
review_004_adaptive_dispatch_p3_pi_lane_1 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_1
review_004_adaptive_dispatch_p3_pi_lane_1 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_2
review_004_adaptive_dispatch_p3_pi_lane_1 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_3
review_004_adaptive_dispatch_p3_pi_lane_1 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_4
review_004_adaptive_dispatch_p3_pi_lane_2 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_5
review_004_adaptive_dispatch_p3_pi_lane_2 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_6
review_004_adaptive_dispatch_p3_pi_lane_2 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_7
review_004_adaptive_dispatch_p3_pi_lane_2 -->|produjo| finding_004_adaptive_dispatch_p3_pi_lane_8
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_5
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_6
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_7
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_8
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_1
repair_004_adaptive_dispatch_p3_pi_lane_1 -->|reparó| finding_004_adaptive_dispatch_p3_pi_lane_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
