# D1-superficie-humana — delta review

Checkpoint inicial: evidencia creada antes de correr gates dirigidos.

## Alcance
- Package: D1-superficie-humana
- Repair commit informado: 2f199d5; HEAD informado: 211df01
- Findings a verificar como closed: D1-F01, D1-F02, D1-F03, D1-F05, D1-F06, D1-F07, D1-F09
- D1-F04: refuted; no se reabre sin evidencia nueva.
- Full re-review: no iniciado; el repair informado no cambia arquitectura/contratos públicos sustancialmente.

## Evidencia en árbol inspeccionada
- Context pack leído: `docs/specs/025-consola-minima-y-flexible/context/D1-superficie-humana.md`.
- Repair evidence leído: `docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md`.
- Finding verification leído: `docs/specs/025-consola-minima-y-flexible/evidence/D1-verification.md`.
- `MENU_ITEMS` en `ai/scripts/set_agents_app.py:3721-3732`: 10 labels ASCII, sin emoji ni doble espacio.
- Primer arranque en `ai/scripts/set_agents_app.py:3738-3741`: texto sin emoji (`Primera vez acá...`).
- `_human_render_value` existe en `ai/scripts/set_agents_app.py:498-520` y renderiza colecciones/booleans para canal humano.
- `_INTERNAL_FLAGS` es `frozenset` en `ai/scripts/set_agents_app.py:3856-3866` con 28 flags.
- `_hidden_help()` preserva comportamiento y sólo suprime ayuda default en `ai/scripts/set_agents_app.py:3869-3874`.
- Test de menú usa regla positiva `isascii()` en `tests/test_harness.py:2672-2687`.
- Test de flags internas congela `expected_internal_flags = frozenset({...})` y lo compara con `app._INTERNAL_FLAGS` en `tests/test_harness.py:5530-5548`.
- Test de borrado silencioso verifica que cada flag interna siga registrada en argparse en `tests/test_harness.py:5577-5588`.
- Jerarquía del picker (D1-F04 refuted) permanece en `ai/scripts/tui.py:720-734`: marcador `›` y `bold()` sobre fila activa.

## Medición directa

Comando corrido:

```bash
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_menu_items_carry_no_emoji_and_single_space_layout tests.test_harness.HarnessTests.test_internal_flags_hidden_from_default_help_shown_with_avanzado tests.test_harness.HarnessTests.test_internal_flags_cannot_be_silently_deleted tests.test_harness.HarnessTests.test_route_doctor_default_is_human_text_on_stderr_json_flag_preserves_machine_envelope
```

Salida:

```text
....
----------------------------------------------------------------------
Ran 4 tests in 0.056s

OK
```

Medición adicional en Python sobre el árbol:

```text
MENU_ITEMS_COUNT 10
MENU_ITEMS_ALL_ASCII True
MENU_ITEMS_NO_DOUBLE_SPACES True
INTERNAL_FLAGS_TYPE frozenset
INTERNAL_FLAGS_COUNT 28
HUMAN_RENDER_EXISTS True
ROUTE_DECIDE_DEFAULT_VISIBLE False
ROUTE_DECIDE_ADVANCED_VISIBLE True
FIRST_RUN_TEXT_ASCII True
```

## Verificación de findings cerrados

| Finding | Estado delta | Evidencia |
|---|---|---|
| D1-F01 | closed | Los consumidores máquina del routing en doctrine/prompt usan `--json`; grep en `Global/*/agents/orchestrator*` muestra `--route-decide ... --json`, `--route-terminal ... --json`, `--routing-recent-writers --json`, `--routing-decisions --json`. El test dirigido de `--route-doctor` confirma default humano y `--json` máquina. |
| D1-F02 | closed | `_human_render_value` existe (`ai/scripts/set_agents_app.py:498-520`) y el canal humano ya no imprime `repr()` bruto de colecciones. |
| D1-F03 | closed | `_INTERNAL_FLAGS` contiene 28 flags internas como `frozenset`; help default las oculta y `--help --avanzado` las muestra, verificado por test dirigido. |
| D1-F05 | closed | Primer arranque sin emoji en `ai/scripts/set_agents_app.py:3738-3741`; medición confirmó `Primera vez acá` presente. |
| D1-F06 | closed | Test antiemoji cambió a regla positiva `all(c.isascii() for c in item)`; test dirigido OK. |
| D1-F07 | closed | Test congela `expected_internal_flags` como `frozenset` y compara contra `app._INTERNAL_FLAGS`; test dirigido OK. |
| D1-F09 | closed | Docstring actualizada a `The 'Estado general' panel` en `ai/scripts/set_agents_app.py:3653-3655`. |

## Regresiones / scope creep del repair

Se detectó un archivo backup trackeado introducido por el repair:

- `git ls-files "ai/scripts/set_agents_app.py.bak"` devolvió `ai/scripts/set_agents_app.py.bak`.
- `git log --oneline -- "ai/scripts/set_agents_app.py.bak"` devolvió `2f199d5 025/D1 superficie-humana, esta vez de verdad (ADR-0050)`.
- `git show --stat 2f199d5` muestra `ai/scripts/set_agents_app.py.bak | 11985 +++++++++++++++++++`.

Esto es una regresión de higiene/scope: deja un backup grande y duplicado bajo tracking. No reabre los siete findings cerrados y no es high/critical; se reporta como finding nuevo low.

## Requires full review

`false`: el repair verificado no cambió arquitectura, contratos públicos ni superficie de riesgo de forma sustancial. La revisión se mantuvo enfocada en los findings cerrados y la delta asociada.

## Veredicto

`pass`: los siete findings cerrados están resueltos en el árbol y los tests dirigidos pasan. Hay un finding nuevo low de higiene/scope por `ai/scripts/set_agents_app.py.bak` trackeado.
