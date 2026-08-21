# 035-panel-honesto-consola-y-tips · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_035_panel_honesto_consola_y_tips["035-panel-honesto-consola-y-tips"]
  feature_035_panel_honesto_consola_y_tips_1["feature: 035-panel-honesto-consola-y-tips"]
  subgraph sg_035_panel_honesto_consola_y_tips_pkg_a["PKG-A"]
    package_035_panel_honesto_consola_y_tips_pkg_a_1["package: PKG-A"]
    finding_035_panel_honesto_consola_y_tips_pkg_a_1["PKG-A-F001 #40;medium#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_a_2["PKG-A-F002 #40;medium#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_a_3["PKG-A-F003 #40;medium#41; verified_by=finding-verifier"]
    review_035_panel_honesto_consola_y_tips_pkg_a_1["package-reviewer: repair_required"]
    verification_035_panel_honesto_consola_y_tips_pkg_a_1["verified_by=finding-verifier"]
    repair_035_panel_honesto_consola_y_tips_pkg_a_1["9 changed files"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_1["SPAWN-001 architect T-001 door audit + ADR-0065 record-review contract + HOW for membership predicate"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_2["SPAWN-002 implementer T-002..T-010: guards + golden rewrite + canonical doctrine + generate trees"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_3["SPAWN-003 gate-runner Independent PKG-A gates: owned-paths, focused bites, build --check, verify.sh"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_4["SPAWN-004 debugger Rewrite test_module_docs _init_ready_package to full panel path#59; do not lower complexity"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_5["SPAWN-005 gate-runner Re-verify after T-006 eighth-site fix: owned-paths, test_module_docs, verify.sh"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_6["SPAWN-006 package-reviewer PKG-A deep review vs spec AC-A.1..A.9, ADR-0065, design.md#59; same-model degradation vs securi…"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_7["SPAWN-007 security-auditor PKG-A authz of review verb: bypass of REVIEW_PANEL_REQUIRED / BLOCKING_FINDING_OPEN"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_8["SPAWN-008 finding-verifier Adversarial refute PKG-A-F001 F002 F003 before repair#59; last spawn 8/8"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_9["SPAWN-009 repair-agent Repair PKG-A-F001 F002 F003 in one pass"]
    spawn_035_panel_honesto_consola_y_tips_pkg_a_10["SPAWN-010 delta-reviewer Delta review of F001-F003 repair#59; last authorized spawn 10/10"]
  end
  subgraph sg_035_panel_honesto_consola_y_tips_pkg_b["PKG-B"]
    package_035_panel_honesto_consola_y_tips_pkg_b_1["package: PKG-B"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_1["PKG-B-F001 #40;high#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_2["PKG-B-F002 #40;high#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_3["PKG-B-F003 #40;medium#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_4["PKG-B-F004 #40;medium#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_5["PKG-B-F005 #40;high#41; verified_by=finding-verifier"]
    finding_035_panel_honesto_consola_y_tips_pkg_b_6["PKG-B-F006 #40;high#41; verified_by=finding-verifier"]
    review_035_panel_honesto_consola_y_tips_pkg_b_1["package-reviewer: repair_required"]
    review_035_panel_honesto_consola_y_tips_pkg_b_2["security-auditor: repair_required"]
    verification_035_panel_honesto_consola_y_tips_pkg_b_1["verified_by=finding-verifier"]
    repair_035_panel_honesto_consola_y_tips_pkg_b_1["7 changed files"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_1["SPAWN-001 architect T-102 extraction ceiling plus PKG-B design #40;module names, three-channel comparison#41;"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_2["SPAWN-002 implementer T-101 characterization + T-103 valve check + T-104 16-row matrix + T-105 wc -l"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_3["SPAWN-003 gate-runner independent PKG-B gates: owned-paths, build --check, verify.sh, characterization compare"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_4["SPAWN-004 gate-runner re-run owned-paths after digest exceptions#59; characterize compare stays the non-P001 command"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_5["SPAWN-005 package-reviewer RP-01 PKG-B correctness vs AC-B.1..B.8 path b"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_6["SPAWN-006 security-auditor RP-01 PKG-B secrets in characterization and vault/routing residue"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_7["SPAWN-007 finding-verifier adversarial refute PKG-B-F001..F006 before repair"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_8["SPAWN-008 repair-agent consolidated repair PKG-B-F001..F006"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_9["SPAWN-009 delta-reviewer delta review of PKG-B F001-F006 repair"]
    spawn_035_panel_honesto_consola_y_tips_pkg_b_10["SPAWN-010 delta-reviewer delta review of PKG-B F001-F006 repair"]
  end
  subgraph sg_035_panel_honesto_consola_y_tips_pkg_c["PKG-C"]
    package_035_panel_honesto_consola_y_tips_pkg_c_1["package: PKG-C"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_1["SPAWN-001 implementer T-201..T-204 TIPS + COMO-FUNCIONA pointer"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_2["SPAWN-002 gate-runner PKG-C docs gates: owned-paths, diff --check, control-plane rg"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_3["SPAWN-003 package-reviewer RP-01 PKG-C docs vs AC-C.1..C.6"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_4["SPAWN-004 integrator cross-package integration + global verify.sh"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_5["SPAWN-005 adversarial-judge final evidence bundle vs spec 035"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_6["SPAWN-006 integrator integration repair of JUDGE-035-001 and JUDGE-035-002"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_7["SPAWN-007 adversarial-judge re-judge after INTEGRATION composition repair"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_8["SPAWN-008 integrator persist independent review records into evidence bundle"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_9["SPAWN-009 adversarial-judge third judge after REVIEWS.md and path-b answer"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_10["SPAWN-010 integrator stale INTEGRATION.md and ADR-0066 line-count after third judge"]
    spawn_035_panel_honesto_consola_y_tips_pkg_c_11["SPAWN-011 adversarial-judge fourth judge after extra JSON slot"]
  end
end
review_035_panel_honesto_consola_y_tips_pkg_a_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_a_1
review_035_panel_honesto_consola_y_tips_pkg_a_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_a_2
review_035_panel_honesto_consola_y_tips_pkg_a_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_a_3
verification_035_panel_honesto_consola_y_tips_pkg_a_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_a_1
verification_035_panel_honesto_consola_y_tips_pkg_a_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_a_2
verification_035_panel_honesto_consola_y_tips_pkg_a_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_a_3
repair_035_panel_honesto_consola_y_tips_pkg_a_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_a_1
repair_035_panel_honesto_consola_y_tips_pkg_a_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_a_2
repair_035_panel_honesto_consola_y_tips_pkg_a_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_a_3
review_035_panel_honesto_consola_y_tips_pkg_b_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_1
review_035_panel_honesto_consola_y_tips_pkg_b_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_2
review_035_panel_honesto_consola_y_tips_pkg_b_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_3
review_035_panel_honesto_consola_y_tips_pkg_b_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_4
review_035_panel_honesto_consola_y_tips_pkg_b_1 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_5
review_035_panel_honesto_consola_y_tips_pkg_b_2 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_1
review_035_panel_honesto_consola_y_tips_pkg_b_2 -->|produjo| finding_035_panel_honesto_consola_y_tips_pkg_b_6
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_1
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_2
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_3
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_4
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_5
verification_035_panel_honesto_consola_y_tips_pkg_b_1 -->|verificó| finding_035_panel_honesto_consola_y_tips_pkg_b_6
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_1
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_2
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_3
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_4
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_5
repair_035_panel_honesto_consola_y_tips_pkg_b_1 -->|reparó| finding_035_panel_honesto_consola_y_tips_pkg_b_6
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
