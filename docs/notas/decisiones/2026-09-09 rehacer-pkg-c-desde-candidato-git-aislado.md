# Rehacer PKG-C desde candidato Git aislado

<!-- notas:auto -->
- fecha: 2026-09-09 · actor: orchestrator
- alcance: [[features/049-identidad-honesta-modelos|049-identidad-honesta-modelos]]

## Contexto

La primera identidad candidata apuntó HEAD contra HEAD y no capturó el worktree; no existe snapshot pre-reparación recuperable.

## Decisión

Por elección explícita del usuario, se reconstruye PKG-C como candidato Git aislado con sólo sus paths, preservando el árbol sucio 045–048 y sin waivar el gate.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
