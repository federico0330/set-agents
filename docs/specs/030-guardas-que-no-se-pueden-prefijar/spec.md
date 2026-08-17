# 030 — Guardas que no se pueden prefijar

- **Estado:** implementado e instalado (pendiente de normalización en state machine).
- **Origen:** incidente SEC-030 en repo público.
- **ADR:** `docs/adr/0059-prefix-match-rce-fix.md`.

## Problema

La policy de comandos read-only validaba por prefijo (`pattern + ".*"`), permitiendo flags
arbitrarias al final de comandos permitidos y abriendo RCE/escritura arbitraria.

## Resultado esperado del paquete S1

1. La validación deja de ser por prefijo y pasa a enumeración explícita de modificadores por comando.
2. `curl` valida URL/esquema y rechaza flags de salida/carga peligrosas.
3. `FORBIDDEN_SYNTAX` queda en fuente única y los guardas la importan (sin copias divergentes).
4. Las PoC de SEC-030 quedan bloqueadas y el corpus legítimo del harness sigue permitido.

## Evidencia ya integrada

- Implementación documentada en `docs/specs/030-guardas-que-no-se-pueden-prefijar/evidence/S1-implementer.md`.
- Diseño/decisiones en ADR-0059.
- Código activo en:
  - `ai/scripts/coord_policy.py`
  - `ai/scripts/claude_bash_guard.py`
  - `ai/scripts/claude_local_gate_guard.py`
  - `ai/scripts/claude_release_guard.py`
  - `tests/test_command_policy.py`

## No-goals

- No ampliar alcance a una reescritura total de todos los wrappers de hooks fuera de SEC-030.
- No reabrir la decisión de seguridad de remover binarios/flags no enumerables del allowlist.
