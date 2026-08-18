# Orden de paquetes: CI y gate primero, consola despues, lane y cuota al final

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]]

## Contexto

El spec 033 ya descompone seis paquetes. El pedido de arranque en Cursor (docs/notas/ARRANQUE-033-CURSOR.md) fija el orden para bajar riesgo: PKG-4 y PKG-5 dejan CI y verify.sh en condiciones de sostener el resto; PKG-2 y PKG-3 son la consola; PKG-1 y PKG-6 tocan mas superficie.

## Decisión

Implementar un paquete por vez hasta accepted, en este orden: PKG-4, PKG-5, PKG-2, PKG-3, PKG-1, PKG-6. No abrir el siguiente con el anterior a medias.

## Consecuencias

El current_package_id del create-package quedo en PKG-6 (ultimo creado). El orquestador ignora ese puntero y arranca por PKG-4.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
