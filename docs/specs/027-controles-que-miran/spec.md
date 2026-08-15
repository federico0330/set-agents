# 027 — Controles que miran

- **Estado**: aprobado por pedido directo de Federico (2026-08-14): *"fixea esas seis guardas antes
  de pushearlo"*.
- **Origen**: cuatro defectos latentes que las features 022-026 encontraron **sin buscarlos**,
  registrados con medición y deliberadamente no reparados en el paquete que los descubrió — porque
  el paquete que un control acaba de aprobar no puede ser el que repara el control.
- **ADR**: 0051.

## Precisión sobre el conteo

Las **cinco guardas falsas-verdes** que aparecieron en la sesión (dos en 022/P1, dos en 022/P3, una
en 023/B3) **ya están reparadas** dentro de sus propios paquetes, cada una con su mordida en las dos
direcciones. Esta feature **no las re-abre**.

Lo que queda abierto son **cuatro defectos de la misma familia** más uno flageado por 026/P2. Todos
comparten la forma: *algo que informa OK sobre algo que no mira*.

## Los defectos, medidos

### D-1 — `check-owned-paths.py` no ve los archivos nuevos

`check-owned-paths.py:40-42` obtiene los archivos cambiados con `git diff --name-only <baseline> --`,
que **no lista archivos sin trackear**.

Reproducido el 2026-08-14: se creó `ai/scripts/_probe_new_file.py` y el chequeo lo ignoró
(`ve _probe_new_file.py? False`). En 022/P1 pasó de verdad: el paquete creó
`ai/scripts/provider_registry.py` —el archivo central, el registro del que derivan siete tablas— y
el control de alcance **guardó silencio**.

Un paquete puede crear cualquier archivo, en cualquier lugar del repo, y el control nunca lo nota.

### D-2 — Los módulos de test no pasan aislados

`python3 -m unittest tests.test_harness` da **118 errores**. La suite entera pasa porque algún
módulo parchea `sys.path` antes que los demás y el resto se beneficia del efecto colateral.

**Medido y descartado como regresión**: en el commit `b119ca7`, antes de 022, el mismo comando daba
**120 errores y 2 fallos**. Es preexistente, y 022 lo dejó levemente mejor.

Un CI que corra módulos por separado, o cualquiera que corra un test dirigido, ve rojo.

### D-3 — Un test puede escribir en el estado real del usuario, y lo hizo

Durante 024/C2 un test sin mockear escribió en `~/.local/state/set-agentes/` y **perdió una entrada
de la configuración real** (`ollama = false`). El implementer lo detectó, lo corrigió y lo reportó
por su cuenta.

**El defecto no es del agente: es que sea posible.** Cualquiera que corra la suite en su máquina
puede mutarse la configuración.

### D-4 — El gate de credenciales de pi corre después del subproceso

`_probe_pairs` ejecuta `pi --list-models` y **recién después** consulta
`pi_auth_provider_keys()`. El resultado observable es correcto —el par queda excluido— pero se paga
el subproceso, que puede bloquear hasta `PI_PROBE_MIN_TIMEOUT_SECONDS` (60 s), aunque la credencial
ya se sepa inválida.

**Preexistente y deliberado**: en `b119ca7` el comentario lo declara *"Belt-and-suspenders… a cheap,
non-subprocess signal ALONGSIDE the naturally fail-closed column-parse below"*. Adelantarlo cambia
el comportamiento de pi y por eso necesita su propio review.

### D-5 — `_decide_status` no filtra los códigos de modelo

Flageado por el implementer de 026/P2: `routing_cli.py` no filtra `MODEL_PINNED` ni
`MODEL_REQUEST_*` en las decisiones de review. `grep` da **cero menciones**.

## Paquetes

### PKG-1 — `alcance-y-aislamiento`

- **AC-01**: `check-owned-paths.py` ve los archivos **nuevos**. Un archivo sin trackear creado
  dentro del paquete cuenta como cambio, y si está fuera de `owned_paths` da `OWNERSHIP_FAIL`.
  Test que falle contra el código de hoy.
- **AC-02**: los módulos de test pasan **aislados**. La forma la decide el implementador —`conftest`,
  un `sys.path` explícito por módulo, un runner— pero el criterio es medible:
  `python3 -m unittest tests.test_harness` y `tests.test_routing` por separado, ambos verdes.
- **AC-03**: un test que corra `./build.sh --check` o el gate de aislamiento **falla** si alguien
  vuelve a romperlo.

### PKG-2 — `nada-escribe-afuera`

- **AC-04**: **ningún test puede escribir fuera de un directorio temporal.** Guarda que falle
  ruidosamente, al estilo del candado de DDL de 023/B3 (`test_canonical_ddl_is_pinned_to_schema`),
  que nació exactamente de este tipo de agujero.
  El caso real a cubrir: `STATE_DIR` del usuario (`~/.local/state/set-agentes/`) y sus
  configuraciones de CLI (`~/.claude`, `~/.codex`, `~/.pi`, `~/.config/opencode`).
- **AC-05**: la guarda se prueba en las dos direcciones: un test que escribe en `tmp` pasa; uno que
  escribe en `$HOME` **falla nombrando el archivo**.

### PKG-3 — `gates-que-preguntan-antes`

- **AC-06**: el gate de credenciales de pi corre **antes** del subproceso. Se conserva el
  belt-and-suspenders: el parse de columnas sigue siendo fail-closed; lo que cambia es no pagar el
  subproceso cuando la credencial ya se sabe inválida. Test que mida que **no** se ejecuta el
  subproceso en ese caso.
- **AC-07**: `_decide_status` filtra `MODEL_PINNED` y `MODEL_REQUEST_*` en las decisiones de review,
  igual que ya filtra los demás códigos informativos.

### PKG-4 — `owned-paths-matchea-directorios`

Descubierto **por** PKG-1: al hacer que el control vea los archivos nuevos, quedó a la vista un
falso positivo que antes estaba tapado.

- **AC-08**: un directorio en `owned_paths` matchea los archivos que contiene.
  Medido el 2026-08-14: `matches("tests/test_harness.py", ["tests"])` devuelve **False**, y lo
  mismo `matches("docs/adr/0051-x.md", ["docs/adr"])` y con barra final (`["tests/"]`). Es
  `fnmatch` sobre patrones "pelados", que no descienden.
  Consecuencia medida: el gate de PKG-1 reporta **18 archivos fuera de alcance**, entre ellos
  `tests/test_harness.py` y `tests/__init__.py`, que **están** en sus `owned_paths`.
  Es el espejo del defecto que PKG-1 arregló: antes callaba sobre lo que debía marcar; ahora
  marca lo que no debe.
- **AC-09**: la corrección **no puede aflojar** el control. Un archivo genuinamente fuera de
  alcance sigue dando `OWNERSHIP_FAIL`. Test en las dos direcciones, y el caso borde de un
  directorio cuyo nombre es prefijo de otro (`tests` no matchea `tests-extra/x.py`).

## No-goals

- No se re-abren las cinco guardas falsas ya reparadas.
- No se toca el sort key.
- No se cambia el comportamiento observable de pi más allá de no pagar un subproceso inútil.
- No se resuelve el codename de cliente de 024: eso es `HUMAN_DECISION_REQUIRED` y sigue abierto.

## Riesgos

1. **AC-02 puede tocar muchos archivos de test.** Si arreglar el aislamiento exige editar decenas de
   módulos, parar y reportar: hay soluciones de una línea (un `conftest`) y soluciones de cien.
2. **AC-04 puede volverse un falso positivo.** Un test legítimo que escriba en un `TemporaryDirectory`
   bajo `/tmp` no puede fallar. La guarda mira **destino**, no intención.
3. **AC-06 cambia el orden de un gate.** El resultado observable tiene que ser idéntico en las dos
   direcciones: credencial válida ⇒ el par se probea igual; inválida ⇒ excluido, ahora sin subproceso.

## Gates

Por paquete: suite en verde (**`pytest` no está instalado**; base **1117 OK / 3 skips**),
`./ai/scripts/verify.sh` → `VERIFY_PASS`, `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS`, ACs con evidencia `file:line`. Review independiente en otro proveedor, repair
consolidado, delta review.

## Criterio de cierre

Crear un archivo nuevo fuera de `owned_paths` y que `check-owned-paths.py` **lo vea**. Correr
`tests/test_harness.py` **solo** y que dé verde. Escribir en `$HOME` desde un test y que la suite
**falle nombrando el archivo**. Y que una credencial de pi inválida **no** dispare el subproceso.
