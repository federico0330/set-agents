# Context pack — P1-dispatch-core (feature 004, contract 1.1.0)

Objetivo: hacer consumible el cerebro de ruteo (003/P1R aceptado) — catálogo por niveles, selección
sensible al riesgo y CLI de despacho — sin romper ningún invariante de la 003 salvo las dos enmiendas
aprobadas AM-1/AM-2 (ver spec.md §"Approved contract amendments").

## Leé primero
- `docs/specs/004-adaptive-dispatch/spec.md` (contrato; secciones Tier model, AC-00..AC-05)
- `docs/specs/004-adaptive-dispatch/acceptance.md` (P1 scenarios)
- `docs/adr/0005-trusted-routing-sqlite-lifecycle.md` (incl. enmienda R3)
- Código base: `ai/scripts/routing_core/{domain,service,store,catalog}.py`, `ai/scripts/routing.py`,
  `ai/scripts/set_agents_app.py` (zonas routing: ~32-120, ~1040-1075), `tests/test_routing.py` (19 tests)

## Mapa de cambios por tarea
- **T-100** ADR-0006 (`docs/adr/0006-adaptive-dispatch-cache-and-facts.md`): mecánica AM-1 (derivación por
  campo, risk raise-only) y AM-2 (cache filtering-only: root = root del store routing-v2, clave =
  uid+digest(models.toml [catalog]+[routing])+par, TTL 300s, tmp+rename 0600, corrupto⇒ignorar,
  fresh-selected re-probe antes de autorizar writer).
- **T-101** `ai/catalogs/routes.v1.toml`: catalog_version=2; 6 filas (2 proveedores × 3 tiers):
  openai-codex fast=gpt-5.6-luna/low, balanced=gpt-5.6-sol/medium, frontier=gpt-5.6-terra/high;
  anthropic fast=haiku, balanced=sonnet, frontier=opus (effort medium). `tier` escalar único (el binding
  canónico lo codifica como grupo de UN elemento — la forma de la tupla de la 003 no cambia). Validación
  en `build_snapshot`: version==2, tier ∈ enum, effort ∈ [catalog].codex_effort para openai (xhigh
  rechazado mientras xhigh_benchmarked=false), effort=="medium" para anthropic, clave opcional
  `runtimes` allowlisted (fuera de la tupla del ID; duplicados que solo difieren en runtimes =
  CATALOG_INVALID).
- **T-102** `domain.py`: `TIER_ORDER`, `required_tier(task_class, risk)` (CRITICAL o high⇒frontier;
  mechanical/documentation/inspection + low⇒fast; resto balanced). `service.py`: exclusión
  `TIER_INSUFFICIENT` para tier < requerido; orden (pref-proveedor-reviewer, tier asc, priority,
  route_id). Matriz unit (task_class × risk) completa.
- **T-103** `store.py`: SCHEMA=4, estado `abandoned` (terminal, sin identidad actual, window 0, nunca
  review identity; CHECKs ajustados), `abandon(run_id)` desde authorized, `open_runs()`,
  `recent_writers()`. `set_agents_app.py`: `--route-decide` (descriptor JSON: role, task_class, risk
  raise-only, review_of_run_id, selected_runtime, feature_id/package_id→context flags desde el
  context_pack del paquete activo; sin paquete ⇒ flags false), `--route-dispatched`, `--route-terminal`
  (incl. authorized→abandoned solo failure), `--routing-open-runs`, `--routing-recent-writers`;
  exempt-set por modo (--json global; --fresh-probes con decide; --latency-ms con terminal); reason codes
  nuevos allowlisted (REVIEW_IDENTITY_UNVERIFIED con ok=true/exit 0); clase review sin run_id ⇒ decisión
  NO ejecutable con tier/model (nunca spawn ruteado); busy ⇒ ROUTING_UNAVAILABLE exit 1 sin retry.
- **T-104** `catalog.py`: cache según ADR-0006 (`probe_inventory(config, cache_root=..., ttl=300,
  fresh=False, pairs=None)`); `service.py`: `_reprobe(pairs)` fresco del par seleccionado (+fallback si
  difiere) ANTES de `_authorize_issued`; fallo ⇒ PROVIDER_UNAUTHENTICATED. `routing.compose` wirea
  cache_root al root del store. Explain reusa el cache.
- **T-105** N-1 (elementos de required_tools no-str ⇒ FACTS_INCOMPLETE), N-2 (`_compose_for_tests` exige
  root explícito cuando no simula), N-4 (verify.sh py_compile suma routing_core/*.py), suite: matriz
  tier, cache (sentinel PATH, TTL, digest, corrupto, bytes), abandoned, open-runs/recent-writers, CLI
  decide writer/review/docs-rw, concurrencia decide, wall-time informativo.

## Invariantes que NO se tocan
Facts single-use e in-process; fail-closed byte-idéntico; permit/nonce de composición; independencia de
reviewer (con run_id verificado); redacción de envelopes; sin migración de DBs viejas (schema 2 y 3
quedan ROUTING_UNAVAILABLE; wipe del operador documentado).

## Gates del paquete
`python3 -m unittest discover -s tests -p 'test_routing.py'`; 2 regresiones HarnessTests nombradas;
`setup_models.py --check`; py_compile (incl. routing_core/*); GateSpecs (v2:python-compile,
v2:routing-unit, v2:harness-verify); `./ai/scripts/verify.sh` ≥120s; CLI exits; `git diff --check`;
ownership contra baseline del paquete.
