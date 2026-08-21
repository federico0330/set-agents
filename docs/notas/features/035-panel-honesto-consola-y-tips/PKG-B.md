# 035-panel-honesto-consola-y-tips · PKG-B

<!-- notas:auto -->
## Motivo

- objetivo: Segunda pasada de extraccion de set_agents_app.py con caracterizacion previa de tres canales y residuo enumerado con experimento propio, sin cambiar el CLI publico de set-agents
- ruteo: Cursor host pin 034/ADR-0063: implementer=composer-2.5; sin --route-decide en el anfitrion → implementer (composer-2.5)
- complejidad: medium
- riesgo: medium
- paths: `ai/scripts/set_agents_app.py`, `ai/scripts/routing_cli.py`, `ai/scripts/vault_ops.py`, `tests/test_routing.py`, `docs/specs/035-panel-honesto-consola-y-tips/evidence`

## Tareas

- [x] T-101 (completed) · 44 cases, 38 identical, 6 declared-uncharacterizable, 0 diffs; NORMALIZERS.md before compare
- [x] T-102 (completed) · design.md §11 path (b): HarnessTests._import :745-797 restore is the ceiling; ADR-0066
- [x] T-103 (completed) · path b: zero moves; valve failed all 16; F-B-ARCH-01 docstring sentences
- [x] T-104 (completed) · evidence/PKG-B-residue-matrix.md 16/16 third column filled, all anclado
- [x] T-105 (completed) · wc -l set_agents_app.py 4399 before and after

## Hallazgos

- PKG-B-F001 [high] closed — testing
- PKG-B-F002 [high] closed — data-integrity
- PKG-B-F003 [medium] closed — testing
- PKG-B-F004 [medium] closed — testing
- PKG-B-F005 [high] closed — correctness
- PKG-B-F006 [high] closed — security

## Recorrido

- review: repair_required (6 hallazgos)
- verificación: 0 refutados, 6 sostenidos
- repair: PKG-B-F001, PKG-B-F002, PKG-B-F003, PKG-B-F004, PKG-B-F005, PKG-B-F006 → 7 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `owned-paths`: pass
- gate `build-check`: pass
- gate `verify.sh`: pass
- gate `characterize-compare`: pass
- gate `risk-classification`: pass

context pack: `docs/specs/035-panel-honesto-consola-y-tips/context/PKG-B.md`

↩ [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
