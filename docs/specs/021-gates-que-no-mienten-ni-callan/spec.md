# 021 — Gates que no mienten ni callan

- **Estado**: aprobado por pedido directo de Federico (2026-08-12): *"Arregla el build.sh
  --check y los cuatro stalls de infraestructura"*.
- **Origen**: dos defectos encontrados con evidencia al cerrar 020; el segundo, causado en
  parte por la propia doctrina del harness.
- **ADR**: 0041.

## Los dos defectos, medidos

### D-1 — `build.sh --check` no compara nada de `Global/`

`build.sh:76-97`: genera los cuatro árboles en un `STAGING` temporal y después, en el modo
`check`, **solo compara dos archivos de self-scaffold** (`feature-state.py`,
`check-owned-paths.py`) entre `PROYECTO/ai/scripts/` y `ai/scripts/`. El `STAGING` recién
generado **nunca se compara contra `Global/`**. El `CHECK_PASS` que uno lee lo imprime
`generate.py` al generar, no una verificación de drift.

El modo `--diff` (`:99-104`) sí hace `diff -ruN` contra los cuatro árboles. `--check` no.

Consecuencia medida: durante 019 y 020 se registraron **decenas de gates** con la evidencia
`./build.sh --check → CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2` como prueba de "sin
drift". Ninguno probaba eso. El delta review de 020/P2 detectó 2 líneas de drift latente en
`Global/*` que ese gate no vio.

### D-2 — la suite enmascara el drift que el gate debería encontrar

`verify.sh:24-28` **sí** hace la comparación real (`diff -ruN "Global/$harness"
"$STAGING/$harness"` para los cuatro). Pero corre **después** de la suite completa
(`:18`), y la suite invoca `run("./build.sh")` en modo generate decenas de veces
(`tests/test_harness.py:129-130,2741,3012,…`), que hace `rm -rf Global/$harness; cp -a
$STAGING/$harness Global/$harness` **sobre el árbol real**. Para cuando `verify.sh` compara,
el drift ya fue corregido por sus propios tests.

Medido por el delta review de 020/P2: `git diff --stat` daba `6049 insertions` antes de la
suite y `6047` después.

### D-3 — el modo recomendado de correr los gates deja al que los corre mudo

Cuatro agentes murieron en la sesión del 2026-08-11 con `Agent stalled: no progress for
600s`, todos mutadores de corrida larga. Causa verificada:

```
$ timeout 25 bash -c 'python3 -m unittest discover -s tests -v 2>&1 | tail -3'
(cortado por timeout: CERO bytes emitidos en 25s)
```

El pipe bufferea por bloques: `... | tail` no emite **un solo byte** hasta que el comando
termina, y la suite tarda 7-10 minutos. Sin pipe, `unittest -v` sí emite línea por línea
(verificado). El patrón `| tail -N` está recomendado en los context packs que el propio
orquestador escribió y fue usado por los agentes que murieron.

**Límite honesto**: el watchdog de 600s pertenece al runtime del agente, **no a este
repositorio**. Esta feature no lo puede cambiar. Lo que sí puede es dejar de crear la
condición que lo dispara.

## Paquetes y criterios

### PKG-1 — `P1-check-que-verifica` (`generacion-arboles`)

- **AC-01**: `build.sh --check` compara el `STAGING` recién generado contra los cuatro
  árboles de `Global/` y **falla con `rc` distinto de cero** si difieren, nombrando los
  archivos.
  **Perfil de comparación FIJO — decisión de Federico (2026-08-12), no re-litigable**: la
  comparación se hace **siempre con `--profile go-zen`**, ignorando el `active-profile`
  local. Razón (F-01 del challenge, verificada): `active-profile` está en `.gitignore` y se
  resuelve por máquina (`models_config.auto_profile()`, `ai/scripts/models_config.py:269-286`);
  los perfiles difieren en **19 archivos**; y `Global/` está commiteado bajo `go-zen`. Con
  perfil local, `install.sh:370` fallaría en toda máquina sin el par "go" vivo —rompiendo el
  onboarding— y `setup_models.py:397,570` fallaría en todo cambio de modelo, que es su
  propósito entero. Con perfil fijo, el gate responde la pregunta correcta: *¿lo commiteado
  en `Global/` es lo que genera `_canonical`?* — que es de repositorio, no de máquina.
  **Reutilizá el `diff` de `verify.sh:26-28`, no el de `--diff`** (F-08): `--diff`
  (`build.sh:99-104`) lleva `|| true` y **siempre sale 0** — es un modo "mostrame", no un
  gate.
- **AC-02**: la salida distingue las dos verificaciones. `SELF_SCAFFOLD_SYNC_OK files=2` hoy
  se lee como "sin drift" y no lo es: tiene que quedar claro qué cubre cada línea, y que el
  árbol está sin drift **solo** cuando ambas pasan.
- **AC-03**: test que **prueba el defecto**: se ensucia un archivo de `Global/` y
  `./build.sh --check` tiene que fallar. Debe fallar en rojo contra el `build.sh` de hoy —
  hoy pasa en verde con el árbol sucio, que es el bug.
- **AC-04**: la suite deja de enmascarar el drift. **La vía es el ORDENAMIENTO, no la
  reescritura** (F-02/F-03 del challenge): `verify.sh` ya corre `--check` en `:6` y la suite
  en `:17`, así que una vez que `--check` compare de verdad (AC-01), el drift se detecta
  **antes** de que la suite lo pise — sin tocar ninguno de los 17 call sites. El challenger
  los leyó uno por uno: los 17 regeneran `Global/` por la misma razón (necesitan leer
  contenido fresco de `ROOT/Global/<harness>/` para assertear algo de `generate.py`).
  Lo que este AC agrega es **fijar el orden como regla**: `./build.sh --check` corre SIEMPRE
  antes que la suite cuando ambos se citan como evidencia de gate, sea vía `verify.sh` o
  sueltos. Hay precedente real de citarlos sueltos (`HANDOFF-PASO9.md:103`) y un job de CI
  que corre la suite sola (`.github/workflows/*.yml:32-51`, `windows-bootstrap`).
  **Si en package-planning se demuestra que el ordenamiento no alcanza, eso es
  `HUMAN_DECISION_REQUIRED`** — no se reescriben los 17 sitios por las dudas. Federico pidió
  arreglar dos cosas puntuales, no abrir un frente.
- **AC-05**: los gates registrados con evidencia falsa durante 019 y 020 quedan anotados. No
  se re-abren esas features: se registra una decisión que diga qué probaba realmente ese
  gate, para que nadie lea esa evidencia como lo que no fue.

### PKG-2 — `P2-gates-que-no-callan` (`consola` / doctrina)

- **AC-06**: un modo de correr los gates que **nunca** quede más de ~60s sin emitir. La forma
  la decide el ADR (flag de `verify.sh`, wrapper, o heartbeat). **Cómo se testea** (F-09): un
  subproceso sintético que emite con pausas conocidas, con las líneas timestampeadas al
  leerlas, y un umbral reducido para no volver la suite más lenta — no la suite real.
- **AC-07**: la doctrina fija el patrón correcto para correr comandos largos.
  **La causa raíz es otra de la que se creía** (F-04, verificado): no es buffering del
  escritor sino que **`tail -N` sin `-f` no puede emitir nada hasta ver el EOF**, sea cual
  sea el buffering upstream. Comprobado: `stdbuf -oL <cmd> | tail -3` se cuelga **igual**.
  Por lo tanto el remedio **no** es `stdbuf`: es **no poner `tail -N` en la cadena** de un
  comando largo — escribir a archivo y leerlo después, o dejar que la salida fluya.
  Portabilidad (F-06): si se nombra alguna herramienta, `stdbuf` es GNU y **no viene en
  macOS/BSD**, donde el CI corre (`.github/workflows/*.yml:22-30`, job `verify-macos`); usar
  `python3 -u` / `PYTHONUNBUFFERED=1`, que son portables.
- **AC-08**: queda escrito —en el ADR y en la doctrina— que el watchdog es del runtime del
  agente y no de este repo, y que lo que el repo controla es no crear la condición. Sin esa
  aclaración, el próximo que lea "arreglamos los stalls" va a creer que no pueden volver a
  pasar.
- **AC-09**: **prevención hacia adelante, no corrección de un defecto documentado** (F-05).
  El orquestador afirmó que el patrón `| tail -N` estaba en los context packs que escribió;
  el challenger lo desmintió y el orquestador lo verificó: `grep -rnE "\| *tail\b"` sobre
  `Global/_canonical/` y sobre los context packs de 019 y 020 da **cero** ocurrencias. El
  patrón vivía en texto efímero de spawn, no en archivos versionados. El test, entonces, no
  arregla nada existente: **fija hacia adelante** que no aparezca.
  **Patrón exacto, fijado acá y no a criterio del implementador** (F-07): `\| *tail\b`
  anclado al pipe literal. Un `grep` ingenuo por `tail` da **10 falsos positivos hoy**, todos
  dentro de "detail"/"details" (`Global/_canonical/agents/architect.md:51`,
  `package-reviewer.md:35,51`, …).

## No-goals

- No se toca el watchdog del runtime del agente: no está en este repo.
- No se reabren 019 ni 020: sus gates quedan anotados, no invalidados.
- No se acelera la suite. Que tarde 7-10 minutos es otro problema; este es que calle.
- No se convierte `check-anchors` en gate (no-goal heredado de 020).

## Riesgos

1. **AC-04 es el riesgo real**: los tests que corren `build.sh` contra el árbol real lo
   hacen por algo, y cambiarlos puede romper cobertura genuina. Entender **por qué** cada
   uno lo hace antes de tocarlo; si la respuesta no está clara, no tocarlo y documentar.
2. Cambiar el `rc` de `build.sh --check` puede romper a quien lo invoque esperando 0:
   `grep -rn "build.sh --check"` antes.
3. `tests/test_harness.py` assertea frases doctrinales por grep: toda frase nueva o movida
   necesita su test y un `grep -n` previo.

## Gates

Por paquete: `python3 -m unittest discover -s tests` en verde (**`pytest` no está
instalado**; base **970 OK / 3 skips**), `./build.sh --check` sin drift **con su semántica
nueva**, ACs con evidencia `file:line`. Review independiente, repair consolidado, delta
review.

## Criterio de cierre

Ensuciar un archivo de `Global/` y que `./build.sh --check` falle; correr la suite completa
y que `git diff --stat` **no cambie** por efecto de la propia suite; y correr los gates
midiendo que ningún intervalo sin salida supere el umbral.
