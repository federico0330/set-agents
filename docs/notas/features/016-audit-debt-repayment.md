# 016-audit-debt-repayment

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 61
- estado final: **DONE**
- spec: `docs/specs/016-audit-debt-repayment/spec.md` (hash `a71594c8b921`)

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

## Paquetes

- [[features/016-audit-debt-repayment/P1-harness-debt|P1-harness-debt]] — accepted · PR-07 repair_entry authoritative field + PR-08 extract verification waiver/verdict branch…
- [[features/016-audit-debt-repayment/P2-hygiene|P2-hygiene]] — accepted · Strip client-specific absolute paths/module names from package-gate-runner.md template + …

## Approach y decisiones

- ruteo P1-harness-debt: Self-modification of the state-management harness, behavioral extraction with pinned equivalence, mandatory reviewer di…
- ruteo P2-hygiene: Disjoint low-risk hygiene, additive-only observability, no public contract break
- [2026-08-02] delta-reviewer: DELTA_REVIEW P2 R1: verify structural filter in _decide_status (scope: only _decide_status), CLI-boundary matrix rows, hard-failure rows untouched, no collateral edits.
- [2026-08-02] implementer: PACKAGE_IMPLEMENTATION P1-harness-debt (AC-01..07, AC-11): 6 repair_entry sites + cmd_transition pop + fallback, extract _apply_verification_waiver/_apply_verdicts with pinned beh…
- [2026-08-02] gate-runner: PACKAGE_GATES P1: test_harness full module, 8 new tests + 9 AC-04 tests by name, twin byte-diff, build.sh --check, git diff --check. Full suite/verify.sh deferred to integration (…
- [2026-08-02] package-reviewer: PACKAGE_REVIEW P1: package-reviewer read-only vs AC-01..07/11; AC-05b: every guard line of old cmd_record_verification lands in exactly one extracted function; targeted tests only…
- [2026-08-03] integrator: INTEGRATION 016: read-only validation of P1-harness-debt + P2-hygiene together vs contract 1.1.0, debt ledger closure check (audit-debt-006-p2), no re-run of heavy gates (already …
- [2026-08-03] integrator: Integration validation PASS: P1/P2 disjoint (grep zero cross-hits), 11/11 ACs mapped, non-goals untouched (PR-06/10/11 verified), no lifecycle restriction. Housekeeping: remaining…
- decisión: [[decisiones/2026-08-02 p1f-01-repair-entry-pop-package-id-opcional|P1F-01 aceptado como deuda low: el pop de repair_entry depende del --package-id opcional]]
- decisión: [[decisiones/2026-08-03 audit-debt-006-p2-cierre-parcial-016|Cierre parcial de audit-debt-006-p2: PR-07/08/09 saldadas por 016; PR-06/10/11 siguen diferidas]]

## Qué falta

- 1 hallazgos abiertos

## Presupuestos

- spawns: 10 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/016-audit-debt-repayment/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTS/docs/specs/016-audit-debt-repayment/bitacora.md`

_Actualizado: 2026-08-03T00:02:59+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
