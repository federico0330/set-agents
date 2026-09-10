# Navegación TTY como fundación preexistente de C2

<!-- notas:auto -->
- fecha: 2026-09-09 · actor: orchestrator
- alcance: [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]] · [[features/049-identidad-honesta-modelos/PKG-C2|PKG-C2]]

## Contexto

La copia HEAD no implementa la navegación por números, vim y flechas que los tests aprobados de la consola exigen; la versión actual de tui.py sí pertenece al sistema visual existente que el contrato ordena preservar.

## Decisión

FOUNDATION_REFvuelo puede incluir ai/scripts/tui.py, rotulado preexist preexistente sin receipt igual y sin atribuirlo a 049, para conservar el comportamiento fijado por tests/test_menu_ui.py.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
