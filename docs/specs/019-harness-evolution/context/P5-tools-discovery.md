# Context pack — P5-tools-discovery (ADR-0038)

Spec: `docs/specs/019-harness-evolution/spec.md`, AC-30..AC-35. Último paquete de la feature. Es el
único que toca la superficie de seguridad del harness (`coord_policy.py`): leelo entero antes de
escribir una línea.

## El problema que resolvés

Hoy el catálogo de herramientas es **cerrado**: `tools.toml` (`ai/scripts/set_agents_app.py:1168`
`load_catalog()` lo lee y nada más). Si un agente necesita un CLI que no está en el catálogo,
`cmd_tools_install` imprime `TOOL_UNKNOWN <name> — agregalo en tools.toml`
(`ai/scripts/set_agents_app.py:1228`) y devuelve `2`. Eso es un **callejón sin salida**: el agente no
puede agregarlo (editar `tools.toml` no está en su canal permitido), y el mensaje se lo tira al humano
sin flujo.

La decisión de producto ya tomada (§0.4 del pedido, no la re-litigues): el catálogo se abre **bajo
demanda** con `propose → aprobación humana → approve → install`. **Siempre se pregunta antes de
instalar algo nuevo; sudo siempre queda manual.**

## Postura de seguridad que NO se relaja (esto es lo importante del paquete)

`cmd_tools_install` (`:1225-1273`) ya tiene una postura ganada a pulso y este paquete **no la toca**:

- sudo se muestra completo y pregunta **aun con `--yes`** (`:1243-1255`); sin TTY → `TOOL_MANUAL` con
  el comando exacto.
- sin TTY y sin `--yes` → nunca corre nada en silencio (`:1256-1260`).
- fallback npm→pnpm (`:1238`), `pick_method` por plataforma (`:1186`).

Lo que `--tools-approve` produce es **una entrada de catálogo más**, que después atraviesa ese mismo
`cmd_tools_install` sin cambios. Si te encontrás editando el cuerpo de `cmd_tools_install` para que el
flujo nuevo funcione, parate: el diseño está mal.

## AC-30 — `--tools-propose` (no instala)

```
--tools-propose <name> --kind cli|mcp|skill --detect <bin> --install-<method> "<cmd>" --why "<motivo>"
```

Valida y **no muta nada**: imprime la pregunta consolidada para el humano y sale.

Validación fail-closed, en la línea del resto del repo:

- `<name>`: forma cerrada. Reusá el criterio de `coord_policy._CATALOG_NAME`
  (`ai/scripts/coord_policy.py:172`, `[a-z0-9][a-z0-9_-]{0,31}`) — no inventes una segunda gramática de
  nombres, que diverjan es una bomba de tiempo.
- `<cmd>`: **rechazá sudo y pipes ocultos**. Rechazo explícito con código de salida y mensaje, nunca
  un saneamiento silencioso. Ojo: `curl … | bash` ES un método legítimo del catálogo actual
  (`tools.toml` `[cli.gcloud.install] curl`), así que "pipe oculto" no puede significar "cualquier
  pipe" — definí el criterio en el ADR y testealo en ambas direcciones (lo que pasa y lo que no).
  Si el criterio te queda ambiguo, elegí el más restrictivo y dejalo escrito: es más barato aflojarlo
  después que descubrir que dejaste pasar algo.
- `--kind` fuera de `{cli, mcp, skill}` → error explícito.

## AC-31 — `--tools-approve <name>` + `tools.local.toml`

- Escribe el bloque en **`tools.local.toml`** (NUEVO, **untracked** — agregalo a `.gitignore`) con el
  mismo schema que `tools.toml` (`[cli.<name>]` con `detect` + `install.<method>` + `doc`/`note`).
- `load_catalog()` (`:1168`) pasa a **mergear** `tools.toml` + `tools.local.toml`. Que el repo no tenga
  `tools.local.toml` **no puede fallar**: ausente = catálogo curado y listo (mismo criterio never-fails
  que `notes_root` en `render_notes.py:36`).
- Decidí y documentá quién gana ante colisión de nombre. Recomendación: **el curado gana**, y el local
  colisionante se reporta — un catálogo local no debería poder secuestrar `vercel`.
- `log-decision` en el approve (qué herramienta, por qué, quién la pidió).
- La instalación sigue por `cmd_tools_install` **sin cambios de postura**. MCPs entran **disabled**
  (política MCP del repo, ADR-0025.5).
- **Round-trip probado**: propose → approve → aparece en `--tools` / `_tools_data()` → `--tools-install`
  la agarra. Ese round-trip es evidencia, no un test de humo.

## AC-32 — `TOOL_UNKNOWN` deja de ser callejón sin salida

`ai/scripts/set_agents_app.py:1228`: el mensaje pasa a sugerir el flujo propose (el comando exacto a
correr). Ojo: `TOOL_UNKNOWN` es un token de salida que la suite puede estar pineando — `grep -rn
"TOOL_UNKNOWN" tests/` **antes** de tocarlo, y mantené el token, cambiá lo que sigue.

## AC-33 — `coord_policy._tools_channel_allowed`

`ai/scripts/coord_policy.py:175-204`. Extendé el **argv-walker** a las dos flags nuevas, con gramática
cerrada por flag, como ya hace con `--tools-install NAME [--yes|--dry-run]` (`:190-194`) y
`--mcp-* NAME [--harness H]` (`:197-203`).

El docstring (`:176-184`) explica **por qué** es un walker y no un regex: el escape histórico
`--context --scaffold X` (nota SEC-001 en `SAFE_ARGV`) es lo que cuesta un chequeo laxo del resto de
argv. **No agregues un patrón con `.*` a `SAFE`.** `--tools-propose` toma varios pares
flag+valor, incluido un `<cmd>` con espacios: esa es exactamente la forma que un regex laxo deja
escapar. Escribí el caso adversario como test (un `--tools-propose` con un argv que intente colar otra
cosa, y que `allowed()` lo rechace).

Y pensalo dos veces antes de permitir `--tools-approve` en el canal del agente: el approve es
**la aprobación humana**. Si el agente puede correr approve solo, el flujo propose→humano→approve es
teatro. Recomendación fuerte: **`--tools-propose` sí entra al canal; `--tools-approve` NO** — lo corre
el humano (o el orquestador tras la respuesta explícita del humano, por su propio canal). Sea cual sea
tu decisión, va argumentada en el ADR y con test.

## AC-34 — skills solo project-local

Una skill instalable va a `.claude/skills/` **del proyecto destino**, nunca a `Global/_canonical/`.
Mutar el canónico está **fuera de alcance y explícito en el ADR**: `Global/_canonical/` es la fuente
desde la que `./build.sh` genera los 4 árboles; una skill inyectada ahí se propagaría a todos los
proyectos y sobreviviría a cualquier revisión.

## AC-35 — doctrina y consola

- `Global/_canonical/agents/orchestrator.md`, sección `## Tool catalog — resolve first, record always
  (ADR-0025)` (`:632-645`): "tool faltante" deja de ser blocker también **fuera** del catálogo curado —
  el camino es propose, no `blocked`.
- `Global/_canonical/agents/implementer.md`, bloque Resolve-first (`:57-64`): mismo tratamiento; hoy
  solo cubre "un CLI del catálogo curado".
- Consola: ítem de menú **"Proponer herramienta nueva"** y las dos flags. `MENU_ITEMS`
  (`ai/scripts/set_agents_app.py:2421-2431`) y el panel `Herramientas (catálogo)` del estado general
  (`:2388-2389`) / `_tools_header()` (`:1276-1290`).
- **Cuidado**: `tools_menu()`/`_tools_data()` tienen contrato pineado por la suite inmutable — el
  docstring de `_tools_data` (`:1212`) dice "AC-28: the data cmd_tools()/tools_menu() both render, in
  catalog order" y `_tools_header` (`:1278-1280`) dice que el formato de fila y el Enter→install son
  contrato pineado. Agregá, no reescribas.

## Restricciones

- **ADR-0038 primero, después test, después código.** Re-verificá con `ls docs/adr/` que `0038` esté
  libre e indexalo en `docs/adr/README.md`. En el ADR van, explícitos: el criterio de rechazo de
  sudo/pipes, la resolución de colisión curado-vs-local, quién puede correr approve, y por qué
  `Global/_canonical/` queda fuera.
- Tras tocar `Global/_canonical/`: `./build.sh` y después `./build.sh --check` sin drift.
- `tests/test_harness.py` assertea frases doctrinales **por grep**: toda frase exacta que el AC nombre
  necesita su test, y toda frase existente que muevas puede romper un grep (`grep -n "<frase>"
  tests/test_harness.py` antes).
- Nada de refactors oportunistas en `set_agents_app.py` ni en `coord_policy.py`.
- No se persiste nada descubierto en `models.toml`; routing/billing no se tocan.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` no está instalado**; el conteo sube, nunca baja) ·
`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh` y después `./build.sh --check` sin drift ·
`git diff --check` limpio · `git status --porcelain` **no debe mostrar `tools.local.toml`** (untracked
por `.gitignore`).

Nota: correr `tests.test_harness` **aislado** produce ~72 errores `KeyError: 'set_agents_app'`
preexistentes (aislamiento de import), no son regresión tuya; usá `discover` o `verify.sh`.

Prueba viva que va como evidencia (pegá comando + salida real):

```bash
python3 ai/scripts/set_agents_app.py --tools-propose <name> --kind cli --detect <bin> --install-npm "npm install -g <pkg>" --why "..."
python3 ai/scripts/set_agents_app.py --tools-propose evil --kind cli --detect x --install-curl "sudo rm -rf /" --why "..."   # debe rechazar
python3 ai/scripts/set_agents_app.py --tools-approve <name>
python3 ai/scripts/set_agents_app.py --tools | grep <name>
python3 ai/scripts/set_agents_app.py --tools-install <name> --dry-run
```

## Advertencia de proceso (leela, no es genérica)

Esta feature acumula **tres afirmaciones de verificación fabricadas** del rol reparador — tablas que
decían "verificado con tal comando" cuando el comando no decía eso. Está registrado en
`ai/state/decisions-log.jsonl`. **Cada afirmación de verificación tuya viene con el comando pegado y su
salida real.** Si no lo corriste, escribí "sin verificar": una conjetura marcada es honesta, una sin
marcar es un defecto.

Y en los tres paquetes anteriores apareció **un test decorativo por paquete** (pasaba con el arreglo
removido). Antes de entregar: por cada test nuevo, neutralizá el cambio que assertea, confirmá que el
test se pone en rojo, revertí, y pegá esa prueba de mordida.

## Evidencia esperada

`docs/specs/019-harness-evolution/evidence/P5-implementer.md`: tabla AC → cambio (`archivo:línea`) →
prueba; el round-trip propose→approve→install pegado entero; los rechazos (sudo, pipe, nombre
inválido, kind inválido) con su salida; el caso adversario de `coord_policy` con el `allowed()` que lo
rechaza; la prueba de mordida por test; y los gates pegados.

## Checkpoint

Si te acercás al límite de ejecución, escribí primero el progreso parcial y los próximos pasos exactos
en el archivo de evidencia, y recién ahí pará.

## Fuera de alcance

Routing, billing y consola de modelos (P1/P2, aceptados) · `docs/modules/**` y el motor de render (P3)
· doctrina de narración, `/explicar` y question policy (P4) · `Global/_canonical/skills/**` como
destino de instalación (AC-34) · ampliar `enabled_providers` / `routes.v1.toml` / `ROUTING_PROVIDERS` ·
techo de gasto · gate de auditoría externa (codex-audit, descartado por DEC-3).
