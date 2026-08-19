# 034-cuota-organica-y-writer-barato · PKG-D

<!-- notas:auto -->
## Motivo

- objetivo: Pins Cursor por rol desde models.toml; generate.py deja de forzar inherit; 032 AC-06 superseded en parte
- ruteo: cursor-host native subagent; no --route-decide (032); inherit → implementer (inherit)
- complejidad: high
- riesgo: high
- paths: `ai/scripts/generate.py`, `ai/scripts/models_config.py`, `models.toml`, `tests/test_harness.py`
- depende de: PKG-B

## Tareas

- [x] T-D01 (completed) · generate-cursor-pins, build-check
- [x] T-D02 (completed) · family-cursor-branch, unittest-cursor
- [x] T-D03 (completed) · validate-cursor-target-rewrite, test-rewrite
- [x] T-D04 (completed) · doctrine-cursor, rg-no-inherit-phrase

## Hallazgos

- SEC-001 [high] closed — security

## Recorrido

- review: repair_required (1 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- repair: SEC-001 → 4 archivos
- delta review: pass
- testing: pass
- runtime QA: pass (waived)
- gate `P001`: pass
- gate `focused-tests`: pass
- gate `build-check`: pass
- gate `repair-ceiling`: pass

context pack: `docs/specs/034-cuota-organica-y-writer-barato/context/PKG-D.md`

↩ [[features/034-cuota-organica-y-writer-barato|034-cuota-organica-y-writer-barato]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
