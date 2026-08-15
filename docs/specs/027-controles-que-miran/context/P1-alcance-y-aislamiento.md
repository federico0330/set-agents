# Context pack — P1-alcance-y-aislamiento

Spec: `docs/specs/027-controles-que-miran/spec.md`, **AC-01, AC-02, AC-03**.

## Los dos defectos, reproducidos hoy

### AC-01 — el control de alcance no ve los archivos nuevos

`ai/scripts/check-owned-paths.py:40-42` usa `git diff --name-only <baseline> --`, que **no lista
archivos sin trackear**.

Reproducido el 2026-08-14: se creó `ai/scripts/_probe_new_file.py`, se corrió el chequeo, y devolvió
`ve _probe_new_file.py? False` con `out_of_scope: 3` — los tres de siempre, sin el nuevo.

**Pasó de verdad**: en 022/P1 el paquete creó `ai/scripts/provider_registry.py` —el registro del que
derivan siete tablas, el archivo central del paquete— y el control **guardó silencio**.

### AC-02 — los módulos de test no pasan aislados

`python3 -m unittest tests.test_harness` da **118 errores**, por `ModuleNotFoundError` de módulos que
viven en `ai/scripts/`. La suite entera pasa porque algún módulo parchea `sys.path` primero y el
resto se beneficia del efecto colateral.

**Es preexistente, medido**: en un checkout limpio de `b119ca7` el mismo comando daba **120 errores y
2 fallos**. No lo introdujo 022.

## TAREA

**AC-01** — Que el chequeo vea los archivos nuevos. `git status --porcelain` los lista; `git diff`
no. Un archivo sin trackear dentro del paquete cuenta como cambio, y fuera de `owned_paths` da
`OWNERSHIP_FAIL`.

**Test que falle contra el código de hoy**: escribilo antes del arreglo y confirmá el rojo.

**AC-02** — Que los módulos pasen aislados. La forma la elegís vos, pero el criterio es medible:
`python3 -m unittest tests.test_harness` y `tests.test_routing` **por separado**, ambos verdes.

**Si arreglar esto exige editar decenas de módulos, pará y reportá.** Hay soluciones de una línea
—un `conftest`, un `sitecustomize`, un `tests/__init__.py` que ajuste `sys.path`— y soluciones de
cien. Elegí la de una y decí por qué.

**AC-03** — Un test que **falle** si alguien vuelve a romper el aislamiento.

## La trampa

`check-owned-paths.py` es el control que aprueba el alcance de los paquetes. **Si tu arreglo lo
vuelve más estricto de golpe, todos los paquetes en vuelo empiezan a fallar** — incluido el tuyo.

Verificá qué reporta sobre el estado actual del repo **antes** de cambiarlo, y si el cambio genera
ruido legítimo, decilo en la evidencia en vez de relajar la regla.

## Restricciones

- **ADR-0051** (`ls docs/adr/` para confirmar que está libre, indexalo en `docs/adr/README.md`).
- **No relajes ningún test** para que el aislamiento pase.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques nada bajo `~`.**
- **No toques `README.md`**: el orquestador lo está reescribiendo en paralelo.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1117 OK / 3 skips**)
· `python3 -m unittest tests.test_harness` **solo** · `python3 -m unittest tests.test_routing`
**solo** · `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041). Cuatro agentes ya lo violaron esta noche y tuvieron que repetir.

## Evidencia

`docs/specs/027-controles-que-miran/evidence/P1-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **el chequeo viendo un archivo nuevo, antes y
después**; los dos módulos corriendo aislados con su conteo; qué reportaba el chequeo sobre el repo
antes del cambio; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** Ya van
cinco guardas huecas en este proyecto. No escribas la sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

La guarda de escritura fuera de `tmp` (P2) · el gate de pi y `_decide_status` (P3) · el sort key · el
codename de cliente de 024, bloqueado esperando decisión humana · `README.md`.
