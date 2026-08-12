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
  `docs/specs/021-gates-que-no-mienten-ni-callan/evidence/P1-implementer.md`.
- `verify.sh` no cambió de forma: ya tenía el orden correcto (`:6` antes que `:17`); lo que cambió
  es que ahora esa posición relativa importa de verdad, porque `:6` dejó de ser un no-op de facto.
- `TIPS-USO.md` documenta la regla de orden y la nueva semántica de `--check`/`BUILD_CHECK_PASS`.
- Ningún call site de los 17 que la suite usa para regenerar `Global/` se tocó.
