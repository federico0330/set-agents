# 005-portable-harness — evidencia de integración (2026-07-30)

## Paquetes integrados

Los 3 paquetes de 005 están `accepted` e `integrated: true`:

- **P1-portable-core** (AC-00..AC-09) — `diff_ref: "HEAD"` (literal, no un sha real — ver nota de
  honestidad abajo).
- **P2-vault-mandatory** (AC-10..AC-21) — `diff_ref: 898c539669b840e5b5d78a97f484b9abef0df9a6`.
- **P3-tui** (AC-22..AC-30) — `diff_ref: 898c539669b840e5b5d78a97f484b9abef0df9a6`.

## Costuras revisadas entre paquetes

- **P1 ↔ P2**: `ai/scripts/set_agents_spawn.py` (propiedad de P1, ampliada por autorización explícita del
  usuario para propagar `PROJECT_ROOT`/cwd al lifecycle Pi) es leído sin conflicto por el flujo de vault de
  P2 — P2 no toca ese archivo, solo `set_agents_app.py`.
- **P2 ↔ P3**: el menú TUI nuevo (`ai/scripts/tui.py`, P3) reemplaza los 5 menús viejos de
  `set_agents_app.py`, incluyendo `cmd_tools_install` (que ahora envuelve su `input()` con
  `tui.suspend_terminal()`) y los flujos de vault de P2 (`vault_menu()`), migrados a `tui.run_picker`
  preservando el fallback de texto libre. Sin regresión: los tests de P2 sobre vault (symlink, doctor,
  exclude-notes) siguen verdes con el adaptador nuevo.
- **P1 ↔ P3**: `setup_models.py` (tocado por P1 para portabilidad) también migró su `choose()`/`wizard()` a
  `tui.run_picker` en P3, sin cambiar el contrato de `_safe_input()` que P1 ya había establecido.

Sin hallazgos cruzados nuevos — cada costura ya estaba cubierta por los tests de regresión de su propio
paquete, y la suite completa (457 tests) los ejercita juntos en cada corrida.

## Gates

- `./ai/scripts/verify.sh` → **`VERIFY_PASS`** (457 tests, 0 skips, `GLOBAL_PORTABILITY_OK`,
  `CANONICAL_PATHS_OK`, `FEATURE_STATE_OK`).
- `./build.sh --check` → **`SELF_SCAFFOLD_SYNC_OK files=2`**.
- `record-gate "integration verify" pass --global-gate` registrado contra `005-portable-harness`.

## Nota de honestidad sobre `diff_ref`

Nada se commiteó en toda la sesión (regla de sesión: solo se commitea a pedido explícito del usuario).
`git rev-parse HEAD` es `898c539669b840e5b5d78a97f484b9abef0df9a6`, un commit anterior a P2 y P3 de esta
feature — los `diff_ref` de esos dos paquetes apuntan a ese sha stale porque no existe ningún commit real
posterior contra el cual apuntar; y el `diff_ref` de P1 es la cadena literal `"HEAD"`, una imprecisión
histórica menor de cuando P1 se aceptó. Ninguno de los dos se "corrige" acá: no hay un commit real al cual
recorregirlos, y tocar un campo de evidencia de un paquete ya `accepted` estaría fuera de alcance para una
pasada de integración (el integrador no reabre paquetes aceptados por observaciones cosméticas). La garantía
real de esta integración es que los gates de arriba se corrieron frescos contra el árbol de trabajo vivo, no
que exista un commit que los respalde.

## Hallazgos cruzados

Ninguno. Regresión: cero.

## Veredicto

Los 3 paquetes componen sin deriva de contrato. Gate global registrado. Lista para `transition INTEGRATION`
y, una vez cerrado el fix de `done_ready()` sobre `blockers` resueltos (006-P3.1, AC-36), para
`transition DONE`.
