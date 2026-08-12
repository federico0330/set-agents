# P2-billing-aware-ordering — evidencia de repair

Feature 019, PKG-2 (ADR-0035). Repair consolidado sobre los 3 hallazgos del review de
`docs/specs/019-harness-evolution/evidence/P2-implementer.md`. Estado al iniciar esta pasada:
las tres correcciones ya estaban presentes en el árbol de trabajo (working tree) sin commit —
esta pasada las **verificó** con evidencia fresca (incluida la prueba de mordida exigida
para F-01) y produjo esta tabla de trazabilidad; no fue necesario tocar código nuevo.

## Hallazgo → cambio → verificación

| Hallazgo | Archivo:línea | Cambio | Verificación |
|---|---|---|---|
| F-01 (alto) | `tests/test_routing.py:4293-4325` (`test_ac13_control_subscription_wins_at_equal_tier`) | Fixture reescrito: `opencode-go` (subscription) vs `opencode-zen` (metered), MISMO runtime (`"opencode"`) y MISMO tier (`"balanced"`) — solo `billing_rank` en el sort key puede decidir. Se agregó `self.assertEqual(decision.exclusions, ())` para pinear que ningún hard-exclusion decide el caso. | Prueba de mordida (ver §1 abajo): neutralizado falla, invertido falla, restaurado pasa. `python3 -m unittest tests.test_routing.RoutingTests.test_ac13_control_subscription_wins_at_equal_tier` → OK. |
| F-02 (bajo) | `tests/test_routing.py:4184` | Renombrado `test_sort_key_tripwire_pins_five_element_tuple_shape` → `test_sort_key_tripwire_pins_full_tuple_shape` (la tupla pinea 8 elementos desde ADR-0032/0034/0035, el comentario ya lo decía). `grep -rn` confirmó que el nombre viejo solo aparece en documentos de evidencia HISTÓRICOS de otros paquetes (`P1-implementer.md`, `P2-implementer.md`) — no se tocaron, son el registro inmutable de lo que esos paquetes hicieron en su momento, no documentación viva que referencie el test por nombre. Ningún doc vivo (`docs/adr/`, `docs/specs/019-harness-evolution/spec.md`, `docs/specs/019-harness-evolution/context/`) referencia el nombre viejo. | `python3 -m unittest tests.test_routing.RoutingTests.test_sort_key_tripwire_pins_full_tuple_shape` → OK. |
| F-03 (bajo) | `ai/scripts/setup_models.py:173-176` (default) y `:196-224` (`_panel_lines`, rama de string inesperado) | Default alineado a `models_config.ROUTING_DEFAULTS["discovered_providers"]` (`"auto"`, no `[]`). Rama nueva: `discovered == "auto"` resuelve contra el inventario vivo (`_resolve_live_discovered`); cualquier OTRO string truthy (no `"auto"`) degrada a un mensaje explícito (`"valor de configuración inesperado (...)"`) en vez de `', '.join(discovered)` iterándolo carácter a carácter; una lista explícita se sigue mostrando tal cual. | Verificación en vivo (ver §2 abajo): string inesperado → mensaje explícito, nunca letras sueltas; dict sin la clave `discovered_providers` → default `"auto"` resuelto (no `[]` silencioso). Suite: `tests/test_models_wizard_ui.py` (6 tests del panel) OK dentro de la corrida completa. |

## 1. Prueba de mordida F-01 (exigida por el hallazgo)

Base (`ai/scripts/routing_core/catalog.py:180-191`, `billing_rank`, sin tocar):

```python
def billing_rank(provider: str, model: str) -> int:
    if PROVIDER_BILLING_KIND.get(provider) == "subscription":
        return 0
    if isinstance(model, str) and _FREE_MODEL_SUFFIX.search(model):
        return 0
    return 1
```

### Neutralizado (`return 0` siempre, temporal, revertido después)

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac13_control_subscription_wins_at_equal_tier -v
test_ac13_control_subscription_wins_at_equal_tier ... FAIL

AssertionError: 'opencode-zen' != 'opencode-go'
- opencode-zen
+ opencode-go

Ran 1 test in 0.069s
FAILED (failures=1)
```

### Invertido (`0` solo para `opencode-zen`, temporal, revertido después)

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac13_control_subscription_wins_at_equal_tier -v
test_ac13_control_subscription_wins_at_equal_tier ... FAIL

AssertionError: 'opencode-zen' != 'opencode-go'
- opencode-zen
+ opencode-go

Ran 1 test in 0.068s
FAILED (failures=1)
```

### Restaurado (`ai/scripts/routing_core/catalog.py` idéntico al de antes del experimento)

```
$ python3 -m unittest tests.test_routing.RoutingTests.test_ac13_control_subscription_wins_at_equal_tier -v
test_ac13_control_subscription_wins_at_equal_tier ... ok

Ran 1 test in 0.064s
OK
```

Árbol sin huellas del experimento: `grep -n "BITE-TEST" ai/scripts/routing_core/catalog.py` → sin
resultados; `git diff ai/scripts/routing_core/catalog.py | grep -c "BITE-TEST"` → `0`.

## 2. Verificación en vivo F-03

```
$ python3 -c "
import sys; sys.path.insert(0,'ai/scripts')
import setup_models
config = {'areas': {}, 'roles': {}, 'subscriptions': {}, 'routing': {'discovered_providers': 'weird-unexpected-value'}}
text = '\n'.join(setup_models._panel_lines(config, [], 'go-zen'))
for line in text.splitlines():
    if 'descubiertos' in line: print(line)
"
proveedores descubiertos rutables: valor de configuración inesperado ('weird-unexpected-value')

$ python3 -c "
import sys; sys.path.insert(0,'ai/scripts')
import setup_models, models_config
config = {'areas': {}, 'roles': {}, 'subscriptions': {}, 'routing': {}}
print('ROUTING_DEFAULTS discovered_providers =', models_config.ROUTING_DEFAULTS['discovered_providers'])
text = '\n'.join(setup_models._panel_lines(config, [], 'go-zen'))
for line in text.splitlines():
    if 'descubiertos' in line: print(line)
"
ROUTING_DEFAULTS discovered_providers = auto
proveedores descubiertos rutables: auto → ninguno vivo ahora (ver --route-doctor)
```

Nunca aparece `list("weird-unexpected-value")` iterado carácter a carácter, y un dict sin la
clave ya no renderiza como si la auto-adopción estuviera apagada.

## 3. Gates

### `python3 -m unittest discover -s tests`

```
Ran 831 tests in 697.517s

OK (skipped=3)
```

### `./ai/scripts/verify.sh`

```
OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

### `./build.sh --check`

```
CHECK_PASS: generated and validated profile go-zen
SELF_SCAFFOLD_SYNC_OK files=2
```

### `git diff --check`

Sin salida, exit 0 (limpio).

## 4. Notas

- Ownership respetado: solo se tocó (verificó) `tests/test_routing.py` y
  `ai/scripts/setup_models.py`. No se tocó `models.toml`, `routes.v1.toml`, `ai/state/`, ni
  `routing_core/` — F-01 confirmado como defecto de test únicamente (la prueba de mordida
  demuestra que el comportamiento de producción, `billing_rank` sin modificar, ya es
  correcto).
- No se debilitó ninguna aserción de regresión; F-01 en realidad ENDURECIÓ el test
  (agregó `exclusions == ()`, que es precisamente la aserción cuya ausencia dejó pasar el
  fixture roto).
- No se hicieron commits, no se tocó `ai/state/`, no se marcó nada como aceptado.
