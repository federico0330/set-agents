# 019-harness-evolution · P5-tools-discovery

<!-- notas:auto -->
## Motivo

- objetivo: Catalogo de tools abierto con aprobacion humana: --tools-propose/--tools-approve, tools.local.toml, allowlist cerrada en coord_policy y doctrina de tool faltante (ADR-0038)
- complejidad: medium
- riesgo: SEC-001: el argv-walker nunca por regex laxo; sudo siempre manual
- paths: `docs/adr/0038-tools-discovery-with-approval.md`

## Tareas

- [x] --tools-propose: validacion, rechazo de sudo/pipes, pregunta consolidada, no instala (completed) · cmd_tools_propose + _validate_install_command en set_agents_app.py: fail-closed, sudo siempre rechazado, unico pipe legitimo curl|wget ... | bash|sh (criterio mas restrictivo que instaladores reales, deliberado y documentado en ADR-0038), kind fuera del enum es error, nombre con la gramatica de _CATALOG_NAME. Rechazos pegados con salida real en la evidencia.
- [x] --tools-approve: tools.local.toml untracked + merge en load_catalog + log-decision (completed) · load_catalog mergea tools.toml + tools.local.toml, el curado gana ante colision y la ausencia del archivo no falla. tools.local.toml y tools.proposals.json ignorados (.gitignore:39-43), verificado con git status --porcelain. log-decision via subprocess a feature-state.py tras un bug real: el import directo de cli_reporting.cmd_log_decision crasheaba con AttributeError en model.render_notes y ningun test unitario lo detecto porque todos mockean esa funcion -- solo lo agarro la prueba en vivo.
- [x] TOOL_UNKNOWN sugiere el flujo propose (completed) · token TOOL_UNKNOWN preservado; mensaje nuevo apunta a --tools-propose
- [x] coord_policy: argv-walker con gramatica cerrada para las dos flags (completed) · coord_policy.py:175-215 _tools_propose_allowed con los 4 flags requeridos, sin repeticion; :244-247 deny explicito de --tools-approve; generate.py:253-261 deny en el mapa de permisos de OpenCode (glob mas grueso que el walker)
- [x] Skills solo project-local; doctrina de tool faltante en orchestrator/implementer; item de menu (completed) · Global/_canonical/agents/{orchestrator,implementer}.md; Global/_canonical vetado como destino para los 3 kinds; item de menu Proponer herramienta nueva

## Hallazgos

- F-01 [critical] closed
- F-02 [critical] closed
- F-03 [high] closed
- F-04 [high] closed
- F-05 [medium] closed
- F-06 [medium] closed
- F-07 [medium] closed
- F-08 [medium] closed
- F-09 [medium] closed
- F-10 [medium] closed
- F-11 [medium] closed
- F-12 [low] closed
- F-13 [low] closed
- F-14 [low] closed
- F-15 [low] closed
- NEW-01 [high] closed
- NEW-02 [medium] closed
- NEW-03 [medium] closed
- NEW-04 [low] closed

## Recorrido

- review: repair_required (15 hallazgos)
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 5 sostenidos
- verificación: 0 refutados, 2 sostenidos
- verificación: 0 refutados, 1 sostenidos
- verificación: 0 refutados, 2 sostenidos
- repair: F-01 → 4 archivos
- repair: F-02 → 1 archivos
- repair: F-03 → 1 archivos
- repair: F-04 → 1 archivos
- repair: F-05 → 1 archivos
- repair: F-06 → 1 archivos
- repair: F-12 → 4 archivos
- repair: F-13 → 1 archivos
- repair: F-14 → 1 archivos
- repair: F-15 → 1 archivos
- repair: F-07 → 4 archivos
- repair: F-08 → 4 archivos
- repair: F-09 → 4 archivos
- repair: F-10 → 4 archivos
- repair: F-11 → 4 archivos
- repair: NEW-01 → 3 archivos
- repair: F-06 → 3 archivos
- repair: NEW-02 → 3 archivos
- repair: NEW-03 → 3 archivos
- repair: NEW-04 → 3 archivos
- delta review: repair_required
- delta review: repair_required
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `verify`: pass
- gate `build-check`: pass
- gate `diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_312476b9f44c1e39845bce98ef7ab859
- SPAWN-002 implementer · modelo openai-codex/gpt-5.6-terra · effort high · route run1_b21bda145b39cfe2422b5e6e6de1c199
- SPAWN-003 package-reviewer · modelo anthropic/opus · effort medium · route dec1_7b5568f3b598b9b205b0606f1a07ae37
- SPAWN-004 delta-reviewer · modelo anthropic/opus · effort medium · route dec1_f567208d29fb6ac7aba67b82e7bb5a97
- SPAWN-005 repair-agent · modelo openai-codex/gpt-5.6-terra · effort high · route run1_7abab8c5a85bb7d516c20d17e865eac1
- SPAWN-006 delta-reviewer · modelo anthropic/opus · effort medium · route dec1_c0f5c57b1373c0ff1eeebd9083313d5e
- SPAWN-007 delta-reviewer · modelo anthropic/opus · effort medium · route dec1_ec4aa18d5adc55c0c5cb8569ac5cf991
- SPAWN-008 delta-reviewer · modelo anthropic/opus · effort medium · route dec1_c38dadb70b15d556516bc4a17bf58add
- SPAWN-009 integrator · modelo openai-codex/gpt-5.6-sol · effort balanced · route run1_12433558d22d959e44c257a86abcf578

context pack: `docs/specs/019-harness-evolution/context/P5-tools-discovery.md`

↩ [[features/019-harness-evolution|019-harness-evolution]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
