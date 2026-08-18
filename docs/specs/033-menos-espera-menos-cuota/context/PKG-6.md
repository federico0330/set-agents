# Context pack — PKG-6 cuotas-que-alcanzan

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-6.1–AC-6.6**. Último. No bajar calidad para ahorrar.

**Objetivo.** Bajar despachos y `cache_read` por paquete: context pack obligatorio, gates P001 sin modelo, panel acotado por riesgo, presupuesto visible al 80%, y que la Sección 2 de `cost-report` deje de medir cero.

## Paths (leídos hoy)

- `ai/scripts/feature_state_lib/model.py:23,37` — fases; `PACKAGE_PLANNING` → `PACKAGE_IMPLEMENTATION` **sin** guarda de `context_pack`. Campo default `None` en `:308`.
- `ai/scripts/feature_state_lib/transitions.py:17-20,62-63` — `check_transition` no mira context pack al entrar a implementación. AC-6.1: misma clase de guarda que el resto del state machine; un paquete sin `docs/specs/<feature>/context/<PKG>.md` no entra a `PACKAGE_IMPLEMENTATION`.
- `Global/_canonical/agents/implementer.md:12` — “read it FIRST **if it exists**”. El prompt no alcanza; la fase tiene que negar.
- `ai/scripts/feature-state.py:397-448` — `cmd_record_spawn` (vive **fuera** del lib): incrementa `attempts.spawns`, bloquea al **techo** (`:414-416`), no al 80%. AC-6.2/6.4 van acá o se extraen al lib.
- `ai/scripts/feature-state.py:471-520` — `cmd_start_review_panel`: toma `--role` del caller; **no** lee `complexity`/`risk`. AC-6.3: small+low → un revisor; medium/high → panel completo. La regla en el state machine, no en el criterio del día.
- `ai/scripts/feature_state_lib/cli_review.py:75-88` — `panel_roles()` exige ≥1 `--role`; cita `required_reviewers` del planner. Hoy el JSON del paquete **no** persiste esa lista.
- `ai/scripts/feature_state_lib/model.py:108-113` — `MODE_BUDGETS` (spec **coincide**): feature 12 / scoped 8 / quick-fix 4 / incident 6. `validate_state` (`:396-397`) rechaza **después** de `spawns > techo`.
- `ai/scripts/feature_state_lib/render_status.py:233` — ya imprime `spawns/techo`. Falta aviso al **80%** en status y narración (AC-6.4).
- `ai/scripts/cost-report.py:14-25,617-645` — Sección 2 = `routing.db` `dispatches` vía `collect_pi` (`:329-337`, `usage_status='ok'`). En anfitrión Cursor los subagentes **no** pasan por `*_spawn.py` / `--route-decide` → 246 sesiones en §1 y **cero** en §2. AC-6.5: ingerir lo que el harness sí registra (`ai/state/features/*.json` `spawns[]` / history `record-spawn`), sin inventar `--route-decide`.
- P001 allowlist: `ai/scripts/claude_local_gate_guard.py:43-61` (`py_compile` de 2 scripts, `--help`, `check-owned-paths.py`, `git diff --check`, `record-gate`). Rol `local-gate-runner` en `generate.py:33`. AC-6.2: `record-spawn` de `gate-runner` cuyos comandos son todos P001 se rechaza nombrando `local-gate-runner`.
- Separación de deberes ya anclada: `NON_ACCEPTING_ACTORS` (`model.py:89`) incluye `implementer`; `package_accept_ready` `:505-508`; test `test_harness.py:10100-10109` (hoy clava `repair-agent`). AC-6.6: test que **fije** que achicar el panel no habilita auto-aprobación ni revisor que parchea.

## ADRs / invariantes

- ADR-0009 — implementer nunca aprueba su trabajo; no se toca para ahorrar.
- ADR-0026 — evidencia sobre memoria; el context pack es el antídoto al 92% `cache_read`.
- `MODE_BUDGETS` — el techo del **modo** (`scoped`=8 acá); no bajar `max_deep_review_cycles` por decreto.
- Este runtime es Cursor: **nunca** `--route-decide` ni `*_spawn.py --dispatch-*`.
- ADR-0041 — heartbeat; sin pipe/tail.
- `Global/*/hooks/feature_state_lib` es **generado** por `build.sh`. No editar a mano.

## Validación local

```
python3 -m unittest tests.test_harness.HarnessTests.test_record_spawn_mints_sequential_spawn_ids_from_the_counter tests.test_harness.HarnessTests.test_accept_package_rejects_open_findings_and_bad_actors
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests
python3 ai/scripts/cost-report.py --project /home/federico/SET-AGENTES --since 2026-08-10
./build.sh --check
git diff --check
```

Tests nuevos de AC-6.1–6.6 en `tests/test_harness.py` (o módulo vecino). `pytest` no existe. La Sección 2 del report debe dejar de ser cero (AC-6.5).

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]` — no auth/secrets/PII. AC-6.6 es invariante de proceso, no superficie de security-auditor.
- `runtime_surface`: **true** — el state machine y `cost-report` son el producto del harness (transiciones y persistencia observables).
- test owner: **implementer**. `strict_tdd`: **false**.

## Fuera de alcance

Bajar ciclos de review · sacar finding-verifier · que el implementer se auto-apruebe · `--route-decide` · editar `Global/` a mano · 032 Cursor target · PKG-1..5.

## Excepciones recomendadas

`owned_paths` = `ai/scripts/feature_state_lib`, `ai/scripts/cost-report.py`.

- `ai/scripts/feature-state.py` — `cmd_record_spawn` (`:397`) y `cmd_start_review_panel` (`:471`) **no** están en el lib.
- `tests/test_harness.py` (y/o `tests/test_*.py` nuevo) — AC-6.1–6.6. El owned no incluye `tests/`.

## Mordida

AC-6.1: `cp` de `transitions.py`, sacar la guarda de context pack, intentar `transition PACKAGE_IMPLEMENTATION` sin pack → el test nuevo rojo; `cp` restaurar → verde. AC-6.6 igual contra `NON_ACCEPTING_ACTORS`. Nunca `git checkout`/`restore`/`stash`.
