# 027-controles-que-miran · P3-gates-que-preguntan-antes

<!-- notas:auto -->
## Motivo

- objetivo: Que el gate de pi corra antes del subproceso y que _decide_status filtre los codigos de modelo
- complejidad: medium
- paths: `ai/scripts/routing_core`, `ai/scripts/routing_cli.py`, `tests`, `docs/adr`
- depende de: P2-nada-escribe-afuera

## Tareas

- [x] El gate de credenciales de pi corre antes del subproceso, sin cambiar el resultado (AC-06) (completed) · Espia fail-fast sobre catalog.subprocess.run con credencial invalida: cero llamadas, y el par de pi queda ausente. Rojo confirmado contra el codigo previo, donde el proceso pinneado corria primero., Credencial valida: el proceso de list-models si se llama y vuelve el mismo modelo curado; columnas malas, exit no-cero y salida vacia siguen ausentes, fail-closed. Diferencial de 10 escenarios del reviewer: resultado observable identico en los 10., P3-F04 reparado: el gate movido quedo dentro del try/except fail-closed, con test que muerde (test_ac06_pi_key_gate_surprise_only_drops_the_pair_never_raises) y complemento que prueba que un par ajeno queda intacto.
- [x] _decide_status filtra MODEL_PINNED y MODEL_REQUEST_* (AC-07) (completed) · Matriz de test_decide_status_helper_matrix extendida: los tres marcadores nombrados dan (True,0); combinados con FACTS_INCOMPLETE o REVIEWER_INDEPENDENCE_UNAVAILABLE siguen dando (False,1), o sea el filtro no es allow-all., P3-F01 reparado: el comodin MODEL_REQUEST_ paso a los dos codigos nombrados CON separador final. Verificado por el orquestador en el arbol integrado: MODEL_REQUEST_TOTALLY_NEW_HARD_FAILURE y el prefijo pelado pasaron de (True,0) a (False,1), y los tres nombrados siguen en (True,0)., P3-F03 reparado: asercion end-to-end nueva sobre test_route_decide_cli_hermetic_matrix, con model-preference.toml real, exit 0 y MODEL_PINNED presente en el envelope por el CLI real, no sobre RouteDecision sinteticos.

## Hallazgos

- P3-F01 [medium] closed — correctness
- P3-F02 [medium] closed — correctness
- P3-F03 [medium] closed — testing
- P3-F04 [low] closed — resilience
- P3-F05 [low] closed — readability

## Recorrido

- review: repair_required (5 hallazgos)
- verificación: 0 refutados, 5 sostenidos
- repair: P3-F01, P3-F02, P3-F03, P3-F04, P3-F05 → 5 archivos
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass
- gate `ownership`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/claude-sonnet-5 · effort medium
- SPAWN-002 package-reviewer · modelo anthropic/claude-opus-5 · effort high
- SPAWN-003 repair-agent · modelo anthropic/claude-sonnet-5 · effort medium

context pack: `docs/specs/027-controles-que-miran/context/P3-gates-que-preguntan-antes.md`

↩ [[features/027-controles-que-miran|027-controles-que-miran]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
