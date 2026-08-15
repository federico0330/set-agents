# 025 — Consola mínima y flexible

- **Estado**: aprobado por Federico (2026-08-12): *"quiero que la app de terminal sea más
  minimalista y sólo muestre lo transparente al usuario, sin muchos comandos ni caracteres raros…
  Y quita/oculta las opciones que al usuario no le agregan nada"*, más la expansión de menú y
  flexibilidad que dio por escrito.
- **Decisión ya tomada**: las flags internas **se ocultan del `--help` y siguen funcionando**.
- **ADRs**: 0050 (D1 superficie humana), 0053 (D2 trabajo visible), 0054 (D3 posturas de
  autonomía), 0055 (D4 harness por CLI), 0056 (D5 vault en todo spawn).

  > **Corrección de numeración, 2026-08-15.** Esta línea decía *"0049 (superficie humana), 0050
  > (posturas de autonomía)"*, y los dos números estaban mal: `0049` ya lo había tomado 024/C3
  > (`primer-arranque-honesto`) antes de que este paquete arrancara, y `0051`/`0052` los tomó 027
  > mientras 025 estaba detenida. Los context packs de D1 a D5, escritos después, asignaron el
  > bloque contiguo correcto y son los que siguieron los implementers. El orquestador desempató
  > a favor de los context packs. Registrado en `decisions-log.jsonl`.

## Estado medido

> **Números remedidos el 2026-08-15**, contra el estado del repo de hoy. Los originales de esta
> sección venían de una exploración del 2026-08-12 y quedaron viejos.

El menú son **10 ítems, todos con emoji**. El CLI expone **68 flags**. De cuántas son "de
diagnóstico interno" esta spec ya no da un número: el original decía 31, sin criterio escrito, y
el review independiente de D1 midió que las que un humano usa de verdad en su terminal son **15**,
con **22** si se incluyen las de diagnóstico defendibles. El corte lo decide el paquete con
evidencia por flag —menciones en documentación dirigida a humanos contra menciones en prompts de
agentes y en `coord_policy.SAFE_ARGV`—, no una cuota heredada.

`tui.py` tiene un picker sólido con detección de TTY pero **ningún spinner, animación ni progreso**.

De la skill `ui-ux-pro-max` —scopeada a web y mobile, cuyo grueso no aplica a una terminal—
transfieren tres reglas, y una es literal lo que se pidió: **no usar emoji como iconos
estructurales** (dependen de la fuente, rompen alineación, no se pueden tematizar), **empty states
que guían** en vez de vacío, y **errores que dicen causa y salida**.

## Paquetes

### PKG-1 — `superficie-humana`

- **AC-01**: menú sin emoji, jerarquía por **espaciado y peso**.
- **AC-02**: las 31 flags internas se ocultan del `--help` y **siguen respondiendo igual**.
  `coord_policy` las tiene en su allowlist y los spawns las invocan: **borrarlas rompe el harness**.
  `--help --avanzado` las muestra.
- **AC-03**: la salida JSON cruda de los comandos de routing pasa a texto humano por default, con
  `--json` para la máquina. Hoy `--route-doctor` escupe un JSON de una línea.

### PKG-2 — `trabajo-visible`

- **AC-04**: spinner o progreso para todo lo que tarde más de ~300 ms, degradando a texto plano sin
  TTY, con `NO_COLOR` y en pipes.
- **AC-05**: ninguna animación puede bloquear input ni ser el único indicador de estado.

### PKG-3 — `posturas-de-autonomia`

- **AC-06**: tres posturas elegibles, cada una con su explicación **en la propia pantalla**:

  | Postura | Qué hace |
  |---|---|
  | Autónoma | Usa MCPs, CLIs y skills por su cuenta; narra por hito |
  | Consultiva | Propone y espera confirmación en las acciones que mutan |
  | Todo consultado | Pregunta antes de cada delegación |

  Se apoya en doctrina que **ya existe** —ADR-0025 resolve-first, ADR-0037 resolvé antes de
  preguntar, la política MCP enable→use→disable— y la vuelve **un parámetro en vez de una
  constante**.
- **AC-07**: toggles de metodología con su explicación: **TDD estricto** (ya existe por paquete vía
  ADR-0022), **SDD** (existe como skill) y **RDD**.
- **AC-08**: **RDD queda definido en el vocabulario de Federico**: *Receipt Driven Development*
  (Gentleman Programming) — exigirle a la IA **recibos verificables** (logs, resultados de tests,
  ejecuciones reales) en vez de promesas. **El harness ya lo practica sin nombrarlo**: ADR-0026
  evidencia sobre memoria, las pruebas de mordida, la evidencia `file:line`. Este AC lo nombra, lo
  hace elegible, y **no reinventa lo que ya existe**.

### PKG-4 — `harness-por-CLI`

- **AC-09**: instalar el harness sólo en un CLI y dejar los otros vírgenes.
- **AC-10**: desinstalarlo de uno sin tocar los otros. La base ya está: `install.py` tiene
  manifiesto, poda de huérfanos, backup con rotación y rollback — y desde 022/P4, **poda de
  subárboles JSON que jamás toca una clave ajena**. Falta la superficie de desinstalación selectiva.
- **AC-11**: usar un CLI virgen "por esta vez", sin desinstalar.

### PKG-5 — `vault-en-todo-spawn`

- **AC-12**: que cada spawn de proyecto use Obsidian, para que los agentes se comuniquen entre sí.
  ADR-0012 ya declara el vault obligatorio y existen `--vault-init`, `--vault-link`,
  `--vault-doctor`. **Este paquete arranca verificando qué parte de eso se cumple hoy en un spawn
  real** — no asumiendo que basta con que el ADR lo diga.

## No-goals

- **No se borran las 31 flags**: se ocultan. Borrarlas rompe los spawns.
- No se toca el ruteo ni el sort key.
- No se implementa la app de escritorio ni el chatbot propio: es visión a más largo plazo. Esta
  feature la **habilita** dándole superficie presentable, no la ejecuta.

## Riesgos

1. **Ocultar una flag que un spawn invoca.** Mitigado: se ocultan del `--help`, no del parser, con
   test de que cada una sigue respondiendo.
2. **Que el spinner rompa la salida en CI.** Mitigado por AC-04: degradación sin TTY, `NO_COLOR` y
   pipes, con test.
3. **Que las posturas queden decorativas.** El riesgo real: que "consultiva" no cambie ninguna
   conducta. Cada postura necesita un test que pruebe una diferencia observable.

## Gates

Por paquete: suite en verde, `verify.sh` → `VERIFY_PASS`, `build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, ACs con evidencia `file:line`. Review independiente,
repair, delta review.

## Criterio de cierre

Recorrer el menú entero sin encontrar un emoji ni una salida JSON cruda; que toda operación de más
de 300 ms muestre progreso; desinstalar el harness de un CLI verificando que los otros tres quedan
intactos; y que un spawn real de proyecto tenga su vault.
