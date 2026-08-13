# Context pack — P1-registro-de-proveedores (ADR-0042)

Spec: `docs/specs/022-disponibilidad-real/spec.md`, **AC-01, AC-02, AC-03**. Primer paquete de
022; los otros cuatro dependen de éste y **no** están en vuelo.

## Qué es este paquete, en una línea

Un único `PROVIDERS` del que se **derivan** las tablas de proveedores que hoy están en lockstep
manual. **No cambia comportamiento.** Si algo se comporta distinto después, es un defecto de
este paquete, no una mejora.

## Los siete símbolos, medidos hoy (no de memoria)

| Símbolo | Ubicación | Nota |
|---|---|---|
| `_OPENCODE_PROVIDER_KEYS` | `ai/scripts/routing_core/catalog.py:116-117` | display text de `opencode auth list` |
| `_OPENCODE_CLI_IDS` | `catalog.py:125-126` | argumento CLI de `opencode models <id>` |
| `_PAIR_COMMANDS` | `catalog.py:154-161` | **ya deriva** su mitad opencode de `_OPENCODE_CLI_IDS` |
| `PROVIDER_BILLING_KIND` | `catalog.py:172-173` | |
| key map de `_configured_models` | `catalog.py:216-217` | provider → clave de `[catalog]` |
| `DISCOVERABLE_PROVIDERS` | `ai/scripts/models_config.py:41` | es un `set` |
| `_MODEL_PREFERENCE_PROVIDERS` | `ai/scripts/set_agents_app.py:94` | es una `tuple` **ordenada** |

**La spec los llama "seis" y nombra siete.** No adivines cuál cuenta es la buena: derivá los
siete y **decí en la evidencia** cuál es el número correcto y por qué (probablemente seis son
los duplicados *manuales*, porque `_PAIR_COMMANDS` ya deriva la mitad opencode). Si corregís el
conteo, corregilo también en el objetivo del paquete vía la evidencia — no edites la spec.

## Tres trampas verificadas. Leelas antes de diseñar.

### 1. El "test que protege el sexto duplicado" no es lo que la spec sugiere — es peor y mejor a la vez

Medido con `grep -rn '_MODEL_PREFERENCE_PROVIDERS' tests/`:

- **SÍ existe un lockstep real** en `tests/test_routing.py:3191-3200`
  (`test_adr0034_ac10_discoverable_providers_lockstep_guard`): assertea
  `models_config.DISCOVERABLE_PROVIDERS == {provider for _, provider in _PAIR_COMMANDS}`.
  **Ese test tiene que seguir pasando sin tocarlo.** Es tu red.
- **`_MODEL_PREFERENCE_PROVIDERS` no tiene ninguno.** Su única aserción está en `:3965`,
  **adentro de un `with mock.patch(...)` de otro test** cuyo propósito es distinto, comparando
  contra un literal hardcodeado. Es incidental, no una guarda.

O sea: la guarda falta exactamente en el símbolo que vive en otro archivo. Escribí **ese** test.

### 2. Hay un no-goal explícito y previo que decís lo contrario de lo que vas a hacer

`set_agents_app.py:90-94`, literal:

```
# The closed, four-provider universe `_PAIR_COMMANDS` already probes
# (`routing_core/catalog.py:133-140`) -- defined independently here, never importing or
# referencing the catalog module's own billing-kind classification table (AC-06 non-goal).
```

Y `:113-114` afirma que es **"byte-identical to `models_config.DISCOVERABLE_PROVIDERS`"** —
lo cual **no es cierto en el sentido literal**: uno es `set`, el otro `tuple` ordenada.

Dos consecuencias obligatorias:

- **ADR-0042 tiene que superseder ese no-goal explícitamente**, no ignorarlo. Alguien lo decidió
  con una razón; la razón nombrada es la tabla de *billing-kind*, que es más angosta que "no
  derivar nada". Decilo así.
- **Los comentarios que quedan contradiciendo al código son un defecto entregable.** Si derivás,
  reescribí `:90-94` y `:113-114`. Un comentario que miente es lo que este paquete existe para
  eliminar.
- **Preservá el orden de la tupla.** `DISCOVERABLE_PROVIDERS` es un `set` sin orden; si derivás
  la tupla de un `set`, el orden queda no determinístico entre corridas. El orden de hoy es
  `("openai-codex", "anthropic", "opencode-zen", "opencode-go")` y llega a superficie de usuario.

### 3. Dónde vive `PROVIDERS` es la decisión de diseño del paquete, y hay una restricción dura

Medido:

- `catalog.py` **no importa** `models_config` en absoluto.
- `models_config.py` importa `routing_core.catalog` **sólo lazy, adentro de funciones**
  (`:257`, `:275`), y el docstring de `detect_subscriptions` (`:250-251`) dice por qué:
  *"Lazy import (no routing_core dependency at module load)"*.

Entonces: **si ponés `PROVIDERS` en `catalog.py`, hacer que `models_config.DISCOVERABLE_PROVIDERS`
lo derive a nivel de módulo rompe esa disciplina.** No la rompas por conveniencia. Un módulo
neutro sin dependencias que importen los tres consumidores es la salida obvia, pero la elección
es tuya y **va argumentada en ADR-0042 con esta medición**, no como preferencia estética.

## AC-02 — cómo se prueba que no cambiaste nada

Test de caracterización: cada tabla derivada **igual a los literales de hoy**. Los literales van
pegados en el test, no importados de la fuente nueva — un test que compara la derivación contra
sí misma es exactamente la guarda falsa de la trampa 1, ahora escrita por vos.

Ya existen tests que assertean estos valores contra literales (`:3131-3136` los dos mapas
opencode, `:3256-3266` `PROVIDER_BILLING_KIND` con `assertEqual` de dict completo). **No los
toques.** Que sigan verdes sin una sola edición es la mejor prueba de que el refactor preserva
comportamiento; editarlos destruye la prueba.

## AC-03 — qué corrige el ADR

`ADR-0034:124-126` afirma que el día que opencode exponga Copilot no haría falta tocar código.
**Es inexacto**: harían falta entradas en las tablas de arriba. ADR-0042 lo corrige **con la
medición** y explica que este paquete es lo que vuelve cierta esa afirmación. No edites ADR-0034
retroactivamente: `docs/adr/README.md` marca la relación (no-goal de la spec).

## Restricciones

- **ADR-0042 primero** — `ls docs/adr/` para confirmar que el número está libre; indexalo en
  `docs/adr/README.md`. `owned_paths` tiene el directorio `docs/adr`, no un nombre inventado.
- **Sin refactors oportunistas.** El pedido es derivar tablas. No reorganices `catalog.py`, no
  toques `_probe_pairs`, no toques el sort key. El techo `[catalog]` tri-estado es **P2**.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- No relajes, saltees ni borres tests.
- `tests/test_harness.py` assertea frases doctrinales por grep: `grep -n` antes de mover texto.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh`
→ `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` ·
`git diff --check` limpio.

**Corré los comandos largos así, exactamente:**

```
ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
```

No lo pipees a `tail`: sin `-f`, `tail` no emite un byte hasta EOF, la suite tarda 7-10 minutos y
el watchdog del runtime te mata a los 600 s (ADR-0041). Murieron ocho instancias así en la sesión
anterior, **una de ellas con la herramienta ya nombrada en su prompt**. No es una opción entre
varias: es el comando.

## Evidencia

`docs/specs/022-disponibilidad-real/evidence/P1-implementer.md`: tabla AC → cambio
(`archivo:línea`) → prueba; los siete símbolos con su derivación; el conteo seis-vs-siete
resuelto; el argumento de dónde vive `PROVIDERS` con la medición de imports; la prueba de que
`:3191-3200`, `:3131-3136` y `:3256-3266` pasan **sin editarlos**; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.**
Aparecieron tests decorativos en tres de los cinco paquetes de 019 y en P1 de 020.

**Cada bloque que pegues es literal, o está marcado como recortado.** La sesión anterior acumuló
nueve afirmaciones de verificación que no resistieron la re-ejecución, tres del propio
orquestador. Si no lo corriste, escribí "sin verificar".

## Checkpoint

Escribí la evidencia en el **primer minuto** y guardá a disco a medida que avanzás. Si sentís que
te acercás al límite de ejecución, escribí progreso parcial + próximos pasos exactos antes de
parar.

## Fuera de alcance

El techo tri-estado (P2) · la firma de credencial y el de-auth (P3) · `providers.toml` y los
comandos `--provider-*` (P4) · altas/bajas automáticas (P5) · el sort key · agregar Copilot ·
features 023-025.
