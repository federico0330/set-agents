# El descriptor de ruteo nombra el runtime que realmente ejecuta

<!-- notas:auto -->
- fecha: 2026-08-13 · actor: orchestrator
- alcance: [[features/022-disponibilidad-real|022-disponibilidad-real]] · [[features/022-disponibilidad-real/P1-registro-de-proveedores|P1-registro-de-proveedores]]

## Contexto

La primera decision de P1 salio con el default selected_runtime=opencode y eligio openai-codex/gpt-5.6-terra (run1_881c88). Pero el unico mecanismo de delegacion del orquestador en esta sesion son subagentes de Claude Code, que corren modelos Claude. Registrar ese route_id habria dejado en el paquete la evidencia de que el implementer corrio en opencode.

## Decisión

El descriptor lleva selected_runtime=claude-code cuando la delegacion es por la herramienta Agent. La corrida opencode se abandono (--route-terminal). La decision efectiva es run1_370bfc8a, claude-code/anthropic/opus, effort medium.

## Consecuencias

Un route_id que nombra un runtime que no ejecuto es evidencia falsa del mismo tipo que ADR-0026 prohibe. Tambien fija el criterio de independencia del reviewer de este paquete: el writer es opus, asi que el reviewer necesita otro modelo con contexto limpio.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
