# 030-guardas-que-no-se-pueden-prefijar · S1-command-policy-rce-fix

<!-- notas:auto -->
## Motivo

- objetivo: Cerrar SEC-030 prefix-match RCE con allowlist estructurada
- complejidad: small
- paths: `ai/scripts/coord_policy.py`, `ai/scripts/claude_bash_guard.py`, `ai/scripts/claude_local_gate_guard.py`, `ai/scripts/claude_release_guard.py`, `tests/test_command_policy.py`

## Tareas

- [x] t1-registrar-implementacion-integrada (completed) · tests/test_command_policy.py corpus+PoCs OK

## Recorrido

- review: pass (0 hallazgos)
- testing: pass
- runtime QA: pass
- gate `gate-sec030`: pass

↩ [[features/030-guardas-que-no-se-pueden-prefijar|030-guardas-que-no-se-pueden-prefijar]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
