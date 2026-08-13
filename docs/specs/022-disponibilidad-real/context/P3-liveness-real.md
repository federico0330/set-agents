# Context pack — P3-liveness-real

Spec: `docs/specs/022-disponibilidad-real/spec.md`, **AC-07, AC-08, AC-09, AC-10**. Depende de
**P2** (`resolve_ceiling`, ya aceptada). Es el paquete que más le importa al usuario: mañana suma
Copilot y opencode-go, y este paquete decide si el harness se entera.

## El defecto

`_cache_key` (`catalog.py:402-416`) sólo lleva firma de credencial de **opencode**. Dar de baja
una credencial en codex, claude-code o pi es invisible hasta que expira el TTL — `PROBE_CACHE_TTL
= 300.0` (`:24`). Y hay **dos cachés divergentes en disco**, confirmado en vivo:

```
-rw------- 1579 ago 13 00:34 ~/.local/state/set-agentes/probe-cache.json
-rw------- 1845 ago 13 00:35 ~/.local/state/set-agentes/routing-v2/probe-cache.json
```

Distinto tamaño, escritas con un minuto de diferencia. `--route-doctor` inspecciona la primera;
la vía de decisión usa la segunda. El diagnóstico mira un archivo que el decisor no usa.

## Evidencia nueva de esta sesión que la spec NO tenía. Leela: cambia el diseño.

### 1. El probe pregunta "¿podés listar?" y responde "está vivo". Son preguntas distintas.

Medido hoy, en esta máquina:

- `opencode auth list --pure` → la credencial **OpenAI está presente**.
- `opencode models openai --pure` → lista **13 modelos, sin error**.
- `--route-doctor` → `openai-codex: authenticated=true, models_listable=6`.
- Y la **inferencia real** por ese mismo par → `Error: Provided authentication token is expired.`

O sea: el probe da el par por vivo y el proveedor no responde. **No inventes una solución a esto
en P3** —es AC-16/AC-18, P5— pero **no escribas en el ADR que la firma prueba liveness**, porque
no lo hace. Prueba *presencia de credencial*. Decilo con esas palabras.

### 2. La misma cuenta está vencida en un runtime y viva en otro

`codex login status` → `Logged in using ChatGPT`, y `codex exec` **funciona** (devolvió PONG),
con la misma cuenta que opencode reporta vencida. Cada runtime tiene su propio store de
credenciales. **Esto valida empíricamente la firma POR RUNTIME de AC-07**: no es una elección
estética, es que una firma global daría la respuesta equivocada en tres de cuatro casos.

### 3. La firma de hoy cuesta un SUBPROCESO, y eso es lo que no hay que multiplicar

`_live_opencode_auth_signature` (`catalog.py:378-400`) corre `opencode auth list --pure` **en cada
composición que consulta el caché**. AC-07 pide que las firmas nuevas sean `stat`/lectura local.
**Si agregás tres subprocesos más, el remedio es peor que la enfermedad.**

Y hay una mejora que la spec no nombra y que podés tomar **con argumento**: el propio opencode
guarda sus credenciales en `~/.local/share/opencode/auth.json`, así que su firma también podría
pasar a lectura local. No es obligatorio; si lo hacés, justificalo y probá que el comportamiento
no cambia. Si no lo hacés, decí por qué.

## Las credenciales, medidas (claves solamente, nunca valores)

**`~/.codex/auth.json`**
`OPENAI_API_KEY`, `auth_mode`, `last_refresh`, `tokens.{access_token, account_id, id_token, refresh_token}`

→ Tiene **`tokens.account_id`**: identidad de cuenta real. `last_refresh` y los tokens **rotan**.

**`~/.claude/.credentials.json`**
`claudeAiOauth.{accessToken, expiresAt, rateLimitTier, refreshToken, refreshTokenExpiresAt, scopes, subscriptionType}`
y además **`mcpOAuth.{...}`**

→ **Trampa que la spec no vio**: `mcpOAuth` vive en el MISMO archivo (hoy tiene un token de
Vercel). Una firma ingenua tipo "hasheo el archivo entero" o "uso el mtime del archivo" **rota
cada vez que se refresca un token de MCP**, que no tiene nada que ver con la credencial del
proveedor. Resultado: probe fresco en cada decisión. La firma tiene que leer **campos
nombrados de `claudeAiOauth`**, nunca el archivo completo ni su mtime.

→ Confirmado el límite que Federico aceptó: **no hay ningún campo de identidad de cuenta**. Los
no-rotantes (`scopes`, `subscriptionType`, `rateLimitTier`) no identifican una cuenta. Así que
para claude-code la firma detecta **presencia y ausencia**, no un cambio de cuenta a otra del
mismo plan sin pasar por logout. Se declara en ADR-0043, no se disimula. Hashear el
`refreshToken` **no** se hace.

**Supuesto a validar temprano, con medición, no de memoria** (AC-09): que `refreshToken`,
`scopes` y `subscriptionType` efectivamente no roten en un refresh normal. Captura A/B. Si rotan,
la firma de claude-code hay que rediseñarla y eso cambia el paquete.

## AC-08 — las dos propiedades que hacen o rompen esto

Cada una con su test, y son lo primero que escribís:

1. **Refresh de token** (cambia sólo token/expiry) ⇒ la firma **NO** cambia y el caché sirve.
   Sin esto, Claude Code renueva OAuth y probeás en cada decisión — hasta 60 s en pi
   (`PI_PROBE_MIN_TIMEOUT_SECONDS`).
2. **Logout / credencial borrada** ⇒ la firma **SÍ** cambia ⇒ probe fresco.

## AC-10 — una sola caché

Raíz del store: `store.py:293` (`~/.local/state/set-agentes/routing-v2`) y `ensure_cache_root`
(`:326`), que ya tiene la disciplina de directorio privado y es la que usa la vía de decisión.
Migran `set_agents_app.py:144,497,843,3133` y `models_config.py:258-259,277-278`. La legada se
poda **con las mismas validaciones de seguridad** que `_write_probe_cache` (`_validate_cache_dir`,
`catalog.py:418`).

Bump de `_CACHE_SCHEMA_VERSION` (`catalog.py:28`, hoy `2`) **con su test**: hoy no existe ninguno
que verifique que un bump invalida cachés viejas.

## Disciplina de seguridad — no negociable

Misma que `pi_auth_provider_keys` (`catalog.py:343-350`): `lstat`, archivo regular, uid propio,
**sólo nombres de campo**, hash antes de guardar, **jamás** en un log ni en el envelope. Leer
archivos de credencial es superficie sensible nueva; si dudás, fail-closed (firma vacía ⇒ cache
miss ⇒ probe fresco), nunca fail-open.

## Restricciones

- **ADR-0043** (`ls docs/adr/` para confirmar que está libre, indexalo en `docs/adr/README.md`):
  qué prueba realmente un probe, el límite de claude-code, y la declaración de que **pi descubre
  modelos, no credenciales** (`pi_auth_provider_keys` sólo confirma claves ya conocidas, y sus dos
  proveedores ya están auditados por otros runtimes: **pi nunca puede aportar un proveedor nuevo**).
- **Sin refactors oportunistas.** No toques el sort key. No probees dentro de `route()`. No
  agregues subprocesos al camino de decisión.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- No relajes, saltees ni borres tests.

## Alcance

`ai/scripts/routing_core/catalog.py` · `ai/scripts/routing_core/store.py` ·
`ai/scripts/set_agents_app.py` · `ai/scripts/models_config.py` · `tests/test_routing.py` ·
`docs/adr/` . **Si aparece un séptimo archivo, pará y reportalo.** Sabelo:
`check-owned-paths.py:40-42` usa `git diff --name-only` y **no ve archivos nuevos** — la disciplina
la ponés vos, no el control.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **990 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos exactamente así:**

```
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
```

No los pipees a `tail`: sin `-f` no emite un byte hasta EOF, la suite tarda ~9 minutos y el
watchdog te mata a los 600 s (ADR-0041). Es el comando, no una opción.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P3-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; la captura A/B del refresh real; las dos propiedades
de AC-08 con su test; la prueba de que **ninguna firma nueva agrega un subproceso**; la migración
de las dos cachés a una con la poda validada; el bump de schema con su test; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En P1 de
esta misma feature, dos de tres guardas pasaban en **verde** con la fuente rota. Mordé todo, en las
dos direcciones.

**Cada bloque que pegues es literal, o está marcado como recortado.** Si no lo corriste, "sin
verificar". **Y jamás pegues material de credencial**: nombres de campo sí, valores nunca.

## Checkpoint

Si te acercás al límite de ejecución, escribí progreso parcial **y los próximos pasos exactos** en
la evidencia antes de parar.

## Fuera de alcance

`providers.toml` y `--provider-*` (P4) · altas y bajas automáticas y `--provider-verify` (P5) ·
resolver que "listable ≠ usable" (P5) · el sort key · agregar Copilot · arreglar
`check-owned-paths.py` · features 023-025.
