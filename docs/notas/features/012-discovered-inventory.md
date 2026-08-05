# 012-discovered-inventory

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 52
- estado final: **DONE**
- spec: `docs/specs/012-discovered-inventory/spec.md` (hash `fd507fcb13f2`)

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

## Paquetes

- [[features/012-discovered-inventory/P1-discovered-inventory|P1-discovered-inventory]] — accepted · Reemplazar el catálogo de proveedores escrito a mano por un inventario sondeado del entor…

## Approach y decisiones

- [2026-07-30] repair-agent: repair-agent consolidado, orden por severidad: SEC-001 (critical) primero, F-01/F-02 (high, tests que no discriminan) segundo, resto después.
- [2026-07-30] delta-reviewer: delta-reviewer, contexto limpio, acotado al diff de la reparación (catalog.py, service.py, models.toml, models_config.py, ADR-0016, README, test_routing.py).
- [2026-07-30] repair-agent: repair-agent, segunda ronda, alcance mínimo: 3 hallazgos.
- [2026-07-31] delta-reviewer: delta-reviewer, contexto limpio, acotado a los 3 fixes de la ronda 2.
- [2026-08-02] integrator: INTEGRATION entry: read-only validation of P1-discovered-inventory against approved spec 012.
- [2026-08-02] integrator: Integration validation PASS: AC-01..AC-12 verified in tree (pair commands, dual maps, lockstep allowlists, CANONICAL_MODEL aliasing closing SEC-001/002, billing kinds, ADR-0016 Ac…

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 8 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/012-discovered-inventory/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/012-discovered-inventory/bitacora.md`

_Actualizado: 2026-08-02T15:00:53+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
