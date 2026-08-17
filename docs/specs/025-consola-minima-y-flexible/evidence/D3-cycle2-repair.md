# D3-posturas-de-autonomia — reparación ciclo 2

- Estado: repaired; único finding D3-F01 (AC-06), base `57455378796b253a39962580758085549fd7239d`.
- Alcance permitido: contrato runtime de postura, su prueba focal y artefactos generados; sin state,
  D4/D5 ni `verify.sh`.

## Finding → reparación propuesta

| Finding | Cambio mínimo | Evidencia prevista |
|---|---|---|
| D3-F01 | Formalizar en la doctrina runtime una tabla asociativa `postura → acción` y una precedencia explícita `ADR-0037 resuelto > postura`; la postura sólo decide acciones aún no resueltas. | Prueba que persiste cada postura, lee ese contrato de cada lane y deriva la acción por su key; una permuta de filas debe fallar. |

## RED registrado

```text
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario
exit 1
AssertionError: falta el contrato runtime que lee el orquestador
```

## Reparación y GREEN

`Global/_canonical/agents/orchestrator.md` ahora declara `POSTURA_RUNTIME_CONTRACT_V1`, que el
orquestador consume al leer `config.toml`. Su orden es inequívoco:

```text
adr_0037_resolved > postura
adr_0037_resolved: execute_without_asking
```

Por lo tanto, una decisión ya resuelta por ADR-0037 siempre se ejecuta sin volver a preguntar;
sólo una propuesta todavía no resuelta se resuelve por postura. Para el mismo escenario
mutante+delegante no resuelto, el contrato asocia exactamente `autonoma` con actuar, `consultiva`
con proponer y esperar confirmación antes de mutar, y `todo_consultado` con preguntar y esperar
antes de toda delegación. `./build.sh` propagó el bloque sin edición manual a los cuatro lanes.

La prueba reemplazó la búsqueda independiente de substrings: exige el contrato, parsea su mapa y,
después de persistir cada postura real en un `config.toml` temporal, deriva y compara su acción
exacta en los cinco artefactos runtime.

| Validación | Exit | Resultado |
|---|---:|---|
| `./build.sh` | 0 | `Generated tracked artifacts for go-zen` |
| 9 pruebas focales D3 de `tests.test_harness.HarnessTests` (heartbeat) | 0 | `Ran 9 tests in 6.307s` / `OK` |
| Mutación en memoria: permutar las filas `autonoma` y `consultiva` en todos los contratos | 0 del wrapper esperado | `Ran 1 test`; `FAILED (failures=1)`, con el mapa asociado distinto del esperado; la mordida resiste la permuta. |
| `./build.sh --check` (heartbeat) | 0 | `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`, `BUILD_CHECK_PASS` |
| `git diff --check` | 0 | sin salida |

No se corrieron suite global ni `verify.sh`, por el alcance indicado. No se tocaron state, D4 ni D5.

## Archivos modificados

- `Global/_canonical/agents/orchestrator.md` y sus cuatro artefactos generados.
- `tests/test_harness.py`.
- Esta evidencia.

## Commit

- Pendiente al escribir esta evidencia: se añadirá el SHA del commit acotado tras el `git diff --check`
  final sobre el commit.
