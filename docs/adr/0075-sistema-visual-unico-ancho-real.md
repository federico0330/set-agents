# ADR-0075 — Un solo sistema visual: ancho de celda real, paleta por rol, capacidad medida
# en cada llamada

- Estado: Accepted (2026-08-31); **superseded en parte por ADR-0076** (2026-09-09).
  Feature `048-consola-para-humanos`, PKG-A.
- ADR-0076 reemplaza únicamente la cláusula temporal de §5: `menu()` ya no mide antes del
  primer loop; el primer frame usa caché/ausencia y la medición ocurre bajo `Actualizar estado`.
  La prohibición de medir desde un paint y todas las decisiones visuales de este ADR siguen vigentes.
- El onboarding automático y `first_run` del ingreso al home simple fueron superseded de forma
  explícita por ADR-0076/049; no son una excepción a este contrato visual ni vuelven a ejecutar
  mediciones antes del primer frame. `Modo experto` pasa a ser una acción directa de ese home.
- **Amplía ADR-0050**, no lo supersede. La decisión de 0050 sigue vigente palabra por palabra
  ("jerarquía por espaciado y peso, no por glifo"); lo que cambia es el *test* que la
  custodiaba, que era a la vez más estricto y más laxo que la decisión.
- Ejes store / API Gateway / deploy: n/a. Cero persistencia, cero red, cero despliegue.

## Contexto

Tres defectos medidos, todos en la capa de pintado.

### 1. Dos sistemas de color que no se hablaban

`set_agents_app.use_color()/color()` (ANSI de 16 colores) y `tui_views` (256 colores, paleta
propia). Un panel se pintaba con uno y su picker con el otro.

### 2. `tui_views` congelaba la paleta al importar

```python
if use_color():          # a nivel de módulo, tui_views.py:37
    CYAN = "\033[38;5;75m"
    ...
else:
    CYAN = EMERALD = ... = ""
```

Importado en un proceso cuyo stdout no era TTY en ese instante, `CYAN == ""` para siempre. Y
`rounded_box(title_color=CYAN)` además bindeaba el valor en *def-time*, un congelamiento más.

### 3. El padding contaba codepoints, no celdas

`visual_len = len(strip_ansi(text))`. Con eso se calculaba el relleno de `rounded_box` y de
`metrics_grid`. En cuanto un glifo de ancho doble entró en un título — y entró: `🧰 Ecosistema
y Herramientas Avanzadas`, `⚙️ Modo de Trabajo`, `🛡️ Seleccionar Postura`, `📐 Seleccionar
Metodología` — el borde derecho quedó corrido.

Y ese emoji **pasaba el gate**: `test_menu_items_carry_no_emoji_and_single_space_layout` sólo
miraba `MENU_ITEMS`, nunca los headers. La regla que usaba, además, era `isascii()`, que
rechaza `"Cómo está"` (que no rompe nada) y admitiría cualquier símbolo que caiga en ASCII.
El propio ADR-0050 dice "texto plano **ASCII/Latin**": el test era más estricto que su decisión.

## Decisión

### 1. `ai/scripts/ui.py` es el único sistema visual; `tui_views.py` se borra

Paleta Rose Piné direccionada **por rol** (`title`, `heading`, `ok`, `warn`, `err`, `muted`,
`line`, `cool`), nunca por nombre de color, de modo que cambiar de tema sea cambiar una tabla.
Stdlib puro (DEC-4).

### 2. La capacidad se recalcula en cada llamada

`caps(stream)` → `"truecolor" | "256" | "16" | "none"`, leyendo `NO_COLOR`, `TERM`,
`COLORTERM` y `stream.isatty()` **en el momento**. Ninguna constante de color a nivel de
módulo. La escalera degrada de verdad: truecolor → 256 → 16 → sin color.

### 3. `cell_width()` es la única autoridad de ancho

`unicodedata.east_asian_width` W/F = 2, `combining` = 0, resto 1. `pad()` y `clip()` la usan;
`len()` no se usa para layout en ningún lado.

### 4. La regla de etiqueta se enuncia en positivo y se aplica a todo

```python
LABEL_PUNCT = " -/()[]·?¿!¡,.:;+&'\""
def is_safe_label(text):
    return all(c.isalnum() or c in LABEL_PUNCT for c in text)
```

Letras, dígitos, espacios y un conjunto cerrado de puntuación. **Un glifo decorativo es
trabajo del renderer, nunca del texto** — el cursor (`▸`), el punto de estado (`●`), la
casilla (`[x]`) los pone `ui`, no la etiqueta. Esa es exactamente la decisión de ADR-0050,
enunciada de forma que:

- admite `"Cómo está"`, `"Más"`, `"¿Qué CLI?"` — español honesto, que `isascii()` rechazaba;
- rechaza `⏻` (U+23FB, el catalizador de 0050), `🗒`, `🧰`, `⚙️` — incluidos los que llevan
  selector de variación, que un chequeo de ancho solo dejaría pasar.

El test se aplica ahora a **toda** etiqueta visible (home en modo experto, hints, harness
choices, nombres de host, targets y presets del wizard, labels de postura), no sólo a
`MENU_ITEMS`, y tiene su mitad negativa: los cinco glifos que motivaron 0050 deben seguir
siendo rechazados.

### 5. Un paint no mide

`probe_host_model_counts()` levanta un subproceso por CLI. `_home_header` lo llamaba, o sea
que **cada repintado del menú podía disparar probes** (mitigado por un cache de 60 s, pero el
primer paint lo pagaba entero, y el primer paint es el que el usuario ve). Ahora `menu()`
mide una vez, con `tui.with_progress`, antes de abrir el loop; `_pulse_line()` lee sólo del
cache y, si no hay medición, lo dice con palabras en vez de imprimir un cero.

## La trampa que este ADR no pisa

Cambiar `isascii()` por `is_safe_label()` **no es aflojar el test para que pasen las tildes**.
El test nuevo falla en más casos que el viejo, no en menos: cubre etiquetas que el viejo ni
miraba (donde había emoji de verdad), y su mitad negativa afirma explícitamente que los glifos
de 0050 siguen prohibidos. Lo que se corrigió es que el viejo confundía "no romper la
alineación" con "no tener tildes", dos cosas distintas.

## Alternativas rechazadas

- **Sólo prohibir por ancho (`east_asian_width in "WF"`).** No alcanza: `⚙️` es U+2699
  (ancho ambiguo) + U+FE0F, y `⏻` es ancho ambiguo a secas. Los dos pasarían.
- **Mantener `tui_views` y arreglarle el congelamiento.** Quedarían igual dos paletas y dos
  `use_color()`. El defecto de fondo era tener dos sistemas, no que uno estuviera roto.
- **Adoptar `rich`/`textual`.** DEC-4 de 005 (repetida en el Non-goal de 045) prohíbe una
  dependencia TUI fuera de stdlib, y el motor de `tui.py` ya resuelve raw mode, decodificación
  de teclas, viewport y búsqueda.

## Consecuencias

- `ai/scripts/tui_views.py` deja de existir; `SessionCache`/`GLOBAL_CACHE` viven en `ui.py`.
- `menu_style()` devuelve los pintores de `ui`, así que picker, headers y paneles comparten
  paleta.
- Los pickers de `setup_models.py` reciben estilo por primera vez: antes ninguna de sus ocho
  llamadas a `run_picker` pasaba `style`, así que la pantalla Modelos se veía monocroma
  mientras el resto de la app estaba tematizado.
- Un glifo nuevo en el sistema visual tiene que medir una celda: hay un test que recorre
  `CURSOR`, `DOT_*`, `CHECK`, `CROSS`, `BAR_*` y el spinner y lo verifica.
