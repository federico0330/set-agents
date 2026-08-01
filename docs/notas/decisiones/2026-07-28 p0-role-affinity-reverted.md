# P0-role-affinity revertido: codificaba a mano la decision que el usuario quiere dinamica

<!-- notas:auto -->
- fecha: 2026-07-28 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P0-role-affinity|P0-role-affinity]]

## Contexto

El usuario pidio inicialmente sonnet construyendo y gpt auditando, y P0 lo implemento como preferencia de proveedor por rol en routes.v1.toml (12 filas). El panel devolvio dos high: en el carril primario OpenCode una decision anthropic se abandona y cae al agente estatico, perdiendo el tier dinamico; y nada exige que los dos grupos de roles sean disjuntos. Al presentarle las tres opciones de reparacion el usuario rechazo las tres y reformulo el objetivo: que el orquestador elija el modelo y el effort entre TODO lo disponible en el harness donde corre, siendo critico sobre responsabilidad, tokens y tiempo restante de sesion -- por ejemplo kimi-k2.7-code para una tarea chica, opus para una importante.

## Decisión

Revertir P0 entero (routes.v1.toml y tests/test_routing.py) y volver a la linea base de 209 tests. Una preferencia fija de proveedor por rol es lo contrario del objetivo reformulado: le saca al orquestador justo la decision que se le quiere dar. Ademas dos tercios de lo que P0 prometia ya eran ciertos sin el: models.toml [areas.implement] claude=sonnet y [areas.audit] claude=opus ya regian el carril Claude Code, y en review verificada REVIEW_PROVIDER_CONFLICT ya forzaba al reviewer al proveedor opuesto al del escritor.

## Consecuencias

Tres huecos quedan identificados para la feature 008 (seleccion adaptativa real), todos verificados hoy: (1) routes.v1.toml solo conoce openai-codex y anthropic, asi que los modelos propios de OpenCode (kimi-k2.7-code, deepseek-v4-flash-free, glm-5.2, north-mini-code-free, nemotron-3-ultra-free) son irrepresentables para el router aunque existan en models.toml; (2) el effort esta pegado a la fila del tier (fast=low, frontier=high) y no es una variable que el orquestador module por tarea; (3) ningun proveedor expone cuota restante al arnes, asi que lo maximo honesto es medir lo gastado, dejar declarar un presupuesto de sesion y rutear contra el remanente estimado -- lo que hace de 007-P2 dependencia dura de la 008. Se conserva como requisito para la 008 el test que el package-reviewer identifico como unico guardian real del catalogo partido: la enumeracion de que cada rol conserva ambos proveedores en cada tier, porque catalog.py:387 solo verifica la union y no detecta un rol quitado de una sola fila. Copias del catalogo y los tests de P0 quedaron en el scratchpad de la sesion.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
