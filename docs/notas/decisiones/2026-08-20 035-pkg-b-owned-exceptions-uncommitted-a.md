# Excepciones PKG-B por PKG-A sin commitear

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-B|PKG-B]]

## Contexto

PKG-A accepted pero el working tree sigue sucio vs HEAD 788eb62. check-owned-paths de PKG-B veria feature_state_lib, twins, Global, tests y docs de A como cambio fuera de owned_paths. No hay commit: el usuario no lo pidio.

## Decisión

update-package --exception sobre las rutas sucias de A y las docs vivas. No ensancha owned_paths de B. No autoriza al implementer de B a editar esas rutas.

## Consecuencias

El candado de B sigue en set_agents_app.py, routing_cli.py, vault_ops.py, test_routing.py y evidence. Un archivo nuevo en ai/scripts/ se declara owned o exception cuando el architect lo nombre.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
