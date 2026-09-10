# PKG-C2 — Convergencia de consola: verificación y reparación consolidada

## Estado, objetivo y candidato

Estado vigente: feature `049-identidad-honesta-modelos`, revision **242**,
`PACKAGE_REPAIR`; `RP-01` terminó `repair_required`. La fuente es el contrato aprobado
`docs/specs/049-identidad-honesta-modelos/spec.md` (`049-model-identity/v0.3.0`, hash
`0ed880d4…`). El finding-verifier ya reprodujo independientemente los **23** hallazgos:
`upheld=23`, `refuted=[]`. Los solapamientos se agruparon, pero los 23 IDs continúan
individualmente upheld y la reparación debe conservar esa trazabilidad. No volver a
verificar findings. `repair_batches=0`; la reparación funcional todavía no comenzó.

El candidato original permanece congelado: `FOUNDATION_REF=168cd65996f5e5e96c5c1f8131b1090a92879ef5`
(tree `744a7ae8c4163ad616476a65cfa04eded60f05a6`) a
`C2_REF=5ab059e2dd863384178205a57324ec6fe7b47074` (tree
`76876df1ea59fac9f8c608a88a7d4574949e9858`), con siete paths y digest
`sha256:2be57212d43707ab6c0f94da0426d7689d132c988c41e7b26920c3fd3eda5543`.

**`NEW_FOUNDATION_REF` ya existe** (no crear de nuevo):
`3878fb0dcf41a475ad8dcd4bb691ddd5c5ad018b` (tree
`ad4fab90e00e71179a0bb35818c742c484eb61c0`). Agrega únicamente
`ai/scripts/routing_core/service.py` y `ai/scripts/provider_registry.py`, rotulados
**preexistentes sin receipt** — no delta atribuible a 049 ni al transport de C2.
El worktree `/tmp/set-agents-049-c2.YfrczU` está detached limpio en ese ref.

**Handoff incompleto (SPAWN-016):** el primer `repair-agent` sólo extendió la fundación
y devolvió un handoff incompleto; no hay `REPAIRED_C2_REF` ni reparación transportada al
root. Queda **un único reintento** focal de reparación. Si falla: `BLOCKED` /
`HUMAN_DECISION_REQUIRED` — no abrir otro ciclo de implementación.

## Propiedad, límites y funciones madre

Owned actual: `ai/scripts/setup_models.py`, `ai/scripts/onboarding.py`,
`tests/test_console_model_state_049.py`, `tests/test_model_apply_049.py`,
`tests/test_models_wizard_ui.py`, `tests/test_menu_ui.py`. Shared:
`ai/scripts/set_agents_app.py` (conservar adaptador `--model-state` de PKG-B). Sólo lectura:
`ai/scripts/model_state.py`, `ai/scripts/generate.py`, `ai/scripts/models_config.py`,
ADR-0075/0076, state y specs. Las dos dependencias de fundación **no** entran al delta C2.

**Hard constraint:** no tocar ni generar `Global/**`, `models.toml`, state, specs, A/B, ni
sesiones `/model`; nunca reset/checkout/stash del root. El repair trabaja en worktree
detached desde `NEW_FOUNDATION_REF` y sólo puede transportar paths owned/shared tras gates.

Madres: `menu()` `set_agents_app.py:4012`, `run_tty()` `:3612`,
`write_overlay_cell()` `setup_models.py:557`, `router_choose_automatically()` `:794`,
`_edit_overlay_cell()` `:824`, `RoutingService.route()`
`routing_core/service.py:115,265`, `HOSTS`/`resolve_host_state()`/`list_host_rows()`
`provider_registry.py:101,123,138`, `effective_models_config()` `models_config.py:512` y
`generate()` `generate.py:496`. Re-leer líneas en el worktree; pueden haber corrido.

Los siete paths del rango C2 original son: `A ai/scripts/onboarding.py`,
`M ai/scripts/set_agents_app.py`, `M ai/scripts/setup_models.py`,
`A tests/test_console_model_state_049.py`, `M tests/test_menu_ui.py`,
`A tests/test_model_apply_049.py`, `M tests/test_models_wizard_ui.py`.

## Hallazgos abiertos (23, ya verificados upheld)

### Fundación e integración (2)

- `PKG-C2-F01` (`set_agents_app.py:746`): `effort_request` es incompatible con el
  `RoutingService.route` congelado; reproducir decisión válida → `ROUTING_UNAVAILABLE`
  (`ModelRequestCliTests` 3/5 falla). Reparación esperada: usar la API compatible ya
  versionada en `NEW_FOUNDATION_REF` o quitar el keyword no soportado.
- `PKG-C2-F02` (`set_agents_app.py:3982`): APIs de `provider_registry` no estaban en la
  fundación vieja; `NEW_FOUNDATION_REF` ya las aporta. Resultado: invocar las APIs de
  fundación sin transportar esos files como delta C2.

Decisión durable **“Extender fundación C2 a dependencias integradas”**: cumplida en
`NEW_FOUNDATION_REF`. No se atribuyen a 049 ni se transportan como delta C2.

### Transacción, readback, lock y caché (8)

- `PKG-C2-F03` (`setup_models.py:625`): editar área no primaria → `applied` por readback
  de orchestrator sin cambio; exigir readback exacto runtime/scope/field o `pending`.
- `PKG-C2-F04` (`set_agents_app.py:4252`): intercalar writer de host/pin pierde update;
  todo writer de preferencias debe usar el lock compartido.
- `PKG-C2-F05` (`setup_models.py:641`): apply exitoso deja reload de disco `None` y RAM
  sentinela; persistir `ModelState` válido y reemplazar caché RAM.
- `PKG-C2-F06` (`setup_models.py:1081`): Restore persiste y anuncia éxito sin
  install/readback; usar coordinador transaccional y resultado pending.
- `PKG-C2-F11` (`setup_models.py:626`): hijo instalador colgado bloquea cambios futuros;
  timeout, terminate/reap, liberar lock y registrar pending.
- `PKG-C2-SEC-002` (`setup_models.py:794`): con apply lock real, writer público de pin aún
  muta; unificar lock de todos los entry points read-modify-write.
- `PKG-C2-SEC-003` (`setup_models.py:619`): edición audit/area dice aplicada con readback
  ajeno; leer target exacto o pending.
- `C2-UX-F01` (`setup_models.py:707`): disco queda pending pero UI muestra applied viejo;
  sincronizar caché, convergencia visible y retry apply.

### Frescura, refresh y cobertura de regresión (8)

- `PKG-C2-F07` (`setup_models.py:734`): timeout observado borra modelo/timestamp bueno;
  merge por fuente preservando evidencia stale.
- `PKG-C2-F08` (`setup_models.py:664`): pending/mixed no muestra pending, stale ni fresh,
  ni retry; renderizar convergencia/frescura y acción retry.
- `PKG-C2-F09` (`setup_models.py:1102`): timeout de catálogo escapa y fallo host detiene
  drift; aislar fuentes y mapear fallos acotados a error humano.
- `PKG-C2-F10` (`set_agents_app.py:3978`): fresh process con host-counts válidos en disco
  muestra unreviewed; sembrar primer frame sólo desde caché validada, sin probe.
- `PKG-C2-F12` (`tests/test_model_apply_049.py:35`): 55 tests pasan sin scope/cache/
  restore/refresh/contention/routing; añadir regresiones conductuales por resultado reparado.
- `C2-UX-F02` (`setup_models.py:734`): timeout borra observado mientras otra fuente es
  fresh; stale merge por fuente con timestamp visible.
- `C2-UX-F03` (`setup_models.py:1102`): `OSError` de catálogo sale del wizard; aislarlo y
  renderizar error humano reintentable.
- `C2-UX-F04` (`set_agents_app.py:3974`): host disk cache válido no aparece en frame uno;
  seed cache-only previo a pintar.

### Seguridad TTY, backups y subprocesses (5)

- `PKG-C2-SEC-001` (`setup_models.py:803`): `.bak` predecible symlink hace que `copy2`
  sobreescriba víctima; backup exclusivo seguro contra symlink y rechazar estado inseguro.
- `PKG-C2-SEC-004` (`setup_models.py:342`): ID OSC llega a picker/cache; allowlist ASCII,
  límite de largo y sanitización TTY.
- `PKG-C2-SEC-005` (`setup_models.py:342`): ID >1MiB y timeout de hijo no están acotados;
  limitar captura/tiempo, kill/reap y mapear a stale/pending.
- `C2-UX-F05` (`setup_models.py:652`): U+202E sobrevive sanitizer; rechazar categorías
  Unicode control/format.
- `C2-UX-F06` (`setup_models.py:656`): siete `ModelStateReason` quedan en mensaje genérico;
  mapping humano exhaustivo.

## Grupos y reparación aislada (único reintento)

Los grupos para una reparación consolidada son: readback exacto
`PKG-C2-F03` + `PKG-C2-SEC-003`; lock compartido `PKG-C2-F04` +
`PKG-C2-SEC-002`; caché/convergencia `PKG-C2-F05` + `PKG-C2-F08` + `C2-UX-F01`;
stale refresh `PKG-C2-F07` + `C2-UX-F02`; fallos aislados `PKG-C2-F09` + `C2-UX-F03`;
primer frame `PKG-C2-F10` + `C2-UX-F04`; sanitización `PKG-C2-SEC-004` + `C2-UX-F05`;
y límites de hijos `PKG-C2-F11` + `PKG-C2-SEC-005`. Permanecen individualmente: F01,
F02, F06, F12, SEC-001 y UX-F06. Agrupar no fusiona, descarta ni cierra IDs.

La reparación ocurre **sólo** en `/tmp/set-agents-049-c2.YfrczU`, partiendo de
`NEW_FOUNDATION_REF` (HEAD actual). Aplicar el repair C2 y capturar `REPAIRED_C2_REF`.
Medir el repair real contra la fundación nueva, no imputar la extensión:

```bash
WT=/tmp/set-agents-049-c2.YfrczU
NEW_FOUNDATION_REF=3878fb0dcf41a475ad8dcd4bb691ddd5c5ad018b
C2_REF=5ab059e2dd863384178205a57324ec6fe7b47074
# inmediatamente después del commit de reparación C2
REPAIRED_C2_REF=$(git -C "$WT" rev-parse HEAD)
git -C "$WT" diff --check "$NEW_FOUNDATION_REF..$REPAIRED_C2_REF"
git -C "$WT" diff --name-status "$NEW_FOUNDATION_REF..$REPAIRED_C2_REF"
git -C "$WT" diff --numstat "$C2_REF..$REPAIRED_C2_REF"
git -C "$WT" diff --name-only "$NEW_FOUNDATION_REF..$REPAIRED_C2_REF"
```

Ejecutar tests focales (`unittest`, no pytest) y `py_compile` desde `$WT`. Luego
recapturar tree/path digest y repetir `candidate-no-global`, ownership, focused tests y
`diff --check`. **No `Global/**`** en repair ni transporte. Techo ADR-0023: al primer
`record-repair`, `budget_lines=min(100, ceil(2703/2))=100`; medir contra
`3878fb0d…`. FAIL → `HUMAN_DECISION_REQUIRED`. No almacenar prompts, respuestas, IDs o
export OpenCode; `strict_tdd=false` permanece sin debilitar tests.
