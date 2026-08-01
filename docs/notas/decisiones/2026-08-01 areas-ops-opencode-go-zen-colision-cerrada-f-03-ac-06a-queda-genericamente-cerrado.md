# areas.ops.opencode.go-zen colision CERRADA (F-03); AC-06(a) queda genericamente cerrado, sin residuo

<!-- notas:auto -->
- fecha: 2026-08-01 · actor: repair-agent
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]] · [[features/015-anthropic-dispatch-parity/P1-anthropic-dispatch-parity|P1-anthropic-dispatch-parity]]

## Contexto

El repair pass anterior (F-02, slug areas-judge-opencode-go-zen-colision-cerrada-f-02-amplia-ac-06a-nuevo-residuo-areas-ops) cerro [areas.judge].opencode."go-zen" pero, correctamente, no toco [areas.ops].opencode."go-zen" (== "openai/gpt-5.6-terra", identico al valor de tier frontier de la escalera de seis roles tiered) por estar fuera del alcance que el usuario habia autorizado en ese momento (solo judge) -- se documento como residuo nuevo, explicito, en ADR-0019 D8 y en el log de decisiones.

## Decisión

El usuario aprobo explicitamente cerrar tambien esta tercera celda, mismo patron que audit/judge. [areas.ops].opencode."go-zen" pasa de "openai/gpt-5.6-terra" a "openai/gpt-5.4-mini" (models.toml:141+), alineado con las lanes zen/local propias de esta area y con sus areas operativas hermanas ([areas.gate]/[areas.release]/[areas.memory], que comparten el mismo triplete claude/codex/codex_effort y ya usaban ese mismo valor de go-zen) -- no colisiona con ningun valor de escalera tiered (luna/sol/terra). El test test_ac06a_no_area_go_zen_value_collides_with_any_tiered_roles_go_zen_ladder se reescribe para afirmar cierre total (colliding_sites == set()), sin residuo nombrado en ningun lado. ADR-0019 D8 se actualiza (F-03) para marcar este cierre.

## Consecuencias

AC-06(a) queda genericamente cerrado: ninguna celda [areas.*].opencode.go-zen colisiona con ninguna escalera [roles.tiered-role.tiers.*].opencode.go-zen en todo el arbol. El test de regresion falla si una futura re-tierizacion o re-curacion reabre esta clase de colision en cualquier celda, no solo en las tres ya nombradas.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
