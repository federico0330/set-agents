# ADR-0024 — Integration receipt: a git tree-hash freeze gating `PACKAGE_ACCEPTED→INTEGRATION`

- Estado: Accepted (2026-08-03). Quinta y última de cinco ADRs (0020-0024) del estudio de RDD de `gentle-ai`;
  ver ADR-0020 para el contexto compartido. La de mayor escrutinio de las cinco — toca la capa de permisos.

## Contexto

El "recibo" mecánico real hoy en SET-AGENTES existe solo para el paso de release: `release_gate.py` +
`release_action.py` + un PreToolUse hook (`claude_release_guard.py`) bloquean de verdad cualquier
`git commit`/`push`/`gh` que no pase por el wrapper sancionado. Nada análogo existe para
`PACKAGE_ACCEPTED → INTEGRATION` — hoy esa transición corre bajo el allow genérico de
`ai/scripts/coord_policy.py` (`r"python3 ai/scripts/feature-state\.py \S+"`), que admite CUALQUIER
subcomando de `feature-state.py`, incluida una transición directa a `INTEGRATION` sin que nada la verifique
contra un candidato realmente congelado. El usuario confirmó extender el patrón de tríada de hook ya probado
para release, aplicado a esta transición específica.

Investigación previa a la implementación reveló tres cosas que cambiaron el plan original:
1. `coord_policy.py` (el policy module) ES el guard del orquestador — invocado vía `claude_bash_guard.py`
   (un wrapper genérico que ya existe), no hace falta un tercer script `claude_integration_guard.py` nuevo
   como se había previsto originalmente; alcanza con extender `coord_policy.py`'s `SAFE`.
2. Un chequeo de string/regex simple (`"transition INTEGRATION"`) es insuficiente: `argparse` permite
   reordenar `--flag valor` alrededor del positional `to_phase`, así que
   `transition --actor x INTEGRATION --package-id y` es idéntico en efecto a
   `transition INTEGRATION --actor x --package-id y` pero un regex ingenuo solo atrapa la segunda forma.
3. **`integration_ready` NO puede ser una precondición dura de `transitions.check_transition`.** Un primer
   intento lo agregó ahí y rompió DOS tests de la suite inmutable
   (`test_done_ready_reaches_done_after_a_real_block_and_reopen_cycle`,
   `test_package_workflow_happy_path_executes_real_transitions`): ambos ejercen
   `accept-package → transition INTEGRATION → transition DONE` sin `record-receipt` en ningún punto —
   comportamiento real, ya validado, que predata este ADR. La corrección de "el llamador se saltea el
   receipt" no puede vivir en la máquina de estados genérica, que sirve a cualquier caller del CLI (tests,
   operadores humanos, otros roles), no solo al orquestador. Se revirtió el cambio en `transitions.py`; el
   enforcement real queda exclusivamente en la capa de Bash del orquestador (decisión 4), coherente con cómo
   `release_gate.py` tampoco es una precondición de `cmd_transition` — es un chequeo que un wrapper específico
   corre antes de ejecutar el comando real, nunca una regla universal de la máquina de estados.

## Decisión

1. **`integration_ready(package)`** vive en `feature_state_lib/candidate_identity.py` (no en `model.py`, para
   mantenerla junto a `rederive_and_compare`, que es lo único que usa). Exige: `receipt` presente con
   `terminal_state == "accepted"`, sus hashes coincidiendo con el `candidate_identity` actual, y una
   re-derivación en vivo exitosa (`rederive_and_compare`) — nunca confía en un booleano guardado. **No la
   llama `transitions.check_transition`** (ver punto 3 del Contexto) — su único caller es
   `integration_gate.py`.
2. **Tríada nueva**: `ai/scripts/integration_gate.py` (política pura, espejo de `release_gate.py`, reusa
   `integration_ready` en vez de reimplementar lógica) + `ai/scripts/integration_action.py` (wrapper
   ejecutable, espejo de `release_action.py`, un positional extra `PACKAGE_ID` porque la autoridad de
   integración es por paquete, no por feature — valida que el `--package-id` del comando envuelto coincida
   exactamente con el `package_id` chequeado, y que una acción `transition` sea literalmente la transición a
   `INTEGRATION`, nunca otra fase colada por el mismo wrapper). Este es el ÚNICO lugar que efectivamente
   exige el receipt — la máquina de estados por sí sola sigue permitiendo `transition INTEGRATION` sin
   receipt para cualquier caller que no pase por este wrapper, igual que hoy permite `git commit` directo
   para cualquier actor que no sea `github-release-manager`.
3. **`coord_policy.py`** gana `_transition_blocks_integration(argv)`, un parser posicional dedicado (no un
   regex) que camina `argv` igual que `argparse` resolvería el positional `to_phase` de `transition` entre
   sus flags (todos toman exactamente un valor) — detecta `INTEGRATION` sin importar el orden de los flags.
   Se llama ANTES de cualquier otro chequeo en `allowed()`, así que ni el regex `SAFE` ni `SAFE_ARGV` pueden
   dejarlo pasar por otra vía. Una nueva entrada `SAFE` admite la forma envuelta
   (`~/.claude/hooks/integration_action.py <state> <pkg> (freeze-candidate|record-receipt|transition) -- ...`).
4. **OpenCode** (`generate.py`'s bloque `coord-ro`) recibe el mismo par deny/allow en su formato glob-only:
   `"...transition INTEGRATION*": deny` (más específico, ubicado después del allow genérico — el matcher de
   OpenCode ya usa "most-specific-match", confirmado por un test existente de la suite) +
   `"~/.config/opencode/hooks/integration_action.py*": allow`. Es menos riguroso que el chequeo posicional de
   `coord_policy.py` (no hay forma de expresar "cualquier orden de flags" en glob puro), pero cubre la forma
   canónica que la propia doctrina de `orchestrator.md` siempre emite. Codex no tiene un mecanismo
   equivalente de permisos por comando en este repo — no se inventó uno solo para esta pieza.
5. `integration_gate.py`/`integration_action.py` se copian junto con una copia completa de
   `feature_state_lib/` a los 3 directorios `hooks/` generados (`claude-code`, `opencode`, `codex`) —
   `integration_gate.py`, a diferencia de `release_gate.py` (JSON puro, sin dependencias), reusa
   genuinamente `candidate_identity`/`model`, y un hook instalado vive fuera de cualquier `ai/scripts/` de
   proyecto (ADR-0008), así que necesita su propia copia para poder importar el paquete.

## Rejected alternatives

- **Un tercer script `claude_integration_guard.py` nuevo.** Innecesario una vez confirmado que
  `claude_bash_guard.py` ya es el wrapper genérico del orquestador sobre `coord_policy.py` — agregarlo
  hubiera sido superficie duplicada sin necesidad.
- **Un regex simple `"transition INTEGRATION"` en `coord_policy.py`.** Rechazado tras confirmar que
  `argparse` permite reordenar flags alrededor del positional — un regex así deja un hueco real, no teórico.
- **Reimplementar el freeze/re-derive dentro de `integration_gate.py`.** Rechazado: hubiera duplicado la
  lógica de git tree-hash de `candidate_identity.py`, con el riesgo de que las dos copias diverjan.
- **Inventar un mecanismo de permisos para Codex.** No existe ninguno equivalente hoy en `generate.py` para
  la capacidad `coord-ro` — agregar uno solo para esta pieza sería alcance no aprobado.

## Consecuencias

- `PACKAGE_ACCEPTED → INTEGRATION` queda protegido en UNA capa real: el Bash del orquestador
  (`coord_policy.py`/OpenCode's `coord-ro`), verdaderamente bloqueante a nivel de tool-call en las dos lanes
  principales, forzando el paso por `integration_action.py` → `integration_gate.check()` →
  `integration_ready`. La máquina de estados (`cmd_transition`) NO exige el receipt — comportamiento
  idéntico al de antes de este ADR para cualquier caller que no sea el orquestador siguiendo su propia
  doctrina (tests, un humano operando el CLI a mano, otro rol). Esto es deliberado, no un descuido: es
  exactamente la misma asimetría que ya existe entre `release_gate.py` (un chequeo que corre un wrapper
  específico) y `cmd_transition`/`git commit` (que nunca lo exigen por sí solos).
- El wrapper (`integration_action.py`) nunca reimplementa el chequeo de negocio — delega en
  `integration_ready`, la única fuente de verdad sobre "cuándo está lista la integración".
- Ningún otro subcomando de `feature-state.py` se ve afectado, y ningún comportamiento preexistente de
  `cmd_transition`/`transitions.check_transition` cambió — el carve-out es exacto a la capa de permisos del
  orquestador, nunca a la máquina de estados que sirve a todos los callers del CLI.
