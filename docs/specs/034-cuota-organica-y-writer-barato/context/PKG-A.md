# Context pack — PKG-A ruteo-organico-enforceable

Spec: `docs/specs/034-cuota-organica-y-writer-barato/spec.md` (hash `539a4ff6…d9721`). **AC-A.1–AC-A.6**. Primero. HOW: ADR-0064.

**Objetivo.** Un cambio 1–3 archivos sin señal de riesgo **no puede** entrar a `scoped`/`feature` en silencio. Quick-fix = `implement → gate → log-quickfix` (sin `init`). `init --mode scoped|feature` exige `--risk-signal TOKEN` o muere `RISK_SIGNAL_REQUIRED`.

## Paths

- `Global/_canonical/skills/request-triage/SKILL.md:88-98` vs `:122` — quick-fix = default 1–3; la tabla llama `scoped (default)`. Unificar. Tokens `:73-75` + `user-asked-full-pipeline`.
- `Global/_canonical/agents/orchestrator.md:24-41` — ADR-0020 read-side (el 3). No cambiar el número. Alinear la frase write-side con la skill.
- `ai/scripts/feature-state.py:875-878` — `--mode` default **sigue** `scoped`. Efecto: `init` desnudo falla. No cambiar el default a `quick-fix` (AC-A.6).
- `ai/scripts/feature_state_lib/cli_lifecycle.py:150-181` — `cmd_init` no persiste señal. Agregar `--risk-signal`; sin token en scoped/feature → `RISK_SIGNAL_REQUIRED` y **no** deja state válido. Token desconocido → `RISK_SIGNAL_INVALID`. `quick-fix` e `incident` no exigen flag.
- `ai/scripts/feature_state_lib/model.py` — `RISK_SIGNAL_TOKENS` frozen-set (design §5) y `risk_signal` aditivo en `base_state` (`.get()`, sin backfill).
- `ai/scripts/feature-state.py:1194-1201` — `log-quickfix` flags **intactas** (AC-A.4).
- Tests: `tests/test_harness.py` (`test_log_quickfix_appends_and_renders` ~`:4968` se queda). Nuevo test de mordida AC-A.2.

Tokens cerrados: `money-billing` | `data-migration` | `auth-pii` | `public-contract` | `multi-module` | `user-asked-full-pipeline`.

## ADRs / invariantes

- ADR-0064 — el observable es el CLI, no un LLM. Fixture = `init --mode scoped` sin flag sobre un 1–3/copy.
- ADR-0020 — el 3 es constante cruzada; read-side intacto.
- 033 AC-6.1 — quick-fix **no crea** paquete → no hay context pack. Gate rojo en quick-fix: reintento o escala con señal; **no** salvage (AC-A.5).
- AC-X.2 — solo `feature-state.py` escribe el JSON. AC-X.1 — no tocar 033. AC-X.3 — no Engram.

## Validación local

```
python3 -m unittest tests.test_harness.HarnessTests.test_log_quickfix_appends_and_renders
python3 -m unittest tests.test_harness  # o el módulo del test nuevo AC-A.2
./build.sh --check
git diff --check
```

`pytest` no existe. **strict-TDD (ADR-0022):** el test de A.2 se escribe primero; se ve ROJO con un `init --mode scoped` sucio (sin flag); restaurar → VERDE. Nunca `git checkout`/`restore`/`stash` para la mordida — `cp` del módulo.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]` — doctrina + guarda CLI. Tokens de producto, no PII/auth/pagos. `complexity=small` + `risk=low` para que el motor (`required_reviewers_for`) no meta `security-auditor`.
- `runtime_surface`: **false** (waiver: harness CLI/docs, sin UI de app).
- test owner: **implementer** (focused). `strict_tdd`: **true** (mordida A.2).
- `selected_role`/`model`: implementer / inherit. Cursor host; no `--route-decide`.

## Fuera de alcance

Salvage / techo frontier / pins Cursor / `models.toml` / `generate.py` / `cost-report.py` / 033 tui-wizard-lanes / Engram / cambiar `MODE_BUDGETS` / aflojar `log-quickfix`.

## Excepciones recomendadas

`owned_paths` ya incluye `tests/test_harness.py`. Si el test nuevo vive en `tests/test_*.py` vecino, `--exception` ese archivo.

## Mordida

Fixture: blast radius 1–3 (copy), sin señal de la lista, `init --mode scoped` **sin** `--risk-signal` → comando falla `RISK_SIGNAL_REQUIRED`, no hay state válido, test ROJO si ese init es aceptado. `init --mode quick-fix` no pinta A.2 de rojo. Ausencia de `init` = camino feliz.
