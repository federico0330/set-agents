# 049 — Diseño / handoff de arquitectura

- ADR rector: [ADR-0076](../../adr/0076-model-state-evidencia-efimera-y-readback.md).
- Estado de OpenCode 1.18.14: flags CLI verificadas; schema de export raíz/mensaje sigue **UNVERIFIED** y sólo puede habilitar observación tras fixture descartable.
- No se crea módulo: caso de uso en `module.consola`, proyección/readback en `module.generacion-arboles`.

## Supersedes

- `048-consola-para-humanos` · onboarding automático y `first_run` del ingreso al home simple · ADR-0076.
- `048-consola-para-humanos` · medición antes del primer frame · ADR-0076 y ADR-0075 §5.
- `048-consola-para-humanos` · non-goal de contrato de máquina que impida `--model-state` · ADR-0076.

049 mantiene renderer, paleta y jerarquía de 048/ADR-0075, pero reemplaza explícitamente el onboarding/`first_run` automático para ese home. `Modo experto` queda como acción directa, no como consecuencia de onboarding ni submenú obligatorio. ADR-0071 sigue mandando factory/effective.

## Funciones madre y flujo

| Entrada | Función madre leída | Responsabilidad 049 |
|---|---|---|
| Generación | `generate()` — [`ai/scripts/generate.py:495`](../../../ai/scripts/generate.py#L495) | vista efectiva únicamente para install/drift local |
| CLI | `main()` — [`ai/scripts/set_agents_app.py:4514`](../../../ai/scripts/set_agents_app.py#L4514) | API `--model-state` singular, read-only y argv exclusivo |
| Proyecto | `resolve_project_root()` — [`ai/scripts/project_identity.py:41`](../../../ai/scripts/project_identity.py#L41) | ruta canónica exacta |
| Home | `menu()` — [`ai/scripts/set_agents_app.py:4002`](../../../ai/scripts/set_agents_app.py#L4002) | frame cache-only, refresh explícito, experto directo |
| Child TTY | `run_tty()` — [`ai/scripts/set_agents_app.py:3611`](../../../ai/scripts/set_agents_app.py#L3611) | etiqueta/rc reales, sin traceback |
| Preferencia | `_edit_overlay_cell()` — [`ai/scripts/setup_models.py:577`](../../../ai/scripts/setup_models.py#L577) | lock que abarca persistencia, install y readback |
| Integridad | `write_overlay_cell()` — [`ai/scripts/setup_models.py:554`](../../../ai/scripts/setup_models.py#L554) | validar antes de persistir |
| Resolución | `effective_models_config()` + `resolve_role()` — [`ai/scripts/models_config.py:512`](../../../ai/scripts/models_config.py#L512) | desired de runtime primario/orchestrator |

```text
model_state(project):
  scope = (primary_runtime(), "orchestrator")
  observed = unsupported_runtime unless scope.runtime == "opencode"
  observed = observe_roots(project) only for opencode
  return ModelState(observed, desired_effective(scope), read_installed(scope), routing(scope))

apply(change):
  acquire_exclusive_lock_or_fail_without_mutation()
  persist_validated_intent()
  generate_effective_for_exact_target(); install_target(); reread_target()
  release_lock(); return applied_or_pending()
```

Los símbolos nuevos son **UNVERIFIED** hasta ajustarlos al árbol y tests existentes; el flujo, límites y resultados sí son normativos.

## Observación OpenCode, scope y privacidad

1. Resolver proyecto canónico y runtime primario. Runtime no OpenCode produce `unsupported_runtime` sin subprocess. Proyecto irresoluble produce `project_unresolved`.
2. Usar únicamente `opencode session list --format json --pure` y `opencode export --sanitize --pure` en cwd canónico. Nunca SQLite.
3. Del resultado reconocido, admitir exclusivamente sesiones **raíz** con directorio canónico exactamente igual al proyecto. Hijas se descartan sin competir.
4. Ordenar raíces por `updated_at` descendente y `session_id` opaco sólo como desempate interno. Seleccionar una. Dentro de ella elegir el último `user/submitted` válido por `(submitted_at, message_id)` descendente. Sin fallback a otra raíz.
5. El observador entero tiene deadline 5 s, máximo 20 raíces candidatas y 1 MiB de stdout agregado. Superar un límite, schema desconocido o parseo inválido degrada con `ModelStateReason`; no se imprime contenido ni ID.

El child efímero retiene sólo modelo opaco nullable, tiempo, status/source/reason. El export y todos los demás campos se descartan en memoria. No hay cache, temporal, telemetry, stdout/stderr crudo ni sesión-ID en la interfaz.

`ModelStateReason` es el único enum: `not_checked|unsupported_runtime|opencode_absent|project_unresolved|timeout|invalid_json|output_limit|session_limit|no_project_root|no_submitted_message|cache_read_failed|probe_failed|child_failed|not_installed|unavailable`. Cada `checked_at` empieza como `null`; ningún renderer reconstruye el estado.

## Convergencia y restauración

ADR-0071 preserva esta matriz:

| Camino | Vista |
|---|---|
| `build.sh --install` y `check-drift.sh` local | efectiva |
| generación normal, `build.sh --check`, `--diff`, `Global/**` | factory |

El lock exclusivo comienza después de la confirmación y no se libera hasta terminar persistencia, generación, instalación y readback. Un segundo writer retorna reintentable antes de toda mutación. Fallar instalación/readback conserva intención y declara pendiente; retorno de child no basta para éxito.

Router-auto borra sólo `[model_pin]`; restore borra sólo overrides locales. La fixture de restore debe probar byte-identidad de hosts y subscriptions, además de las familias preservadas.

## UX, plugin y gates

El home simple pinta desde cache/ausencia en menos de 300 ms y sin subprocess. `Actualizar estado` mide por fuente, conserva el último valor válido ante error y usa texto reintentable. `Modo experto` es una acción directa. No se ejecuta onboarding automático ni `first_run` en el ingreso 049.

Los plugins son detección read-only: no existe camino de backup, ownership, deshabilitación, edición o borrado dentro de 049, aun si el productor parece identificable.

Gates: fixtures raíz/hija/proyecto/tie/20+1/1MiB/deadline; schema sin `session_id`; lock de dos writers; factory/effective; restore con hosts/subscriptions byte-idénticos; first-frame; ayuda/TTY; tests de consola/modelos, `./build.sh --check`, `./ai/scripts/verify.sh`, `git diff --check` y TTY aislada 1.18.14.
