# Context pack — PKG-3 elegir-modelo-sin-scrollear

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-3.1–AC-3.8**. Cuarto (después de PKG-2).

**Objetivo.** Elegir entre 125 modelos sea una decisión: agrupado por proveedor, contador, valor actual marcado, búsqueda al tipear, sin parpadeo. El viewport y `/` **ya existen** — no reinventarlos.

## Paths (leídos hoy)

- `ai/scripts/tui.py:720-728` — `_viewport_slice` (clamp que contiene el cursor).
- `ai/scripts/tui.py:731-745` — `_render_items`: marker `›`, bold del cursor, **sin** encabezados de sección ni `▲`/`▼` ni `●`. Spec `:731-745` **coincide**.
- `ai/scripts/tui.py:763-821` — `_render`: search con `/` en `:797-813` (spec `:797-812` **coincide**; hint cierra en 813). Wipe total en **`:818`** `stdout.write("\x1b[H\x1b[2J")` — spec `:818` **coincide**. AC-3.7: `\x1b[H\x1b[J` o dirty-rows; test de **bytes** de que `[2J` no sale en el redibujo.
- `ai/scripts/tui.py:140-169` — `reduce` / `_reduce_navigate`: `SEARCH` (`/`) entra a search (`:167-168`); cualquier otra tecla (letra) es no-op (`return state` en `:169`). AC-3.6: una letra en `navigate` entra a search **sin** `/` primero; `/` y Esc siguen igual.
- `ai/scripts/tui.py:184-192` — `_search_matches` substring/casefold. Reusar.
- `ai/scripts/setup_models.py:331-341` — `choose()` → `tui.run_picker(options, freetext_allowed=True)`. Lista plana de `available_opencode_models` (`:303-317`). Acá se arma agrupado + valor actual + sufijos `dim()`.
- `ai/scripts/setup_models.py:378` — picker "Campo" (lanes). **PKG-1**; no reordenar campos acá.
- Tests: `tests/test_harness.py` `TuiTests` (`:12422`) — reductor puro, streams falsos. `tests/test_menu_ui.py` — menú principal, no el picker de modelos (no romper contrato). `tests/test_models_wizard_ui.py` — panel del wizard.

AC-3.1 encabezados no seleccionables (`opencode-go (19)`, …); flechas los saltan. AC-3.2 `n de total` / filtro. AC-3.3 `▲`/`▼`. AC-3.4 `●` + cursor sobre el valor actual, no índice 0. AC-3.5 sufijos `dim()`: `-free`, `← implementer`. AC-3.8: cero dependencia de TTY real.

## ADRs / invariantes

- Contrato TUI 005/P3: reductor puro (`tui.py:140-144` “Zero I/O”), `run_picker` testeable con stdin/stdout fake.
- `/` y Esc intactos (AC-3.6 / AC-3.8).
- `WIZARD_ITEMS` 0-4 inmutables (`setup_models.py:349-353`).
- ADR-0041 — heartbeat; sin pipe/tail.
- No mezclar con PKG-1 (lanes) ni PKG-2 (probe async) más de lo que el picker necesite de la lista ya cargada.

## Validación local

```
python3 -m unittest tests.test_harness.TuiTests tests.test_menu_ui tests.test_models_wizard_ui
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests
./build.sh --check
git diff --check
```

Tests nuevos (secciones, contador, `▲▼`, `●`, type-to-search, ausencia de `\x1b[2J`) en `TuiTests` o módulo vecino, **sin TTY**. `pytest` no existe.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]`. **No** `ux-ui-designer`: ese rol especifica HTML, tokens, WCAG, ARIA y escribe `ux.md` (`~/.cursor/agents/ux-ui-designer.md:22-42`). Este cambio es el reductor/render ANSI de `tui.py`, ya cubierto por `TuiTests` sin TTY (AC-3.8). Meter ux-ui-designer es over-declare de wall-clock.
- `runtime_surface`: **true** — picker observable.
- test owner: **implementer**. `strict_tdd`: **false** (reductor denso, pero la red `TuiTests` ya existe; no opt-in de ceremonia).

## Fuera de alcance

PKG-2 (congelamiento/cache) · PKG-1 (colapsar lanes) · reescribir el viewport clamp · exigir TTY · menú principal de `set_agents_app.py` salvo que un contrato de `test_menu_ui.py` se rompa (entonces arreglá el picker, no el menú).

## Excepciones recomendadas

`owned_paths` = `tui.py`, `setup_models.py`. No incluye `tests/`.

- `tests/test_harness.py` — `TuiTests` es el dueño del reductor/bytes de wipe.
- `tests/test_models_wizard_ui.py` — si `choose()` cambia la forma de las opciones.
- `tests/test_menu_ui.py` — **solo** si un contrato viejo de `/` se toca; el archivo prueba el menú, no el catálogo de modelos.

## Mordida

AC-3.7: `cp tui.py`, dejar `\x1b[2J` en `_render`, ver rojo el test de bytes, `cp` restaurar, verde. Igual para type-to-search (volver `:169` a ignore-CHAR). Nunca `git checkout`/`restore`/`stash`.
