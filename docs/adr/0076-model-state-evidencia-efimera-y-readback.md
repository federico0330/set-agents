# ADR-0076 — `ModelState`: evidencia efímera y convergencia por readback

- Estado: **Accepted** (2026-09-09), enmendado por contrato 049 v0.3.0 aprobado.
- Feature: `049-identidad-honesta-modelos`.
- Supersede ADR-0075 §5 sólo para medición previa al primer frame; extiende ADR-0071 para instalación/drift efectivos.
- Supersede de 048 el onboarding automático y `first_run` en el ingreso al home simple de 049.

## Contexto

Último envío observado, default SET, artefacto instalado y routing son evidencias independientes. `/model` manda en la sesión abierta y no cambia SET. El footer es evidencia de una respuesta ya generada, mientras un selector prepara el próximo envío. Ningún rótulo de plugin no rastreado prueba ejecución.

La función madre de CLI es `main()` (`ai/scripts/set_agents_app.py:4514`); el home es `menu()` (`:4002`), el apply parte de `_edit_overlay_cell()` (`ai/scripts/setup_models.py:577`) y la proyección parte de `generate()` (`ai/scripts/generate.py:495`). OpenCode 1.18.14 confirma las flags oficiales, pero los campos de export raíz/mensaje permanecen **UNVERIFIED** hasta fixture descartable.

## Decisión

### Estado singular y público

`set-agents --model-state [--project DIR] [--json]` construye un único `ModelState` para `(runtime_primario_resuelto, orchestrator)`. No agrega selector de runtime/rol. Si no existe runtime, el scope es `unavailable`. Sólo si el runtime es `opencode` se intenta observación; otro runtime retorna `observed=unobserved` con `unsupported_runtime` y no ejecuta OpenCode.

Los modelos son strings opacas nullable. La salida no muestra `session_id` ni ningún transcript. La CLI humana y JSON reciben el mismo valor; los renderers no recalculan precedencias. `checked_at` es `null` hasta la primera medición.

Hay un solo enum compartido: `not_checked|unsupported_runtime|opencode_absent|project_unresolved|timeout|invalid_json|output_limit|session_limit|no_project_root|no_submitted_message|cache_read_failed|probe_failed|child_failed|not_installed|unavailable`.

### Selección de OpenCode y frontera privada

Sólo se invocan `opencode session list --format json --pure` y `opencode export --sanitize --pure`; nunca SQLite. El proyecto se canoniza primero. El universo contiene únicamente sesiones **raíz** con directorio canónico exactamente igual al proyecto; todas las hijas se excluyen.

Se elige la raíz por `updated_at` descendente y `session_id` opaco sólo como desempate interno. De esa raíz, y de ninguna otra, se elige su último mensaje válido `user/submitted`, con `(submitted_at, message_id)` como desempate interno. Si la raíz o el mensaje no pueden probarse, se degrada; no hay heurística ni fallback.

El observador completo está limitado a **5 s**, **20 sesiones raíz candidatas** y **1 MiB total de stdout** sumado entre los children. El export se allow-listea en un child efímero y se descarta en memoria; SET no persiste, cachea, telemetra, registra ni reemite contenido crudo o IDs. Límite, timeout o parseo fallido se vuelven reason cerrado.

### Convergencia, lock y restauración

La preferencia se valida antes de persistir. Tras confirmar, un lock exclusivo cubre de punta a punta `persistir → generar efectiva → instalar target → releer`. Un segundo writer falla reintentable antes de cualquier mutación. Sólo readback exacto produce `applied`; error de install/readback conserva intención y resulta `pending_apply`.

ADR-0071 mantiene factory para `Global/**`, `build --check` y `build --diff`; instalación y drift local usan efectiva. Router-auto borra sólo `[model_pin]`; restore borra sólo overrides locales de modelos. Toda fixture de restore debe dejar hosts y subscriptions byte-idénticos.

### UX y plugins

El primer frame es cache/ausencia sin subprocesses. `Actualizar estado` es el único camino de medición y conserva evidencia válida ante error. `Modo experto` es acción directa del home simple; no se ejecuta onboarding automático ni `first_run` de 048 en ese ingreso. ADR-0075 conserva paleta, ancho, renderer y jerarquía.

Plugins/rótulos de 049 son estrictamente read-only. No se ofrece ni realiza backup, ownership gate, deshabilitación, edición, borrado ni modificación de configuración.

## Consecuencias y gates

- El desacuerdo sesión/default es neutral; desired/installed distinto es pendiente de aplicar.
- La privacidad privilegia degradación segura ante schema no probado.
- Fixtures obligatorios: raíz/hija/proyecto/ties, 20+1, 1MiB total, timeout, sin IDs, runtime no OpenCode, lock de dos writers, restore hosts/subscriptions byte-idénticos y home sin subprocess/first_run.
- Gates finales: tests consola/modelos, `./build.sh --check`, `./ai/scripts/verify.sh`, `git diff --check` y TTY aislada OpenCode 1.18.14.
