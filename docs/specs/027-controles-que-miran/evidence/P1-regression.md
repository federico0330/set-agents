# P1-alcance-y-aislamiento — regresión dirigida

Fecha: 2026-08-14. Paquete: `P1-alcance-y-aislamiento`.

Esta corrida reutiliza la cobertura aceptada después del delta PASS. No se agregaron ni editaron tests en esta fase.

## Trazabilidad AC → test → resultado

| AC | Test (file:line) | Contrato observado | Resultado |
|---|---|---|---|
| AC-01 | `tests/test_harness.py:8521` — `test_owned_paths_gate_sees_untracked_new_files` | En un repositorio temporal, `danger.py` sin trackear aparece en `changed_files` y `out_of_scope`; el gate retorna `2` y `OWNERSHIP_FAIL`. | PASS — 1 test, 0.103 s. |
| AC-02 | `tests/test_harness.py:8619` — `test_module_isolation_gate_fails_if_the_sys_path_fix_regresses`; `tests/test_harness.py:8639` — `test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses` | Cada guarda lanza un `python3 -m unittest` en subproceso sin ayuda de orden de imports y exige salida 0, sin `ModuleNotFoundError` / `KeyError`. El choke point bajo prueba es `tests/__init__.py:18`. | PASS — 1 + 1 tests, 0.144 s + 0.242 s. |
| AC-03 | `tests/test_harness.py:8619`, `tests/test_harness.py:8639`, `tests/test_harness.py:8663` — `test_import_helper_leaves_sys_modules_exactly_as_it_found_it` | Las dos guardas de subproceso bloquean regresiones de aislamiento; la tercera comprueba los tres estados previos de `sys.modules["set_agents_app"]`: módulo presente, clave ausente y clave presente con valor `None`, preservando presencia y valor exactos. | PASS — 3 tests en las corridas dirigidas, incluida la de tres estados (0.045 s). |

## Comandos ejecutados

Todos los comandos fueron dirigidos; ninguno superó 20 segundos, por lo que no correspondió `heartbeat-run.py`.

```text
$ python3 -m unittest tests.test_harness.HarnessTests.test_owned_paths_gate_sees_untracked_new_files
Ran 1 test in 0.103s
OK
exit=0

$ python3 -m unittest tests.test_harness.HarnessTests.test_module_isolation_gate_fails_if_the_sys_path_fix_regresses
Ran 1 test in 0.144s
OK
exit=0

$ python3 -m unittest tests.test_harness.HarnessTests.test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses
Ran 1 test in 0.242s
OK
exit=0

$ python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it
Ran 1 test in 0.045s
OK
exit=0

$ git diff --check
<sin salida>
exit=0
```

## Integridad de tests y huecos

- Inspección de `git diff --unified=0 -- tests/test_harness.py tests/__init__.py`: no hubo líneas eliminadas que definan un `test_*`, ni eliminaciones de aserciones, `skip` u `only`; los tests de regresión de P1 continúan con aserciones reales. La única eliminación del diff de `tests/test_harness.py` reemplaza el `exec_module` del helper por la restauración de estado aceptada, no borra una prueba.
- No se halló un hueco verificable: AC-01 cubre el archivo no trackeado fuera de alcance, AC-02 queda cubierto por los dos subprocesos sin orden incidental de imports, y AC-03 tiene guardas explícitas más el tercer estado `sys.modules[name] = None` incorporado por P1-F01.
- No se ejecutaron la suite completa ni los módulos enteros `tests.test_harness` / `tests.test_routing` en esta fase, por estar expresamente fuera del alcance de esta validación dirigida. Sus resultados de aceptación previos constan en `P1-implementer.md`; para esta evidencia: **SIN VERIFICAR**.

Resultado final: **PASS**.
