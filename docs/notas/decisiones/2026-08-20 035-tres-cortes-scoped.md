# 035 scoped: panel honesto, extraer consola, TIPS-USO

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator

## Contexto

Federico pidió las tres piezas diferidas en 035-consult-como-funciona-no-refactor. Señal user-asked-full-pipeline. Ejes store/gateway/deploy no se tocan. MODE_BUDGETS scoped=8 intacto. Cursor sin --route-decide. Engram sigue no-goal.

## Decisión

Abrir scoped 035-panel-honesto-consola-y-tips. Spec y challenge ANTES de init. No código hasta USER_APPROVAL. Tres cortes: (1) extraer routing/vault de set_agents_app.py con caracterización, (2) record-review no puede saltear required_reviewers ni security-auditor, (3) TIPS-USO deja de decir que OpenCode es el único control plane. record-review con findings high en pass queda como deuda hermana a incluir o no-goal explícito en el spec.

## Consecuencias

init --mode scoped --risk-signal user-asked-full-pipeline recién con hash aprobado. Tests que usan record-review como atajo van a tener que pasar por el panel o por small+low.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
