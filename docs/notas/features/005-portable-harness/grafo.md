# 005-portable-harness · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_005_portable_harness["005-portable-harness"]
  feature_005_portable_harness_1["feature: 005-portable-harness"]
  subgraph sg_005_portable_harness_p1_portable_core["P1-portable-core"]
    package_005_portable_harness_p1_portable_core_1["package: P1-portable-core"]
    finding_005_portable_harness_p1_portable_core_1["P1-REV-001 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_2["P1-REV-002 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_3["P1-REV-003 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_4["P1-REV-004 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_5["P1-REV-005 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_6["P1-REV-006 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_7["P1-REV-007 #40;medium#41;"]
    finding_005_portable_harness_p1_portable_core_8["P1-REV-008 #40;medium#41;"]
    finding_005_portable_harness_p1_portable_core_9["P1-DLT-001 #40;high#41;"]
    finding_005_portable_harness_p1_portable_core_10["P1-DLT-002 #40;medium#41;"]
    review_005_portable_harness_p1_portable_core_1["delta: repair_required"]
    review_005_portable_harness_p1_portable_core_2["repair_required #40;orchestrator#41;"]
    repair_005_portable_harness_p1_portable_core_1["4 changed files"]
    repair_005_portable_harness_p1_portable_core_2["8 changed files"]
    blocker_005_portable_harness_p1_portable_core_1["blocker: resolved"]
    blocker_005_portable_harness_p1_portable_core_2["blocker: resolved"]
  end
  subgraph sg_005_portable_harness_p2_vault_mandatory["P2-vault-mandatory"]
    package_005_portable_harness_p2_vault_mandatory_1["package: P2-vault-mandatory"]
    finding_005_portable_harness_p2_vault_mandatory_1["SEC-001 #40;critical#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_2["SEC-002 #40;critical#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_3["SEC-003 #40;high#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_4["SEC-004 #40;high#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_5["SEC-005 #40;medium#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_6["SEC-006 #40;medium#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_7["SEC-007 #40;low#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_8["SEC-008 #40;medium#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_9["SEC-009 #40;low#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_10["SEC-010 #40;low#41; verified_by=finding-verifier"]
    finding_005_portable_harness_p2_vault_mandatory_11["DR-001 #40;medium#41; verified_by=orchestrator"]
    finding_005_portable_harness_p2_vault_mandatory_12["DR-002 #40;medium#41; verified_by=orchestrator"]
    finding_005_portable_harness_p2_vault_mandatory_13["DR-004 #40;medium#41; verified_by=orchestrator"]
    finding_005_portable_harness_p2_vault_mandatory_14["DR-005 #40;low#41;"]
    finding_005_portable_harness_p2_vault_mandatory_15["DR-006 #40;low#41;"]
    review_005_portable_harness_p2_vault_mandatory_1["security-auditor: repair_required"]
    review_005_portable_harness_p2_vault_mandatory_2["delta: repair_required"]
    verification_005_portable_harness_p2_vault_mandatory_1["verified_by=finding-verifier"]
    verification_005_portable_harness_p2_vault_mandatory_2["verified_by=orchestrator"]
    repair_005_portable_harness_p2_vault_mandatory_1["12 changed files"]
    repair_005_portable_harness_p2_vault_mandatory_2["4 changed files"]
  end
  subgraph sg_005_portable_harness_p3_tui["P3-tui"]
    package_005_portable_harness_p3_tui_1["package: P3-tui"]
    finding_005_portable_harness_p3_tui_1["F-01 #40;high#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_2["F-02 #40;high#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_3["F-03 #40;high#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_4["F-04 #40;high#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_5["F-05 #40;medium#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_6["F-06 #40;low#41;"]
    finding_005_portable_harness_p3_tui_7["F-07 #40;medium#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_8["F-08 #40;medium#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_9["F-09 #40;low#41;"]
    finding_005_portable_harness_p3_tui_10["F-10 #40;low#41;"]
    finding_005_portable_harness_p3_tui_11["D-02 #40;high#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_12["D-03 #40;medium#41; verified_by=repair-agent"]
    finding_005_portable_harness_p3_tui_13["D-05 #40;low#41;"]
    finding_005_portable_harness_p3_tui_14["D-06 #40;low#41;"]
    review_005_portable_harness_p3_tui_1["package-reviewer: repair_required"]
    review_005_portable_harness_p3_tui_2["delta: repair_required"]
    verification_005_portable_harness_p3_tui_1["verified_by=repair-agent"]
    verification_005_portable_harness_p3_tui_2["verified_by=repair-agent"]
    repair_005_portable_harness_p3_tui_1["2 changed files"]
    repair_005_portable_harness_p3_tui_2["4 changed files"]
    repair_005_portable_harness_p3_tui_3["3 changed files"]
  end
end
review_005_portable_harness_p1_portable_core_1 -->|produjo| finding_005_portable_harness_p1_portable_core_9
review_005_portable_harness_p1_portable_core_1 -->|produjo| finding_005_portable_harness_p1_portable_core_10
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_1
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_2
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_3
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_4
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_5
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_6
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_7
review_005_portable_harness_p1_portable_core_2 -->|produjo| finding_005_portable_harness_p1_portable_core_8
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_1
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_2
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_3
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_4
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_5
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_6
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_7
repair_005_portable_harness_p1_portable_core_1 -->|reparó| finding_005_portable_harness_p1_portable_core_8
repair_005_portable_harness_p1_portable_core_2 -->|reparó| finding_005_portable_harness_p1_portable_core_9
repair_005_portable_harness_p1_portable_core_2 -->|reparó| finding_005_portable_harness_p1_portable_core_10
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_1
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_2
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_3
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_4
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_5
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_6
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_7
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_8
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_9
review_005_portable_harness_p2_vault_mandatory_1 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_10
review_005_portable_harness_p2_vault_mandatory_2 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_11
review_005_portable_harness_p2_vault_mandatory_2 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_12
review_005_portable_harness_p2_vault_mandatory_2 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_13
review_005_portable_harness_p2_vault_mandatory_2 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_14
review_005_portable_harness_p2_vault_mandatory_2 -->|produjo| finding_005_portable_harness_p2_vault_mandatory_15
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_1
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_2
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_3
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_4
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_5
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_6
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_7
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_8
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_9
verification_005_portable_harness_p2_vault_mandatory_1 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_10
verification_005_portable_harness_p2_vault_mandatory_2 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_11
verification_005_portable_harness_p2_vault_mandatory_2 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_12
verification_005_portable_harness_p2_vault_mandatory_2 -->|verificó| finding_005_portable_harness_p2_vault_mandatory_13
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_1
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_2
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_3
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_4
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_5
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_6
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_7
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_8
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_9
repair_005_portable_harness_p2_vault_mandatory_1 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_10
repair_005_portable_harness_p2_vault_mandatory_2 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_11
repair_005_portable_harness_p2_vault_mandatory_2 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_12
repair_005_portable_harness_p2_vault_mandatory_2 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_13
repair_005_portable_harness_p2_vault_mandatory_2 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_14
repair_005_portable_harness_p2_vault_mandatory_2 -->|reparó| finding_005_portable_harness_p2_vault_mandatory_15
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_1
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_2
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_3
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_4
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_5
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_6
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_7
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_8
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_9
review_005_portable_harness_p3_tui_1 -->|produjo| finding_005_portable_harness_p3_tui_10
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_1
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_11
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_12
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_8
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_13
review_005_portable_harness_p3_tui_2 -->|produjo| finding_005_portable_harness_p3_tui_14
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_1
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_2
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_3
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_4
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_5
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_7
verification_005_portable_harness_p3_tui_1 -->|verificó| finding_005_portable_harness_p3_tui_8
verification_005_portable_harness_p3_tui_2 -->|verificó| finding_005_portable_harness_p3_tui_1
verification_005_portable_harness_p3_tui_2 -->|verificó| finding_005_portable_harness_p3_tui_11
verification_005_portable_harness_p3_tui_2 -->|verificó| finding_005_portable_harness_p3_tui_12
verification_005_portable_harness_p3_tui_2 -->|verificó| finding_005_portable_harness_p3_tui_8
repair_005_portable_harness_p3_tui_1 -->|reparó| finding_005_portable_harness_p3_tui_1
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_2
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_3
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_4
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_5
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_6
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_7
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_8
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_9
repair_005_portable_harness_p3_tui_2 -->|reparó| finding_005_portable_harness_p3_tui_10
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_1
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_11
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_12
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_8
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_13
repair_005_portable_harness_p3_tui_3 -->|reparó| finding_005_portable_harness_p3_tui_14
package_005_portable_harness_p1_portable_core_1 -->|bloqueó| blocker_005_portable_harness_p1_portable_core_1
package_005_portable_harness_p1_portable_core_1 -->|bloqueó| blocker_005_portable_harness_p1_portable_core_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
