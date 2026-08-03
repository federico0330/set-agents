# AC-13: la mitad de discoverability viva del roster queda environment-gated, no BLOCKED de feature

<!-- notas:auto -->
- fecha: 2026-08-02 · actor: orchestrator
- alcance: [[features/013-pi-interactive-target|013-pi-interactive-target]] · [[features/013-pi-interactive-target/P1-pi-interactive-target|P1-pi-interactive-target]]

## Contexto

El chequeo subagent({action:list})//subagents-doctor de AC-13 quedo implementado como test opt-in (SET_AGENTS_PI_E2E=1) con skip nombrado gate=AC-13-pi-subagents-roster. En este sandbox pi-subagents no esta instalado (~/.pi/agent/npm ausente), asi que la mitad del roster degrada a skip nombrado. block transicionaria toda la feature a BLOCKED, desproporcionado para un gap de entorno con test implementado.

## Decisión

Se registra el gap como decision persistida en vez de blocker de fase: el test existe, degrada con nombre, y debe correrse en una maquina con pi-subagents instalado antes de considerar AC-13 completamente ejercitado en vivo.

## Consecuencias

Quien instale pi-subagents corre SET_AGENTS_PI_E2E=1 python3 -m unittest -k roster_discoverable y obtiene la evidencia viva pendiente. El paquete puede aceptarse con esta mitad environment-gated, igual que preveia el propio AC-13.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
