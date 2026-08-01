# Feature 013 — pi-interactive-target, contract 1.3.0

Status: `SPEC_CHALLENGE` round 1 (18 findings against contract 1.0.0), round 2 (4 blocking, C-01..C-04, plus
6 non-blocking, N-01..N-06, against contract 1.1.0), and round 3 (5 non-blocking, R3-01..R3-05, against
contract 1.2.0) all returned findings — see `## Historial de challenge` below. Round 3's verdict was
`ready_for_user_approval`: all 5 of its findings were explicitly non-blocking and are fixed in this same
revision rather than warranting a fourth challenge round. All findings from all three rounds are fixed; the 5
round-1 product/security decisions and the round-2 `maxSubagentDepth` decision (N-05) were resolved by the
user and are baked into the affected ACs below as settled, no longer open. Ready for user approval.
Depends on: `docs/adr/0007-pi-lane.md` (Accepted) and `docs/adr/0008-two-roots-portability.md` (Accepted) —
this contract EXTENDS both (a new, separate surface of `pi`) and amends one narrow clause of ADR-0007
Decision 4 (see AC-14) plus, per user decision 4 below, closes one narrow residual-risk clause of ADR-0007
Decision 2's own dispatch-lane argv (see AC-12) — it does not reopen either ADR's own accepted decisions
otherwise. No other feature's approved contract is touched, except for the narrow, named ownership question
AC-12 raises against whichever already-accepted package currently owns `ai/scripts/set_agents_spawn.py`
(verified below — not this feature's own file).

## Origen

The user opened `pi` interactively (not through this harness's dispatch lane) and found a competing product
("gentle-pi"/"gentle-engram", by Gentleman Programming) loaded as global extensions, unrelated to this repo.
It has been removed (`pi remove npm:gentle-pi`, `pi remove npm:gentle-engram` — confirmed absent from
`~/.pi/agent/settings.json`'s `packages` array, read live this session). The real ask behind that report: when
a human opens `pi` interactively, it should load THIS harness's own roles/skills/commands, the same way
OpenCode, Claude Code, and Codex already do — not sit empty, and not load a third party's.

## Historial de challenge

**Ronda 1** — `revision_required`, 18 hallazgos: 3 críticos, 4 altos, 6 medios, 5 bajos.

Críticos: **F-01** (no había ninguna AC de punta a punta que realmente arrancara `pi` y observara la carga
real — todo era existencia de archivo/frontmatter; `pi --help` no tiene subcomando de inspección de skills).
**F-02** (la afirmación de AC-06.2 de que `$ARGUMENTS`/`$@` eran "convenciones disjuntas que requieren
traducción" era FALSA — la propia documentación embebida de `pi`, `docs/prompt-templates.md`, confirma que
`$ARGUMENTS` es un alias NATIVO de `$@` en su motor de templates; además el conteo estaba mal — es 21 de 22
comandos canónicos, no "20 de 22", el único que no usa `$ARGUMENTS` es `status.md`). **F-03** (el spike
bloqueante de AC-05 también era innecesario — `docs/skills.md` documenta `compatibility` como un campo
OPCIONAL e informativo que el loader lenient de `pi` no aplica como filtro de descubrimiento; "unknown
frontmatter fields are ignored").

Altos: **F-04** (AC-04/AC-07 dejaban implícito, sin decidirlo, si `orchestrator.md` convertido a
`Global/pi/agents/orchestrator.md` era o no lo que hace que `pi` interactivo se comporte como orquestador —
`pi-subagents` no tiene ningún equivalente a `mode: primary`, así que la respuesta real depende
enteramente de dónde vive el comportamiento por defecto). **F-05** (`generate.py`'s `validate()` tiene DOS
tuplas de arnés más, además de las ya cubiertas, que necesitan un miembro `"pi"`; y existe una función
`validate_pi_target()` cuyo docstring afirma literalmente lo opuesto de lo que esta feature hace — "pi gets NO
generated agent tree" — dejada así sería un comentario auto-contradictorio en el mismo archivo que este
feature edita). **F-06** (el techo de herramientas de AC-03 comparaba el token abierto `subagent` de pi contra
la lista cerrada `Agent(<27 roles>)` de Claude Code sin decidir si esa divergencia era un gap real o un
desvío deliberado y documentado). **F-07** (AC-06 no decía qué pasa con el campo `agent:` de los 22 comandos
canónicos al convertirlos — silenciosamente descartado, o vuelto una instrucción explícita en el cuerpo — sin
lo segundo, se pierde la garantía de separación de deberes revisor-nunca-se-autoaprueba en el prompt
convertido).

Medios: **F-08** (el Non-goals original nombraba los 12 archivos leftover de `~/.pi/agent/agents/` pero nunca
mencionaba `~/.pi/agent/chains/`, 3 archivos más, ni siquiera para excluirlos explícitamente). **F-09** (AC-11,
hoy AC-14, no exigía la disciplina de enmienda in-file que el propio `docs/adr/README.md` manda para
supersesión parcial — solo una fila nueva para 0017, no una nota dentro de `0007-pi-lane.md` cerca de su
Decisión 4, pese a que ese mismo archivo ya tiene el precedente exacto, `## Enmienda — repair R1`). **F-10**
(AC-01, AC-04 y AC-09 —hoy AC-10— no tenían ninguna cobertura en `## Verificación`, pese a que AC-09 afirma
explícitamente ser "provable, not merely asserted"). **F-11** (la Contexto afirmaba "eleven sections" para
`Global/_shared/AGENTS.codex.md` cuando son doce, y el nombre exacto de la última sección necesitaba
verificación — no coincide entre los tres arneses existentes). **F-12** (el cierre del carril de despacho —
agregar `--no-skills`/`--no-prompt-templates` a `set_agents_spawn.py` — quedaba como "riesgo residual
aceptado, sin dueño ni fecha" en vez de una AC concreta). **F-13** (ninguna AC exigía una guarda de colisión
si el converter de `pi` pisara un archivo preexistente en `~/.pi/agent/agents/` que no fuera del `MANIFEST` de
`install.py` — el primero de los cuatro targets generados donde ese riesgo es real).

Bajos: **F-14** (la Contexto corregía de más: decía que `~/.agents/` no es una ubicación global, lo cual es
correcto para `agents/`, pero `~/.agents/skills/` SÍ es una segunda ubicación global documentada que el
skill-loader de `pi` sí revisa — la corrección necesitaba ser más precisa, no una generalización). **F-15**
(no se dejaba constancia de que la alternativa documentada de `pi` — un puntero en `settings.json` a
`~/.claude/skills` directamente, sin árbol generado — fue considerada y rechazada, ni por qué). **F-16** (la
cita del path global `~/.pi/agent/AGENTS.md` apuntaba a `pi --help`, que solo prueba que la flag existe, no
que ese sea el path — la fuente real es `docs/usage.md`/`docs/quickstart.md`). **F-17** (AC-06 no mencionaba
`argument-hint`, ni si el descubrimiento de `prompts/` es recursivo, y la cita `generate.py:334-384` para el
loop de roles arrancaba una línea antes del `for row in roles:` real). **F-18** (no había sección de Rollback
para AC-08, pese a ser el primer target que escribe en una raíz de `$HOME` completamente nueva).

**Las 5 decisiones de producto/seguridad reales** (no errores de verificación, así que no se "arreglaron" con
una re-lectura — se resolvieron con el usuario, relayed por el coordinador): F-04 → decisión 1 (persona por
defecto de `pi` interactivo — doctrina + contenido operativo del orquestador, ambos embebidos en
`Global/pi/AGENTS.md`); F-07 → decisión 2 (`agent:` se traduce a una llamada `subagent(...)` explícita en el
cuerpo, nunca se descarta); F-06 → decisión 3 (el token abierto `subagent` se acepta como divergencia
deliberada y documentada, no un gap, porque `pi-subagents` ya impone el límite estructural real); F-12 →
decisión 4 (el cierre del carril de despacho se vuelve una AC concreta, con el mecanismo de excepción de
ownership nombrado). Una sexta decisión del usuario, sin hallazgo numerado que la motivara directamente
(surgió de una pregunta operativa aparte, relacionada con F-08's alcance de Non-goals): autorizar el borrado
manual, de una sola vez, de los 12+3 archivos leftover de gentle-ai más su carpeta de soporte, fuera de
cualquier paquete — ver Non-goals.

Todos los 18 hallazgos quedan direccionados en esta revisión; el detalle de "cómo" vive en cada AC afectada
(ver `## Acceptance Criteria`) y se resume, hallazgo por hallazgo, en el reporte que acompaña esta revisión
fuera de este archivo. La numeración de ACs pasa de AC-01..AC-11 a AC-01..AC-14 para sostener el alcance
agregado (AC-09 guarda de colisión, AC-12 cierre de carril de despacho, AC-13 chequeo E2E) — cada AC nueva
o renumerada dice explícitamente, en su propio texto, cuál era su número/contenido en la ronda 1 cuando
aplica.

**Ronda 2** — `revision_required` contra el contrato 1.1.0, 10 hallazgos: 4 bloqueantes (**C-01..C-04**), 6
no bloqueantes (**N-01..N-06**). De los 18 hallazgos de la ronda 1, 16 quedaron confirmados como
genuinamente resueltos por esta ronda (no se tocan en esta revisión); los 4 hallazgos bloqueantes de ronda 2
son gaps nuevos, propios de cómo la ronda 1 resolvió sus propios hallazgos, no hallazgos de ronda 1
reabiertos.

Bloqueantes: **C-01** (AC-02 mandaba borrar `validate_pi_target()`, lo cual viola la regla incondicional de
la doctrina de este repo — "las pruebas de regresión nunca se debilitan, saltean, ni borran para pasar" — ya
que `tests/test_harness.py:3046-3054`
(`test_pi_target_validate_requires_canonical_prompt_per_role`) ejercita esa función directamente; revertido:
`validate_pi_target()` se MANTIENE, firma y lógica sin cambios, único cambio es su docstring, que ya no
contradice el archivo que la contiene — ver AC-02). **C-02** (la enmienda in-file de AC-14 a
`docs/adr/0007-pi-lane.md` estaba acotada a una sola cláusula de la Decisión 4; se amplía a las tres piezas
de esa decisión que quedan falsas — título/premisa, la cláusula de `install.py`, y la consecuencia sobre
`validate_pi_target` —, y se agrega un `feature-state.py log-decision` obligatorio que supere explícitamente
la decisión persistida `ac09-ac10-pi-minimal-target-accepted` (`ai/state/decisions-log.jsonl:14`) y su nota
en `docs/notas/decisiones/2026-07-27 ac09-ac10-pi-minimal-target-accepted.md` — ver AC-14). **C-03** (la
receta de invocación de `pi` de AC-13 colgaba / tocaba red; reemplazada por la receta de dos pasos
verificada en vivo esta sesión — resolver el binario real contra el `$HOME` real con
`pnpm dlx --package @earendil-works/pi-coding-agent which pi`, después invocar ESE path directo bajo pty con
`HOME` scratch, timeout explícito y criterio de éxito por contenido del log, nunca por código de salida — ver
AC-13). **C-04** (AC-03 declaraba invariantes de techo de herramientas sin exigir los campos concretos que
los sostienen; ahora exige que el converter emita siempre `tools` y `systemPromptMode: replace` explícitos
por rol, más `maxSubagentDepth` explícito para el único rol de clase `coord-ro` — ver AC-03).

No bloqueantes: **N-01** (AC-09 ahora dice explícitamente que la guarda de colisión dispara en `--preview` Y
en modo escritura, con mensaje accionable, y nombra la consecuencia operativa sobre el hook `post-commit`).
**N-02** (AC-08 referencia a AC-09 para no leerse como enumeración exhaustiva). **N-03** (AC-06 decide:
el campo `agent:` se elimina del frontmatter emitido, nunca se deja sin traducir). **N-04** (Contexto
corregido: `~/.agents/skills/omarchy` es hoy un symlink roto, no un skill poblado; el riesgo real es futuro
y de shadowing por nombre, no una afirmación sobre contenido actual). **N-05** (AC-03 anota que `coord-ro`
es hoy exactamente un rol, `orchestrator`, y decide pinnear `maxSubagentDepth: 2` explícito para esa clase).
**N-06** (seis citas de línea re-verificadas y corregidas: doctor envelope, líneas de copia de doctrina,
freshness loop, atribución de "name matches directory", guardia `GLOBAL_BARE_APP_CLI` faltante en la
enumeración de AC-11, y comentario desactualizado en `set_agents_spawn.py`). Contrato pasa de 1.1.0 a 1.2.0.

**Ronda 3** — `ready_for_user_approval` contra el contrato 1.2.0, 5 hallazgos, los 5 no bloqueantes
(**R3-01..R3-05**), explícitamente no ameritan una cuarta ronda de challenge. Los 5 quedan arreglados en esta
misma revisión: **R3-01** (el comentario de `tests/test_harness.py:3047-3050` seguía afirmando la premisa
retractada por C-01 — "AC-10/ADR-0007: pi gets no generated tree..."; AC-02 ahora aclara explícitamente que
actualizar ese COMENTARIO en el mismo pase no es "debilitar" la prueba de regresión, solo sus aserciones/
comportamiento están protegidos). **R3-02** (AC-14 era la única AC de `## Verificación` sin línea de
cobertura pese a ser la más grande, 10 sub-ítems, e incluir una mutación de estado obligatoria; se agrega su
bullet con los cuatro chequeos). **R3-03** (la consecuencia de AC-09/N-01 sobre `check-drift.sh` estaba mal
mecánicamente — bajo `errexit`+`pipefail` el script aborta en la línea 21 con el código de salida propio de
`install.py`, nunca llega a la rama `DRIFT_UNKNOWN` de la línea 24; corregido, y el código de salida de la
nueva guarda se fija en `2`, igual que la convención interna existente de `check-drift.sh:14-18` y el
precedente ya real de `install.py`'s `INSTALL_ABORTED_UNSAFE_ROOT`, para no colisionar con el `exit 1` de
`DRIFT_DETECTED`). **R3-04** (la receta de invocación de AC-13 no fijaba el CWD, y el prompt de confianza de
proyecto es CWD-dependiente, no `$HOME`-dependiente; se fija el CWD a un directorio scratch vacío y se
prefiere `--no-approve` sobre `--approve`, misma salida verificada, aislamiento por construcción). **R3-05**
(se documenta en el Audit que AC-13 resuelve su binario `pi` vía `pnpm dlx`, una versión distinta —`0.83.0`—
de la del wrapper interactivo real, `~/.local/bin/pi`, pineado a `0.82.1`; tratado como bajo riesgo, no
cerrado del todo). Contrato pasa de 1.2.0 a 1.3.0.

## Contexto

Three independently confirmed facts anchor this contract, all re-verified live this session (not reused from
an earlier summary without checking):

1. **`pi` (v0.82.1 on this machine's soft-pinned interactive wrapper `~/.local/bin/pi`, confirmed via
   `pi --version`) loads a global context file on interactive start**, the same convention Codex/Claude Code
   already use: `~/.pi/agent/AGENTS.md` plus any project `AGENTS.md`/`CLAUDE.md` found walking up from `cwd`,
   unless `--no-context-files`/`-nc` is passed. **Corrected in this revision (F-16): the citation for this
   global path is not `pi --help`'s option list** (which only proves the flag exists, not the path) **but
   `docs/usage.md:100-102`** ("Pi loads `AGENTS.md` or `CLAUDE.md` at startup from: ... `~/.pi/agent/AGENTS.md`
   for global instructions"), corroborated by `docs/quickstart.md:88-100`, both read directly this session from
   the pinned `0.81.1` package's extracted docs (`~/.local/share/pnpm/store/v11/links/@earendil-works/
   pi-coding-agent/0.81.1/.../docs/`). This is a **different, unrelated version number** from ADR-0007's
   dispatch-lane hard pin (`PI_PINNED_VERSION = "0.81.1"`, `ai/scripts/routing_core/catalog.py`, resolved via
   `pnpm dlx --package @earendil-works/pi-coding-agent@0.81.1`) — the interactive wrapper's soft, release-age
   pin (`PNPM_CONFIG_MINIMUM_RELEASE_AGE=7200` in `~/.local/bin/pi`, a personal dotfile this repo does not
   manage) moves independently of the harness's own hard pin. This contract's ACs never assume a specific
   interactive `pi` version; where a claim depends on version-specific behavior it is stated as
   verified-on-0.82.1, not as a permanent guarantee.
2. **The dispatch lane (ADR-0007) already runs a disjoint flag set on every spawn, confirmed against the real
   code, not the ADR's prose.** `ai/scripts/set_agents_spawn.py:244-248`'s fixed argv is exactly
   `--model <id> --print --mode json --no-session --no-extensions --no-context-files --tools <guard_tools>`
   (flags on lines 245-246 specifically). This is a *different session* from an interactive `pi` invocation:
   `--no-session` (ephemeral, no history), `--no-extensions` (blocks `pi-subagents`, the sole provider of the
   "agent" resource type — see point 3), `--no-context-files` (blocks `AGENTS.md`/`CLAUDE.md` auto-load).
   **This set does NOT include `--no-skills` or `--no-prompt-templates`** — both real, independent flags
   confirmed in `pi --help`'s option list. **Resolved in this revision (user decision 4, was F-12): this is no
   longer left as an accepted residual risk — AC-12 below closes it directly**, by adding both flags to this
   exact argv, subject to the ownership-exception mechanism AC-12 names (this file is not currently inside
   this feature's own `owned_paths`; see AC-12).
3. **`pi` core has no "agents" resource type of its own.** `pi --help`, read live, lists exactly five
   loadable resource families with their own `--no-*` toggle: extensions, skills, prompt-templates, themes,
   and context-files — no "agents" entry anywhere in that list. Live-verified this session (`pi --verbose`
   under a pty, scratch `$HOME`, see AC-13): the interactive startup header renders exactly three discovery
   sections — `[Context]`, `[Skills]`, `[Prompts]` — never an `[Agents]` section, confirming this is not just a
   `--help` claim but the actual observed startup behavior. The concept of a loadable role/agent file comes
   entirely from the separately-installed npm extension `pi-subagents`, confirmed present and enabled in
   `~/.pi/agent/settings.json`'s `packages` array (`"npm:pi-subagents"`, alongside `pi-intercom`,
   `@juicesharp/rpiv-ask-user-question`, `pi-web-access`, `@juicesharp/rpiv-todo`, `pi-btw`,
   `pi-mcp-adapter` — none of these seven are touched by this contract, see Non-goals). `pi-subagents`
   auto-discovers agent files from `~/.pi/agent/agents/**/*.md` (global/user scope) — verified directly from
   its own bundled documentation, `~/.pi/agent/npm/node_modules/pi-subagents/skills/pi-subagents/SKILL.md`,
   section "Discovery and Scope Rules": project scope (`.pi/agents/**/*.md`, plus a legacy project-relative
   `.agents/**/*.md`) wins over user scope (`~/.pi/agent/agents/**/*.md`), which wins over `pi-subagents`'
   own eight builtin agents (`scout`, `planner`, `worker`, `reviewer`, `context-builder`, `researcher`,
   `delegate`, `oracle`, physically installed at `~/.pi/agent/npm/node_modules/pi-subagents/agents/*.md` — a
   *different* directory from this feature's write target, `~/.pi/agent/agents/`, verified live this session;
   see AC-09). The same SKILL.md also confirms, read live (line 735), the real structural boundary that
   matters for AC-03: **"Ordinary children also do not receive the `subagent` extension tool"**, and (line
   613) **"Default subagent nesting depth is 2. Deeper recursive delegation is blocked unless configured
   otherwise."** No frontmatter field in any real agent file read this session (`~/.pi/agent/npm/node_modules/
   pi-subagents/agents/*.md`, and the "Creating and Editing Agents by File" section of the same SKILL.md)
   resembles OpenCode's `mode: primary` or any other "default session persona" concept — confirmed absent, not
   merely unobserved (see AC-04/AC-07, user decision 1). **This corrects an earlier internal claim that
   `~/.agents/` is a second GLOBAL agent directory** — the real documented legacy path is project-relative
   (`.agents/`, no leading `~`), not a home directory alternative, for AGENTS **specifically**; this contract's
   agent install target is exclusively `~/.pi/agent/agents/`. **Narrowed in this revision (F-14): that
   correction does not generalize to skills.** `docs/skills.md`'s own "Locations" section, read live this
   session, lists two GLOBAL skill locations, not one: `~/.pi/agent/skills/` **and** `~/.agents/skills/` (note
   the `skills/` suffix — this is a skills-specific exception to the agents-path correction above, not a
   contradiction of it). Informational, no AC needed (see AC-09's collision guard, which is scoped to the
   `agents/` write target and does not need to widen to cover this): this machine's real `$HOME` already has a
   `~/.agents/skills/` entry, `omarchy` — **corrected in this revision (round 2, N-04): re-verified live this
   session, `~/.agents/skills/omarchy` is a DANGLING symlink** (`-> /home/federico/.local/share/omarchy/
   default/omarchy-skill`, a path that no longer exists — Omarchy was fully removed from this machine, per
   this operator's own memory notes), not a populated skill with a real `SKILL.md` — round 1's "populated"
   framing over-claimed, and round 2's "empty" retraction was itself imprecise (it is neither populated nor
   simply empty; it is a broken pointer to nothing). The real, precisely-stated risk is about the FUTURE, not
   today's content: `docs/skills.md:188`'s documented collision behavior — "Name collisions (same name from
   different locations) warn and keep the first skill found" — means a future, actually-populated entry under
   `~/.agents/skills/<name>` matching one of the 38 canonical skill names would interact with this feature's
   own `~/.pi/agent/skills/<name>` at load time. **Directionality is UNVERIFIED, stated plainly rather than
   assumed:** `docs/skills.md`'s own "Locations" list (`:26-28`) enumerates `~/.pi/agent/skills/` (this
   feature's write target) BEFORE `~/.agents/skills/`, which — if list order equals scan order, itself not
   independently confirmed — would mean this feature's own skill wins a same-name collision, not the reverse;
   the documentation does not state scan order explicitly, so this contract makes no directional claim, only
   that a same-name collision between the two locations is a real, unaudited interaction for a future
   populated `~/.agents/skills/<name>` entry. **This limitation is also stated plainly rather than implied
   away: AC-13's scratch-`$HOME` E2E check does not, and structurally cannot, catch this** — it runs against
   a fully isolated scratch `$HOME` with no `~/.agents/skills/` populated at all, never the real `$HOME`; a
   future collision in the real `$HOME` is outside what any check in this contract observes. This feature's
   skill install target stays `~/.pi/agent/skills/` only, per AC-05/AC-08; `~/.agents/skills/` is never
   written, read, or pruned by this contract.
   `~/.pi/agent/agents/` today already holds 12 leftover `.md` files (`sdd-*.md`, verified live this session:
   `sdd-apply`, `sdd-archive`, `sdd-design`, `sdd-explore`, `sdd-init`, `sdd-onboard`, `sdd-proposal`,
   `sdd-spec`, `sdd-status`, `sdd-sync`, `sdd-tasks`, `sdd-verify`) and `~/.pi/agent/chains/` holds 3 more
   (`sdd-full.chain.md`, `sdd-plan.chain.md`, `sdd-verify.chain.md`), plus a `~/.pi/agent/gentle-ai/support/`
   folder — all from the removed gentle extensions, all still present at spec-writing time (F-08 correction:
   the original Contexto named only the 12 `agents/` files, never `chains/`). **The user has since authorized
   deleting all of this as a one-time manual cleanup, outside this package** (see Non-goals) — untouched by
   this contract's own code either way: `install.py`'s pruning is fenced to files its own `MANIFEST` previously
   recorded writing (`install.py:222-238`), by design never touching pre-existing third-party content, so none
   of these files were ever eligible for automated pruning under the existing D2/D10 doctrine
   (`docs/adr/0008-two-roots-portability.md`) regardless of whether the manual cleanup already ran.

**What already exists on this machine vs. what must be created**, checked live rather than assumed from an
inherited description: `~/.pi/agent/agents/` and `~/.pi/agent/skills/` already exist (the latter empty);
`~/.pi/agent/prompts/` and `~/.pi/agent/AGENTS.md` do **not** currently exist at all. This is not a blocker —
`install.py`'s `atomic_write` already does `path.parent.mkdir(parents=True, exist_ok=True)` (`install.py:209`)
for every managed file it writes, so a missing `prompts/` directory is created on first install, exactly like
every other managed subdirectory today — but it corrects an inherited claim that all four locations "already
exist, empty/minimal," which is only half true.

### Real converter precedent this contract extends (verified against the working tree, not paraphrased)

`ai/scripts/generate.py`'s `generate()` function builds all three existing harness trees inside **one shared
loop over the active roster**. **Corrected in this revision (F-17c): the loop itself, `for row in roles:`, is
at `generate.py:335`, not `:334`** (`:334` is `bodies = {}`, the dict the loop then populates — re-verified by
reading the file directly this session), reading each role's canonical prompt body exactly once
(`body = (CANON / "agents" / f"{row['role']}.md").read_text()`, `generate.py:336`) and writing three sibling
outputs from that same `body`/`desc` pair — OpenCode (`generate.py:339-355`), Claude Code
(`generate.py:357-364`), Codex (`generate.py:366-384`). `CANON` is `Global/_canonical` (`generate.py:16`);
`roles` is the **active roster** returned by `models_config.load_roles(profile, ...)` (`generate.py:57`,
called from `load_roles` at `generate.py:55-61`), not a blind glob of every file physically present under
`Global/_canonical/agents/` — the roster can be a real subset per `roles.tsv`/profile, and this distinction
matters directly to AC-02 below (28 files exist under `Global/_canonical/agents/`, verified by listing the
directory; the pi converter must iterate the same `roles` variable already in scope, not re-glob).

**New in this revision (F-05): `generate.py`'s `validate()` function (`generate.py:513-548`) has a
self-contradicting piece this contract must resolve, not merely extend.** Two of its internal loops hardcode a
harness tuple that needs a fourth `"pi"` member, re-verified against the real current lines (both moved from
the original spec's citations, `:526`/`:535`, which were stale):
- The frontmatter-validation loop, `for harness in ("opencode", "claude-code"): ...` at **`generate.py:527`**
  (checks every `agents/*.md` file starts with valid `---\n...\n---\n` frontmatter).
- The role-set-mismatch guard, `for harness, suffix in (("opencode", ".md"), ("claude-code", ".md"),
  ("codex", ".toml")): ...` at **`generate.py:535`** (checks the generated file stems exactly equal the
  expected roster, per harness).

Separately, `validate_pi_target(roles)` (`generate.py:497-510`, called unconditionally from `validate()` at
`generate.py:548`) has a docstring that literally asserts the opposite of what this contract implements: *"pi
gets NO generated agent tree — ... 'semantically equivalent role artifacts' reduces to: every role the
spawner can address has that canonical prompt on disk ... without duplicating a generated tree."* That was
true under ADR-0007 Decision 4 (dispatch lane, no `install.py` target) and stops being true the moment AC-02
below starts emitting `Global/pi/agents/<role>.md` for real. **Corrected in this revision (round 2, C-01):
`validate_pi_target()` is KEPT, not removed.** Round 1's "remove it, it would be dead code contradicting its
own docstring" reasoning was wrong on the facts: the function is not dead (it is already called
unconditionally at `generate.py:548`, on every `validate()` run) and this repo's own doctrine forbids
deleting a regression test to make a spec pass — `tests/test_harness.py:3046-3054`
(`test_pi_target_validate_requires_canonical_prompt_per_role`) calls `validate_pi_target()` directly and
asserts its exact current behavior (does not raise for a role with a canonical prompt on disk; raises
`ValueError` matching `"pi target"` for one without). Its **signature and per-role logic are unchanged**, so
that test keeps passing unmodified. Only its **docstring is rewritten**: instead of asserting "pi gets NO
generated agent tree" (false the moment AC-02 ships), it must state that this function is the explicit,
pi-target-scoped assertion that every active-roster role's canonical prompt exists on disk — the one source
invariant every generated `Global/pi/agents/<role>.md` file (AC-02's new branch) transitively depends on. This
makes the function non-duplicative of, not redundant work against, the two `validate()` loops AC-02 extends
with a `pi` member: those two loops check the **generated pi output** (frontmatter validity, role-set
completeness); `validate_pi_target()` keeps checking the **source** canonical prompt per role — the same
check `load_roles`'s own `die()` (`generate.py:58-61`) already performs upstream in every code path that
reaches `validate()`, kept here as a second, explicit, pi-target-named assertion rather than folded into or
duplicated by the two extended loops. See AC-02.

Skills are copied identically into all three existing harnesses today by one shared call per harness inside a
loop already keyed off a harness-name tuple: `for harness in ("opencode", "claude-code", "codex"): copy_tree(CANON
/ "skills", out / harness / "skills")` (`generate.py:413-414`). **This corrects an inherited claim that the
copy source is `Global/claude-code/skills/`** — the real source, per the code, is `Global/_canonical/skills`
(`CANON / "skills"`); `Global/claude-code/skills`, `Global/opencode/skills`, and `Global/codex/skills` are
themselves just three copies of it, confirmed byte-identical live this session (`diff -rq Global/_canonical/skills
Global/claude-code/skills` → no output, 38 files each side, same count in all four locations checked).
Commands are copied the same way, one tuple entry short: `for harness in ("opencode", "claude-code"):
copy_tree(CANON / "commands", out / harness / "commands")` (`generate.py:411-412` — Codex does not receive a
commands tree today; not something this contract changes).

The per-harness global doctrine file — **corrected in this revision (F-11): twelve sections, not eleven**
(Reply language, Core invariant, Narration, Living documentation, Separation of duties, Required workflow,
Quality rules, Execution discipline, Question policy, Turn continuity, MCP discipline, Human decision —
re-counted live this session by grepping `^## ` in `Global/_shared/AGENTS.codex.md`, 82 lines, 12 matches) —
is **not one shared file** — it is three independently maintained near-duplicates,
`Global/_shared/AGENTS.opencode.md`, `Global/_shared/CLAUDE.md`, and `Global/_shared/AGENTS.codex.md`, each
copied verbatim by `shutil.copy2` into its own harness's tree (**`generate.py:416-418`, corrected in this
revision from an earlier `:416-419` citation — round 2, N-06b: `:419` is a different file,
`shutil.copy2(SHARED / "config.codex.snippet.toml", ...)`, not a fourth doctrine-file copy**). The exact
final-section
name is **not** identical across the three: `AGENTS.codex.md`'s is `## Human decision`, `CLAUDE.md`'s is
`## Human decision required` — both verified live this session by reading each file directly, correcting an
earlier ambiguous claim that assumed one name without checking both. Diffing `AGENTS.codex.md` against
`CLAUDE.md` live shows real wording drift between them (91 diff lines) even though both carry the same
twelve-section doctrine — they are not required to be byte-identical, only substantively equivalent. This is
the real precedent AC-07 follows: a **fourth** near-duplicate, not a shared/refactored single source (no
opportunistic refactor of the existing three) — see AC-07 for what, per user decision 1, this fourth file must
additionally carry beyond the twelve-section doctrine.

## Alcance

In scope, all inside `Global/pi/**` (a new tree, generated and tracked exactly like `Global/opencode/**`,
`Global/claude-code/**`, `Global/codex/**` already are) plus the install-time wiring that puts it under
`~/.pi/agent/`, plus the two narrowly-scoped items outside `Global/pi/**` user decisions 1 and 4 require:

- A fourth converter branch in `generate.py`'s existing per-role loop, emitting
  `Global/pi/agents/<role>.md` for every role in the active roster, pi-subagents-compatible frontmatter,
  canonical body reused verbatim, plus a corrected (not removed — round 2, C-01) docstring for
  `validate_pi_target()` (AC-02, AC-03, AC-04).
- Extending the existing `copy_tree(CANON / "skills", ...)` call to a fourth harness, `Global/pi/skills/**`
  (AC-05) — no longer gated on a compatibility spike (resolved, see AC-05).
- A new prompts converter, `Global/_canonical/commands/*.md` → `Global/pi/prompts/*.md`, including the
  `agent:` → explicit `subagent(...)` body instruction per user decision 2 (AC-06).
- A new fourth doctrine file, `Global/_shared/AGENTS.pi.md` → `Global/pi/AGENTS.md`, carrying BOTH the
  twelve-section generic doctrine AND the orchestrator's own operating content per user decision 1 (AC-07).
- A fourth `install.py` target, `pi` → `~/.pi/agent` (AC-08), including a collision guard for the one
  write target with real pre-existing third-party content risk (AC-09, new).
- The two freshness/portability guards that must (or must not) change to keep `Global/pi/**` from silently
  drifting (AC-11).
- **New, per user decision 4:** the two-flag dispatch-lane closure on `set_agents_spawn.py` (AC-12) — outside
  `Global/pi/**`, and, as named there, likely outside this feature's own `owned_paths` too.
- **New, per F-01:** a real end-to-end check that starts `pi` and observes real loading, not just static
  file/frontmatter checks (AC-13).
- A new ADR, `docs/adr/0017-pi-interactive-target.md`, skeleton only, plus the required in-file amendment to
  `docs/adr/0007-pi-lane.md` (AC-14).

## Non-goals (explicit, so a later package does not assume them included)

- **`pi-subagents`, `pi-intercom`, `@juicesharp/rpiv-ask-user-question`, `pi-web-access`,
  `@juicesharp/rpiv-todo`, `pi-btw`, `pi-mcp-adapter`** — all seven stay exactly as currently installed
  (verified live in `~/.pi/agent/settings.json`). Nothing here installs, removes, updates, or reconfigures any
  of them.
- **`ai/scripts/set_agents_spawn.py`'s dispatch-lane argv is modified in exactly one, narrow way, and only via
  AC-12 — not "in any way" as an earlier revision of this Non-goal claimed.** AC-12 adds exactly two flags,
  `--no-skills`/`--no-prompt-templates`, to the fixed argv at `set_agents_spawn.py:245-246`; nothing else in
  that file changes, and no other file's spawn-time behavior changes. This is the one item in this contract
  that reaches outside `Global/pi/**`/`~/.pi/agent/` and, per the ownership check in AC-12, is very likely
  outside this feature's own `owned_paths` — package-planning must resolve that via the mechanism AC-12 names
  before implementing it, not silently assume it is included in whatever package implements the rest of this
  contract.
- **No `Global/pi/themes/` target** — `pi --help` lists a themes resource family with its own
  `--no-themes` toggle, and nothing requested a themes surface; out of scope.
- **Nothing inside `~/.pi/agent/npm/`** — that directory is `pi`'s own package-manager-owned tree.
- **No cleanup of the leftover gentle-extension files sitting in `~/.pi/agent/`** as PART OF this contract's
  own logic — `install.py`'s pruning is fenced to files its own `MANIFEST` previously recorded writing
  (`install.py:222-238`), by design never touching pre-existing third-party content; none of these files were
  ever written by this installer and none is eligible for pruning under the existing D2/D10 doctrine
  (`docs/adr/0008-two-roots-portability.md`). **Corrected in this revision (F-08 + user decision 5): this
  covers all three locations, not just the 12 files in `agents/`** — `~/.pi/agent/agents/`'s 12 `sdd-*.md`
  files, `~/.pi/agent/chains/`'s 3 `sdd-*.chain.md` files, and the `~/.pi/agent/gentle-ai/support/` folder (all
  three confirmed still present live this session). **The user has separately authorized deleting all of this
  as a one-time, manual cleanup action outside this package** — parallel to the earlier
  `pi remove npm:gentle-pi`/`npm:gentle-engram` step, and deliberately NOT implemented as new logic inside
  `install.py`: ADR-0008 D2's pruning fence exists specifically to never delete content the installer didn't
  itself write, and a generic "delete anything named `sdd-*`" rule would be exactly the wrong, fragile
  invariant to add to that machinery for a one-time, already-decided cleanup. No AC in this contract covers
  this removal; it is not this package's work item.
- **No extension of `--doctor --harness pi`** (**corrected in this revision — round 2, N-06a: the envelope's
  CLI entry point is `ai/scripts/set_agents_app.py`'s `cmd_doctor` (`set_agents_app.py:602`), not
  `set_agents_spawn.py`** — `cmd_doctor` calls `set_agents_spawn.doctor()` (`set_agents_spawn.py:132`) for
  the redacted data payload, but the envelope itself, ADR-0007 Decision 5, is owned and printed by
  `set_agents_app.py`) to also check the interactive wrapper's version or the new
  `~/.pi/agent/{agents,skills,prompts,AGENTS.md}` tree — that envelope is contractually byte-identical per
  ADR-0008's Implementer Contract item 3 (`docs/adr/0008-two-roots-portability.md`: "the `--doctor --harness
  pi` envelope is BYTE-IDENTICAL. Zero branches added to `cmd_doctor`"); this contract does not touch it, and
  any future doctor coverage for the interactive surface is a separate decision.
- **No opportunistic merge of the three existing `Global/_shared/AGENTS.*.md`/`CLAUDE.md` doctrine files into
  one shared source** — the fourth file this contract adds follows the SAME three-near-duplicates precedent,
  not a refactor of it.

## Acceptance Criteria

- **AC-01 — the interactive surface and the dispatch lane stay two different sessions with two different flag
  sets; the gap between them is named AND, per user decision 4, closed within this same contract.** `pi`'s
  interactive load path (this contract) and ADR-0007's dispatch-lane spawn path (`set_agents_spawn.py:244-248`)
  never collide because they are literally different process invocations with different flags — confirmed
  live: the dispatch lane passes `--no-session --no-extensions --no-context-files`, which is unrelated to and
  does not interact with `Global/pi/AGENTS.md` or `Global/pi/agents/**` (context-files and extensions are both
  blocked there). **Resolved in this revision (was an accepted residual risk in round 1; F-12/user decision
  4):** the dispatch lane's argv does **not currently** pass `--no-skills`/`--no-prompt-templates` (verified
  absent from `set_agents_spawn.py:245-246`), so once `Global/pi/skills/**` and `Global/pi/prompts/**` are
  installed under `~/.pi/agent/`, every dispatch-lane `pi` child would auto-discover and load them too —
  adding this harness's own skill catalog and prompt library into a session ADR-0007 designed to be minimal
  and auditable. This is **not** a guard violation under ADR-0007 Decision 2's threat model (skills and
  prompt-templates grant no new tool, argv, cwd, or env access — the four guards in that table are untouched),
  only added context weight and content the dispatch lane's original design never accounted for — but it no
  longer stays an open follow-up: **AC-12 below closes it directly**, adding both flags to the same fixed argv,
  subject to the ownership-exception mechanism AC-12 names (the file is very likely outside this feature's own
  `owned_paths` today).
- **AC-02 — a fourth converter branch inside the existing per-role loop, not a new pass, plus a corrected
  (not removed) validation function.** Inside `generate.py`'s `for row in roles:` loop
  (**`generate.py:335-384`**, corrected from an earlier `:334-384` citation that pointed one line too early —
  see "Real converter precedent" above), alongside the existing OpenCode/Claude-Code/Codex writes, add a `pi`
  branch that reuses the SAME `body` (`generate.py:336`) and `desc` (`generate.py:338`) already computed for
  that role — never a second read of the canonical file, never a divergent copy — and writes
  `Global/pi/agents/<role>.md` (via the generated-output staging root, same pattern as the other three:
  `out / "pi/agents" / f"{row['role']}.md"`). The mkdir loop at `generate.py:331-332`
  (`for harness in ("opencode", "claude-code", "codex"): (out / harness).mkdir(parents=True)`) gains a fourth
  member, `"pi"`. `write_indexes()` (`generate.py:287-291`), which produces the `managed-files.txt` AC-08's
  installer reads, gains the same fourth member in its own hardcoded tuple. The role set covered is the
  **active roster** (`roles`, from `models_config.load_roles`), the same set already iterated for the other
  three harnesses — not a separate glob over `Global/_canonical/agents/*.md`'s 28 files, which can exceed the
  active roster per profile. **New in this revision (F-05):** `validate()`'s frontmatter-validation loop
  (`generate.py:527`) and role-set-mismatch guard (`generate.py:535`) each gain a fourth `"pi"` tuple member,
  checking the real generated `Global/pi/agents/*.md` output the same way the other three harnesses already
  are checked. **Corrected in this revision (round 2, C-01): `validate_pi_target(roles)`
  (`generate.py:497-510`) and its call site (`generate.py:548`) are KEPT, not removed** — round 1's removal
  plan was wrong: the function is not dead code (it already runs on every `validate()` call) and this repo's
  own doctrine forbids deleting a regression test to make a spec pass; `tests/test_harness.py:3046-3054`
  (`test_pi_target_validate_requires_canonical_prompt_per_role`) calls `validate_pi_target()` directly and
  must keep passing unchanged. Its signature and per-role canonical-prompt-existence logic are untouched;
  only its **docstring** is rewritten, since its current premise ("pi gets NO generated agent tree ...
  without duplicating a generated tree ... no per-user pi settings surface this repo owns") is false the
  moment this AC ships. The corrected docstring states that this function is the explicit, pi-target-scoped
  assertion that every active-roster role's canonical prompt exists on disk on the SOURCE side — the
  invariant every generated `Global/pi/agents/<role>.md` file transitively depends on — distinct from, and
  not duplicated by, the two `validate()` loops just extended above, which check the GENERATED pi output
  (frontmatter validity, role-set completeness) rather than the source. This is the same check `load_roles`'s
  own `die()` (`generate.py:58-61`) already performs upstream in every path that reaches `validate()`; kept
  here as a second, explicit, pi-named assertion rather than folded into the two extended loops (see "Real
  converter precedent" for the full argument). **New in this revision (round 3, R3-01) — "must keep passing
  unchanged" governs the test's assertions and runtime behavior only, not a ban on touching the file at
  all.** `tests/test_harness.py:3047-3050`, the comment directly above this test's body, still asserts the
  exact retracted premise this same AC's docstring fix removes ("AC-10/ADR-0007: pi gets no generated tree —
  its 'role artifact' IS the canonical prompt..."). In the same pass that rewrites `validate_pi_target()`'s
  docstring, this test's COMMENT is updated to stop asserting that retracted premise. Editing a stale comment
  is not "weakening" a regression test under this repo's doctrine — only its assertions and behavior are
  protected, and both stay byte-for-byte identical (the two `assertRaisesRegex`/direct-call lines, unchanged);
  leaving the comment self-contradicting the docstring it sits next to would itself be a defect. Stated
  explicitly so a future implementer does not misread "test stays unchanged" as "do not touch this file."
- **AC-03 — pi-subagents-compatible frontmatter, minimum required fields, and a tool ceiling whose
  delegation-breadth divergence is now a settled, documented decision, not an open gap.** Verified directly
  against `pi-subagents`' own bundled agent files (`~/.pi/agent/npm/node_modules/pi-subagents/agents/worker.md`,
  `.../researcher.md`) and its "Creating and Editing Agents by File" documentation section
  (`.../skills/pi-subagents/SKILL.md`): the only two REQUIRED fields are `name` and `description`; real,
  observed optional fields include `model`, `thinking`, `systemPromptMode`, `inheritProjectContext`,
  `inheritSkills`, `tools` (a comma-separated lowercase list — observed values: `read, grep, find, ls, bash,
  edit, write, contact_supervisor`, and separately `read, write, web_search, fetch_content,
  get_search_content, intercom`), `output`, `defaultProgress`, `defaultReads`, `fallbackModels`,
  `maxSubagentDepth`, `package`. `name`/`description` are populated exactly like the existing Claude Code
  branch already does (`row['role']`, `json.dumps(desc)`, `generate.py:358`) — a JSON string literal is also
  valid YAML flow scalar, the same technique, no new risk. **The invariant this AC requires:** a pi role's
  `tools` grant must never be WIDER than that same role's Claude Code `tools` grant (`claude_tools()`,
  `generate.py:247-255` — four shapes: `"Read, Bash"` for `local-gate-runner`; `"Read, Grep, Glob, Bash,
  Agent(<names>)"` for `coord-ro`; `"Read, Grep, Glob, Bash"` for every read-only/gate/release/run capability;
  `"Read, Grep, Glob, Edit, Write, Bash"` otherwise). **Resolved in this revision (was F-06, now user decision
  3 — the "UNVERIFIED for architecture" framing on this specific point is removed):** for `coord-ro`-class
  roles, pi's own delegation concept — the `subagent` tool, granted as a bare, open token with no observed
  per-name restriction syntax — is genuinely WIDER in shape than Claude Code's closed `Agent(<27 roles>)`
  allowlist. This is accepted as a **documented, deliberate divergence, not a gap**, because `pi-subagents`
  itself enforces a hard structural boundary at the engine level, independent of any allowlist: read live this
  session from its own SKILL.md — "Ordinary children also do not receive the `subagent` extension tool" (line
  735) and "Default subagent nesting depth is 2. Deeper recursive delegation is blocked unless configured
  otherwise" (line 613). An ordinary (non-fanout) child spawned under a `coord-ro` role's own delegation simply
  has no `subagent` tool at all, regardless of what the parent's frontmatter token grants; a child explicitly
  built as a fanout agent is still depth-capped. **The real, narrower invariant that now holds, replacing
  "never wider than Claude Code's tools list" as an absolute:** no NEW capability CLASS is granted to any pi
  role beyond what that same role already has in Claude Code — no direct filesystem/bash/network tool crosses
  from a Claude Code `coord-ro` grant (`Read, Grep, Glob, Bash`) to a pi grant that lacks it, and vice versa;
  only the delegation-BREADTH axis differs (open `subagent` token vs. a closed named allowlist), and that
  specific axis is the one this AC now accepts as diverging, for the structural reason above. **Still
  UNVERIFIED for architecture, unresolved by any user decision:** the exact pi-tool-name equivalents for
  `Glob` (observed pi vocabulary has `find`/`ls`, not a single `Glob`-equivalent token) — the requirement is
  that no filesystem/bash/network capability class widens, not a specific string mapping table, which this
  pass does not have primary evidence to assert.

  **New in this revision (round 2, C-04) — the converter must ALWAYS emit the fields the invariants above
  actually depend on; `name`/`description` alone are not enough.** Round 1 stated the tools-ceiling and
  `systemPromptMode` concerns as prose invariants without requiring the converter to emit the frontmatter
  fields that make them hold. This is a real gap, verified live this session: `pi-subagents`' own
  `README.md:472` states plainly, **"If `tools` is omitted, `pi-subagents` does not pass `--tools`, so the
  child gets Pi's normal builtin tools"** — and `pi`'s own `docs/usage.md:214` lists that default set as
  **"`read`, `bash`, `edit`, `write`, `grep`, `find`, `ls`"**, i.e. the FULL set, `edit`/`write` included. An
  omitted `tools` field is therefore not a neutral default — it silently blows this AC's own never-wider-than-
  Claude-Code ceiling for every `review-ro`/`run-ro`-class role (whose Claude Code grant is `Read, Grep, Glob,
  Bash`, no `Edit`/`Write`). Concretely, this AC (the converter's required-output-fields list) now requires,
  for every role, in addition to `name`/`description`:
  1. **`tools`** — always present, never omitted, populated per the ceiling invariant above (exact
     pi-tool-name mapping remains UNVERIFIED for architecture, per the `Glob`-equivalent note above; the
     requirement is that the field is present and non-widening, not a specific string).
  2. **`systemPromptMode: replace`** — always present, never omitted. **Verified live this session, and
     re-verified past what round 1/round 2's own citation checked:** `pi-subagents`' `SKILL.md:528`/`:570`
     show `replace` used in its own worked examples, and separately `README.md:456` documents `replace` as
     already the DEFAULT when the field is omitted ("`systemPromptMode` — `replace` by default; `append`
     keeps Pi's base prompt"). This means an omitted field is not, on the evidence found, currently unsafe the
     way an omitted `tools` field is — but `SKILL.md` (the document this AC's frontmatter-shape claims are
     otherwise sourced from) never states that default itself; only `README.md`'s separate table does. Pinning
     `systemPromptMode: replace` explicitly is therefore required as a defensive, self-documenting
     redundancy — cheap, and it removes any dependency on an unstated-in-the-cited-source default that could
     change — not because the current default is unsafe. Either way, the emitted value must make the canonical
     role body fully REPLACE pi's generic assistant persona, never be appended to it: critical for e.g.
     `package-reviewer`, where an appended body would leave pi's generic implementer-flavored default persona
     bleeding through underneath a read-only reviewer's instructions, contradicting separation of duties.
  3. **`maxSubagentDepth: 2` — required, but only for `coord-ro`-capability roles** (per N-05 below,
     `roles.tsv`'s `coord-ro` class is, at time of writing, exactly one role: `orchestrator`). This pins, in
     the emitted frontmatter, the exact depth cap `pi-subagents`' own SKILL.md documents as its current
     default ("Default subagent nesting depth is 2", line 613) rather than silently relying on that default
     staying in place — the accepted delegation-breadth divergence above (open `subagent` token vs. Claude
     Code's closed allowlist) leans structurally on this cap, so making it explicit and contractual, not just
     assumed, is a cheap way to keep that acceptance robust. Non-`coord-ro` roles do not need this field: per
     the ceiling invariant above, they never receive the `subagent` tool at all, so a depth cap on a tool they
     do not have is moot.
- **AC-04 — `orchestrator.md` flows through the same converter as every other role; no special-casing — but
  this is NOT what makes interactive `pi` behave as orchestrator, and this AC must not be read as claiming
  that.** `pi-subagents` has no `mode: primary`/"default session agent" concept in its frontmatter (none of
  the fields enumerated in AC-03 relate to it, and none of the fields in its own "Creating and Editing Agents
  by File" section — `name`, `package`, `description`, `model`, `thinking`, `tools`, `systemPromptMode`,
  `inheritProjectContext`, `inheritSkills`, `defaultProgress`, `defaultReads`, `output`, `fallbackModels`,
  `maxSubagentDepth` — resembles one, confirmed by reading the section directly this session) — a
  `pi-subagents` agent file is always a launchable CHILD, invoked via the `subagent(...)` tool or a human
  `/run <name>`, never the interactive session's own default persona. **Resolved in this revision (was F-04,
  now user decision 1):** that default persona role is served EXCLUSIVELY by `Global/pi/AGENTS.md` (AC-07),
  loaded automatically on every interactive start unless `-nc` is passed — converting `orchestrator.md` into
  `Global/pi/agents/orchestrator.md` anyway is still required by this AC, but purely to mirror the existing
  precedent exactly (it grants no special interactive-default behavior by itself): OpenCode ALREADY emits both
  a global `AGENTS.md` doctrine file (`generate.py:416`) AND a separate `agents/orchestrator.md` agent file
  with `mode: primary` (`generate.py:339-355`); Claude Code ALREADY emits both `CLAUDE.md`
  (`generate.py:417`) AND `agents/orchestrator.md` (`generate.py:357-364`). Pi's fourth copy is the same
  redundant-looking-but-already-established pattern, not a new one, and AC-02's roster loop does not
  special-case it BY NAME either way — `orchestrator` is not excluded from AC-02's roster loop, and no
  frontmatter field it receives is keyed off it being specifically `orchestrator`. **Clarified in this
  revision (round 2, C-04/N-05): this does not mean `orchestrator`'s emitted frontmatter is byte-identical in
  shape to every other role's** — like every other role, its fields are driven by its `capability` column
  (`coord-ro`, per `roles.tsv`, currently matched only by `orchestrator` — see AC-03/N-05), which is why it
  alone carries an explicit `maxSubagentDepth: 2`. That is class-driven differentiation, the same mechanism
  `claude_tools()` already uses to vary the Claude Code `tools` grant by capability today, not
  interactive-default/`mode: primary`-equivalent special-casing of the role by name — the distinction this AC
  exists to draw.
- **AC-05 — skills copy, now UNBLOCKED; the compatibility spike is retracted, not merely resolved
  favorably.** Extend the existing tuple at `generate.py:413-414` (`for harness in ("opencode", "claude-code",
  "codex"): copy_tree(CANON / "skills", out / harness / "skills")`) with a fourth member, `"pi"`, landing at
  `Global/pi/skills/**`, byte-identical to the other three by construction (`copy_tree` is `shutil.copytree`,
  no transformation, `generate.py:282-284`). **Resolved in this revision (was a blocking round-1 spike, now
  F-03): `docs/skills.md`, read live this session from the pinned `0.81.1` package's extracted docs, settles
  the question directly — `compatibility` is documented as an OPTIONAL, informational field ("Max 500 chars.
  Environment requirements.") and the Validation section states plainly: "Unknown frontmatter fields are
  ignored," listing only three things that produce warnings (oversized/invalid `name`, oversized
  `description`) and one hard exclusion (missing `description`) — `compatibility` is not among any of them.**
  `grep -rl "^compatibility:" Global/_canonical/skills/*/SKILL.md` returns **36 of 38** files, every one
  declaring the identical value `compatibility: opencode` — this value is now confirmed to be purely
  informational metadata for `pi`'s lenient Agent-Skills-spec loader, never an enforced discovery filter, so
  installing these 36 files verbatim under `~/.pi/agent/skills/` does not exclude any of them. No live
  compatibility smoke test is required before implementation; the straight copy ships as originally hoped,
  zero code beyond the tuple extension. The static checks the round-1 challenger already ran remain this AC's
  concrete verification: 38/38 skills have valid `description`, valid name pattern, no oversized description,
  and — **relabeled in this revision (round 2, N-06d): "name matches directory" is this feature's OWN,
  stricter internal consistency check, not a `pi`-imposed requirement.** `docs/skills.md:143` states plainly,
  in its frontmatter fields table, that `pi` "does not require this to match the parent directory because
  that standard requirement is suboptimal for shared skill directories," restated at `docs/skills.md:157`;
  the earlier citation of `:154` (a mid-list bullet, "Lowercase letters, numbers, hyphens only," not the
  actual "does not require" sentence) was imprecise. This AC keeps the check anyway as a self-imposed
  consistency guard over `Global/_canonical/skills/**`, unrelated to `pi`'s own loader behavior — F-01's new
  end-to-end AC, AC-13, separately covers the higher-level "does it actually load" question with a real
  `pi --verbose` session.
- **AC-06 — a new prompts converter, with both translation questions now resolved, not open.** New converter:
  `Global/_canonical/commands/*.md` → `Global/pi/prompts/*.md`, one output file per canonical command
  (22 files, verified by listing `Global/_canonical/commands/`; discovery of `prompts/` is confirmed
  **non-recursive** per `docs/prompt-templates.md`'s own "Loading Rules" section, read live this session —
  irrelevant here since this converter's output is a single flat directory of 22 files with no subdirectories
  needed).
  1. **`agent: <role>` — resolved (was F-07, now user decision 2): folded into the prompt BODY as an explicit
     instruction, never dropped silently.** All 22 of 22 canonical commands declare an `agent:` field
     (verified: `grep -l "^agent:" Global/_canonical/commands/*.md | wc -l` → 22 of 22). `pi`'s own prompt
     frontmatter carries no `agent`/role-binding key (confirmed absent from all seven real
     `pi-subagents`-bundled prompt files and from `docs/prompt-templates.md`'s own Format section) — a pi
     prompt is a canned starting message for the CURRENT session, never bound to a subagent by its own
     frontmatter. This preserves the reviewer-never-self-approves separation-of-duties invariant, which a
     silently-dropped role binding would erode. The real, verified `subagent(...)` call shape (read live this
     session from `pi-subagents`' own SKILL.md, "Single agent" example, line 237-240):
     ```typescript
     subagent({ agent: "<role>", task: "..." })
     ```
     The converter must inject an explicit instruction into the body of every converted prompt whose canonical
     command declares `agent: <role>`, directing the model to invoke `subagent({ agent: "<role>", task: ... })`
     for that role. This makes the converted prompt's correct behavior depend on `pi-subagents` being
     active — already true today for `Global/pi/agents/**` (AC-02/AC-04), not a new dependency this AC
     introduces, but worth stating explicitly since a prompt (unlike an agent file) can in principle be used
     with `--no-extensions`, in which case the instruction would have no `subagent` tool to call.
     [UNVERIFIED for architecture: the exact injected wording/placement in the body — the requirement is that
     the instruction is explicit and present, not silently dropped, not the literal string.]

     **New in this revision (round 2, N-03): the emitted `Global/pi/prompts/*.md` frontmatter STRIPS the
     `agent:` key** — it is never carried through, even alongside the body instruction above.
     `docs/prompt-templates.md`'s own Format section, read live this session, documents exactly two
     recognized prompt-frontmatter fields, `description` (optional, defaults to the first non-empty line) and
     `argument-hint` (optional, autocomplete display only) — no `agent`/role-binding key is part of the
     documented format. Leaving an unrecognized `agent:` key in the emitted frontmatter would be untested
     behavior against `pi`'s loader (round 1 already confirmed unknown frontmatter fields are lenient-ignored
     for SKILL.md; the prompt-template loader's own tolerance for an unrecognized key is not independently
     verified anywhere in this contract). Stripping costs nothing (the role binding already lives, explicitly,
     in the body instruction above — the only place `pi-subagents` can act on it) and avoids relying on
     unverified loader leniency for a key that carries no function in `pi`'s prompt format.
  2. **The argument-placeholder token needs NO translation — resolved (was F-02, a blocking spike; now
     retracted entirely, the earlier "disjoint conventions" claim was wrong).** `docs/prompt-templates.md`'s
     own "Arguments" section, read live this session from the pinned `0.81.1` package's extracted docs, states
     directly: "`$1`, `$2`, ... positional args" and **"`$@` or `$ARGUMENTS` for all args joined"** — `pi`'s
     template engine treats `$ARGUMENTS` as a NATIVE alias for `$@`, not a foreign convention requiring
     translation. **Corrected count (re-verified live this session): 21 of 22 canonical commands use the
     literal token `$ARGUMENTS`** (`grep -L '\$ARGUMENTS' Global/_canonical/commands/*.md` → exactly one file
     lacks it, `status.md`) — not "20 of 22" as an earlier revision claimed. No literal token substitution, no
     live spike, and no translation logic is required for this converter; `$ARGUMENTS` copies through
     verbatim and `pi` resolves it exactly as `$@`.
  3. **New in this revision (F-17a/b):** `argument-hint` is a real, optional pi prompt-template frontmatter
     field, documented in `docs/prompt-templates.md`'s own Format/Argument-Hints sections (shown in
     autocomplete, e.g. `argument-hint: "<PR-URL>"`) — this converter does not populate it from anything
     canonical (no equivalent field exists on the 22 canonical commands), named here so a future reader does
     not wonder whether it was missed.
- **AC-07 — a fourth, independent doctrine file, `Global/_shared/AGENTS.pi.md`, that additionally embeds the
  orchestrator's own operating content — this IS what makes interactive `pi` behave as orchestrator by
  default, with no extra step.** A new file is created carrying, first, the same doctrine substance verified
  present in the three existing files (Reply language, Core invariant, Narration, Living documentation,
  Separation of duties, Required workflow, Quality rules, Execution discipline, Question policy, Turn
  continuity, MCP discipline, Human decision — **twelve sections, corrected from an earlier "eleven," read in
  full from `Global/_shared/AGENTS.codex.md`, 82 lines**), copied verbatim by `generate.py` into
  `out/pi/AGENTS.md` via the exact same `shutil.copy2` pattern as its three siblings (**`generate.py:416-418`,
  corrected in this revision from an earlier `:416-419` citation — round 2, N-06b: `:419` copies a different
  file, `config.codex.snippet.toml`, not a fourth doctrine file — one new line added after `:418`**). This
  fourth file's exact final-section name is not required to match
  either existing file's exactly (`AGENTS.codex.md` uses `## Human decision`, `CLAUDE.md` uses `## Human
  decision required` — both real, both verified live, neither one canonical), matching the existing
  substantively-equivalent-not-byte-identical precedent (91 `diff` lines between `AGENTS.codex.md` and
  `CLAUDE.md`, verified live). **New in this revision (was F-04, resolved as user decision 1):** this file
  ALSO carries the orchestrator's own operating content — question policy, spawn economy, narration registers
  (`Cliente:`/`Ingeniería:`) — sourced from `Global/_canonical/agents/orchestrator.md`'s own canonical body
  (real sections confirmed present there this session: `## Spawn economy — hard rules` at line 308,
  `## Question policy` at line 356, `## Narración — protocolo de transparencia` at line 447, `## Delegation
  flow`/`### Tiered dispatch` at lines 123/160, `## Turn continuity` at line 382, `## Consult mode` at line
  296, `## Hard boundary` at line 438). This is what resolves F-04 concretely: opening `pi` interactively puts
  the human straight into orchestrator behavior with **no extra step**, because `Global/pi/AGENTS.md` — not
  `Global/pi/agents/orchestrator.md` (AC-04) — is the file `pi` loads automatically on every interactive start.
  Do **not** rely on `Global/pi/agents/orchestrator.md` having any `mode: primary`-equivalent field; none
  exists in `pi-subagents`, confirmed (see AC-04). [UNVERIFIED for architecture: the exact selection and
  wording of which orchestrator sections/how much of their content is folded in verbatim vs. summarized — the
  requirement is that the resulting file's operating content is sufficient for interactive `pi` to actually
  behave like the orchestrator (question policy, spawn economy, and narration registers present and
  substantively equivalent to the canonical orchestrator body), not a byte-for-byte transclusion.]
- **AC-08 — `install.py` gains a fourth target, `pi` → `~/.pi/agent`, using the exact existing mechanism, no
  new abstraction.** Concretely, four small, additive changes to `ai/scripts/install.py` (**not an exhaustive
  list of everything this write path needs — round 2, N-02: see also AC-09's collision guard, which adds
  fail-closed logic to this same write path**): (1) the `--target`
  `argparse` choices tuple (`install.py:23`, currently `("opencode", "claude-code", "codex")`) gains `"pi"`;
  (2) `all_targets` (`install.py:29-33`) gains `"pi": home / ".pi/agent"`; (3) `managed_files()`
  (`install.py:101-109`) needs no code change — it already iterates `targets.items()` generically, reading
  whatever `staging/<harness>/managed-files.txt` AC-02's `write_indexes()` extension produces; (4)
  `previous_targets()`'s pruning fence (`install.py:222-238`) needs no code change either — it already derives
  its safety fence from `all_targets.values()` generically. `SPECIAL` (`install.py:36-40`) gains **no** new
  entry: `Global/pi/AGENTS.md` installs as a plain, full-overwrite managed file, exactly the precedent already
  set by `Global/opencode/AGENTS.md` and `Global/codex/AGENTS.md` today — neither of which is in `SPECIAL`
  either (verified: `SPECIAL` only ever held the three merge-JSON/TOML files, `opencode.json`,
  `settings.overlay.json`, `config.snippet.toml` — no `AGENTS.md`/`CLAUDE.md` variant has ever been a merge
  target). The generic placeholder-scan smoke check (`install.py:381-382`, `if any(PLACEHOLDER in
  path.read_bytes() for _, path in files if path.exists())`) already iterates every target's `files` list
  generically and needs no change to cover `pi`. **No pi-specific smoke check is added** (the three existing
  ones — OpenCode MCP-disabled, Claude Engram-disabled, Codex multi-agent-enabled, `install.py:360-380` — are
  each about a harness-specific config surface this contract does not touch for `pi`; named as a deliberate
  non-goal, not an oversight, since nothing in this contract's scope requires a `pi`-side config assertion
  beyond "the placeholder is gone," already covered). See AC-09 for the new collision guard this target needs,
  and Verificación's Rollback subsection for why no pi-specific rollback logic is needed either.
- **AC-09 (new, F-13) — a fail-closed collision guard for `~/.pi/agent/agents/`, the one write target among the
  four generated harness trees where pre-existing third-party content is real, not hypothetical.** If a file
  this feature's converter would write to `~/.pi/agent/agents/` collides with a pre-existing file NOT recorded
  in `install.py`'s own `MANIFEST` (i.e., third-party content this installer never wrote — e.g. the gentle
  leftovers named in Non-goals, or any future third-party agent file a user or another extension drops there),
  the install must fail closed rather than silently overwrite it. This is the first of the four generated
  harness targets where this risk is real: `Global/pi/skills/**` and `Global/pi/prompts/**` land in
  `~/.pi/agent/skills/` and `~/.pi/agent/prompts/`, both confirmed empty/non-existent at spec-writing time (see
  Contexto, "What already exists"), and `Global/pi/AGENTS.md` is a single named file with no glob-driven
  collision surface; `~/.pi/agent/agents/` is the only one of the four that already holds a real, populated set
  of third-party `.md` files today (the 12 `sdd-*.md` leftovers, pending the user's separately-authorized
  manual cleanup — see Non-goals) and could hold more in the future. **Verified live this session, re-run per
  F-13's explicit instruction: zero collisions between the 28 canonical role names
  (`Global/_canonical/agents/*.md`, listed directly) and the 8 `pi-subagents` builtin agent names (`scout`,
  `planner`, `worker`, `reviewer`, `context-builder`, `researcher`, `delegate`, `oracle`)** — `comm -12` on the
  two sorted name lists returns nothing. Those 8 builtins also physically live in a different directory
  entirely (`~/.pi/agent/npm/node_modules/pi-subagents/agents/*.md`, `pi-subagents`' own installed package
  tree), not `~/.pi/agent/agents/` (this feature's write target) — so today, a literal file-level collision
  with the builtins specifically cannot occur even without this guard. The guard remains required regardless:
  `pi-subagents`' documented customization pattern explicitly allows creating a user-scope override file with
  the SAME name as a builtin (its own "Management actions create or update user/project agent files" section),
  so a same-named file landing in `~/.pi/agent/agents/` in the future — whether from a human override, a
  reinstalled gentle-style extension, or any other source this installer did not itself write — is a real,
  standing risk this AC closes generically, not one scoped only to today's specific 12 leftover names.

  **New in this revision (round 2, N-01) — the guard fires in BOTH `--preview` and write mode, with a
  concrete, actionable error, and one named operational consequence.** Consistent with this repo's existing
  fail-closed guards (e.g. `check-canonical-paths.py`), an unrecorded collision must be detected and reported
  identically whether `install.py` is run as a dry run or for real — **`install.py`'s current `--preview`
  path (`install.py:281-309`) always exits 0 regardless of findings** (it prints `LEGACY_CONFLICTS=...` when
  present but still `raise SystemExit(0)`; that is a weaker, print-only precedent this AC does NOT reuse for
  its own guard). The error must name the exact colliding path (relative to `~/.pi/agent/agents/`) and
  instruct the operator to resolve it BY HAND, outside the installer — no override flag, no silent bypass —
  per ADR-0008 D2's own "never touch third-party content" doctrine, which this guard exists specifically to
  uphold, not relax. **Operational consequence, named explicitly so it is not a surprise found later —
  corrected in this revision (round 3, R3-03): the mechanism stated in an earlier revision of this AC was
  mechanically wrong, re-verified against the real script and reproduced live this session with a minimal
  repro of the same `errexit`+`pipefail` shape.** `ai/scripts/check-drift.sh` runs under `set -euo pipefail`
  (`check-drift.sh:6`). Its `--preview` call is a command substitution inside a pipeline, assigned to a
  variable: `PREVIEW="$(python3 "$ROOT/ai/scripts/install.py" --staging "$STAGING" --home
  "${DRIFT_HOME:-$HOME}" --preview 2>/dev/null | tail -5)"` (`check-drift.sh:21`, verified live, unqualified
  `--target` selects every registered target via `selected = set(args.target or all_targets)`, `pi` included
  once AC-08 lands). Under `errexit`+`pipefail`, if `install.py --preview` exits non-zero for a collision, the
  pipeline's own exit status IS that non-zero code (`tail` always exits 0, so `pipefail` surfaces
  `install.py`'s code as the pipeline's), and — live-reproduced this session with a minimal repro of the same
  shape — a variable assignment consisting solely of a failing command substitution ABORTS the script right
  there, at line 21, with `install.py`'s own exit code, no drift-specific message. **It never reaches
  `check-drift.sh:24`'s `[ -z "$COUNT" ]` check**, so the `DRIFT_UNKNOWN`/`exit 2` path at
  `check-drift.sh:25-26` is NOT what fires — an earlier revision's framing of this consequence was wrong on
  the mechanism, only right that the badge ends up degraded either way. Separately, `check-drift.sh`'s own
  `DRIFT_DETECTED` path (`check-drift.sh:29-34`) exits with code `1` and prints remediation advice ("corré: cd
  $ROOT && ./build.sh --install"). **This AC therefore requires the new guard's exit code be pinned to a
  value that does NOT collide with `1` (`DRIFT_DETECTED`'s own code):** a collision surfacing as exit `1`
  would be silently indistinguishable from ordinary drift, and `check-drift.sh`'s own remediation advice would
  then also fail closed on the same unresolved collision — a confusing loop for the operator, who would be
  told to re-run the exact command that just failed. **The guard's exit code is `2`**, matching two
  independent, already-existing precedents verified live this session: `check-drift.sh`'s own internal-error
  convention (`check-drift.sh:14-18`, "Generation failure is an internal error (2), never 'stale' (1)",
  `exit 2`) AND `install.py`'s own existing `INSTALL_ABORTED_UNSAFE_ROOT` guard (`install.py:63-75`, `raise
  SystemExit(2)`), the closest existing fail-closed-abort precedent already inside `install.py` itself.
  Reusing `2` means an aborted `check-drift.sh` run for an unrecorded collision reads, correctly, as
  `DRIFT_UNKNOWN`-shaped (a preview that could not be computed) via `install.py`'s own propagated exit status
  at line 21, rather than colliding with or being mistaken for ordinary `DRIFT_DETECTED` (code 1).
- **AC-10 (was AC-09) — the seven already-installed pi extensions stay untouched, and this is provable, not
  merely asserted.** None of `pi-subagents`, `pi-intercom`, `@juicesharp/rpiv-ask-user-question`,
  `pi-web-access`, `@juicesharp/rpiv-todo`, `pi-btw`, `pi-mcp-adapter` is referenced by name in any file this
  contract creates or edits — `install.py`'s new `pi` target only ever writes files under the four relative
  paths `agents/`, `skills/`, `prompts/`, `AGENTS.md`, never `~/.pi/agent/settings.json` (where the `packages`
  array lives) and never `~/.pi/agent/npm/` (where the extensions themselves are installed). This is the same
  separation ADR-0008 already establishes for the other three harnesses' own MCP/plugin config: a managed
  prompt/skill/agent tree never mutates the surrounding runtime's own package manifest. **The provable claim,
  concretely (F-10, this AC previously had zero coverage in Verificación): every relative path this
  feature's `install.py --target pi` write set touches falls under exactly one of `agents/|skills/|prompts/`
  or the literal file `AGENTS.md`, relative to `~/.pi/agent/` — nothing else** (see Verificación).
- **AC-11 (was AC-10) — freshness/portability guards: two different, already-existing checks, only one of
  which needs extending; verified against the real scripts, not assumed as one undifferentiated "the guard."**
  1. **`verify.sh`'s portability heredoc (`verify.sh:28-52`) already covers `Global/pi/**` for free — no
     change needed, confirmed by reading the code.** `GLOBAL_PLACEHOLDER_MISSING` (`verify.sh:44`)/
     `GLOBAL_BUILDER_PATH` (`verify.sh:48`)/`GLOBAL_ABSOLUTE_PATH_RATCHET` (`verify.sh:50`) — **and a fourth
     guard in the same block, missing from this enumeration until this revision (round 2, N-06e):
     `GLOBAL_BARE_APP_CLI` (`verify.sh:45-46`)**, which fires when the placeholder-substituted and raw
     occurrence counts of `ai/scripts/set_agents_app.py` disagree within a file — iterate
     `global_root.rglob("*")` where `global_root = root / "Global"` (`verify.sh:32`) — no hardcoded harness
     tuple anywhere in that block. Any file added under `Global/pi/**` is automatically scanned for a bare
     (unsubstituted) `ai/scripts/set_agents_app.py` reference (both the "missing entirely" and the "partially
     substituted" shapes), the builder's own absolute path, and any new `/home/`/`/Users/`-anchored literal,
     the moment it exists on disk — same enforcement, zero code change, for all four guards.
  2. **`verify.sh`'s tracked-vs-regenerated freshness check (`verify.sh:25-27`, corrected in this revision
     from an earlier `:24-27` citation — round 2, N-06c: `:24` is `./build.sh --output "$STAGING" >/dev/null`,
     the staging step, not part of the loop itself) DOES need extending**, and without it a stale or
     hand-edited `Global/pi/**` would never be caught. That block currently reads
     `for harness in opencode claude-code codex; do diff -ruN "Global/$harness" "$STAGING/$harness"; done` —
     a fourth line, `diff -ruN "Global/pi" "$STAGING/pi"`, is required. `build.sh` needs the matching update in
     three places: its `usage()` text (`build.sh:12`, `--target opencode|claude-code|codex` → add `|pi`), its
     `generate` mode's copy loop (`build.sh:80-83`, `for harness in opencode claude-code codex; do rm -rf
     ...; cp -a ...; done`, add `pi`), and its `diff` mode (`build.sh:75-77`, three `diff -ruN` lines, add a
     fourth for `pi`). `build.sh --check`'s OWN internal drift check (`build.sh:60-71`, the THIRD kind of
     drift per ADR-0008 D9 — template vs. harness self-scaffold, `feature-state.py`/`check-owned-paths.py`
     only) is unrelated to this AC and needs no change; naming it here only to rule it out explicitly, per
     ADR-0008 D9's own "the three drift checks are DIFFERENT and must never be conflated" instruction.
- **AC-12 (new, F-12/user decision 4) — dispatch-lane closure: add `--no-skills` and `--no-prompt-templates`
  to `set_agents_spawn.py`'s fixed dispatch-lane argv, and name the exact scope-authorization path
  package-planning must follow, since the file is very likely outside this feature's own `owned_paths`.**
  Concretely: the fixed argv construction at `set_agents_spawn.py:244-248` (flags on lines 245-246,
  `"--no-session", "--no-extensions"` then `"--no-context-files", "--tools", ...`) gains the two additional
  flags, `--no-skills` and `--no-prompt-templates`, both confirmed real and independent in `pi --help`'s
  option list (`--no-skills, -ns`, `--no-prompt-templates, -np`). This keeps ADR-0007's dispatch lane's system
  prompt exactly as originally audited — closing AC-01's residual risk instead of merely naming it as accepted.
  **New in this revision (round 2, N-06f):** this AC also requires updating the stale comment directly above
  the argv construction, `set_agents_spawn.py:241-243` ("T-304 guards: `--no-session`, `--no-extensions`, and
  `--no-context-files` are UNCONDITIONAL — never gated by `guard_tools`, never omitted. Only the `-t` allowlist
  varies by tier.") — verified live this session, exact lines confirmed by reading the file directly. That
  comment names exactly three unconditional flags; once this AC adds `--no-skills`/`--no-prompt-templates`,
  the unconditional set becomes five, and the comment must be updated to say so, not left describing three.
  **Ownership, verified live this session, not assumed:** `ai/scripts/set_agents_spawn.py` does not appear in
  this feature's own state file (it does not exist yet — this is a pre-`cmd_init` spec); grepping every
  `ai/state/features/*.json` for `set_agents_spawn.py` inside an `owned_paths` array shows it currently listed
  by two DIFFERENT already-accepted packages — `004-adaptive-dispatch`'s `P3-pi-lane` (status `accepted`) and
  `007-quota-visibility`'s `P2-spawn-accounting` (status `accepted`) — plus `011-quota-failover`'s
  `P1-quota-failover` package, whose status is `package_gates` (not accepted; that feature is `BLOCKED`
  per its own spec, so its ownership claim should not be treated as authoritative). **The correct path for
  package-planning, named here so it is not silently assumed, citing the real precedent found in this repo's
  own state:** either (a) request an ownership exception on `set_agents_spawn.py` for this package via
  `feature-state.py update-package --exception '{"path": "ai/scripts/set_agents_spawn.py", "reason": ...,
  "status": "approved"}'` — the exact mechanism and JSON shape already used for precisely this kind of
  narrow, human-approved scope expansion onto a file outside a package's own `owned_paths`, real precedent at
  `ai/state/features/005-portable-harness.json:2316-2330` (`005-portable-harness`'s own P1 needed the same kind
  of exception on this exact same file, for an unrelated earlier change); or (b) split this two-flag change
  into a tiny, separate quickfix against whichever of `004-adaptive-dispatch`'s `P3-pi-lane` or
  `007-quota-visibility`'s `P2-spawn-accounting` package-planning judges the more natural current owner, via
  `feature-state.py log-quickfix --summary ... --result done --file ai/scripts/set_agents_spawn.py --gate ...`.
  This spec does not pick between (a) and (b) — that is a scope-authorization call for package-planning, not a
  product decision — it only confirms both mechanisms are real, already implemented in `feature-state.py`, and
  names the one concrete precedent found for (a). **Also required (AC-14 depends on this):** a matching update
  to ADR-0007's own text near its Decision 4, documenting this closure — not only a new entry in ADR-0017 (see
  AC-14).
- **AC-13 (new, F-01) — a real end-to-end check that starts `pi` and observes real loading, not just
  file-existence/frontmatter checks.** **Live-verified this session, not merely proposed:** `pi --help` has no
  skill-inspection subcommand (confirmed, full option list read live), and `pi --verbose` renders a real
  startup header with exactly three discovery sections and the literal file paths it loaded:
  ```
  [Context]
    ~/.pi/agent/AGENTS.md

  [Skills]
    user
      ~/.pi/agent/skills/demo/SKILL.md

  [Prompts]
    user
      /demo
  ```
  **Corrected in this revision (round 2, C-03): the exact invocation recipe below is REPLACED — the round-1
  recipe (`script -qc "pi --verbose --offline --no-session" <logfile>` against a scratch `$HOME`) hangs or
  hits the network, reproduced this session.** Root cause: the bare `pi` on `$PATH` is this operator's
  personal soft-pinned wrapper (`~/.local/bin/pi`), which itself shells out through `mise`/`pnpm dlx` to
  resolve the real binary on first use — that resolution is itself `$HOME`-dependent state (pnpm's
  content-addressed store, mise's own shims) and, run against a freshly-scratch `$HOME` with none of that
  state, re-triggers first-run resolution and touches the network. The underlying claim (`pi` actually loads
  the tree) is real and was reproduced; only the recipe was broken. **The working two-step recipe, verified
  live this session against real output (captured above, `pi` 0.83.0 — a newer soft-pinned resolution than
  round 1's `0.82.1`, consistent with this contract's own versioned-not-permanent-guarantee discipline):**
  1. **Resolve the real `pi` binary path against the REAL `$HOME`** (not the scratch one), so the resolution
     step itself never touches the scratch environment: `pnpm dlx --package @earendil-works/pi-coding-agent
     which pi` — this returns an absolute path under the operator's real pnpm dlx cache (e.g.
     `~/.cache/pnpm/dlx/<hash>/node_modules/.bin/pi`), live-verified this session to complete in seconds with
     no network access when the package is already cached (the common case on a machine that has run this
     harness's own dispatch lane, which resolves the same package).
  2. **Invoke that resolved absolute path directly (never the `~/.local/bin/pi` wrapper) with `HOME=<scratch>`
     set AND the process's working directory explicitly pinned to an empty scratch directory, under a real
     pty, with an explicit timeout, plus `--no-approve`.** **Corrected in this revision (round 3, R3-04): two
     fixes to the recipe below, neither present in round 2's version.** First, the CWD was left unpinned —
     round 3 found the project-trust prompt this recipe works around is CWD-dependent, not `$HOME`-dependent:
     from an empty scratch CWD, no prompt fires at all; from this repo's own root (a real, `pi`-trust-eligible
     project directory), it blocks. The recipe now explicitly pins the working directory to a scratch/empty
     directory — never wherever the check happens to be invoked from — removing the dependency on the
     caller's own CWD entirely. Second, `--approve` (`pi --help`: `--approve, -a`, "Trust project-local files
     for this run") is replaced with `--no-approve` (`pi --help`: `--no-approve, -na`, "Ignore project-local
     files for this run" — re-read directly this session, not merely reused from the round-3 summary). Round 3
     found the two flags render an identical discovery header for this check's purposes, because every
     assertion AC-13 makes is user-scope (`~/.pi/agent/**`), never project-scope, so whether project-local
     files are trusted or ignored is immaterial to what this check observes; `--no-approve` is preferred as
     the more isolated/conservative choice — it unblocks the same headless-startup prompt while isolating the
     check by construction (explicitly ignoring project-local files) rather than by trusting anything
     project-local, consistent with pinning the CWD to an empty scratch directory in the first place. The full
     command, both corrections applied: `cd <scratch-empty-dir> && HOME=<scratch> timeout 20 script -qc
     "<resolved-pi-path> --verbose --offline --no-session --no-approve" <logfile>`.
  **Success criterion is CONTENT-based, never the process exit code, stated explicitly per this AC's own
  requirement:** `pi --verbose` is an interactive TUI that does not exit on its own even after rendering the
  header (confirmed live: the process still runs, `timeout` kills it, `script`'s recorded exit code is 124 —
  a timeout, not a crash, and NOT treated as a failure signal). The test harness relies purely on
  `timeout` + grepping the captured, ANSI-stripped log for the expected section headers and paths — it does
  **not** send any quit/interrupt keystroke sequence to the pty; sending one is unnecessary because content
  already renders and is captured well before the timeout fires (confirmed live: `[Context]`/`[Skills]`/
  `[Prompts]` and their paths appear roughly 1-2 seconds after launch, verified across three live runs this
  session). **Paths render abbreviated with `~`, not expanded absolute paths — the content assertion must
  match against the literal abbreviated form** (e.g. `~/.pi/agent/AGENTS.md`, `~/.pi/agent/skills/demo/
  SKILL.md`), confirmed by the captured log above; asserting against an expanded `$HOME`-substituted absolute
  path would never match. This AC requires a package-planning-owned scratch-`$HOME` smoke test, using the
  corrected two-step recipe above, populated with a representative converted tree (one role's
  `agents/<role>.md`, one skill's `skills/<name>/SKILL.md`, one prompt's `prompts/<name>.md`, and
  `AGENTS.md`), asserting: `[Context]` lists `~/.pi/agent/AGENTS.md`; `[Skills]` → `user` lists the
  `SKILL.md` path for every skill under `Global/pi/skills/**`; `[Prompts]` → `user` lists `/<command-name>`
  for every file under `Global/pi/prompts/**`. **`[[Agents]]` is confirmed absent from this header** (pi
  core's startup inventory has no "agents" resource family at all — see Contexto point 3), so
  `Global/pi/agents/**`'s discoverability cannot be proven by `pi --verbose` and needs a separate live check:
  `pi-subagents`' own `subagent({ action: "list" })` call (verified real syntax, `pi-subagents` SKILL.md line
  515) or its `/subagents-doctor` slash command, run inside an actual session with `pi-subagents` active,
  asserting the converted roster is enumerated. **Credential/environment-gated, same established pattern as
  `011-quota-failover`'s and `012-discovered-inventory`'s own credential-gated E2E checks:** this requires the
  real, locally-installed `pi` binary plus `pi-subagents` active; a CI environment without them degrades to
  `BLOCKED`/`HUMAN_DECISION_REQUIRED` for this check specifically, never a silent skip and never a false pass
  on the static-check layer alone (AC-05's 38/38 static skill checks, AC-02's frontmatter/role-set checks).
- **AC-14 (was AC-11) — a new ADR, `docs/adr/0017-pi-interactive-target.md` (skeleton requirement only —
  writing the ADR itself is a later step, owned by `architect`), PLUS the in-file amendment discipline this
  repo's own `docs/adr/README.md` already mandates for partial supersession.** Confirmed as the next free
  number by listing `docs/adr/` directly (highest existing file: `0016-discovered-inventory.md`,
  `docs/adr/README.md` lists it as `Accepted`). The ADR must, at minimum:
  1. Frame itself explicitly as **extending** ADR-0007, citing the real, currently-disjoint flag sets from
     AC-01 (interactive load path vs. `set_agents_spawn.py:244-248`'s dispatch argv) — not a contradiction,
     because they are different sessions with different flags, evidenced live, not asserted.
  2. **Expanded in this revision (round 2, C-02) — record that it narrowly amends THREE pieces of ADR-0007
     Decision 4, not one, all found live this session in `docs/adr/0007-pi-lane.md`:**
     1. **The Decision's own title and opening premise** — `## Decisión 4 — target `pi` MÍNIMO en
        generate/install (sin árbol generado)` (`docs/adr/0007-pi-lane.md:93`) and its opening sentence,
        "Deliberadamente NO se genera: el prompt canónico de cada rol ... es en sí mismo un prompt de sistema
        válido y se pasa VERBATIM al spawn" (`docs/adr/0007-pi-lane.md:95-96`) — both now FALSE the moment
        AC-02 ships a real generated `Global/pi/agents/**` tree; the Decision's own name asserts the opposite
        of what this contract builds.
     2. **The `install.py` clause** — "`install.py` NO gana un target `pi` nuevo: no hay un árbol de archivos
        por-usuario que este repo deba escribir para Pi" (`docs/adr/0007-pi-lane.md:106-112`) — which was true
        for the dispatch lane's own concern (an ephemeral `--print` subprocess that never reads
        `~/.pi/agent/agents/`, `skills/`, or `prompts/` under its own flag set) and is not true for this new,
        separate interactive surface, which explicitly does read all three. The dispatch lane's own
        mechanism — the canonical role prompt passed verbatim via `--append-system-prompt`, ADR-0007 Decision
        1/4, with no install-time substitution at all — is untouched; this ADR amends only the "no
        `install.py` target" clause, for the interactive surface alone.
     3. **The listed consequence about `validate_pi_target`** — "`generate.py` gana `validate_pi_target(roles)`
        (llamada desde `validate()`): re-afirma que cada rol activo tiene su prompt canónico en disco — la
        única precondición real de la superficie pi ..." (`docs/adr/0007-pi-lane.md:103-105`). **This becomes
        INCOMPLETE, not false, per round 2's C-01 resolution** (`validate_pi_target()` is KEPT, exactly as
        this consequence still accurately describes — see AC-02): the pi surface now ALSO has a second,
        generated-output-side validation this 2026-07-27 text has no way to mention (the two `validate()`
        loops AC-02 extends with a `pi` member, checking the GENERATED `Global/pi/agents/*.md` files
        themselves, not just their source). The amendment note must name this as an addition/clarification,
        not a reversal, so a future reader of ADR-0007 alone is not misled into thinking
        `validate_pi_target()` is still the pi surface's *only* validation.
  3. **New in this revision (F-12/AC-12):** record that AC-12's dispatch-lane closure additionally narrows
     ADR-0007 Decision 2's own residual-risk framing (skills/prompt-templates now blocked from dispatch-lane
     children by the same two flags that already block extensions/context-files) — this is a second, separate
     narrowing of ADR-0007, distinct from Decision 4's install-target clause above, and must be recorded as
     such.
  4. **New in this revision (F-09):** in addition to a `docs/adr/README.md` row for `0017`, add an **in-file
     amendment note inside `docs/adr/0007-pi-lane.md` itself, near its Decision 4 text**, marking that clause
     as narrowed/amended by ADR-0017 — following the exact precedent already visible in that same file (its own
     `## Enmienda — repair R1` section, confirmed live at line 199) and in `docs/adr/README.md`'s own existing
     rows for ADR-0004 and ADR-0013 (`"Superseded in part by 0005"` / `"Superseded in part by 0014"` in the
     Status column, with a scoped parenthetical — `"0005 (routing journal only)"` / `"0014 (spawn node
     deferral only)"` — in the Superseded-by column, both verified live this session). The README row for
     `0007` must be updated the same way — `Status: "Accepted; superseded in part by 0017"`, `Superseded by:
     "0017 (install.py target + dispatch-lane skills/prompt-templates closure only)"` — not only a new row
     added for `0017` itself.
  5. Record AC-05's now-resolved compatibility question (no live spike needed; `compatibility` is optional,
     informational, unenforced by `pi`'s lenient loader — cite `docs/skills.md`'s Validation section) as a
     concrete, dated finding.
  6. Record AC-06's two now-resolved translation decisions (`agent:` → explicit `subagent(...)` body
     instruction per user decision 2; `$ARGUMENTS` needs no translation, native alias per
     `docs/prompt-templates.md`'s Arguments section) as concrete, dated findings.
  7. Record AC-03's tool-ceiling divergence (open `subagent` token vs. Claude Code's closed allowlist) as an
     accepted, documented decision per user decision 3, citing the structural-boundary evidence from
     `pi-subagents`' own SKILL.md.
  8. **New in this revision (F-15):** record that `pi`'s own documented alternative — a `settings.json`
     pointer directly to `~/.claude/skills` (or any other harness's skill directory), requiring zero generated
     tree, real and documented in `docs/skills.md`'s "Using Skills from Other Harnesses" section — was
     considered and rejected, because it would break this repo's established one-copy-per-harness-tree
     symmetry with the other three targets (OpenCode/Claude Code/Codex) and would entangle a managed file
     (`Global/pi/skills/**`, installed and tracked by this repo's own machinery) with the user's own free-form
     `settings.json`, which `install.py` does not manage for any of the four harnesses today.
  9. Record AC-01's residual risk as CLOSED by AC-12 (not merely named), with AC-12's exact mechanism (two
     flags at `set_agents_spawn.py:245-246`) and its ownership-exception precedent.
  10. **New in this revision (round 2, C-02) — a `feature-state.py log-decision` call is REQUIRED to
      explicitly supersede the existing persisted decision that asserted the opposite of what this feature
      ships**, before or alongside the ADR-0007 in-file amendment above — per this repo's own Living
      Documentation doctrine (a persisted decision is never silently left contradicting shipped reality).
      Verified live this session: the decision is `ai/state/decisions-log.jsonl:14`
      (`at: "2026-07-27T13:30:44+00:00"`, `feature_id: "004-adaptive-dispatch"`, `package_id: "P3-pi-lane"`,
      `slug: "ac09-ac10-pi-minimal-target-accepted"`, title "AC-09/AC-10 literal deviations accepted: minimal
      pi target + pnpm-store pin"), whose `consequences` field states verbatim: "install.py stays untouched;
      P3 adds no generated pi agent tree" — the exact opposite of AC-08's new `pi` target. The matching note
      file is `docs/notas/decisiones/2026-07-27 ac09-ac10-pi-minimal-target-accepted.md`, confirmed present
      on disk this session. Both must be named as a required step here, not left implicit: `log-decision`
      records a NEW decision entry whose `context`/`decision` text explicitly names and supersedes the old
      slug (the same pattern this repo already uses for an explicit supersession —
      `ai/state/decisions-log.jsonl`'s own `buenos-dias-anthropic-surcharge-claim-was-wrong-supersedes-
      first-pass` entry is the real, existing precedent for a decision whose slug itself declares it
      supersedes an earlier one); `log-decision` has no dedicated "supersede" flag, so the superseding
      relationship is carried in the new entry's own prose, matching that precedent exactly.

### Audit (self-review)

- **Universe named, for every "does X exist"/"is X compatible" claim in this contract:** the active role
  roster (`roles`, from `models_config.load_roles`, a real subset of the 28 files physically present under
  `Global/_canonical/agents/`, per AC-02); all 38 files under `Global/_canonical/skills/*/SKILL.md`, verified
  by direct listing (AC-05); all 22 files under `Global/_canonical/commands/*.md`, verified by direct listing
  (AC-06); the 8 `pi-subagents` builtin agent names, verified by direct listing of their real install
  directory (AC-09). No claim in this contract is stated over "however many happen to exist" without that
  count having been taken live this session.
- **Absence behavior defined:** a canonical role missing its prompt file already dies loudly today
  (`load_roles`'s `die(f"{row['role']}: missing canonical prompt")`, `generate.py:58-61`) — AC-02 reuses that
  exact check by reusing the same loop, so a role absent from disk fails the whole build before any harness
  (including `pi`) is written, never a silent partial tree. A pre-existing, unrecorded file at
  `~/.pi/agent/agents/<name>.md` now fails the install closed rather than being silently overwritten (AC-09).
  A prompt whose `agent:` field has no injected `subagent(...)` instruction is not a silently-accepted
  "done" state under AC-06 — the instruction's presence is part of the AC, not an optional enhancement.
- **Data source proven to carry the signal, for every claim, not paraphrased from an inherited summary:**
  every code citation in this document (`generate.py`, `install.py`, `build.sh`, `verify.sh`,
  `set_agents_spawn.py`) was opened and read directly this session, with exact line numbers taken from that
  read (including two citations corrected from stale line numbers found in the round-1 draft: the role loop's
  `:334`→`:335` start, and `validate()`'s two harness-tuple loops' real lines, `:527`/`:535`). Every `pi`-side
  claim (agents/skills/prompts discovery paths, frontmatter shapes, argument-placeholder syntax, `--help` flag
  list, extension package list, the `compatibility`-field enforcement question, the `$ARGUMENTS`/`$@` alias
  claim, the `subagent(...)` call syntax, the structural no-further-delegation boundary) was read directly
  from real, locally-installed files (`~/.pi/agent/settings.json`, `~/.pi/agent/npm/node_modules/
  pi-subagents/**`, `pi --help`'s live output, and the pinned `0.81.1` package's extracted
  `docs/{skills,prompt-templates,usage,quickstart}.md`) — never reused from an inherited description without
  independently checking it. The end-to-end `pi --verbose` startup-header claim (AC-13, F-01) was not merely
  read from documentation but actually run live this session against a scratch `$HOME` under a pty, with the
  real rendered output captured and reproduced verbatim in AC-13.
- **Pairwise conflict pass:** the one real cross-requirement interaction found in round 1 — `Global/pi/skills/**`
  and `Global/pi/prompts/**` (AC-05/AC-06) becoming silently reachable from ADR-0007's already-accepted
  dispatch-lane spawns (`set_agents_spawn.py:244-248`) — is no longer left as a named-but-accepted residual
  risk; it is now closed by AC-12, with the closure itself creating a new, explicitly named interaction (AC-12
  touches a file this feature does not own, requiring the scope-authorization step named there before
  implementation — this is itself the kind of cross-boundary interaction the audit discipline exists to
  surface, not silently execute). A second interaction, new to this revision: AC-09's collision guard and
  Non-goals' gentle-leftover manual-cleanup note both touch `~/.pi/agent/agents/`'s pre-existing content —
  checked as a pair: AC-09's guard is unconditional (it fires on ANY unrecorded pre-existing file, not only the
  12 named leftovers), so it remains correct and necessary whether or not the user's manual cleanup has run by
  the time this package installs; the two do not conflict or race. No other pair of ACs in this contract fires
  on the same entity: AC-02/AC-03/AC-04 (agents), AC-05 (skills), AC-06 (prompts), AC-07 (doctrine file), AC-08
  (install target) each own a disjoint relative-path namespace under `Global/pi/**` and `~/.pi/agent/`, with no
  two ACs writing the same file.
- **UNVERIFIED-for-architecture tags, collected (narrowed from round 1 — several are now resolved and
  removed):** AC-03's exact pi-tool-name vocabulary for `Glob`-equivalents (`find`/`ls` observed, no formal
  mapping table asserted — the invariant, not the mapping, is this pass's claim); AC-06's exact injected
  `subagent(...)` instruction wording/placement in the prompt body (the requirement that it exists and is
  explicit is resolved by user decision 2; the literal string is not); AC-07's exact selection/wording of which
  orchestrator sections are folded into the doctrine file (the requirement that the result is operationally
  sufficient is resolved by user decision 1; the exact prose is not). Resolved and removed from this list since
  round 1: AC-03's `subagent`-token-vs-allowlist divergence (user decision 3); AC-05's compatibility-filter
  question (F-03, documentation-settled); AC-06's `agent:`-field resolution (user decision 2) and
  `$ARGUMENTS`/`$@` question (F-02, documentation-settled).
- **What I could not verify, stated plainly rather than omitted:** (1) `pi` core's own documentation for the
  default global discovery paths of `skills/` and `prompts/` beyond what is now directly confirmed live in
  `docs/skills.md`'s "Locations" section (`~/.pi/agent/skills/` and `~/.agents/skills/`) and
  `docs/prompt-templates.md`'s "Locations" section (`~/.pi/agent/prompts/*.md`) — both now read directly from
  the pinned package's extracted docs this session, resolving what round 1 flagged as unverifiable (the pnpm
  content-addressed store, once located, is in fact human-browsable — round 1's "not extracted" caveat is
  retracted, the docs were simply not looked for at the right path). (2) Whether every future `pi` release
  keeps `--verbose`'s startup header rendering the same three-section shape captured in AC-13 — this pass
  states the claim as verified-on-0.82.1 (round 1) and re-verified on 0.83.0 (round 2, C-03's corrected
  recipe, same three-section shape reproduced against a newer soft-pinned resolution), the same versioning
  discipline the rest of this contract already applies, not a permanent guarantee. (3) The exact
  scope-authorization outcome for AC-12 (ownership exception vs. quickfix) — deliberately left to
  package-planning, per AC-12's own text, not a gap in this pass's research. (4) Whether every trust-flag
  choice ever changes the discovery header content itself (as opposed to merely unblocking headless startup
  past the project-trust prompt) — live evidence gathered under round 2's `--approve`-based recipe showed no
  effect on header content, and round 3's switch to `--no-approve` (R3-04) is stated on the same reasoning
  (both flags are project-scope controls, AC-13's assertions are all user-scope), but this pass has not
  exhaustively tested every `--approve`/`--no-approve` combination against every CWD/trust-state
  permutation. (5) **New in this revision (round 3, R3-05):** whether AC-13's end-to-end check proves loading
  against the EXACT interactive wrapper binary a human actually runs. AC-13 resolves its `pi` binary via
  `pnpm dlx --package @earendil-works/pi-coding-agent which pi`, which resolved to `0.83.0` this session — a
  different, newer build than the wrapper the human actually runs interactively, `~/.local/bin/pi`, currently
  soft-pinned to `0.82.1` (re-confirmed via `pi --version` this session). This is not a contradiction (both
  builds are real, recent releases of the same package), but it is a real caveat given AC-13 is framed as the
  check that "survives the fixture that would fool this feature" — AC-13, as specified, technically only
  proves loading works in the dlx-resolved build, not necessarily byte-for-byte in the wrapper's own resolved
  version. Treated as low-risk, not fully closed: both share the same underlying npm package's documentation
  and behavior at adjacent versions, but this specific dlx-resolved-vs-wrapper-resolved gap has not been
  independently closed by running the wrapper's own exact resolved binary through the same check.

## Secuenciación

This is scoped as a single package, plus AC-12's narrow, separately-authorized touch on
`set_agents_spawn.py` (owned elsewhere — see AC-12). Within the package, a natural internal order — not a
hard gate, since most ACs have no dependency on each other and could land in parallel:

1. AC-02 (agents converter, including the `validate()` extension and `validate_pi_target()`'s docstring
   correction — kept, not removed, per round 2 C-01), AC-03
   (frontmatter/tool ceiling — no remaining open question to resolve first), AC-04 (orchestrator role file),
   and AC-07 (doctrine file, including the orchestrator-content fold-in) — no external dependency, no blocking
   spike remaining for any of these.
2. AC-05 (skills copy) and AC-06 (prompts converter, including the `agent:`→`subagent(...)` body instruction) —
   both unblocked, no live spike required before implementation (resolved from round 1's blocking spikes).
3. AC-08 (install target) and AC-09 (collision guard) together — AC-09 is a property of the same install path
   AC-08 adds, not a separate pass over it.
4. AC-11 (guards) — mechanical, depends only on AC-02/AC-05/AC-06/AC-07/AC-08 existing.
5. AC-13 (end-to-end `pi --verbose` check) — depends on AC-02/AC-05/AC-06/AC-07 having real output to observe;
   naturally lands after them, functions as this package's own proof its earlier steps actually work end to
   end, not merely pass static checks.
6. AC-12 (dispatch-lane closure) — **before starting implementation, package-planning must resolve the
   ownership question named in AC-12's own text**: either secure an `update-package --exception` on
   `ai/scripts/set_agents_spawn.py` for this package (precedent: `ai/state/features/
   005-portable-harness.json:2316-2330`), or route the two-flag change as a `log-quickfix` against whichever
   of `004-adaptive-dispatch`'s `P3-pi-lane` or `007-quota-visibility`'s `P2-spawn-accounting` package
   currently makes more sense as the tiny fix's owner. This step has no code dependency on any other AC in this
   list and could run at any point, but is sequenced last here because it is the one item outside this
   package's own `owned_paths` and should not block the rest of the package while the authorization is
   pending.
7. AC-14 (ADR skeleton) last, once every other AC's real findings (AC-05's resolved compatibility answer,
   AC-06's two resolved translation decisions, AC-03's accepted divergence, AC-12's closure mechanism and
   whichever authorization path it took) are concrete outcomes to record rather than placeholders — including
   the required in-file amendment to `docs/adr/0007-pi-lane.md` near its Decision 4 text and the
   `docs/adr/README.md` row updates for both `0007` and `0017`.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS`, including AC-11's extended `diff -ruN "Global/pi" "$STAGING/pi"`
line and the unmodified portability heredoc, both green · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK
files=2` (unrelated to this contract, unaffected) · `./build.sh --diff` shows a clean fourth `pi` diff (empty,
once generated and committed) · `python3 -m unittest discover -s tests -v` — test count must rise from
whatever the live count is at package-planning time (measured then, not asserted here as a stale number) to
cover, per AC (this list is now the fully corrected/extended version of round 1's, per F-10):

- **AC-01** (new coverage, F-10): a unit test constructing the real dispatch-lane argv
  (`set_agents_spawn.py`'s argv-building function) and asserting, post-AC-12, that it contains
  `--no-skills`/`--no-prompt-templates` alongside the three pre-existing guard flags — proving the two
  sessions' flag sets are as documented, not merely asserted in prose.
- AC-02's roster-loop extension (a role's `Global/pi/agents/<role>.md` output exists, has valid `name`/
  `description`/`tools`/`systemPromptMode` frontmatter — round 2, C-04 — and its body byte-equals the
  canonical source read directly); plus a negative test that `validate()` fails closed if a role's generated
  `Global/pi/agents/<role>.md` is hand-edited out of sync with its canonical source (exercising the extended
  frontmatter/role-set loops). **Corrected in this revision (round 2, C-01):** `validate_pi_target()` is not
  removed, so there is no "did removal silently drop coverage" question to confirm; instead, this AC's
  coverage must confirm `tests/test_harness.py:3046-3054`
  (`test_pi_target_validate_requires_canonical_prompt_per_role`) still passes UNCHANGED post-revision, and add
  one new assertion that `validate_pi_target()`'s docstring no longer contains the retracted "pi gets NO
  generated agent tree" premise (a cheap, direct regression guard against the exact contradiction C-01 fixes).
- AC-03's ceiling invariant (a `coord-ro`-capability role's pi `tools` list never grants a filesystem/bash/
  network capability absent from that same role's Claude Code `tools` list — the narrowed invariant, not the
  retired absolute one). **New in this revision (round 2, C-04):** a test asserting every generated
  `Global/pi/agents/*.md` file has a non-empty `tools` field (never omitted) and `systemPromptMode: replace`
  (never omitted, never any other value) — not just `name`/`description`, which round 1's coverage stopped
  at; and a test asserting the `coord-ro`-capability role (`orchestrator`) carries `maxSubagentDepth: 2`
  explicitly (round 2, N-05).
- **AC-04** (new coverage, F-10): a test asserting `Global/pi/agents/orchestrator.md` is emitted by the same
  roster loop as every other role, with no field driven by being `orchestrator` BY NAME (**clarified in this
  revision — round 2, C-04/N-05: `orchestrator` does carry one field most roles lack, `maxSubagentDepth: 2`,
  but that difference is driven entirely by its `coord-ro` CAPABILITY CLASS, the same class-keyed
  differentiation `claude_tools()` already applies today for every harness — not by its role name or any
  interactive-default/primary-persona special-casing**), AND a separate assertion that `Global/pi/AGENTS.md`
  (AC-07), not this file, is the one referenced by `pi`'s own context-file discovery path — proving the two
  are not conflated.
- AC-05's skills-copy byte-identity to `Global/_canonical/skills` (unconditional now, no spike-gated branch).
- AC-06's prompts-copy: byte-identical `$ARGUMENTS` passthrough (no substitution), and presence of the
  injected `subagent(...)` instruction for every prompt whose canonical command declared `agent:`.
- AC-07's new doctrine file exists, contains each of the twelve sections named in Contexto, AND **(F-10, was
  missing entirely)** contains the orchestrator's operating content — a check that the file's text includes
  substantive question-policy, spawn-economy, and narration-register content, not just the twelve generic
  doctrine sections (e.g. asserting the presence of the `Cliente:`/`Ingeniería:` narration-register
  vocabulary and a recognizable spawn-economy rule, not merely a section heading).
- AC-08's four `install.py` additions (an `--target pi --preview` dry run against a scratch `$HOME` produces
  the expected `MANAGED_DIFF_FILES` count and no `SPECIAL` entry for `AGENTS.md`).
- AC-09's collision guard: a scratch-`$HOME` test with an unrecorded, pre-existing file at
  `~/.pi/agent/agents/collision-test.md` asserts `install.py --target pi` fails closed rather than
  overwriting it, and that a file already recorded in `MANIFEST` from a prior run is still updated normally
  (proving the guard is scoped to unrecorded content, not everything). **New in this revision (round 2,
  N-01):** the same collision fixture is run twice, once under `--preview` and once in write mode, asserting
  BOTH exit non-zero with an error naming the exact colliding relative path — proving the guard is not a
  write-mode-only check that `--preview` silently skips.
- **AC-10** (new coverage, F-10 — this AC previously claimed to be "provable, not merely asserted" with zero
  test): a test asserting every relative path in `install.py --target pi`'s write set (from `managed_files()`
  plus the single `AGENTS.md` entry) falls under exactly one of `agents/`, `skills/`, `prompts/`, or the
  literal filename `AGENTS.md`, relative to `~/.pi/agent/` — nothing else, and specifically never
  `settings.json`, `auth.json`, `trust.json`, or any path under `npm/`.
- AC-11's guard extensions actually fail when `Global/pi/**` is hand-edited out of sync with a fresh
  regeneration (a real negative test, not only a positive one).
- **AC-12** (new coverage): a unit test on the real dispatch-lane argv-building function confirming both new
  flags are present and unconditional (never gated by `guard_tools` or any tier), matching the T-304 guard
  discipline the three pre-existing unconditional flags already follow.
- **AC-13** (new, credential/environment-gated, see below): the real end-to-end `pi --verbose` check.
- **AC-14** (new coverage, round 3, R3-02 — this AC previously had zero coverage in `## Verificación` despite
  being the largest AC, 10 sub-items, and including a mandatory state mutation): four checks — (1)
  `docs/adr/0017-pi-interactive-target.md` exists; (2) `docs/adr/README.md` has a row for `0017` AND an
  updated `Status`/`Superseded-by` annotation on `0007`'s own row (`Status: "Accepted; superseded in part by
  0017"`, `Superseded by: "0017 (install.py target + dispatch-lane skills/prompt-templates closure only)"`);
  (3) `docs/adr/0007-pi-lane.md` contains an amendment note naming `0017`, placed near its Decision 4 text,
  following the same `## Enmienda` precedent already in that file; (4) `ai/state/decisions-log.jsonl` has a
  new entry whose text names the superseded slug, `ac09-ac10-pi-minimal-target-accepted`.

`git diff --check` · ownership vs. baseline · `security-auditor` review recommended (not mandated by this spec
— left to package-planning) given AC-08 writes to a new location under `$HOME` outside the three
previously-audited harness roots, and AC-12 touches a file with its own prior security repair history
(ADR-0007's `## Enmienda — repair R1`).

### Rollback (F-18, new — AC-08's own subsection, since this is the first target writing into a brand-new
`$HOME` root)

`install.py` already has a generic, backed-up rollback mechanism covering every target uniformly — no
pi-specific rollback code is needed, the same way no pi-specific smoke check was needed in AC-08. Concretely:
every install run snapshots the pre-existing state of every file it is about to touch into a timestamped
backup directory (`backups_root = home / ".local/state/set-agentes/backups"`, `install.py:312-330`, 0700
permissions, the last 20 runs retained) before writing anything, and `rollback()` (`install.py:333-345`)
restores every touched file from that snapshot via the same `atomic_write` primitive used to install them —
this mechanism is generic over `targets` and requires no per-harness branch, so it already covers the new `pi`
target the moment AC-08 registers it in `all_targets`. `~/.pi/agent/` today also holds `auth.json`,
`trust.json`, `sessions/`, `intercom/`, and `models-store.json` — none of which this feature touches (AC-08's
write set is exactly `agents/|skills/|prompts/|AGENTS.md`, verified by AC-10's own test) — so a rollback of
this target's files can never disturb those. Following ADR-0007 Decision 3's own rollback-documentation
convention (a one-line "**Rollback** = ..." note under the decision that introduces the mutable state): this
target's rollback is "revert via the existing `install.py rollback()` path, same as the other three harness
targets — no new mechanism, no new code."

**This feature's own fixture-that-would-fool-it, named explicitly per the faithfulness rule:** a hermetic unit
test that stubs `pi`'s own skill/prompt-template/context-file loader (rather than actually placing a file
under `~/.pi/agent/` and asking a real `pi` session whether it is discoverable) would go green on AC-05/AC-06/
AC-07 even if the real `pi` binary silently ignored one of them. AC-13's end-to-end check is what survives
that exact fixture — captured live this session (2026-07-31, `pi` 0.82.1 in round 1 and re-confirmed on
`pi` 0.83.0 in round 2 using AC-13's corrected two-step invocation recipe, C-03; real `--verbose` startup
header, reproduced verbatim in AC-13) rather than only proposed. It must run against the real, locally-installed `pi`
(this machine has it; a CI environment without it degrades to `BLOCKED`/`HUMAN_DECISION_REQUIRED` for that
check specifically, the same pattern `011-quota-failover`'s and `012-discovered-inventory`'s own
credential-gated E2E checks already establish, never a silent skip and never a false pass on the unit-test
layer alone).
