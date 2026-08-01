# La primera correccion de BUENOS-DIAS.md tambien afirmaba sin verificar

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P3-correct-record|P3-correct-record]]

## Contexto

Supersede a buenos-dias-anthropic-surcharge-claim-was-wrong (2026-07-29T15:25:33+00:00). El package-reviewer de 007-P3 (panel RP-01) encontro que el texto de reemplazo copiaba el Contexto de spec.md (fechado 2026-07-28) como presente, sin re-verificar contra la maquina real. Dos afirmaciones nuevas resultaron falsas: (1) 'routing.db ya no existe' -- la verificacion en vivo de 007-P2 (spawn real por el carril Pi, 2026-07-29 10:10) la recreo en schema 6 con un dispatch real (usage_input=3321, usage_output=5, cost_micros=3351); (2) 'una base vieja migra en vez de quedar atascada' -- contradice el alcance explicito de 007-P1 (spec.md: 'not recovery of that database') y la decision del 2026-07-28 de descartar los dos backups schema-4 reales, que ademas de los comentarios les falta el CHECK N03 y siguen rechazados por AC-04/AC-05 a proposito. Tambien: 'la unica muestra en vivo' era falso (hay dos, 3221/6 y 3321/5); la comparacion 'para features largas eso pesa mas que el proveedor que elijas dentro del carril' reintroducia la comparacion anthropic-vs-openai-codex que el contrato 007 excluye explicitamente; y un item de la cola de trabajo (migrate_from_v4 en la 005) seguia listado como pendiente cuando 007-P1 ya lo entrego.

## Decisión

docs/notas/BUENOS-DIAS.md reescrito de nuevo verificando cada afirmacion contra el disco en el momento de escribirla, no contra la fecha del spec citado: se nombra que routing.db existe en schema 6 con el dispatch real de la QA de P2; se acota la reparacion de DDL a AC-03 (divergencia solo-comentarios) dejando explicito que los backups reales siguen rechazados por diseno y descartados por decision previa; se citan las dos muestras de usage en vez de una; se nombra la comparacion entre carriles como fuera de alcance con su razon (routes.v1.toml + enabled_providers todo-o-nada); se marca el item de cola como entregado; y las dos referencias sueltas a 'log-decision' pasan a citar el slug real.

## Consecuencias

Leccion para el propio arnes, no solo para esta nota: una correccion de prosa que copia el estado de un documento fechado como si fuera el estado actual de la maquina reproduce el mismo defecto que corrige. Toda afirmacion de estado de infraestructura en docs/notas/ se verifica contra el sistema en el momento de escribirla.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
