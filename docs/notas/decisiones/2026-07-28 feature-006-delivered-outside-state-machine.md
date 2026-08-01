# La feature 006 se entrego sin archivo de estado (violacion file-first, detectada despues)

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/006-execution-graph|006-execution-graph]]

## Contexto

ai/state/features/ contiene 002, 003, 004 y 005 pero NO 006-execution-graph. La 006 se entrego completa (spec, ADR-0009, codigo, panel de review concurrente, refutacion, dos delta-reviews, auditoria final, 12 commits, 209 tests verdes) SIN pasar nunca por feature-state.py init. Se detecto al abrir la 007, no durante la entrega.

## Decisión

No se backfillea el archivo de estado de la 006. Fabricar a posteriori una historia de transiciones, spawns y revisiones que nunca se registraron produce un expediente que parece autoritativo y no lo es -- exactamente el fallo que el modelo file-first existe para evitar. La 006 queda documentada por lo que si es real y verificable: docs/specs/006-execution-graph/spec.md, docs/adr/0009-finding-verification.md, los 12 commits y la suite de tests. Este registro es el puntero al hueco.

## Consecuencias

STATUS.md no muestra la 006 y nunca lo hara: cualquier lectura del estado del proyecto la omite. Causa raiz del proceso: init de una feature es un paso manual del orquestador sin ningun gate que lo exija, asi que entregar por fuera del state machine no cuesta ningun error -- solo silencio. Candidato a paquete futuro: que verify.sh o build.sh --check fallen si HEAD toca docs/specs/<id>/ sin que exista ai/state/features/<id>.json. La 007 se abrio por el canal correcto antes de escribir una linea de codigo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
