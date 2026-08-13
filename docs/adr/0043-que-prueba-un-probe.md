# ADR-0043 — Qué prueba realmente un probe; firma de credencial por runtime; una sola caché

- Estado: Accepted (2026-08-13). Feature 022-disponibilidad-real, PKG-3 (`P3-liveness-real`).
  Depende de ADR-0042 (PKG-1/PKG-2, ya aceptado). No supersede nada.

## Contexto

Medición en vivo sobre el estado del repo antes de este paquete (`grep -rn`/lectura directa,
`docs/specs/022-disponibilidad-real/evidence/P3-implementer.md` tiene el detalle mordido):

1. **`_cache_key`** (`routing_core/catalog.py`, antes de este paquete) solo llevaba firma de
   credencial de **opencode** (`_live_opencode_auth_signature`, un subprocess de
   `opencode auth list --pure`, más `_opencode_binary_signature`, path+mtime del binario
   `opencode`). Dar de baja una credencial en **codex**, **claude-code** o **pi** era invisible
   hasta que `PROBE_CACHE_TTL` (300s) expiraba — 3 de 4 runtimes.
2. **Dos cachés divergentes en disco, confirmado en vivo**: `--route-doctor` inspeccionaba
   `STATE_DIR/probe-cache.json` (`~/.local/state/set-agentes/probe-cache.json`) mientras que la
   vía de decisión real (`RoutingService.__init__`, vía `RoutingStore.ensure_cache_root()`)
   lee/escribe `~/.local/state/set-agentes/routing-v2/probe-cache.json`. Mismo defecto,
   duplicado además en `set_agents_app.py` (cuatro sitios) y `models_config.py` (dos sitios).
3. **El probe responde una pregunta distinta de la que parece responder.** Medido en vivo:
   `opencode auth list --pure` reporta la credencial OpenAI presente, `opencode models
   openai --pure` lista modelos sin error, `--route-doctor` reporta `authenticated=true,
   models_listable=6` — y la inferencia real por ese mismo par devuelve `Error: Provided
   authentication token is expired.` El probe prueba **presencia de credencial**, no
   **liveness**. Resolver esto (que un CLI acepte listar con un token vencido) es P5
   (AC-16/AC-18), fuera de alcance de este paquete — pero el nombre no debe mentir sobre lo
   que mide.
4. **Los mismos campos, dos runtimes, dos respuestas.** `codex login status` reporta
   `Logged in using ChatGPT` y `codex exec` funciona (PONG real) con la MISMA cuenta que
   opencode reporta vencida. Cada runtime tiene su propio store de credenciales — valida
   empíricamente que la firma tiene que ser **por runtime**, no un booleano global: una firma
   global daría la respuesta equivocada en 3 de 4 casos.
5. **Las credenciales, medidas (campos solamente, nunca valores)**:
   - `~/.codex/auth.json`: `auth_mode`, `OPENAI_API_KEY`, `tokens.{id_token, access_token,
     refresh_token, account_id}`, `last_refresh`. `tokens.account_id` es identidad de cuenta
     real (una fila estable de la base de ChatGPT). `last_refresh` y los tres campos de
     `tokens` que no son `account_id` **rotan** en cada refresh (medido: nombre del campo, no
     su valor — el propio nombre `last_refresh` ya es evidencia de que el archivo se
     reescribe periódicamente).
   - `~/.claude/.credentials.json`: `claudeAiOauth.{accessToken, expiresAt, rateLimitTier,
     refreshToken, refreshTokenExpiresAt, scopes, subscriptionType}` **y**, en el MISMO
     archivo, `mcpOAuth.{...}` — hoy una credencial de un MCP de Vercel, sin relación alguna
     con el proveedor Claude Code. Una firma ingenua ("hasheo el archivo entero" o "uso su
     mtime") rota en cada refresh de ESE MCP, no solo de la credencial que importa — la
     trampa medida y nombrada explícitamente en el context pack de este paquete.
   - `~/.pi/agent/auth.json`: ya cubierto, sin subprocess, por `pi_auth_provider_keys()`
     (spike Q2, 012) — un `frozenset` de nombres de proveedor, nunca valores.

## Decisión

### 1. Un probe prueba presencia de credencial, no liveness — se declara con esas palabras

`route_doctor`, los docstrings de `probe_inventory`/`_probe_pairs` y esta ADR usan
"credential presence" o su equivalente en español, nunca "liveness" ni "disponibilidad real
del modelo". Resolver la brecha entre "el CLI lista sin error" y "el proveedor responde de
verdad" es AC-16/AC-18 (P5) — este paquete no la resuelve, la nombra correctamente.

### 2. Firma de credencial por runtime, toda `stat`/lectura local, cero subprocesos nuevos

`_cache_key` pasa de una sola firma (opencode) a seis fuentes nuevas, todas locales:

- **`_binary_signature(name)`** (generaliza `_opencode_binary_signature`, ADR-0034 AC-08):
  path+mtime de `opencode`, `codex` y `claude` en PATH — un swap de binario invalida la
  caché sin bump manual, ahora para los tres CLIs, no solo opencode.
- **`_codex_auth_signature()`**: `~/.codex/auth.json`, SOLO `tokens.account_id` (identidad
  real) y si `OPENAI_API_KEY` está presente (booleano, nunca el valor). Nunca
  `access_token`/`refresh_token`/`id_token`/`last_refresh`.
- **`_claude_code_auth_signature()`**: `~/.claude/.credentials.json`, SOLO
  `claudeAiOauth.{scopes, subscriptionType, rateLimitTier}` — nunca `accessToken`/
  `refreshToken`/`expiresAt`/`refreshTokenExpiresAt`, y nunca el archivo completo ni su
  mtime (la trampa de `mcpOAuth` de arriba).
- **`_pi_auth_signature()`**: `pi_auth_provider_keys()` (sin cambios) + `PI_PINNED_VERSION`
  — un cambio de versión pineada también invalida, porque un release distinto de pi puede
  leer/escribir un `auth.json` con forma distinta.

Cada valor se hashea (`sha256`) antes de plegarse en `_cache_key` — nunca se loguea, nunca
viaja en un envelope, nunca es el valor crudo de una credencial. Disciplina idéntica a
`pi_auth_provider_keys` (`lstat`, nunca symlink, archivo regular, uid propio; cualquier
sorpresa es fail-closed a la firma vacía, que nunca iguala a una firma real — cache miss,
nunca un match fabricado).

`_cache_key` sigue siendo una función pura sin I/O más allá de `stat`/lectura local — cero
subprocesos nuevos, medido y probado
(`test_adr0043_ac07_cache_key_never_spawns_a_subprocess_for_the_new_signatures`,
`tests/test_routing.py`). El único subprocess de toda la composición de la clave sigue siendo
`_live_opencode_auth_signature`, provisto por el LLAMADOR (`probe_inventory`) como
`auth_signature`, nunca invocado desde `_cache_key` mismo.

La clave es **una sola** para todo el documento de caché (que cubre los pares de los cuatro
runtimes a la vez) — un cambio de credencial en CUALQUIER runtime invalida el documento
entero, forzando un re-probe completo en la siguiente decisión. Es la superficie mínima que
cierra el defecto sin introducir invalidación parcial (que exigiría rediseñar el formato del
documento, fuera de alcance).

### 3. Límite estructural de claude-code — aceptado por Federico, declarado, no disimulado

`~/.claude/.credentials.json` **no tiene ningún campo de identidad de cuenta** — a diferencia
de codex (`tokens.account_id`). Los únicos campos no-rotantes medidos (`scopes`,
`subscriptionType`, `rateLimitTier`) son atributos del *grant*/plan OAuth (qué puede hacer
esta cuenta, qué plan paga), no un identificador de cuenta. Consecuencia declarada: la firma
de claude-code detecta **presencia y ausencia** (logout, borrado de credencial, archivo
ausente) pero **no** un cambio de una cuenta a otra del mismo plan sin pasar por un logout
intermedio. Cerrar esa brecha exigiría hashear `refreshToken` — **esta feature no lo hace**
(AC-09 es explícito: "hashear el refreshToken no se hace"). El límite queda escrito acá y no
se maquilla como si la firma detectara más de lo que detecta.

### 4. Supuesto validado — con las salvedades de seguridad que impusieron el método

El diseño de arriba depende de que `scopes`/`subscriptionType`/`rateLimitTier`
(claude-code) y `tokens.account_id` (codex) NO roten en un refresh normal. Medición en vivo
de la FORMA de ambos archivos, hecha en esta sesión (nombres de campo solamente, nunca
valores — ver evidencia): confirma exactamente los campos que el context pack anticipaba,
incluida la presencia real de `mcpOAuth` (hoy un token de Vercel) en el mismo archivo que
`claudeAiOauth`.

**No se forzó un refresh real contra el backend OAuth** (ni siquiera con `HOME` desviado a
una copia aislada) para capturar un A/B de valores antes/después: muchos proveedores OAuth
rotan el `refresh_token` del lado del servidor en cada uso (single-use rotating refresh
tokens); forzar un refresh con el `refresh_token` REAL — aunque el resultado se escriba solo
en una copia — puede invalidar del lado del servidor el `refresh_token` que sigue viviendo en
el archivo real, dejando al usuario sin sesión válida. Es el mismo riesgo, con la misma
severidad, que la instrucción explícita de no correr un `logout` real — tratado con la misma
disciplina aunque no esté nombrado literalmente. **Queda marcado "sin verificar mediante
refresh forzado en vivo"**, explícitamente, en vez de simulado como certeza.

El diseño es robusto a esa incertidumbre por construcción: la firma de claude-code nunca lee
`refreshToken`/`accessToken` (así que si esos SÍ rotan, es irrelevante), y los tres campos que
sí lee son, por semántica de OAuth, atributos del grant, no del token — un argumento de diseño
explícito, marcado como tal y no como medición. Si una medición futura contradice este
argumento, el diseño de la firma de claude-code se revisa (mismo texto de advertencia que el
context pack de PKG-3 ya dejó escrito).

### 5. Una sola caché — la raíz del store, la legada se poda con la misma disciplina de seguridad

`RoutingStore.root` (`store.py`, `~/.local/state/set-agentes/routing-v2`) es la única raíz de
caché de probes desde este paquete. Los seis sitios que antes pasaban
`cache_root=STATE_DIR` (o el equivalente `Path.home() / ".local/state/set-agentes"` en
`models_config.py`) migran a `_probe_cache_root()` — un helper por módulo que expone
`RoutingStore().root` (atributo puro, sin I/O al construirse, misma pereza que `STATE_DIR`
siempre tuvo) para no crear directorios como efecto secundario de una lectura diagnóstica.
`route_doctor`, `--doctor-all` y el panel "Estado general" (las tres superficies "vidriera"
que un humano corre para ver qué detecta el harness) además podan, con el mismo esfuerzo
best-effort, el archivo legado sobreviviente (`prune_legacy_probe_cache`, misma disciplina de
`_validate_cache_dir` que `_write_probe_cache` ya usaba: directorio 0700 de este uid, sin
symlink; archivo regular de este uid, sin symlink — cualquier sorpresa deja el archivo
intacto, nunca se borra a ciegas). Nunca toca el directorio `STATE_DIR` en sí (que también
aloja `config.toml`/`model-preference.toml`/etc.), solo el archivo `probe-cache.json` legado.

### 6. `_CACHE_SCHEMA_VERSION` 2 → 3, con test — no existía ninguno antes

Bump porque la SEMÁNTICA de la clave cambió (seis fuentes nuevas), aunque la forma del
documento persistido (`{"key", "at", "pairs"}`) no se movió — el propio docstring de
`_CACHE_SCHEMA_VERSION` ya distinguía "content shape" de "key semantics" y este bump cae en
la segunda categoría. Antes de este paquete no existía ningún test que probara que un bump
invalida una caché escrita bajo la versión anterior; ahora sí
(`test_adr0043_ac09_cache_schema_version_bump_invalidates_old_cache_documents`).

### 7. `pi` descubre modelos, no credenciales — reafirmado, no reabierto

Sin cambios de este paquete: `pi_auth_provider_keys()` solo confirma claves YA conocidas por
otros runtimes (sus dos proveedores, `openai-codex`/`anthropic`, ya están auditados por
codex/claude-code) — pi nunca puede aportar un proveedor nuevo al inventario. `_pi_auth_
signature()` (arriba) reutiliza esa misma función sin ampliar lo que lee.

## Alternativas rechazadas

- **Hashear `refreshToken` de claude-code para recuperar identidad de cuenta**: rechazado —
  AC-09 lo prohíbe explícitamente (`refreshToken` es material de credencial, no un
  identificador estable; rota, y hashear un secreto rotante que además es la llave para
  obtener un `accessToken` nuevo amplía la superficie sensible sin necesidad).
- **Hashear el archivo `~/.claude/.credentials.json` completo, o usar su mtime**: rechazado
  por la trampa medida de `mcpOAuth` — rotaría en cada refresh de un MCP sin relación,
  anulando la caché en cada decisión por una razón ajena a la credencial del proveedor.
- **Forzar un refresh real (incluso sandboxed vía `HOME`) para la captura A/B**: rechazado por
  el riesgo de rotación de `refresh_token` del lado del servidor invalidando la sesión real
  del usuario — mismo nivel de severidad que un `logout` real, tratado igual aunque la
  consigna no lo nombrara literalmente.
- **Leer el propio `~/.local/share/opencode/auth.json` de opencode para eliminar su
  subprocess** (mejora nombrada como opcional en el context pack): rechazada para este
  paquete — reimplementar la normalización que `opencode auth list --pure` ya hace (mapeo de
  nombres de proveedor, distinción `●`/`○` pendiente-vs-confirmado) sobre un formato de
  archivo no documentado reabre el mismo riesgo de parseo no verificado que ADR-0034 M-1 ya
  evita para los CLI ids — y el subprocess existente ya es el único de toda la composición de
  la clave, no el problema que este paquete existe para resolver. Queda declarada, no tomada.
- **Un solo booleano de credencial por runtime, sin distinguir identidad**: rechazado por la
  medición del punto 4 del Contexto — una firma que solo mira "¿hay algo logueado?" no
  distinguiría un cambio de cuenta de codex (que sí tiene `account_id`) de una simple
  presencia, perdiendo la única señal de identidad real que un runtime SÍ ofrece.
- **Invalidación parcial por runtime (una sub-clave por par en vez de una clave global)**:
  rechazado por alcance — exigiría rediseñar el formato del documento persistido
  (`{"key", "at", "pairs"}`), y un re-probe completo tras CUALQUIER cambio de credencial ya
  cierra el defecto medido (300s → inmediato) sin ese costo de diseño.

## Consecuencias

- Dar de baja (o dar de alta) una credencial en cualquiera de los cuatro runtimes se nota en
  la decisión siguiente, no hasta 300s después — el criterio de cierre de la spec 022 para
  este paquete.
- `--route-doctor` reporta sobre la MISMA caché que la vía de decisión usa; el archivo legado
  se poda solo, sin intervención manual, con la disciplina de seguridad ya establecida.
- El límite de identidad de claude-code queda escrito y es parte del contrato, no una
  sorpresa futura.
- La palabra "liveness" en el nombre de este paquete (`P3-liveness-real`) queda corregida por
  esta ADR: lo que se cierra es presencia de credencial por runtime, no verificación de que el
  proveedor responda — eso sigue siendo P5.

## Extensión (022 PKG-5, `P5-altas-y-bajas-automaticas`) — AC-16..AC-19

Este paquete es exactamente el "eso sigue siendo P5" nombrado arriba. Extiende esta ADR (no la
supersede, no crea una nueva) con la verificación empírica de credenciales `detected_unlistable`
y con la separación `listed_by_provider`/`usable_after_ceiling`.

### AC-16/AC-17 — verificación empírica, memoria de CLI id, nunca autorización

Para cada credencial `detected_unlistable` que `route_doctor` ya reportaba (M-1, ADR-0034), se
deriva UN candidato — transformación exacta del nombre mostrado por `opencode auth list --pure`,
espacio→guion (`_unlistable_candidate_id`, `catalog.py`) — y se intenta UNA verificación empírica
(`_verify_unlistable_credential`): `opencode models <candidato> --pure`, aceptado únicamente si el
CLI contesta con un listado bien formado `<candidato>/<modelo>`, parseado por
`_parse_opencode_models` (el mismo parser que ya usan los cuatro pares auditados — cero parseo
nuevo). Cualquier sorpresa — binario ausente, timeout, código de salida no-cero, una línea `Error`,
un prefijo mal formado, o un listado vacío — es `None`, fail-closed: no se acepta nada, nunca una
adivinanza parcial.

Medido en vivo esta noche (evidencia P5): `opencode models github-copilot --pure` responde
`Provider not found` incluso con `--refresh` — el candidato se propone, el CLI no lo confirma, no
se acepta nada. Es exactamente el caso que motiva la regla: ADR-0034 (arriba) ya midió que la
misma transformación espacio→guion da el id EQUIVOCADO para `opencode-zen` (CLI id real:
`opencode`) — por eso el candidato nunca se confía solo, siempre se mide.

**El resultado es memoria del CLI id, nunca una autorización.** `_verify_unlistable_credential` es
consumido ÚNICAMENTE por `route_doctor` — nunca se pliega en `_PAIR_COMMANDS`, `_probe_pairs`,
`resolve_discovered_providers`, ni ninguna otra estructura que `service.route()` lea. Un candidato
confirmado eleva `listed_by_provider` en el reporte diagnóstico y nada más:
`usable_after_ceiling` queda en 0 para estos entries siempre, porque no existe un par auditado ni
un techo curado contra el cual esa credencial pueda ser ruteable. Esto es deliberado y está
probado: `test_adr0034_m1_github_copilot_never_gets_an_audited_pair_even_authenticated`
(`tests/test_routing.py`, paquete P1-P4, ya aceptado) sigue pasando sin tocarlo — un candidato
confirmado en `route_doctor` no cambia en absoluto lo que `resolve_discovered_providers` deriva.

La baja es simétrica y automática **sin código nuevo**: `route_doctor` nunca persiste este
resultado (ni en disco, ni en la caché de probes) — cada llamada repite la medición desde cero, así
que si el candidato deja de contestar, la SIGUIENTE llamada ya lo reporta sin verificar de nuevo,
exactamente igual que lo reportaría si nunca hubiera contestado. No hay "registro" que dar de baja
porque nunca hubo un registro persistente que dar de alta — la única memoria es la del reporte de
la corrida actual.

### AC-18 — `--provider-verify` mide liveness real, alcance explícito sobre el caso Ollama/P4

`--provider-verify` (P4, AC-12) pasa a intentar, además del chequeo de forma ya existente, un `GET
{baseURL}/models` real con timeout 2s (`_provider_liveness`, `set_agents_app.py`) — **solo para
entries cuyo `origin` esté en alcance**. El texto de la spec es literal: "sólo providers user", así
que el alcance POR DEFECTO es exactamente `{"user"}`, no re-litigable.

Reporta `alive` (el server contestó, cualquier status HTTP — hasta un 404 prueba que algo está
escuchando), `dead` (conexión rechazada — nada escucha en ese puerto, el caso Ollama medido:
`curl http://localhost:11434/v1/models` → `000`, `ConnectionRefusedError` en Python) o
`unreachable` (timeout, fallo de DNS, o cualquier otra sorpresa de red — indeterminado, NUNCA
reportado como `dead`: "nunca 'no existe' cuando fue 'no contestó'"). El timestamp de la medición
viaja en cada línea (`at=<ISO-8601 UTC>`).

**La interacción con P4, resuelta explícitamente, no implícita**: después de P4, el bloque
`ollama` real de esta máquina quedó `origin=harness-legacy` (`seed_or_migrate` lo etiqueta así
porque su valor es byte-idéntico al `HARNESS_PROVIDER_SEED` que el harness distribuye) — nunca
`user`. Si `--provider-verify` mirara only `user` sin más, el caso real de Federico (el endpoint de
Ollama muerto) quedaría estructuralmente afuera del chequeo de liveness, sin que nadie lo
mencionara. Se eligió AMPLIAR CON ARGUMENTO (`--include-legacy`) en vez de forzar
`--provider-remove`+`--provider-add` como único camino: el default sigue siendo exactamente `user`
(la letra de AC-18, intacta), y `--include-legacy` suma `harness-legacy` al alcance de forma
explícita y documentada (`_LIVENESS_DEFAULT_ORIGINS`/`_LIVENESS_WITH_LEGACY_ORIGINS`,
`set_agents_app.py`). Un `--provider-remove ollama` seguido de `--provider-add` sigue siendo un
camino válido (convierte el bloque a `origin=user`, dentro del default) pero ya no es el ÚNICO.

`--prune-dead` (opt-in, nunca automático) saca de `providers.toml` únicamente los ids que ESA
corrida midió `dead` — nunca `unreachable` (no es evidencia de ausencia) y nunca un entry
shape-inválido (nunca se le intentó liveness). Misma disciplina que `--provider-remove`: el efecto
real en `opencode.json` espera al próximo `./build.sh --install`, nunca lo escribe esta llamada.

**Nunca dentro de `route()`, nunca en la clave de caché (`_cache_key`), nunca en el spawn**: la
única función que llama `_provider_liveness` es `cmd_provider_verify`, y la única función que llama
`_verify_unlistable_credential`/`_unlistable_candidate_id` es `route_doctor` — ninguna de las dos
cadenas de llamadas toca `routing_core/service.py`, `catalog._cache_key`, ni ningún `*_spawn.py`
(ver `tests/test_provider_registry.py::LivenessNeverInHotPathTests`, grep-tripwire explícito).

### AC-19 — `listed_by_provider`/`usable_after_ceiling` en las tres superficies

`route_doctor` (`catalog.py`), `cmd_doctor_all` y `_estado_general_lines` (`set_agents_app.py`)
imprimían `len(models)` sobre el resultado YA intersectado con el techo curado (`_probe_pairs`) y
lo etiquetaban de una forma que se leía como "lo que el proveedor expone" — exactamente el defecto
medido en vivo esta noche: `opencode-zen` lista 58 modelos, el techo curado de `models.toml` no
coincide 1:1, y las tres superficies mentían por omisión sobre esa diferencia.

`_probe_pairs` gana un canal lateral opcional, `listed_out` (nunca cambia su valor de retorno ni
el comportamiento de ningún llamador existente que no lo pase): captura el listado CRUDO,
pre-techo, para cada par OpenCode que efectivamente probeó, ANTES de intersectarlo con el techo
curado. `probe_inventory` lo reenvía solo por la rama `pairs=` (siempre fresca, nunca cacheada —
la única rama donde el dato es honesto; la caché en disco nunca guardó el crudo, solo el
post-techo, y no se le agrega ese campo en este paquete: `_CACHE_SCHEMA_VERSION` se queda en 3).

`route_doctor` ya usaba esa rama para su propio listado (siempre fresco), así que sumar
`listed_out` ahí es directo. `cmd_doctor_all`/`_estado_general_lines` usaban la ruta CACHEADA por
rendimiento/consistencia con la vía de decisión real — ahí se agrega `probe_listed_and_usable`
(`catalog.py`): reusa esa misma llamada cacheada para `usable_after_ceiling`, y suma un
re-probe SIEMPRE FRESCO pero acotado a los pares OpenCode (nunca codex/claude-code/pi — `pi` sola
tiene un piso de 60s en frío, `PI_PROBE_MIN_TIMEOUT_SECONDS`, y re-probarla en cada render del
menú habría hecho lenta justo la superficie "vidriera" que esta AC existe para arreglar) para
`listed_by_provider`. Para codex/claude-code/pi, que nunca exponen un listado en vivo distinto de
su techo curado (`_PAIR_COMMANDS` solo les audita un booleano de login), `listed_by_provider`
coincide con `usable_after_ceiling` por construcción — nunca una medición fabricada, la ausencia
de una señal separada declarada tal cual es.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P3-implementer.md` (PKG-3, AC-07..09) y
`docs/specs/022-disponibilidad-real/evidence/P5-implementer.md` (PKG-5, AC-16..19, esta extensión).
