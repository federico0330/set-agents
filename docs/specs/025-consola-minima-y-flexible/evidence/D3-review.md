# D3-posturas-de-autonomia — review independiente

- Revisor: `package-reviewer` (read-only sobre código/tests; este archivo es la única evidencia escrita).
- Artefacto fijo: `0d20287372a6eacb8ad60875b83b4d0b84b39be4` (`HEAD` al iniciar).
- Integración D3 rastreada a `1da748e992b7be91126f7365abf8295edaf7d089`, incluida en `bec3dcfb2cdd06b98fb4ab82d6490a3858f0a5a9`.
- Alcance: AC-06..AC-08, contexto D3, ADR-0054/ADR-0022, gates previos, `set_agents_app.py`, doctrina del orquestador, artefactos generados y pruebas focales. Sin suite global ni `verify.sh`.
- Skills: `package-review`, `structured-findings`, `test-gap-analysis`. `strict-tdd-verify` no aplica: el paquete declara `strict_tdd: false`.

## Entradas y trazabilidad

| Comando / lectura | Exit | Resultado relevante |
|---|---:|---|
| `git rev-parse HEAD` | 0 | `0d20287372a6eacb8ad60875b83b4d0b84b39be4` |
| `git show -s --format='%H %P %s' 0d202873...` | 0 | SHA fijo presente; padre `d30f94f...`. |
| `git show --stat --oneline 1da748e` | 0 | Cambio D3 identificado en app, doctrina, ADR, artefactos generados y `tests/test_harness.py`. |
| Lectura de `ai/state/features/025-consola-minima-y-flexible.json` con `jq` | 0 | D3 cubre AC-06..08; `strict_tdd: false`; gates previos registrados pass. |
| Lectura de `D3-gates-runtime-qa.md` | 0 | Gate previo declara 8 tests focales y CLI aislado verdes; se revalidará de forma independiente. |

## Checkpoint previo a pruebas

Inspección estática completada:

1. Las claves `postura` y `metodologia_preferida` usan el `config.toml` y el writer preexistentes; defaults de la pantalla: `autonoma` y `off`.
2. Los cuatro artefactos de orquestador generados contienen la sección de ADR-0054.
3. La preferencia RDD orienta el flag por paquete `strict_tdd`; no crea un segundo flag real, coherente con ADR-0022.
4. Riesgo abierto a reproducir: `postura_gate()` declara que no participa en ningún camino CLI/runtime y existe para la mordida; por lo tanto su test podría quedar verde aunque la conducta real del agente no cambie.
5. Riesgo abierto a reproducir: `postura_actual()`/`metodologia_preferida()` normalizan valores desconocidos, pero el orquestador lee el TOML crudo y la doctrina sólo define fallback para clave ausente.
6. Gap candidato: ninguna prueba de metodología exige que `metodologia_preferida`/las reglas SDD-RDD aparezcan en la doctrina que consume el orquestador; la evidencia del implementer afirma que la mordida del canal cubre ambas secciones, pero el test sólo itera `POSTURAS`.

Plan asentado en este checkpoint: tests focales declarados, compatibilidad del store compartido y análisis de referencias para distinguir caminos runtime de helpers de prueba. Las divergencias de canal/fallback quedaron demostradas por control de flujo y se reportan abajo sin ampliar a una suite global.

## Verificación ejecutada

| Comando | Exit | Resultado |
|---|---:|---|
| `python3 -m unittest -v` sobre los 8 tests enumerados por `D3-gates-runtime-qa.md` | 0 | `Ran 8 tests in 5.842s` / `OK`. Confirma pantalla, persistencia y assertions actuales; no resuelve por sí solo la validez de la mordida. |
| `python3 -m unittest -v tests.test_harness.HarnessTests.test_set_agents_status_and_auto_update_config tests.test_harness.HarnessTests.test_app_config_writers_never_clobber_each_other tests.test_harness.HarnessTests.test_vault_init_and_link_persist_the_vault_path_for_fallback_discovery` | 0 | `Ran 3 tests in 6.740s` / `OK`. Compatibilidad focal del store compartido, auto-update y vault preservada. |
| `rg -n "postura_gate" ai/scripts Global tests --glob '*.py' --glob '*.md' --glob '*.toml'` | 0 | Sólo tres apariciones: definición `set_agents_app.py:1135`, docstring y llamada desde `tests/test_harness.py:1067`; cero consumidores de producción. |
| `rg -n "metodologia_preferida|METODOLOGIAS|Receipt Driven|strict_tdd" tests/test_harness.py` | 0 | Las assertions de metodología cubren pantalla/config y skills; ninguna lee la sección `Metodología preferida` del orquestador ni demuestra una decisión SDD/RDD. |

No se corrió suite global, `verify.sh` ni se modificó código/test/state/commit.

## Hallazgos

### D3-F01 — high · testing · AC-06

- **Archivo/línea:** `ai/scripts/set_agents_app.py:1135` (admisión explícita en `:1138-1141`); prueba en `tests/test_harness.py:1058-1071`.
- **Evidencia:** `postura_gate()` declara que no es llamado por ningún camino CLI y que existe para que la mordida pueda afirmar tres resultados. El `rg` ejecutado confirma que el único consumidor es el propio test. Por eso la prueba queda verde aunque el orquestador ignore `postura` y las tres posturas produzcan exactamente la misma conducta real.
- **Reproducción:** reemplazar o eliminar la lectura/aplicación de postura en `Global/_canonical/agents/orchestrator.md` sin tocar el helper; `test_las_tres_posturas...` sigue llamando exclusivamente al helper desconectado y conserva sus tres resultados. Inversamente, romper `postura_gate()` haría fallar el gate sin romper ninguna conducta de producción.
- **Outcome requerido:** la mordida exigida por `spec.md:103-104` debe atravesar un camino que el runtime realmente consume: una decisión hermética del orquestador/spawn o un escenario de agente controlado que cargue `config.toml` y demuestre `actúa` / `propone y espera` / `pregunta antes de delegar`. Eliminar el helper muerto o conectarlo a ese camino real.
- **Scope sugerido:** mecanismo runtime de aplicación de postura + test focal D3; no ampliar a D4/D5.

### D3-F02 — medium · testing · AC-07/AC-08

- **Archivo/línea:** `tests/test_harness.py:1073-1090`, `:1110-1137`; conducta declarada en `Global/_canonical/agents/orchestrator.md:585-604`.
- **Evidencia:** la supuesta mordida común del canal sólo busca el path, ADR y textos de `POSTURAS`. El test RDD sólo mira la explicación de `METODOLOGIAS` en Python y las dos skills. Ninguno exige que el orquestador lea `metodologia_preferida` ni que sus reglas SDD/RDD sigan presentes.
- **Reproducción:** quitar completa la sección `## Metodología preferida (ADR-0054)` de los artefactos de orquestador manteniendo la pantalla Python; las 8 assertions focales inspeccionadas siguen satisfechas, pero `--metodologia sdd|rdd` queda decorativo.
- **Outcome requerido:** agregar una prueba que falle al cortar el canal de metodología y que verifique la regla observable: SDD orienta el triage ambiguo y RDD orienta sólo paquetes nuevos hacia el mismo `strict_tdd: true`, sin sobrescribir un paquete ya declarado.
- **Scope sugerido:** `tests/test_harness.py` y, si la mordida revela que falta un consumidor real, sólo el canal D3 del orquestador.

### D3-F03 — medium · correctness · AC-06/AC-07

- **Archivo/línea:** `ai/scripts/set_agents_app.py:1123-1125`, `:1197-1199`; `Global/_canonical/agents/orchestrator.md:563-590`; edición manual soportada en `docs/adr/0054-posturas-de-autonomia.md:111-115`.
- **Evidencia:** la pantalla normaliza `postura` desconocida a `autonoma` y metodología desconocida a `off`, mientras el consumidor real lee el TOML crudo. La doctrina sólo define fallback para clave ausente; no define qué hacer con valor desconocido, tipo inválido o TOML malformado. Así dos consumidores del mismo archivo pueden decidir estados distintos.
- **Reproducción:** por la vía oficialmente soportada de edición humana, dejar `postura = "omnisciente"` o `metodologia_preferida = "otra"`. `cmd_posturas()`/`cmd_metodologias()` reportan defaults por los normalizadores citados; el orquestador lee los valores literales y no tiene regla aplicable. Un TOML malformado agrava la divergencia: `app_config()` cae a `{}`, mientras la lectura del agente falla.
- **Outcome requerido:** unificar la resolución validada que consumen pantalla y orquestador, o especificar en doctrina un fallback fail-closed idéntico para ausente/desconocido/malformado y cubrirlo con prueba. La pantalla nunca debe afirmar una postura distinta de la que aplicará el agente.
- **Scope sugerido:** lector/canal D3 y pruebas de configuración inválida; preservar `write_app_config` y contratos existentes.

## Reporte

VERDICT repair_required

```json
{
  "package_id": "D3-posturas-de-autonomia",
  "verdict": "repair_required",
  "findings": [
    {
      "id": "D3-F01",
      "severity": "high",
      "category": "testing",
      "acceptance_criterion": "AC-06",
      "file": "ai/scripts/set_agents_app.py",
      "line": 1135,
      "evidence": "postura_gate() está desconectada de todo runtime y sólo la llama el test; su propia docstring lo admite y rg confirma cero consumidores de producción.",
      "reproduction": "Eliminar la aplicación de postura de la doctrina dejando postura_gate intacta conserva el test de tres resultados; romper postura_gate rompe el test sin cambiar producción.",
      "required_outcome": "Probar las tres diferencias a través de un camino runtime realmente consumido y retirar/conectar el helper muerto.",
      "suggested_scope": "Canal runtime D3 y test focal de las tres posturas."
    },
    {
      "id": "D3-F02",
      "severity": "medium",
      "category": "testing",
      "acceptance_criterion": "AC-07/AC-08",
      "file": "tests/test_harness.py",
      "line": 1073,
      "evidence": "Los tests cubren pantalla/config/skills pero no la sección Metodología preferida ni una decisión SDD/RDD del orquestador.",
      "reproduction": "Quitar la sección de metodología del orquestador deja satisfechas las assertions D3 actuales y vuelve decorativo el toggle.",
      "required_outcome": "Una prueba debe romperse al cortar el canal y fijar SDD ambiguo/RDD strict_tdd sólo para paquete nuevo.",
      "suggested_scope": "tests/test_harness.py y el canal D3 si la mordida descubre ausencia de consumidor."
    },
    {
      "id": "D3-F03",
      "severity": "medium",
      "category": "correctness",
      "acceptance_criterion": "AC-06/AC-07",
      "file": "Global/_canonical/agents/orchestrator.md",
      "line": 566,
      "evidence": "La pantalla normaliza valores inválidos pero el agente lee TOML crudo; sólo existe fallback doctrinal para clave ausente.",
      "reproduction": "Editar config.toml con postura/metodología desconocida hace que la pantalla muestre default mientras el orquestador recibe un valor sin semántica.",
      "required_outcome": "Pantalla y agente deben usar la misma resolución validada o el mismo fallback explícito para ausente/desconocido/malformado.",
      "suggested_scope": "Lector/canal D3 y pruebas de configuración inválida."
    }
  ]
}
```

## Destilado (dominio: data / algorithms)

- Un toggle de configuración no está verificado si la prueba ejercita una función espejo desconectada del consumidor runtime.
- Todo consumidor de una preferencia persistida debe compartir validación y fallback; mostrar un default mientras otro consumidor lee el valor crudo crea dos estados efectivos.
- RDD reutiliza el único flag por paquete `strict_tdd`; una preferencia global sólo puede orientar paquetes nuevos, nunca duplicar ni sobrescribir esa fuente de verdad.
