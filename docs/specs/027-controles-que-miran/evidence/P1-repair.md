# P1 repair evidence — alcance y aislamiento

## Resultado

- `package_id`: `P1-alcance-y-aislamiento`
- `status`: `REPAIRED_WITH_PENDING_PACKAGE_GATES`
- `repaired_findings`: `P1-F01` (medium, upheld)
- `changed_files`: `tests/test_harness.py` (ya contenía el arreglo antes de esta pasada); este archivo de evidencia.
- `remaining_findings`: ninguno para P1-F01.
- `blockers`: los dos módulos aislados y los gates de paquete no terminaron dentro del límite de 30 s de la ejecución encapsulada; se indican como **sin verificar**, no como aprobados.

## P1-F01 → corrección → verificación

| Finding | Cambio mínimo | Prueba |
| --- | --- | --- |
| `P1-F01`: `_import()` confundía una clave ausente con `sys.modules[name] is None` | `tests/test_harness.py:31-35` define `_SYS_MODULES_ABSENT`; `:318-326` obtiene con `sys.modules.get(name, _SYS_MODULES_ABSENT)` y restaura por identidad. La clave presente con `None` vuelve a quedar presente y con ese mismo valor. | `tests/test_harness.py:8663-8723` cubre entrada previa con módulo, ausente y presente con `None`; en particular `:8711-8718` verifica presencia y valor `None`. |

La inspección confirmó que el árbol ya traía el arreglo con centinela. No se reescribió lógica fuera de ese hallazgo.

## Mordida rojo/verde (caso `None`)

Respaldo/restauración exigidos, sin `git checkout`, `git restore` ni `git stash`:

```text
$ cp tests/test_harness.py /tmp/p1-f01-test_harness.before-bite.py
$ # mutación temporal: `get(name, _SYS_MODULES_ABSENT)` → `get(name)` y
$ # `previous is _SYS_MODULES_ABSENT` → `previous is None`
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it
F
FAIL: test_import_helper_leaves_sys_modules_exactly_as_it_found_it
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_harness.py", line 8715, in test_import_helper_leaves_sys_modules_exactly_as_it_found_it
    self.assertIn("set_agents_app", sys.modules,
AssertionError: 'set_agents_app' not found in {...} : _import() must restore a sys.modules[name] = None entry as present, not pop it
Ran 1 test in 0.042s
FAILED (failures=1)
```

Salida roja **recortada explícitamente**: se omitió el listado completo de `sys.modules` dentro de `{...}`; conserva la aserción, línea y conteo literales.

```text
$ cp /tmp/p1-f01-test_harness.before-bite.py tests/test_harness.py
$ cmp -s tests/test_harness.py /tmp/p1-f01-test_harness.before-bite.py && printf 'BITE_RESTORED=1\n'
BITE_RESTORED=1
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it
.
----------------------------------------------------------------------
Ran 1 test in 0.036s

OK
```

## Gates ejecutados

| Command | Resultado |
| --- | --- |
| `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness.HarnessTests.test_import_helper_leaves_sys_modules_exactly_as_it_found_it` | PASS — `Ran 1 test in 0.036s`, `OK`. |
| `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_harness` | **Sin verificar** — emitió literalmente `... heartbeat-run: still running, 20s without output`; esta ejecución encapsulada cortó a 30 s sin devolver código/conteo final. |
| `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.test_routing` | **Sin verificar** — emitió literalmente `... heartbeat-run: still running, 20s without output`; esta ejecución encapsulada cortó a 30 s sin devolver código/conteo final. |
| `git diff --check` | PASS — salida vacía, exit 0. |

No se corrieron `python3 -m unittest discover -s tests`, `./ai/scripts/verify.sh` ni `./build.sh --check`: **sin verificar**, fuera de la reparación puntual solicitada y sin resultado de los dos módulos aislados.
