# ADR-0041 — `build.sh --check` compara de verdad, con perfil fijo, y el orden de gates queda escrito

- Estado: Accepted (2026-08-12). Feature 021-gates-que-no-mienten-ni-callan, PKG-1
  (`P1-check-que-verifica`).

## Contexto

`build.sh:76-97` (antes de este ADR): el modo `check` genera los cuatro árboles en un `STAGING`
temporal y después **solo compara dos archivos de self-scaffold** (`feature-state.py`,
`check-owned-paths.py`) entre `PROYECTO/ai/scripts/` y `ai/scripts/`. El `STAGING` recién generado
**nunca se compara contra `Global/`**. El texto `CHECK_PASS: generated and validated profile X` que
se lee en la salida lo imprime `generate.py:730` al generar el `STAGING` (todo modo de `build.sh`
invoca `generate.py --output`, así que ese texto aparece siempre) — es "corrí sin explotar", no un
veredicto de drift.

El modo `--diff` (`build.sh:99-104`) sí hace `diff -ruN` contra los cuatro árboles, pero lleva
`|| true` en cada línea: **siempre sale 0**. Es un modo "mostrame", no un gate.

Consecuencia medida: durante las features 019 y 020 se registraron decenas de gates citando
`./build.sh --check → CHECK_PASS + SELF_SCAFFOLD_SYNC_OK files=2` como prueba de "sin drift".
Ninguno probaba eso — el delta review de 020/P2 detectó 2 líneas de drift latente en `Global/*`
que ese gate no vio (ver AC-05 más abajo).

Un segundo defecto relacionado (D-2 de la spec): `verify.sh` corre `--check` en `:6` y la suite
completa en `:17`; la suite invoca `./build.sh` en modo generate decenas de veces
(`tests/test_harness.py`), que sobrescribe `Global/$harness` con lo recién generado. El drift real
existe entre el `:6` y el `:17` de una corrida de `verify.sh`, pero para cuando algo lo mira ya fue
"corregido" por los propios tests de la suite — nunca queda como falla visible.

## Decisión

### 1. El perfil de comparación es FIJO: siempre `go-zen`, nunca el `active-profile` local

`build.sh --check` genera un árbol de comparación **dedicado**, con `generate.py --profile
go-zen` explícito, **ignorando** tanto la variable `$PROFILE`/flag `--profile` que el usuario le
haya pasado a `build.sh` como el archivo `active-profile` (per-máquina, `.gitignore`, resuelto por
`models_config.auto_profile()`, `ai/scripts/models_config.py:269-286`).

Razón: `Global/` está commiteado bajo `go-zen`; los perfiles difieren en 19 archivos medidos por el
spec-challenge. Si `--check` usara el perfil local, se rompería en cualquier lugar donde ese perfil
no fuera `go-zen`:
- `install.sh:370` corre `"$ROOT/build.sh" --check` bajo `set -euo pipefail` durante el bootstrap,
  **antes** de que exista ningún par "go" autenticado — con perfil local reventaría el onboarding
  en toda máquina nueva.
- `ai/scripts/setup_models.py:397` (`subprocess.run([...,"--check"], check=False)`, wizard) y
  `:570` (`check=True`, modo `--plumbing`) corren `--check` después de escribir un cambio de
  modelo — con perfil local fallarían en **todo** cambio de modelo, que es exactamente el caso de
  uso que existen para cubrir.

Con perfil fijo, `--check` responde la pregunta correcta y única que puede responder de forma
determinística en cualquier máquina: *¿lo commiteado en `Global/` es lo que `generate.py` produce
para el perfil bajo el que está commiteado?* — una pregunta de repositorio, no de máquina. Los
modos `generate`/`diff`/`install` siguen honrando `$PROFILE`/`active-profile` sin cambios: siguen
siendo sobre "qué instalo en ESTA máquina", una pregunta distinta.

### 2. La comparación reutiliza el patrón `diff` de `verify.sh:26-28`, no el de `--diff`

`diff -ruN "$ROOT/Global/$harness" "$CHECK_STAGING/$harness"` para los cuatro árboles, sin `|| true`
— así que una diferencia hace que el bucle marque drift y el modo salga con `rc=1`, nombrando los
archivos que difieren en la salida estándar de `diff -ruN` (headers `---`/`+++` por archivo). El
modo `--diff` existente (`build.sh:99-104`) no se toca: sigue siendo el modo "mostrame" que nunca
falla, para inspección manual.

### 3. La salida distingue las dos verificaciones (AC-02)

`build.sh --check` corre dos chequeos independientes y AMBOS tienen que pasar para el veredicto de
"sin drift":

| Línea | Qué cubre |
|---|---|
| `SELF_SCAFFOLD_SYNC_OK files=2` / `SELF_SCAFFOLD_DRIFT file=... reason=...` | los dos scripts de self-scaffold (`feature-state.py`, `check-owned-paths.py`) entre `PROYECTO/ai/scripts/` y `ai/scripts/` — sin relación con `Global/`. |
| `GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4` / diffs nombrados + `GLOBAL_TREE_DRIFT profile=go-zen` | los cuatro árboles de `Global/` contra una generación fresca forzada a `go-zen` — el chequeo que faltaba. |
| `BUILD_CHECK_PASS` | solo aparece cuando **ambos** chequeos anteriores pasan. Reemplaza la lectura previa de `CHECK_PASS` (que era el auto-print de `generate.py` al generar el `STAGING`, no un veredicto). Ese auto-print de `generate.py` se silencia (`>/dev/null`) en el modo `check` específicamente, para que no se lea como un veredicto de segunda mano. |

Cualquier no-cero en cualquiera de los dos chequeos deja `rc=1` y **nunca** imprime
`BUILD_CHECK_PASS`.

### 4. AC-04 — el orden es la vía, no la reescritura de los 17 call sites

`verify.sh` ya corre `--check` en `:6` y la suite completa en `:17`. Con el punto 1-3 de este ADR,
`--check` ahora compara de verdad, así que el drift se detecta **antes** de que la suite lo pise —
sin tocar ninguno de los 17 call sites que regeneran `Global/` dentro de la suite (todos lo hacen
por la misma razón: necesitan leer contenido fresco de `ROOT/Global/<harness>/` para assertear algo
de `generate.py`, no para "arreglar" nada).

Regla fijada (doctrina, `TIPS-USO.md`): **`./build.sh --check` corre SIEMPRE antes que la suite
completa cuando ambos se citan como evidencia de un gate**, sea la secuencia interna de
`verify.sh` o invocaciones sueltas. Precedente real de citarlos sueltos:
`HANDOFF-PASO9.md:103` (`verify.sh → VERIFY_PASS`, `build.sh --check → SELF_SCAFFOLD_SYNC_OK
files=2`, como dos líneas de evidencia independientes). El job `windows-bootstrap`
(`.github/workflows/ci.yml:32-51`) corre la suite sola (no puede correr `build.sh`, que es bash) —
eso es aceptable porque **nunca** se cita como prueba de que `Global/` no tiene drift, solo de que
los scripts Python compilan y la suite pasa en Windows.

### 5. AC-05 — la evidencia histórica de 019/020 queda anotada, no reabierta

Los gates de 019 y 020 que citaron `./build.sh --check → CHECK_PASS` como "sin drift" no probaban
eso — probaban que `generate.py` corrió sin excepciones y que 2 archivos de self-scaffold
coincidían. Esas features no se reabren. La anotación de qué probaba realmente ese gate se registra
como decisión (`feature-state.py log-decision`, tier bajo un ADR formal) por el orquestador, no por
este ADR ni por este paquete — este documento dejaba constancia de la razón; el registro operativo
vive en `ai/state/decisions-log.jsonl` / `docs/notas/decisiones/`.

## Alternativas rechazadas

- **Perfil local (`active-profile`/`$PROFILE`) para la comparación de `--check`.** Rompe
  `install.sh:370` en todo onboarding sin el par "go" vivo y `setup_models.py:397,570` en todo
  cambio de modelo — ver punto 1.
- **Reescribir los 17 call sites de la suite que regeneran `Global/`.** Innecesario: el
  ordenamiento ya resuelve D-2 sin tocarlos, y cada uno regenera por una razón real (leer contenido
  fresco para su propio assert). Reescribirlos habría sido abrir un frente que Federico no pidió.
  Si en algún momento se demuestra que el ordenamiento no alcanza, es una decisión de producto
  (`HUMAN_DECISION_REQUIRED`), no algo que este paquete decida unilateralmente.
- **Usar el `diff` de `--diff` (`build.sh:99-104`) para el nuevo chequeo de `--check`.** Ese modo
  lleva `|| true` en cada línea y nunca falla — adaptarlo habría significado reescribirlo también;
  más simple y más claro reutilizar el patrón ya probado de `verify.sh:26-28`.
- **Reabrir 019/020 para corregir su evidencia.** No-goal explícito de la spec: se anota qué
  probaba realmente el gate, no se invalida el trabajo aceptado.

## Consecuencias

- `./build.sh --check` ahora falla (`rc=1`) si cualquier archivo de `Global/{opencode,claude-code,
  codex,pi}` difiere de lo que `generate.py --profile go-zen` produce, nombrando los archivos vía
  `diff -ruN`. Antes: `rc=0` siempre que los dos scripts de self-scaffold coincidieran, sin mirar
  `Global/` en absoluto.
- Los tres call sites que dependían de `rc=0` de `--check` (`install.sh:370`,
  `setup_models.py:397`, `setup_models.py:570`) se re-verificaron corriéndolos, no se asumió: ver
  `docs/specs/021-gates-que-no-mienten-ni-callan/evidence/P1-implementer.md`. De los tres, solo
  `install.sh:370` siguió funcionando sin tocarlo. **Los otros dos sí se rompían de verdad**:
  `setup_models.py` corre `--check` inmediatamente después de escribir un `models.toml` nuevo, antes
  de que nada regenere `Global/` a partir de ese cambio (eso lo hace `./build.sh` a secas, en un
  commit aparte) — con `--check` respondiendo ahora "¿`Global/` coincide con una generación fresca?"
  (punto 1 de este ADR), cualquier cambio de modelo real reportaba `GLOBAL_TREE_DRIFT`, no porque el
  cambio estuviera mal sino porque nadie había regenerado `Global/` todavía. Es la pregunta
  equivocada en ese punto del flujo: ahí lo que hace falta es un smoke test de "¿esta config nueva
  genera sin explotar?", sin comparar contra `Global/`. El arreglo, dentro del alcance de este
  paquete, agregó `_generate_smoke_test(profile)` (`ai/scripts/setup_models.py:107-121`), que llama
  a `build.sh --output <tmp> --profile <profile>` — un modo que ya existía en `build.sh`, sin tocar —
  y reproduce la misma validación de "generó sin explotar" que `--check` daba antes como efecto
  colateral de construir su STAGING, sin la comparación contra `Global/` que ahora `--check` sí hace.
  Los dos call sites (`setup_models.py:589-604` no interactivo, `setup_models.py:416-421` wizard)
  pasaron a llamar a `_generate_smoke_test(profile)` en vez de `build.sh --check`, y el mensaje de
  error `BUILD_CHECK_FAIL` se separó en `MODELS_GENERATE_FAIL` (no generó) y `BUILD_INSTALL_FAIL` (no
  instaló) — antes compartían el mismo texto, que confundía las dos causas.
- `verify.sh` no cambió de forma: ya tenía el orden correcto (`:6` antes que `:17`); lo que cambió
  es que ahora esa posición relativa importa de verdad, porque `:6` dejó de ser un no-op de facto.
- `TIPS-USO.md` documenta la regla de orden y la nueva semántica de `--check`/`BUILD_CHECK_PASS`.
- Ningún call site de los 17 que la suite usa para regenerar `Global/` se tocó.

## Addendum — PKG-2 `P2-gates-que-no-callan` (AC-06..AC-09): D-3, la segunda mitad de esta decisión

Estado: Accepted (2026-08-12).

### Contexto

D-3 de la spec: cuatro agentes murieron en la sesión del 2026-08-11 con `Agent stalled: no
progress for 600s`, todos mutadores de corrida larga que habían pipeado un gate a `| tail -N`
(patrón recomendado en texto efímero de spawn, nunca en un archivo versionado — verificado con
`grep -rnE "\| *tail\b"` sobre `Global/_canonical/` y `PROYECTO/`, cero ocurrencias antes y
después de este paquete).

### La causa raíz que se creía es falsa — corregido explícitamente para que no vuelva

El primer diagnóstico de esta sesión decía "el pipe bufferea por bloques" y proponía `stdbuf`
como remedio. **Es falso, medido dos veces por este paquete** (evidencia completa en
`docs/specs/021-gates-que-no-mienten-ni-callan/evidence/P2-implementer.md`, §2):

1. `timeout 25 bash -c 'python3 -m unittest discover -s tests -v 2>&1 | tail -3'` — cero bytes en
   25s contra la suite real.
2. `timeout 8 bash -c 'stdbuf -oL python3 -u -c "<escritor con flush=True explícito por línea>" |
   tail -3'` — **cero bytes en 8s**, con un escritor que ya no bufferea nada por su cuenta.
3. El mismo escritor del punto 2, sin `tail` en la cadena, emite línea por línea con normalidad.

`tail -N` sin `-f` **estructuralmente no puede emitir nada hasta ver EOF**, sea cual sea el
buffering upstream — el escritor del punto 2 y el del punto 3 son idénticos; la única diferencia
es la presencia de `| tail -3`. **El remedio no es `stdbuf`**: es no poner `tail -N` en la cadena
de un comando largo. Además `stdbuf` es GNU coreutils y no existe en macOS/BSD, donde corre el CI
(`.github/workflows/*.yml`, job `verify-macos`) — si se nombra una herramienta para volver
line-buffered la salida propia de un comando, es `python3 -u` / `PYTHONUNBUFFERED=1`, portable.

### Decisión

1. **AC-06 — `ai/scripts/heartbeat-run.py`**: un wrapper que corre el comando dado, reenvía su
   stdout+stderr combinado línea por línea a medida que llegan (nunca espera a que el hijo
   termine) e inyecta su propia línea de latido si pasan `--interval` segundos (default 60) sin
   una línea real. No acelera el comando — AC-06 es sobre silencio, no sobre velocidad; eso es un
   no-goal explícito de la spec.
2. **AC-07 — doctrina en `TIPS-USO.md`** (sección "Running long commands without going silent"):
   fija el patrón prohibido (`| tail -N`) y los tres patrones correctos, en orden de preferencia:
   dejar fluir la salida cruda, redirigir a archivo y leer después, o `heartbeat-run.py`. Nombra
   `python3 -u`/`PYTHONUNBUFFERED=1`, nunca `stdbuf`, por portabilidad. `TIPS-USO.md` lo documenta
   para quien lo lee a mano, pero no propaga a un encargo nuevo. La misma regla vive también en
   `Global/_canonical/skills/spawn-prompt/SKILL.md` (sección Rules) — la plantilla fija que el
   orquestador carga para redactar CUALQUIER spawn (ADR-0026) — porque esa es la superficie real
   que evita que el próximo encargo vuelva a decir `| tail -N`, sin duplicarlo en los 28 briefs de
   rol. Se propaga a los cuatro árboles (`Global/opencode`, `Global/claude-code`, `Global/codex`,
   `Global/pi`) vía `./build.sh`, verificado por `./build.sh --check`.
3. **AC-08 — el límite queda escrito, acá y en `TIPS-USO.md`**: el watchdog de 600s es del
   **runtime del agente**, no de este repositorio; esta feature no lo puede cambiar. Lo único que
   el repo controla es no crear la condición de silencio que lo dispara. Sin esta aclaración
   escrita, "arreglamos los stalls" se leería como que no pueden volver a pasar por ninguna otra
   causa — y sí pueden: cualquier comando con una pausa real mayor al watchdog, corrido SIN
   `heartbeat-run.py` y sin salida propia, sigue pudiendo estancar a quien lo mire.
4. **AC-09 — prevención hacia adelante, no corrección** (F-05 del challenge): el patrón
   `| tail -N` nunca estuvo en un archivo versionado (`Global/_canonical/`, `PROYECTO/`) — vivía
   en texto efímero de spawn. El test nuevo (`tests/test_harness.py`,
   `test_the_tail_pipe_antipattern_never_lands_in_a_versioned_brief_or_template`) fija que no
   aparezca de ahora en más, con el patrón exacto ya decidido por la spec (F-07): `\| *tail\b`,
   anclado al pipe literal — un `grep` ingenuo por `tail` da falsos positivos dentro de
   "detail"/"details" (13 medidos en `Global/_canonical/` al momento de este paquete, todos en esa
   palabra).

### Alternativas rechazadas

- **Recomendar `stdbuf -oL` en la doctrina como forma de evitar el stall.** No arregla nada: el
  problema no es el buffering del escritor (medido arriba), es `tail -N` en sí. Además no es
  portable (GNU-only, ausente en macOS/BSD donde corre el CI).
- **Acelerar la suite para que el umbral de 60s nunca se alcance.** No-goal explícito de la spec:
  que tarde 7-10 minutos es un problema distinto de que calle: este paquete resuelve el segundo.
- **Tocar el watchdog de 600s.** No está en este repositorio; pertenece al runtime del agente.
- **Reabrir 019/020 para borrar el patrón de sus context packs.** No aplica: el patrón nunca
  estuvo en un archivo versionado de esas features (verificado por `grep`), así que no hay nada
  que borrar — AC-09 es prevención, no corrección.

### Consecuencias

- `ai/scripts/heartbeat-run.py` queda disponible para cualquier comando largo, dentro o fuera de
  este repositorio; no reemplaza ni modifica `verify.sh`/`build.sh` (ningún call site existente se
  tocó).
- `TIPS-USO.md` documenta el patrón prohibido y los correctos; un test de doctrina ancla que el
  patrón prohibido no aparezca en `Global/_canonical/` (briefs de agente) ni en `PROYECTO/`
  (plantillas que se copian a cada proyecto nuevo).
- El límite del watchdog de 600s queda escrito como propiedad del runtime, no de este repo, en
  este ADR y en `TIPS-USO.md`.
