# Context pack — D3-posturas-de-autonomia

Spec: `docs/specs/025-consola-minima-y-flexible/spec.md`, **AC-06, AC-07, AC-08**. Depende de D2.

## Estado medido hoy

### Dónde vive la constante que hay que volver parámetro

La doctrina de autonomía **no está en ningún módulo Python**: es prosa, y está **duplicada en cinco
archivos**, todos fuente de generación.

| Archivo | Secciones | Instalado en |
|---|---|---|
| `Global/_canonical/agents/orchestrator.md` (801 líneas) | `## Question policy` :558 · `## Turn continuity` :607 · `## Tool catalog — resolve first (ADR-0025)` :673 · `## Narración` :697 · `## Spawn economy` :507 · `## Package audit policy` :543 · `## Consult mode` :493 | los 4 árboles, vía `generate.py` |
| `Global/_shared/CLAUDE.md` (101 líneas) | `## Question policy` :57 · turn continuity :73 · `## MCP discipline` :87 | `~/.claude/CLAUDE.md` |
| `Global/_shared/AGENTS.opencode.md` (114) | `## Question policy` :62 · :77 · `## MCP discipline` :101 | `~/.config/opencode/AGENTS.md` |
| `Global/_shared/AGENTS.codex.md` (86) | ídem | `~/.codex/AGENTS.md` |
| `Global/_shared/AGENTS.pi.md` (183) | ídem | `~/.pi/agent/AGENTS.md` |

`AGENTS.md`/`CLAUDE.md` son la **primera línea** de cada `managed-files.txt`
(`Global/{codex,claude-code,pi,opencode}/managed-files.txt:1`); `generate.py:563` los copia desde
`_shared`. Es decir: **la doctrina se hornea en `~` en tiempo de instalación**.

`ai/scripts/coord_policy.py` **no es** donde vive: son 327 líneas de allowlist de comandos bash
(`SAFE` :23, `SAFE_ARGV` :61, `FORBIDDEN_SYNTAX` :134, `ALWAYS_DENY` :140). Gobierna *qué comando
puede correr un agente*, no *cuánto pregunta*. Podría ser un segundo eje de las posturas, pero hoy
no tiene ninguna noción de postura. Verificalo antes de tocarlo.

### El patrón de toggle que ya existe y hay que copiar

`APP_CONFIG = STATE_DIR / "config.toml"` (`set_agents_app.py:48`), con lector `app_config()` :1021,
escritor `write_app_config(**updates)` :1032 (que existe justamente para que nadie pisé el archivo
entero, ver su docstring), predicado `auto_update_enabled()` :1028, y **el toggle de menú completo
ya escrito** en :3578-3581 (`"Togglear auto-update (hoy: on/off)"` → `set_auto_update(...)`), con su
badge en :3559. Ese es el molde exacto de AC-06/AC-07. No inventes otro store.

### Metodologías: qué existe ya

- **TDD estricto**: existe de verdad y es por paquete. `feature-state.py:871` (`create.add_argument("--strict-tdd")`) y :880 (update); default en `feature_state_lib/model.py:316` (`"strict_tdd": False`, "declared by package-planner at create-package time"); parseo en `cli_lifecycle.py:292,318-319`. Skills `Global/_canonical/skills/strict-tdd/` y `strict-tdd-verify/`. ADR-0022.
- **SDD**: skill `Global/_canonical/skills/sdd/SKILL.md`, y es el eje del modo `feature` en `skills/request-triage/SKILL.md:43-55,111`.
- **RDD**: **la spec se equivoca al decir que el harness lo practica "sin nombrarlo"**. La sigla ya está escrita, dos veces, con otra acepción: `skills/strict-tdd/SKILL.md:17` y `skills/strict-tdd-verify/SKILL.md:17` dicen *"Ported from `gentle-ai`'s (Gentleman Programming) **RDD** strict-TDD module"*. AC-08 tiene que **reconciliar**, no estrenar: definir Receipt Driven Development sin contradecir esas dos líneas ni duplicar `strict-tdd`.

## La trampa

**Un toggle en `config.toml` no tiene ningún canal hacia el prompt de un agente.** La postura la
guardás en `~/.local/state/set-agentes/config.toml`; la conducta la dicta un `.md` **estático que
ya se copió a `~/.claude/CLAUDE.md` en el último `./build.sh --install`**. Si la postura se
implementa editando `Global/_shared/*.md` o `_canonical/agents/orchestrator.md`, entonces *cambiar
de postura requiere reinstalar* — y eso no es un toggle, es una variante de build. Y si sólo
escribís el flag en `config.toml` sin canal de lectura, la postura no cambia absolutamente nada:
es el riesgo 3 de la spec, "que las posturas queden decorativas", materializado.

Elegí el canal **antes** de escribir código y dejalo en el ADR. Las opciones que el repo ya
soporta: inyección en el texto de la tarea del spawn (`compose_task`, `claude_code_spawn.py:309`),
lectura del `config.toml` por un flag del CLI que el orquestador ya tiene allowlisted, o
parametrizar la generación. **Las tres tienen costos distintos; ninguna es gratis.**

Segunda trampa, menor pero cara: `Global/_canonical` y `Global/_shared` son **fuente de
generación**. Cualquier edición ahí obliga a `./build.sh --check` → `GLOBAL_TREE_SYNC_OK`; si no
regenerás los árboles derivados, el gate te frena. Y `verify.sh:43-46` exige que toda referencia a
`set_agents_app.py` dentro de los generados use el placeholder `__SET_AGENTS_ROOT__` — contá las
ocurrencias, el check compara cantidades.

## La mordida exigida

La spec lo dice explícito: *cada postura necesita un test que pruebe una diferencia observable.*
Traducido a rojo/verde:

1. **Persistencia**: la postura elegida sobrevive al reinicio del proceso. Rojo trivial pero
   obligatorio — es el único que hoy podés copiar de `auto_update`.
2. **Diferencia observable por postura**: un mismo escenario, corrido en las tres posturas, produce
   **tres resultados distintos y assertados**. Rojo: hacé que las tres devuelvan lo mismo y confirmá
   que el test falla. **Sin este test el paquete es decorativo y el reviewer lo tiene que rechazar.**
3. **El canal llega**: assert de que el texto/parámetro de la postura efectivamente aparece donde el
   agente lo va a leer (lo que hayas elegido: la tarea compuesta, la salida del flag, el prompt
   generado). Rojo: cortá el canal, confirmá el fallo. Este es el que distingue "guardé un booleano"
   de "cambié la conducta".
4. **AC-06 exige la explicación en la propia pantalla**: assert del texto visible, no sólo del valor.

## Restricciones

- **ADR reservado: 0054** (`ls docs/adr/`; 0050 reservado sin escribir por D1, 0052 tomado por
  027/P4, 0053 por D2). Indexalo en `docs/adr/README.md`. El ADR **tiene que nombrar el canal**.
- `owned_paths`: `ai/scripts`, `Global/_canonical`, `tests`, `docs/adr`.
- **No inventes un store nuevo**: `write_app_config` o nada.
- **No reescribas ADR-0025 ni ADR-0037.** Las posturas los **parametrizan**; la postura por defecto
  tiene que reproducir la conducta de hoy, byte por byte. Un default que cambia la conducta actual
  es un cambio de doctrina no aprobado.
- **No dupliques `strict-tdd`** en un toggle nuevo: AC-07 lo **expone**, ya existe (ADR-0022).
- No uses `git checkout`/`restore`/`stash`. No toques nada bajo `~`. Nunca `./build.sh --install`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh` →
`VERIFY_PASS` · **`./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`** (obligatorio en
este paquete: tocás `Global/_canonical`) · `git diff --check`.

**Comandos largos: `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`** (ADR-0041).

## Evidencia

`docs/specs/025-consola-minima-y-flexible/evidence/D3-implementer.md`, primer minuto: tabla AC →
cambio (`archivo:línea`) → prueba; **el canal elegido y por qué, con las alternativas descartadas**;
las tres pantallas de postura pegadas literales; la definición de RDD y cómo se reconcilia con
`strict-tdd/SKILL.md:17`; y las cuatro pruebas de mordida con su rojo. Literal o marcado recortado.

## Fuera de alcance

Menú/flags/`--json` (D1) · spinner (D2) · instalación por CLI (D4) · vault (D5) · el ruteo y el sort
key · reescribir `coord_policy` · cambiar la conducta por defecto del harness.
