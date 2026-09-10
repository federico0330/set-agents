# PKG-D2 — Runtime QA (hermetic)

**Date:** 2026-09-10  
**Candidate:** `/tmp/set-agents-049-d2.OwbVs7` @ `9bc4e2d28b3007a63ba86dc98f87f4634ed8178e`  
**Base ref:** `ff91f5538c3ee588b29a6b7267ad82439191b5c1`  
**Scope:** fake OpenCode 1.18.14 TTY observation, allow-list argv, sanitized env (no live OpenCode auth/login)

## Global boundary

```bash
git diff --name-only ff91f55..9bc4e2d | grep -c '^Global/' || true
```

| Exit | Output |
|------|--------|
| 0 | `0` |

Owned paths only:

- `docs/specs/049-identidad-honesta-modelos/evidence/PKG-D2-gates.md`
- `docs/specs/049-identidad-honesta-modelos/evidence/PKG-D2-tty.md`
- `tests/test_model_identity_integration_049.py`
- `tests/test_model_identity_tty_049.py`

## Check 1 — Fake OpenCode allow-list (exact argv only)

**Tests:** `FakeOpenCodeAllowListTests` (5)

```bash
cd /tmp/set-agents-049-d2.OwbVs7
python3 -m unittest -v tests.test_model_identity_tty_049.FakeOpenCodeAllowListTests
```

| Exit | Outcome |
|------|---------|
| 0 | OK. Accepts exact `session list --format json --pure` and `export --sanitize --pure <id>`; rejects `auth`, `login`, `install`, and incomplete argv variants. |

## Check 2 — Isolated TTY observation and degradation

**Tests:** `IsolatedTtyObservationTests` (4), `TtyPanelPresentationTests` (1)

```bash
cd /tmp/set-agents-049-d2.OwbVs7
python3 -m unittest -v \
  tests.test_model_identity_tty_049.IsolatedTtyObservationTests \
  tests.test_model_identity_tty_049.TtyPanelPresentationTests
```

| Exit | Outcome |
|------|---------|
| 0 | OK. Sanitized `PATH`/`HOME`/`SET_AGENTS_STATE`; absent OpenCode → `unobserved` with closed reason, overlay unchanged; refresh observes `opaque/luna` without retaining private fields; wizard **Actualizar datos** uses observation path only; panel separates observed Luna from neutral Terra default. |

## Check 3 — CLI integration (help split, model-state, session identity)

**Tests:** `CliMainHelpSmokeTests`, `HelpIntegrationTests`, `ModelStateArgvIntegrationTests`, `SessionIdentityIntegrationTests`

```bash
cd /tmp/set-agents-049-d2.OwbVs7
python3 -m unittest -v tests.test_model_identity_integration_049
```

| Exit | Outcome |
|------|---------|
| 0 | OK. Human vs advanced help split; invalid `--model-state` exits 2 without partial JSON; valid query emits single schema object; session Astra→Luna surfaces last-sent while Terra default stays neutral; observation does not mutate SET overlay or install artifacts. |

## Full scoped suite (AC-09)

```bash
cd /tmp/set-agents-049-d2.OwbVs7
python3 -m unittest -v tests.test_model_identity_tty_049 tests.test_model_identity_integration_049
```

| Exit | tests | failures | errors | elapsed |
|------|------:|---------:|-------:|--------:|
| 0 | 19 | 0 | 0 | ≈3.8s |

## Summary

| Check | Result |
|-------|--------|
| Fake OpenCode argv allow-list | PASS |
| Sanitized env / no host OpenCode | PASS |
| Observation + degradation paths | PASS |
| Wizard observation (no auth/install) | PASS |
| Panel Luna vs Terra presentation | PASS |
| CLI help + model-state integration | PASS |
| Session identity side-effect free | PASS |
| No `Global/**` in D2 delta | PASS |

**Overall:** PASS — hermetic fake OpenCode 1.18.14 unittest suite matches PKG-D2 TTY observation acceptance.
