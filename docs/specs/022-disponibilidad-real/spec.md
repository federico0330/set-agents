# 022 — Disponibilidad real: lo que hay ahora, sin configurar nada

- **Estado**: aprobado por Federico (2026-08-12) como parte del plan A→B→C.
  Pedido literal: *"que el harness tanto en opencode como en pi se dé cuenta de los modelos
  disponibles actualmente… si yo hoy pago copilot y en opencode vinculo la cuenta, el harness
  ya debe poder elegirlos sin configuración de por medio, lo mismo si yo doy de baja openai"*.
  Más el addendum: *"los agregados quiero poder administrarlos desde `set-agents`, sin tener
  que modificar ningún JSON"*.
- **Diseño**: producido por un Plan agent con los anclajes de tres exploraciones read-only.
- **ADRs**: 0042 (registro único + techo tri-estado + tres orígenes), 0043 (qué prueba
  realmente un probe).

## Objetivo

Que el harness sepa, **sin configuración previa y sin mentir**, qué proveedores y modelos están
disponibles *ahora* — incluidos los que el usuario da de alta o de baja después de instalar.

## Lo que YA funciona (no rehacerlo)

ADR-0034 cerró la auto-adopción: `discovered_providers = "auto"` resuelve el inventario
realmente probeado ∩ el set auditado, y el pool pasó de 6 rutas a 25. Una credencial nueva de
**opencode** se detecta al instante, porque su firma está en la clave del caché.

## Los cinco defectos que quedan, medidos

1. **El techo `[catalog]` hace obligatoria la configuración.** `_probe_pairs`
   (`catalog.py:467-469`) hace `if not allowed: continue`: un proveedor sin clave en
   `[catalog]` de `models.toml` **se saltea entero**. Hoy sumar un proveedor sí requiere
   editar config — exactamente lo que el pedido quiere eliminar.
2. **`models_listable` engaña.** Reporta listado ∩ techo curado, no lo que el proveedor expone.
3. **La baja es invisible hasta 300 s en 3 de 4 runtimes.** `_cache_key`
   (`catalog.py:351-365`) solo lleva firma de opencode. Y los roles de review retornan antes
   del re-probe (`service.py:429`), así que deciden con inventario stale.
4. **Hay dos cachés divergentes en disco.** `--route-doctor` inspecciona
   `STATE_DIR/probe-cache.json` y `--route-decide` usa `routing-v2/probe-cache.json`. El
   diagnóstico mira un archivo que el decisor no usa. Sin ADR, spec ni test que lo reconozca.
5. **Lo que el harness distribuye no se puede quitar.** `Global/_shared/opencode.json:5-23`
   trae un provider `ollama` hardcodeado apuntando a `http://localhost:11434/v1` con tres
   modelos fijos, que `install.py` escribe en el `opencode.json` de **todo** el que instale. Y
   `deep_merge` (`install.py:49-53`) sólo agrega: si el usuario lo borra, el próximo install se
   lo repone. La única salida hoy es editar el repo.

## Dos límites honestos, escritos y no disimulados

- **Copilot está bloqueado aguas arriba.** `opencode models github-copilot --pure` devuelve
  `Provider not found` **incluso con `--refresh`** (medido, `ADR-0034:20`). Esta feature no lo
  puede desbloquear. Lo que sí hace es que **el día que opencode lo exponga, no haga falta
  tocar código** — y corrige la afirmación de `ADR-0034:124-126` que decía eso y era inexacta:
  hoy harían falta entradas en cinco tablas.
- **pi descubre modelos, no credenciales.** No existe equivalente de `opencode auth list`;
  `pi_auth_provider_keys()` (`catalog.py:292-307`) sólo confirma claves ya conocidas, y sus dos
  proveedores ya están auditados por otros runtimes. **pi nunca puede aportar un proveedor
  nuevo**, y eso se declara en vez de insinuar lo contrario.

## Paquetes

Cinco, **serializados**: A2 y A3 tocan el mismo archivo y paralelizarlos garantiza conflicto.

### PKG-1 — `registro-de-proveedores`
- **AC-01**: un único `PROVIDERS: dict[str, ProviderSpec]` del que se **derivan**
  `_PAIR_COMMANDS`, `_OPENCODE_PROVIDER_KEYS`, `_OPENCODE_CLI_IDS`, `PROVIDER_BILLING_KIND`,
  `DISCOVERABLE_PROVIDERS`, el key-map de `_configured_models` y **`_MODEL_PREFERENCE_PROVIDERS`
  (`set_agents_app.py:94`)** — el sexto duplicado, que la primera versión de esta spec no
  nombraba (F4 del challenge). Sumar un proveedor pasa de **seis** entradas en lockstep manual
  a **una fila**.
  **Ojo con su test**: `tests/test_routing.py:3965` dice proteger ese literal pero lo compara
  contra **otro literal hardcodeado idéntico**, no contra `DISCOVERABLE_PROVIDERS`. Y el
  comentario de `set_agents_app.py:131-133` afirma lo contrario. Es exactamente el defecto que
  este paquete existe para eliminar, disfrazado de guarda: el test tiene que comparar contra la
  **fuente real**.
- **AC-02**: test de caracterización — las tablas derivadas son **byte-idénticas** a los
  literales de hoy. Este paquete no cambia comportamiento.
- **AC-03**: ADR-0042 corrige la afirmación de `ADR-0034:124-126` con la medición.

### PKG-2 — `techo-catalogo-tri-estado`
- **AC-04**: el tri-estado aplica **solo a `opencode_zen`, `opencode_go` y a proveedores
  futuros sin key dedicada** — decisión de Federico (2026-08-12), no re-litigable.
  `[catalog].claude` y `[catalog].codex` **siguen siendo listas obligatorias no vacías**, como
  hoy. Razón medida por el challenge (F1): `models_config.py:130-136` las exige con `die`,
  `load_roles` (`:352-357`) las indexa sin fallback, y son las **únicas con filas curadas** en
  `routes.v1.toml` — si pasaran a auto, cada fila curada existente dispararía el
  `CATALOG_CEILING_REQUIRED` de AC-06. `[catalog].codex_effort` queda **explícitamente fuera**:
  es una lista de efforts, no un techo de proveedor, y meterla en la redacción genérica
  "`<key>`" fue un error de la primera versión.
  Los tres estados: lista = techo curado, `[]` = veto, **ausente = auto**.
  **Del precedente de `[subscriptions]` (`models_config.py:361-382`) se toma la FORMA, no el
  manejo de error** (F1): allí "ausente" degrada a `WARN` y sigue, porque es validación de
  build; acá alimenta el filtrado en vivo del snapshot de ruteo, y AC-06 exige que el caso malo
  falle **fuerte y nombrado**. Importar la mansedumbre de subscriptions contradiría a AC-06. `_configured_models` se reemplaza por
  `resolve_ceiling(config, provider) -> ("curated", set) | ("auto", None) | ("veto", set())`,
  consumido por los **tres** sitios que hoy divergen: `_probe_pairs:467-469`,
  `_read_probe_cache:409` (que hoy re-intersecta y en modo auto dejaría el caché siempre vacío)
  y `build_snapshot:632-633,647`.
- **AC-05**: cuatro capas impiden que entre cualquier cosa, y cada una con su test: el par debe
  estar **auditado**; lo auto **nunca** entra al snapshot curado (sólo por la vía sintetizada,
  con `MODEL_METADATA_INFERRED`); billing desconocido ⇒ rank caro; y cap determinístico por
  proveedor + `[catalog].exclude` extendido a `provider:*`.
- **AC-06**: una fila curada de `routes.v1.toml` que apunte a un proveedor en auto/veto falla
  **fuerte y nombrada** (`CATALOG_CEILING_REQUIRED`), no con el genérico `CATALOG_INVALID`.

### PKG-3 — `liveness-real`
- **AC-07**: el de-auth se cierra **en la clave de caché, no con más subprocesos**: firma de
  credencial por runtime, toda `stat`/lectura local — codex (`~/.codex/auth.json`), claude-code
  (`~/.claude/.credentials.json`), pi (`pi_auth_provider_keys()` + `PI_PINNED_VERSION`),
  opencode (lo de hoy + mtime de los binarios `codex` y `claude`).
- **AC-08**: **las dos propiedades que hacen o rompen esto**, cada una con su test:
  *refresh de token* (cambia sólo token/expiry) ⇒ la firma **no** cambia y el caché sirve; y
  *logout / credencial borrada* ⇒ la firma **sí** cambia ⇒ probe fresco. Sin la primera,
  Claude Code renueva OAuth y probeás en cada decisión, hasta 60 s en pi
  (`PI_PROBE_MIN_TIMEOUT_SECONDS`).
- **AC-09**: la firma se compone de **presencia e identidad de credencial, nunca material y
  nunca campos que rotan**, hasheada, jamás logueada ni en el envelope — misma disciplina que
  `pi_auth_provider_keys`. Bump de `_CACHE_SCHEMA_VERSION` con su test: hoy no existe ninguno.
  **Límite estructural de claude-code, aceptado por Federico y a documentar en ADR-0043** (F2):
  `~/.claude/.credentials.json` **no tiene ningún campo de identidad de cuenta** — codex sí
  (`tokens.account_id`), y los únicos campos no-rotantes de claude (`scopes`,
  `subscriptionType`, `rateLimitTier`) no identifican una cuenta. Así que para claude-code la
  firma detecta **presencia y ausencia** (logout, credencial borrada, archivo ausente) pero
  **no** un cambio de una cuenta a otra del mismo plan sin pasar por logout. Detectarlo exigiría
  hashear el `refreshToken`, que esta feature **no** hace. El límite se declara; no se disimula.
  **Supuesto a validar temprano en este paquete, no de memoria** (F2): que `refreshToken`,
  `scopes` y `subscriptionType` efectivamente no roten en un refresh normal. Captura A/B del
  archivo antes y después de un refresh real; si rotan, la firma de claude-code hay que
  rediseñarla.
- **AC-10**: **una sola caché**, en la raíz del store (`store.py:326-334`), que ya tiene la
  disciplina de directorio privado y es la que usa la vía de decisión. Migran
  `set_agents_app.py:144,497,843,3133` y `models_config.py:258-259,277-278`. La legada se poda
  **con las mismas validaciones de seguridad** que `_write_probe_cache`.

### PKG-4 — `proveedores-del-usuario`
- **AC-11**: `~/.local/state/set-agentes/providers.toml` (precedente: `model-preference.toml`),
  con `origin` por entrada: `harness`, `discovered`, `user`. Los tres orígenes dejan de estar
  aplanados.
- **AC-12**: comandos `--provider-list|add|remove|verify`, sin tocar JSON a mano. El wizard de
  `setup_models.py` no se toca: remapea modelos de `models.toml`, es otra cosa.
- **AC-13**: el bloque `provider` de `opencode.json` pasa a **renderizarse** desde el registro,
  no a estar hardcodeado en `Global/_shared/opencode.json:5-23`. **Es lo que hace que quitar
  funcione.**
- **AC-14**: la poda por manifiesto se extiende de archivos a **subárboles JSON**
  (`opencode.json#/provider/ollama`), y **jamás** toca una clave que el harness no puso. Test
  obligatorio: un provider agregado a mano por el usuario sobrevive intacto a un install que
  poda otro.
- **AC-15**: siembra migratoria desde el `opencode.json` vivo que registra **todo** lo que haya
  bajo `provider.*` — decisión de Federico (F3): lo del harness como `origin=harness-legacy` y
  **cualquier provider que el usuario haya agregado a mano como `origin=user`**. Desde el primer
  arranque se puede listar, verificar y quitar desde `set-agents`, que es el pedido literal.
  La alternativa —registrar solo lo que el harness reconoce— dejaba invisibles los providers
  propios de quien ya tenía el harness instalado, que es el caso más probable.
  **A nadie le desaparece nada**: el registro declara qué hay y de dónde vino, nunca borra.

### PKG-5 — `altas-y-bajas-automaticas`
- **AC-16**: para cada credencial `detected_unlistable` que `route_doctor` ya reporta, se
  intenta una **verificación empírica** con candidatos derivados **sólo del nombre de la
  credencial autenticada** (exacto; espacio→guion). El id se acepta **únicamente si el CLI
  contestó bien**: listado con prefijo `<id>/<model>` bien formado, parseado por
  `_parse_opencode_models`. No es heurística que adivina: es medición que confirma.
- **AC-17**: la baja es **simétrica y automática**. El registro es *memoria del CLI id*, nunca
  una autorización: la ruteabilidad siempre exige probe vivo. Con AC-07, se nota en la decisión
  siguiente.
- **AC-18**: `--provider-verify` para modelos declarados que ya no responden (el caso Ollama):
  `GET {baseURL}/models`, timeout 2 s, sólo providers `user`. Reporta
  `alive | dead | unreachable` —nunca "no existe" cuando fue "no contestó"— con el timestamp de
  la medición, y ofrece `--prune-dead`. **Nunca** dentro de `route()`, **nunca** en la clave de
  caché, **nunca** en el spawn.
- **AC-19**: la separación `listed_by_provider` / `usable_after_ceiling` va en **las tres
  superficies que muestran "qué proveedores hay"**, no solo en `--route-doctor` (F5):
  `route_doctor` (`catalog.py:714-793`), `cmd_doctor_all` (`set_agents_app.py:849`) y
  **`_estado_general_lines` (`:3134`)**. Esa última es el panel del **primer ítem del menú**, o
  sea la vidriera: es donde un usuario no técnico va a mirar "¿el harness ya ve mi suscripción
  nueva?". Hoy las tres imprimen `len(models)` post-techo y se leen como "lo que el proveedor
  expone". El defecto de invisibilidad total se arregla gratis en las tres porque comparten
  `_probe_pairs`; el de la etiqueta engañosa hay que arreglarlo en cada una.

## No-goals

- No se toca el sort key (`service.py:382`) ni se le agrega un factor. El consumo es 023.
- No se agregan filas curadas a `routes.v1.toml` para proveedores nuevos, Copilot incluido:
  entran por la vía sintetizada o no entran.
- No se probea dentro de `route()`, por decisión ni por spawn.
- No se inventan CLI ids ni se derivan por regla.
- No se edita ADR-0034 retroactivamente: se supersede en parte y `docs/adr/README.md` marca la
  relación.
- No se convierte a pi en descubridor de credenciales: se declara el límite.

## Riesgos

1. **El techo auto infla el pool** (60 modelos zen sintetizados) → sort más lento. Mitigación:
   cap por proveedor, `is_inferred` ya penaliza, y medir p50/p90 antes y después.
2. **La firma rota en cada refresh** → probe en cada decisión, hasta 60 s en pi. Mitigación: la
   firma excluye campos que rotan, y el test de propiedad refresh-vs-logout es obligatorio.
3. **Leer archivos de credencial es superficie sensible nueva.** Mitigación: misma disciplina
   que `pi_auth_provider_keys` — lstat, regular, uid propio, sólo nombres, hash antes de
   guardar, nunca en log ni envelope.
4. **La poda de subárboles JSON borra una clave del usuario.** Mitigación: sólo ids registrados
   en el manifiesto, con test de un provider hecho a mano presente.
5. **Sacar Ollama de `_shared` le rompe el flujo a alguien.** Mitigación: siembra migratoria +
   `--provider-add` lo restituye en un comando.

## Gates

Por paquete: `python3 -m unittest discover -s tests` en verde (**`pytest` no está instalado**),
`./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` (semántica de ADR-0041), ACs
con evidencia `file:line`. Review independiente **en encargos chicos** — cuatro reviews grandes
murieron por stall en 021 y los de tres puntos completaron.

## Criterio de cierre

Desvincular una credencial y que la **decisión siguiente** ya no la ofrezca (hoy tarda hasta
300 s en 3 de 4 runtimes). Agregar un proveedor propio desde `set-agents`, usarlo, **quitarlo**,
y que un install posterior **no lo reponga**. Y `--route-doctor` reportando sobre la caché que
el decisor realmente usa.
