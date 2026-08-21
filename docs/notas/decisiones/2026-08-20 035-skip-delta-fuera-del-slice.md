# record-repair --skip-delta no entra en 035

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator

## Contexto

spec-challenger F-035-002: record-repair --skip-delta (cli_repair.py:274-282) puede llegar a PACKAGE_TESTING con otro finding abierto. Pedido original: tres cortes (panel vs record-review, extraer consola, TIPS). La deuda hermana de record-review pass sí entra porque era el mismo comentario de transitions.py.

## Decisión

skip-delta queda no-goal nombrado. AC-A.4/A.5 se limitan al verbo record-review, no a 'todas las puertas hacia PACKAGE_TESTING'. El advisor de transitions.py se conserva. Un slice futuro puede cerrar skip-delta; 035 no se infla.

## Consecuencias

Producto-analyst revisa el contrato con este recorte. Sí entra: ADR de contrato público de record-review + doctrina orchestrator.md (F-035-001). Sí entra: corrección de medición required_reviewers ausente vs null, mordidas enumeradas, PKG-B matriz falsable, caracterización de salida completa.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
