# En Cursor no se instalan hooks de evento en esta version

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/032-cursor-como-runtime|032-cursor-como-runtime]]

## Contexto

Cursor soporta hooks.json con beforeShellExecution y contrato JSON por stdin/stdout (verificado 2026-08-18). El harness tiene coord_policy.py, la politica que ya sufrio un RCE por prefix-match (feature 030). Portarla a Cursor requiere distinguir el agente principal de un subagente, y el payload de beforeShellExecution no trae esa distincion: una politica coord-ro aplicada a todo bloquearia las escrituras legitimas del implementer.

## Decisión

El target cursor se instala sin hooks.json. La superficie que gobierna en Cursor es su propio modelo de permisos, y eso se dice explicitamente en README, INSTALACION y en la doctrina que el propio agente lee (Global/_shared/AGENTS.cursor.md).

## Consecuencias

Una guarda ausente y declarada es honesta; una guarda presente que no cubre lo que promete es un defecto. Los hooks de Cursor quedan como trabajo siguiente, con la pregunta abierta de como identificar al subagente que corre el comando.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
