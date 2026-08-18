# Context pack — PKG-1 una-sola-lane-opencode

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-1.1–AC-1.7**. Quinto (después de PKG-3). **AC-1.6 no es opcional.**

**Objetivo.** Una sola dimensión OpenCode: el usuario elige un modelo por área, no una lane. Los prefijos de proveedor (`openai/…`, `opencode/…`, `opencode-go/…`) **siguen**. Lo que muere es el preset `go-zen|zen|openai-only`.

## Paths (leídos hoy)

- `ai/scripts/models_config.py:31` — `LANES = ("go-zen", "zen", "openai-only")`. Spec **coincide**. ~46 usos (resolve, load, emit).
- `ai/scripts/models_config.py:97-102` — `active_profile()` lee `active-profile` (hoy `go-zen`).
- `ai/scripts/models_config.py:177-178` — `[session].opencode_small_model` debe cubrir exactamente `LANES` (dict). AC-1.4: pasa a string.
- `ai/scripts/models_config.py:377-411` — `detect_subscriptions` (se **queda**, panel tri-estado) vs `auto_profile()` (se **va** con el selector de lane).
- `ai/scripts/models_config.py:433-459` — `resolve_role`: merge lane-por-lane, `opencode_model = lanes.get(profile)`.
- `models.toml` — **38** mapas `opencode = { … }` (grep hoy). Conservar el valor **`go-zen`**. `opencode_small_model` en `:54` (tres keys; `openai-only` es gpt-5.4-mini, las otras north-mini). **18** tablas `[roles.<rol>.tiers.<tier>]` (`:215-296`: debugger/delta-reviewer/finding-verifier/implementer/package-reviewer/security-auditor × fast/balanced/frontier) — las tres lanes ya son el mismo modelo; un test debe **probarlo** antes de colapsar (AC-1.5). `[roles.local-gate-runner]` `:257-258` solo tiene `"go-zen"`: no es de las 18; colapsar sin inventar keys.
- `ai/scripts/setup_models.py:31` importa `LANES`; picker Campo `:378` ofrece `opencode.{lane}`; panel `:230` `lane:` y `:275` `OPENCODE[{profile}]`. AC-1.3: Campo = `["claude","codex","codex_effort","opencode"]`; columna `OPENCODE`; sin `lane:`.
- `ai/scripts/generate.py:796-807` — `--profile`; default `active_profile()`.
- `build.sh:13,43,123-131` — flag `--profile`; `--check` fuerza `go-zen`.
- `ai/scripts/verify.sh:30` — `--profile go-zen` (owned de PKG-5; hay que actualizarlo acá cuando el flag muera).
- `active-profile` — un archivo, contenido `go-zen`. Desaparece (AC-1.2).
- AC-1.6: `routing_core/domain.py:27-52` clasifica `quota_exhausted`; `routing_core/store.py:847-897` cierra y dispara un fallback. Feature **011-quota-failover** `final_state=BLOCKED` (`docs/historia/estado-2026-08/features/011-quota-failover.json:32`, AC-06 humano). Probar **(a)** el router elige otro y lo registra **o (b)** falla ruidoso nombrando proveedor + acción. Prohibido: cuelgue, traceback crudo, fallback silencioso a un modelo no elegido. Preferir (b) en owned paths; `routing_core` solo si (a) es la verdad y hace falta un hook de test.
- 7 tests a **reescribir** (no borrar, salvo `test_auto_profile.py` entero si la lane desaparece — nota en el commit: qué invariante dejó de existir): `tests/test_auto_profile.py`, `test_decide_always.py`, `test_harness.py`, `test_models_wizard_ui.py`, `test_probe_subscriptions.py`, `test_routing.py`, `test_spawn_materialization.py`.

## ADRs / invariantes

- ADR-0048 — overlay de suscripciones; el rename `local`→`openai-only` ya está. Este paquete **elimina el eje**, no lo renombra otra vez.
- ADR-0029 — tri-estado; `detect_subscriptions` intacto.
- 011 BLOCKED — AC-1.6 no asume failover vivo.
- ADR-0041 — heartbeat; sin pipe/tail.

## Validación local

```
python3 -m unittest tests.test_auto_profile tests.test_probe_subscriptions tests.test_models_wizard_ui tests.test_decide_always tests.test_spawn_materialization
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_routing tests.test_harness
python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check
git diff --check
```

`pytest` no existe. Más el test nuevo de AC-1.6.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]` — contrato de modelos, no auth/PII/UI web. (Complejidad high no suma especialistas por sí sola.)
- `runtime_surface`: **true** — generate/wizard/resolve cambian comportamiento observable.
- test owner: **implementer**. `strict_tdd`: **false**.

## Fuera de alcance

Prefijos de proveedor · panel tri-estado de suscripciones · implementar 011 · Cursor target 032 · `Global/` a mano (sale de `build.sh`) · relajar tests para pasar.

## Excepciones recomendadas

`owned_paths` no incluye `tests/` ni `verify.sh`.

- `tests/test_auto_profile.py`, `tests/test_decide_always.py`, `tests/test_harness.py`, `tests/test_models_wizard_ui.py`, `tests/test_probe_subscriptions.py`, `tests/test_routing.py`, `tests/test_spawn_materialization.py` — AC-1.7.
- `ai/scripts/verify.sh` — `:30 --profile go-zen` queda mentira cuando el flag muere.
- `ai/scripts/routing_core/` — **solo** si AC-1.6(a) necesita un seam; si no, no.

## Mordida

AC-1.6 y cada test reescrito: `cp` del módulo de producción, restaurar un mapa de 3 lanes o un silencio de agotamiento, rojo, `cp` volver, verde. Nunca `git checkout`/`restore`/`stash`.
