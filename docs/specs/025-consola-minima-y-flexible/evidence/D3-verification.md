# D3-posturas-de-autonomia — verificación adversarial de hallazgos

- Rol: `finding-verifier`, independiente y read-only sobre código, tests, estado y commits; este archivo es la única evidencia escrita.
- Artefacto fijo verificado: `0d20287372a6eacb8ad60875b83b4d0b84b39be4` (`git rev-parse HEAD`, exit 0).
- Paquete/diff base: commit D3 `1da748e992b7be91126f7365abf8295edaf7d089`, padre `2f199d5ae39955ccfb99b841964f4639824812d5`; 10 archivos, 872 inserciones.
- Alcance: refutación focal de `D3-F01`, `D3-F02`, `D3-F03` contra AC-06..08, ADR-0054, diff completo D3 y gates previos. Sin suite global, `verify.sh`, reparación, D4 ni D5.
- Skills aplicadas: `request-triage` (modo análisis/verificación), `structured-findings`, `audit-diff`, `package-review` sólo en las superficies nombradas.

## Entradas leídas

- `docs/ai/knowledge/architecture.md` y `docs/ai/knowledge/_global/architecture.md` completos: sin invariantes acumulados adicionales.
- Context pack `docs/specs/025-consola-minima-y-flexible/context/D3-posturas-de-autonomia.md` completo.
- `evidence/D3-review.md` completo, incluyendo los tres hallazgos consolidados.
- `evidence/D3-gates-runtime-qa.md` completo: gate previo reporta 8 tests focales y CLI aislado verdes.
- `spec.md:54-73,97-104`: AC-06..08 y riesgo explícito de posturas decorativas.
- `docs/adr/0054-posturas-de-autonomia.md` completo: canal elegido = lectura directa del TOML por el agente desde doctrina estática; `strict_tdd` sigue siendo la única fuente real por paquete.
- `evidence/D3-implementer.md` completo: admite que no hubo E2E con un agente real, que `metodologia_preferida` no está conectada a código de triage/planning y que la mordida #3 es sólo una aproximación textual.

## Checkpoint estático

| Hallazgo | Evidencia inspeccionada | Resultado inicial |
|---|---|---|
| D3-F01 | `set_agents_app.py:1135-1148`, `test_harness.py:1058-1090`, búsqueda de referencias | El helper dice que ningún CLI lo llama; la única invocación encontrada está en el test (`:1067`). No hay guard/camino runtime Python que refute la desconexión. |
| D3-F02 | `test_harness.py:1073-1090,1110-1137`, doctrina `orchestrator.md:585-604` | La mordida del canal sólo itera `POSTURAS`; las pruebas de metodología cubren pantalla/config/skills, no la sección doctrinal ni una decisión del orquestador. |
| D3-F03 | `set_agents_app.py:1074-1078,1123-1125,1197-1199`; doctrina `orchestrator.md:563-590` | La app normaliza inválidos; la doctrina sólo sanciona ausente y enumera válidos. No hay fallback compartido ni prueba para edición manual inválida/malformada. |

Se ejecutarán reproducciones herméticas, sin mutar el árbol, antes de emitir verdictos.

## Reproducciones

### D3-F01 — helper desconectado

1. Búsqueda completa:

   - Comando: `rg -n "postura_gate" ai/scripts Global tests --glob '*.py' --glob '*.md' --glob '*.toml'`
   - Exit: `0`.
   - Salida: definición/docstring en `ai/scripts/set_agents_app.py:1135-1141` y única llamada en `tests/test_harness.py:1067`; ningún consumidor de producción.

2. Poison probe hermético: se importó `set_agents_app.py`, se escribió una config temporal con `todo_consultado`, se reemplazó `postura_gate` en memoria por un mock que falla si se invoca y se ejecutó `cmd_posturas()`.

   - Comando: `python3 - <<'PY'` (import registrado en `sys.modules`; `mock.patch.object(app, "postura_gate", poisoned)`; `app.cmd_posturas()`).
   - Exit: `0`.
   - Salida real:

     ```text
     POSTURA=todo_consultado
     cmd_posturas_rc=0
     reported_todo_consultado=True
     poisoned_postura_gate_calls=0
     ```

El helper puede romperse o no ejecutarse sin afectar el camino CLI que persiste/muestra la postura. La doctrina LLM es otro artefacto de prosa y tampoco llama el helper. AC-06/riesgo 3 (`spec.md:103-104`) exige que cambie conducta, no sólo que una función espejo devuelva tres strings. No apareció guard, consumidor runtime, AC ni test de regresión que refute el hallazgo.

Nota de ejecución: el primer intento del poison probe no registró el módulo dinámico en `sys.modules` y el Python interno falló con `KeyError: 'd3_app_f01'`; el comando compuesto terminó `0` porque después corrió `rg`. Se corrigió sólo el harness del experimento y el rerun independiente produjo la salida anterior. No fue una falla del producto.

### D3-F02 — canal de metodología no protegido

Se ejecutaron los 8 tests D3 bajo una mutación exclusivamente en memoria de `Path.read_text`: para cada doctrina de orquestador se eliminó el bloque desde `## Metodología preferida (ADR-0054)` hasta el siguiente heading, sin escribir ningún archivo. Así, cuando `test_el_canal_de_postura...` leyó canonical/Claude, vio una doctrina sin metodología.

- Comando: `python3 - <<'PY'` (patch de `Path.read_text` + `unittest.TestSuite` con los 8 tests enumerados en `D3-gates-runtime-qa.md`).
- Exit: `0`.
- Salida real:

  ```text
  ........
  ----------------------------------------------------------------------
  Ran 8 tests in 5.713s

  OK
  doctrine_files_read_without_methodology=2
  tests_run=8 failures=0 errors=0
  ```

La reproducción confirma exactamente el gap: el canal doctrinal de metodología puede desaparecer de los artefactos que inspecciona la mordida y los gates D3 actuales siguen verdes. `tests/test_harness.py:1079-1090` sólo fija path/ADR/`POSTURAS`; `:1110-1137` fija pantalla/config/skills, no `orchestrator.md:585-604` ni una decisión SDD/RDD. El propio implementer declara que `metodologia_preferida` no está wireado a código de triage/planning. No hay AC ni regresión que refute el hallazgo.

### D3-F03 — fallback divergente para configuración inválida

Probe temporal con los dos casos soportados por el hallazgo: valores TOML válidos pero fuera del vocabulario, y TOML malformado. Se parchearon en memoria `APP_CONFIG`/`STATE_DIR` hacia `/tmp`; no se tocó configuración real.

- Comando: `python3 - <<'PY'` (config temporal, lectura cruda con `tomllib` y resolución con `app.postura_actual()`/`app.metodologia_preferida()`).
- Exit: `0`.
- Salida real:

  ```text
  raw_postura=omnisciente
  ui_postura=autonoma
  raw_metodologia=otra
  ui_metodologia=off
  raw_malformed=TOMLDecodeError
  app_config_malformed={}
  ui_postura_malformed=autonoma
  ui_metodologia_malformed=off
  ```

La app normaliza por `set_agents_app.py:1123-1125,1197-1199` (y `app_config()` absorbe decode errors en `:1074-1078`), mientras la doctrina manda leer directamente las claves y sólo define fallback para ausente (`orchestrator.md:563-567,587-590`). ADR-0054 permite explícitamente edición humana de `config.toml` (`:111-115`). El test `test_postura_desconocida_no_se_acepta` sólo cubre `argparse` por CLI; no cubre el canal de edición humana que el ADR declara. No hay fallback doctrinal para desconocido/tipo inválido/malformado que refute la divergencia.

Nota de ejecución: el primer probe temporal tuvo el mismo `KeyError: 'd3_app_f03'` del import dinámico y exit `1`; el rerun corrigió sólo el registro del módulo y produjo la salida anterior. No fue una falla del producto.

## Verdictos

```json
{
  "package_id": "D3-posturas-de-autonomia",
  "verdicts": [
    {
      "id": "D3-F01",
      "verdict": "upheld",
      "reason": "La reproducción confirma que postura_gate sólo alimenta el test y no participa de ningún camino runtime; no hay evidencia suficiente para refutar que la mordida observable sea decorativa."
    },
    {
      "id": "D3-F02",
      "verdict": "upheld",
      "reason": "Con la sección doctrinal de metodología eliminada en memoria, los 8 tests D3 siguen pasando; el canal y sus reglas SDD/RDD no están protegidos por la regresión actual."
    },
    {
      "id": "D3-F03",
      "verdict": "upheld",
      "reason": "La reproducción confirma dos estados efectivos: la app muestra defaults para valores inválidos/malformados mientras el consumidor doctrinal lee el TOML crudo sin fallback equivalente."
    }
  ],
  "observations": [],
  "scope_recommendation": "Reparación consolidada limitada al canal runtime D3 y sus pruebas focales: conducta observable de postura, consumo/regresión de metodología y resolución consistente de configuración inválida. Mantener fuera D4/D5, spawners no necesarios, coord_policy y refactors ajenos."
}
```

## Destilado (dominio: architecture)

- Una función espejo que sólo invoca un test no prueba que una doctrina LLM cambie conducta runtime.
- Las preferencias persistidas necesitan una sola semántica de validación/fallback para pantalla y consumidor doctrinal.
- RDD orienta el `strict_tdd` por paquete ya existente; su canal debe probarse sin crear una segunda fuente de verdad.
