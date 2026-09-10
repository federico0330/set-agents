# 048 — Console for humans

- **Estado:** Approved (Federico, 2026-08-31) — pedido literal: *"Es una aplicación poco colorida,
  muy sobrecargada, poco intuitiva, nada de todo eso lo puede entender un usuario final que
  solamente instala el harness para mejorar su efectividad de uso de IA. Rehacé la aplicación de
  consola."* Referencia visual pedida por el usuario: `gentle-ai`.
- **Modo:** feature · risk signal `public-contract` (superficie humana) + `multi-module`.
- **Packages:** A (sistema visual), B (arquitectura del menú), C (primer arranque guiado),
  D (hosts accionables), E (documentación).
- **ADRs:** 0074 (despacho por clave), 0075 (sistema visual único). Amplía 0071 con la familia
  `hosts` del overlay.
- **Enmienda 045.** Los Non-goals de `045-consola-viva-e-instancia` "no reordenar
  `WIZARD_ITEMS[0..4]` ni renumerar las ramas de `MENU_ITEMS`" y "copy estilo gentle-TUI" quedan
  sin efecto por decisión explícita del usuario en esta sesión. Todo el resto de 045 sigue
  vigente y verificado: AC-A.1 (la matriz `AREA`/`EFFORT` no aparece en la primera pantalla),
  AC-A.2 (ninguna fila cero inventada), AC-B.* (el gusto va al overlay, `models.toml` limpio),
  AC-C.1 (postura y metodología sin `--avanzado`), AC-D.* (effort por lane).

## Problema

`./set-agents` es la única puerta del producto y no le habla al usuario que lo instala.

1. **Jerga y sin acentos.** El home eran seis etiquetas ASCII (`Como esta`, `Instalar /
   actualizar`, `Como elige la IA`, `Como trabaja`, `Mas`, `Salir`), ninguna con una línea que
   dijera qué pasa al elegirla. El header abría con `SET · automatico · 0 cuentas vivas` y una
   grilla de tres tarjetas antes de que el lector supiera qué es una "cuenta viva".
2. **Dos sistemas de color, uno congelado.** `set_agents_app.color()` (16 colores) y `tui_views`
   (256, decidido en import-time: sin TTY al importar, sin color para siempre).
3. **Emoji desalineado.** `🧰 ⚙️ 🛡️ 📐` en los headers de `more_menu`/`preferencias_menu`,
   dentro de cajas cuyo padding usaba `len()`. Contradice ADR-0050 y pasaba el gate porque el
   test sólo miraba `MENU_ITEMS`.
4. **Sin primer arranque.** `first_run()` imprimía "leé README.md" y dejaba al usuario en el
   mismo menú. El README documentaba un menú de nueve emoji que no existe desde ADR-0050.
5. **Segunda fuente de verdad ya divergida.** El header de postura decía
   `autonoma/guarded/paso-a-paso`; `POSTURAS` define `autonoma/consultiva/todo_consultado`.
6. **Un paint que mide.** `_home_header` llamaba `probe_host_model_counts()` (un subproceso por
   CLI) en cada repintado.
7. **Tres registros, una sola superficie.** `PROVIDERS`, `HOSTS` y `providers.toml` conviven;
   la consola sólo actuaba sobre suscripciones — el registro que no puede representar un host.
   De ahí que no hubiera forma de "agregar agy": "Cuentas" es el overlay tri-estado sobre
   `[subscriptions]`, cuyo universo son cuatro prefijos (`openai`, `anthropic`, `zen`, `ollama`).

## Alcance

### PKG-A — sistema visual (`ai/scripts/ui.py`, ADR-0075)
Paleta Rose Piné por rol, `caps()` recalculado por llamada, `cell_width()` como única autoridad
de ancho, `is_safe_label()` como regla de etiqueta, componentes (`rule`, `kv`, `steps`, `bar`,
`checkbox`, `radio`, filas de picker, wordmark). `tui_views.py` se borra. `tui.py` gana
multi-selección aditiva (`multi=True`, `tui.Marked`, espacio togglea).

### PKG-B — arquitectura del menú (ADR-0074)
`Action(key, label, hint, level)`; el home despacha por clave. Modo simple / experto recordado
en `app.toml`: en simple, cinco verbos y `Salir`; en experto, las superficies de ingeniería
suben a primer nivel. `MORE_ITEMS`/`more_menu` desaparecen. Copy reescrito con acentos.

### PKG-C — primer arranque guiado (`ai/scripts/onboarding.py`)
Cinco pasos: qué hay en la máquina → qué configurar (multi-selección) → cómo querés trabajar
(preset) → revisión → aplicar con marcas. Se dispara en `first_run()` y queda como la acción
`configurar`. Las pantallas son funciones puras; las mutaciones se inyectan desde
`set_agents_app` (ADR-0066).

### PKG-D — hosts accionables
`hosts_menu()`/`host_menu()`: medir, elegir modelo (sólo lo que el probe listó) y elegir
esfuerzo para agy/copilot y compañía. Persiste en una familia `hosts` nueva del overlay de
instancia (`models_config.host_pin` / `write_host_pin`), no en `AREA_FIELDS`: un pin de host es
gusto de máquina, no de duty.

### PKG-E — documentación
Este spec, ADR-0074/0075, `docs/modules/consola.md`, y la sección de menú del README.

## Non-goals

- Cualquier dependencia TUI fuera de stdlib (DEC-4 de 005, reiterado por 045).
- **Instalarle el harness a agy.** `install.py --target` acepta
  `(opencode, claude-code, codex, pi, cursor)` y `host_adapters._agy_install_harness` es un
  `NotImplementedError` declarado como costura diferida por 047. Decisión explícita del usuario:
  agy se hace usable como lane, no instalable. La brecha queda documentada acá.
- Superficie TUI para `providers.toml` (`--provider-add` y hermanos siguen ocultos, ADR-0050).
- Tocar contratos de máquina: ni un flag, ni una clave de JSON, ni un formato de estado.

## Assumptions

- `SUBSCRIPTION_BY_PREFIX` sigue siendo el universo de "Cuentas"; agregar un host ahí sería
  escribir una entrada que ningún consumidor lee. **Verificado**: `_subscription_candidates`
  (`setup_models.py:169-180`) y `_PROVIDER_SUBSCRIPTION` (`models_config.py:505`).
- El presupuesto de primer paint de 300 ms (`tests/test_models_wizard_first_paint.py`) sigue
  siendo el techo del wizard de modelos. **Verificado**: la suite pasa sin cambios.
