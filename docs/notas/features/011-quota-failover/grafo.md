# 011-quota-failover · grafo

<!-- notas:auto -->
```mermaid
flowchart TD
subgraph sg_011_quota_failover["011-quota-failover"]
  feature_011_quota_failover_1["feature: 011-quota-failover"]
  subgraph sg_011_quota_failover_p1_quota_failover["P1-quota-failover"]
    package_011_quota_failover_p1_quota_failover_1["package: P1-quota-failover"]
    spawn_011_quota_failover_p1_quota_failover_1["SPAWN-001 implementer Implement Feature 011 atomic quota exhaustion failover"]
    spawn_011_quota_failover_p1_quota_failover_2["SPAWN-002 implementer Continue Feature 011 implementation from durable checkpoint"]
    spawn_011_quota_failover_p1_quota_failover_3["SPAWN-003 implementer Complete only AC-06 runner and evidence after implementation checkpoint"]
    blocker_011_quota_failover_p1_quota_failover_1["blocker: open"]
  end
end
package_011_quota_failover_p1_quota_failover_1 -->|bloqueó| blocker_011_quota_failover_p1_quota_failover_1
```
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
