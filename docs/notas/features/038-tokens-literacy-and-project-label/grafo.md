# 038-tokens-literacy-and-project-label · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_038_tokens_literacy_and_project_label["038-tokens-literacy-and-project-label"]
  feature_038_tokens_literacy_and_project_label_1["feature: 038-tokens-literacy-and-project-label"]
  subgraph sg_038_tokens_literacy_and_project_label_pkg_1["PKG-1"]
    package_038_tokens_literacy_and_project_label_pkg_1_1["package: PKG-1"]
    finding_038_tokens_literacy_and_project_label_pkg_1_1["PKG1-TEST-01 #40;low#41; verified_by=finding-verifier"]
    finding_038_tokens_literacy_and_project_label_pkg_1_2["PKG1-TEST-02 #40;medium#41; verified_by=finding-verifier"]
    finding_038_tokens_literacy_and_project_label_pkg_1_3["PKG1-TEST-03 #40;low#41; verified_by=finding-verifier"]
    review_038_tokens_literacy_and_project_label_pkg_1_1["repair_required #40;package-reviewer#41;"]
    verification_038_tokens_literacy_and_project_label_pkg_1_1["verified_by=finding-verifier"]
    repair_038_tokens_literacy_and_project_label_pkg_1_1["1 changed files"]
    spawn_038_tokens_literacy_and_project_label_pkg_1_1["SPAWN-001 implementer Implement project_label, tiered doctrine, code literacy, cost-report per encargo #91;grok-4.6#93;"]
    spawn_038_tokens_literacy_and_project_label_pkg_1_2["SPAWN-002 package-reviewer Independent deep review of PKG-1 against spec 038 and ADR-0069 #91;gpt-5.6-sol#93;"]
    spawn_038_tokens_literacy_and_project_label_pkg_1_3["SPAWN-003 finding-verifier Adversarial refutation of PKG-1 review findings before repair #91;gpt-5.6-sol#93;"]
    spawn_038_tokens_literacy_and_project_label_pkg_1_4["SPAWN-004 repair-agent Close PKG1-TEST-01/02/03 by extending the three named harness tests"]
    spawn_038_tokens_literacy_and_project_label_pkg_1_5["SPAWN-005 delta-reviewer Delta review of test-only repair for PKG1-TEST-01/02/03 #91;gpt-5.6-sol#93;"]
  end
end
review_038_tokens_literacy_and_project_label_pkg_1_1 -->|produjo| finding_038_tokens_literacy_and_project_label_pkg_1_1
review_038_tokens_literacy_and_project_label_pkg_1_1 -->|produjo| finding_038_tokens_literacy_and_project_label_pkg_1_2
review_038_tokens_literacy_and_project_label_pkg_1_1 -->|produjo| finding_038_tokens_literacy_and_project_label_pkg_1_3
verification_038_tokens_literacy_and_project_label_pkg_1_1 -->|verificó| finding_038_tokens_literacy_and_project_label_pkg_1_1
verification_038_tokens_literacy_and_project_label_pkg_1_1 -->|verificó| finding_038_tokens_literacy_and_project_label_pkg_1_2
verification_038_tokens_literacy_and_project_label_pkg_1_1 -->|verificó| finding_038_tokens_literacy_and_project_label_pkg_1_3
repair_038_tokens_literacy_and_project_label_pkg_1_1 -->|reparó| finding_038_tokens_literacy_and_project_label_pkg_1_1
repair_038_tokens_literacy_and_project_label_pkg_1_1 -->|reparó| finding_038_tokens_literacy_and_project_label_pkg_1_2
repair_038_tokens_literacy_and_project_label_pkg_1_1 -->|reparó| finding_038_tokens_literacy_and_project_label_pkg_1_3
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
