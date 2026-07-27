# Context pack — P3-pi-lane (feature 004, contract 1.1.0)

Objetivo: cerrar el "fork funcional de gentle-ai" con la **elección de modelo cross-provider REAL por
spawn**. P2 dio la elección de tier dentro de openai-codex en OpenCode (con degrade honesto a base cuando
el router elige anthropic). P3 agrega **Pi como cuarto runtime ejecutable**: el orquestador decide
`(provider, model)` con `--route-decide` y spawnea `pi --model <provider>/<model> --print` — honrando la
decisión sea openai-codex O anthropic, por invocación. Esto es lo que ningún otro runtime permite y lo que
el spike T-300 probó viable + en vivo.

## Leé primero
- `docs/specs/004-adaptive-dispatch/evidence/P3-spike-T300.md` — **el spike, con la prueba en vivo y el
  inventario real de modelos**. Es la base de todo lo de acá. Leelo entero.
- `docs/specs/004-adaptive-dispatch/{spec,acceptance,plan}.md` (AC-09g/09/10/11/11g/12/13; plan §P3-pi-lane
  T-300..T-305)
- `docs/adr/0004-*` (routing/permisos son de SET-AGENTES, Pi es peer no dueño), `docs/adr/0005-*` (R3
  threat model), `docs/adr/0006-*` (AM-1/AM-2)
- Código base:
  - `ai/scripts/routing_core/service.py:132` — **el flip**: hoy `selected_runtime=="pi"` ⇒
    `PI_SIMULATION_ONLY` (no ejecutable). Línea 133 es el chequeo normal de inventario que debe aplicar a pi
    una vez que es un runtime probado.
  - `ai/scripts/routing_core/catalog.py:20` `_PAIR_COMMANDS` + parsers por par (`_parse_codex_login` lee
    STDERR, `_parse_opencode_*`, `probe_inventory`) — agregar `(pi, openai-codex)` y `(pi, anthropic)`.
  - `ai/scripts/models_config.py:33` `RUNTIMES` (pi YA está), `[orchestrator.pi]` (157-176), `SELECTED_RUNTIMES`.
  - `ai/scripts/generate.py` loops `("opencode","claude-code","codex")` (283/326/406/408/435/506/514),
    `install.py` TARGETS/ROOTS (23/29-33) — el "target pi".
  - `ai/scripts/set_agents_app.py` — `--doctor` existente (extender `--harness pi`), zonas routing.

## Inventario real (post-login, del spike) — el mapa concreto
`~/.pi/agent/auth.json` autenticado con **`anthropic` + `openai-codex`** (nombres IDÉNTICOS a los del
catálogo). `pi --list-models`:
- **openai-codex**: `gpt-5.6-luna/sol/terra` → **IDENTIDAD** con el catálogo (cero traducción).
- **anthropic**: `claude-opus-4-5|4-6|4-7|4-8`, `claude-sonnet-4-5|4-6|5`, `claude-haiku-4-5`, `claude-fable-5`
  → el catálogo usa nombres cortos; mapa curado **`opus→claude-opus-4-8`, `sonnet→claude-sonnet-5`,
  `haiku→claude-haiku-4-5`** (alineado con los tiers Claude del arnés). Única traducción de P3;
  user-ajustable.

## Arquitectura recomendada (desviación deliberada del plan original — justificada por el proof en vivo)
El plan T-302/T-303 asumía un árbol de agentes Pi generado + una **extensión TypeScript** `set_agents_spawn`
sobre el SDK. El proof en vivo demostró que el **camino CLI-subproceso es suficiente y más simple**, sin host
JS ni superficie TypeScript nueva. Recomendación (los reviewers deben desafiarla):
- **Spawner = script Python** `ai/scripts/set_agents_spawn.py` (consistente con el resto de ai/scripts), que
  invoca `pi --model <provider>/<model> --print --mode json --no-session --append-system-prompt <role.md>
  <task>` desde un cwd controlado (`pi` muta el cwd). Parsea el stream JSON (`agent_start`→`agent_settled`),
  lee `message.model` para **verificar la decisión** (match por modelo decidido, como P2), captura
  `usage.cost` y el marcador terminal.
- **Guards 002 AC-04 como flags** (no como extensión): `--no-session` (contexto fresco efímero),
  `--no-extensions` (nunca carga pi-subagents ⇒ **hijos depth-0, sin delegación**), allowlist de tools
  read-only (`-t read,grep,ls,find`) **hasta que los guards estén verdes**; recién ahí ampliar a
  code-rw por capability.
- **"pi target" en generate/install = mínimo**: NO se genera un árbol de agentes Pi; el spawner pasa el
  prompt canónico del rol (`Global/_canonical/agents/<role>.md`, ya instalado) via `--append-system-prompt`.
  install puede registrar `pi` como target para un marcador de settings/doctor si hace falta, nada más.
  Documentá por qué (esto de-scopea T-302 respecto del plan).

## Mapa de cambios por tarea
- **T-301** ADR-0007 (`docs/adr/0007-pi-lane.md`): decisión CLI-subproceso vs SDK/extensión (con el proof
  como evidencia), guards-como-flags, mapa de model-ids, condiciones del flip. **Managed install** de Pi con
  versión EXACTA pinneada (el wrapper `~/.local/bin/pi` solo tiene release-age soft-pin; pinnear 0.81.1 o la
  que se elija) + status/rollback + `set_agents_app.py --doctor --harness pi` (reporta versión, auth.json
  key-set, list-models OK/FAIL — sin volcar tokens).
- **T-302** target `pi` en generate/install (mínimo, ver arquitectura): fresh-context, sin delegación,
  depth 0. Superficies de doctor/validate.
- **T-303** `ai/scripts/set_agents_spawn.py`: el spawner CLI-subproceso; ciclo de vida completo incl.
  **crash⇒failure** (exit≠0 o falta `agent_settled` ⇒ cerrar run como failure via `--route-terminal`);
  camino de rechazo (modelo decidido ≠ `message.model` ⇒ abandoned + no ejecutar). Integra con el ciclo
  P1 (`--route-decide`→run_id→`--route-dispatched`→spawn→`--route-terminal`).
- **T-304** guards a nivel spawn (002 AC-04 en el nuevo punto de enforcement) con test por-guard;
  **hijos read-only hasta que estén verdes** (allowlist de tools mínima; code-rw solo tras probar que el
  hijo no delega ni escapa).
- **T-305** pares `(pi, openai-codex)` y `(pi, anthropic)` + parsers en catalog.py (probe = `pi --list-models`
  parseado por columna provider + `auth.json` key-set; positives-only, misma disciplina AM-2); validación
  del allowlist `runtimes` por-ruta si aplica; **flip de `PI_SIMULATION_ONLY`** (service.py:132) gateado a
  que el doctor pi esté verde; docs de rollout/rollback + ADR/architecture. Mapa de model-ids catálogo↔Pi
  (identidad openai-codex; corto→canónico anthropic).

## Invariantes que NO se tocan
- Núcleo P1 AM-1/AM-2, ciclo SQLite, SCHEMA=4: intactos salvo el flip puntual de service.py:132 y los pares
  de probe nuevos (aditivos). P2 (variantes OpenCode, gate de coherencia, doctrina): intacto.
- Separación de deberes: reviewers read-only con `review_of_run_id`; el spawner Pi NO permite que un hijo
  delegue (depth 0, `--no-extensions`).
- Redacción: NUNCA loguear tokens de `auth.json`; el doctor reporta solo el key-set y OK/FAIL. El descriptor
  de `--route-decide` es intención no confiable.
- Threat model R3: adversario in-process/same-UID fuera de scope; "caller"=intent.
- Sin migrar DBs viejas; regresiones nunca debilitadas; drift check (Global==generate fresco) verde.
- **PI_SIMULATION_ONLY NO se flipa hasta que**: doctor pi verde (versión pinneada + auth + list-models),
  guards verdes (hijos no delegan, no escapan), y el spawner cierra el ciclo (incl. crash⇒failure) — todo
  probado hermético + QA en vivo (Pi ya autenticado).

## Gates del paquete
`python3 -m unittest discover -s tests -v` (sin debilitar); `./build.sh --check` (incl. coherencia P2 +
validaciones pi); `py_compile` (incl. routing_core + set_agents_spawn); `./ai/scripts/verify.sh` VERIFY_PASS
(drift limpio); `git diff --check`; ownership vs baseline del paquete. **QA en vivo** (Pi autenticado):
decide→spawn pi→terminal por CLI ruteando de verdad, verificando `message.model`==decidido, para al menos
openai-codex/gpt-5.6-luna y anthropic/claude-*; crash⇒failure; doctor pi verde.

## Propiedad (owned_paths)
`docs/adr/0007-pi-lane.md`, `ai/scripts/set_agents_spawn.py` (nuevo), `ai/scripts/routing_core/catalog.py`,
`ai/scripts/routing_core/service.py` (solo el flip 132), `ai/scripts/models_config.py`, `models.toml`,
`ai/scripts/generate.py`, `ai/scripts/install.py`, `ai/scripts/set_agents_app.py` (doctor),
`tests/test_routing.py`, `tests/test_harness.py`, `docs/architecture/overview.md`,
`docs/specs/004-adaptive-dispatch/context/P3-pi-lane.md`, `docs/specs/004-adaptive-dispatch/evidence/P3-*`.
Read-only: `ai/catalogs/routes.v1.toml` (los 5+ roles ya están en las filas; pi no cambia el catálogo),
`roles.tsv`, `Global/_canonical/agents/**` (se leen como prompts, no se modifican).
