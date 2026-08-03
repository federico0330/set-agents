# 016-audit-debt-repayment · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_016_audit_debt_repayment["016-audit-debt-repayment"]
  feature_016_audit_debt_repayment_1["feature: 016-audit-debt-repayment"]
  subgraph sg_016_audit_debt_repayment_p1_harness_debt["P1-harness-debt"]
    package_016_audit_debt_repayment_p1_harness_debt_1["package: P1-harness-debt"]
    finding_016_audit_debt_repayment_p1_harness_debt_1["P1F-01 #40;low#41;"]
    review_016_audit_debt_repayment_p1_harness_debt_1["package-reviewer: pass"]
    spawn_016_audit_debt_repayment_p1_harness_debt_1["SPAWN-001 implementer Implement P1-harness-debt: PR-07 repair_entry + PR-08 extraction + PR-09 docs, on feature-state.p…"]
    spawn_016_audit_debt_repayment_p1_harness_debt_2["SPAWN-002 gate-runner Independent gates on P1-harness-debt #40;harness module scope#41;"]
    spawn_016_audit_debt_repayment_p1_harness_debt_3["SPAWN-003 package-reviewer RP-P1-01 deep review of P1-harness-debt incl. AC-05b extraction-diff obligation"]
    spawn_016_audit_debt_repayment_p1_harness_debt_4["SPAWN-004 integrator Integration validation of accepted P1+P2 together against contract 1.1.0"]
  end
  subgraph sg_016_audit_debt_repayment_p2_hygiene["P2-hygiene"]
    package_016_audit_debt_repayment_p2_hygiene_1["package: P2-hygiene"]
    finding_016_audit_debt_repayment_p2_hygiene_1["P2F-01 #40;high#41; verified_by=finding-verifier"]
    finding_016_audit_debt_repayment_p2_hygiene_2["P2F-02 #40;low#41; verified_by=finding-verifier"]
    review_016_audit_debt_repayment_p2_hygiene_1["package-reviewer: repair_required"]
    verification_016_audit_debt_repayment_p2_hygiene_1["verified_by=finding-verifier"]
    repair_016_audit_debt_repayment_p2_hygiene_1["2 changed files"]
    spawn_016_audit_debt_repayment_p2_hygiene_1["SPAWN-001 implementer Implement P2-hygiene: template cleanup + redirect reason_code"]
    spawn_016_audit_debt_repayment_p2_hygiene_2["SPAWN-002 gate-runner Independent deterministic gates on P2-hygiene"]
    spawn_016_audit_debt_repayment_p2_hygiene_3["SPAWN-003 package-reviewer RP-P2-01 deep review of P2-hygiene diff vs AC-08/09/10"]
    spawn_016_audit_debt_repayment_p2_hygiene_4["SPAWN-004 finding-verifier Adversarial verification of P2F-01/P2F-02 before repair"]
    spawn_016_audit_debt_repayment_p2_hygiene_5["SPAWN-005 repair-agent Consolidated repair R1 of P2F-01/P2F-02"]
    spawn_016_audit_debt_repayment_p2_hygiene_6["SPAWN-006 delta-reviewer Focused delta review of R1 repair #40;P2F-01/P2F-02#41;"]
  end
end
review_016_audit_debt_repayment_p1_harness_debt_1 -->|produjo| finding_016_audit_debt_repayment_p1_harness_debt_1
review_016_audit_debt_repayment_p2_hygiene_1 -->|produjo| finding_016_audit_debt_repayment_p2_hygiene_1
review_016_audit_debt_repayment_p2_hygiene_1 -->|produjo| finding_016_audit_debt_repayment_p2_hygiene_2
verification_016_audit_debt_repayment_p2_hygiene_1 -->|verificó| finding_016_audit_debt_repayment_p2_hygiene_1
verification_016_audit_debt_repayment_p2_hygiene_1 -->|verificó| finding_016_audit_debt_repayment_p2_hygiene_2
repair_016_audit_debt_repayment_p2_hygiene_1 -->|reparó| finding_016_audit_debt_repayment_p2_hygiene_1
repair_016_audit_debt_repayment_p2_hygiene_1 -->|reparó| finding_016_audit_debt_repayment_p2_hygiene_2
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
