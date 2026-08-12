# El repair de P5 murio por stall de infraestructura; se relanza una vez (asignacion distinta al implementer)

<!-- notas:auto -->
- fecha: 2026-08-11 · actor: orchestrator
- alcance: [[features/019-harness-evolution|019-harness-evolution]] · [[features/019-harness-evolution/P5-tools-discovery|P5-tools-discovery]]

## Contexto

Segundo 'Agent stalled: no progress for 600s' de la sesion, ahora en el rol repair-agent. Verificado en disco por el orquestador: no dejo NADA -- no existe docs/specs/019-harness-evolution/evidence/P5-repair.md, ADR-0038 conserva su timestamp original (15:30), y los tres bloqueantes siguen vivos: _validate_install_command('true & touch /tmp/X') devuelve None, '/usr/bin/sudo apt install x' devuelve None, _toml_str('a\nb') devuelve el basic string sin terminar. El diff stat coincide exacto con lo que dejo el implementer.

## Decisión

Es una muerte de infraestructura, no una falla en la tarea, y es una ASIGNACION DISTINTA a la del implementer (que ya gasto su relanzamiento): el presupuesto de un relanzamiento se cuenta por asignacion, no por paquete. Se relanza el repair una vez, con la misma mitigacion que funciono en el relanzamiento del implementer: escribir el archivo de evidencia desde el primer minuto e ir reparando de a un finding, escribiendo a disco despues de cada uno. Una segunda muerte del repair si es un blocker real y se reporta como tal.

## Consecuencias

Patron a vigilar: los dos stalls de la sesion fueron en agentes mutadores de corrida larga. Si vuelve a pasar, la respuesta no es un tercer relanzamiento sino partir el encargo, aunque eso complique la ownership del archivo compartido.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
