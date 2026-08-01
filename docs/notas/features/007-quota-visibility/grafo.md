# 007-quota-visibility · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_007_quota_visibility["007-quota-visibility"]
  feature_007_quota_visibility_1["feature: 007-quota-visibility"]
  subgraph sg_007_quota_visibility_p1_schema_normalize["P1-schema-normalize"]
    package_007_quota_visibility_p1_schema_normalize_1["package: P1-schema-normalize"]
    finding_007_quota_visibility_p1_schema_normalize_1["F-01 #40;medium#41; verified_by=finding-verifier"]
    review_007_quota_visibility_p1_schema_normalize_1["architect: repair_required"]
    verification_007_quota_visibility_p1_schema_normalize_1["verified_by=finding-verifier"]
  end
  subgraph sg_007_quota_visibility_p2_spawn_accounting["P2-spawn-accounting"]
    package_007_quota_visibility_p2_spawn_accounting_1["package: P2-spawn-accounting"]
    finding_007_quota_visibility_p2_spawn_accounting_1["F-SEC-01 #40;critical#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_2["F-SEC-02 #40;high#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_3["F-SEC-03 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_4["F-SEC-04 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_5["F-PR-01 #40;high#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_6["F-PR-02 #40;high#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_7["F-PR-03 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_8["F-PR-04 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_9["F-PR-05 #40;low#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_10["F-PR-06 #40;low#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p2_spawn_accounting_11["N-01 #40;high#41; verified_by=delta-reviewer"]
    finding_007_quota_visibility_p2_spawn_accounting_12["N-02 #40;low#41;"]
    finding_007_quota_visibility_p2_spawn_accounting_13["N-03 #40;low#41;"]
    review_007_quota_visibility_p2_spawn_accounting_1["security-auditor: repair_required"]
    review_007_quota_visibility_p2_spawn_accounting_2["package-reviewer: repair_required"]
    review_007_quota_visibility_p2_spawn_accounting_3["delta: repair_required"]
    verification_007_quota_visibility_p2_spawn_accounting_1["verified_by=finding-verifier"]
    verification_007_quota_visibility_p2_spawn_accounting_2["verified_by=delta-reviewer"]
    repair_007_quota_visibility_p2_spawn_accounting_1["7 changed files"]
    repair_007_quota_visibility_p2_spawn_accounting_2["5 changed files"]
  end
  subgraph sg_007_quota_visibility_p3_correct_record["P3-correct-record"]
    package_007_quota_visibility_p3_correct_record_1["package: P3-correct-record"]
    finding_007_quota_visibility_p3_correct_record_1["F-01 #40;high#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_2["F-02 #40;high#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_3["F-03 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_4["F-04 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_5["F-05 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_6["F-06 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_7["F-07 #40;low#41;"]
    finding_007_quota_visibility_p3_correct_record_8["F-08 #40;low#41;"]
    finding_007_quota_visibility_p3_correct_record_9["N-01 #40;medium#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_10["N-02 #40;low#41; verified_by=finding-verifier"]
    finding_007_quota_visibility_p3_correct_record_11["N-03 #40;low#41; verified_by=finding-verifier"]
    review_007_quota_visibility_p3_correct_record_1["package-reviewer: repair_required"]
    review_007_quota_visibility_p3_correct_record_2["delta: repair_required"]
    verification_007_quota_visibility_p3_correct_record_1["verified_by=finding-verifier"]
    verification_007_quota_visibility_p3_correct_record_2["verified_by=finding-verifier"]
    repair_007_quota_visibility_p3_correct_record_1["8 changed files"]
    repair_007_quota_visibility_p3_correct_record_2["7 changed files"]
  end
end
review_007_quota_visibility_p1_schema_normalize_1 -->|produjo| finding_007_quota_visibility_p1_schema_normalize_1
verification_007_quota_visibility_p1_schema_normalize_1 -->|refutó| finding_007_quota_visibility_p1_schema_normalize_1
review_007_quota_visibility_p2_spawn_accounting_1 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_1
review_007_quota_visibility_p2_spawn_accounting_1 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_2
review_007_quota_visibility_p2_spawn_accounting_1 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_3
review_007_quota_visibility_p2_spawn_accounting_1 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_4
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_5
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_6
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_7
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_8
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_9
review_007_quota_visibility_p2_spawn_accounting_2 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_10
review_007_quota_visibility_p2_spawn_accounting_3 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_11
review_007_quota_visibility_p2_spawn_accounting_3 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_12
review_007_quota_visibility_p2_spawn_accounting_3 -->|produjo| finding_007_quota_visibility_p2_spawn_accounting_13
verification_007_quota_visibility_p2_spawn_accounting_1 -->|refutó| finding_007_quota_visibility_p2_spawn_accounting_10
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_1
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_5
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_6
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_2
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_3
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_4
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_9
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_7
verification_007_quota_visibility_p2_spawn_accounting_1 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_8
verification_007_quota_visibility_p2_spawn_accounting_2 -->|verificó| finding_007_quota_visibility_p2_spawn_accounting_11
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_1
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_5
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_2
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_6
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_3
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_4
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_9
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_7
repair_007_quota_visibility_p2_spawn_accounting_1 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_8
repair_007_quota_visibility_p2_spawn_accounting_2 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_11
repair_007_quota_visibility_p2_spawn_accounting_2 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_12
repair_007_quota_visibility_p2_spawn_accounting_2 -->|reparó| finding_007_quota_visibility_p2_spawn_accounting_13
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_1
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_2
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_3
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_4
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_5
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_6
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_7
review_007_quota_visibility_p3_correct_record_1 -->|produjo| finding_007_quota_visibility_p3_correct_record_8
review_007_quota_visibility_p3_correct_record_2 -->|produjo| finding_007_quota_visibility_p3_correct_record_9
review_007_quota_visibility_p3_correct_record_2 -->|produjo| finding_007_quota_visibility_p3_correct_record_10
review_007_quota_visibility_p3_correct_record_2 -->|produjo| finding_007_quota_visibility_p3_correct_record_11
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_1
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_2
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_3
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_4
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_5
verification_007_quota_visibility_p3_correct_record_1 -->|verificó| finding_007_quota_visibility_p3_correct_record_6
verification_007_quota_visibility_p3_correct_record_2 -->|verificó| finding_007_quota_visibility_p3_correct_record_9
verification_007_quota_visibility_p3_correct_record_2 -->|verificó| finding_007_quota_visibility_p3_correct_record_10
verification_007_quota_visibility_p3_correct_record_2 -->|verificó| finding_007_quota_visibility_p3_correct_record_11
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_1
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_2
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_3
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_4
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_5
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_6
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_7
repair_007_quota_visibility_p3_correct_record_1 -->|reparó| finding_007_quota_visibility_p3_correct_record_8
repair_007_quota_visibility_p3_correct_record_2 -->|reparó| finding_007_quota_visibility_p3_correct_record_9
repair_007_quota_visibility_p3_correct_record_2 -->|reparó| finding_007_quota_visibility_p3_correct_record_10
repair_007_quota_visibility_p3_correct_record_2 -->|reparó| finding_007_quota_visibility_p3_correct_record_11
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
