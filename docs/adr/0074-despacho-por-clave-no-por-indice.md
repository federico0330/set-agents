# ADR-0074 — El menú despacha por clave estable, no por la posición de la fila

- Estado: Accepted (2026-08-31). Feature `048-consola-para-humanos`, PKG-B.
- **Enmienda el Non-goal de 045** "no renumerar las ramas de `MENU_ITEMS`" y "no reordenar
  `WIZARD_ITEMS[0..4]`" (`docs/specs/045-consola-viva-e-instancia/spec.md`, sección Non-goals).
  Ese Non-goal existía para proteger unos pines de test; este ADR cambia los pines por otros
  más fuertes y por eso el Non-goal deja de tener objeto.
- No toca ningún contrato de máquina: ni un flag del CLI, ni una clave de JSON, ni un archivo
  de estado. Es enteramente sobre cómo el TUI decide qué función llamar.

## Contexto

`menu()` despachaba con una escalera de enteros:

```python
choice = tui.run_picker(MENU_ITEMS, ...)
index = choice.index
if index == 0:      # Como esta
elif index == 1:    # Instalar / actualizar
...
elif index == 5:    # Salir
```

y `wizard()` (`setup_models.py`) hacía lo mismo sobre `WIZARD_ITEMS[0..4]`. Los tests seguían
esa forma: `test_menu_ui.py` mandaba `Selected(1), Selected(0), Selected(2)` y afirmaba que
`install.sh` recibía `--harness opencode`; `test_harness.py` afirmaba
`MENU_ITEMS[0] == "Como esta"` y `MENU_ITEMS[-1] == "Salir"`.

**Un pin de índice es más débil de lo que aparenta.** Afirma que la fila número N hace lo que
la rama número N hace — que es cierto por construcción. Lo que *no* puede detectar es que la
etiqueta que ese índice pretendía proteger se haya mudado a otra rama: si alguien intercambia
dos entradas de la tupla sin tocar la escalera, `Selected(1)` sigue llegando a `elif index ==
1` y el test sigue verde mientras el usuario, eligiendo "Instalar", corre el wizard de modelos.

El costo del acoplamiento también era real: la tupla no se podía reordenar ni ampliar sin
mover a mano cada rama y cada test, y por eso el spec 045 tuvo que declarar el reordenamiento
un Non-goal en vez de resolverlo.

## Decisión

### 1. Una tabla declarativa; `key` es el contrato

```python
@dataclasses.dataclass(frozen=True)
class Action:
    key: str      # id estable — lo que pinean los tests
    label: str    # texto humano, libre de reescribirse
    hint: str     # una línea explicativa
    level: str    # "simple" | "experto"
```

`HOME_ACTIONS` (`set_agents_app.py`) y `WIZARD_ACTIONS` (`setup_models.py`) son la única
fuente. `visible_actions(experto)` filtra por nivel y devuelve las filas de este momento;
`_run_home_action(key, ...)` tiene una rama por clave y ninguna por posición.

### 2. `MENU_ITEMS` sobrevive, derivado

Sigue existiendo como nombre de módulo porque README y otros lectores lo usan, pero se calcula
(`tuple(a.label for a in HOME_ACTIONS if a.level == "simple")`), nunca se mantiene a mano. Un
label y su rama ya no pueden separarse: no hay dos listas que sincronizar.

### 3. Los tests nombran la acción, no la fila

```python
def _pick(self, key, experto=False):
    keys = [a.key for a in app.visible_actions(experto=experto)]
    self.assertIn(key, keys, f"la acción {key!r} desapareció del home")
    return app.tui.Selected(keys.index(key))
```

Esto es **estrictamente más fuerte** que lo que reemplaza, en dos sentidos verificables:

- Falla si la acción desaparece (el `assertIn`); el pin de índice no lo notaba, seguía
  eligiendo la fila que quedara en esa posición.
- Sigue afirmando el comportamiento exacto que el pin viejo afirmaba —
  `run_tty([install.sh, "--harness", "opencode"])`, byte por byte — sólo que llega ahí
  nombrando `configurar` en vez de contando filas.

Y los ordenamientos que sí importaban se conservan afirmados sobre claves:
`salir` último en ambos modos, `vault` fuera del modo simple,
`herramientas → proponer → mcps` consecutivos.

## La trampa que este ADR no pisa

**No es debilitar un test para que pase.** Cada aserción de comportamiento del bloque anterior
sigue en pie, sin cambiar: Esc/Ctrl-C salen con rc 0, `mcp_menu` mantiene acción y harness como
enums cerrados, los tres pickers encadenados comparten una sola `TerminalSession`, cancelar
cualquier paso de `vault_menu` nunca alcanza un comando mutante, y el argv de `install.sh` es
idéntico. Lo único que cambió es **cómo el test llega a la rama**, y en la dirección que
detecta un defecto más.

Cada test reescrito se mordió en rojo antes de darlo por verde (evidencia en el paquete).

## Alternativas rechazadas

- **Dejar la escalera de índices y sólo reordenar la tupla.** Es lo que el Non-goal de 045
  prohibía, con razón: sin claves, cada reordenamiento es una oportunidad de desalinear la
  tupla y la escalera, en silencio y en verde.
- **Un `dict[str, Callable]` en vez de una tupla de `Action`.** Un dict no tiene orden
  declarado como dato de primera clase — el orden del home es diseño, no un detalle de
  implementación, y quiero poder afirmarlo (`salir` último, `vault` antes del toggle).
- **Mudar el menú a su propio módulo.** Rechazada por ADR-0066: el cargador del golden suite
  restaura `sys.modules`, así que una función que sale de `set_agents_app.py` pierde la
  identidad de `__globals__` con el objeto que 35 `patch.object(app, ...)` parchean — y en el
  caso de `vault_menu` dejaría verde en falso un `assert_not_called()` sobre un comando
  mutante. La tabla vive dentro del monolito; sólo salió código puro (`ui.py`, `onboarding.py`).

## Consecuencias

- Agregar, quitar o reordenar una entrada del home es editar una tupla. La rama viaja con la
  clave.
- El modo experto es un filtro sobre `level`, no un submenú: las superficies de ingeniería
  suben a primer nivel cuando el usuario las pide y desaparecen cuando no.
- `MORE_ITEMS` y `more_menu()` dejan de existir; sus cinco entradas son filas de nivel
  `experto` del home.
