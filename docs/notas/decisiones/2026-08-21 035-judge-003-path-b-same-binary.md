# JUDGE-035-003 contradice el camino (b) aprobado

<!-- notas:auto -->
- fecha: 2026-08-21 · actor: orchestrator
- alcance: [[features/035-panel-honesto-consola-y-tips|035-panel-honesto-consola-y-tips]] · [[features/035-panel-honesto-consola-y-tips/PKG-B|PKG-B]]

## Contexto

Segundo juez 17a6cfd8 pide baseline de 788eb62 vs after del arbol actual para mutant-provider-remove. design.md:518-521: camino (b) corre baseline y after contra el mismo arbol y el mismo binario. --provider-remove no se mudo. El primer juez pedia el caso en el manifiesto; el follow-up lo agrego con el regalo del camino (b).

## Decisión

003 no es defecto. 004 si: el bundle no tenia los informes independientes como markdown; se depositan desde el state JSON (reviews, subreviews, verifications, deltas) sin reescribir veredictos.

## Consecuencias

REVIEWS.md en evidence/. Tercer juez. Si insiste en 003, HUMAN_DECISION_REQUIRED (juez vs ADR-0066).
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
