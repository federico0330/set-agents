# 002-adaptive-pi-orchestration

<!-- notas:auto -->
## Estado

- fase: `BLOCKED` · modo: feature · revisión 57
- estado final: **BLOCKED**
- spec: `docs/specs/002-adaptive-pi-orchestration/spec.md` (hash `77fed4274cc4`)

## Criterios de aceptación

- AC-01
- AC-02
- AC-03
- AC-04
- AC-05
- AC-06
- AC-07
- AC-08
- AC-09
- AC-10
- AC-11
- AC-12
- AC-13
- AC-14
- AC-15

## Paquetes

- [[features/002-adaptive-pi-orchestration/P1-routing-core|P1-routing-core]] — repair_required · Schema-2 configuration, deterministic routing, proportional flows, telemetry, CLI, and na…

## Approach y decisiones

- ruteo P1-routing-core: Critical routing contract requires hosted frontier implementation
- [2026-07-24] repair-agent: PACKAGE_IMPLEMENTATION exception cycle 3; P1-DR2-001..008, owned P1 paths, hosted model, finding-specific regressions, no self-approval.
- [2026-07-24] repair-agent: P1-DR2-001..008 implementados en routing.py/tests; gates locales PASS, verify global conserva dos fallas P3 conocidas.
- [2026-07-24] package-reviewer: PACKAGE_REVIEW P1-R2; correctness/integration/tests, read-only, closure evidence for P1-DR2.
- [2026-07-24] security-auditor: PACKAGE_REVIEW P1-R2 security lane; filesystem/no-follow/crash consistency/reviewer independence, read-only.
- [2026-07-24] package-reviewer: P1-R2 package-reviewer repair_required: DR2-004/005/006 closed; DR2-001/002/003/007/008 open con probes.
- [2026-07-24] security-auditor: P1-R2 security subreview errored por policy del proveedor; sin hallazgos inventados, evidencia registrada como blocked.
- decisión: [[decisiones/2026-07-24 p1-third-repair-authorization|Excepción autorizada: tercer ciclo de reparación P1]]
- decisión: [[decisiones/2026-07-30 002-retirado-superseded-por-003-trusted-routing-pi-runtime|002 retirado, superseded por 003-trusted-routing-pi-runtime]]

## Qué falta

- → corresponde tu decisión (ver Blocker)
- ⛔ bloqueo: HUMAN_DECISION_REQUIRED: user-authorized third repair cycle failed final review; five high findings remain and P1 exhau…
- 5 hallazgos abiertos

## Presupuestos

- spawns: 12 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/002-adaptive-pi-orchestration/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/002-adaptive-pi-orchestration/bitacora.md`

_Actualizado: 2026-07-24T16:16:04+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**2026-07-30 — Feature retirada.** El bloqueo de arriba (`P1-routing-core`, 5 hallazgos altos) quedó
superado: el rediseño que pedía (catálogo de confianza, observations, identidad de implementador, telemetría
crash-safe) se construyó y aceptó bajo [[../../003-trusted-routing-pi-runtime/spec|003-trusted-routing-pi-runtime]]
(`DONE`, 2026-07-29). Ver la decisión de retiro arriba y `docs/specs/002-adaptive-pi-orchestration/spec.md`
(nota de supersesión). No hay más trabajo de código previsto bajo esta feature; `phase`/`final_state` quedan
`BLOCKED` a propósito (el arnés no tiene un estado `SUPERSEDED` propio — ver la decisión para el detalle).
