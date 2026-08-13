# P3-liveness-real — evidencia del implementer

Estado: COMPLETO

## Medición en vivo, campos solamente (nunca valores) — punto de partida real

`~/.codex/auth.json` (`lstat`: uid propio, `mode 0o100600`):
```
{
 "auth_mode": "str",
 "OPENAI_API_KEY": "NoneType",
 "tokens": {"id_token": "str", "access_token": "str", "refresh_token": "str", "account_id": "str"},
 "last_refresh": "str"
}
```

`~/.claude/.credentials.json` (`lstat`: uid propio, `mode 0o100600`):
```
{
 "mcpOAuth": {"plugin:vercel:vercel|<hash>": {"serverName": "str", "serverUrl": "str",
   "accessToken": "str", "discoveryState": {...}, "clientId": "str", "redirectUri": "str"}},
 "claudeAiOauth": {"accessToken": "str", "refreshToken": "str", "expiresAt": "int",
   "refreshTokenExpiresAt": "int", "scopes": "list", "subscriptionType": "str", "rateLimitTier": "str"}
}
```

Confirma exactamente lo que el context pack mide: `mcpOAuth` vive en el mismo archivo que
`claudeAiOauth` (hoy un token de Vercel), y codex tiene `tokens.account_id` mientras que
claude-code no tiene ningún campo de identidad de cuenta.

## Captura A/B del refresh real — decisión de seguridad, no de conveniencia

**No forcé un refresh real contra el backend OAuth de Anthropic/OpenAI**, ni siquiera con
`HOME` apuntado a una copia aislada. Motivo: los proveedores OAuth suelen rotar el
`refresh_token` del lado del servidor en cada uso (single-use rotating refresh tokens) — si
eso es cierto acá, ejecutar un refresh real usando el `refresh_token` real (aunque el
resultado se escriba solo en una copia con `HOME` desviado) invalidaría del lado del servidor
el `refresh_token` que sigue viviendo en el archivo REAL (`~/.claude/.credentials.json`,
nunca tocado), dejando al usuario sin sesión válida mañana a la mañana. Ese riesgo tiene la
misma severidad que la instrucción explícita de nunca correr un `logout` real ("el usuario
está durmiendo y depende de esas credenciales mañana") y lo traté con la misma disciplina,
aunque no esté nombrado literalmente.

Intenté una A/B **pasiva** (sin forzar nada): medí ambos archivos al empezar la tarea (T0) y
otra vez al terminar la implementación (T1, antes de correr los gates), sin ninguna acción mía
sobre esos archivos en el medio:

```
T0 (2026-08-13T~00:35Z aprox.)
codex   last_refresh=2026-08-10T13:09:56.660684973Z  account_id sha256[:12]=bd7fdcdb430d
claude  scopes=['user:file_upload','user:inference','user:mcp_servers','user:profile','user:sessions:claude_code']
        subscriptionType=max  rateLimitTier=default_claude_max_5x  expiresAt=1786607838466

T1 (2026-08-13T04:13:27Z)
codex   last_refresh=2026-08-10T13:09:56.660684973Z  account_id sha256[:12]=bd7fdcdb430d   (sin cambios)
claude  scopes=[...misma lista...]  subscriptionType=max  rateLimitTier=default_claude_max_5x
        expiresAt=1786607838466   (sin cambios — ningún refresh natural ocurrió en la ventana)
```

No hubo ningún refresh natural en la ventana de esta sesión (esperable: `expiresAt` de
claude-code estaba ~4h por delante de "ahora" al empezar), así que **no hay una medición A/B
de un refresh real dentro de esta sesión — queda marcado "sin verificar mediante refresh
observado o forzado"**, explícitamente, no simulado como certeza.

El diseño es robusto a esa incertidumbre por construcción, no por suerte: la firma de
claude-code nunca lee `refreshToken`/`accessToken` (si esos SÍ rotan, es irrelevante para la
firma), y los tres campos que sí lee (`scopes`, `subscriptionType`, `rateLimitTier`) son, por
semántica de OAuth, atributos del *grant*/plan, no del *token* — un argumento de diseño
explícito, marcado como tal, no como medición. Ídem para `tokens.account_id` de codex: es un
identificador de cuenta estable, no material de sesión. Detalle completo del razonamiento en
`docs/adr/0043-que-prueba-un-probe.md`, sección "4. Supuesto validado".

## Tabla AC → cambio → prueba

| AC | Cambio | `archivo:línea` | Prueba |
|---|---|---|---|
| AC-07 (codex) | `_codex_auth_signature()`: solo `tokens.account_id` + presencia de `OPENAI_API_KEY`, hasheado | `routing_core/catalog.py:425-446` | `test_adr0043_ac07_ac08_codex_auth_signature_ignores_rotating_material_reacts_to_logout` (`tests/test_routing.py:3921`) — MORDIDO |
| AC-07 (claude-code) | `_claude_code_auth_signature()`: solo `claudeAiOauth.{scopes,subscriptionType,rateLimitTier}`, nunca `mcpOAuth`, hasheado | `routing_core/catalog.py:448-469` | `test_adr0043_ac07_ac08_claude_code_auth_signature_ignores_material_and_the_unrelated_mcp_block` (`tests/test_routing.py:3952`) — MORDIDO |
| AC-07 (pi) | `_pi_auth_signature()`: `pi_auth_provider_keys()` + `PI_PINNED_VERSION`, hasheado | `routing_core/catalog.py:471-479` | `test_adr0043_ac07_pi_auth_signature_folds_provider_keys_and_the_pinned_version` (`tests/test_routing.py:3988`) |
| AC-07 (opencode + binarios) | `_binary_signature(name)` generaliza el viejo `_opencode_binary_signature` a `opencode`/`codex`/`claude` | `routing_core/catalog.py:366-384` | `test_adr0043_ac07_binary_signature_covers_opencode_codex_and_claude` (`tests/test_routing.py:4000`) |
| AC-07 (lectura compartida) | `_read_credential_json(path)`: `lstat`, nunca symlink, archivo regular, uid propio, JSON válido, dict | `routing_core/catalog.py:408-422` | Cubierto por el test de AC-09 fail-closed (abajo) — MORDIDO |
| AC-07 (wiring en `_cache_key`) | Las seis firmas se pliegan en `_cache_key` | `routing_core/catalog.py:506-528` (llamadas en `:531-533`) | `test_adr0043_ac07_cache_key_folds_every_runtime_signature` (`tests/test_routing.py:4016`) — MORDIDO (dos formas: quitar `_pi_auth_signature` de la clave, y verificar por spy que `_binary_signature` se llama con los tres nombres) |
| AC-07 (cero subprocesos nuevos) | Ninguna de las seis funciones nuevas llama `subprocess.run` | `routing_core/catalog.py:366-479` | `test_adr0043_ac07_cache_key_never_spawns_a_subprocess_for_the_new_signatures` (`tests/test_routing.py:4043`) — MORDIDO |
| AC-08 propiedad 1 (refresh no cambia la firma) | Ver AC-07 (codex/claude-code) arriba, más el end-to-end | `routing_core/catalog.py:425-469` | Unit: los dos tests de AC-07 arriba. End-to-end vía `probe_inventory`: `test_adr0043_ac07_ac08_codex_refresh_keeps_the_cache_warm_and_logout_invalidates_it_via_probe_inventory` (`tests/test_routing.py:4055`) — MORDIDO |
| AC-08 propiedad 2 (logout invalida) | Ídem — archivo ausente ⇒ firma vacía ⇒ nunca matchea | `routing_core/catalog.py:425-469` | Mismos tests que la propiedad 1 — MORDIDO |
| AC-09 (disciplina de seguridad) | `_read_credential_json`: `lstat`, nunca symlink, uid propio; fail-closed en cualquier sorpresa | `routing_core/catalog.py:408-422` | `test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json` (`tests/test_routing.py:4086`) — MORDIDO |
| AC-09 (bump de schema + test) | `_CACHE_SCHEMA_VERSION` 2 → 3, con test nuevo (antes no existía ninguno) | `routing_core/catalog.py:25-33` | `test_adr0043_ac09_cache_schema_version_bump_invalidates_old_cache_documents` (`tests/test_routing.py:4113`) — MORDIDO |
| AC-09 (límite claude-code declarado) | Sin campo de identidad de cuenta en claude-code; documentado, no disimulado | `docs/adr/0043-que-prueba-un-probe.md` sección "3" | Lectura directa del ADR + docstring de `_claude_code_auth_signature` (`catalog.py:448-460`) |
| AC-10 (poda de la legada) | `prune_legacy_probe_cache(legacy_root)`, misma disciplina que `_write_probe_cache` | `routing_core/catalog.py:620-651` | `test_adr0043_ac10_prune_legacy_probe_cache_removes_only_the_validated_sibling_file` (`tests/test_routing.py:4133`) y `test_adr0043_ac10_prune_legacy_probe_cache_never_crosses_a_symlink_or_a_wrong_mode_directory` (`tests/test_routing.py:4147`) — ambos MORDIDOS |
| AC-10 (raíz única, `set_agents_app.py`) | `_probe_cache_root()` = `_routing_store().root` (atributo puro, sin I/O), reemplaza `cache_root=STATE_DIR` en los 4 sitios | `set_agents_app.py:73-86` (helper); call sites `:178, :539, :891, :3187`; poda en `:538, :890, :3186` | `test_adr0043_ac10_probe_cache_root_follows_the_routing_test_root_seam_not_state_dir` (`tests/test_routing.py:4169`), `test_adr0043_ac10_cmd_route_doctor_uses_the_single_root_and_prunes_the_legacy_file` (`:4176`) — MORDIDO, `test_adr0043_ac10_cmd_doctor_all_uses_the_single_root_and_prunes_the_legacy_file` (`:4199`) |
| AC-10 (raíz única, `models_config.py`) | `_probe_cache_root()` = `RoutingStore().root`, reemplaza `Path.home() / ".local/state/set-agentes"` en 2 sitios | `models_config.py:271-280` (helper); call sites `:292, :310` | `test_adr0043_ac10_models_config_probe_cache_root_is_the_single_store_root_not_state_dir` (`tests/test_routing.py:4218`) — MORDIDO |
| AC-10 (tripwire, no regresión) | Grep sobre ambos módulos: ningún sitio pasa el STATE_DIR legado | — | `test_adr0043_ac10_no_call_site_still_passes_the_legacy_state_dir_shaped_root` (`tests/test_routing.py:4223`) — MORDIDO |
| ADR-0043 | Nuevo, indexado en README | `docs/adr/0043-que-prueba-un-probe.md`, `docs/adr/README.md` | Lectura directa |

## Prueba de "ninguna firma nueva agrega un subproceso"

Test dedicado, corrido y mordido (arriba). Además, verificación end-to-end real: correr
`--route-doctor`/`--doctor-all` en la máquina real no agrega ninguna llamada nueva a
`codex`/`claude` más allá de las que YA hacía el probe existente (`codex login status`,
`claude auth status --json`) — las seis firmas nuevas son `stat`/lectura de archivo, medido
con `mock.patch.object(cat.subprocess, "run", side_effect=fail)` envolviendo `_cache_key`
sola (sin `probe_inventory` alrededor, que sí legítimamente corre subprocesos para el
LISTADO de modelos — eso no cambió). Bite: agregar `subprocess.run(("true",), check=False)`
adentro de `_pi_auth_signature` → el test explota con
`AssertionError: no subprocess may run while computing _cache_key` (confirmado, ver sección
de mordidas más abajo).

## La captura A/B real del comportamiento del sistema en producción — el cierre de AC-10

Máquina real, `~/.local/state/set-agentes/` real, ANTES de tocar nada (dos cachés
confirmadas divergentes, igual que el context pack midió):

```
$ ls -la ~/.local/state/set-agentes/probe-cache.json ~/.local/state/set-agentes/routing-v2/probe-cache.json
-rw------- 1 federico federico 1579 ago 13 00:34 /home/federico/.local/state/set-agentes/probe-cache.json
-rw------- 1 federico federico 1845 ago 13 01:08 /home/federico/.local/state/set-agentes/routing-v2/probe-cache.json
```

Corriendo `set-agents --route-doctor --json` REAL (código de este paquete, sin mocks):

```
$ python3 ai/scripts/set_agents_app.py --route-doctor --json
{"command": "route-doctor", "data": {"cache": {"age_seconds": 36.32856488227844, "key_current": true,
  "reason": "OK", "used": true}, "providers": [...]}, "ok": true, "reason_codes": [], "schema_version": 2, "warnings": []}
```

`"used": true, "key_current": true, "age_seconds": 36.3` — está leyendo la caché de
`routing-v2` (recién escrita 36s antes por una corrida previa de `detect_subscriptions`, ver
abajo), no la legada de 00:34. Después de esa corrida:

```
$ ls ~/.local/state/set-agentes/probe-cache.json
ls: no se puede acceder a '.../probe-cache.json': No existe el fichero o el directorio
$ ls -la ~/.local/state/set-agentes/routing-v2/probe-cache.json
-rw------- 1 federico federico 1845 ago 13 01:08 /home/federico/.local/state/set-agentes/routing-v2/probe-cache.json
```

La legada quedó podada (borrada); la de `routing-v2` sigue intacta, mismo tamaño y mismo
mtime que antes (`route_doctor` nunca la escribe — contrato preexistente, ADR-0035, sin
tocar). Confirma en la máquina real, con credenciales reales, el criterio de cierre de la
spec: *"--route-doctor reportando sobre la caché que el decisor realmente usa"*.

Corrida adicional de `--doctor-all` (real, después de la poda) — sin error, siete pares
detectados incluyendo los tres runtimes que antes de este paquete no aportaban firma:

```
$ python3 ai/scripts/set_agents_app.py --doctor-all
PROVIDER anthropic runtime=claude-code models=4
PROVIDER openai-codex runtime=codex models=6
PROVIDER openai-codex runtime=opencode models=6
PROVIDER opencode-go runtime=opencode models=18
PROVIDER opencode-zen runtime=opencode models=58
PROVIDER anthropic runtime=pi models=3
PROVIDER openai-codex runtime=pi models=6
```

El documento de caché real sigue con la disciplina de redacción de siempre (`_write_probe_cache`):

```
$ python3 -c "import json; d=json.load(open('.../routing-v2/probe-cache.json')); print(sorted(d.keys())); print(len(d['key']))"
['at', 'key', 'pairs']
64
```

Solo `{"key","at","pairs"}` — el `key` es un hash sha256 (64 hex), nunca un valor de
credencial cruda.

## Migración de dos cachés a una

Los seis sitios (`set_agents_app.py:178,539,891,3187` y `models_config.py:292,310`) migraron
a `_probe_cache_root()` — un helper por módulo que expone `RoutingStore().root` (atributo
puro sin I/O, misma pereza que `STATE_DIR` ya tenía) para no crear directorios como efecto
secundario de una lectura diagnóstica ni tocar el filesystem dentro de un test que mockea
`probe_inventory` (ver "Trampa nueva encontrada" abajo). La poda del archivo legado
(`prune_legacy_probe_cache`) corre en las tres superficies "vidriera"
(`cmd_route_doctor`, `cmd_doctor_all`, `_estado_general_lines`) — best-effort, nunca bloquea
el diagnóstico si falla.

### Trampa nueva encontrada durante la implementación (no estaba en el context pack)

`test_adr0034_f05_repair_effective_providers_short_circuits_when_base_covers_discoverable`
(preexistente) llama `app._effective_preference_providers()` directamente, sin ningún aislamiento
de entorno, mockeando solo `routing_core.catalog.probe_inventory`. Si `_probe_cache_root()`
hubiera llamado `RoutingStore().ensure_cache_root()` (que SÍ hace I/O — crea directorios), ese
test habría creado `~/.local/state/set-agentes/routing-v2` de verdad en la máquina de
CUALQUIERA que corra la suite, porque el argumento `cache_root=` se evalúa ANTES de invocar
`probe_inventory` (que sí está mockeado) — el mock nunca llega a proteger el cómputo del
argumento en sí. Por eso `_probe_cache_root()` usa `RoutingStore().root` (un atributo puro,
sin I/O al construirse) en vez de `ensure_cache_root()`: la validación/creación real sigue
viviendo exactamente donde siempre vivió, dentro de `probe_inventory`/`_validate_cache_dir`
(que nunca crea, solo valida). Confirmado que el test preexistente sigue en verde sin tocar
el filesystem real (corrida completa de `tests/test_routing.py`, ver Gates).

## Bump de schema

`_CACHE_SCHEMA_VERSION` 2 → 3 (`catalog.py:33`), con test nuevo — antes no existía ninguno.
Mordido (ver Gates/Mordidas).

## Mordidas — cada test nuevo, en las dos direcciones

Metodología: `cp` del archivo original a `/var/tmp/.../scratchpad/bites/*.orig` antes de
mutar; mutación in-place con un script Python (nunca `git checkout`/`stash`); corrida del
test específico para confirmar ROJO; `cp` de vuelta desde el backup para restaurar; corrida
de nuevo para confirmar VERDE. Al final, `diff` byte-a-byte contra los tres backups confirma
restauración exacta de los tres archivos tocados.

| # | Mordida | Test que debía fallar | Resultado |
|---|---|---|---|
| 1 | `_codex_auth_signature` también lee `tokens.access_token` (rotante) | `test_adr0043_ac07_ac08_codex_auth_signature_ignores_rotating_material_reacts_to_logout` + el end-to-end | ROJO confirmado (`AssertionError` de hash distinto tras el "refresh"; y `bin/codex` reprobado quedó en el log cuando no debía) |
| 2 | `_claude_code_auth_signature` hashea también `mcpOAuth` completo | `test_adr0043_ac07_ac08_claude_code_auth_signature_ignores_material_and_the_unrelated_mcp_block` | ROJO confirmado (la firma cambia con un refresh de MCP simulado, exactamente la trampa) |
| 3 | `_pi_auth_signature` agrega `subprocess.run(("true",))` | `test_adr0043_ac07_cache_key_never_spawns_a_subprocess_for_the_new_signatures` | ROJO confirmado (`AssertionError: no subprocess may run...`) |
| 4 | `_CACHE_SCHEMA_VERSION` revertido a `2` | `test_adr0043_ac09_cache_schema_version_bump_invalidates_old_cache_documents` | ROJO confirmado (`AssertionError: 2 != 3`) |
| 5 | `prune_legacy_probe_cache` sin chequeo de symlink en el ARCHIVO | `test_adr0043_ac10_prune_legacy_probe_cache_never_crosses_a_symlink_or_a_wrong_mode_directory` | ROJO confirmado (borraría a través de un symlink) |
| 6 | `cmd_route_doctor` vuelve a `cache_root=STATE_DIR` | `test_adr0043_ac10_no_call_site_...` + `test_adr0043_ac10_cmd_route_doctor_uses_the_single_root_...` | ROJO confirmado, ambos |
| 7 | `models_config._probe_cache_root` vuelve a `Path.home() / ".local/state/set-agentes"` | `test_adr0043_ac10_models_config_probe_cache_root_...` + el tripwire | ROJO confirmado, ambos |
| 8 | `_cache_key` deja de plegar `_pi_auth_signature()` | `test_adr0043_ac07_cache_key_folds_every_runtime_signature` | ROJO confirmado (misma clave con y sin la firma de pi) |
| 9 | `_read_credential_json` deja de chequear symlink/uid | `test_adr0043_ac09_credential_signatures_fail_closed_on_symlink_and_corrupt_or_foreign_shaped_json` | ROJO confirmado (leyó a través del symlink, devolvió una firma no vacía) |

Restauración final verificada con `diff` byte-a-byte contra los tres `.orig`: los tres
archivos (`catalog.py`, `set_agents_app.py`, `models_config.py`) quedaron exactamente como
antes de cada mordida.

## Gates

```
$ python3 -m unittest tests.test_routing.RoutingTests -v -k adr0043
Ran 16 tests in 5.457s
OK
```

```
$ python3 -m unittest tests.test_routing -v          # archivo completo
Ran 283 tests in 146.582s
OK
```

```
$ python3 -m unittest tests.test_auto_profile tests.test_probe_subscriptions -v
Ran 15 tests in 11.525s
OK
```

Gates completos (comandos exactos de la consigna, vía `heartbeat-run.py --interval 20 --`):

```
$ ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
----------------------------------------------------------------------
Ran 1006 tests in 539.103s

OK (skipped=3)
```

Base declarada: 990 OK / 3 skips. Con los 16 tests nuevos de este paquete: 1006 OK / 3 skips
(mismos 3 skips de siempre, ninguno nuevo) — exit code 0.

```
$ ./build.sh --check
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

```
$ git diff --check
(sin salida — limpio)
```

```
$ ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
... (1006 tests, todos "ok" o "skipped", ninguno "FAIL"/"ERROR") ...
----------------------------------------------------------------------
Ran 1006 tests in 569.270s

OK (skipped=3)
... (portabilidad, vault, tools-propose, wizard: todo OK) ...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

`verify.sh` re-corrió `build.sh --check`, la suite completa (1006 OK / 3 skips, los mismos
tres skips de siempre — dos E2E de pi con `SET_AGENTS_PI_E2E` no seteado, uno de
`route-decide` sin ruta elegible en esta máquina — ninguno nuevo), `py_compile` de todo
`ai/scripts/*.py`/`routing_core/*.py`/`feature_state_lib/*.py`/`tests/*.py`, `git diff
--check`, y el diff de portabilidad completo contra `Global/`. `VERIFY_PASS` final.

```
$ git diff --check
(sin salida — limpio)
```

## Lo que declino a propósito, con argumento (opcional en el context pack)

**No convertí la firma de opencode a lectura local de `~/.local/share/opencode/auth.json`.**
Razón: reimplementar la normalización que `opencode auth list --pure` ya hace (mapeo de
nombre de proveedor, distinción `●`/`○` pendiente-vs-confirmado) sobre un formato de archivo
no documentado reabre el mismo riesgo de parseo no verificado que ADR-0034 M-1 ya evita para
los CLI ids — y el subprocess de opencode ya es el ÚNICO de toda la composición de la clave,
no el problema que este paquete existe para resolver (el problema medido era "3 de 4 runtimes
sin firma alguna", ya cerrado). Detalle completo en `docs/adr/0043-que-prueba-un-probe.md`,
"Alternativas rechazadas".

## Lo que no pude verificar

- **Rotación real de `scopes`/`subscriptionType`/`rateLimitTier` (claude-code) o de
  `tokens.account_id` (codex) en un refresh de verdad** — sin verificar, por decisión de
  seguridad explícita (ver sección "Captura A/B del refresh real" arriba). El diseño no
  depende de esta medición para ser correcto (nunca lee campos rotantes), pero la ASUNCIÓN en
  sí queda marcada como no confirmada empíricamente dentro de esta sesión — quedó una A/B
  pasiva (T0/T1, sin cambios en la ventana de la sesión) en su lugar.

Todo lo demás en este documento está corrido y confirmado, con evidencia literal pegada
arriba.
