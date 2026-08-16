# 025-consola-minima-y-flexible · D1-superficie-humana

<!-- notas:auto -->
## Motivo

- objetivo: Menu sin emoji, 31 flags internas ocultas pero vivas, y salida humana en vez de JSON crudo
- complejidad: medium
- paths: `ai/scripts/set_agents_app.py`, `ai/scripts/tui.py`, `tests`, `docs/adr`

## Tareas

- [x] Menu sin emoji, jerarquia por espaciado y peso (AC-01) (completed) · MENU_ITEMS sin emoji, con agrupacion por proposito y separacion antes de Salir. La guarda dejo de ser lista negra de rangos unicode -que no cubria U+23FB, el glifo que motivo el paquete- y paso a regla positiva isascii; mordida con el glifo reinyectado., El emoji del primer arranque en set_agents_app.py:3550, que solo veia el usuario nuevo y que ningun test miraba, tambien salio.
- [x] Ocultar las 31 flags internas del --help sin romperlas, con --help --avanzado (AC-02) (completed) · 28 de 68 flags ocultas con help=argparse.SUPPRESS, ninguna borrada, y --help --avanzado las muestra: 40 visibles por default contra 68 con la flag, verificado en vivo. El corte se hizo con evidencia por flag -mencion en documentacion humana contra mencion en prompts de agentes y coord_policy.SAFE_ARGV-, no con la cuota de 31 que la spec habia heredado de una exploracion vieja., Test que prueba que cada flag oculta sigue respondiendo end-to-end, y guarda contra borrado con lista literal congelada en el test: la version anterior usaba la misma constante que el codigo como oraculo, o sea se preguntaba a si misma, y el reviewer la rompio borrando la flag de los dos lados.
- [x] Texto humano por default en los comandos de routing, --json para la maquina (AC-03) (completed) · routing_human = not args.json: texto humano a stderr por default, y --json preserva el sobre byte por byte -cmp da IDENTICAL sobre 6358 bytes-. La rama humana dejo de imprimir repr() de Python: antes escupia una linea de 5763 caracteres con tuplas, False y reason_codes duplicado., El hallazgo que casi se escapa, y que encontro el review: los prompts de los cuatro harnesses ordenan --routing-recent-writers y --route-terminal SIN --json, y de ahi sale el review_of_run_id cuando el contexto se compacto. Sin el arreglo, el orquestador recibia stdout vacio, no encontraba el id, y todo reviewer se spawneaba con REVIEW_IDENTITY_UNVERIFIED, en silencio y sin que ningun test fallara. Los cinco archivos corregidos, con BUILD_CHECK_PASS.

## Hallazgos

- D1-F01 [high] open — correctness
- D1-F02 [high] open — correctness
- D1-F03 [high] open — correctness
- D1-F04 [medium] open — correctness
- D1-F05 [medium] open — correctness
- D1-F06 [medium] open — testing
- D1-F07 [low] open — testing
- D1-F09 [low] open — readability

## Recorrido

- review: repair_required (8 hallazgos)
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/sonnet · effort medium · route run1_9a9d617d4b6885d58de13f800a9afd95
- SPAWN-002 package-reviewer · modelo anthropic/claude-opus-5 · effort high
- SPAWN-003 repair-agent · modelo anthropic/claude-sonnet-5 · effort medium

context pack: `docs/specs/025-consola-minima-y-flexible/context/D1-superficie-humana.md`

↩ [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
