# Pasada de integración 2026-08-02: 008 y 012 a DONE; 006 y 010 quedan PACKAGE_ACCEPTED por diseño

<!-- notas:auto -->
- fecha: 2026-08-02 · actor: orchestrator

## Contexto

Cuatro features estaban en PACKAGE_ACCEPTED con próximo paso INTEGRATION en el tablero. Se corrieron cuatro validaciones de integración read-only (una por feature, contra spec aprobada y ACs) más un gate global determinista (verify.sh 558 tests OK skipped=1, unittest 558 OK, build.sh --check CHECK_PASS SELF_SCAFFOLD_SYNC_OK, baseline fa43fce). Las cuatro validaciones dieron pass sin hallazgos bloqueantes.

## Decisión

008-dynamic-selection y 012-discovered-inventory transicionan INTEGRATION->DONE con gate global registrado. 006-execution-graph NO transiciona: su spec (docs/specs/006-execution-graph/spec.md:198-204) ordena que quede en PACKAGE_ACCEPTED para siempre porque P1/P2 se entregaron bajo waiver y solo las 9 ACs de P3 se rastrearon. 010-spawn-provenance NO transiciona: HANDOFF-PASO9 §5.5 y su spec lo fijan en PACKAGE_ACCEPTED, sin requisito de INTEGRATION/DONE.

## Consecuencias

El tablero seguirá mostrando 'próximo paso: INTEGRATION' para 006 y 010: es fraseo automático del renderer para toda feature en PACKAGE_ACCEPTED, no trabajo pendiente. Queda anotado en BUENOS-DIAS.md §5 y en 00 - Proyecto.md. Observación no bloqueante de 010: el edit a docs/adr/0013 existe en el árbol pero packages[0] no registra el objeto exception (hueco de contabilidad, no de sustancia).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
