# Guía educativa COMO-FUNCIONA.md; no hay refactor unbounded

<!-- notas:auto -->
- fecha: 2026-08-20 · actor: orchestrator

## Contexto

Pedido: leer todo, pulir calidad, corroborar por qué en Claude no corren gates de seguridad/infra, y un .md de cómo funciona el harness. Triage: consult + documento. El refactor de todo el árbol viola la regla de no-refactors oportunistas.

## Decisión

Se escribe docs/COMO-FUNCIONA.md (humano, no notas:auto). No se inicia pipeline ni se toca código de producción. El ausente security-auditor en Claude es la lane quick-fix (ADR-0064), no un runtime roto. No existe infrastructure-auditor; architect + runtime_surface cubren infra. Diferido a pedido explícito: extraer set_agents_app, cerrar gap record-review vs start-review-panel, actualizar TIPS-USO control plane.

## Consecuencias

Federico tiene un mapa pedagógico. Un polish de calidad requiere scoped con --risk-signal user-asked-full-pipeline o public-contract. TIPS-USO.md sigue diciendo que OpenCode es el único control plane; la guía nueva documenta que Claude/Cursor también orquestan.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
