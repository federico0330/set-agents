# PKG-A — Proyección efectiva local

## Objetivo

Hacer que la instalación local y su drift se generen desde la configuración efectiva
(`factory ∪ models.local.toml`) sin cambiar la proyección de fábrica. Cubre la parte
de proyección de AC-05 y aporta la base para AC-06.

## Baseline y límites de propiedad

- Baseline: `dad5987722d9254b7ebb8c6dc9bdd49a678be357`, con árbol ya sucio por 045–048.
  Registrá `git status --porcelain=v1`; no atribuyas, borres ni reformatees esos cambios.
- No modificar `Global/**`: los artefactos globales y `build --check/--diff` permanecen
  factory-only.
- No tocar `models.toml`, `ai/scripts/set_agents_app.py`, `ai/scripts/setup_models.py`
  ni tests existentes sin enmienda de ownership; crear pruebas propias.

## Archivos y puntos de entrada

| Path | Por qué |
| --- | --- |
| `ai/scripts/generate.py` | Función madre `generate()` (495); vista efectiva sólo cuando un consumidor local la pide. |
| `build.sh` | Despacha `--install`, `--check` y `--diff`; separa factory/local. |
| `ai/scripts/check-drift.sh` | Genera staging para comparar instalación local. |
| `ai/scripts/install.py` | Sólo si hace falta pasar el destino/vista exacto sin ampliar el merge gestionado. |
| `tests/test_effective_projection_049.py` | Pruebas nuevas; no convertir 045–048 en evidencia propia. |

## Trabajo

1. Definir una entrada explícita a `generate()` para la vista efectiva; default y emisión
   de fábrica quedan byte-equivalentes.
2. Encaminar sólo `build.sh --install` y staging de drift local por esa entrada, incluso
   con `--target`.
3. Mantener `build.sh --check`, `build.sh --diff` y `Global/**` factory-only.
4. Cubrir overlay legal/ausente y modelos opacos; demostrar que fábrica/Global no cambian
   y drift compara el valor efectivo instalado.

## Contratos e invariantes

- `spec.md` AC-05: `/model` no toca SET ni artefactos; instalación local usa vista efectiva.
- ADR-0071: factory para `Global/**`, `--check`, `--diff`; efectiva para instalar/drift local.
- ADR-0076: readback, no rc de child, determina aplicado; lock y UI son de PKG-C.
- `ai/scripts/models_config.py:512`: `effective_models_config()` no muta fábrica.

## Riesgo, revisión y validación

Complejidad media: proyección que llega a configuración local. `required_reviewers`:
`package-reviewer`, `security-auditor`; checkpoint temprano: preview/target acotado antes de
instalar. Test owner implementer; `strict_tdd=false`.

```bash
python3 -m unittest -v tests.test_effective_projection_049
./build.sh --check
git diff --check
```

Usar HOME/STATE temporales y `install.py --preview`, nunca instalación global.

## Hecho cuando

El overlay cambia sólo staging local de instalación/drift; `Global/**` y caminos factory no
varían, sin tocar sesión abierta.
