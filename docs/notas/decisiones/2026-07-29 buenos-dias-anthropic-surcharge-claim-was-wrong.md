# BUENOS-DIAS.md retractaba mal el costo del carril Pi

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P3-correct-record|P3-correct-record]]

## Contexto

La nota de la sesion 2026-07-27 (docs/notas/BUENOS-DIAS.md) afirmaba dos cosas que 007-P1/P2 verificaron falsas: (1) que el ruteo adaptativo estaba apagado por una routing.db en schema 4 irrecuperable, con rm ~/.local/state/set-agentes/routing-v2/routing.db como remediacion; (2) que el carril anthropic de Pi 'cobra por token como extra-usage'.

## Decisión

Se retractan las dos afirmaciones (AC-19, 007-P3). routing.db ya no existe en la maquina y el ruteo no esta bloqueado; ademas 007-P1 cerro la clase de bug que hacia irrecuperable una base vieja (normalizacion de DDL delimiter-aware, ciega a comentarios). El carril anthropic de Pi no tiene sobrecargo por token: ~/.pi/agent/auth.json entra por anthropic -> {type: oauth}, mismo bucket de cuota que el resto de la suscripcion; el error 'You are out of extra usage' solo prueba agotamiento momentaneo de la cuota incluida. Lo asimetrico real y medido es el consumo por unidad de trabajo: el carril Pi es un subprocess CLI por spawn sin cache entre spawns (ADR-0007), 3221 tokens de entrada por 6 de salida en la unica muestra en vivo.

## Consecuencias

docs/notas/BUENOS-DIAS.md seccion 3 reescrita citando esta decision. Enlaza con routing-db-schema4-unmigratable (la causa raiz que la nota citaba y que 007-P1 cerro).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**Superada 2026-07-29** por
[[decisiones/2026-07-29 buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass|buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-first-pass]].
La `## Decisión` de arriba (bloque auto, append-only) repite dos afirmaciones que un finding-verifier
independiente encontró falsas al momento de escribirlas: "routing.db ya no existe en la máquina" (existe, en
schema 6, con un dispatch real de la QA de 007-P2) y "la única muestra en vivo" (hay dos). La entrada
superadora tiene el texto correcto. `docs/notas/BUENOS-DIAS.md` cita a la superadora, no a esta.
