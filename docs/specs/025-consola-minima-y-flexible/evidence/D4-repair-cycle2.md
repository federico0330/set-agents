# D4 repair cycle 2 — AC-11 / D4-F01

- Paquete: `D4-harness-por-CLI`
- Finding: `D4-F01` (AC-11): el escenario C anterior instalaba una lane nueva en un home virgen; no ejercitaba una sesión de una vez sobre una lane ya instalada ni probaba que esa instalación no fuese leída.
- Base declarada: `bbed1d3`.
- Alcance de esta única reparación: exponer `set-agents --virgin {opencode,claude,codex,pi} -- [args]`, que ejecuta sólo ese hijo con `HOME`, `TMPDIR` y todos los `XDG_*_HOME` en un directorio temporal 0700; no instala, no desinstala y elimina el directorio temporal al finalizar.

## RED (registrado antes del código de producto)

Comando:

```text
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane -v
```

Exit: `1`.

La nueva mordida primero instala los cuatro lanes en `TemporaryDirectory`, hashea sus árboles, invoca
`set-agents --virgin claude -- --version` contra un shim `claude` que sólo acepta un `HOME`/XDG aislado,
y después exige hashes idénticos. En la base falló con `set-agents: error: unrecognized arguments: --virgin claude -- --version` (exit `2` del hijo), que hizo fallar la aserción principal.

## Progreso parcial y próxima acción

Se agregó `cmd_virgin_session` y su despacho aislado en
`ai/scripts/set_agents_app.py`: argv sin shell, CLI allowlisted, ambiente mínimo, `HOME`/`CODEX_HOME`/XDG
temporales. Se conectó el intercepto temprano de `main()` y el texto de ayuda; la mordida se reejecutó verde:

```text
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_virgin_session_uses_an_isolated_home_without_reading_or_mutating_installed_lane -v
exit 0 — OK (1 test, 10.057s)
```

ADR-0055 y el escenario C de runtime QA ya reflejan el comportamiento. No se tocó `~`, no se ejecutó
instalación global. Gates finales:

```text
git diff --check
exit 0

./ai/scripts/verify.sh
exit 0 — SELF_SCAFFOLD_SYNC_OK; GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4; BUILD_CHECK_PASS
```
