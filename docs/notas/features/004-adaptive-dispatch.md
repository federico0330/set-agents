# 004-adaptive-dispatch

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 95
- estado final: **DONE**
- spec: `docs/specs/004-adaptive-dispatch/spec.md` (hash `fe543d780deb`)

## Criterios de aceptación

- AC-00
- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09g
- AC-09
- AC-10
- AC-11
- AC-11g
- AC-12
- AC-13

## Paquetes

- [[features/004-adaptive-dispatch/P1-dispatch-core|P1-dispatch-core]] — accepted · Tiered catalog, risk-aware selection, dispatch CLI, probe cache (AM-1/AM-2)
- [[features/004-adaptive-dispatch/P2-opencode-lane|P2-opencode-lane]] — accepted · Tiered OpenCode agent variants <role>@<tier> consumed by the orchestrator per --route-dec…
- [[features/004-adaptive-dispatch/P3-pi-lane|P3-pi-lane]] — accepted · Pi as fourth executable runtime: true cross-provider per-spawn model selection via pi --m…

## Approach y decisiones

- ruteo P1-dispatch-core: Security-critical trust boundary work on the routing core itself; in-session Claude implementer per user instruction, i…
- ruteo P2-opencode-lane: Build-pipeline + orchestrator-doctrine work touching permission surfaces; in-session Claude implementer for speed per u…
- ruteo P3-pi-lane: New runtime axis (4th executable runtime, live model selection); in-session Claude implementer, independent gates+panel…
- [2026-07-27] gate-runner: PACKAGE_GATES P3-pi-lane gate-runner read-only spawn 2/12: unittest 165, build.sh --check, py_compile incl set_agents_spawn+routing_core, verify.sh drift, git diff --check, owners…
- [2026-07-27] package-reviewer: Panel P3-R1 package-reviewer read-only over ced2caa..WORKTREE spawn 3/12: AC-09/10/11/11g/12/13 conformance, spawner lifecycle correctness (crash=>failure, decided-model verificat…
- [2026-07-27] security-auditor: Panel P3-R1 security-auditor read-only spawn 4/12: guard bypass (--no-extensions/--no-session/read-only allowlist), depth-0/no-delegation escape, decided-model spoof (message.mode…
- [2026-07-27] repair-agent: PACKAGE_REPAIR R1 repair-agent (Claude in-session) spawn 5/12: SEC-A01 HIGH neutralize untrusted task-as-flag (fail closed TASK_LOOKS_LIKE_FLAG or stdin) + hostile-task test; SEC-…
- [2026-07-27] gate-runner: DELTA_REVIEW R1 gate-runner read-only spawn 6/12: unittest 172, build.sh --check, py_compile, verify.sh drift, git diff --check, ownership vs ced2caa, SEC-A01 hostile-task refusal…
- [2026-07-27] delta-reviewer: DELTA_REVIEW R1 delta-reviewer read-only spawn 7/12: resolved|open per SEC-A01/A02/A04/A05/PKG-N01/N02; reproduce SEC-A01 hostile-task neutralization; check delta regressions; cor…
- decisión: [[decisiones/2026-07-26 am1-hybrid-facts|AM-1: derivacion hibrida de facts con risk raise-only (enmienda a 003)]]
- decisión: [[decisiones/2026-07-26 am2-probe-cache-fresh-selected|AM-2: cache de probes filtering-only + re-probe fresco del seleccionado (enmienda a 003/ADR-0005)]]
- decisión: [[decisiones/2026-07-26 scope-cheap-tier-and-pi-spike|Alcance 004: tier barato sin opencode/* y P3 condicionado a spike]]
- decisión: [[decisiones/2026-07-27 sec-a02-coord-run-closure-accepted|SEC-A02 accepted: coord may terminal/abandon any routing run]]
- decisión: [[decisiones/2026-07-27 t300-pi-lane-feasibility-yes|T-300 spike: P3-pi-lane is FEASIBLE (all four YES)]]
- decisión: [[decisiones/2026-07-27 ac09-ac10-pi-minimal-target-accepted|AC-09/AC-10 literal deviations accepted: minimal pi target + pnpm-store pin]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 20 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/004-adaptive-dispatch/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/004-adaptive-dispatch/bitacora.md`

_Actualizado: 2026-07-27T14:04:38+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
