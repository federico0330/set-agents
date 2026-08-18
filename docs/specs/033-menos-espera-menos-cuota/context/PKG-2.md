# Context pack — PKG-2 el-menu-no-congela

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-2.1–AC-2.5**. Tercero (después de PKG-4 y PKG-5).

**Objetivo.** El wizard "Modelos" pinta algo útil en **< 300 ms** siempre: primer frame con disco; suscripciones y catálogo vivo llegan después y refrescan in-place; degradación **con nombre** si el probe falla.

## Paths (leídos hoy)

- `ai/scripts/setup_models.py:344-366` — `wizard()`: **antes** del `while True` hace `detect_subscriptions(config)` en `:357` dentro de `try/except Exception` mudo (`:356-359`, `except` en `:358`). Ese es el congelamiento de ~13 s. Spec `:356-359` **coincide** (try 356 / call 357 / except 358).
- `ai/scripts/models_config.py:377-392` — definición de `detect_subscriptions` (probe `routing_core.catalog.probe_inventory`). El spec atribuyó los 13.12 s a `setup_models.py:357`: es el **call site**, no la def.
- `ai/scripts/setup_models.py:229-287` — `_panel_lines`: header `lane: {profile} (auto)` (`:230`) y columna `OPENCODE[{profile}]` (`:275`). PKG-2 **no** saca el eje lane (eso es PKG-1); sí puede mostrar antigüedad del cache (`suscripciones: hace 4 min`).
- `ai/scripts/setup_models.py:303-317` — `available_opencode_models`: `subprocess.run(["opencode","models"], timeout=20)` síncrono, ~2.9 s / 125 ids. Fuera del camino crítico del primer paint.
- `ai/scripts/tui.py:577-641` — `with_progress` ya existe: delay 0.3 s (`:574`), stderr nunca stdout, línea persistente `final=` / `"<msg>: listo"`. **Reutilizar, no reescribir.**
- `ai/scripts/set_agents_app.py:3845` — uso de referencia en el menú principal (`with_progress("chequeando actualizaciones", …)`). Spec `:3845` **coincide**. Solo lectura.
- Tests a extender: `tests/test_models_wizard_ui.py` (panel compacto, tri-estado; config de fixture aún con mapa de lanes `:23-24`); `tests/test_probe_subscriptions.py`; `tests/test_harness.py` clase `TuiTests` (`:12422`) ya cubre `with_progress` (`:13348+`).

AC-2.1: dibujar el picker **antes** del probe. AC-2.2: `tui.with_progress` mientras vuela. AC-2.3: cache en disco con TTL (arrancar 10 min subs / 60 min catálogo) + sello + tecla de refresco. AC-2.4: reemplazar el `except Exception` mudo por degradación visible (`suscripciones: no se pudo medir — mostrando pins`). AC-2.5: test que congela el probe 5 s y demuestra primer frame < 300 ms.

## ADRs / invariantes

- ADR-0029 / ADR-0048 — tri-estado de suscripciones; `detect_subscriptions` sigue existiendo para el panel (AC-1.2 de PKG-1 lo conserva; acá no lo borres).
- `wizard()` índices 0-4 de `WIZARD_ITEMS` (`setup_models.py:349-353`) son contrato inmutable de la suite. Acciones nuevas **al final**.
- ADR-0041 — heartbeat para comandos largos; sin pipe/tail.
- AC-3.8 (PKG-3) — TUI testeable sin TTY; este paquete tampoco puede exigir terminal real.

## Validación local

```
python3 -m unittest tests.test_models_wizard_ui tests.test_probe_subscriptions
python3 -m unittest tests.test_harness.TuiTests.test_with_progress_without_a_tty_writes_not_one_byte_to_stdout tests.test_harness.TuiTests.test_with_progress_no_color_in_a_pipe_degrades_but_still_reports
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.TuiTests
./build.sh --check
git diff --check
```

Más el test nuevo AC-2.5 (probe congelado 5 s, primer frame < 300 ms). `pytest` no existe.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]`. **No** `ux-ui-designer`: el rol (`~/.cursor/agents/ux-ui-designer.md`) es frontend HTML/tokens/WCAG/ARIA/`ux.md`. Esto es consola ANSI que reusa `tui.with_progress`; no hay tokens ni HTML. Evidencia: `tui.py:577` ya es el primitive; el paquete cambia *cuándo* pinta el wizard, no el design system.
- `runtime_surface`: **true** — wizard operador, primer paint observable.
- test owner: **implementer**. `strict_tdd`: **false**.

## Fuera de alcance

PKG-3 (agrupar/contador/parpadeo) · PKG-1 (sacar `LANES`/`lane:`) · reescribir `tui.with_progress` · `set_agents_app.py` menú principal · tocar el probe de routing más allá del cache TTL del wizard.

## Excepciones recomendadas

`owned_paths` = `setup_models.py`, `models_config.py`. No incluye `tests/`.

- `tests/test_models_wizard_ui.py` — AC-2.1/2.3/2.4 viven acá.
- `tests/test_probe_subscriptions.py` — si el cache TTL se apoya en `detect_subscriptions`.
- test nuevo AC-2.5 (mismo dir `tests/`).
- **No** `tui.py` salvo seam mínimo para inyectar reloj en AC-2.5; preferir mock del probe.

## Mordida

AC-2.5: `cp` de `setup_models.py`, volver a poner el probe síncrono antes del primer `run_picker`, ver rojo (<300 ms falla), `cp` restaurar, verde. Nunca `git checkout`/`restore`/`stash`.
