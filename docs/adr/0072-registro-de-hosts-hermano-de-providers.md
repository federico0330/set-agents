# ADR-0072 — Registro de hosts: un tercer registro hermano de `PROVIDERS`, nunca mezclado con él

- Estado: **Accepted** (2026-08-26). Feature `046-hosts-descubiertos` (AC-01..AC-07), con la cláusula
  §9 que gobierna a `047-lanes-agy-fx-copilot`.
- **Extiende ADR-0042** sin superseder nada de él: `PROVIDERS` sigue siendo la única fuente de las
  tablas keyed-by-provider y su orden de inserción sigue siendo contrato
  (`ai/scripts/provider_registry.py:18-21`). El eje de hosts es un **tercer** registro en el mismo
  módulo neutral, por el mismo precedente que 022 PKG-4 sentó con el segundo (`:76-89`).
- **Supersede el universo de hosts del panel Estado**: `_estado_general_lines`
  (`ai/scripts/set_agents_app.py:3737-3740`) deja de definir "qué CLIs de IA tiene esta máquina" a
  partir de `HARNESS_CLIS` (`:51`) más una fila `pi` agregada a mano.
- Reafirma, no levanta: **M-1** para el provider OpenCode `github-copilot`
  (`ai/scripts/routing_core/catalog.py:144-158`), **ADR-0038** (instalar es propose→approve),
  **ADR-0043** (qué prueba un probe), **ADR-0063** (Cursor fuera de `RUNTIMES`).

## Contexto

El harness no tiene eje de hosts. Tiene un eje de **providers** (`PROVIDERS`,
`provider_registry.py:56-73`: cuatro identidades OpenCode-facing con `opencode_auth_key` y
`opencode_cli_id`) y una lista de CLIs hardcodeada (`HARNESS_CLIS = ("opencode", "claude", "codex")`,
`set_agents_app.py:51`) que alimenta `auth_state` (`:1301`) y `_status_data` (`:1350-1353`), más una
fila `pi` agregada a mano al panel (`:3739-3740`). Un CLI instalado y funcionando que no sea uno de
esos cuatro es invisible.

Medido en esta sesión, 2026-08-26, con `command -v`:

| candidato | resultado |
|---|---|
| `agy` | `/home/federico/.local/bin/agy` |
| `fx` | **ausente** |
| `copilot` | `/home/federico/.local/bin/copilot` |
| `claude` | `/home/federico/.local/bin/claude` |
| `codex` | `/home/federico/.local/bin/codex` |
| `opencode` | `/home/federico/.opencode/bin/opencode` |
| `pi` | `/home/federico/.local/bin/pi` |

`agy` y `copilot` están instalados y ausentes de toda superficie. Meterlos en `PROVIDERS` no es opción:
el orden de inserción de ese dict es contrato real (`_MODEL_PREFERENCE_PROVIDERS` deriva su tupla
ordenada de `tuple(PROVIDERS)` y ese orden llega a mensajes de validación al usuario), y un host — un
binario en `PATH` — es una clase de cosa distinta de una identidad de provider.

## Decisión

### 1. `HOSTS` vive en `provider_registry.py`, como tercer registro independiente

`HOSTS: dict[str, HostSpec]`, con `HostSpec` como `dataclasses.dataclass(frozen=True)`, en el mismo
módulo. Razón medida: `provider_registry.py` no importa nada más que `dataclasses`/`json`/`re`/`tomllib`
(`:24-30`) y su docstring (`:10-16`) explica por qué esa propiedad es la que permite que sus tres
consumidores lo importen a nivel de módulo — que es exactamente lo que necesita un consumidor que corre
en el pintado del menú. Un módulo nuevo bajo `ai/scripts/` pagaría en los dos gates que escanean ese
directorio (`py_compile` en `verify.sh`, el guardián de encoding en `tests/test_harness.py`) a cambio de
nada.

Diferencia explícita con `PROVIDERS`: el orden de `HOSTS` es el orden de **display** y nada más. Ninguna
otra tabla deriva de él, así que no hereda el miedo de `tuple(PROVIDERS)`. Queda escrito para que nadie
lo lea al revés.

### 2. `HostSpec`: dos campos, ningún hecho duplicado

```
HostSpec(detect_bins: tuple[str, ...], lane: str | None)
```

- `detect_bins` es **ordenado** y la presencia es "alguno resuelve". Es tupla y no escalar por un caso
  medido, no por generalidad especulativa: `_pi_lane_state()` (`set_agents_app.py:921-929`) documenta
  que `shutil.which("pi")` es un **falso negativo estructural** en toda máquina fresca, porque `pi`
  resuelve vía `pnpm dlx` contra el pin de `routing_core/catalog.py`. La fila de `pi` es
  `("pi", "pnpm")`, y **cuál** de los dos matcheó da el mismo detalle de tres valores que
  `_pi_lane_state` devuelve hoy (`yes` / `via-pnpm-dlx` / `no`) — una sola fuente, no dos.
- `lane` es el miembro de `RUNTIMES` que materializa el host, o `None`. `has_lane` es `lane is not None`,
  **derivado y no almacenado**: la lección de ADR-0042 es que seis copias sincronizadas a mano de un
  mismo hecho se desincronizan, y un booleano al lado del `lane` que lo determina es la copia número dos.

Nada de auth ni de versión entra en `HostSpec`: eso ya lo miden `auth_state` (`:1301`) y `version_of`
(`:1327`), y el registro es una declaración estática, no un cache de mediciones.

### 3. Resolución de estado: función total, primer match gana

El vocabulario cerrado de 046 §Scope 3, con **dónde** se computa cada estado:

| estado | condición | fuente |
|---|---|---|
| `ausente` | ningún `detect_bins` resuelve | `shutil.which` — sólo `PATH`, sin red, seguro en el pintado del menú |
| `sin lane` | resuelve y `lane is None` | el registro |
| `unlistable` | resuelve, tiene lane, y no hay lista de modelos verificada disponible | probe **cacheado** (`_probe_cache_root()`, ADR-0043) |
| `vivo` | resuelve, tiene lane, y la lista verificada tiene ≥1 modelo | el mismo cache |

Exactamente uno por host, primer match gana, así que `sin lane` y `unlistable` nunca pueden reclamarse
a la vez (046 audit (i)).

`unlistable` se computa **desde el cache**, nunca con un subprocess sincrónico en el hot path de
`menu()` (046 UNVERIFIED #5): el panel es `PATH`-only por diseño de AC. Un cache miss es `unlistable`,
no `vivo` — fail-closed, la disciplina M-1 (`catalog.py:144-158`), y además literalmente cierto: sin
lista verificada el host aporta cero pares al router en ese instante. La columna de detalle nombra
**por qué** (`sin probe todavía` vs. `probe sin modelos`), que es la regla de ausencia-nombrada que
045 AC-A.2 ya impone sobre este mismo panel. Ese detalle es texto: nada ramifica sobre él, y no es un
quinto estado.

### 4. Descubrir observa; nunca instala y nunca rutea

Un binario en `PATH` que no está en `HOSTS` no produce fila y no dispara nada (AC-05). La única puerta
sigue siendo el propose→approve de ADR-0038 (`cmd_tools_install`, cola `TOOL_UNKNOWN`,
`set_agents_app.py:2138-2142`).

La lista de candidatos es una **constante de Python**, no una tabla TOML extensible por el usuario. Una
lista extensible sería precisamente la puerta de instalación silenciosa que AC-05 cierra, y
`tools.local.toml` ya muestra lo que cuesta mantener honesta una lista extensible (revalidación en
`:2143-2167`).

### 5. Miembros: los siete de 046, y `cursor` deliberadamente afuera

`agy`, `fx`, `copilot`, `claude`, `codex`, `opencode`, `pi`.

`cursor` resuelve en esta máquina (`/usr/bin/cursor`) y **no** es miembro. Dos razones: 046 AC-01 fija
el universo en siete nombres y se mide contra esa lista, así que un octavo contradiría el AC aprobado; y
ADR-0063 mantiene a Cursor como pin-host fuera de `RUNTIMES`, donde una fila con `lane=None` permanente
invitaría justo a la lectura "hagámoslo lane" que 047 lista como no-goal. Si se quiere una fila Cursor,
es una enmienda de spec (ADR-0028), no un pie de página de ADR.

### 6. Host ≠ provider OpenCode: dos ejes, ninguno derivado del otro

La fila host `copilot` y el provider OpenCode `github-copilot` son independientes (046 AC-06). M-1 sigue
en pie: credencial autenticada, `opencode models github-copilot --pure` responde `Provider not found`,
cero pares agregados (`catalog.py:144-158`). La independencia es **estructural**, no una rama de código:
`github-copilot` nunca aparece en `_PAIR_COMMANDS` (`catalog.py:155`, `:170-174`), así que `_probe_pairs`
jamás lo consulta, y `HOSTS` no es entrada de `_PAIR_COMMANDS`.

### 7. `HARNESS_CLIS` conserva su significado; la tabla del panel se reemplaza

`HARNESS_CLIS` (`:51`) sigue siendo el universo de los flujos de install/auth que ya lo consumen
(`auth_state` `:1301`, `_status_data` `:1350-1353`); no se toca. Lo que se reemplaza es la tabla
`Harnesses` de `_estado_general_lines` (`:3737-3740`), que pasa a derivar de `HOSTS`. La fila `pi`
agregada a mano (`:3739-3740`) **desaparece**, absorbida como `HOSTS["pi"]`: dos filas para un host es
el defecto de eje duplicado que esta feature existe para borrar (046 UNVERIFIED #4).

### 8. Ni módulo nuevo ni entrada en `modules.toml`

El registro de hosts no es un módulo nuevo: vive al lado de `PROVIDERS`, en un archivo que ya existe —
mismo precedente que la cláusula "No new module: this lives inside `module.estado`" de ADR-0065.
Límite honesto que este ADR nombra sin arreglar: `ai/scripts/provider_registry.py` hoy **no está en
ningún `paths` de `docs/modules/modules.toml`** (`models_config.py` es de `module.generacion-arboles`,
`routing_core/**` de `module.routing`). Es un hueco preexistente de detección de impacto, no algo que
046 introduzca, y taparlo desde acá dispararía un render de `docs/modules/` que no pertenece a este
paquete.

### 9. Cláusula para 047: cuándo un host entra a `RUNTIMES` / `SELECTED_RUNTIMES`

Un host entra a los enums **sólo** cuando su par `(runtime, provider)` tiene una entrada **medida** en
`_PAIR_COMMANDS` (`routing_core/catalog.py:170-174`). La razón está en el código, no en preferencia:
el loop de exclusiones de `service.route()` descarta todo candidato cuyo modelo no esté en
`self.inventory[(effective_runtime, provider)]` (`service.py:366` → `PROVIDER_UNAUTHENTICATED`), y el
inventario se construye únicamente a partir de pares de `_PAIR_COMMANDS` (`catalog.py:898-900`). Ensanchar
los enums sin comando de probe medido compra un descriptor que valida y una lane que no puede rutear
nunca — y gastaría en nada la única supersesión de contrato público que 047 puede pedir.

De ahí, por host:

- **`agy`** — recomendado **sí**, condicionado: entra cuando (a) se mida su comando de listado de
  modelos y (b) tenga entrada en `_PAIR_COMMANDS` con identidad de provider. Ensanchar
  `SELECTED_RUNTIMES` (`domain.py:20`), `RUNTIMES` (`usage.py:97`), `models_config.RUNTIMES` (`:44`) y
  el rechazo rc=2 de `cmd_route_decide` (`set_agents_app.py:690`) es **un solo cambio atómico**
  (047 audit (iv)): si se separan, un descriptor que nombra la lane falla mientras la lane existe.
- **Copilot CLI** — misma regla. Medible o se queda en `sin lane`. Su estado de host nunca implica un
  par ruteable OpenCode (§6).
- **`fx`** — re-medido **ausente** en esta máquina, así que acá no se puede medir nada: cierra como
  `SPAWN_DEFERRED` con razón escrita en el `evidence/` de la feature (047 AC-05) y **no** entra a los
  enums. La razón debe distinguir los dos casos que el token cubre: binario ausente vs. probe inestable.
- **Sin estado intermedio.** Un host con adapter pero sin membresía en los enums no rutea nada, así que
  sigue siendo `sin lane` en el vocabulario de 046 hasta que los enums se ensanchen. No hay media-lane.
- **`install_harness` es ortogonal a los enums.** Aplicar el harness (roles, doctrina, config) a un host
  ya instalado no requiere que sea lane de routing — Cursor es la prueba viva (ADR-0063). Lo gatea la
  membresía en `HOSTS`; instalar el **binario** sigue siendo de ADR-0038.

## Alternativas rechazadas

- **Meter hosts en `PROVIDERS`.** Su orden de inserción es contrato vía
  `tuple(PROVIDERS)` → `_MODEL_PREFERENCE_PROVIDERS` → mensajes de validación al usuario
  (`provider_registry.py:18-21`), y un binario en `PATH` no es una identidad
  `opencode_auth_key`/`opencode_cli_id`.
- **Un módulo nuevo `host_registry.py`.** Paga `py_compile` y el guardián de encoding por nada;
  `provider_registry.py` ya **es** el hogar neutral de un segundo registro independiente (ADR-0042,
  `:76-89`).
- **Derivar la tabla de hosts de `HARNESS_CLIS` o de `PROVIDERS`.** Es el defecto exacto: produce filas,
  pasa un assert ingenuo de "la tabla no está vacía", y deja `agy`, `fx` y `copilot` invisibles (la
  fixture que engañaría a 046 AC-01).
- **Lista de candidatos extensible por el usuario en TOML.** Puerta de instalación silenciosa alrededor
  de ADR-0038.
- **Un quinto token para "todavía no probado".** `unlistable` más una columna de detalle que no ramifica
  lo dice honestamente y mantiene cerrado el vocabulario de 046 — que es la condición para que 047 sólo
  pueda mover un host entre estados existentes.
- **`detect_bin` escalar, con `pi` como caso especial aparte.** Reintroduce el falso negativo estructural
  que `_pi_lane_state` documenta y deja dos fuentes para un host.
- **Conservar la fila de `_pi_lane_state()` al lado de la fila host `pi`.** Dos filas para un host es el
  eje duplicado que la feature borra.
- **Agregar `cursor` como octavo host.** Contradice el universo de siete que 046 AC-01 mide y roza el
  no-goal de 047 sobre Cursor.
- **Ensanchar `RUNTIMES` para un host con probe sin medir.** Rechazado con la evidencia de
  `service.py:366` y `catalog.py:898-900`: enum ancho, lane que no rutea nunca.
- **Levantar o re-medir M-1 desde acá.** No-goal explícito de 046; sigue vigente hasta que alguien lo
  mida de nuevo.

## Consecuencias

- Los siete candidatos aparecen siempre, con un estado cada uno: la ausencia es una fila, no un hueco
  (AC-01, AC-02). `fx` es la prueba viva y la suite tiene que pasar en una máquina donde ninguno resuelve
  (AC-07).
- `PROVIDERS` queda byte-idéntico en orden y membresía; los mensajes de `--model-preference` no cambian
  (AC-04).
- El panel de Estado deja de tener un universo de hosts hardcodeado en dos lugares; `HARNESS_CLIS`
  sobrevive con su significado original de install/auth.
- 047 hereda una regla escrita para la única decisión de contrato público que puede pedir, y `fx` tiene
  una salida que **pasa** sin fabricar una lane.
- Hueco nombrado y no tapado: `provider_registry.py` sigue fuera de `docs/modules/modules.toml`, así que
  un paquete que lo toque no dispara detección de impacto de módulo.

## Evidencia

Medición propia 2026-08-26 (`command -v` sobre los siete candidatos más `cursor`/`pnpm`), coincidente
con la de la spec.
`ai/scripts/provider_registry.py:10-30`, `:56-73`, `:76-89`, `:18-21`.
`ai/scripts/set_agents_app.py:51`, `:690`, `:921-929`, `:1301`, `:1327`, `:1350-1353`, `:2138-2167`,
`:3737-3762`.
`ai/scripts/routing_core/catalog.py:144-158`, `:170-174`, `:898-900`.
`ai/scripts/routing_core/service.py:366`. `ai/scripts/routing_core/domain.py:20`.
`ai/scripts/routing_core/usage.py:97`. `ai/scripts/models_config.py:44`.
`docs/modules/modules.toml`. Contratos: `docs/specs/046-hosts-descubiertos/{spec,design,acceptance}.md`,
`docs/specs/047-lanes-agy-fx-copilot/{spec,design,acceptance}.md`.

## Destilado (dominio: architecture)

- El inventario que alimenta el router se construye **sólo** desde `_PAIR_COMMANDS`
  (`catalog.py:898-900`), y `service.py:366` excluye todo lo que no esté ahí: ensanchar `RUNTIMES` sin
  comando de probe medido produce una lane que no puede rutear nunca.
- `shutil.which(<host>)` no alcanza como primitiva de detección: `pi` resuelve vía `pnpm dlx` y un
  `which` pelado es falso negativo estructural (`set_agents_app.py:921-929`). La detección es una tupla
  ordenada de binarios, y cuál matcheó es el detalle.
- Presencia de credencial y lista de modelos verificada son ejes distintos (M-1,
  `catalog.py:144-158`): un cache de probe vacío es `unlistable` fail-closed, nunca `vivo` con cero
  modelos.
