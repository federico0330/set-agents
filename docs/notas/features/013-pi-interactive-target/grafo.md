# 013-pi-interactive-target · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_013_pi_interactive_target["013-pi-interactive-target"]
  feature_013_pi_interactive_target_1["feature: 013-pi-interactive-target"]
  subgraph sg_013_pi_interactive_target_p1_pi_interactive_target["P1-pi-interactive-target"]
    package_013_pi_interactive_target_p1_pi_interactive_target_1["package: P1-pi-interactive-target"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_1["SEC-01 #40;high#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_2["SEC-02 #40;low#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_3["RF-01 #40;medium#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_4["RF-02 #40;medium#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_5["RF-03 #40;low#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_6["RF-04 #40;low#41; verified_by=finding-verifier"]
    finding_013_pi_interactive_target_p1_pi_interactive_target_7["RF-05 #40;low#41; verified_by=finding-verifier"]
    review_013_pi_interactive_target_p1_pi_interactive_target_1["security-auditor: repair_required"]
    review_013_pi_interactive_target_p1_pi_interactive_target_2["package-reviewer: repair_required"]
    verification_013_pi_interactive_target_p1_pi_interactive_target_1["verified_by=finding-verifier"]
    repair_013_pi_interactive_target_p1_pi_interactive_target_1["5 changed files"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_1["SPAWN-001 implementer Implement P1-pi-interactive-target: 7 tasks covering AC-01..AC-14 with local validation per task"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_2["SPAWN-002 gate-runner Independent deterministic gates on P1 before review panel"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_3["SPAWN-003 package-reviewer RP-01 deep review of complete P1 diff against spec and package criteria"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_4["SPAWN-004 security-auditor RP-01 security audit: new HOME write surface + collision guard + set_agents_spawn.py excepti…"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_5["SPAWN-005 finding-verifier Adversarial verification of RP-01 findings SEC-01/SEC-02/RF-01..RF-05 before repair"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_6["SPAWN-006 repair-agent Consolidated repair R1 of upheld findings SEC-01, RF-01..RF-05"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_7["SPAWN-007 gate-runner Independent gates for consolidated repair R1 before delta review"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_8["SPAWN-008 delta-reviewer Focused delta review of consolidated repair R1 against SEC-01, RF-01..RF-05"]
    spawn_013_pi_interactive_target_p1_pi_interactive_target_9["SPAWN-009 integrator Integration validation of accepted P1 against contract before global gate and DONE"]
  end
end
review_013_pi_interactive_target_p1_pi_interactive_target_1 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_1
review_013_pi_interactive_target_p1_pi_interactive_target_1 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_2
review_013_pi_interactive_target_p1_pi_interactive_target_2 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_3
review_013_pi_interactive_target_p1_pi_interactive_target_2 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_4
review_013_pi_interactive_target_p1_pi_interactive_target_2 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_5
review_013_pi_interactive_target_p1_pi_interactive_target_2 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_6
review_013_pi_interactive_target_p1_pi_interactive_target_2 -->|produjo| finding_013_pi_interactive_target_p1_pi_interactive_target_7
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|refutó| finding_013_pi_interactive_target_p1_pi_interactive_target_2
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_1
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_3
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_4
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_5
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_6
verification_013_pi_interactive_target_p1_pi_interactive_target_1 -->|verificó| finding_013_pi_interactive_target_p1_pi_interactive_target_7
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_1
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_3
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_4
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_5
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_6
repair_013_pi_interactive_target_p1_pi_interactive_target_1 -->|reparó| finding_013_pi_interactive_target_p1_pi_interactive_target_7
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
