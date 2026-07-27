# 004-adaptive-dispatch

<!-- notas:auto -->
## Estado

- fase: `PACKAGE_ACCEPTED` · modo: feature · revisión 34
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

## Approach y decisiones

- ruteo P1-dispatch-core: Security-critical trust boundary work on the routing core itself; in-session Claude implementer per user instruction, i…
- [2026-07-27] package-reviewer: Panel P1-R1, package-reviewer read-only over 03939b1..WORKTREE, spawn 3/12: AC-00..AC-05 conformance, 003 invariant regressions, AM-1/AM-2 fidelity, tier semantics, structured fin…
- [2026-07-27] security-auditor: Panel P1-R1, security-auditor read-only, spawn 4/12: descriptor abuse/tier downgrade, cache poisoning/staleness, abandoned-state abuse, envelope redaction, R3 threat model applies.
- [2026-07-27] repair-agent: PACKAGE_REPAIR R1, repair-agent (Claude in-session) spawn 5/12: reason->exit table (PKG-N01/SEC-002), single-UPDATE abandon+audit (PKG-N02/SEC-A/B), abandoned DDL CHECK+timestamp …
- [2026-07-27] gate-runner: DELTA_REVIEW R1 gate-runner read-only spawn 6/12: focused 48, harness 2, setup, py_compile incl routing_core, GateSpecs, verify.sh >=300s, CLI matrix, git diff --check, ownership …
- [2026-07-27] delta-reviewer: DELTA_REVIEW R1 delta-reviewer read-only spawn 7/12: decide resolved|open per PKG-N01..N11/SEC-A01..A03 against contract 1.1.0; reproduce each attack; check delta regressions; ver…
- [2026-07-27] orchestrator: P1-dispatch-core PACKAGE_ACCEPTED: impl (T-100..T-105) + P1-R1 consolidated repair (18 findings from 2 package-reviewers + 1 security-auditor) + independent gates + delta-review p…
- decisión: [[decisiones/2026-07-26 am1-hybrid-facts|AM-1: derivacion hibrida de facts con risk raise-only (enmienda a 003)]]
- decisión: [[decisiones/2026-07-26 am2-probe-cache-fresh-selected|AM-2: cache de probes filtering-only + re-probe fresco del seleccionado (enmienda a 003/ADR-0005)]]
- decisión: [[decisiones/2026-07-26 scope-cheap-tier-and-pi-spike|Alcance 004: tier barato sin opencode/* y P3 condicionado a spike]]

## Qué falta

- → `INTEGRATION` — all packages accepted

## Presupuestos

- spawns: 7 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/004-adaptive-dispatch/bitacora.md`

_Actualizado: 2026-07-27T10:01:27+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
