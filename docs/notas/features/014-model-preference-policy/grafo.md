# 014-model-preference-policy · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_014_model_preference_policy["014-model-preference-policy"]
  feature_014_model_preference_policy_1["feature: 014-model-preference-policy"]
  subgraph sg_014_model_preference_policy_p1_model_preference_policy["P1-model-preference-policy"]
    package_014_model_preference_policy_p1_model_preference_policy_1["package: P1-model-preference-policy"]
    finding_014_model_preference_policy_p1_model_preference_policy_1["SEC14-01 #40;low#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_2["RF14-01 #40;medium#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_3["RF14-02 #40;low#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_4["RF14-03 #40;medium#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_5["RF14-04 #40;low#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_6["RF14-05 #40;low#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_7["RF14-06 #40;low#41; verified_by=finding-verifier"]
    finding_014_model_preference_policy_p1_model_preference_policy_8["RF14-07 #40;low#41; verified_by=finding-verifier"]
    review_014_model_preference_policy_p1_model_preference_policy_1["security-auditor: repair_required"]
    review_014_model_preference_policy_p1_model_preference_policy_2["package-reviewer: repair_required"]
    verification_014_model_preference_policy_p1_model_preference_policy_1["verified_by=finding-verifier"]
    repair_014_model_preference_policy_p1_model_preference_policy_1["5 changed files"]
    spawn_014_model_preference_policy_p1_model_preference_policy_1["SPAWN-001 implementer Implement P1-model-preference-policy: taxonomy, config+CLI, sort-key, observability, ADR"]
    spawn_014_model_preference_policy_p1_model_preference_policy_2["SPAWN-002 gate-runner Serialized heavy gates for 014-P1 #40;also evidence for 016-P1 testing#41;"]
    spawn_014_model_preference_policy_p1_model_preference_policy_3["SPAWN-003 package-reviewer RP-014-01 deep review of P1 vs AC-01..AC-09"]
    spawn_014_model_preference_policy_p1_model_preference_policy_4["SPAWN-004 security-auditor RP-014-01 security audit: sort-key vs independence ordering, config injection, CLI validation"]
    spawn_014_model_preference_policy_p1_model_preference_policy_5["SPAWN-005 finding-verifier Adversarial verification of RP-014-01 findings before repair"]
    spawn_014_model_preference_policy_p1_model_preference_policy_6["SPAWN-006 repair-agent Consolidated repair R1 of SEC14-01 + RF14-01..07"]
    spawn_014_model_preference_policy_p1_model_preference_policy_7["SPAWN-007 delta-reviewer Focused delta review of R1 repair #40;8 findings#41;"]
  end
end
review_014_model_preference_policy_p1_model_preference_policy_1 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_1
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_2
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_3
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_4
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_5
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_6
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_7
review_014_model_preference_policy_p1_model_preference_policy_2 -->|produjo| finding_014_model_preference_policy_p1_model_preference_policy_8
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_1
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_2
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_3
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_4
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_5
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_6
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_7
verification_014_model_preference_policy_p1_model_preference_policy_1 -->|verificó| finding_014_model_preference_policy_p1_model_preference_policy_8
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_1
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_2
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_3
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_4
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_5
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_6
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_7
repair_014_model_preference_policy_p1_model_preference_policy_1 -->|reparó| finding_014_model_preference_policy_p1_model_preference_policy_8
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
