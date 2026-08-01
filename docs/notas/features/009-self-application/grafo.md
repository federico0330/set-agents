# 009-self-application · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_009_self_application["009-self-application"]
  feature_009_self_application_1["feature: 009-self-application"]
  subgraph sg_009_self_application_p1_knowledge_home["P1-knowledge-home"]
    package_009_self_application_p1_knowledge_home_1["package: P1-knowledge-home"]
    finding_009_self_application_p1_knowledge_home_1["F-01 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_2["F-03 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_3["F-05 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_4["F-02 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_5["F-04 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_6["F-06 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_7["F-07 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p1_knowledge_home_8["F-08 #40;low#41; verified_by=finding-verifier"]
    review_009_self_application_p1_knowledge_home_1["package-reviewer: repair_required"]
    review_009_self_application_p1_knowledge_home_2["architect: repair_required"]
    verification_009_self_application_p1_knowledge_home_1["verified_by=finding-verifier"]
    verification_009_self_application_p1_knowledge_home_2["verified_by=finding-verifier"]
    verification_009_self_application_p1_knowledge_home_3["verified_by=finding-verifier"]
    repair_009_self_application_p1_knowledge_home_1["4 changed files"]
  end
  subgraph sg_009_self_application_p2_state_machine_required["P2-state-machine-required"]
    package_009_self_application_p2_state_machine_required_1["package: P2-state-machine-required"]
    finding_009_self_application_p2_state_machine_required_1["F-02 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_2["F-04 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_3["F-05 #40;low#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_4["F-06 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_5["F-07 #40;low#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_6["F-01 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_7["F-03 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_8["F-08 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p2_state_machine_required_9["F-09 #40;low#41; verified_by=finding-verifier"]
    review_009_self_application_p2_state_machine_required_1["architect: repair_required"]
    review_009_self_application_p2_state_machine_required_2["package-reviewer: repair_required"]
    verification_009_self_application_p2_state_machine_required_1["verified_by=finding-verifier"]
    repair_009_self_application_p2_state_machine_required_1["3 changed files"]
  end
  subgraph sg_009_self_application_p3_panel_integrity["P3-panel-integrity"]
    package_009_self_application_p3_panel_integrity_1["package: P3-panel-integrity"]
    finding_009_self_application_p3_panel_integrity_1["F-01 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p3_panel_integrity_2["F-02 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p3_panel_integrity_3["F-03 #40;high#41; verified_by=finding-verifier"]
    finding_009_self_application_p3_panel_integrity_4["F-04 #40;medium#41; verified_by=finding-verifier"]
    finding_009_self_application_p3_panel_integrity_5["F-05 #40;medium#41; verified_by=finding-verifier"]
    review_009_self_application_p3_panel_integrity_1["package-reviewer: repair_required"]
    review_009_self_application_p3_panel_integrity_2["architect: repair_required"]
    review_009_self_application_p3_panel_integrity_3["delta: repair_required"]
    verification_009_self_application_p3_panel_integrity_1["verified_by=finding-verifier"]
    verification_009_self_application_p3_panel_integrity_2["verified_by=finding-verifier"]
    repair_009_self_application_p3_panel_integrity_1["4 changed files"]
    repair_009_self_application_p3_panel_integrity_2["3 changed files"]
  end
end
review_009_self_application_p1_knowledge_home_1 -->|produjo| finding_009_self_application_p1_knowledge_home_1
review_009_self_application_p1_knowledge_home_1 -->|produjo| finding_009_self_application_p1_knowledge_home_2
review_009_self_application_p1_knowledge_home_1 -->|produjo| finding_009_self_application_p1_knowledge_home_3
review_009_self_application_p1_knowledge_home_2 -->|produjo| finding_009_self_application_p1_knowledge_home_4
review_009_self_application_p1_knowledge_home_2 -->|produjo| finding_009_self_application_p1_knowledge_home_5
review_009_self_application_p1_knowledge_home_2 -->|produjo| finding_009_self_application_p1_knowledge_home_6
review_009_self_application_p1_knowledge_home_2 -->|produjo| finding_009_self_application_p1_knowledge_home_7
review_009_self_application_p1_knowledge_home_2 -->|produjo| finding_009_self_application_p1_knowledge_home_8
verification_009_self_application_p1_knowledge_home_1 -->|verificó| finding_009_self_application_p1_knowledge_home_4
verification_009_self_application_p1_knowledge_home_2 -->|refutó| finding_009_self_application_p1_knowledge_home_3
verification_009_self_application_p1_knowledge_home_2 -->|verificó| finding_009_self_application_p1_knowledge_home_2
verification_009_self_application_p1_knowledge_home_3 -->|refutó| finding_009_self_application_p1_knowledge_home_1
verification_009_self_application_p1_knowledge_home_3 -->|refutó| finding_009_self_application_p1_knowledge_home_6
verification_009_self_application_p1_knowledge_home_3 -->|refutó| finding_009_self_application_p1_knowledge_home_7
verification_009_self_application_p1_knowledge_home_3 -->|refutó| finding_009_self_application_p1_knowledge_home_8
verification_009_self_application_p1_knowledge_home_3 -->|verificó| finding_009_self_application_p1_knowledge_home_5
repair_009_self_application_p1_knowledge_home_1 -->|reparó| finding_009_self_application_p1_knowledge_home_4
repair_009_self_application_p1_knowledge_home_1 -->|reparó| finding_009_self_application_p1_knowledge_home_2
repair_009_self_application_p1_knowledge_home_1 -->|reparó| finding_009_self_application_p1_knowledge_home_5
review_009_self_application_p2_state_machine_required_1 -->|produjo| finding_009_self_application_p2_state_machine_required_1
review_009_self_application_p2_state_machine_required_1 -->|produjo| finding_009_self_application_p2_state_machine_required_2
review_009_self_application_p2_state_machine_required_1 -->|produjo| finding_009_self_application_p2_state_machine_required_3
review_009_self_application_p2_state_machine_required_1 -->|produjo| finding_009_self_application_p2_state_machine_required_4
review_009_self_application_p2_state_machine_required_1 -->|produjo| finding_009_self_application_p2_state_machine_required_5
review_009_self_application_p2_state_machine_required_2 -->|produjo| finding_009_self_application_p2_state_machine_required_6
review_009_self_application_p2_state_machine_required_2 -->|produjo| finding_009_self_application_p2_state_machine_required_7
review_009_self_application_p2_state_machine_required_2 -->|produjo| finding_009_self_application_p2_state_machine_required_8
review_009_self_application_p2_state_machine_required_2 -->|produjo| finding_009_self_application_p2_state_machine_required_9
verification_009_self_application_p2_state_machine_required_1 -->|refutó| finding_009_self_application_p2_state_machine_required_2
verification_009_self_application_p2_state_machine_required_1 -->|refutó| finding_009_self_application_p2_state_machine_required_3
verification_009_self_application_p2_state_machine_required_1 -->|refutó| finding_009_self_application_p2_state_machine_required_4
verification_009_self_application_p2_state_machine_required_1 -->|refutó| finding_009_self_application_p2_state_machine_required_5
verification_009_self_application_p2_state_machine_required_1 -->|refutó| finding_009_self_application_p2_state_machine_required_9
verification_009_self_application_p2_state_machine_required_1 -->|verificó| finding_009_self_application_p2_state_machine_required_6
verification_009_self_application_p2_state_machine_required_1 -->|verificó| finding_009_self_application_p2_state_machine_required_1
verification_009_self_application_p2_state_machine_required_1 -->|verificó| finding_009_self_application_p2_state_machine_required_7
verification_009_self_application_p2_state_machine_required_1 -->|verificó| finding_009_self_application_p2_state_machine_required_8
repair_009_self_application_p2_state_machine_required_1 -->|reparó| finding_009_self_application_p2_state_machine_required_6
repair_009_self_application_p2_state_machine_required_1 -->|reparó| finding_009_self_application_p2_state_machine_required_1
repair_009_self_application_p2_state_machine_required_1 -->|reparó| finding_009_self_application_p2_state_machine_required_7
repair_009_self_application_p2_state_machine_required_1 -->|reparó| finding_009_self_application_p2_state_machine_required_8
review_009_self_application_p3_panel_integrity_1 -->|produjo| finding_009_self_application_p3_panel_integrity_1
review_009_self_application_p3_panel_integrity_1 -->|produjo| finding_009_self_application_p3_panel_integrity_2
review_009_self_application_p3_panel_integrity_2 -->|produjo| finding_009_self_application_p3_panel_integrity_3
review_009_self_application_p3_panel_integrity_2 -->|produjo| finding_009_self_application_p3_panel_integrity_4
review_009_self_application_p3_panel_integrity_3 -->|produjo| finding_009_self_application_p3_panel_integrity_5
verification_009_self_application_p3_panel_integrity_1 -->|refutó| finding_009_self_application_p3_panel_integrity_4
verification_009_self_application_p3_panel_integrity_1 -->|verificó| finding_009_self_application_p3_panel_integrity_1
verification_009_self_application_p3_panel_integrity_1 -->|verificó| finding_009_self_application_p3_panel_integrity_2
verification_009_self_application_p3_panel_integrity_1 -->|verificó| finding_009_self_application_p3_panel_integrity_3
verification_009_self_application_p3_panel_integrity_2 -->|verificó| finding_009_self_application_p3_panel_integrity_5
repair_009_self_application_p3_panel_integrity_1 -->|reparó| finding_009_self_application_p3_panel_integrity_1
repair_009_self_application_p3_panel_integrity_1 -->|reparó| finding_009_self_application_p3_panel_integrity_2
repair_009_self_application_p3_panel_integrity_1 -->|reparó| finding_009_self_application_p3_panel_integrity_3
repair_009_self_application_p3_panel_integrity_2 -->|reparó| finding_009_self_application_p3_panel_integrity_5
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
