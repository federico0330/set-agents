# C2-modelstoml-neutro — evidencia del implementer

Estado: COMPLETO

Iniciado: 2026-08-14T03:25:59-03:00

## Tabla AC → cambio → prueba

| AC | Veredicto | Cambio (`archivo:línea`) | Prueba |
|---|---|---|---|
| AC-03 (`[subscriptions]` ausente = auto) | CUMPLE | `models.toml:6-14` — sección vacía (sin declaraciones), comentario explicando el contrato + el overlay. `ai/scripts/models_config.py:146-153` — `load_config` deja de exigir `[subscriptions]` no vacío (sólo exige que exista como tabla); las demás secciones (`catalog`/`session`/`areas`) siguen exigiendo no-vacío. | `python3 -c "... models_config.load_config()['subscriptions'] == {}"` → `{}` (ver bloque abajo). `tests/test_probe_subscriptions.py::SubscriptionTriStateTests` (11 tests, reescritos para no depender de una línea `openai = true` que ya no existe en el tracked file — ahora usan `load_config()+mutate+emit()`, mismo idioma que `test_harness.py::_repo_models_variant`). |
| AC-04 (small model sin Zen en la lane renombrada; rename) | CUMPLE | `ai/scripts/models_config.py:31` `LANES = ("go-zen", "zen", "openai-only")`; `:411` `auto_profile()` devuelve `"openai-only"`. `models.toml` — 35 sitios `"local" = ` → `"openai-only" = ` (todas las tablas `opencode = {...}` de `[areas.*]`/`[roles.*]` + `[session].opencode_small_model`); `models.toml:54` el small model de la lane `openai-only` pasa de `opencode/north-mini-code-free` (namespace zen) a `openai/gpt-5.4-mini` (mismo modelo barato ya curado en cada otra celda `openai-only`). `tests/fixtures/models.toml`, `tests/test_harness.py`, `tests/test_auto_profile.py` — mismo rename. | `grep -c '"local" = ' models.toml` → `0`. `grep -c '"openai-only" = ' models.toml` → `35`. `models_config.load_roles(lane)` para las 3 lanes → OK (ver bloque abajo). `tests.test_auto_profile.AutoProfileTests.test_no_opencode_pair_is_openai_only` — OK. `tests.test_harness.HarnessTests.test_openai_only_profile_generates_and_validates` — OK (`generate.py --profile openai-only`). |
| AC-05 (overlay en `STATE_DIR`, wizard no ensucia el árbol) | CUMPLE | `ai/scripts/models_config.py:280-372` — `subscriptions_overlay_path()` (import diferido de `set_agents_app.STATE_DIR`, nunca un segundo literal — ver "Trampa ADR-0043" abajo), `load_subscriptions_overlay()`, `write_subscription_overlay()` (atómico, mismo patrón que `emit_atomic`), `effective_subscriptions()`. `ai/scripts/setup_models.py:397-432` (wizard, opción "Suscripciones", escribe el overlay de inmediato, nunca `config["subscriptions"]`), `:611-628` (`--add`/`--drop` ídem, inmediato, ya no acumulan en el pipeline `mutated→emit_atomic`), `:146-157` (`_subscription_candidates`, universo auditado en vez de `sorted(config["subscriptions"])`, vacío en un tracked file neutro). | Ver "Wizard ya no ensucia el árbol" abajo: `--add anthropic` contra el `models.toml` REAL → `git diff --stat -- models.toml` idéntico antes/después, overlay real actualizado. `tests.test_harness.HarnessTests.test_setup_models_drop_subscription_writes_the_overlay_not_the_tracked_file` — OK (`models.toml` byte-idéntico tras un `--drop` exitoso). `tests.test_models_wizard_ui.WizardBehaviorTests.test_subscription_auto_writes_the_overlay_never_the_tracked_config` — OK (mock de `write_subscription_overlay`, `config["subscriptions"]` sin tocar). |

## Efecto colateral encontrado y cerrado (no pedido por el AC, necesario para que AC-03 no rompa el build)

`load_role_tiers` (`ai/scripts/models_config.py:521-590`, las seis tablas
`[roles.<role>.tiers.*]`) nunca tuvo la tolerancia tri-estado que `load_roles` ya tenía desde
ADR-0029 — invisible mientras `[subscriptions]` siempre declaraba `true`. Con AC-03 (tracked file
neutro), moría incondicionalmente en las seis lanes tiered, en cualquier máquina, en cada build.
Capturado en vivo por el primer `./ai/scripts/verify.sh`/suite corridos durante esta
implementación (`CHECK_FAILED: debugger: tier fast model openai/gpt-5.6-luna needs the 'openai'
subscription...`). Cerrado alineando `load_role_tiers` (`:566-584`) al mismo contrato que
`load_roles` (false explícito muere, `SET_AGENTS_STRICT_MODELS=1` fuerza el die histórico,
ausente-y-detectado carga en silencio, ausente-y-no-detectado degrada a `WARN degraded`).
Documentado en ADR-0048.

## Trampa ADR-0043 encontrada y cerrada (mismo motivo)

Mi primera versión de `models_config.py` declaraba `STATE_DIR = Path(os.environ.get(...) or
Path.home() / ".local/state/set-agentes")` a nivel de módulo — exactamente el literal que
`tests/test_routing.py::test_adr0043_ac10_no_call_site_still_passes_the_legacy_state_dir_shaped_root`
existe para prohibir en este archivo (una segunda raíz independiente para el mismo directorio).
El propio gate lo capturó en vivo. Cerrado: `subscriptions_overlay_path()` resuelve
`set_agents_app.STATE_DIR` vía import diferido (dentro de la función, nunca a nivel de módulo —
evita el ciclo real, ya que `set_agents_app` importa `models_config` incondicional en su propio
nivel de módulo), sin redeclarar el directorio. Confirmado: `grep -n
'Path.home() / ".local/state/set-agentes"' ai/scripts/models_config.py` → sin resultados.

## Verificación en memoria (subscriptions ausente + LANES + small model)

```
$ python3 -c "
import sys; sys.path.insert(0, 'ai/scripts')
import models_config as mc
config = mc.load_config()
print('subscriptions:', config['subscriptions'])
print('LANES:', mc.LANES)
for lane in mc.LANES:
    roles = mc.load_roles(lane)
    print(lane, 'OK', len(roles), 'roles')
print('small_model(openai-only):', mc.small_model('openai-only'))
print('subscription_of(...):', mc.subscription_of(mc.small_model('openai-only'), config))
"
subscriptions: {}
LANES: ('go-zen', 'zen', 'openai-only')
go-zen OK 28 roles
zen OK 28 roles
openai-only OK 28 roles
small_model(openai-only): openai/gpt-5.4-mini
subscription_of(...): openai
```

`load_roles('openai-only')` no imprime ningún `WARN degraded` en esta máquina (el probe detecta
sus credenciales reales vía el overlay + la red tri-estado — nada que reportar).

## La migración: decisiones de ruteo antes y después (misma máquina)

**Backup de `STATE_DIR` tomado antes de escribir nada bajo `~`:**
`cp -a ~/.local/state/set-agentes /var/tmp/.../state-backup/set-agentes-backup-1786689955`
(scratchpad de esta sesión — el directorio no traía `subscriptions.local.toml` todavía, así que
el backup lo confirma: el archivo es enteramente nuevo, escrito por esta implementación).

**Antes** (tracked `models.toml` con `anthropic=true, ollama=false, openai=true, zen=true`,
lane `local`, sin overlay): `--route-decide` para `orchestrator` y `implementer`.

```json
orchestrator (antes): {"command": "route-decide", "data": {"bias_class": "decision", "context_ok": false, "decision_id": "dec1_5fe327b06f3dac01f30ac8c6291eed1f", "effort": "medium", "exclusions": [], "execution_enabled": false, "fallback_identity": ["rt1_19b417ba8ec5fd2a", "opencode", "openai-codex", "gpt-5.6-luna", "gpt-5.6", "low"], "family": "grok", "feature_id": null, "independence_verified": false, "model": "grok-4.5", "package_id": null, "preference_configured": false, "provider": "opencode-go", "reason_codes": ["MODEL_METADATA_INFERRED tier=balanced family=grok", "BILLING_RANK provider=opencode-go rank=0", "MODEL_PINNED opencode-go/grok-4.5"], "role_class": "other", "route_id": "rt1_4f43973f3f9d5883", "run_id": null, "runtime": "opencode", "selection_path": "pin", "tier": "balanced"}, "ok": false, "reason_codes": ["MODEL_METADATA_INFERRED tier=balanced family=grok", "BILLING_RANK provider=opencode-go rank=0", "MODEL_PINNED opencode-go/grok-4.5"], "schema_version": 2, "warnings": []}

implementer (antes): {"command": "route-decide", "data": {"bias_class": "build", "context_ok": false, "decision_id": "dec1_a15f6b4fa5d026b22e9d90db32f881cc", "effort": "medium", "exclusions": [20 x TIER_INSUFFICIENT], "execution_enabled": true, "fallback_identity": ["rt1_ccb6955af7ce0d2d", "claude-code", "anthropic", "sonnet", "sonnet", "medium"], "family": "gpt-5.6", "feature_id": null, "independence_verified": false, "model": "gpt-5.6-sol", "package_id": null, "preference_configured": false, "provider": "openai-codex", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "role_class": "writer", "route_id": "rt1_5a0df34ea168a966", "run_id": "run1_721e7e205352a7c65a89c161b650272a", "runtime": "opencode", "selection_path": "dynamic", "tier": "balanced"}, "ok": true, "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "schema_version": 2, "warnings": []}
```

**Migración ejecutada** (`models_config.write_subscription_overlay`, una llamada por
suscripción, ANTES de neutralizar el tracked file): `anthropic=True, ollama=False, openai=True,
zen=True` → `~/.local/state/set-agentes/subscriptions.local.toml` (verificado byte a byte igual
a lo que estaba en `models.toml:6-10` antes de tocarlo).

**Después** (tracked `models.toml` neutro, lane `openai-only`, overlay poblado): mismo
`--route-decide`, mismos descriptores.

```json
orchestrator (después): {"command": "route-decide", "data": {"bias_class": "decision", "context_ok": false, "decision_id": "dec1_c2a89e1c4696fb1c291d87e1a7b86e72", "effort": "medium", "exclusions": [], "execution_enabled": false, "fallback_identity": ["rt1_19b417ba8ec5fd2a", "opencode", "openai-codex", "gpt-5.6-luna", "gpt-5.6", "low"], "family": "grok", "feature_id": null, "independence_verified": false, "model": "grok-4.5", "package_id": null, "preference_configured": false, "provider": "opencode-go", "reason_codes": ["MODEL_METADATA_INFERRED tier=balanced family=grok", "BILLING_RANK provider=opencode-go rank=0", "MODEL_PINNED opencode-go/grok-4.5"], "role_class": "other", "route_id": "rt1_4f43973f3f9d5883", "run_id": null, "runtime": "opencode", "selection_path": "pin", "tier": "balanced"}, "ok": false, "reason_codes": ["MODEL_METADATA_INFERRED tier=balanced family=grok", "BILLING_RANK provider=opencode-go rank=0", "MODEL_PINNED opencode-go/grok-4.5"], "schema_version": 2, "warnings": []}

implementer (después): {"command": "route-decide", "data": {"bias_class": "build", "context_ok": false, "decision_id": "dec1_f929af80fd9a2e5f69c7b7cf7ee0e918", "effort": "medium", "exclusions": [20 x TIER_INSUFFICIENT], "execution_enabled": true, "fallback_identity": ["rt1_ccb6955af7ce0d2d", "claude-code", "anthropic", "sonnet", "sonnet", "medium"], "family": "gpt-5.6", "feature_id": null, "independence_verified": false, "model": "gpt-5.6-sol", "package_id": null, "preference_configured": false, "provider": "openai-codex", "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "role_class": "writer", "route_id": "rt1_5a0df34ea168a966", "run_id": "run1_8d4532a948afdded1d35a1bc20882711", "runtime": "opencode", "selection_path": "dynamic", "tier": "balanced"}, "ok": true, "reason_codes": ["BILLING_RANK provider=openai-codex rank=0"], "schema_version": 2, "warnings": []}
```

**Comparación programática** (todos los campos salvo `decision_id`/`run_id`, que son un id
aleatorio por decisión, no una propiedad de la decisión):

```
orchestrator: IDENTICAL=True
implementer: IDENTICAL=True
```

Re-verificado una segunda vez después de terminar toda la implementación (subscripciones
neutras + rename + overlay + fix de `load_role_tiers` + fix del literal ADR-0043, todo aplicado):

```
IDENTICAL: True   # orchestrator, --route-decide re-corrido contra el árbol final
```

**Por qué da idéntico, medido, no supuesto:** `grep -rn "subscriptions" ai/scripts/routing.py
ai/scripts/routing_core/*.py` → sin resultados. `[subscriptions]` nunca llega a
`routing.compose`/`service.route` — sólo gatea `load_roles`/`load_role_tiers` (die/WARN de
validación) y el display del wizard. La migración se hizo de todos modos porque esos dos sí
dependen de ella (ver AC-03 arriba y la sección "Efecto colateral").

## Wizard ya no ensucia el árbol / `tree_clean()` sigue verde

Corrido contra el `models.toml` REAL de este repo (no una copia), después de todos los demás
cambios de este paquete:

```
$ git diff --stat -- models.toml
 models.toml | 92 +++++++++++++++++++++++++++++++++----------------------------
 1 file changed, 50 insertions(+), 42 deletions(-)

$ python3 ai/scripts/setup_models.py --add anthropic
SUBSCRIPTION_WRITTEN anthropic=true (/home/federico/.local/state/set-agentes/subscriptions.local.toml)

$ git diff --stat -- models.toml
 models.toml | 92 +++++++++++++++++++++++++++++++++----------------------------
 1 file changed, 50 insertions(+), 42 deletions(-)
```

Idéntico antes y después — `--add` (y por el mismo código, `--drop` y el wizard) nunca tocan
`models.toml`. `set_agents_app.tree_clean()` (`git status --porcelain == ""`) evalúa
exactamente lo mismo antes y después de correr el comando: cero cambio de estado adicional.

**Guardia con rojo/verde real** (no la sexta guarda hueca): `tests/test_harness.py::
test_setup_models_drop_subscription_writes_the_overlay_not_the_tracked_file` neutraliza el
efecto (`--drop ollama` en una copia temporal del `models.toml` real) y afirma
`self.assertEqual(before, models.read_text(), "models.toml must stay untouched -- AC-05")` —
con el código PRE-AC-05 (`config["subscriptions"][args.drop] = False` + `emit_atomic` al
tracked file), esta aserción fallaba (el archivo cambiaba); con el código actual, pasa.
Confirmado corriendo la suite completa (ver Gates).

## `load_role_tiers`: rojo confirmado, revertido, verde confirmado

```
# Con el fix (models_config.py:566-584) revertido temporalmente (cp de respaldo):
$ python3 -m unittest tests.test_probe_subscriptions.SubscriptionTriStateTests.test_tier_table_explicit_false_still_dies tests.test_probe_subscriptions.SubscriptionTriStateTests.test_tier_table_absent_and_detected_loads_silently tests.test_probe_subscriptions.SubscriptionTriStateTests.test_tier_table_absent_and_undetected_warns_but_never_dies -v
...
FAILED (errors=2)   # los dos casos "absent" mueren con ModelsError -- exactamente el defecto

# Restaurado el fix:
$ python3 -m unittest tests.test_probe_subscriptions -v
...
OK   # 11/11, incluidas las tres nuevas
```

## Gates

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
...
Ran 1113 tests in 1067.185s

OK (skipped=3)
```

(Base: 1110 OK / 3 skips. +3 tests nuevos —`load_role_tiers` tri-state, `tests/test_probe_
subscriptions.py`—; el resto de los cambios de AC-04/AC-05 renombran tests existentes, sin
sumar de más. 1110+3=1113, coincide exacto.)

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
...
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1113 tests in 952.435s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```
(corrida completa, literal — incluye su propio `build.sh --check`, la suite completa de nuevo
con el mismo 1113/3, `py_compile`, `git diff --check`, el diff de `Global/{opencode,claude-code,
codex,pi}` contra un build fresco y los tres guardianes finales, los cuatro en verde.)

```
$ ./build.sh
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
$ git status --porcelain -- Global/ | wc -l
0
```

(Cero diff en `Global/` tras regenerar: `[subscriptions]` no cambia bytes de salida —sólo
gatea WARN/die de validación—, y el rename de lane no toca ninguna celda que `--profile go-zen`
lea. Confirma que este paquete no necesita re-commitear `Global/`.)

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

```
$ git diff --check
(sin salida, rc=0)
```

Generación de las tres lanes (contrato completo, no sólo la forzada por `--check`):

```
$ ./build.sh --output /tmp/out-go-zen --profile go-zen
CHECK_PASS: generated and validated profile go-zen
$ ./build.sh --output /tmp/out-zen --profile zen
CHECK_PASS: generated and validated profile zen
$ ./build.sh --output /tmp/out-openai-only --profile openai-only
CHECK_PASS: generated and validated profile openai-only
```

## Incidente propio, corregido en el momento (transparencia)

Al ejecutar la suite de tests con la implementación de `setup_models.py` ya aplicada pero
ANTES de terminar de actualizar `tests/test_models_wizard_ui.py`, el test viejo
`test_subscription_auto_removes_the_key` (sin mockear `write_subscription_overlay`, porque
todavía no sabía que el código de producción ya llamaba a la función real) ejecutó una
escritura real contra `~/.local/state/set-agentes/subscriptions.local.toml`, borrando la clave
`ollama` recién migrada. Detectado inmediatamente al correr `--add anthropic` de prueba y ver
sólo 3 claves en el overlay en vez de 4. Restaurado con
`models_config.write_subscription_overlay('ollama', False)` (mismo valor que tenía el
`models.toml` original). Re-verificado: `--route-decide` sigue idéntico (ver arriba, segunda
corrida) y el overlay quedó con las cuatro claves originales. Causa cerrada: el test se
reescribió para mockear `write_subscription_overlay` (ver `tests/test_models_wizard_ui.py`), y
todo test nuevo de este paquete que alcanza el camino de escritura real corre contra un
`SET_AGENTS_STATE` aislado (`tests/test_harness.py::_setup_models`, actualizado para siempre
pasar `env={"SET_AGENTS_STATE": ...}`) o mockea la función.

## Archivos tocados

Dentro de ALCANCE: `models.toml`, `ai/scripts/models_config.py`, `ai/scripts/setup_models.py`,
`tests/fixtures/models.toml`, `tests/test_auto_profile.py`, `tests/test_harness.py`,
`tests/test_models_wizard_ui.py`, `tests/test_probe_subscriptions.py`,
`docs/adr/0048-subscriptions-neutral-overlay-lane-rename.md` (nuevo), `docs/adr/README.md`,
`Global/` (regenerado por `./build.sh`, diff vacío — nada quedó pendiente de commitear ahí).

Fuera del ALCANCE literal, tocados y flageados (prosa desactualizada por el rename, no lógica):
`build.sh:13` (string de uso: `--profile go-zen|zen|local` → `--profile go-zen|zen|openai-only`),
`COMO-CAMBIAR-MODELO.md` (nombre de lane + sección de suscripciones/overlay), `TIPS-USO.md:39`
(nombre de lane en la lista de `active-profile`). Ningún cambio de lógica en ninguno de los tres.

`~` tocado: `~/.local/state/set-agentes/subscriptions.local.toml` (nuevo archivo, escrito por
diseño — AC-05). Backup de `STATE_DIR` tomado antes de escribir nada
(`/var/tmp/.../state-backup/set-agentes-backup-<epoch>/`, scratchpad de esta sesión). Incidente
propio de contaminación durante testing, detectado y corregido en el momento (ver sección
arriba) — el valor final coincide exactamente con el `models.toml` original.

## Fuera de alcance (no tocado, según el context pack)

Primer arranque / `ROUTING_UNCONFIGURED` (C3), `LICENSE`/matriz de soporte (C4), el sort key,
`ai/state`/siembra (C1, ya aceptada), el aislamiento roto de los módulos de test vía `_import`
(preexistente — confirmado en vivo: `test_variant_coherence_gate_fails_build_on_unprojectable_
tier_model` falla en soledad con `ModuleNotFoundError: No module named 'provider_registry'` y
pasa corrida junto a otro módulo de test, mismo síntoma que el registrado), features 025/026.
`[areas.*]`/`[roles.*]` (incluido `[areas.coord]`, el modelo del orquestador) no se tocaron en
valor — sólo la clave de lane renombrada, como pide AC-04; no son overlay porque son decisión
curatorial del repo, no estado de credenciales de una máquina (razonado en ADR-0048).
