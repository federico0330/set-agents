# setting-sources user confía en scope generado desde el propio repo

<!-- notas:auto -->
- fecha: 2026-08-01 · actor: orchestrator
- alcance: [[features/015-anthropic-dispatch-parity|015-anthropic-dispatch-parity]]

## Contexto

Hallazgo del checkpoint temprano de security-auditor sobre P1-anthropic-dispatch-parity (AC-01/AC-02), antes de cablear AC-03/AC-04.

## Decisión

--setting-sources user confía en ~/.claude/**, que build.sh --install puebla desde Global/claude-code/** de este mismo repo. Un spawn writer-class (dentro del límite de contención por cwd) puede editar esos archivos fuente legítimamente, y el próximo --install los promueve al scope de confianza. No es un privilegio nuevo (un implementer interactivo ya puede editar Global/** hoy) y está gobernado por check-owned-paths.py, pero debe quedar escrito explícitamente en el ADR-0019 en vez de implícito, porque la mitigación de R3-01 se lee como absoluta y no lo es.

## Consecuencias

Deuda registrada para AC-08 (ADR-0019); no bloquea el resto del paquete.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
