# D3-posturas-de-autonomia — delta-review ciclo 2

- Rol: `delta-reviewer`; revisión read-only del código, tests y state. Este informe es el único
  artefacto escrito.
- Base: `57455378796b253a39962580758085549fd7239d`.
- Reparación: `bbed1d3a1725a7caae680b876e646ae4d8927abe`; evidencia integrada en
  `3b2324f217076a62e053ba28da780187a8b9d4da`.
- Alcance: cierre focal de D3-F01 (AC-06), asociación `postura -> acción` y precedencia de
  ADR-0037. Sin suite global, `verify.sh`, cambios de código/state ni revisión completa.

## Verificación focal

El delta de reparación sólo modifica el contrato doctrinal canónico, sus cuatro derivados y la
prueba focal; el commit siguiente agrega la evidencia. No cambia store, CLI, spawners,
arquitectura ni contratos públicos.

`Global/_canonical/agents/orchestrator.md:580-600` deja una única precedencia observable:
`adr_0037_resolved > postura`. Una decisión ya resuelta se ejecuta sin volver a preguntar; la
postura sólo decide una acción aún no resuelta. Dentro de ese caso, el contrato asocia exactamente:

- `autonoma -> act_on_your_own`
- `consultiva -> propose_and_wait_for_explicit_confirmation_before_mutation`
- `todo_consultado -> ask_and_wait_before_every_delegation`

Esto es consistente con ADR-0037: sus cuatro fuentes resuelven primero y una respuesta existente se
ejecuta con `log-decision` (`Global/_canonical/agents/orchestrator.md:628-636`). La postura no
reabre repairs, gates ni el siguiente paquete ya aprobado.

`tests/test_harness.py:1058-1103` persiste cada postura, parsea la tabla asociativa de los cinco
artefactos runtime y obtiene la acción por la key realmente persistida. Ya no son búsquedas
independientes de substrings.

| Comando / probe | Exit | Resultado |
|---|---:|---|
| Test focal `test_las_tres_posturas_dan_tres_resultados_distintos_para_el_mismo_escenario` con heartbeat | 0 | `Ran 1 test`; `OK`. |
| Mutación en memoria: intercambiar las acciones de `autonoma` y `consultiva` en los cinco contratos | 0 del wrapper esperado | `tests=1 failures=1 errors=0 mutated_reads=5`; la mordida detectó la permuta. |
| Mutación en memoria: invertir `adr_0037_resolved > postura` | 0 del wrapper esperado | `tests=1 failures=1 errors=0 mutated_reads=5`; la mordida detectó la precedencia incorrecta. |
| `git diff --check 5745537... 3b2324f...` | 0 | Sin salida. |

Se tomó además la evidencia post-repair de `D3-cycle2-repair.md`: 9 focales D3 verdes y
`./build.sh --check` con `GLOBAL_TREE_SYNC_OK` / `BUILD_CHECK_PASS`. No se corrió la suite global
ni `verify.sh` en esta revisión.

## Cierre

- **D3-F01 — closed.** El contrato runtime ya es inequívoco, la asociación se prueba como mapa y
  las mutaciones de asociación y precedencia rompen la mordida.
- D3-F02 y D3-F03, cerrados en el delta anterior, no fueron tocados ni reabiertos.
- Nuevos findings: ninguno.

VERDICT pass

```json
{
  "package_id": "D3-posturas-de-autonomia",
  "verdict": "pass",
  "closed_findings": [
    {
      "id": "D3-F01",
      "evidence": "Global/_canonical/agents/orchestrator.md:580-600 fija ADR-0037 > postura y el mapa postura->accion; tests/test_harness.py:1058-1103 lo parsea por key persistida. Los probes de permuta de filas e inversion de precedencia produjeron 1 failure cada uno en cinco artefactos runtime."
    }
  ],
  "new_or_reopened_findings": [],
  "requires_full_review": {
    "value": false,
    "reason": "La reparacion fue focal al contrato doctrinal y su mordida; no cambio arquitectura, contratos publicos ni superficie de riesgo."
  }
}
```
