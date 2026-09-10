# 049 — Criterios de aceptación (BDD)

Estos escenarios prueban `049-model-identity/v0.3.0`. Los modelos de fixture son strings opacas; ningún escenario presume un catálogo.

## Flujo observable

```text
persona → --model-state / Modelos → runtime primario + orchestrator
                                      ├─ OpenCode sólo si runtime=opencode
                                      ├─ SET efectivo → default deseado
                                      ├─ artefacto releído → instalado
                                      └─ pins → routing futuro
cambiar default → lock exclusivo → persistir → instalar → releer → aplicado | pendiente
home simple → acción directa Modo experto | Actualizar estado → fresh | stale/error
```

## AC-01 — raíz canónica, orden y privacidad

**Given** un proyecto canónico P, raíces P vieja/nueva, una hija más nueva, P2 y filas desordenadas

**When** se ejecuta `set-agents --model-state --project P --json`

**Then** sólo participan raíces cuya ruta canónica es exactamente P; hija y P2 se excluyen

**And** se elige raíz por `updated_at` descendente y `session_id` sólo como desempate interno

**And** de la única raíz elegida se toma el último mensaje válido `user/submitted`, nunca assistant ni hija

**And** la salida usa “último envío observado”, no expone `session_id` y no contiene transcript.

*Fixture que engañaría:* una lista ordenada sin hijas. Debe mezclar raíces, empate, hija y proyecto con prefijo parecido.

## AC-02 — scope singular, modelos opacos y schema

**Given** runtime primario resuelto, rol `orchestrator`, deseado/instalado y routing

**When** se solicita `--model-state --json`

**Then** stdout contiene exactamente un objeto schema v1 para ese scope singular, sin selector/lista de roles o runtimes

**And** cada modelo es string opaca o `null`, sin catálogo ni nombre hardcodeado

**And** no aparece ninguna clave, enum o `session_id` no documentado.

**Given** runtime primario no OpenCode

**When** se solicita estado

**Then** `observed` es `unobserved` con reason `unsupported_runtime` y no se invoca OpenCode.

## AC-03 — argv, razón y primer estado

**Given** cualquier fuente degradada, cache ausente o primer arranque

**When** se emite estado humano o JSON

**Then** toda razón pertenece al único enum `ModelStateReason`

**And** antes de medir, cada `refresh.*.checked_at=null` y `reason=not_checked`.

**When** se combina `--model-state` con mutación, instalación, generación, routing, TUI, selector, posicional o proyecto inválido

**Then** termina rc 2, stderr humano, cero JSON parcial y cero mutaciones.

## AC-04 — observación acotada y degradación

**Given** OpenCode ausente, timeout, JSON inválido, más de 20 raíces candidatas, stdout acumulado mayor a 1 MiB, proyecto irresoluble o raíz sin `user/submitted`

**When** se solicita `--model-state`

**Then** termina rc 0 con `observed.status=unobserved` y reason único correspondiente

**And** usa sólo `opencode session list --format json --pure` y `opencode export --sanitize --pure`, deadline total 5 s, máximo 20 raíces y 1 MiB total de stdout

**And** no persiste ni reemite prompts, respuestas, tools, metadata no allow-listed ni IDs de sesión.

## AC-05 — `/model`, proyección y lock exclusivo

**Given** sesión abierta, fábrica F, overlay legal L y dos cambios concurrentes

**When** se usa `/model`

**Then** sólo cambian envíos posteriores y SET/artefactos permanecen byte-idénticos.

**When** el primer cambio confirmado persiste, genera efectiva, instala y relee

**Then** el lock exclusivo cubre toda esa secuencia y sólo readback exacto informa `applied`.

**When** llega el segundo cambio durante el lock

**Then** falla reintentable antes de mutar overlay, fábrica, instalación o sesión.

**And** `build --check`, `build --diff` y `Global/**` siguen factory-only; drift local usa L.

## AC-06 — fallo de aplicación

**Given** preferencia válida y un instalador/readback que falla después de persistir

**When** termina la aplicación

**Then** desired persiste, installed conserva última evidencia y convergence es `pending_apply`

**And** el reintento no modifica sesión abierta ni declara éxito falso.

## AC-07 — home, experto y refresh

**Given** cache válida, cache ausente/no escribible, primer arranque y spies de subprocess

**When** abre `./set-agents` hasta el primer frame

**Then** tarda menos de 300 ms, crea cero subprocesses y muestra acción directa `Modo experto` junto a Estado, Configurar, Modelos, Forma de trabajo y Salir

**And** no ejecuta ni fuerza onboarding automático o `first_run` de 048.

**When** se elige `Modo experto`

**Then** entra directamente a ingeniería existente, preservando renderer, paleta y jerarquía ADR-0075.

**When** `Actualizar estado` falla para una fuente y otra responde

**Then** la primera conserva último valor/timestamp como `stale` (o `error` sin valor), la segunda queda `fresh` y no hay traceback.

## AC-08 — restauración y plugins

**Given** pins, preferences, role overrides, biases, overrides locales, hosts y subscriptions

**When** se confirma “Dejar que el router elija”

**Then** sólo desaparecen pins.

**When** se confirma “Restaurar defaults de SET” desde el mismo fixture

**Then** sólo desaparecen overrides locales y hosts/subscriptions permanecen byte-idénticos.

**Given** plugin TUI ausente o externo con modelo estático

**When** Modelos lo detecta

**Then** es advertencia no autoritativa read-only: no hay backup, deshabilitación, edición ni borrado.

## AC-09 — integración

**Given** consola/modelos existentes y OpenCode 1.18.14 aislado

**When** corren tests relevantes, `./build.sh --check`, `./ai/scripts/verify.sh`, `git diff --check` y TTY aislada

**Then** quedan verdes sin debilitar pruebas y la TTY prueba observación o degradación segura.
