# 014-model-preference-policy

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 40
- estado final: **DONE**
- spec: `docs/specs/014-model-preference-policy/spec.md` (hash `a75c53dbed98`)

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

## Paquetes

- [[features/014-model-preference-policy/P1-model-preference-policy|P1-model-preference-policy]] — accepted · Role-class-scoped model/provider preference: taxonomy+resolver, sibling config+CLI, one s…

## Approach y decisiones

- ruteo P1-model-preference-policy: Edits the live primary-dispatch sort key + new atomic config surface + CLI with fail-closed validation; architecture-cr…
- [2026-08-02] gate-runner: PACKAGE_GATES 014 + PACKAGE_TESTING 016-P1: full discover, verify.sh, build.sh --check/--diff, git diff --check, serialized single-runner per build-staging race decision.
- [2026-08-02] package-reviewer: PACKAGE_REVIEW 014: read-only vs contract 3.2.0; sort-key position, resolver partition, config surface, observability, ADR-0018; targeted tests only.
- [2026-08-02] security-auditor: PACKAGE_REVIEW 014: security-auditor read-only on sort-key placement vs REVIEWER_INDEPENDENCE, _model_preference internal-marker injection, TOML parsing fail-closed, atomic writes.
- [2026-08-03] finding-verifier: FINDING_VERIFICATION 014: refute/uphold SEC14-01, RF14-01..07 with live reproduction where claimed.
- [2026-08-03] repair-agent: PACKAGE_REPAIR 014 R1: except clauses (show/route-explain), dedicated MODEL_PREFERENCE_INVALID handling in route-decide, production-plumbing test with populated STATE_DIR, service…
- [2026-08-03] delta-reviewer: DELTA_REVIEW 014 R1: verify except-clause mappings, production-plumbing test bites, full-doc validation both write paths, marker pop, deviation durably recorded.
- decisión: [[decisiones/2026-08-03 ac-01i-grunt-no-flip-en-verified-review-2-proveedores|AC-01(i): grunt no puede flippear provider en verified review con catalogo de 2 proveedores]]

## Convenciones

| Eje | Origen | Stance | Umbral | Siguiente | Revisit |
|---|---|---|---|---|---|
| data-store | - | - | - | - | - |
| api-gateway | - | - | - | - | - |
| deploy-platform | - | - | - | - | - |
| audience | - | - | - | - | - |
| embeddings | - | - | - | - | - |
| realtime | - | - | - | - | - |
| mobile | - | - | - | - | - |
| auth | - | - | - | - | - |
| cost | - | - | - | - | - |
| legal | - | - | - | - | - |

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 7 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/014-model-preference-policy/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/014-model-preference-policy/bitacora.md`

_Actualizado: 2026-08-03T00:38:12+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
