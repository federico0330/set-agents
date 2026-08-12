# Context pack — P2-billing-aware-ordering (ADR-0035)

Spec: `docs/specs/019-harness-evolution/spec.md`, AC-12..AC-16. Leé también la sección
**Medición en vivo** (M-1..M-4) y `docs/adr/0034-auto-adopted-providers.md`, que P1 acaba de
escribir: este paquete se apoya en él y no lo re-litiga.

## Objetivo

Dos cosas. (a) Que a igual tier el router prefiera **suscripción o modelo free** sobre **metered**,
de modo que `opencode-zen` (el único metered) entre exactamente cuando aporta algo que los otros no
tienen: es el único que satisface el tier, o el único que da independencia de reviewer. (b) Que la
consola deje de mentir sobre el inventario: un `--route-doctor` que diagnostica de verdad, y un panel
y wizard que declaran la política nueva.

## Lo primero que hacés (defecto vivo, ya registrado)

`ai/scripts/setup_models.py:156` y `:364` hacen `list(routing.get("discovered_providers", []))`.
Con el nuevo default `"auto"` que dejó P1, eso da `['a','u','t','o']`. Reproducido en vivo hoy: el
panel imprime `proveedores descubiertos rutables: a, u, t, o`. Está registrado en
`ai/state/decisions-log.jsonl` y **es tuyo**. Reproducilo antes de arreglarlo (así):

```bash
python3 -c "
import sys;sys.path.insert(0,'ai/scripts')
import models_config, setup_models
c=models_config.load_config('models.toml'); r=models_config.load_roster('roles.tsv')
print([l for l in setup_models._panel_lines(c,r,'go-zen') if 'descubiertos' in l])"
```

`"auto"` no es una lista: es una **política**. Todo consumidor tiene que resolverla contra el
inventario vivo (`catalog.resolve_discovered_providers`, la función única que dejó P1) o tratarla
como el string que es, nunca iterarla como secuencia.

## Deuda heredada que también es tuya (F-02 de la review de P1)

`models.toml:26-27` — las listas `[catalog].opencode_zen` y `opencode_go` fueron medidas el
**2026-07-30** y están desactualizadas. Como `_configured_models` (`catalog.py:157`) intersecta contra
ese techo, `"auto"` **no puede routear** un modelo vivo ausente de la lista. Diferencias conocidas:
faltan `ling-3.0-tiny-free`, `longcat-2.0-free`, `mimo-v2.5-free`, `qwen3.5-plus`; sobran (muertos,
inofensivos) `claude-opus-4-1`, `ling-3.0-flash-free`; `opencode-go` lista 16 ids contra 18 vivos.

`models.toml` **no** estaba en tus owned_paths: tenés una **excepción de ownership aprobada**
registrada en el state file para exactamente este refresh. Re-medí en vivo antes de escribir
(`opencode models opencode --pure` y `opencode models opencode-go --pure`) y dejá la fecha nueva en el
comentario que ya está ahí. La intersección se mantiene: es el techo auditado, no lo elimines.

## Archivos y qué hacer en cada uno

### AC-12 — `ai/scripts/routing_core/catalog.py:169`

`PROVIDER_BILLING_KIND = {"opencode-zen": "metered", "opencode-go": "subscription"}` — completalo:
`subscription` para `openai-codex`, `anthropic`, `opencode-go`; `metered` para `opencode-zen`. El
comentario que lo precede dice "no weighting/selection logic reads this map yet (008-P3's
territory)": ese día llegó, actualizalo citando ADR-0035.

`billing_rank(provider, model) -> int` **función pura**, en `catalog.py` junto al mapa o en
`domain.py`: `0` si el provider es `subscription` **o** el modelo es free, `1` si es `metered` o
desconocido. La convención de "free" es el sufijo `-free`, que `inference.py:41` (`_FAST_HINTS`) ya
usa; no inventes otra. Un provider ausente del mapa rankea `1` (fail-closed hacia lo caro: no
premiamos lo que no conocemos).

### AC-13 — `ai/scripts/routing_core/service.py:375`

La tupla actual, que ADR-0034 documenta explícitamente y un test tripwire pinea:

```
(same_provider_as_writer, pin_rank, TIER_ORDER, _bias_rank, is_inferred, curated_priority, route_id)
```

Insertá `billing_rank` **tras `TIER_ORDER` y antes de `_bias_rank`**, quedando:

```
(same_provider_as_writer, pin_rank, TIER_ORDER, billing_rank, _bias_rank, is_inferred, curated_priority, route_id)
```

Actualizá el comentario que enumera la tupla (`service.py:372-374`) y el test tripwire. **No toqués
el bucle de exclusiones**: las exclusiones duras no cambian, y eso es justamente lo que hace que zen
entre solo cuando aporta. Los dos tests que AC-13 exige son exactamente esos dos casos:

1. zen es el **único** que satisface el tier requerido ⇒ se elige, aunque sea metered.
2. zen es el **único** que da independencia de reviewer (todo lo demás excluido por
   `REVIEW_*_CONFLICT`) ⇒ se elige.
   Y el caso de control: a igual tier con una alternativa de suscripción disponible ⇒ **no** se elige.

### AC-14 — reason code aditivo

Estilo `MODEL_METADATA_INFERRED` / `REPROBE_REJECTED` (ambos ya en esa función): un código que deje el
rank observable en `decisions-v1.jsonl`. Aditivo puro: nunca reemplaza ni reordena códigos, nunca
cambia `success`/`runtime`/`identity`/`fallback`.

### AC-15 — `set-agents --route-doctor`

Nuevo flag en `ai/scripts/set_agents_app.py`. Precedente estructural: `cmd_routing_report`
(`:477`) y `cmd_route_decide` (`:494`) — mismo envelope de una línea JSON (`routing.cli_envelope`),
mismo `_routing_output(..., human)`, mismo manejo de flags de modo (`:2587` `_mode_flags` y
`:2501-2506` los `add_argument`). Corre con probes frescos y reporta **por par**: autenticado sí/no,
cuántos modelos lista, billing kind, y el diagnóstico del cache (key vigente, edad, si está siendo
usado o invalidado y por qué). Tiene que hacer visible el caso M-1: **`github-copilot` autenticado
pero sin modelos listables** — ese es justamente el caso que el usuario no puede diagnosticar hoy.

Ojo: `--route-doctor` es read-only y no autoriza nada; no debe abrir runs ni escribir en la store.

### AC-16 — panel y wizard, `ai/scripts/setup_models.py`

- `_panel_lines:139-190`: la línea de descubiertos pasa a mostrar **`auto → <lista viva>` con su
  billing** (p. ej. `opencode-zen (metered), opencode-go (suscripción)`), resolviendo la política en
  vez de iterar el string. Cuando el valor es una lista explícita, se muestra como tal.
- El rótulo `"DEFAULTS CURADOS (fallback cuando el lane no aplica la decisión):"` (`:177`) y la línea
  de política (`:171-176`) se reescriben citando **ADR-0034/0035**. Cuidado: `tests/test_menu_ui.py`
  y `tests/test_models_wizard_ui.py` pinean marcadores de estos textos por grep — cambialos en
  lockstep y decí en la evidencia qué marcador movió cada uno y por qué.
- Wizard opción 7 (`:362-379`): hoy togglea dos providers de una tupla hardcodeada. Pasa a ofrecer
  **`auto (recomendado) / lista manual / ninguno`**. En "lista manual" seguís ofreciendo el toggle,
  pero derivá los candidatos del set auditado, no de la tupla literal.

## Read-only (NO editar)

`ai/catalogs/routes.v1.toml`, `models_config.ROUTING_PROVIDERS`, `[routing].enabled_providers`,
`ai/scripts/routing_core/store.py`, `ai/scripts/opencode_spawn.py`, y todo lo de P3/P4/P5
(`docs/modules/`, `Global/_canonical/`, `tools.toml`, `coord_policy.py`).

Excepción explícita y única: `models.toml`, solo para el refresh de `[catalog].opencode_zen` y
`opencode_go` descrito arriba.

## Restricciones

- **ADR-0035 primero, después test, después código.** Re-verificá con `ls docs/adr/` que `0035` esté
  libre justo antes de crearlo, e indexalo en `docs/adr/README.md` con el formato de las filas
  existentes.
- Las exclusiones duras no se tocan. El costo es un criterio de **orden**, nunca de elegibilidad: si
  zen es lo único que sirve, zen se usa. Escribí eso explícitamente en el ADR.
- No debilites ninguna aserción de regresión. `tests/test_routing.py`, `tests/test_harness.py`,
  `tests/test_menu_ui.py` y `tests/test_models_wizard_ui.py` son contrato.
- Sin techo de gasto mensual ni presupuesto por provider: DEC-2 de la spec lo deja fuera.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` no está instalado**; la suite tarda ~7 min y hoy
son 819 tests OK con 3 skips preexistentes — el conteo sube, nunca baja) · `./ai/scripts/verify.sh` →
`VERIFY_PASS` · `./build.sh --check` sin drift · `git diff --check` limpio ·
`check-owned-paths.py` sobre tu diff.

Pruebas vivas que van como evidencia:

```bash
./set-agents --route-doctor
python3 -c "
import sys;sys.path.insert(0,'ai/scripts')
import models_config, setup_models
c=models_config.load_config('models.toml'); r=models_config.load_roster('roles.tsv')
print('\n'.join(setup_models._panel_lines(c,r,'go-zen')))"
echo '{"role":"implementer","task_class":"implementation","risk":"low","selected_runtime":"opencode"}' | ./set-agents --route-decide - --fresh-probes
./set-agents --routing-decisions --limit 5
```

## Evidencia esperada

`docs/specs/019-harness-evolution/evidence/P2-implementer.md`: tabla AC → cambio (`archivo:línea`) →
prueba; enumeración test por test de cada aserción de contrato modificada, con ADR-0035 como fuente;
la tupla final del sort key escrita explícitamente; la salida real de `--route-doctor` y del panel; el
antes/después del refresh de `models.toml` con la fecha de medición. Lo que no puedas verificar,
marcalo "sin verificar".

## Checkpoint

Si te acercás al límite de ejecución, escribí primero el progreso parcial y los próximos pasos
exactos en el archivo de evidencia, y recién ahí pará.

## Fuera de alcance

Techos de gasto · `docs/modules/` y la capa cognitiva (P3) · narración, question policy y `/explicar`
(P4) · tools discovery (P5) · ampliar `enabled_providers`/`routes.v1.toml`/`ROUTING_PROVIDERS` ·
agregar pares para `github-copilot` (M-1: solo se **reporta** en `--route-doctor`, no se adopta).
