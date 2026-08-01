# cost-report.py se cae entero si routing.db todavia no migro a schema 6

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: delta-reviewer
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P2-spawn-accounting|P2-spawn-accounting]]

## Contexto

Encontrado en la segunda ronda de delta review de 007-P2 (fuera del diff reparado, no introducido por este paquete): collect_pi hace SELECT de las columnas usage_* sin chequear la version de schema de routing.db. Contra una base schema 4 o 5 (un estado que el propio ADR-0010 declara soportado hasta que se corra --routing-migrate explicitamente), collect_pi levanta sqlite3.OperationalError: no such column: usage_input. main() llama a collect_pi sin try/except, asi que ese crash se lleva puestos los otros tres carriles (opencode/claude-code/codex) en la misma corrida -- cost-report.py entero deja de andar, no solo el carril pi. Reproducido de forma independiente por el orquestador.

## Decisión

No se arregla en 007-P2: la linea que falla (collect_pi, query base) no fue tocada por este paquete ni por su reparacion, y DELTA_REVIEW esta acotada al diff reparado. Se registra para que un paquete futuro (candidato: 007-P3 correct-record, que ya toca esta zona) agregue el mismo tipo de guarda defensiva que collect_pi ya tiene para identidad de proyecto invalida (F-SEC-04/F-PR-05): detectar la ausencia de las columnas usage_* y salir con un aviso por stderr en vez de un traceback.

## Consecuencias

Hasta que se arregle: cualquier usuario que corra cost-report.py contra una routing.db sin migrar a schema 6 ve un traceback crudo y pierde TODOS los carriles del reporte, no solo el de pi. Mitigacion actual: TIPS-USO.md ya documenta que --routing-migrate es necesario; el riesgo es de UX/observabilidad, no de integridad de datos.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
