# 010-spawn-provenance · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_010_spawn_provenance["010-spawn-provenance"]
  feature_010_spawn_provenance_1["feature: 010-spawn-provenance"]
  subgraph sg_010_spawn_provenance_p1_spawn_provenance["P1-spawn-provenance"]
    package_010_spawn_provenance_p1_spawn_provenance_1["package: P1-spawn-provenance"]
    finding_010_spawn_provenance_p1_spawn_provenance_1["P1-REV-001 #40;medium#41; verified_by=finding-verifier"]
    review_010_spawn_provenance_p1_spawn_provenance_1["package-reviewer: repair_required"]
    verification_010_spawn_provenance_p1_spawn_provenance_1["verified_by=finding-verifier"]
    repair_010_spawn_provenance_p1_spawn_provenance_1["1 changed files"]
    spawn_010_spawn_provenance_p1_spawn_provenance_1["SPAWN-002 gate-runner Independent package gate verification before review"]
    spawn_010_spawn_provenance_p1_spawn_provenance_2["SPAWN-003 integrator Record approved ownership exception and AC-04 decision before package gates"]
    spawn_010_spawn_provenance_p1_spawn_provenance_3["SPAWN-004 integrator Persist gates and enter independent package review"]
    spawn_010_spawn_provenance_p1_spawn_provenance_4["SPAWN-005 package-reviewer Independent deep review of integrated 010 package"]
    spawn_010_spawn_provenance_p1_spawn_provenance_5["SPAWN-006 package-reviewer One relaunch of stalled independent package review in RP-01"]
    spawn_010_spawn_provenance_p1_spawn_provenance_6["SPAWN-007 repair-agent Repair consolidated medium review finding P1-REV-001"]
    spawn_010_spawn_provenance_p1_spawn_provenance_7["SPAWN-008 gate-runner Independent full-suite verification of P1-REV-001 repair"]
    spawn_010_spawn_provenance_p1_spawn_provenance_8["SPAWN-009 debugger Diagnose full-suite hang after P1-REV-001 test repair"]
    spawn_010_spawn_provenance_p1_spawn_provenance_9["SPAWN-010 delta-reviewer Focused independent delta review of P1-REV-001 repair"]
    spawn_010_spawn_provenance_p1_spawn_provenance_10["SPAWN-011 integrator Integration validation of accepted P1-spawn-provenance before global gate"]
  end
end
review_010_spawn_provenance_p1_spawn_provenance_1 -->|produjo| finding_010_spawn_provenance_p1_spawn_provenance_1
verification_010_spawn_provenance_p1_spawn_provenance_1 -->|verificó| finding_010_spawn_provenance_p1_spawn_provenance_1
repair_010_spawn_provenance_p1_spawn_provenance_1 -->|reparó| finding_010_spawn_provenance_p1_spawn_provenance_1
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
