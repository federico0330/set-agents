# PKG-B — ModelState y CLI de sólo lectura

## Objetivo

Publicar `ModelState` para `(runtime primario, orchestrator)` y
`set-agents --model-state [--project DIR] [--json]`. La observación OpenCode es efímera,
acotada y privada; desired, installed y routing preservan sus fuentes.

## Baseline y coordinación

- Baseline `dad5987722d9254b7ebb8c6dc9bdd49a678be357`: 045–048 ya ensuciaron el árbol.
  Capturar status antes/después, sin reverts, limpieza ni atribución retroactiva.
- `ai/scripts/set_agents_app.py` es owned aquí para adaptador CLI y shared con PKG-C. Éste
  depende de PKG-B: preservar su integración al editar el menú después.
- No modificar `Global/**`, `models.toml`, `build.sh`, `setup_models.py` ni SQLite.

## Checkpoint vigente

- PKG-A está **accepted**. El hallazgo `PKG-A-F01` de alcance de drift para Cursor fue
  reparado, probado y cerrado; no reabrir ni reatribuir esa corrección desde PKG-B.
- PKG-B es el paquete actual en `PACKAGE_REPAIR`, segundo y último repair. El primer delta
  cerró `F01`, `F02`, `F04`, `F05`, `SEC-001` y `SEC-003`; no reabrir ni reatribuir esos seis.
  `finding-verifier` sostuvo los cuatro findings restantes. Conserva `strict_tdd=true`: cada
  reparación parte de prueba roja focal, no se debilitan regresiones y se preserva el baseline
  sucio de 045–048.
- `PKG-B-F03`: Cursor sí está soportado e instala `~/.cursor/agents/orchestrator.md`; releer
  ese artefacto y cubrir fixture, sin degradarlo a `unsupported_runtime`.
- `PKG-B-SEC-002`: escapar C0, DEL y todo C1 (`U+0080..U+009F`) en renderer humano; JSON
  conserva strings opacas sin sanitización semántica.
- `PKG-B-DELTA-F01`: el child real bounded con `returncode != 0` debe mapear a fallo/razón
  cerrada y tener prueba de proceso real, no sólo double inyectado.
- `PKG-B-DELTA-F02`: para timestamps iguales, usar únicamente `message_id` validado como
  desempate interno descendente; nunca publicarlo ni cambiar el contrato JSON.

## Archivos y puntos de entrada

| Path | Por qué |
| --- | --- |
| `ai/scripts/model_state.py` | Nuevo módulo inyectable: schema v1, enum, observador y render humano. |
| `ai/scripts/set_agents_app.py` | Función madre `main()` (4514): argv exclusivo, rc y despacho read-only. |
| `ai/scripts/project_identity.py` | Sólo lectura: `resolve_project_root()` (55), ruta canónica exacta. |
| `ai/scripts/models_config.py` | Sólo lectura: `effective_models_config()` (512) y `resolve_role()` (743), desired. |
| `tests/test_model_state_049.py` | Pruebas herméticas de contrato, límites, privacidad y argv. |

## Trabajo

1. Modelar schema v1, único `ModelStateReason`, timestamps/refresh iniciales y render humano
   sin catalogar modelos.
2. Resolver scope singular desde `[runtime].primary`; derivar desired efectivo, installed por
   readback y routing sin mutar.
3. Observar OpenCode sólo con `session list --format json --pure` y `export --sanitize --pure`:
   raíces canónicas exactas, allow-list y descarte inmediato de todo salvo modelo/timestamp.
4. Cumplir deadline total 5 s, máximo 20 raíces y stdout agregado 1 MiB; degradar rc 0 con
   razón cerrada, sin IDs ni transcript.
5. Hacer `--model-state` exclusivo: argv/proyecto inválido retorna rc 2, stderr humano,
   cero JSON parcial y cero mutaciones.

## Contratos e invariantes

- AC-01..AC-04 son el contrato público completo: no claves/enums nuevos ni selector de scope.
- ADR-0076: nunca SQLite, temporales o cache de export; hija no compite; sin fallback de raíz.
- Campos de export OpenCode 1.18.14 siguen UNVERIFIED: shape no probado → `invalid_json`,
  nunca heurística.
- Modelos son strings opacas/null; no hardcodear Astra/Terra/Luna.

## Riesgo, revisión y validación

Complejidad alta: API CLI pública y frontera de datos sensibles. `required_reviewers`:
`package-reviewer`, `security-auditor`. Test owner implementer; `strict_tdd=true`.

```bash
python3 -m unittest -v tests.test_model_state_049
python3 ai/scripts/set_agents_app.py --model-state --json
git diff --check
```

La prueba argv inválida usa fixture/entorno temporal y debe probar stdout vacío con rc 2;
nunca ejecutar instalación.

## Hecho cuando

JSON v1 se emite una vez para el único scope; fixtures de raíces/hijas/límites/timeout/schema
degradan sin filtrar IDs ni contenido.
