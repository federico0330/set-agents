# B3 se relanza en otro proveedor por limite de sesion, no por fallar la tarea

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/023-senales-de-consumo|023-senales-de-consumo]] · [[features/023-senales-de-consumo/B3-ventana-y-rollup|B3-ventana-y-rollup]]

## Contexto

El implementer de B3 (claude-code/anthropic/opus, run1_0f2ddb58) murio con 'You've hit your session limit, resets 3:50pm'. Verificado por el orquestador: NO dejo codigo a medias -git status solo muestra estado y notas del propio orquestador-, no existe el archivo de evidencia, y store.py no tiene ningun _migrate_7_to_8. El schema sigue en 7.

## Decisión

Relanzo UNA vez en otro proveedor, sin preguntar, segun la regla de continuidad de turno: una instancia que muere por agotamiento de cuota no fallo la tarea y no consume presupuesto de reintentos. Nueva decision run1_af1780fa, codex/openai-codex/gpt-5.6-terra, verificado vivo con un PONG antes de despachar. El run anterior se cierra como failure porque --route-quota-exhausted rechazo el input.

## Consecuencias

Queda una sola relanzada para esta asignacion: si el segundo intento tambien muere, es un blocker real y se reporta como tal. La lane de anthropic queda degradada hasta las 15:50; el orquestador sigue trabajando dentro de los proveedores que quedan, que es lo que la doctrina pide -degradado no es detenido-. Los reviews independientes ya venian corriendo en codex, asi que la independencia por proveedor ahora exige cuidado: si el writer es codex, el reviewer NO puede serlo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
