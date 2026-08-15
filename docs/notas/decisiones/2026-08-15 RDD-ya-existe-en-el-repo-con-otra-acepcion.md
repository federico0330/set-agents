# RDD no es un termino a definir: ya esta en uso instalado, con otro significado

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/025-consola-minima-y-flexible|025-consola-minima-y-flexible]] · [[features/025-consola-minima-y-flexible/D3-posturas-de-autonomia|D3-posturas-de-autonomia]]

## Contexto

El plan de 025 dejo 'a definir antes de la spec: que es RDD en tu vocabulario (no aparece en el repo)'. El package-planner lo verifico y la premisa es falsa: Global/_canonical/skills/strict-tdd/SKILL.md:17 y strict-tdd-verify/SKILL.md:17 dicen literalmente 'Ported from gentle-ai (Gentleman Programming) RDD strict-TDD module'. La sigla ya viaja instalada en las maquinas de los usuarios, asociada a TDD estricto.

## Decisión

AC-08 deja de ser 'definir un termino nuevo' y pasa a ser 'reconciliar una sigla ya en uso sin contradecir dos skills instaladas'. Si Federico queria decir otra cosa con RDD, eso es una pregunta para el, no una decision del implementer: se le plantea con las dos acepciones a la vista en vez de elegir una en silencio.

## Consecuencias

Definir RDD como cosa distinta de lo que dicen las dos skills instaladas produciria dos significados de la misma sigla dentro del mismo producto, que es peor que no tener el toggle. El planner tambien verifico que coord_policy.py NO es donde vive la constante de autonomia: son 327 lineas de allowlist de comandos bash, gobiernan que comando puede correr un agente y no cuanto pregunta.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
