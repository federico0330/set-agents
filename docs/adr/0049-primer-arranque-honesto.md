# ADR-0049 — Primer arranque honesto: `install.sh --yes` termina, `NO_ELIGIBLE_ROUTE` deja de ser
# mudo, y el harness deja de reescribir los globales del usuario sin decirlo

- Estado: Accepted (2026-08-14). Feature 024-listo-para-terceros, PKG-3 (`C3-primer-arranque-honesto`).
  AC-06, AC-07, AC-08.

## Contexto

Tres defectos medidos en el camino de instalación/ruteo que un recién llegado (o una instalación
desatendida) pisa en el primer arranque, C1/C2 de esta misma feature ya aceptadas (el estado ya no
viaja en el clon, `models.toml` ya no declara credenciales de nadie).

### AC-06 — `install.sh --yes` no termina

`confirm()` (`install.sh:56-62`) devuelve `0` **siempre** que `$YES -eq 1`. `auth_opencode()`
(`install.sh:309-311`, antes de este ADR) hacía `while confirm "..."; do opencode auth login || true;
done` — con `--yes`, la condición del `while` nunca es falsa: el loop no termina. Medido en vivo (ver
Evidencia): `timeout 5 bash install.sh --yes` corta con `EXIT=124` y **3153** invocaciones a
`opencode auth login` en esos 5 segundos. Una instalación desatendida (CI, un script, alguien
probando el producto con `--yes`) cuelga ahí para siempre.

### AC-07 — `NO_ELIGIBLE_ROUTE` no dice qué hacer

Cuando ninguna credencial está viva, el loop de exclusión de `RoutingService.route`
(`routing_core/service.py`, antes cerca de la línea 344) marca cada ruta candidata
`PROVIDER_UNAUTHENTICATED` (el mismo string que `catalog.py:306,321` produce cuando el parseo del
probe de auth falla), `candidates` queda vacío, y la decisión sale `NO_ELIGIBLE_ROUTE`
(`service.py`, antes línea 437). Correcto como fail-closed — pero mudo: alguien que acaba de clonar
recibe un `HUMAN_DECISION_REQUIRED` sin instrucción de qué comando correr.

### AC-08 — el install reescribe `~/.codex/config.toml` sin que se note

`merge_codex` (`install.py`) sobreescribe incondicionalmente `model`/`model_reasoning_effort` de
`~/.codex/config.toml` con lo que `roster_codex_orchestrator()` (`models_config.codex_orchestrator`)
resuelve desde `models.toml`. `build.sh`'s caso `install` ya corre `install.py --preview` antes de
la instalación real, y ya pide confirmación en TTY salvo con `--yes` — pero ese `--preview` diffea
el árbol COMPLETO (managed-files + specials) de una sola pasada. Medido en vivo (ver Evidencia): un
fixture con `~/.codex/config.toml` preexistente (`model = "gpt-5.6-luna"`), instalado sobre una
`$HOME` sin nada más, produce un `--preview` de **565KB, 9506 líneas, 96 archivos** — el hunk que
cambia el `model` (`gpt-5.6-luna` → `gpt-5.6-terra`) es UNA de esas líneas, en la posición 9487,
indistinguible del resto del ruido (contenido de prompts/agents.md que nunca es del usuario). No es
hipotético: en la sesión que motivó este paquete, el `--install` real le cambió a Federico
`gpt-5.6-luna` por `gpt-5.6-terra`, y lo único que lo notó fue el orquestador (otro agente) leyendo el
diff aparte, antes de correr el comando — el harness en sí no lo señaló. Misma familia de defecto que
ADR-0042/PKG-4 (022) cerró para el bloque `provider.*` de `opencode.json`: el harness no pisa lo del
usuario sin que quede a la vista.

## Decisión

### 1. AC-06 — con `--yes`, un solo intento de login, nunca un loop

`auth_opencode()` bifurca: con `$YES -eq 1`, corre `opencode auth login || true` **una vez** (nunca
en loop) — `--yes` ya es consentimiento para intentar loguearse, no consentimiento para preguntar
para siempre. Sin `--yes`, el `while confirm ...` interactivo queda exactamente igual (un humano
real decide cuándo parar de loguear proveedores). `install.sh:295-313` (antes 294-313).

### 2. AC-07 — `ROUTING_UNCONFIGURED` aditivo, sólo cuando TODAS las exclusiones son auth

`RoutingService.route` (`routing_core/service.py`), en la rama `if not candidates:` que hoy produce
`NO_ELIGIBLE_ROUTE`: cuando `writer` es `None` (el caso simple, no el de independencia de revisor) Y
`exclusions` es no vacío Y **todas** sus entradas tienen `reason == "PROVIDER_UNAUTHENTICATED"`, se
agrega un segundo elemento a `reason_codes`:

```
ROUTING_UNCONFIGURED no live credentials -- log in first: opencode auth login | codex login | claude (then /login)
```

Tres guardas explícitas contra falsos positivos:

- **`writer` presente (`REVIEWER_INDEPENDENCE_UNAVAILABLE`) nunca se decora.** Ese código sigue
  siendo el halt cerrado que ADR-0011 documenta — `--route-decide` devolviéndolo sigue siendo una
  denegación dura en todo runtime, sin excepción.
- **`exclusions` vacío nunca dispara el hint** (`bool(exclusions) and all(...)`, nunca sólo
  `all(...)` sobre una lista vacía — `all(())` es `True` por vacuidad, y un catálogo vacío es un
  defecto de catálogo genuino, no de credenciales).
- **Una sola exclusión de otra razón (`ROLE_INCOMPATIBLE`, `TOOLS_MISSING`, `CONTEXT_MISSING`,
  `TIER_INSUFFICIENT`, `RUNTIME_UNAVAILABLE`, ...) mezclada con las de auth apaga el hint entero** —
  `all(...)` exige unanimidad. Verificado mordiendo el positivo Y el negativo (ver Evidencia):
  el mismo fixture que hoy prueba una exclusión genuinamente mixta
  (`test_observed_risk_is_never_downgraded_and_enums_are_closed`) queda con
  `reason_codes == ("NO_ELIGIBLE_ROUTE",)` exacto, sin `ROUTING_UNCONFIGURED`.

Aditivo en el sentido estricto: `NO_ELIGIBLE_ROUTE` sigue siendo el primer (y a veces único)
elemento de `reason_codes`; nada en `_decide_status` (`routing_cli.py`) cambia — la tupla con el hint
extra sigue sin matchear `_DECIDE_OK_NON_EXECUTABLE_REASONS`, así que `ok`/`exit code` no se mueven un
bit. Dos tests preexistentes con igualdad exacta de tupla (`test_pi_is_pair_scoped_and_fails_closed_
without_a_probed_pair`, dos asserts) medían escenarios donde TODAS las exclusiones ya eran
`PROVIDER_UNAUTHENTICATED` — se actualizaron para reflejar el elemento aditivo, mismo criterio que
ADR-0035 ya estableció para la incorporación de `BILLING_RANK` en este mismo archivo.

### 3. AC-08 — el cambio de `model`/`model_reasoning_effort` de Codex se señala solo, siempre

`install.py` gana `flag_codex_model_change(current)`, invocada desde `effective_specials()` justo
antes de `merge_codex(current)` (misma condición `"codex" in targets`, corre en `--preview` y en la
instalación real, siempre, independientemente de `--yes`): si `current` (el `~/.codex/config.toml`
vivo) existe y ya tenía un valor explícito de `model`/`model_reasoning_effort` que **difiere** del
que `roster_codex_orchestrator()` va a escribir, imprime una línea propia, greppeable, separada de
cualquier diff de archivo:

```
CODEX_GLOBAL_MODEL_CHANGE model: gpt-5.6-luna -> gpt-5.6-terra file=/home/x/.codex/config.toml
```

Dos casos que deliberadamente NO imprimen nada (nada del usuario en riesgo, ruido cero en el
bootstrap ordinario):

- **El archivo no existe todavía** (máquina nueva): no hay valor del usuario que pisar.
- **El valor vivo ya coincide** con lo que el roster va a escribir (reinstalación estable, o ya
  aplicado): nada cambia, nada que avisar.

`build.sh`'s caso `install` sigue siendo el único llamador real de `install.py` (además de los tests):
corre `--preview` **antes** de la pregunta `[y/N]`, y de nuevo en la instalación real. Con `--yes` la
pregunta se salta, pero ambas corridas de `install.py` — incluida la de `--preview` — siguen
imprimiendo `CODEX_GLOBAL_MODEL_CHANGE` si aplica: el consentimiento de `--yes` nunca se convierte en
silencio, queda en el log de la corrida igual.

## La trampa que este ADR no pisa

AC-08 **no** se resuelve dejando de escribir `model`/`model_reasoning_effort` — el harness necesita
que el modelo del coordinador Codex sea el que el perfil activo declara, o el ruteo miente sobre qué
modelo está realmente corriendo. Lo que cambia es que la escritura deja de ser silenciosa: se nombra,
sola, con el valor viejo y el nuevo, en cada corrida (`--preview` y real), pase o no `--yes`.

## Alternativas rechazadas

- **AC-06: `--yes` salta el login de opencode por completo (cero intentos).** Rechazada — `--yes` es
  consentimiento explícito para avanzar, y un usuario que corre `./install.sh --yes` en una máquina
  sin loguear sigue queriendo que el instalador INTENTE loguearlo (un intento, sin loop). Callarse
  del todo dejaría una instalación "exitosa" sin ningún proveedor vivo, sin ni siquiera haberlo
  intentado.
- **AC-07: aplicar el mismo hint a `REVIEWER_INDEPENDENCE_UNAVAILABLE`.** Rechazada — ese código es
  el halt cerrado que ADR-0011 fija como denegación dura en todo runtime; decorarlo con texto extra
  arriesga que un consumidor lo trate como "más suave" de lo que es. AC-07 sólo pide `NO_ELIGIBLE_
  ROUTE`; el spec y el context pack lo nombran así, explícito.
- **AC-07: disparar el hint con `any(...)` en vez de `all(...)`.** Rechazada explícitamente en el
  context pack ("aditivo quiere decir aditivo... si una exclusión genuina de catálogo también
  reporta ROUTING_UNCONFIGURED, rompiste el diagnóstico") — `any` habría hecho que UNA sola ruta sin
  loguear, en un catálogo con problemas genuinamente distintos, mintiera "solo te falta loguearte".
- **AC-08: mostrar el diff completo de `config.toml` resaltado (color/marcador) en vez de una línea
  aparte.** Rechazada por alcance — este paquete no toca terminal rendering/color; una línea de texto
  plano, greppable, con prefijo fijo, ya resuelve "el harness lo dice" sin tocar la salida existente
  de `--preview` (que sigue intacta, íntegra, para quien la quiera leer completa).
- **AC-08: extender el mismo mecanismo a `opencode.json`/`settings.json`.** Fuera de alcance de este
  paquete — el defecto medido y las líneas citadas en el context pack son específicamente
  `model`/`model_reasoning_effort` de Codex; `opencode.json`'s bloque `provider.*` ya tiene su propio
  mecanismo de preservación de valor de usuario (ADR-0042/PKG-4, `providers.toml`), un eje distinto.

## Consecuencias

- `install.sh --yes` termina siempre que `opencode` esté instalado y sin credenciales — antes colgaba
  indefinidamente. Comportamiento interactivo (sin `--yes`) sin cambios.
- `route()` puede devolver un `reason_codes` de dos elementos donde antes era de uno
  (`("NO_ELIGIBLE_ROUTE", "ROUTING_UNCONFIGURED ...")`) exactamente cuando el catálogo entero fue
  excluido por falta de credenciales — `execution_enabled`/`ok`/exit code no cambian. Cualquier
  consumidor que comparaba `reason_codes` con igualdad exacta de tupla en ese escenario específico
  necesita el mismo ajuste que `tests/test_routing.py` ya recibió aquí.
- `install.py`/`--preview` imprime una línea nueva, `CODEX_GLOBAL_MODEL_CHANGE`, sólo cuando el valor
  vivo de `model`/`model_reasoning_effort` va a cambiar de verdad contra uno preexistente — nunca en
  un bootstrap sin config.toml previo, nunca en una reinstalación estable.

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C3-implementer.md` — tabla AC→cambio→prueba, el rojo
mordido de cada test nuevo (neutralizado, confirmado en rojo, revertido), la corrida en vivo de
`timeout 5 bash install.sh --yes` (antes: 3153 llamadas, `EXIT=124`; después: 1 llamada, `EXIT=0`), el
`--preview` de 565KB/96 archivos con el hunk de `config.toml` en la línea 9487 (antes) contra la línea
`CODEX_GLOBAL_MODEL_CHANGE` sola (después), y los cuatro gates.
