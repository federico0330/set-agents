# ADR-0050 — Superficie humana: sin emoji estructural, flags internas ocultas (no borradas),
# JSON crudo deja de ser el default

- Estado: Accepted (2026-08-15). Feature 025-consola-minima-y-flexible, PKG-1
  (`D1-superficie-humana`). AC-01, AC-02, AC-03.

## Contexto

Federico, dueño e ingeniero del repo: *"quiero que la app de terminal sea más minimalista y sólo
muestre lo transparente al usuario, sin muchos comandos ni caracteres raros… Y quita/oculta las
opciones que al usuario no le agregan nada."* No pide que se le esconda poder — pide que la
superficie **por defecto** sea la que un humano usa.

Tres defectos medidos en `ai/scripts/set_agents_app.py`:

### AC-01 — `MENU_ITEMS` (antes de este ADR, líneas 3523-3534) son 10 ítems, los 10 con emoji

`🗒  Vault Obsidian` y `⏻  Salir` llevaban **dos espacios** en vez de uno — un parche a mano
compensando que esos dos glifos miden distinto en la mayoría de las fuentes de terminal. Ese
parche era la prueba del problema: emoji como icono estructural depende de la fuente, rompe
alineación, y no se puede tematizar (regla que transfiere de la skill `ui-ux-pro-max`, aunque
scopeada a web/mobile).

### AC-02 — el CLI expone 68 flags (`parser.add_argument`, todas en `main()`), las 68 visibles en `--help`

Algunas son primitivas de ciclo de vida de ruteo (`--route-decide`/`--route-dispatched`/
`--route-terminal`/`--route-quota-exhausted` y sus modificadores puros) que **sólo invocan los
cuatro CLI de spawn** (`opencode_spawn.py`, `codex_spawn.py`, `claude_code_spawn.py`,
`set_agents_spawn.py`, vía `_run_app_cli`, siempre con `--json`) o el canal de automatización que
`coord_policy.SAFE_ARGV` sanciona (`--rout(e|ing)-\S+`). Ninguna aparece sugerida a un humano en
ningún wizard, README o ADR como acción directa. Al revés: `--route-doctor`/`--route-explain`/
`--model-preference-show` **sí** aparecen sugeridas al humano dentro del propio wizard "Modelos"
(`setup_models.py:228,252,254,238`), y `--routing-migrate` está documentado como "operator-driven"
(ADR-0010). Mutar el estado de un run a mano desde la terminal (o dejar que las mande crea) no le
agrega nada al usuario y arriesga romper una autorización de un solo uso en vivo.

### AC-03 — `--route-doctor` (y el resto de comandos de routing) imprime JSON crudo salvo que
stdout sea una TTY

`routing_human = sys.stdout.isatty() and not args.json` (antes de este ADR): un humano en un
terminal real veía texto; la MISMA invocación con stdout redirigido/pipeado (sin pedir `--json`)
caía en JSON crudo igual. `_routing_output` (`set_agents_app.py:498-511`) ya separaba el canal
humano (stderr) del máquina (stdout, `--json`) — el defecto era **cuál elegía por default**, no
la separación en sí.

## Decisión

### 1. AC-01 — `MENU_ITEMS` sin emoji; jerarquía por espaciado y peso, no por glifo

`MENU_ITEMS` pasa a texto plano ASCII/Latin (`"Estado general"`, `"Instalar / Reparar"`, …,
`"Vault Obsidian"`, `"Salir"`), un espacio limpio en cada ítem — el parche de doble espacio
desaparece porque ya no hay glifo de ancho variable que compensar. La jerarquía visual
(espaciado y peso que pide AC-01) ya existe en `tui._render_items`: el marcador `›` más
`bold()` en la fila con el cursor — sin cambios en `tui.py`, porque ese mecanismo ya era
correcto; el defecto vivía enteramente en el contenido de la tupla, no en el picker.

### 2. AC-02 — `help=argparse.SUPPRESS` para 9 flags, nunca `del`/borrado; `--help --avanzado` las
   revela

`_INTERNAL_FLAGS` (conjunto nombrado, único origen de verdad):

```
--route-decide --route-dispatched --route-terminal --route-quota-exhausted
--quota-error --latency-ms --usage --fresh-probes --quota-failover-e2e
```

Criterio, con evidencia, no con intuición: **primitivas de mutación de ciclo de vida de ruteo**
(decide/dispatch/close) + sus **modificadores puros** (sin sentido sin la primitiva que
modifican) + el **gate E2E manual** de AC-06 (`--quota-failover-e2e`, que sólo aparece en logs
de evidencia de paquetes pasados, nunca invocado por un script). Las superficies de **sólo
lectura** de la misma familia (`--route-doctor`, `--route-explain`, `--routing-report`,
`--routing-decisions`, `--routing-open-runs`, `--routing-recent-writers`, `--routing-migrate`) y
`--context` **quedan visibles** — son diagnóstico/operación humana documentada, no bookkeeping de
máquina.

`_build_parser(advanced=False|True)` es el único parser que `main()` construye — `advanced`
controla exclusivamente el `help=` de esas 9 flags (`_hidden_help`); todo lo demás (`dest`,
`type`, `choices`, `default`, `action`) es idéntico entre ambas construcciones, así que ocultar
nunca puede — por construcción — cambiar cómo una flag parsea o qué hace. `main()` intercepta
`--help --avanzado` (cualquier orden) contra `sys.argv` crudo, antes de construir el parser
normal — el mismo patrón que ya usaba la intercepción de `--tools-propose`/`--tools-approve`
(F-14) — y llama a `_build_parser(advanced=True).print_help()`.

`--avanzado` **no** es un argumento argparse real: declararlo como tal lo haría descubrible vía
`--help` normal (`-h`/`--help` imprime todos los flags conocidos, incluido uno recién declarado),
justo lo opuesto del punto.

### 3. AC-03 — default humano, `--json` preserva el sobre exacto

`routing_human = not args.json` (antes: `sys.stdout.isatty() and not args.json`). El texto
humano sigue yendo a stderr, el JSON sigue yendo a stdout con `--json` — `_routing_output` no
cambia una línea. Sólo cambia CUÁNDO se elige cada rama: ahora es puramente "¿pedí `--json`?",
nunca "¿mi stdout resulta ser una terminal ahora mismo?".

Auditado, no asumido: los cuatro CLI de spawn (`opencode_spawn.py`, `codex_spawn.py`,
`claude_code_spawn.py`, `set_agents_spawn.py`) pasan `--json` en **cada** llamada a comandos de
routing vía `_run_app_cli` — grep exhaustivo, cero excepciones. Ningún consumidor real dependía
del default viejo.

## La trampa que este ADR no pisa

AC-02 **no borra ninguna flag** — `coord_policy.SAFE_ARGV` las sigue permitiendo, los cuatro
spawn CLI las siguen invocando exactamente igual, con la MISMA firma. `help=argparse.SUPPRESS`
es una propiedad de renderizado de `--help`, documentada así en la librería estándar; no toca
parsing, dispatch, ni valores por defecto. Un test dedicado (`test_internal_flags_cannot_be_
silently_deleted`, `tests/test_harness.py`) falla si alguna de las 9 desaparece del parser —
oculta o no —, distinto del test que sólo comprueba que sigue oculta.

AC-03 **no** toca el formato del `--json` — mismo `json.dumps(payload, sort_keys=True)`, mismas
claves, mismo orden. `test_route_doctor_default_is_human_text_on_stderr_json_flag_preserves_
machine_envelope` prueba ambas ramas contra el mismo mock.

## Alternativas rechazadas

- **AC-02: borrar las flags internas en vez de ocultarlas.** Rechazada explícitamente por el
  context pack — `coord_policy` las tiene en su allowlist y los cuatro spawn CLI las invocan;
  borrarlas rompe el harness en producción, no sólo en un test.
- **AC-02: ocultar también las superficies de sólo lectura de routing (`--route-doctor` y
  hermanas).** Rechazada — hay evidencia directa de que se sugieren a un humano dentro del wizard
  "Modelos" y en ADRs previos (0010, 0035) como diagnóstico operador-driven; ocultarlas sería
  esconder poder que Federico explícitamente no pidió esconder.
- **AC-02: declarar `--avanzado` como argumento argparse real.** Rechazada — lo haría aparecer en
  el `--help` normal, reabriendo el mismo problema de descubribilidad que F-08 ya cerró para
  `--tools-propose`/`--tools-approve`.
- **AC-03: condicionar el default también a `sys.stdin.isatty()` (o a alguna otra heurística de
  entorno) en vez de sólo `--json`.** Rechazada por simplicidad y por el mismo principio que
  ADR-0038 usa para "nunca instala, siempre pregunta": una sola señal explícita
  (`--json` presente o no) es más fácil de razonar y de auditar en `coord_policy` que un
  heurístico de entorno que puede variar entre corridas idénticas del mismo comando.

## Consecuencias

- `MENU_ITEMS` es texto plano; cualquier renderizador (incluido un futuro tema de color) deja de
  tener que lidiar con ancho de glifo variable.
- `--help` por default lista 59 de 68 flags; `--help --avanzado` lista las 68, con texto real
  para cada una de las 9 antes suprimidas (nunca `argparse.SUPPRESS` crudo).
- El default de todo comando de routing sin `--json` es texto humano en stderr, sin importar si
  stdout es una TTY o está pipeado/redirigido. `--json` sigue produciendo el mismo sobre de
  siempre, byte a byte.

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D1-implementer.md` — tabla AC→cambio→prueba,
el menú antes/después pegado, la lista de 9 flags ocultas con el criterio del corte, la salida de
`--route-doctor` humana vs `--json`, y el rojo mordido de cada test nuevo (neutralizado, confirmado
en rojo, revertido).
