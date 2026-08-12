# Context pack — P2-gates-que-no-callan (ADR-0041)

Spec: `docs/specs/021-gates-que-no-mienten-ni-callan/spec.md`, **AC-06..AC-09**. P1 está en
review; este paquete no depende de su código.

## El defecto, medido

Cuatro agentes murieron en esta sesión con `Agent stalled: no progress for 600s`, todos
mutadores de corrida larga. La causa está verificada:

```
$ timeout 25 bash -c 'python3 -m unittest discover -s tests -v 2>&1 | tail -3'
(cortado por timeout: CERO bytes emitidos en 25s)
```

Sin el pipe, `unittest -v` emite línea por línea. Con `| tail -N`, **cero bytes hasta el final**,
y la suite tarda 7-10 minutos.

## La causa raíz NO es la que parece — leé esto antes de diseñar

El primer diagnóstico decía "el pipe bufferea por bloques". **Es falso.** El challenge lo
verificó con un escritor sin buffering (loop de `echo` + `sleep`): `| tail -3` **igual** se
cuelga hasta EOF. `tail -N` sin `-f` **estructuralmente no puede emitir nada hasta ver el fin
del stream**, sea cual sea el buffering upstream.

Consecuencia directa, verificada por el orquestador:

```
$ timeout 8 bash -c 'stdbuf -oL python3 -u -c "...print con flush..." | tail -3'
  NO emitio nada: stdbuf NO arregla tail -N
```

**El remedio no es `stdbuf`.** Es no poner `tail -N` en la cadena de un comando largo: escribir
a archivo y leerlo después, o dejar que la salida fluya.

Portabilidad, además: `stdbuf` es GNU y **no existe en macOS/BSD**, donde el CI corre
(`.github/workflows/*.yml:22-30`, job `verify-macos`). Si nombrás una herramienta, que sea
`python3 -u` o `PYTHONUNBUFFERED=1`.

## AC-09 es prevención, no corrección — y esto importa

El orquestador afirmó que el patrón `| tail -N` estaba en los context packs que había escrito.
**Era falso y está verificado**: `grep -rnE "\| *tail\b"` sobre `Global/_canonical/` y sobre los
context packs de 019 y 020 da **cero**. El patrón vivía en texto efímero de spawn, no en
archivos versionados.

O sea que el test **no arregla nada existente**: fija hacia adelante que no aparezca. Escribilo
así en la evidencia; no lo presentes como si hubiera un defecto documentado que estás cerrando.

**Patrón exacto, ya fijado, no a tu criterio**: `\| *tail\b`, anclado al pipe literal. Un `grep`
ingenuo por `tail` da **10 falsos positivos hoy**, todos dentro de "detail"/"details"
(`Global/_canonical/agents/architect.md:51`, `package-reviewer.md:35,51`, …).

## AC-06 — cómo se testea el umbral

Un subproceso **sintético** que emite con pausas conocidas, con las líneas timestampeadas al
leerlas, y un umbral reducido. **No** la suite real: no vuelvas los tests más lentos para probar
que algo es rápido.

## AC-08 — el límite que hay que escribir

El watchdog de 600 s **pertenece al runtime del agente, no a este repositorio**. Esta feature no
lo puede cambiar. Lo que el repo controla es **no crear la condición** que lo dispara. Sin esa
aclaración escrita, el próximo que lea "arreglamos los stalls" va a creer que no pueden volver a
pasar.

## Restricciones

- Extendé `docs/adr/0041-build-check-verifies-global.md` (lo escribió P1), no crees uno nuevo:
  es la segunda mitad de la misma decisión. Y **corregí ahí la causa raíz**, para que nadie
  "arregle" un stall de `tail` con `stdbuf` y siga muerto.
- Tras tocar `Global/_canonical/`: `./build.sh` y después `./build.sh --check` — que **ahora sí
  compara de verdad** contra los cuatro árboles (ADR-0041, P1). Si te da `GLOBAL_TREE_DRIFT`, te
  faltó el `build.sh`.
- `tests/test_harness.py` assertea frases doctrinales por grep: `grep -n` antes de mover nada.
  P1 agregó tests ahí; vas a compartir archivo.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para mordidas: `cp` y `cp`.
- No relajes, saltees ni borres tests. Base **972 OK / 3 skips**.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**) · `./ai/scripts/verify.sh`
→ `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` ·
`git diff --check` limpio.

Y aplicate el arreglo a vos mismo: **no pipees los gates a `tail`**. Es el defecto que estás
cerrando.

## Advertencia de proceso

Esta sesión acumula **seis afirmaciones de verificación que no resistieron la re-ejecución** —
cinco de subagentes y **una del propio orquestador** (la nota que decía que `setup_models.py` no
había que tocarlo; el implementer de P1 la desmintió corriendo el comando). **Cada bloque que
pegues es literal, o está marcado como recortado.** Si no lo corriste, "sin verificar".

Y hubo **un test decorativo** en tres de los cinco paquetes de 019 y en P1 de 020. Por cada test
nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.

## Evidencia

`docs/specs/021-gates-que-no-mienten-ni-callan/evidence/P2-implementer.md`: tabla AC → cambio
(`archivo:línea`) → prueba; la medición del intervalo máximo sin emitir, antes y después; los
falsos positivos del grep probados en las dos direcciones; la mordida por test; y los gates.

## Checkpoint

Murieron cuatro instancias por stall en esta sesión — es literalmente el tema de este paquete.
Escribí la evidencia en el primer minuto y guardá a disco a medida que avanzás.

## Fuera de alcance

P1 (el `--check`, ya implementado y en review) · acelerar la suite (que tarde 7-10 minutos es
otro problema; este es que calle) · el watchdog del runtime · todo lo de las features 022-025.
