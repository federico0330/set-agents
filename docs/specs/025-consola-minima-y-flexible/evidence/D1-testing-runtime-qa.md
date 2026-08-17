# D1-superficie-humana — testing y runtime QA

Ejecución sobre árbol integrado `211df01`. Evidencia incremental del gate-runner; no se modificó código ni estado.

## Expectativas

- Menú ASCII, sin doble espacio: `ai/scripts/set_agents_app.py:3721-3732`; test esperado `tests/test_harness.py:2672-2687`.
- Primer arranque sin emoji: `ai/scripts/set_agents_app.py:3738-3741`.
- Flags internas ocultas por default y visibles con `--avanzado`: `ai/scripts/set_agents_app.py:3856-3874`; tests `tests/test_harness.py:5530-5588`.
- Routing humano por default y sobre JSON con `--json`: `ai/scripts/set_agents_app.py:3826`; test `tests/test_harness.py` (test dirigido documentado en `docs/specs/025-consola-minima-y-flexible/evidence/D1-delta-review.md:31`).

## Gates

### Gate dirigido D1

Comando:

```bash
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_menu_items_carry_no_emoji_and_single_space_layout tests.test_harness.HarnessTests.test_internal_flags_hidden_from_default_help_shown_with_avanzado tests.test_harness.HarnessTests.test_internal_flags_cannot_be_silently_deleted tests.test_harness.HarnessTests.test_route_doctor_default_is_human_text_on_stderr_json_flag_preserves_machine_envelope
```

Salida relevante y exit code: `Ran 4 tests in 0.060s`, `OK`; exit code `0`.

### Suite global declarada

Comando exacto:

```bash
python3 ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
```

Resultado: completado con exit code `0`. Salida relevante: `SELF_SCAFFOLD_SYNC_OK files=2`, `GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4`, `BUILD_CHECK_PASS`; la suite unittest reportó casos `... ok` hasta completar el gate.

## Runtime QA observacional

### Ayuda y menú CLI

Comando:

```bash
python3 ai/scripts/set_agents_app.py --help
```

Exit code `0`. La salida muestra el parser de la consola, comandos de routing (`--route-explain`, `--route-doctor`, `--routing-migrate`) y la regla `--json` para salida de observabilidad; también confirma que las flags internas permanecen ocultas en ayuda default y que `--help --avanzado` las expone. Esto corresponde a `ai/scripts/set_agents_app.py:3856-3874` y `tests/test_harness.py:5530-5588`.

### Routing humano

Comando:

```bash
python3 ai/scripts/set_agents_app.py --route-doctor
```

Exit code `0`. Salida observable: spinner en stderr (`consultando routing…`, `consultando routing: listo`) y texto humano `route-doctor: OK`, `providers: ...`, `cache: ...`; no se imprimió un repr crudo. Satisface el contrato esperado en `ai/scripts/set_agents_app.py:3826`.

### Routing máquina

Comando:

```bash
python3 ai/scripts/set_agents_app.py --route-doctor --json
```

Exit code `0`. Salida observable: sobre JSON válido con `"command": "route-doctor"`, `"ok": true`, `"schema_version": 2`, `"reason_codes": []`, `"warnings": []`; la animación quedó fuera del sobre. Satisface el test y expectativa documentados en `docs/specs/025-consola-minima-y-flexible/evidence/D1-delta-review.md:31`.

## Veredicto

`VERDICT: pass`

La QA de CLI satisface el runtime surface declarado de D1 para menú/ayuda/routing. No hace falta waiver.
