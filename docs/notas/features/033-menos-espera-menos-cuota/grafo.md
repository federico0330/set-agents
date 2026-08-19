# 033-menos-espera-menos-cuota · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_033_menos_espera_menos_cuota["033-menos-espera-menos-cuota"]
  feature_033_menos_espera_menos_cuota_1["feature: 033-menos-espera-menos-cuota"]
  subgraph sg_033_menos_espera_menos_cuota_pkg_1["PKG-1"]
    package_033_menos_espera_menos_cuota_pkg_1_1["package: PKG-1"]
    spawn_033_menos_espera_menos_cuota_pkg_1_1["SPAWN-001 implementer colapsar tres lanes OpenCode a un string go-zen y AC-1.6 ruidoso #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_1_2["SPAWN-002 package-reviewer review profundo PKG-1 contra AC-1.1–1.7 #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_1_3["SPAWN-003 security-auditor auditoria de seguridad del colapso de lanes y AC-1.6 #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_2["PKG-2"]
    package_033_menos_espera_menos_cuota_pkg_2_1["package: PKG-2"]
    finding_033_menos_espera_menos_cuota_pkg_2_1["F-PKG2-01 #40;high#41; verified_by=finding-verifier"]
    finding_033_menos_espera_menos_cuota_pkg_2_2["F-PKG2-02 #40;medium#41; verified_by=finding-verifier"]
    review_033_menos_espera_menos_cuota_pkg_2_1["package-reviewer: repair_required"]
    verification_033_menos_espera_menos_cuota_pkg_2_1["verified_by=finding-verifier"]
    repair_033_menos_espera_menos_cuota_pkg_2_1["5 changed files"]
    commit_033_menos_espera_menos_cuota_pkg_2_1["c896d70"]
    spawn_033_menos_espera_menos_cuota_pkg_2_1["SPAWN-001 implementer implementar AC-2.1 a 2.5: primer frame #60;300ms, with_progress, cache TTL, degradacion nombrada #91;in…"]
    spawn_033_menos_espera_menos_cuota_pkg_2_2["SPAWN-002 gate-runner gates PKG-2: owned-paths, build-check, verify.sh, git diff --check #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_2_3["SPAWN-003 package-reviewer revision PKG-2 AC-2.1..2.5 e7f4982 #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_2_4["SPAWN-004 security-auditor subreview seguridad PKG-2 classify-risk high #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_2_5["SPAWN-005 finding-verifier refutar o sostener F-PKG2-01 y F-PKG2-02 antes de reparar #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_2_6["SPAWN-006 repair-agent reparar F-PKG2-01 y F-PKG2-02 en un pase consolidado #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_2_7["SPAWN-007 delta-reviewer revisar el delta de repair F-PKG2-01 y F-PKG2-02 #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_3["PKG-3"]
    package_033_menos_espera_menos_cuota_pkg_3_1["package: PKG-3"]
    finding_033_menos_espera_menos_cuota_pkg_3_1["PKG3-F01 #40;medium#41; verified_by=finding-verifier"]
    finding_033_menos_espera_menos_cuota_pkg_3_2["PKG3-F02 #40;medium#41; verified_by=finding-verifier"]
    review_033_menos_espera_menos_cuota_pkg_3_1["package-reviewer: repair_required"]
    verification_033_menos_espera_menos_cuota_pkg_3_1["verified_by=finding-verifier"]
    repair_033_menos_espera_menos_cuota_pkg_3_1["3 changed files"]
    commit_033_menos_espera_menos_cuota_pkg_3_1["e7fa83f"]
    spawn_033_menos_espera_menos_cuota_pkg_3_1["SPAWN-001 implementer implementar picker agrupado, contador, marca actual, type-to-search y wipe sin 2J #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_3_2["SPAWN-002 package-reviewer review profundo PKG-3 contra AC-3.1–3.8 #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_3_3["SPAWN-003 security-auditor auditoria de seguridad del picker ANSI y choose#40;#41; #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_3_4["SPAWN-004 finding-verifier refutar o sostener PKG3-F01 y PKG3-F02 #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_3_5["SPAWN-005 repair-agent reparar PKG3-F01 y PKG3-F02 en un pase #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_3_6["SPAWN-006 delta-reviewer revisar delta de repair PKG3-F01 y PKG3-F02 #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_4["PKG-4"]
    package_033_menos_espera_menos_cuota_pkg_4_1["package: PKG-4"]
    spawn_033_menos_espera_menos_cuota_pkg_4_1["SPAWN-001 package-planner escribir context packs de los 6 paquetes y persistir --context-pack#59; PKG-4 es el primero a im…"]
    spawn_033_menos_espera_menos_cuota_pkg_4_2["SPAWN-002 implementer implementar AC-4.1 a AC-4.4 en un solo paquete#59; AC-4.5 CI SHA queda para el cierre con jobs #91;inhe…"]
    spawn_033_menos_espera_menos_cuota_pkg_4_3["SPAWN-003 gate-runner gates de cierre PKG-4: check-owned-paths, build.sh --check, verify.sh, git diff --check #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_4_4["SPAWN-004 package-reviewer revision profunda PKG-4 contra spec AC-4.1..4.5, diff 1f5a24f, gates verdes #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_4_5["SPAWN-005 security-auditor subreview seguridad PKG-4 por risk-classification high #40;subprocess-spawn#41; #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_5["PKG-5"]
    package_033_menos_espera_menos_cuota_pkg_5_1["package: PKG-5"]
    spawn_033_menos_espera_menos_cuota_pkg_5_1["SPAWN-001 implementer implementar AC-5.1 a 5.5 #40;presenter verify#41;#59; AC-5.6 no paralelizar sin prueba de aislamiento #91;inh…"]
    spawn_033_menos_espera_menos_cuota_pkg_5_2["SPAWN-002 gate-runner gates PKG-5: owned-paths, build-check, verify.sh #40;ejercita el reporter#41;, git diff --check #91;inheri…"]
    spawn_033_menos_espera_menos_cuota_pkg_5_3["SPAWN-003 implementer arreglar ImportError de discover cuando verify_reporter.py corre como script #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_5_4["SPAWN-004 gate-runner re-run PKG-5 gates after discover ImportError fix #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_5_5["SPAWN-005 package-reviewer revision profunda PKG-5 AC-5.1..5.5 contra 779671b #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_5_6["SPAWN-006 security-auditor subreview seguridad PKG-5 por classify-risk high #40;shebang/subprocess#41; #91;inherit#93;"]
  end
  subgraph sg_033_menos_espera_menos_cuota_pkg_6["PKG-6"]
    package_033_menos_espera_menos_cuota_pkg_6_1["package: PKG-6"]
    finding_033_menos_espera_menos_cuota_pkg_6_1["PKG6-F01 #40;high#41; verified_by=finding-verifier"]
    finding_033_menos_espera_menos_cuota_pkg_6_2["PKG6-F02 #40;medium#41; verified_by=finding-verifier"]
    finding_033_menos_espera_menos_cuota_pkg_6_3["PKG6-F03 #40;medium#41; verified_by=finding-verifier"]
    review_033_menos_espera_menos_cuota_pkg_6_1["package-reviewer: repair_required"]
    verification_033_menos_espera_menos_cuota_pkg_6_1["verified_by=finding-verifier"]
    repair_033_menos_espera_menos_cuota_pkg_6_1["6 changed files"]
    commit_033_menos_espera_menos_cuota_pkg_6_1["3900d4b"]
    spawn_033_menos_espera_menos_cuota_pkg_6_1["SPAWN-001 implementer context pack obligatorio, P001 local-gate-runner, panel por riesgo, aviso 80#37;, cost-report seccio…"]
    spawn_033_menos_espera_menos_cuota_pkg_6_2["SPAWN-002 implementer commit generated Global feature_state_lib mirrors so freeze matches build.sh #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_3["SPAWN-003 implementer commit generated Global feature_state_lib mirrors so freeze matches build.sh #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_4["SPAWN-004 local-gate-runner P001 owned-paths and git diff --check #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_5["SPAWN-005 gate-runner build-check and full verify.sh for PKG-6 #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_6["SPAWN-006 package-reviewer deep review PKG-6 AC-6.1–6.6 against frozen candidate #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_7["SPAWN-007 security-auditor security pass PKG-6 state-machine and cost-report ingest #91;inherit#93;"]
    spawn_033_menos_espera_menos_cuota_pkg_6_8["SPAWN-008 finding-verifier refute or uphold PKG6-F01 F02 F03 before any repair #91;inherit#93;"]
  end
end
review_033_menos_espera_menos_cuota_pkg_2_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_2_1
review_033_menos_espera_menos_cuota_pkg_2_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_2_2
verification_033_menos_espera_menos_cuota_pkg_2_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_2_1
verification_033_menos_espera_menos_cuota_pkg_2_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_2_2
repair_033_menos_espera_menos_cuota_pkg_2_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_2_1
repair_033_menos_espera_menos_cuota_pkg_2_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_2_2
repair_033_menos_espera_menos_cuota_pkg_2_1 -->|reparó| commit_033_menos_espera_menos_cuota_pkg_2_1
review_033_menos_espera_menos_cuota_pkg_3_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_3_1
review_033_menos_espera_menos_cuota_pkg_3_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_3_2
verification_033_menos_espera_menos_cuota_pkg_3_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_3_1
verification_033_menos_espera_menos_cuota_pkg_3_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_3_2
repair_033_menos_espera_menos_cuota_pkg_3_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_3_1
repair_033_menos_espera_menos_cuota_pkg_3_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_3_2
repair_033_menos_espera_menos_cuota_pkg_3_1 -->|reparó| commit_033_menos_espera_menos_cuota_pkg_3_1
review_033_menos_espera_menos_cuota_pkg_6_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_6_1
review_033_menos_espera_menos_cuota_pkg_6_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_6_2
review_033_menos_espera_menos_cuota_pkg_6_1 -->|produjo| finding_033_menos_espera_menos_cuota_pkg_6_3
verification_033_menos_espera_menos_cuota_pkg_6_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_6_1
verification_033_menos_espera_menos_cuota_pkg_6_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_6_2
verification_033_menos_espera_menos_cuota_pkg_6_1 -->|verificó| finding_033_menos_espera_menos_cuota_pkg_6_3
repair_033_menos_espera_menos_cuota_pkg_6_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_6_1
repair_033_menos_espera_menos_cuota_pkg_6_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_6_2
repair_033_menos_espera_menos_cuota_pkg_6_1 -->|reparó| finding_033_menos_espera_menos_cuota_pkg_6_3
repair_033_menos_espera_menos_cuota_pkg_6_1 -->|reparó| commit_033_menos_espera_menos_cuota_pkg_6_1
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
