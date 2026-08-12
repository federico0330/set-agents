# ADR-0035 — Billing-aware ordering, and a console that stops lying about the live inventory

- Estado: Accepted (2026-08-10). Feature 019 (harness-evolution), PKG-2. Extends ADR-0034
  (auto-adopted providers) — does not re-litigate it: ADR-0034 decided WHICH providers become
  routable and how the curated row wins the tie; this ADR decides in what ORDER equally-tiered
  candidates are tried, and makes the console (`--route-doctor`, the panel, the wizard) tell the
  truth about the live inventory `"auto"` now resolves to.

## Contexto

`[routing].discovered_providers` defaults to `"auto"` (ADR-0034). Two live defects surfaced the
day that default landed:

1. **The console reads `"auto"` as a list.** `ai/scripts/setup_models.py:156`/`:364` did
   `list(config.get("routing", {}).get("discovered_providers", []))` — `list("auto")` is
   `['a', 'u', 't', 'o']`. Reproduced live before this fix:

   ```
   $ python3 -c "...; print([l for l in setup_models._panel_lines(c,r,'go-zen') if 'descubiertos' in l])"
   ['proveedores descubiertos rutables: a, u, t, o']
   ```

   `"auto"` is a policy, not a sequence; every consumer must resolve it against the live
   inventory (`catalog.resolve_discovered_providers`) or treat it as the string it is.

2. **`opencode-zen` is the only metered provider in the discoverable set**
   (`{openai-codex, anthropic, opencode-go}` are subscription; `opencode-zen` is pay-per-token,
   `PROVIDER_BILLING_KIND`, 012 AC-08). At equal tier, today's sort key has no billing awareness
   at all — a metered candidate can beat a subscription one on tie-break alone
   (`curated_priority`/`route_id`), which silently grows real spend for zero benefit whenever a
   subscription route would have served the same tier.

Consequences vinculantes de esta medición (no re-litigables en este ADR):

- **DEC-2 de la spec (019)**: a igual tier gana suscripción/free; metered entra SOLO cuando es el
  único que satisface el tier requerido, o el único que da independencia de reviewer. Sin techo de
  gasto mensual — eso queda fuera de alcance (no-goal explícito).
- **M-1 (github-copilot, medido en ADR-0034)**: autenticado pero sin CLI id verificable
  (`opencode models github-copilot --pure` → `Error: Provider not found`). No es routable (ADR-0034
  ya lo decidió); lo que faltaba era que un humano pudiera VER ese estado sin leer código —
  `--route-doctor` es esa superficie.

## Decisión

1. **`PROVIDER_BILLING_KIND` se completa** (`routing_core/catalog.py`): `subscription` para
   `openai-codex`, `anthropic`, `opencode-go`; `metered` para `opencode-zen`. Deja de ser un mapa
   documentado-pero-sin-lector ("no weighting/selection logic reads this map yet") — este ADR es
   el día en que sí se lee.
2. **`billing_rank(provider, model) -> int`, función pura**: `0` si el provider es `subscription`
   **o** el modelo termina en el sufijo `-free` (la misma convención que `inference._FAST_HINTS`
   ya usa, ninguna nueva); `1` en cualquier otro caso, incluido un provider AUSENTE del mapa
   (fail-closed hacia lo caro: nunca premiamos billing que no conocemos).
3. **`billing_rank` entra en el sort key de `RoutingService.route`, tras `TIER_ORDER` y antes de
   `_bias_rank`** — nunca antes del piso de tier, nunca después de la preferencia de clase. La
   tupla final que deja esta ADR:

   ```
   (same_provider_as_writer, pin_rank, TIER_ORDER, billing_rank, _bias_rank, is_inferred,
    curated_priority, route_id)
   ```

   **El bucle de exclusiones duras NO cambia.** El costo es un criterio de orden entre candidatos
   que YA sobrevivieron identidad/auth/rol/tools/contexto/independencia — nunca un criterio de
   elegibilidad. Si `opencode-zen` es el ÚNICO candidato que satisface el tier requerido, o el
   ÚNICO que da independencia de reviewer (todo lo demás excluido por
   `REVIEW_*_CONFLICT`/`REVIEWER_INDEPENDENCE_UNAVAILABLE`), zen se elige exactamente igual que
   hoy — billing_rank solo decide entre candidatos EMPATADOS en todo lo anterior.
4. **Reason code aditivo**: cada decisión deja el billing rank observable en
   `decisions-v1.jsonl`, mismo estilo que `MODEL_METADATA_INFERRED`/`RUNTIME_REDIRECTED` —
   aditivo puro, nunca reemplaza ni reordena un código existente, nunca cambia
   `success`/`runtime`/`identity`/`fallback`.
5. **`set-agents --route-doctor`**: nuevo modo read-only (mismo envelope de una línea JSON que
   `--routing-report`/`--route-decide`), corre con probes frescos (nunca cachea, nunca escribe la
   store ni abre un run) y reporta, por par OpenCode-lane: autenticado sí/no, cuántos modelos
   lista, billing kind, y el diagnóstico del cache (key vigente contra el estado actual, edad,
   si está siendo usado o por qué fue invalidado). Además reporta cualquier credencial OpenCode
   autenticada que NO mapea a ningún CLI id auditado — hoy exactamente `github-copilot` — como
   `detected, unlistable`, haciendo M-1 diagnosticable sin leer código. No se agrega ningún par
   nuevo a `_PAIR_COMMANDS` para lograr esto: es un reporte, no una adopción.
6. **El panel de consola deja de iterar el string.** `_panel_lines` resuelve `"auto"` contra el
   inventario vivo (`resolve_discovered_providers` sobre un probe cacheado) y muestra
   `auto → <lista viva>` con el billing de cada uno (p. ej.
   `opencode-zen (metered), opencode-go (suscripción)`); un valor de lista explícita se sigue
   mostrando tal cual. El rótulo `DEFAULTS CURADOS (fallback...)` y la línea de política citan
   ahora ADR-0034/ADR-0035 en vez de solo ADR-0029/ADR-0032.
7. **El wizard (opción "Proveedores descubiertos") deja de togglear una tupla hardcodeada de dos
   providers.** Ofrece `auto (recomendado) / lista manual / ninguno`; en "lista manual" el toggle
   sigue existiendo pero sus candidatos se derivan del set auditado
   (`models_config.DISCOVERABLE_PROVIDERS`), nunca de una tupla literal — un futuro quinto
   provider auditado aparece en el wizard sin tocar `setup_models.py`.

## Alcance NO tocado por esta ADR

Sin techo de gasto mensual ni presupuesto por provider (DEC-2, no-goal explícito de la spec 019).
`enabled_providers`, `routes.v1.toml`, `ROUTING_PROVIDERS` no se amplían — la vía curada sigue
cerrada (ADR-0034, sin cambios). No se agrega ningún par para `github-copilot`: M-1 se REPORTA en
`--route-doctor`, nunca se adopta. `models.toml` no se toca por este ADR: el refresh de
`[catalog].opencode_zen`/`opencode_go` medido en vivo (60/18 ids) ya estaba al día al momento de
implementar este paquete — verificado, no re-escrito.

## Rejected alternatives

- **Un techo de gasto mensual o presupuesto por provider como parte de este ordenamiento**: DEC-2
  de la spec lo deja fuera explícitamente; billing_rank es un criterio de ORDEN, no de cuota.
- **Excluir `opencode-zen` de la elegibilidad cuando hay una alternativa de suscripción**: violaría
  el objetivo explícito del ADR — zen debe seguir siendo elegible y GANAR cuando es el único que
  satisface tier o independencia; degradarlo a inelegible en cualquier caso rompería exactamente
  el escenario que DEC-2 quiere preservar.
- **Hardcodear un CLI id para `github-copilot` para que `--route-doctor` pueda listar sus
  modelos**: violaría la misma disciplina fail-closed que ADR-0034 ya fijó — `--route-doctor`
  reporta lo que el runtime puede verificar, nunca inventa una vía no auditada.

## Evidencia

`docs/specs/019-harness-evolution/evidence/P2-implementer.md` — tabla AC→archivo:línea→prueba, la
reproducción en vivo del defecto `list("auto")`, la tupla final del sort key, la salida real de
`--route-doctor` y del panel, y la enumeración test-por-test de cada aserción reescrita en las
suites-contrato.
