# D3-posturas-de-autonomia — delta-review focal

- Rol: `delta-reviewer`, read-only sobre código, tests y state; este archivo es la única evidencia escrita.
- Base revisada: `0d20287372a6eacb8ad60875b83b4d0b84b39be4`.
- Repair integrado: `57455378796b253a39962580758085549fd7239d` (`HEAD` al iniciar).
- Alcance: cierre de D3-F01/F02/F03 y regresiones relacionadas en el canal runtime de postura,
  metodología preferida y fallback. Sin suite global, `verify.sh`, cambios de código/state ni commits.
- Skills aplicadas: `request-triage` (análisis focal), `structured-findings`, `package-review`,
  `audit-diff` y `quality-gates` sólo para los comandos reales declarados por el paquete.

## Entradas y checkpoint

- Leídos primero `context/D3-posturas-de-autonomia.md`, luego `D3-review.md`,
  `D3-verification.md`, `D3-repair.md`, `D3-gates-runtime-qa.md`, `spec.md` (AC-06..08),
  ADR-0054, ADR-0022, ADR-0025 y ADR-0037.
- El diff `0d202873..5745537` toca sólo la doctrina canónica y sus cuatro derivados,
  `set_agents_app.py`, `tests/test_harness.py` y la evidencia de reparación. No cambia el store,
  spawners, arquitectura ni contratos públicos.
- El state del paquete declara `strict_tdd: false` y `repair_ceiling: null`; por eso
  `strict-tdd-verify` no aplica y el ceiling formal debe ser el PASS aditivo definido por ADR-0023.
- Riesgo focal antes de pruebas: la nueva regla de resultados distintos en
  `Global/_canonical/agents/orchestrator.md:590-602` convive con la excepción que dice que ninguna
  postura reabre acciones ya resueltas por ADR-0037. Se verificará si la mordida detecta esa
  contradicción o si sólo busca substrings.

## Comandos y resultados

| Comando / reproducción | Exit | Resultado |
|---|---:|---|
| `python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v <9 focales D3>` | 0 | `Ran 9 tests in 6.265s` / `OK`: persistencia, pantalla, canal textual, SDD/RDD, invalid/malformed y writer compartido. |
| `python3 ai/scripts/heartbeat-run.py --interval 20 -- ./build.sh --check` | 0 | `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`, `BUILD_CHECK_PASS`. |
| `python3 ai/scripts/check-repair-ceiling.py --state-file ai/state/features/025-consola-minima-y-flexible.json --package-id D3-posturas-de-autonomia --baseline 0d202873...` | 0 | `REPAIR_CEILING_PASS`; el state no tiene ceiling congelado, por lo que no había presupuesto que exceder. |
| `git diff --check 0d202873... 5745537...` | 0 | Sin errores. |
| Mutation probe en memoria: permutar la asociación `autonoma`/`consultiva` tanto en la tabla como en la frase de “runtime outcomes”, conservando las mismas palabras | 0 | Las dos mordidas de postura siguieron verdes: `tests_run=2 failures=0 errors=0`, `mutated_doctrine_reads=7`. No se escribió el árbol. |
| Mutation probe en memoria: retirar todo `## Metodología preferida (ADR-0054)` de los cinco prompts | 0 del wrapper | El test focal falló como se esperaba en `tests/test_harness.py:1163`: `tests_run=1 failures=1`, `mutated_doctrine_reads=5`. Confirma que F02 ahora sí muerde el canal. |
| Scan de `/home/federico/.{claude,codex,pi}` y `~/.config/opencode` | 0 | Los cuatro prompts instalados existen pero tienen cero matches D3; el runtime de esta máquina todavía usa la instalación anterior. ADR-0054:48-54/111-115 declara que hace falta una instalación inicial, y el paquete prohíbe `--install`, por lo que esto limita la evidencia E2E pero no crea un finding separado. |

No se corrió suite global ni `verify.sh`; no se modificó código, state, configuración instalada ni commits.

## Cierre de findings

- **D3-F01 — reopened.** `postura_gate` fue retirado, pero la nueva prueba no relaciona el valor
  persistido con su acción: en `tests/test_harness.py:1079-1084` comprueba por separado que la key
  y el texto de acción aparezcan en el mismo documento. La reproducción permutó las asociaciones
  y los tests siguieron verdes. Además el canal real es ambiguo: la tabla exige confirmar toda
  mutación/delegación (`Global/_canonical/agents/orchestrator.md:580-588`) y a continuación dice
  que ninguna postura vuelve a preguntar por repairs/gates/paquetes ya aprobados (`:588-591`).
  Para el mismo spawn mutante ya aprobado, AC-06 permite una sola salida, pero el prompt admite dos.
- **D3-F02 — closed.** `tests/test_harness.py:1139-1166` protege los cinco prompts y las reglas
  `sdd`/`rdd`; retirar el bloque hace fallar el test. La preferencia `rdd` y luego `sdd` persiste
  por procesos reales (`:1123-1137`), y RDD sólo orienta paquetes nuevos sin sobrescribir
  `strict_tdd` (`Global/_canonical/agents/orchestrator.md:597-612`).
- **D3-F03 — closed.** La app resuelve desconocido/no-string/malformed a `autonoma`/`off` y la
  doctrina canónica + cuatro derivados fija el mismo fallback
  (`Global/_canonical/agents/orchestrator.md:570-572`; test `tests/test_harness.py:1168-1190`).
- **Nuevos findings:** ninguno. La contradicción y la debilidad de asociación pertenecen al mismo
  outcome de D3-F01, no justifican duplicarlo.

## Reporte

VERDICT repair_required

```json
{
  "package_id": "D3-posturas-de-autonomia",
  "verdict": "repair_required",
  "closed_findings": [
    {
      "id": "D3-F02",
      "evidence": "tests/test_harness.py:1139; el mutation probe que retiró metodología falló, y los focales persistieron sdd/rdd"
    },
    {
      "id": "D3-F03",
      "evidence": "Global/_canonical/agents/orchestrator.md:570 y tests/test_harness.py:1168 fijan el mismo fallback para inválido/malformado"
    }
  ],
  "new_or_reopened_findings": [
    {
      "id": "D3-F01",
      "status": "reopened",
      "severity": "high",
      "category": "testing",
      "acceptance_criterion": "AC-06",
      "file": "tests/test_harness.py",
      "line": 1079,
      "evidence": "La mordida busca key y acción independientemente; al permutar autonoma/consultiva en los prompts, ambas pruebas siguieron pasando. El prompt también ordena confirmar EVERY delegation y simultáneamente no preguntar por delegaciones ya aprobadas (orchestrator.md:580-591).",
      "reproduction": "Mutation probe Path.read_text: asociación permutada en siete lecturas; 2 tests, 0 failures. Los cuatro prompts instalados actuales tampoco contienen D3, por lo que no existe evidencia de un agente real que cierre la brecha.",
      "required_outcome": "Hacer inequívoca la precedencia conforme AC-06 y probar que una postura persistida concreta produce su acción asociada a través del canal efectivamente consumido, con un decisor runtime hermético o escenario de agente controlado; una búsqueda independiente de substrings no alcanza.",
      "suggested_scope": "Sólo bloque ADR-0054 de orchestrator y mordida focal D3; preservar store, spawners y D4/D5."
    }
  ],
  "requires_full_review": {
    "value": false,
    "reason": "El repair no cambió arquitectura, contratos públicos ni superficie de riesgo; resta una corrección focal del canal/prueba de F01."
  }
}
```
