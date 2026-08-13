# Context pack — P5-altas-y-bajas-automaticas

Spec: `docs/specs/022-disponibilidad-real/spec.md`, **AC-16..AC-19**. Último paquete de 022.
Depende de **P4**. Cierra el pedido original: *"si yo hoy pago copilot y en opencode vinculo la
cuenta, el harness ya debe poder elegirlos sin configuración de por medio"*.

**Contexto humano que importa**: Federico suma las suscripciones de **opencode-go y Copilot** hoy a
la mañana. Este paquete es el que decide si el harness se entera solo.

## Evidencia en vivo de esta noche. Es tu caso de prueba, no una hipótesis.

Salida literal de `--route-doctor` medida hoy:

```
anthropic     runtime=opencode authenticated=false billing=subscription models_listable=0
openai-codex  runtime=opencode authenticated=true  billing=subscription models_listable=6
opencode-go   runtime=opencode authenticated=true  billing=subscription models_listable=18
opencode-zen  runtime=opencode authenticated=true  billing=metered      models_listable=58
github copilot runtime=opencode authenticated=true billing=unknown      models_listable=0  detected_unlistable=true
```

Tres cosas que salen de ahí y mandan sobre tu diseño:

### 1. Copilot ya está autenticado y sigue sin listar

`opencode models github-copilot --pure` responde `Provider not found`, **incluso con `--refresh`**.
Es el caso exacto de AC-16: credencial detectada, sin CLI id verificable. **No podés desbloquearlo
vos** — lo que hacés es que el día que opencode lo exponga, funcione sin tocar código.

### 2. La heurística del nombre es una trampa, y ya hay un muerto

AC-16 permite derivar candidatos **sólo del nombre de la credencial** (exacto; espacio→guion). Pero
`ADR-0034` (`catalog.py:132-140`) advierte, medido: esa regla *"would have produced the WRONG id
for `opencode-go` itself — `opencode go` → `opencode-go` only works by coincidence"*. Y de hecho el
CLI id de **opencode-zen** es `opencode`, no `opencode-zen`: la regla falla ahí.

Por eso AC-16 dice **el id se acepta ÚNICAMENTE si el CLI contestó bien**: listado con prefijo
`<id>/<model>` bien formado, parseado por `_parse_opencode_models`. **No es heurística que adivina,
es medición que confirma.** Si el CLI no contesta, no se agrega nada. Fail-closed.

### 3. Listable ≠ usable, medido esta noche

`openai-codex` figura `authenticated=true, models_listable=6` y su **inferencia real** devolvió
`Error: Provided authentication token is expired.` El probe pregunta *"¿podés listar?"* y de ahí se
concluye *"está vivo"*. **Son preguntas distintas.** Esto es insumo directo de AC-19: la etiqueta
tiene que decir qué se midió, no insinuar más.

## AC-18 — el caso Ollama, con el endpoint ya muerto

Medido: `curl http://localhost:11434/v1/models` → **`000`, sin respuesta**. El provider `ollama` con
sus tres modelos está declarado y no contesta.

`--provider-verify`: `GET {baseURL}/models`, timeout 2 s, **sólo providers `user`**. Reporta
`alive | dead | unreachable` —**nunca "no existe" cuando fue "no contestó"**— con el timestamp de la
medición, y ofrece `--prune-dead`.

**Nunca** dentro de `route()`, **nunca** en la clave de caché, **nunca** en el spawn. Un `GET` con
timeout metido en el camino de decisión es exactamente el tipo de cosa que después nadie encuentra.

Ojo con la interacción con P4: después de P4 el bloque `ollama` es `origin=harness-legacy`, no
`user`. Si `--provider-verify` sólo mira `user`, **el caso Ollama real de Federico queda afuera**.
Resolvelo explícitamente y decilo: o ampliás el alcance a `harness-legacy` con argumento, o
documentás que ese bloque se quita con `--provider-remove` (P4) y no con `verify`. **No lo dejes
implícito.**

## AC-17 — la simetría, y qué NO es el registro

La baja es automática y simétrica al alta. **El registro es memoria del CLI id, nunca una
autorización**: la ruteabilidad siempre exige probe vivo. Con las firmas de P3, la baja se nota en
la decisión siguiente en vez de hasta 300 s después.

## AC-19 — las TRES superficies, no una

| Superficie | Dónde | Por qué importa |
|---|---|---|
| `route_doctor` | `catalog.py:1027`, imprime en `:1065,1075` | diagnóstico |
| `cmd_doctor_all` | `set_agents_app.py:863` | |
| `_estado_general_lines` | `set_agents_app.py:3162` | **el primer ítem del menú: la vidriera** |

Las tres imprimen `len(models)` **post-techo** y se leen como "lo que el proveedor expone". Hay que
separar `listed_by_provider` de `usable_after_ceiling`.

`_estado_general_lines` es donde un usuario no técnico va a mirar *"¿el harness ya ve mi suscripción
nueva?"*. **Si arreglás sólo `--route-doctor`, no arreglaste lo que la gente mira.**

## Restricciones

- **ADR-0043** ya existe (P3): extendelo con la verificación empírica, no crees uno nuevo.
- **No inventes CLI ids ni los derives por regla.** Sólo se acepta lo que el CLI confirmó.
- **No agregues filas curadas a `routes.v1.toml`** para proveedores nuevos, Copilot incluido: entran
  por la vía sintetizada o no entran.
- **No probees dentro de `route()`.** Ni el verify, ni el alta, ni la baja.
- **No toques el sort key.** El consumo es 023.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques las credenciales ni los configs reales de Federico.** Fixtures y `HOME` de prueba.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh`
→ `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` ·
`git diff --check` limpio.

**Corré los comandos largos exactamente así:**

```
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
```

No los pipees a `tail`: sin `-f` no emite un byte hasta EOF y el watchdog te mata a los 600 s
(ADR-0041). Es el comando, no una opción.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P5-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; la verificación empírica probada en las dos
direcciones (**el CLI contesta bien ⇒ se acepta; el CLI no contesta o contesta mal ⇒ NO se acepta
nada**); el caso Ollama con `alive|dead|unreachable` distinguidos; **las tres superficies** con su
etiqueta nueva; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En esta
feature ya aparecieron **tres** tests que decían cubrir algo que no miraban: dos en P1 y uno en P3.
No escribas el cuarto.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Checkpoint

Si te acercás al límite de ejecución, escribí progreso parcial **y los próximos pasos exactos** en
la evidencia antes de parar.

## Fuera de alcance

El sort key · el consumo y la cuota (023) · desbloquear Copilot aguas arriba (no se puede) ·
convertir a pi en descubridor de credenciales · arreglar `check-owned-paths.py` · features 023-025.
