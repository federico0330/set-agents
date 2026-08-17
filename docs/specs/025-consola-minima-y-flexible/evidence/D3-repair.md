# D3-posturas-de-autonomia — reparación consolidada

- Base de reparación: `0d20287372a6eacb8ad60875b83b4d0b84b39be4`.
- Alcance: sólo D3-F01, D3-F02 y D3-F03. Sin `verify.sh` ni cambios de D4/D5.

## Plan finding → cambio → prueba

| Finding | Cambio mínimo | Prueba focal |
|---|---|---|
| D3-F01 | Retirar `postura_gate`, que sólo consumía el test; hacer que la mordida escriba cada postura en el `config.toml` runtime y compruebe las instrucciones distintas que consume el orquestador instalado. | Tres escrituras CLI aisladas + doctrina generada de los cuatro lanes. |
| D3-F02 | Proteger el bloque de metodología en el mismo canal y sus dos reglas: SDD para triage ambiguo; RDD sólo propone `strict_tdd: true` para paquete nuevo. | Preferencias SDD/RDD persistidas y assertions contra la doctrina instalada. |
| D3-F03 | Declarar una resolución fail-closed idéntica para ausente, desconocido, tipo inválido o TOML ilegible: `autonoma`/`off`; cubrir pantalla y canal. | Configuraciones inválidas temporales más el contrato textual que consume el orquestador. |

## RED

Se agregaron primero las mordidas de D3-F01/F02/F03. Comando:

```text
python3 -m unittest -v tests.test_harness.HarnessTests.test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario tests.test_harness.HarnessTests.test_rdd_se_reconcilia_con_strict_tdd_no_lo_duplica tests.test_harness.HarnessTests.test_configuracion_invalida_resuelve_igual_en_pantalla_y_doctrina
```

Exit `1`: falló D3-F01 porque `postura_gate` aún existía; las otras dos mordidas expusieron además el path incorrecto del artefacto Codex (`orchestrator.toml`), corregido en el test antes del verde. No se tocó estado ni configuración real.

## Reparación y GREEN

| Finding | Cambio | Prueba/evidencia |
|---|---|---|
| D3-F01 | Se eliminó `postura_gate` de `ai/scripts/set_agents_app.py`; `tests/test_harness.py` escribe cada postura en el `config.toml` temporal y verifica las tres decisiones en el prompt canónico y en los cuatro artefactos que consume el orquestador (`.md`/Codex `.toml`). `Global/_canonical/agents/orchestrator.md` declara explícitamente el canal y sus resultados para una acción mutante+delegante. | La mordida assertó `act on your own` / `wait for the user's explicit confirmation` / `before EVERY delegation` y que no existe el helper espejo. |
| D3-F02 | La mordida de metodología ahora protege el canal instalado en los cinco artefactos: `metodologia_preferida`, SDD para triage ambiguo y RDD sólo para paquete nuevo, sin sobrescribir `strict_tdd`. La prueba de pantalla persiste y vuelve a leer tanto `rdd` como `sdd`. | Los 9 tests focales pasan; RDD sigue remitiendo a ADR-0022/`strict-tdd`, sin segundo toggle. |
| D3-F03 | La doctrina canónica y los cuatro derivados fijan fallback fail-closed común: ausente/desconocida/no-string/ilegible → `autonoma` y `off`, igual que `postura_actual()`/`metodologia_preferida()`. | La mordida escribe un TOML con valores inválidos y luego TOML malformado; la pantalla y el contrato del consumidor resuelven los mismos defaults. |

Comandos GREEN:

```text
./build.sh                                      # exit 0; Generated tracked artifacts for go-zen.
./build.sh --check                              # exit 0; GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
python3 -m unittest -v <9 tests D3 focales>     # exit 0; Ran 9 tests in 6.307s; OK
```

No se ejecutó `verify.sh` ni suite global, por instrucción del paquete. Pendiente al cerrar: commit y `git diff --check` sobre ese commit.

## Commit

- Commit: `22bed24f8bab7baf3a2e3678442312d81769bdb6` (se actualizará al enmendar esta evidencia).
- `git diff --check HEAD^ HEAD`: exit `0`.
