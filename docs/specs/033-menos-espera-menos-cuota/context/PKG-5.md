# Context pack — PKG-5 el-gate-se-ve

Spec: `docs/specs/033-menos-espera-menos-cuota/spec.md` (hash `18dcffaf…e4894c`). **AC-5.1–AC-5.6**. Segundo a implementar (después de PKG-4).

**Objetivo.** 20 minutos de gate mirables: una línea de progreso con ETA real, el bloque de falla apenas ocurre, un resumen final copiable (fallas, skips por razón, 10 más lentos). Es un cambio de **presentación**. El conjunto de tests ejecutados no puede cambiar (AC-5.5).

## Paths (leídos hoy)

- `ai/scripts/verify.sh:5` — `./build.sh --check` primero.
- `ai/scripts/verify.sh:17-23` — guest: 2 tests `-v`; default **`python3 -m unittest discover -s tests -v`** (línea 22). Spec `:22` **coincide**. 1286 tests / 1237 s medidos el 2026-08-18.
- `ai/scripts/verify.sh:24-66` — `py_compile`, `git diff --check`, generate+diff de `Global/`, `check-canonical-paths.py`, `check-feature-state.py`, `VERIFY_PASS`. **No tocar** salvo lo que el presenter de la suite requiera.
- `ai/scripts/verify.sh:30` — `./build.sh --output … --profile go-zen`. **PKG-1** saca `--profile`; este paquete **no** lo mueve.
- `tests/__init__.py:16-28` — `sys.path` único para aislamiento de imports (ADR-0051).
- `tests/__init__.py:30-76` — un sandbox de escritura **por intérprete** (`TemporaryDirectory` + `HOME`/`TMPDIR`/`SET_AGENTS_STATE`) y boundary de `Popen` (`:71-76`).
- AC-5.6 (opcional): paralelizar **solo** si se demuestra que N intérpretes no se pisan el sandbox ni el checkout. Si no hay prueba de aislamiento, **no se hace**.

Hoy `unittest discover -v` entierra fallas al final y no hay ETA. Hace falta un `TestResult`/`TestRunner` propio (o wrapper) que: reescriba una línea `‹hechos›/‹total› · elapsed · ETA · ✗fallas`; imprima el bloque de falla **apenas** falla; al cierre liste fallas, skips agrupados, 10 más lentos. Verbose completo detrás de una env var (AC-5.4); default = resumen.

## ADRs / invariantes

- ADR-0041 — largos con `heartbeat-run.py --interval N -- <cmd>`; sin pipe/tail.
- ADR-0051 — `docs/adr/0051-owned-paths-sees-untracked-files-and-test-isolation.md`: no relajar el sandbox para “ir más rápido”.
- Doctrina de gates: ni skip, ni xfail, ni aflojar un assert para que el resumen se vea mejor (AC-5.5).
- El eje `--profile go-zen` de `:30` es de PKG-1, no de acá.

## Validación local

```
python3 -m unittest tests.test_harness.HarnessTests.test_shell_scripts_parse
# más el test NUEVO de AC-5.5 (mismo conjunto ejecutado, antes/después)
python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest tests.<modulo_nuevo>
python3 ai/scripts/heartbeat-run.py --interval 25 -- ./ai/scripts/verify.sh
./build.sh --check
git diff --check
```

`pytest` no existe. El verify completo es el gate del paquete (~20 min); la prueba de AC-5.1–5.3 se puede hacer con un subset + el runner nuevo, no hace falta 1286 tests para ver la línea de progreso.

## Reviewers / runtime / tests

- `required_reviewers`: `["package-reviewer"]` — presenter de CLI del gate, no UI web, no auth.
- `runtime_surface`: **false** — tooling del gate (`verify.sh`); no hay app/API/persistencia de producto. Los ACs se prueban con unittest del conjunto ejecutado y del formato. `true` dispararía runtime-verifier sobre una corrida de 20 min.
- test owner: **implementer**. `strict_tdd`: **false**.

## Fuera de alcance

PKG-4 (Windows/macOS flaky) · paralelizar sin prueba de aislamiento · cambiar qué tests corren · `build.sh --profile` · `Global/` · 032.

## Excepciones recomendadas

`owned_paths` = `["ai/scripts/verify.sh"]` solamente.

- `tests/` (archivo nuevo `tests/test_*.py`) — AC-5.5 **exige** un test de que el conjunto ejecutado es idéntico. `update-package` no expone `--owned-path`.
- Si extraés el `TestResult` a un `.py` bajo `ai/scripts/` (recomendado: el shell no es testeable), declaralo con `--exception` **cuando el archivo exista** — no adivinar el nombre (lección owned_paths/ADR).

## Mordida

Test nuevo de AC-5.5: `cp` de `verify.sh` (o del reporter) a un tmp, romper el conjunto (p.ej. filtrar un módulo), ver rojo, `cp` restaurar, verde. Nunca `git checkout`/`restore`/`stash`.
