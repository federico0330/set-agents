# AC-01(i): grunt no puede flippear provider en verified review con catalogo de 2 proveedores

<!-- notas:auto -->
- fecha: 2026-08-03 · actor: repair-agent
- alcance: [[features/014-model-preference-policy|014-model-preference-policy]] · [[features/014-model-preference-policy/P1-model-preference-policy|P1-model-preference-policy]]

## Contexto

El catalogo real hoy solo tiene anthropic/openai-codex autenticados. En una decision de review VERIFICADA (con review_of_run_id), REVIEW_PROVIDER_CONFLICT ya excluye al provider del writer antes del sort, dejando exactamente un provider candidato sobreviviente. Una preferencia grunt configurada no puede, con solo 2 proveedores, elegir un provider DISTINTO en ese caso -- solo puede probarse que hace sobrevivir al candidato anthropic donde antes no sobrevivia (PROVIDER_UNAUTHENTICATED/REVIEW_PROVIDER_CONFLICT).

## Decisión

Se documenta esta limitacion como comportamiento esperado, no como defecto: el test de efecto real de grunt (test_grunt_class_live_effect_against_real_effective_runtime_inventory) prueba supervivencia + independencia en el shape verificado, y el reordenamiento cross-provider genuino de grunt se prueba por separado en el shape unverified_review (sin identidad de writer forzada). Se agrega una oracion a docs/adr/0018-model-preference-policy.md registrando esta limitacion en la seccion 'Accepted residual risk'.

## Consecuencias

Onboarding de un tercer proveedor autenticado (p.ej. Kimi Code) removeria esta limitacion sin cambio de codigo en este contrato. Ningun test existente se debilito; la cobertura de reordenamiento genuino sigue existiendo via el shape unverified_review.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
