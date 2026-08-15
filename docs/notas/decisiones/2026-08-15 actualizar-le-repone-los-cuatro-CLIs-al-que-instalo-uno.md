# Defecto latente: cmd_update ignora install-targets.json y reinstala los cuatro arboles

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D4-harness-por-CLI|D4-harness-por-CLI]]

## Contexto

Encontrado por el package-planner de 025 mientras verificaba las afirmaciones del plan sobre D4. Cadena de codigo: set_agents_app.py:1252 arma 'build.sh --install' SIN --target, e install.py:569-570 hace 'if not args.target: scope = set(all_targets)'. install.sh:29-32 y :387-392 si respetan --harness, y check-drift.sh:26 ya lee ~/.local/state/set-agentes/install-targets.json para comparar solo contra los arboles instalados. O sea: la instalacion selectiva existe y funciona, pero la ACTUALIZACION la deshace.

## Decisión

No se repara fuera de su paquete. Queda anotado como la primera verificacion que debe hacer el implementer de D4, en un --home temporal: instalar con --harness claude, correr Actualizar, y comprobar si install-targets.json vuelve a los cuatro. Si se confirma, AC-09 NO esta cumplido aunque --target exista, y el paquete cambia de tamano.

## Consecuencias

Un usuario que deliberadamente dejo tres CLIs virgenes los recupera poblados en el primer 'Actualizar', sin aviso y sin haberlo pedido. Es exactamente la clase de escritura no consentida que 024/C3 reparo en el primer arranque (ADR-0049), reapareciendo por la puerta del update. AFIRMACION POR LECTURA DE CODIGO, NO EJECUTADA: el planner tenia prohibido tocar ~, asi que la cadena esta leida y no corrida.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
