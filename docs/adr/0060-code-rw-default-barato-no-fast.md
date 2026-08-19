# ADR-0060 — Default `code-rw` = barato/free que cumple tools, no sufijo `-fast`

- Estado: **Accepted** (2026-08-19). Feature `034-cuota-organica-y-writer-barato`, PKG-B.
  Aprobado con el Feature Contract (hash `539a4ff6b58b9ca67df9342dddcc79783660dcac73ce987a5da58ce136bd9721`).
- Enmienda ADR-0044 **en parte**: la razón del loop hot-path (`implementer` /
  `product-analyst` deben terminar en `-fast`) deja de valer. El resto de 0044
  (orchestrator fuera de `-fast`, `[areas.coord]` grok de suscripción, límite
  honesto de la lane `codex`, `model_request` efímero P2) sigue vigente.
- No mueve `billing_rank` en el sort key (ADR-0035). No es un segundo decision-maker
  (ADR-0018).

## Contexto

ADR-0044 midió que el sufijo `-fast` **solo existe** en el proveedor `openai` de
OpenCode y que el test
`test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`
(`tests/test_harness.py:733-749`) no medía latencia: medía “tiene que ser OpenAI”.
Sacó a `orchestrator` de ese loop y **conservó** la regla para `implementer` y
`product-analyst` como “camino caliente de dispatch”.

034 cambia la razón de negocio de ese camino caliente: Federico paga suscripciones
y el harness las gasta en el volumen del escritor. El default de todo rol
`capability == code-rw` (`roles.tsv:12-17`) pasa a ser lo más barato/gratis del
catálogo vivo que **todavía pueda editar y correr validación local**. `product-analyst`
no es escritor (`roles.tsv:4`, `docs-rw`/`docs`, clase `decision` ADR-0018) — DEC-ANALYST.

Hoy la celda estática es `[areas.implement].opencode = "openai/gpt-5.6-fast"`
(`models.toml:109-113`). `billing_rank` (`catalog.py:196-207`) ya premia
subscription/`-free` **dentro del sort**, no como default del rol. Un ranking de
precios USD no existe en el árbol y no se va a inventar (ADR-0026: sin fuente).

## Decisión

1. **“Barato” se define reusando `billing_rank` + el piso de tools, no un
   decision-maker nuevo.** Un candidato es elegible como default estático si
   sobrevive el piso de writer `("read", "shell", "write")` (`set_agents_app.py:731`,
   exclusión `TOOLS_MISSING` `service.py:368`) y tiene `billing_rank(provider, model) == 0`.
   Si no hay ninguno: `HUMAN_DECISION_REQUIRED` con el inventario medido — no un id
   inventado. Entre varios 0, se usa la convención **ya escrita** en
   `billing_rank` (`catalog.py:190-192`): el sufijo `-free` es FREE; subscription es
   el otro camino a 0 — preferir `-free` sobre “solo subscription”. Empate restante:
   `curated_priority` / `route_id`. Cero list prices USD. **El sort key de
   `route()` no gana ningún elemento y `billing_rank` no se mueve.**

2. **La celda que cambia es `[areas.implement].opencode`**, la que `load_roles`
   resuelve y la que el test hot-path lee. Los `code-rw` sin tabla `tiers`
   heredan. Se **borran** los overrides que contradicen el default de área:
   `[roles.frontend-engineer].opencode` spark (`models.toml:237-238`) y
   `[roles.refactor-specialist].opencode` spark (`models.toml:271-273`).

3. **`product-analyst` sale del loop `-fast`.** Puede resolver frontier. Ningún
   test lo obliga a `-fast` ni a `-free`.

4. **El test se reescribe, no se borra** (mismo patrón que 0044 usó con
   `orchestrator`): comentario con la razón nueva; `implementer` + al menos un
   segundo `code-rw` asertan barato/free-primero; mitad independencia
   `tests/test_harness.py:750-766` conservada. Mordida RED→GREEN.

5. **Límite honesto — variantes `@tier` y promoción.** `check_variant_catalog_coherence`
   (`generate.py:689-711`) exige proyección a exactamente una fila de
   `routes.v1.toml`. `_opencode_projected_route` (`generate.py:667-677`) solo
   proyecta `openai/<M>`. Un `-free` `opencode/*` **no** entra en
   `[roles.implementer.tiers.*]` ni se relaja la coherencia. Las variantes
   `<role>@<tier>` son **OpenCode-only** (`generate.py:581-585`): Cursor, Claude
   y Codex no reciben `implementer@fast.md`. El default barato/free aterriza
   en la celda **BASE** + pin Cursor (ADR-0063), no en `@fast`. Feature nueva
   = rung `"base"` — **nunca** `"fast"` (`MODEL_TIERS[0]`, `models_config.py:45`).
   Auto-promotion (DEC-PROMOTE, ADR-0061) sube `"base"` → `"balanced"` →
   `"frontier"`: en OpenCode eso son las variantes `@balanced`/`@frontier` de
   la escalera curada; en Cursor es override de invocación (V-D03), no un
   `@tier` generado. 034 no abre el catálogo curado a zen.

## Opciones rechazadas

- **Insertar un `cheapness_rank` (o un tercer valor de `billing_rank`) en el
  sort key de `route()`.** Violaría el invariante de 034 / ADR-0035: `billing_rank`
  no se mueve. El default estático no es selección dinámica.
- **Scrapear precios USD o mantener una tabla de list prices.** Sin fuente
  durable (ADR-0026); se stalea el día que el proveedor cambia el cartel.
- **Borrar el test `-fast` en vez de reescribirlo.** Perdería la mordida y la
  mitad de independencia. 0044 ya rechazó este movimiento para `orchestrator`.
- **Poner el `-free` en `tiers.fast` relajando `check_variant_catalog_coherence`
  o proyectando `opencode/*` a `routes.v1.toml`.** Abriría el catálogo curado
  (fuera de alcance) o aflojaría un gate de build que 004/015/033 necesitan.
- **Tratar a `product-analyst` como escritor barato.** DEC-ANALYST: es juicio
  de producto, clase `decision`. Meterlo al loop free repetiría el error de
  alcance que 0044 corrigió para `orchestrator`, en la dirección opuesta.
- **Tratar `MODEL_TIERS[0] == "fast"` como el rung barato de una feature nueva.**
  `"fast"` nombra `implementer@fast` (luna), que Cursor **no tiene**
  (`generate.py:581-585`). El rung 034 es `"base"` (celda AREA / pin Cursor).
- **Dejar los overrides spark de frontend-engineer / refactor-specialist.**
  DEC-ROLES-BARATO es un default de área, no un spark por rol. Un override que
  no es el barato medido contradice AC-B.1.

## Consecuencias

- El test hot-path deja de anclar OpenAI-por-sufijo. Sigue anclando “el
  escritor arranca barato/free y el reviewer no comparte familia”.
- Cursor (anfitrión de 034) pinnea ese default (ADR-0063). OpenCode `@fast`
  ruteado no se vuelve `-free` en este feature — límite nombrado, no un descuido.
  Una feature nueva no arranca en `@fast`; arranca en BASE.
- Candidato en árbol `opencode/deepseek-v4-flash-free` (`models.toml:250`):
  **UNVERIFIED** tools de implementer. T-B01 / V-B01 lo miden antes de pinnear.
- `local-gate-runner` no es `code-rw`; su `-free` es precedente de id, no el
  default del escritor.

## Evidencia

`docs/specs/034-cuota-organica-y-writer-barato/design.md` §1.
`docs/specs/034-cuota-organica-y-writer-barato/spec.md` AC-B.1–B.3, B.7.
`tests/test_harness.py:733-766`, `models.toml:109-113`, `catalog.py:196-207`,
`generate.py:581-585`, `models_config.py:45`.
