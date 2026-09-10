# PKG-D — Integración, ayuda y TTY aislada

## Objetivo

Cerrar A–C con regresiones integradas, ayuda humana/avanzada y prueba TTY aislada con
OpenCode 1.18.14. No corrige funcionalidad ajena: los hallazgos vuelven a su paquete dueño.

## Baseline y límites de propiedad

- Baseline `dad5987722d9254b7ebb8c6dc9bdd49a678be357`, árbol 045–048 ya sucio. Sólo pruebas y
  evidencia sanitizada; no atribuir/limpiar cambios preexistentes.
- Depende de PKG-A/B/C aceptados. Si falla propiedad ajena, registrar evidencia y volver al dueño.
- No editar `Global/**`, `models.toml`, entry points de producción ni contratos aprobados.

## Archivos y puntos de entrada

| Path | Por qué |
| --- | --- |
| `tests/test_model_identity_integration_049.py` | CLI/help, convergencia y no-regresiones interpaquete. |
| `tests/test_model_identity_tty_049.py` | TTY: observación allow-listed o degradación segura. |
| `docs/specs/049-identidad-honesta-modelos/evidence/` | Logs/resúmenes sanitizados; jamás export, ID, prompt o respuesta. |

## Trabajo

1. Probar sesión Astra→Luna como último envío y default Terra neutral; `/model` no muta SET/install.
2. Probar help normal humano, `--help --avanzado` ingenieril y argv inválido sin JSON parcial.
3. Correr TTY aislada con fixture descartable: sólo observación allow-listed o reason de degradación.
4. Ejecutar gates globales y huella contractual; guardar evidencia sanitizada y reportar drift previo.

## Contratos e invariantes

- AC-09 integra; AC-01..AC-08 continúan siendo A–C.
- ADR-0076: nunca persistir stdout raw, export, IDs ni transcript como evidencia.
- Verificar, no editar, huella reproducible de los cuatro documentos contractuales.

## Riesgo, revisión y validación

Complejidad media: integración multi-paquete y TTY sin nueva mutación de producto.
`required_reviewers`: `package-reviewer`, `security-auditor`; test owner `test-writer`; strict TDD off.

```bash
python3 -m unittest -v tests.test_model_identity_integration_049 tests.test_model_identity_tty_049
./build.sh --check
./ai/scripts/verify.sh
git diff --check
```

TTY usa HOME/STATE temporales. Si falta OpenCode, registrar razón permitida y degradación,
sin instalar ni autenticar.

## Hecho cuando

Gates verdes, TTY aislada sin fuga de datos y evidencia de convergencia sin adjudicar trabajo
preexistente.
