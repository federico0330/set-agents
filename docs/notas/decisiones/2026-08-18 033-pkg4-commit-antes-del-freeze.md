# PKG-4 se commitea antes del freeze porque el candidato exige refs ya en git

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator
- alcance: [[features/033-menos-espera-menos-cuota|033-menos-espera-menos-cuota]] · [[features/033-menos-espera-menos-cuota/PKG-4|PKG-4]]

## Contexto

candidate_identity.py:7-8 dice que freeze resuelve dos refs commiteadas via git rev-parse ref^{tree} y nunca un worktree. Sin commit, freeze de HEAD contra HEAD deja changed_paths vacio y classify-risk mentiria low.

## Decisión

Un commit con el diff de PKG-4 mas los context packs y notas de 033, despues freeze-candidate --baseline HEAD^ --candidate-ref HEAD. No es un commit oportunista: es el invariante del freeze.

## Consecuencias

El SHA local queda listo para AC-4.5 cuando se empuje. Hasta entonces el techo de skips ya esta en el job.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
