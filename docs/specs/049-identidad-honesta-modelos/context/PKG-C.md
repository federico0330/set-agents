# PKG-C — Consola cache-first y wizard de convergencia

## Objetivo

Usar `ModelState` en home simple inmediato y en Modelos para distinguir sesión, default SET,
instalación y routing. Aplicar preferencias sólo bajo lock y confirmar por readback; plugins
son warnings estrictamente read-only.

## Baseline y coordinación

- Baseline `dad5987722d9254b7ebb8c6dc9bdd49a678be357` y suciedad 045–048 ajenos. No reverts,
  limpieza ni reformateo masivo.
- `ai/scripts/set_agents_app.py` es shared con PKG-B, que lo modifica primero para CLI:
  releer su diff y preservar `--model-state`.
- Depende de PKG-A y PKG-B. No reimplementar proyección/observador/schema/CLI ni tocar
  `Global/**`, `models.toml` o una sesión `/model`.

## Checkpoint post-repair: auditoría de repair ceiling

- Evidencia leída en state revision **159**: la reparación consolidada cerró los 18 findings
  de RP-01 y registró 55/55 focales, `py_compile` y `git diff --check` PASS. Sus únicos paths
  declarados son `ai/scripts/set_agents_app.py`, `ai/scripts/setup_models.py`,
  `tests/test_console_model_state_049.py`, `tests/test_model_apply_049.py`,
  `tests/test_models_wizard_ui.py` y `tests/test_menu_ui.py`.
- El gate obligatorio `repair-ceiling` falló, sin waiver: baseline congelada
  `ce6e17ba3e51c8fb860b553db072d3f3b0b1f02d`, `budget_lines=0`,
  `changed_lines=3827`, exit 2. La autorización humana permite **auditar y reconstruir la
  evidencia de causa/base**, no dispensar, borrar, regrabar ni declarar PASS el gate.
- La función madre de esta medición es `main()` en
  `ai/scripts/check-repair-ceiling.py:48`: toma por defecto `candidate_identity.candidate_tree`
  y mide `git diff --numstat <baseline> --`. El freeze que produjo cero está en
  `cmd_record_repair()` (`ai/scripts/feature_state_lib/cli_repair.py:196`, ceiling en :211–224).
  La investigación debe explicar esa divergencia, no alterar esos mecanismos.
- Leer primero, sin escribir: `ai/state/features/049-identidad-honesta-modelos.json`,
  `ai/scripts/check-repair-ceiling.py`, `ai/scripts/feature_state_lib/cli_repair.py`,
  `tests/test_repair_ceiling.py` y `docs/adr/0023-bounded-repair-ceiling.md`.

```bash
git status --porcelain=v1
git show -s --format='%H%n%ci%n%s' ce6e17ba3e51c8fb860b553db072d3f3b0b1f02d
git diff --numstat ce6e17ba3e51c8fb860b553db072d3f3b0b1f02d --
git diff --name-status ce6e17ba3e51c8fb860b553db072d3f3b0b1f02d --
git diff --numstat ce6e17ba3e51c8fb860b553db072d3f3b0b1f02d -- ai/scripts/set_agents_app.py ai/scripts/setup_models.py tests/test_console_model_state_049.py tests/test_model_apply_049.py tests/test_models_wizard_ui.py tests/test_menu_ui.py
python3 ai/scripts/check-repair-ceiling.py --state-file ai/state/features/049-identidad-honesta-modelos.json --package-id PKG-C
```

- El árbol sigue sucio por 045–048 y por trabajo concurrente. No ejecutar reset/checkout,
  no atribuir el diff global a PKG-C, no editar código/tests/state/context ajeno, y no cambiar
  baseline, `budget_lines`, candidate identity ni el resultado del gate. El único resultado
  autorizado de este checkpoint es una explicación verificable de la base y del alcance.

## Archivos y puntos de entrada

| Path | Por qué |
| --- | --- |
| `ai/scripts/set_agents_app.py` | `menu()` (4002) y `run_tty()` (3611): primer frame, refresh y etiqueta/rc real. Shared. |
| `ai/scripts/setup_models.py` | `_edit_overlay_cell()` (577), `write_overlay_cell()` (554): wizard, lock, apply/readback. |
| `ai/scripts/onboarding.py` | Sólo si aislarlo evita evaluar/forzar `first_run` en ingreso 049. |
| `tests/test_console_model_state_049.py` | Primer frame, degradación, acciones y errores. |
| `tests/test_model_apply_049.py` | Lock, `pending_apply`, router-auto/restore. |

## Trabajo

1. Home simple cache/ausencia <300 ms y cero subprocesses: Estado, Configurar, Modelos,
   Forma de trabajo, Modo experto y Salir; experto entra directo.
2. Mover medición/probes/drift a `Actualizar estado`; conservar valor válido stale ante fallo
   y mensaje reintentable, sin traceback.
3. Panel Modelos desde `ModelState`, fuente por evidencia y explicación de `/model` temporal.
4. Lock exclusivo: validar → persistir → generar efectiva → instalar destino → releer. Segundo
   writer falla antes de mutar; fallo de instalación/readback deja intent y `pending_apply`.
5. Router-auto borra sólo `[model_pin]`; restore sólo overrides locales y conserva
   hosts/subscriptions byte-idénticos. Plugin/model label: warning read-only, jamás backup o cambio.

## Contratos e invariantes

- AC-05..AC-08 y ADR-0076: readback exacto es único éxito; cache/child fallido nunca
  traceback ni falso "listo".
- ADR-0075 conserva renderer, paleta y jerarquía; Modo experto no es onboarding.
- No ofrecer deshabilitar/editar/borrar/respaldar plugins. `gentle-logo.tsx` externo sigue
  sin verificar.

## Riesgo, revisión y validación

Complejidad media: UI TTY y lock de preferencias locales. State registra panel base
`package-reviewer`, `security-auditor`; antes de abrirlo, el coordinador extiende con
`ux-ui-designer` por primer frame, jerarquía y error UX. Test owner implementer; strict TDD off.

```bash
python3 -m unittest -v tests.test_console_model_state_049 tests.test_model_apply_049
python3 -m unittest -v tests.test_menu_ui tests.test_models_wizard_first_paint tests.test_models_wizard_ui
git diff --check
```

Usar TTY/subprocesses falsos y state/HOME temporales, nunca apply real.

## Hecho cuando

Primer frame no mide ni lanza hijos; refresh recupera; wizard muestra cuatro evidencias sin
"modelo actual"; auto/restore y lock tienen universos disjuntos.
