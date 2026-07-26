# Excepción autorizada: tercer ciclo de reparación P1

<!-- notas:auto -->
- fecha: 2026-07-24 · actor: orchestrator
- alcance: [[features/002-adaptive-pi-orchestration|002-adaptive-pi-orchestration]] · [[features/002-adaptive-pi-orchestration/P1-routing-core|P1-routing-core]]

## Contexto

La segunda revisión delta reprodujo P1-DR2-001..008 después de dos lotes de reparación y activó HUMAN_DECISION_REQUIRED.

## Decisión

El usuario autorizó explícitamente un tercer ciclo de reparación, acotado a P1-DR2-001..008.

## Consecuencias

No se reduce aceptación ni seguridad; P2 y P3 siguen bloqueados hasta que P1 pase reparación, delta review, testing y runtime QA.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
