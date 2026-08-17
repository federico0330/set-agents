# D1 verification — finding-verifier

Checkpoint inicial: evidencia creada antes de verificar findings.

## Verificación final

| Finding | Veredicto | Razón | Evidencia |
|---|---|---|---|
| D1-F01 | upheld | El finding describía un defecto real: el repair documenta que los prompts/harnesses tuvieron que corregirse para añadir --json a los consumidores máquina de routing. | `docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:21-26` |
| D1-F02 | upheld | El finding describía un defecto real: la rama humana necesitó un renderer nuevo porque antes imprimía repr() de dicts/tuplas y una línea de 5763 caracteres. | `ai/scripts/set_agents_app.py:498-505` |
| D1-F03 | upheld | El finding describía un defecto real: el corte original de 9 flags fue insuficiente; el repair terminó con 28 flags internas ocultas y desglose explícito. | `docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:95-113` |
| D1-F04 | refuted | La jerarquía por espaciado y peso ya estaba en el renderer del picker: cada fila recibe marcador/espacio y la fila activa usa bold(); el finding confundió ausencia de emoji con ausencia de jerarquía. | `ai/scripts/tui.py:720-734` |
| D1-F05 | upheld | El finding describía un defecto real: el repair tuvo que remover el emoji del texto de primer arranque; HEAD muestra la línea ya sin emoji. | `docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:46-49; ai/scripts/set_agents_app.py:3738-3741` |
| D1-F06 | upheld | El finding describía un defecto real: el test antiemoji tuvo que pasar de blacklist incompleta a regla positiva ASCII para cubrir U+23FB y otros no-ASCII. | `tests/test_harness.py:2679-2685` |
| D1-F07 | upheld | El finding describía un defecto real: el guard de borrado se cambió a lista congelada literal y verificación separada contra app._INTERNAL_FLAGS. | `tests/test_harness.py:5539-5548` |
| D1-F09 | upheld | El finding describía un defecto real: el repair actualizó la docstring que seguía citando la etiqueta con emoji eliminada. | `docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:63-66; ai/scripts/set_agents_app.py:3653-3655` |

## JSON final

```json
{
  "actor": "finding-verifier",
  "package_id": "D1-superficie-humana",
  "verdicts": [
    {
      "id": "D1-F01",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el repair documenta que los prompts/harnesses tuvieron que corregirse para añadir --json a los consumidores máquina de routing.",
      "evidence": "docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:21-26"
    },
    {
      "id": "D1-F02",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: la rama humana necesitó un renderer nuevo porque antes imprimía repr() de dicts/tuplas y una línea de 5763 caracteres.",
      "evidence": "ai/scripts/set_agents_app.py:498-505"
    },
    {
      "id": "D1-F03",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el corte original de 9 flags fue insuficiente; el repair terminó con 28 flags internas ocultas y desglose explícito.",
      "evidence": "docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:95-113"
    },
    {
      "id": "D1-F04",
      "verdict": "refuted",
      "reason": "La jerarquía por espaciado y peso ya estaba en el renderer del picker: cada fila recibe marcador/espacio y la fila activa usa bold(); el finding confundió ausencia de emoji con ausencia de jerarquía.",
      "evidence": "ai/scripts/tui.py:720-734"
    },
    {
      "id": "D1-F05",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el repair tuvo que remover el emoji del texto de primer arranque; HEAD muestra la línea ya sin emoji.",
      "evidence": "docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:46-49; ai/scripts/set_agents_app.py:3738-3741"
    },
    {
      "id": "D1-F06",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el test antiemoji tuvo que pasar de blacklist incompleta a regla positiva ASCII para cubrir U+23FB y otros no-ASCII.",
      "evidence": "tests/test_harness.py:2679-2685"
    },
    {
      "id": "D1-F07",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el guard de borrado se cambió a lista congelada literal y verificación separada contra app._INTERNAL_FLAGS.",
      "evidence": "tests/test_harness.py:5539-5548"
    },
    {
      "id": "D1-F09",
      "verdict": "upheld",
      "reason": "El finding describía un defecto real: el repair actualizó la docstring que seguía citando la etiqueta con emoji eliminada.",
      "evidence": "docs/specs/025-consola-minima-y-flexible/evidence/D1-repair.md:63-66; ai/scripts/set_agents_app.py:3653-3655"
    }
  ],
  "summary": "7 upheld, 1 refuted",
  "evidence_path": "docs/specs/025-consola-minima-y-flexible/evidence/D1-verification.md"
}
```

## Destilado (dominio: architecture)
- En D1, las salidas routing human-readable por default convierten todo prompt/harness que parsea routing en consumidor máquina explícito: debe llevar `--json`.
- La jerarquía del picker vive en `tui._render_items` mediante marcador/espacio y `bold()` de la fila activa; los labels del menú sólo deben aportar contenido ASCII sin iconos estructurales.
- Para flags ocultas, el test durable debe congelar la lista esperada y evitar substring-oracles contra el mismo set del código.
