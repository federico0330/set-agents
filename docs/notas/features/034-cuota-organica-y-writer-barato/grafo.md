# 034-cuota-organica-y-writer-barato · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_034_cuota_organica_y_writer_barato["034-cuota-organica-y-writer-barato"]
  feature_034_cuota_organica_y_writer_barato_1["feature: 034-cuota-organica-y-writer-barato"]
  subgraph sg_034_cuota_organica_y_writer_barato_pkg_a["PKG-A"]
    package_034_cuota_organica_y_writer_barato_pkg_a_1["package: PKG-A"]
    spawn_034_cuota_organica_y_writer_barato_pkg_a_1["SPAWN-001 implementer Implement AC-A.1 to A.6 strict-TDD bite on RISK_SIGNAL_REQUIRED"]
    spawn_034_cuota_organica_y_writer_barato_pkg_a_2["SPAWN-002 local-gate-runner P001 compile owned-paths git-diff-check"]
    spawn_034_cuota_organica_y_writer_barato_pkg_a_3["SPAWN-003 local-gate-runner P001 retry after owned-path exceptions"]
    spawn_034_cuota_organica_y_writer_barato_pkg_a_4["SPAWN-004 gate-runner PKG-A focused tests and build --check"]
    spawn_034_cuota_organica_y_writer_barato_pkg_a_5["SPAWN-005 package-reviewer Independent deep review PKG-A AC-A.1-A.6"]
  end
  subgraph sg_034_cuota_organica_y_writer_barato_pkg_b["PKG-B"]
    package_034_cuota_organica_y_writer_barato_pkg_b_1["package: PKG-B"]
    finding_034_cuota_organica_y_writer_barato_pkg_b_1["F-B01 #40;high#41; verified_by=finding-verifier"]
    finding_034_cuota_organica_y_writer_barato_pkg_b_2["F-B02 #40;medium#41; verified_by=finding-verifier"]
    review_034_cuota_organica_y_writer_barato_pkg_b_1["package-reviewer: repair_required"]
    verification_034_cuota_organica_y_writer_barato_pkg_b_1["verified_by=finding-verifier"]
    repair_034_cuota_organica_y_writer_barato_pkg_b_1["5 changed files"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_1["SPAWN-001 implementer Implement AC-B.1 to B.7 cheap writer salvage promotion"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_2["SPAWN-002 local-gate-runner P001 compile owned-paths git-diff-check PKG-B"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_3["SPAWN-003 local-gate-runner P001 retry after triage skill waiver"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_4["SPAWN-004 gate-runner PKG-B focused tests and build --check"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_5["SPAWN-005 package-reviewer Independent deep review PKG-B AC-B.1-B.7"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_6["SPAWN-006 security-auditor Security pass on salvage override and quota routing"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_7["SPAWN-007 finding-verifier Refute or uphold F-B01 and F-B02 before repair"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_8["SPAWN-008 repair-agent Consolidated repair F-B01 F-B02"]
    spawn_034_cuota_organica_y_writer_barato_pkg_b_9["SPAWN-009 delta-reviewer Delta review of F-B01 F-B02 repair"]
  end
  subgraph sg_034_cuota_organica_y_writer_barato_pkg_c["PKG-C"]
    package_034_cuota_organica_y_writer_barato_pkg_c_1["package: PKG-C"]
    finding_034_cuota_organica_y_writer_barato_pkg_c_1["SEC-001 #40;high#41; verified_by=finding-verifier"]
    review_034_cuota_organica_y_writer_barato_pkg_c_1["security-auditor: repair_required"]
    verification_034_cuota_organica_y_writer_barato_pkg_c_1["verified_by=finding-verifier"]
    repair_034_cuota_organica_y_writer_barato_pkg_c_1["3 changed files"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_1["SPAWN-001 implementer Implement AC-C.1 to C.6 frontier cap and cost-report S2"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_2["SPAWN-002 local-gate-runner P001 PKG-C"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_3["SPAWN-003 gate-runner PKG-C focused tests and build --check"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_4["SPAWN-004 package-reviewer Independent deep review PKG-C AC-C.1-C.6"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_5["SPAWN-005 security-auditor Security pass on frontier cap bypass"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_6["SPAWN-006 finding-verifier Refute or uphold SEC-001 before repair"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_7["SPAWN-007 repair-agent Repair SEC-001 P001-command un-classifies heavy spawn"]
    spawn_034_cuota_organica_y_writer_barato_pkg_c_8["SPAWN-008 delta-reviewer Delta review SEC-001 repair"]
  end
  subgraph sg_034_cuota_organica_y_writer_barato_pkg_d["PKG-D"]
    package_034_cuota_organica_y_writer_barato_pkg_d_1["package: PKG-D"]
    finding_034_cuota_organica_y_writer_barato_pkg_d_1["SEC-001 #40;high#41; verified_by=finding-verifier"]
    review_034_cuota_organica_y_writer_barato_pkg_d_1["security-auditor: repair_required"]
    verification_034_cuota_organica_y_writer_barato_pkg_d_1["verified_by=finding-verifier"]
    repair_034_cuota_organica_y_writer_barato_pkg_d_1["4 changed files"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_1["SPAWN-001 implementer Implement AC-D.1 to D.6 Cursor pins per role"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_2["SPAWN-002 local-gate-runner P001 PKG-D"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_3["SPAWN-003 local-gate-runner P001 retry after neighbor-test waivers"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_4["SPAWN-004 gate-runner PKG-D CursorRuntimeTargetTests and build --check"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_5["SPAWN-005 package-reviewer Independent deep review PKG-D AC-D.1-D.6"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_6["SPAWN-006 security-auditor Security pass on Cursor pins"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_7["SPAWN-007 finding-verifier Refute or uphold SEC-001 inherit fake family"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_8["SPAWN-008 repair-agent Repair SEC-001 inherit fake family on review duties"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_9["SPAWN-009 delta-reviewer Delta review SEC-001 inherit guard"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_10["SPAWN-010 integrator Feature integration evidence and global verify"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_11["SPAWN-011 gate-runner Clean verify.sh after integrator adapter"]
    spawn_034_cuota_organica_y_writer_barato_pkg_d_12["SPAWN-012 adversarial-judge Final adversarial judge of 034 evidence bundle"]
  end
end
review_034_cuota_organica_y_writer_barato_pkg_b_1 -->|produjo| finding_034_cuota_organica_y_writer_barato_pkg_b_1
review_034_cuota_organica_y_writer_barato_pkg_b_1 -->|produjo| finding_034_cuota_organica_y_writer_barato_pkg_b_2
verification_034_cuota_organica_y_writer_barato_pkg_b_1 -->|verificó| finding_034_cuota_organica_y_writer_barato_pkg_b_1
verification_034_cuota_organica_y_writer_barato_pkg_b_1 -->|verificó| finding_034_cuota_organica_y_writer_barato_pkg_b_2
repair_034_cuota_organica_y_writer_barato_pkg_b_1 -->|reparó| finding_034_cuota_organica_y_writer_barato_pkg_b_1
repair_034_cuota_organica_y_writer_barato_pkg_b_1 -->|reparó| finding_034_cuota_organica_y_writer_barato_pkg_b_2
review_034_cuota_organica_y_writer_barato_pkg_c_1 -->|produjo| finding_034_cuota_organica_y_writer_barato_pkg_c_1
verification_034_cuota_organica_y_writer_barato_pkg_c_1 -->|verificó| finding_034_cuota_organica_y_writer_barato_pkg_c_1
repair_034_cuota_organica_y_writer_barato_pkg_c_1 -->|reparó| finding_034_cuota_organica_y_writer_barato_pkg_c_1
review_034_cuota_organica_y_writer_barato_pkg_d_1 -->|produjo| finding_034_cuota_organica_y_writer_barato_pkg_d_1
verification_034_cuota_organica_y_writer_barato_pkg_d_1 -->|verificó| finding_034_cuota_organica_y_writer_barato_pkg_d_1
repair_034_cuota_organica_y_writer_barato_pkg_d_1 -->|reparó| finding_034_cuota_organica_y_writer_barato_pkg_d_1
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
