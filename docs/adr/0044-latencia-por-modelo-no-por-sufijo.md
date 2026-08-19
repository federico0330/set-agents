# ADR-0044 — La latencia es una propiedad del modelo elegido, no un requisito del sufijo del nombre

- Estado: Accepted (2026-08-13). **Amended in part by ADR-0060** (Accepted 2026-08-19): el loop
  hot-path que conservaba `-fast` para `implementer`/`product-analyst` pasa a
  barato/free; `product-analyst` sale. Coord grok, límite lane `codex`, y P2
  `model_request` siguen. Feature 026-orquestador-elige-modelo, PKG-1
  (`P1-latencia-por-modelo-no-por-sufijo`) y PKG-2 (`P2-modelo-por-instancia`, AC-04..AC-07,
  sección "Extensión P2" más abajo). El loop `-fast` de `implementer`/`product-analyst`
  queda superseded in part by ADR-0060.

## Contexto

Pedido directo de Federico: *"elimina el hecho de que el modelo orquestador necesariamente tenga
que correr en fast, y dejalo en la politica de cada modelo"*. Origen inmediato: un intento previo
del orquestador de sacar a GPT del rol coordinador puso la suite en rojo en
`tests/test_harness.py:266` (`test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_
reviewers_apart`) y fue revertido a propósito — sin tocar el test — en vez de arreglado.

Medido con `opencode models <provider> --pure` sobre el árbol actual: el sufijo `-fast` **sólo
existe en el proveedor `openai` de opencode** (`gpt-5.6-luna-fast`, `gpt-5.6-sol-fast`,
`gpt-5.6-terra-fast`). Ni `opencode-go` (18 ids, `[catalog].opencode_go`) ni `opencode-zen` (61
ids, `[catalog].opencode_zen`) tienen una sola variante `-fast`. La aserción que exigía ese sufijo
para `orchestrator`, `implementer` y `product-analyst` no medía "baja latencia": medía
**"tiene que ser de OpenAI"**, porque `-fast` es una convención de nombre de un solo proveedor, no
una propiedad general del catálogo.

## Decisión

### 1. `orchestrator` sale de la política de sufijo; `implementer` y `product-analyst` la conservan

`tests/test_harness.py:272-282` reescribe el loop de la aserción sin `orchestrator`, con la razón
documentada en el propio comentario (no en un lugar aparte que se pueda desincronizar). La regla
se mantiene íntegra para los dos roles de volumen — `implementer` y `product-analyst` siguen
siendo el camino caliente de dispatch (muchas instancias cortas por feature), donde `-fast`
compra latencia real. `orchestrator` es una instancia larga y única por feature: el criterio de
elección para el coordinador no es la latencia de arranque de una instancia individual, sino la
calidad de la decisión sostenida a lo largo de una sesión larga. El test sigue en rojo si
`implementer` o `product-analyst` pierden su variante rápida (mordido en las dos direcciones,
evidencia del paquete) — no se relaja, se acota a lo que efectivamente mide.

**No se toca** la parte del test que separa a `package-reviewer`/`adversarial-judge` del
`implementer` (`:285-291` antes de este cambio) — es una garantía de 015-anthropic-dispatch-parity,
de una familia de modelos distinta (deep-reasoning vs. hot-path), ajena a este paquete.

### 2. `[areas.coord].opencode` pasa a un modelo no-GPT, de suscripción

```toml
opencode = { "go-zen" = "opencode-go/grok-4.5", "zen" = "opencode/grok-4.5", "local" = "opencode/grok-4.5" }
```

`opencode-go` en la lane principal (go-zen) porque es **suscripción**: no consume la cuota de
Copilot ni el medido por token de `opencode-zen`. Verificado en vivo: `grok-4.6` **no** está en
`[catalog].opencode_zen` (61 ids curados) — por eso las lanes `zen` y `local`, que sí pasan por
ese techo curado, se quedan en `grok-4.5`, el mismo modelo ya usado en la lane principal.

### 3. El límite honesto: en la lane de `codex` el coordinador sigue siendo GPT

Este cambio vive enteramente en la dimensión `opencode` de `[areas.coord]`. La dimensión `codex`
de esa misma sección (`codex = "gpt-5.6-terra"`) no se toca y no se puede tocar dentro de este
paquete: el CLI `codex` sólo sirve modelos de OpenAI — no hay proveedor no-GPT que ese runtime
pueda invocar. Un coordinador que corre en la lane de `codex` sigue obligado a GPT, no por una
política de latencia sino por una limitación estructural del propio CLI. Esto no es una brecha
que este ADR deje sin nombrar: es el límite real del alcance de "el orquestador elige el modelo"
cuando el runtime asignado es `codex` en vez de `opencode`.

## Alternativas rechazadas

- **Borrar o relajar la aserción de latencia en vez de reescribirla con su alcance real**:
  rechazado — perdería poder de detección para `implementer`/`product-analyst`, que sí dependen de
  `-fast` para el volumen de dispatch que manejan. El defecto era el alcance de la regla
  (incluía a `orchestrator` sin razón), no la regla en sí.
- **Mover a `orchestrator` a un modelo `-fast` de OpenAI para no tocar el test**: es exactamente lo
  que el intento previo (revertido) evitó arreglar — habría mantenido "latencia" como sinónimo de
  "OpenAI" en vez de corregir el defecto conceptual medido en el Contexto.
- **Sacar la política de latencia también de `implementer`/`product-analyst`**: fuera de alcance de
  este paquete (nombrado explícitamente en la spec 026 y en el context pack de PKG-1) — esos dos
  roles son de alto volumen y la razón de negocio para `-fast` sigue vigente ahí.

## Consecuencias

- El coordinador en la lane `opencode` (go-zen/zen/local) corre en `grok-4.5`, suscripción, sin
  perder ninguna garantía de test — la aserción reescrita sigue detectando una regresión real en
  `implementer`/`product-analyst` (mordida en `docs/specs/026-orquestador-elige-modelo/evidence/
  P1-implementer.md`).
- El coordinador en la lane `codex` sigue en GPT — límite estructural del CLI, no una decisión de
  este paquete, declarado para que no se lea como un descuido en una revisión futura.
- La preferencia de modelo por instancia (elegir el modelo de un spawn puntual, más allá de la
  política por área) queda para P2, fuera de este paquete.

## Extensión P2 (`P2-modelo-por-instancia`, AC-04..AC-07) — los tres mecanismos juntos

Pedido directo de Federico: *"que el orquestador pueda elegir qué modelo quiere asignarle a cada
instancia de agente. No quiero que esté obligado a usar gpt para esos roles siempre."* PKG-1 (arriba)
resolvió el caso `orchestrator`/`[areas.coord]` moviendo una POLÍTICA de área. Quedaban dos preguntas
sin resolver: (a) ¿puede el orquestador pedir un modelo para **un solo spawn puntual**, sin tocar la
política del rol entero? y (b) si ese modelo pedido viola una barrera real (independencia de
reviewer, techo de catálogo, tier), ¿qué pasa? Este paquete agrega el TERCER mecanismo — nunca
reemplaza los otros dos — y responde (b) con una negación nombrada, nunca una degradación
silenciosa.

### Los tres mecanismos, con su alcance exacto

| Mecanismo | Alcance | Persistencia | Dónde vive |
|---|---|---|---|
| `[areas.*]` en `models.toml` | por ÁREA (`coord`, `implement`, `audit`, ...) — todo el repo, todos los roles de esa área | persistente, versionado en git | `models.toml`, este ADR §1-3 |
| `--model-pin-set ROLE PROVIDER/MODEL` (ADR-0032) | por ROL — pega a **todos** los spawns futuros de ese rol hasta que se limpie | persistente, del usuario, en `~/.local/state/set-agentes/model-preference.toml` (`[model_pin]`) | `set_agents_app.py` (`cmd_model_pin_set`/`load_model_pin`), `routing_core/service.py` (`self._model_pin`, sort-key `pin_rank`) |
| `model_request` en el descriptor de `--route-decide` (AC-04..AC-07, este paquete) | por INSTANCIA — un solo spawn puntual, nunca más | **efímero**: vive sólo dentro de la llamada a `RoutingService.route()` que lo recibió; nunca se escribe a `model-preference.toml`, nunca altera el pin global, no sobrevive al spawn | `set_agents_app.py` (`_validate_model_request`, la clave nueva en `cmd_route_decide`); `routing_core/service.py:243` (parámetro `model_request` de `route()`) |

Un rol sin pin ni `model_request` sigue la política de área. Ninguno de los tres — ni el nuevo —
puede saltear una exclusión dura (independencia de reviewer, techo de catálogo, tier, par auditado):
los tres entran como factor de SORT, siempre después del bucle de exclusiones de `route()`, nunca
antes (el pin desde ADR-0032, `model_request` desde este paquete, en la misma disciplina,
`service.py:243-528`).

**Medido, no asumido — el pin persistente gana sobre el `model_request` efímero cuando ambos nombran
identidades ELEGIBLES distintas**, no al revés: `pin_rank` se evalúa ANTES de `TIER_ORDER` en la
tupla de sort (`service.py:435`), y `model_request`'s propio factor se insertó DESPUÉS de
`TIER_ORDER` (AC-05) — la comparación de tuplas de Python corta en el primer elemento que
difiere, así que `pin_rank` decide antes de que `model_request` llegue a pesar. Verificado
directamente:
```
>>> # pin={"implementer": ("openai-codex","gpt-5.6-sol")}, model_request=("opencode-go","kimi-k3"), ambos candidatos elegibles
>>> decision.provider, decision.model, decision.reason_codes
('openai-codex', 'gpt-5.6-sol', ('BILLING_RANK provider=openai-codex rank=0',
 'MODEL_PINNED openai-codex/gpt-5.6-sol',
 'MODEL_REQUEST_UNAVAILABLE requested=opencode-go/kimi-k3 reason=OUTRANKED'))
```
El pin gana, y `model_request` lo nombra con su propio código (`OUTRANKED`, nunca silencioso) — un
comportamiento honesto y consistente con AC-06, aunque la interacción PIN-vs-INSTANCIA en sí no
estaba entre los ACs de este paquete (no se tocó `pin_rank` para cambiarlo). Si en el futuro se
decide que la instancia debe ganarle al pin, ese es un cambio de ORDEN relativo explícito, deliberado
y fuera de este paquete — no algo que este documento deba asumir sin medirlo.

### AC-04: el conjunto cerrado del descriptor gana una clave, nunca se abre

`set_agents_app.py:629` (`cmd_route_decide`): `allowed` pasa de 7 a 8 claves — se agrega
`"model_request"`, nunca se generaliza a "cualquier clave adicional". Una clave desconocida sigue
dando `ROUTING_INPUT_INVALID`/rc=2, exactamente como antes de este paquete (`tests/
test_model_request.py::ModelRequestCliTests::test_unknown_key_still_rejected_after_model_request_
joins_the_allowed_set`). El valor es una cadena `"provider/model"`, validada por
`_validate_model_request` con el mismo vocabulario cerrado de proveedores y la misma regex de
modelo que `_validate_model_pin_entry` (ADR-0032) ya usa para `[model_pin]` — reutilizado como valor
suelto, sin tabla, sin archivo.

### AC-05: nunca antes de las exclusiones — el corazón del paquete

`RoutingService.route()` (`routing_core/service.py`) evalúa `model_request` en dos puntos, los dos
DESPUÉS del bucle de exclusiones duras (identidad, auth, rol, herramientas, contexto, independencia
de reviewer, tier — `service.py:321-392`, sin tocar):

1. **Sort key** (`service.py:435`): un factor nuevo, insertado — nunca reordenado — entre
   `TIER_ORDER` y `billing_rank`, el mismo estilo de inserción que `_bias_rank`
   (014-model-preference-policy) y `billing_rank` (ADR-0035) ya establecieron como precedente para
   este mismo bloque. Sólo compara candidatos que YA sobrevivieron el bucle de exclusiones — un
   candidato excluido nunca llega a `candidates`, así que `model_request` no puede hacerlo ganar por
   más que se le pida.
2. **Reason codes** (`service.py:500-512`): `MODEL_REQUEST_APPLIED provider/model` cuando el pedido
   ganó, o `MODEL_REQUEST_UNAVAILABLE requested=provider/model reason=X` cuando no — nunca
   silencioso (AC-06, abajo).

Un test por barrera (`tests/test_model_request.py::ModelRequestBarrierTests`), cada uno pidiendo
explícitamente un modelo que la viola y comprobando que NO se elige y que la exclusión trae su razón:
`REVIEW_PROVIDER_CONFLICT`, `REVIEW_MODEL_CONFLICT`, `TIER_INSUFFICIENT`, `PROVIDER_UNAUTHENTICATED`
(par no auditado), y un modelo fuera del techo de catálogo (`NOT_IN_CATALOG` — la forma observable
que toma un modelo fuera de `resolve_ceiling`, 022/P2, porque nunca llega a existir como
`StaticRoute`). Más un test explícito, `test_model_request_enters_after_the_exclusion_loop_never_
before_it`, que corre el MISMO escenario con y sin `model_request` y comprueba que la lista de
exclusiones y el ganador son byte-idénticos — la única diferencia observable es el marcador
adicional.

### AC-06: la negación nombra el modelo y la razón, precedente `CATALOG_CEILING_REQUIRED`

`MODEL_REQUEST_UNAVAILABLE requested=<provider>/<model> reason=<X>` — nunca un reason_code genérico,
mismo espíritu que `CATALOG_CEILING_REQUIRED` (022/P2): un código específico y accionable en vez de
uno genérico que no dice nada. `reason` resuelve, en orden: la barrera que la propia exclusión ya
nombró (`REVIEW_PROVIDER_CONFLICT`, `TIER_INSUFFICIENT`, ...); `OUTRANKED` cuando el candidato pedido
sobrevivió toda exclusión pero perdió el desempate ante otro candidato empatado o mejor en tier;
`NOT_IN_CATALOG` cuando ningún route del catálogo nombra ese `(provider, model)`.

### AC-07: efímero — no escribe nada, no sobrevive al spawn

`model_request` viaja como argumento nuevo de `RoutingService.route()` (`model_request=None` por
defecto, `service.py:243`), nunca como campo de `TaskRequest` ni de la tabla `_model_pin`/
`preference` que `_config_with_model_preference` inyecta desde el archivo. `cmd_route_decide` lo
arma en una variable local a partir del descriptor y lo pasa directo a `route()` — ningún call site
lo persiste, ningún call site lo pasa a `atomic_write`/`MODEL_PREFERENCE_PATH`. Probado en
`tests/test_model_request.py::ModelRequestCliTests`:
`test_model_request_never_writes_model_preference_toml` (el archivo sigue sin existir después de la
llamada) y `test_model_request_does_not_bias_a_later_decide_call_without_it` (una segunda decisión,
sin `model_request`, en el mismo proceso/raíz de routing, vuelve exactamente al ganador de línea
base — nada quedó pegado).

## Evidencia

`docs/specs/026-orquestador-elige-modelo/evidence/P1-implementer.md` (PKG-1),
`docs/specs/026-orquestador-elige-modelo/evidence/P2-implementer.md` (PKG-2, AC-04..AC-07).
