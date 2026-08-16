# RDD queda definido: es el modulo strict-TDD de gentle-ai, confirmado por Federico

<!-- notas:auto -->
- fecha: 2026-08-16 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D3-posturas-de-autonomia|D3-posturas-de-autonomia]]

## Contexto

El plan de 025 dejo abierto 'a definir antes de la spec: que es RDD en tu vocabulario (no aparece en el repo)'. El package-planner verifico que la premisa era falsa: la sigla YA estaba instalada con un significado, en Global/_canonical/skills/strict-tdd/SKILL.md:17 y strict-tdd-verify/SKILL.md:17, que dicen literalmente 'Ported from gentle-ai (Gentleman Programming) RDD strict-TDD module'. El orquestador lo llevo a decision humana en vez de elegir, porque definirlo distinto habria dejado dos significados de la misma sigla dentro del mismo producto.

## Decisión

Federico confirmo el 2026-08-16: RDD es lo que gentle-ai habia implementado, o sea el modulo strict-TDD ya referenciado en las dos skills. No se define un termino nuevo ni se reconcilia nada: la acepcion instalada es la correcta y la unica. AC-08 de D3 deja de ser 'definir RDD' y pasa a ser exponer el toggle sobre la acepcion que ya existe, junto a los otros toggles de metodologia -TDD estricto por paquete via ADR-0022, y SDD como skill-.

## Consecuencias

D3 queda desbloqueado. Y se evito el defecto que estaba a punto de entrar: un implementer que definiera RDD por su cuenta habria contradicho dos skills que ya viajan instaladas en la maquina de cada usuario, sin que nada lo detectara -no hay ningun chequeo que valide coherencia de vocabulario entre una spec y las skills canonicas-. Ese hueco queda anotado como candidato para el backlog.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
