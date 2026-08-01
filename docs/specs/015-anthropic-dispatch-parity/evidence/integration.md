# Integration — 015-anthropic-dispatch-parity

Feature de un solo paquete (`P1-anthropic-dispatch-parity`, AC-01..AC-08). No hay costuras entre
paquetes propios que revisar — la integración relevante es contra el resto del árbol de trabajo,
no commiteado (`HEAD` sigue en `898c539...`; esta evidencia se verifica contra el árbol vivo).

## Qué se integró

- `ai/scripts/routing_core/service.py` — redirect de runtime efectivo por proveedor (AC-01).
- `ai/scripts/claude_code_spawn.py` (nuevo) — spawn CLI headless hacia Claude Code, con techo de
  herramientas a nivel CLI, `--setting-sources user`, contención por cwd, y veredicto real del
  revisor propagado (AC-02, más el fix de runtime-QA que cerró QA-01).
- `ai/scripts/coord_policy.py` + `Global/claude-code/hooks/coord_policy.py` (excepción de ownership) —
  entrada en la lista blanca para el nuevo CLI.
- `ai/scripts/generate.py` (excepción de ownership) — allow-lines para el lane OpenCode (DR-01).
- `Global/_canonical/agents/orchestrator.md` + 3 copias generadas — doctrina cross-lane/off-lane
  (AC-03/AC-04), regenerada vía `./build.sh`.
- `models.toml` — tres colisiones de modelo cerradas (`areas.audit`, `areas.judge`, `areas.ops`,
  AC-06).
- `docs/adr/0019-anthropic-dispatch-parity.md` + fila en `docs/adr/README.md` (AC-08).

## Costuras revisadas

- **013-pi-interactive-target** (aprobada, `PACKAGE_PLANNING`, todavía sin paquete): su propio spec
  también toca `Global/_canonical/agents/orchestrator.md`. Sin colisión viva hoy (013 no reclamó
  owned_paths todavía). Nota de secuenciamiento ya registrada vía `log-decision`: el package-planning
  de 013 debe releer `orchestrator.md` en su estado POST-015, no el texto anterior.
- **014-model-preference-policy** (contrato 3.1.0, todavía sin aprobación final): depende de 015 para
  que su clase `build` y `grunt` tengan efecto real. Sin código compartido tocado por 015 que 014
  no supiera ya (014 cita 015 explícitamente como dependencia).
- **011-quota-failover** (BLOCKED): 015 no depende de él ni lo modifica; el Non-goal ya deja nombrado
  que la detección de agotamiento en el lane Claude Code queda fuera de alcance de este paquete.

## Gates

- `./ai/scripts/verify.sh` → `VERIFY_PASS` (558 tests, 0 failures, 0 skips inesperados).
- `./build.sh --check` → `CHECK_PASS`.
- `git diff --check` → limpio.
- `check-owned-paths.py` → `OWNERSHIP_PASS` (con las excepciones aprobadas para `coord_policy.py`,
  su copia generada, y `generate.py`).

## Historial de revisión (resumen)

Panel RP-01 (`package-reviewer` + `security-auditor`) → `repair_required` (10 hallazgos, 2 críticos
de seguridad reales verificados en vivo) → reparación → delta-review 1 → `repair_required` (reabrió
un crítico a medio cerrar + 4 hallazgos nuevos) → reparación → delta-review 2 → `pass` → testing →
runtime QA (encontró un bug funcional real: el veredicto del revisor se descartaba en el camino
exitoso) → reparación puntual → re-testing → runtime QA → `pass`, confirmado en vivo con un revisor
real detectando una inyección de comandos de prueba.

## Honestidad sobre el árbol

Nada de este trabajo está commiteado (regla de la sesión: solo se commitea si el usuario lo pide
explícitamente). Esta evidencia certifica el árbol de trabajo vivo, no un commit.
