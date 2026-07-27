# ADR-0007 — Pi lane: CLI-subprocess spawner, guards-as-flags, exact pin, gated flip

- Estado: Aceptado (2026-07-27). Enmienda acotada a la feature 004-adaptive-dispatch (contract 1.1.0),
  package P3-pi-lane. Sustituye la forma literal T-302/T-303 del `plan.md` original (árbol de agentes Pi
  generado + extensión TypeScript sobre el SDK) por la arquitectura recomendada en
  `docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md`, justificada por el spike T-300
  (`docs/specs/004-adaptive-dispatch/evidence/P3-spike-T300.md`) y por la prueba en vivo repetida durante
  esta implementación (`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md`).
- Contexto: ADR-0004 (Pi como runtime opt-in, guardas de seguridad propiedad de SET-AGENTES), ADR-0005 (R3,
  ciclo SQLite), ADR-0006 (AM-1/AM-2, cache de probes).

## Contexto

P1 y P2 dejaron un núcleo de ruteo confiable con dos carriles ejecutables (OpenCode por variantes de tier,
Codex/Claude Code estáticos). Pi era, hasta este paquete, `PI_SIMULATION_ONLY` — una decisión se podía
*explicar* contra Pi pero nunca ejecutar. El spike T-300 probó en vivo que Pi expone todo lo necesario para
un cuarto carril REAL: selección de modelo por-spawn cruzando proveedor (`openai-codex` **o** `anthropic`
en la MISMA invocación del orquestador, algo que ningún otro runtime de este repo permite), vía subproceso
CLI (`pi --model <provider>/<id> --print --mode json`), sin necesitar un host TypeScript/SDK nuevo.

## Decisión 1 — CLI-subproceso, no SDK/extensión TypeScript

El plan original (`plan.md` T-302/T-303) asumía un árbol de agentes Pi generado más una extensión
TypeScript `set_agents_spawn` sobre el SDK de Pi (`createAgentSession`). El spike (Q3) probó TRES caminos
igualmente viables para modelo+effort por-sesión — SDK in-process, RPC, y subproceso CLI — y el subproceso
CLI es el único que:
- No introduce ninguna superficie TypeScript/JS host nueva en un repo que hoy es 100% Python en
  `ai/scripts/`.
- Es EL MISMO patrón que el arnés ya usa para spawnear opencode/codex (subproceso + parseo de su salida).
- Es trivialmente auditable: el argv completo de cada spawn es una lista fija, nunca `shell=True`, nunca
  interpolación de texto de tarea en un shell.

**Prueba en vivo repetida en esta implementación** (2026-07-27, `pi` 0.81.1, ambos proveedores
autenticados):
```
$ pi --model openai-codex/gpt-5.6-luna --print --mode json --no-session --no-extensions \
     --tools read,grep,find,ls "Reply with exactly: PI OK"
```
→ exit 0, stream `session → agent_start → turn_start → message_start/update/end → turn_end → agent_end →
agent_settled`, mensaje final `provider:"openai-codex", model:"gpt-5.6-luna"`, `usage.cost.total` presente.
La misma invocación con `--model anthropic/claude-haiku-4-5` produjo el mismo shape con
`provider:"anthropic", model:"claude-haiku-4-5"`. Ver `docs/specs/004-adaptive-dispatch/evidence/
P3-implementation.md` para el log completo, incluidos los casos de proveedor/modelo inválido (exit 0 pero
`stopReason:"error"` en el mensaje final) y de proveedor completamente desconocido (exit 1, sin ningún
evento JSON) — ambos manejados por `set_agents_spawn.spawn()`.

`ai/scripts/set_agents_spawn.py` es el spawner: construye el argv, corre el subproceso desde un cwd
efímero controlado (Pi muta su cwd — nota del spike), parsea el stream línea por línea, y decide el
resultado (`success` / `model_mismatch` / `failure`) leyendo `message.provider`/`message.model` del último
mensaje `assistant` — el mismo patrón de verificación por MODELO DECIDIDO (no por tier) que la doctrina 004
AC-07 usa para el carril OpenCode.

## Decisión 2 — Guards-as-flags (002 AC-04, enforcement point nuevo)

Sin extensión Pi propia, las guardas de 002 AC-04 (protected-path write, argv/cwd/env manipulation, sin
delegación) se aplican como FLAGS del subproceso, en el spawner:

| Guard | Mecanismo | Condicional |
|---|---|---|
| Contexto fresco/efímero | `--no-session` | Nunca — siempre presente |
| Sin delegación (depth 0) | `--no-extensions` (pi-subagents, la única extensión de delegación que Pi trae, nunca carga) | Nunca — siempre presente |
| Escritura fuera de allowlist | `--tools <allowlist>` — `GUARD_TOOLS_READONLY = (read, grep, find, ls)` por defecto | Sí — pasa a `GUARD_TOOLS_CODE_RW` (agrega bash/edit/write) solo tras el conjunto de tests por-guarda (AC-11g) en verde |
| argv/cwd/env manipulables por la tarea | argv es una lista fija construida por el spawner (nunca `shell=True`); `cwd` es un scratch dir efímero propio del spawner (nunca el cwd del caller); `env` es la copia higiénica `CI/NO_COLOR/TERM` — el texto de la tarea no tiene canal hacia ninguno de los tres | Nunca |

`route_and_spawn` nunca compone `GUARD_TOOLS_CODE_RW` por default — los hijos de este paquete quedan
read-only-only, tal como pide AC-11g, hasta que un paquete futuro pruebe y adopte el tier ampliado.

## Decisión 3 — Install gestionado con pin EXACTO (no soft-pin)

El wrapper personal `~/.local/bin/pi` (no gestionado por este repo) solo aplica un pin BLANDO por edad de
release (`PNPM_CONFIG_MINIMUM_RELEASE_AGE=7200`), señalado como caveat 1 del spike. En vez de tocar ese
dotfile (fuera del alcance de propiedad de este paquete) o generar un instalador nuevo, tanto el probe
(`routing_core/catalog.py`) como el spawner (`set_agents_spawn.py`) invocan Pi a través de UNA versión
EXACTA fijada:

```python
PI_PACKAGE = "@earendil-works/pi-coding-agent"
PI_PINNED_VERSION = "0.81.1"
def pi_pinned_argv(*args): return ("pnpm", "dlx", "--package", f"{PI_PACKAGE}@{PI_PINNED_VERSION}", "pi", "--", *args)
```

Verificado en vivo: `pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1 pi -- --version` resuelve
exactamente `0.81.1` (pnpm's content-addressed store cachea cada versión; no hay red si ya se resolvió una
vez). Costo medido: ~2.9s de overhead de resolución de pnpm por invocación fría — aceptable frente al costo
propio de un turno de agente (segundos a minutos), y auto-documentado en el doctor.

- **Status** = `set_agents_app.py --doctor --harness pi` (ver Decisión 5).
- **Rollback** = revertir `PI_PINNED_VERSION` en el commit (una línea); pnpm mantiene cada versión resuelta
  en su store de contenido, así que una versión previa sigue disponible sin reinstalar nada. No hay estado
  mutable propio de SET-AGENTES que revertir — a diferencia de `install.py`, no existe un árbol de archivos
  gestionado para Pi (Decisión 4).

## Decisión 4 — target `pi` MÍNIMO en generate/install (sin árbol generado)

El plan original preveía un árbol de agentes Pi generado, análogo a `out/opencode|claude-code|codex/`.
Deliberadamente NO se genera: el prompt canónico de cada rol (`Global/_canonical/agents/<role>.md`, ya
versionado, ya el ORIGEN que los otros tres arneses copian con su propio frontmatter) es en sí mismo un
prompt de sistema válido y se pasa VERBATIM al spawn vía `--append-system-prompt`. "Artefactos de rol
semánticamente equivalentes" (AC-10) se cumple por construcción: es el MISMO archivo, no una copia
derivada que podría divergir.

Consecuencias de esta decisión, documentadas explícitamente para el panel de revisión:
- `generate.py` gana `validate_pi_target(roles)` (llamada desde `validate()`): re-afirma que cada rol activo
  tiene su prompt canónico en disco — la única precondición real de la superficie pi, ya exigida
  implícitamente por `load_roles` para los otros tres arneses, ahora explícita para pi también.
- `install.py` NO gana un target `pi` nuevo: no hay un árbol de archivos por-usuario que este repo deba
  escribir para Pi (a diferencia de `~/.config/opencode`, `~/.claude`, `~/.codex`). El "target" pi es, en la
  práctica, el par (prompt canónico ya trackeado por git) + (`--doctor --harness pi`, que lee directamente
  `~/.pi/agent/` sin necesitar un archivo propio). Este es un desvío literal del texto de AC-10
  ("`install.py` gana un target `pi`") pre-aprobado por el context pack del paquete
  ("install puede registrar pi como target para un marcador de settings/doctor si hace falta, nada más") —
  señalado explícitamente para que el panel de revisión lo escrutine.

## Decisión 5 — `--doctor --harness pi` (AC-09)

`set_agents_app.py --doctor --harness pi --json` imprime un envelope schema-2 redactado
(`set_agents_spawn.doctor()`):

```json
{"schema_version": 2, "ok": true, "command": "doctor",
 "data": {"pinned_version": "0.81.1", "version_ok": true,
          "auth_providers": ["anthropic", "openai-codex"], "list_models_ok": true, "doctor_green": true},
 "warnings": [], "reason_codes": []}
```

- `auth_providers` es el KEY-SET de `~/.pi/agent/auth.json` (nombres de proveedor, nunca valores) — lectura
  vía `routing_core.catalog.pi_auth_provider_keys()`, la MISMA función que usa el probe de catálogo.
- `version_ok` compara la salida exacta de `pi --version` (a través del pin) contra `PI_PINNED_VERSION`.
- `list_models_ok` corre `pi --list-models` (a través del pin) y confirma que produce salida no vacía con
  exit 0 — nunca parsea ni imprime el contenido completo en el doctor (el catálogo sí lo parsea, para
  filtrar modelos, pero el doctor solo reporta el booleano).
- `doctor_green` = los tres anteriores en verde. Exit 0 si verde, exit 1 si no (una observación válida, no
  un error de entrada), exit 2 (`DOCTOR_HARNESS_UNSUPPORTED`) para cualquier `--harness` que no sea `pi` o
  ausente — esta package solo especifica el doctor de pi.

## Decisión 6 — mapa de model-ID (T-305)

- `openai-codex`: IDENTIDAD. `catalog.model` (p.ej. `gpt-5.6-luna`) == Pi `provider/id` verbatim
  (`openai-codex/gpt-5.6-luna`). Cero traducción — verificado en vivo.
- `anthropic`: los nombres cortos del catálogo (`opus`, `sonnet`, `haiku`) se traducen vía
  `routing_core.catalog.PI_MODEL_MAP["anthropic"]`:

  | Catálogo | Pi (canónico) |
  |---|---|
  | `opus` | `claude-opus-4-8` |
  | `sonnet` | `claude-sonnet-5` |
  | `haiku` | `claude-haiku-4-5` |

  Curado alineado con los tiers Claude ya usados por el arnés (auditores=opus-4.8, implementación=
  sonnet-5, mecánico=haiku-4.5); ajustable por el usuario si Pi renombra sus ids. `fable` no está en
  `routes.v1.toml` como modelo de ruta (solo se usa para el propio modelo del orquestador en
  `models.toml`), así que no requiere entrada en el mapa.

## Decisión 7 — flip de `PI_SIMULATION_ONLY` (gateado)

`routing_core/service.py` tenía, línea 132, un `elif facts.selected_runtime == "pi": reason=
"PI_SIMULATION_ONLY"` incondicional — Pi nunca llegaba al chequeo normal de inventario
(`self.inventory.get((runtime, provider))`) que todo otro runtime atraviesa. El flip:

```python
PI_SIMULATION_ONLY = False  # una constante, un lugar, un rollback de una línea
...
elif PI_SIMULATION_ONLY and facts.selected_runtime == "pi": reason="PI_SIMULATION_ONLY"
```

**Condiciones que tuvieron que sostenerse ANTES de este commit** (evidenciadas en
`docs/specs/004-adaptive-dispatch/evidence/P3-implementation.md`):
1. `--doctor --harness pi` en verde (versión pinneada resuelve, ambos pares auditados autenticados,
   `pi --list-models` parsea).
2. Los pares `(pi, openai-codex)` y `(pi, anthropic)` agregados a `_PAIR_COMMANDS` con parsers propios
   (`_parse_pi_models`), probados herméticamente contra formas grabadas Y contra la salida real de
   `pi --list-models` en este entorno.
3. Los guards de la Decisión 2 probados: cada uno con un test dedicado (T-304/AC-11g).
4. El spawner cierra el ciclo completo incluyendo crash⇒failure, probado herméticamente (stub) Y en vivo
   (proveedor inexistente ⇒ exit 1 sin ningún evento JSON ⇒ `failure`).
5. QA en vivo de punta a punta para AMBOS proveedores (decide→dispatch→spawn→terminal con
   `SET_AGENTS_ROUTING_TEST_ROOT`, nunca contra el store de producción).

Con el flip en `False`, una ruta pi sigue pasando por el MISMO chequeo de inventario que codex/claude-code/
opencode: un par pi no probado o no autenticado sigue fallando cerrado como `PROVIDER_UNAUTHENTICATED` —
nunca se autoriza contra un par sin verificar. El flip NO introduce un camino de autorización nuevo; solo
deja de excluir a pi ANTES de llegar al camino que ya existía para los otros tres runtimes.

**Rollback**: revertir la constante a `True` (una línea, un commit) — cierra el carril pi instantáneamente,
sin migración de datos, sin tocar ninguna decisión ya autorizada (las durables ya emitidas siguen su ciclo
de vida normal; nuevas decisiones vuelven a `PI_SIMULATION_ONLY`).

## Invariantes que NO se tocan

Todo lo enumerado en el context pack del paquete (`docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md`,
sección "Invariantes que NO se tocan") se mantiene: núcleo P1 AM-1/AM-2 y SCHEMA=4 intactos salvo el flip
puntual arriba; P2 (variantes OpenCode, gate de coherencia, doctrina) intacto; separación de deberes
(reviewers read-only, ningún hijo pi delega); redacción de `auth.json` (solo key-set, nunca valores);
threat model R3 (adversario in-process/mismo-UID fuera de alcance); ninguna regresión debilitada;
`ai/catalogs/routes.v1.toml` y `roles.tsv` sin tocar (los pares pi se derivan del `_PAIR_COMMANDS`
auditado, no de una fila de catálogo nueva — la fila ya declaraba compatibilidad universal por-provider al
no usar `runtimes`).

## Enmienda — repair R1 (seguridad, 2026-07-27)

El panel de seguridad encontró un HIGH (argv-injection) más hardening items sobre la Decisión 2 y el ciclo
de vida; todos reparados en `ai/scripts/set_agents_spawn.py` y `ai/scripts/routing_core/catalog.py`, con
evidencia completa en `docs/specs/004-adaptive-dispatch/evidence/P3-repair-R1.md`:

- **SEC-A01 (HIGH)** — el `task` no confiable es el positional final del argv y pi pinneado 0.81.1 RECHAZA
  un separador `--` (`Unknown option: --`), así que no hay barrera de fin-de-opciones disponible. Confirmado
  en vivo: un `task` de exactamente `--offline` es consumido silenciosamente por el parser propio de pi como
  flag, nunca llega como texto del mensaje — probando que un token hostil final puede pisar/agregar opciones,
  last-wins. `spawn()` ahora falla cerrado (`TASK_LOOKS_LIKE_FLAG`) ANTES de construir el argv o iniciar
  cualquier subproceso, siempre que `task.lstrip()` empiece con `-`.
- **SEC-A02 (MEDIUM)** — un hijo `GUARD_TOOLS_CODE_RW` tiene `bash`, que puede re-invocar el mismo `pnpm dlx
  ... pi ...` y spawnear sus propios hijos pi, sorteando `--no-extensions` (que solo bloquea la extensión
  pi-subagents, no un re-exec por shell). `route_and_spawn`/`main()` — el único camino de ruteo real que
  este paquete expone — ya NO tienen un parámetro `guard_tools` en absoluto: siempre componen
  `GUARD_TOOLS_READONLY`. `GUARD_TOOLS_CODE_RW` queda como constante documentada para un futuro con sandbox
  de bash (que impida re-invocar pi); solo alcanzable llamando al primitivo `spawn()` directamente, fuera de
  este paquete. Además, `--no-context-files` es ahora incondicional en todo spawn (verificado que pi
  0.81.1 soporta la flag), así que un `spawn_cwd` con AGENTS.md/CLAUDE.md propio nunca se auto-carga.
- **PKG-N01/SEC-A03 (LOW)** — `route_and_spawn` envuelve dispatch→spawn→terminal en un solo bloque: CUALQUIER
  excepción después de la autorización (p.ej. `_run_app_cli`'s `subprocess.run(timeout=60)` lanzando
  `TimeoutExpired`/`OSError`) dispara un cierre best-effort `--route-terminal <run_id> failure` (envuelto en
  su propio try/except, nunca puede volver a lanzar) antes de devolver `failure` — ningún run autorizado
  queda abierto solo porque la orquestación alrededor falló.
- **SEC-A04 (LOW, DiD)** — el SDK expone `modelFallbackMessage`, pero el binario pi 0.81.1 en modo
  `--print --mode json` (el único que usa este spawner) NUNCA lo enhebra al stream JSON de stdout (verificado
  contra el fuente pinneado: solo se pasa a `InteractiveMode`). En cambio, el resolver de modelo de pi SÍ
  imprime a STDERR un texto equivalente ("Using custom model id." / "Could not restore model ...") cuando
  sustituye silenciosamente un modelo real distinto bajo el id pedido — confirmado en vivo con
  `openai-codex/not-a-real-model`: el mensaje del asistente sigue ecoando el id (falso) pedido, así que el
  chequeo `observed == target_id` por sí solo no lo detecta. `spawn()` ahora escanea stderr en TODO spawn
  (no solo en el camino de crash) por estos marcadores y trata su presencia como `model_mismatch`.
- **SEC-A05 (LOW, DiD)** — el hijo hereda `os.environ` completo; el stderr crudo ya no se persiste tal cual
  (`_redact()` cubre formas comunes de secreto — `sk-…`, `Bearer …`, `key=/token=/secret=/password=…` — antes
  de recortar a 500 caracteres, aplicado a los tres campos de detalle: crash stderr, excepción de subproceso,
  y `errorMessage` del turno).
- **PKG-N02 (LOW)** — `probe_inventory` ahora aplica un piso `PI_PROBE_MIN_TIMEOUT_SECONDS = 60.0` (alineado
  con `set_agents_spawn.DOCTOR_TIMEOUT_SECONDS`) SOLO para los pares `pi`, para que un store `pnpm` frío no
  produzca un `PROVIDER_UNAUTHENTICATED` falso por timeout — los otros tres runtimes conservan el timeout
  original del caller.

## Consecuencias

- Pi es ahora un runtime EJECUTABLE real, cuarto carril del despacho adaptativo, seleccionable
  per-spawn entre `openai-codex` y `anthropic` en la MISMA invocación — la única superficie del repo que
  permite esto.
- El costo de este carril es visible y medido: ~3s de overhead de `pnpm dlx` por decisión con cache frío
  (una vez por TTL de 300s), y el propio turno del agente Pi (segundos a minutos, según la tarea).
- El "no generamos un árbol de agentes Pi" es una simplificación real pero también una superficie más
  pequeña para auditar — a costa de que el spawner (Python, `ai/scripts/set_agents_spawn.py`) sea el ÚNICO
  punto donde viven las guardas 002 AC-04 para este runtime; su cobertura de tests es, por diseño, la
  totalidad de la superficie de seguridad de este carril.
- Si Pi cambia su tabla de modelos (renombra `claude-opus-4-8`, por ejemplo), el único archivo a tocar es
  `routing_core/catalog.py`'s `PI_MODEL_MAP` — cambio de una línea, sin tocar el catálogo, el spawner, ni
  la doctrina del orquestador.
