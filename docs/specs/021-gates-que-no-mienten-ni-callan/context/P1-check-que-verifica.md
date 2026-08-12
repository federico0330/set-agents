# Context pack — P1-check-que-verifica (ADR-0041)

Spec: `docs/specs/021-gates-que-no-mienten-ni-callan/spec.md`, **AC-01..AC-05**.

## El defecto, reproducible

`build.sh:76-97`: el modo `check` genera los cuatro árboles en un `STAGING` temporal y después
**solo compara dos archivos de self-scaffold** (`feature-state.py`, `check-owned-paths.py`)
entre `PROYECTO/ai/scripts/` y `ai/scripts/`. **El `STAGING` recién generado nunca se compara
contra `Global/`.** El `CHECK_PASS` que uno lee lo imprime `generate.py:730` al generar — es
"corrí sin explotar", no un veredicto de drift.

Comprobalo antes de tocar nada: ensuciá un archivo de `Global/` (con `cp`, **no** con git) y
corré `./build.sh --check`. Hoy pasa en verde. Ese es el bug.

Consecuencia medida: durante 019 y 020 se registraron **decenas de gates** citando
`./build.sh --check → CHECK_PASS` como prueba de "sin drift". Ninguno probaba eso.

## Las dos decisiones ya tomadas — ejecutalas, no las re-litigues

### 1. Perfil de comparación FIJO (decisión de Federico)
La comparación se hace **siempre con `--profile go-zen`**, ignorando el `active-profile` local.

Razón, medida por el spec-challenge: `active-profile` está en `.gitignore` y lo resuelve
`models_config.auto_profile()` (`:269-286`) por máquina; los perfiles difieren en **19
archivos**; y `Global/` está commiteado bajo `go-zen`. Con perfil local, `install.sh:370`
fallaría en toda máquina sin el par "go" vivo —**rompiendo el onboarding antes de instalar
nada**— y `setup_models.py:397,570` fallaría en todo cambio de modelo, que es su propósito.

Con perfil fijo el gate responde la pregunta correcta: *¿lo commiteado en `Global/` es lo que
genera `_canonical`?* — que es de repositorio, no de máquina.

### 2. Reutilizá el `diff` de `verify.sh:26-28`, NO el de `--diff`
`--diff` (`build.sh:99-104`) lleva `|| true` y **siempre sale 0**: es un modo "mostrame", no un
gate. El que realmente falla bajo `set -e` es el de `verify.sh`.

## AC-04 — la vía es el ORDENAMIENTO, no la reescritura

`verify.sh` ya corre `--check` en `:6` y la suite en `:17`. Una vez que `--check` compare de
verdad, el drift se detecta **antes** de que la suite lo pise — **sin tocar ninguno de los 17
call sites**. El challenger los leyó uno por uno: los 17 regeneran `Global/` por la misma razón
(necesitan leer contenido fresco de `ROOT/Global/<harness>/` para assertear algo de
`generate.py`).

Lo que este AC agrega es **fijar el orden como regla**: `./build.sh --check` corre SIEMPRE antes
que la suite cuando ambos se citan como evidencia, sea vía `verify.sh` o sueltos. Hay precedente
real de citarlos sueltos (`HANDOFF-PASO9.md:103`) y un job de CI que corre la suite sola
(`.github/workflows/*.yml:32-51`, `windows-bootstrap`).

**Si descubrís que el ordenamiento no alcanza, eso es `HUMAN_DECISION_REQUIRED`** — no
reescribas los 17 sitios por las dudas. El pedido fue arreglar dos cosas puntuales.

## AC-05 — anotar la evidencia histórica

No se reabren 019 ni 020. Se registra una decisión (`log-decision`) que diga **qué probaba
realmente** ese gate, para que nadie lea esa evidencia como lo que no fue.

## Antes de cambiar el `rc`

`grep -rn "build.sh --check"` — hay al menos tres call sites que hoy esperan `rc=0`:
`install.sh:370` (bajo `set -euo pipefail`), `setup_models.py:397` y `:570`
(`subprocess.run(..., check=True)`). Con el perfil fijo no deberían romperse, pero
**verificalo**, no lo asumas.

## Restricciones

- **ADR-0041 primero** (`ls docs/adr/` para confirmar que está libre, indexalo en
  `docs/adr/README.md`), después el test en rojo, después el código.
- AC-03 pide un test que **falle contra el `build.sh` de hoy**. Escribilo y confirmá el rojo
  antes de tocar `build.sh`.
- `tests/test_harness.py` assertea frases por grep: `grep -n` antes de mover nada.
- **No uses `git checkout`, `git restore` ni `git stash`** sobre archivos del repo. Para ensuciar
  y restaurar en las pruebas: `cp` y `cp`.
- Sin refactors oportunistas en `build.sh`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **970 OK / 3
skips**) · `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` con su semántica
nueva · `git diff --check` limpio.

**No pipees comandos largos a `tail`**: no emiten un byte hasta terminar y el agente muere por
watchdog a los 600 s. Es literalmente el defecto que P2 arregla. Escribí a archivo y leelo, o
dejá que la salida fluya.

## Advertencia de proceso

Esta sesión acumula **cinco afirmaciones de verificación que no resistieron la re-ejecución**
(cuatro transcripciones fabricadas y una cifra mal medida). **Cada bloque que pegues es literal,
o está marcado como recortado.** Si no lo corriste, "sin verificar".

Y apareció **un test decorativo** en tres de los cinco paquetes de 019 y en P1 de 020. Por cada
test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.

## Evidencia

`docs/specs/021-gates-que-no-mienten-ni-callan/evidence/P1-implementer.md`: tabla AC → cambio
(`archivo:línea`) → prueba; `--check` **fallando** con un `Global/` sucio y **pasando** limpio;
la confirmación de que los tres call sites que esperan `rc=0` siguen funcionando; la prueba de
mordida por test; y los gates.

## Checkpoint

Murieron cuatro instancias por stall en esta sesión. Escribí la evidencia en el primer minuto y
guardá a disco a medida que avanzás.

## Fuera de alcance

P2 (los gates que callan) · reescribir los 17 call sites · reabrir 019 o 020 · todo lo de las
features 022-025 del plan aprobado.
