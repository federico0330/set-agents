# 005-portable-harness

<!-- notas:auto -->
## Estado

- fase: `DONE` · modo: feature · revisión 176
- estado final: **DONE**
- spec: `docs/specs/005-portable-harness/spec.md` (hash `e821373ff2e8`)

## Paquetes

- [[features/005-portable-harness/P1-portable-core|P1-portable-core]] — accepted · Make the 004 adaptive router reachable and correctly scoped from any project on any machi…
- [[features/005-portable-harness/P2-vault-mandatory|P2-vault-mandatory]] — accepted · Vault de Obsidian obligatorio: instalacion multiplataforma, registro de vault-link, notes…
- [[features/005-portable-harness/P3-tui|P3-tui]] — accepted · Reemplazar los menús numerados por un selector de flechas stdlib-only, con core puro test…

## Approach y decisiones

- [2026-07-30] -: Abriendo P3-tui: AC-22..AC-30 ya aprobados en el contrato 1.1.0, sin bloqueantes. Narrando apertura antes de crear el paquete (sin --package-id, sin record-spawn contra P2-vault-m…
- [2026-07-30] implementer: implementer, contra P3-tui, AC-22..AC-30, 8 tareas, adversarial-primero
- [2026-07-30] package-reviewer: package-reviewer, contra P3-tui integrado, foco adversarial en AC-26/27 (handoff de terminal + señales)
- [2026-07-30] repair-agent: repair-agent, consolidado, F-01..F-10, tests de regresión rojo-primero por hallazgo
- [2026-07-30] repair-agent: repair-agent, consolidado, 1 llamada record-repair al final
- [2026-07-30] delta-reviewer: delta-reviewer, foco en si D-02/D-03/F-08 (mecanismos nuevos: render a stderr, clamp de header, filtro de search) quedaron genuinamente cerrados
- decisión: [[decisiones/2026-07-27 global-absolute-path-leak|Pre-existing absolute-path leak in tracked Global/ templates (out of P1 scope, tracked)]]
- decisión: [[decisiones/2026-07-27 p1-pi-project-cwd-propagation|Pi lifecycle propagates project context by explicit cwd]]
- decisión: [[decisiones/2026-07-29 record-spawn-misused-for-pre-package-narration-also-trips-budget|record-spawn contra el package_id viejo para narrar la apertura de un paquete nuevo repite el falso bloqueo]]
- decisión: [[decisiones/2026-07-29 adr-0009-slot-taken-by-006-p2-vault-adr-is-0012|AC-10 de 005 nombra docs/adr/0009-mandatory-vault.md pero ese numero ya lo uso 006-P2]]
- decisión: [[decisiones/2026-07-29 tools-toml-obsidian-apt-dnf-zypper-were-fabricated|AC-11's apt/dnf/zypper obsidian identifiers were fabricated, not source-verified]]
- decisión: [[decisiones/2026-07-29 vault-doctor-basename-fallback-still-collides-when-both-sides-unregistered|vault-doctor's basename fallback for an unregistered project still lets two never-registered repos collide]]

## Qué falta

- _nada pendiente_ ✅

## Presupuestos

- spawns: 20 (máx 12/paquete) · deep review máx 2 ciclos

[[00 - Proyecto|⌂ Proyecto]] · [[features/005-portable-harness/grafo|grafo]] · bitácora: `/home/federico/SET-AGENTES/docs/specs/005-portable-harness/bitacora.md`

_Actualizado: 2026-07-30T16:16:18+00:00_
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
