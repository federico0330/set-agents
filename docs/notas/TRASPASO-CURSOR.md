# Traspaso a Cursor — 2026-08-17

Continuación después de la corrida de Codex (commits `211df01..24b4d8a`). Este archivo es el
prompt de arranque; el estado medido vive en `ai/state/features/` y la historia larga en
[[TRASPASO]].

---

Sos el orquestador del harness SET-AGENTES, trabajando **sobre el harness mismo**, en
`/home/federico/SET-AGENTES`, branch `main`, base `24b4d8a`. El repo es **público**.

Seguís el workflow del propio repo: file-first, gate-driven, por paquetes. El estado durable vive
en `ai/state/features/*.json` y **sólo se muta con `python3 ai/scripts/feature-state.py <verbo>`**,
nunca editando el JSON a mano.

## Estado medido hoy (verificado, no de memoria)

- `main` = `24b4d8a`. **30 commits sin pushear** a `origin/main`.
- Working tree **sucio**: 51 archivos (31 modificados = notas/bitácoras regeneradas por
  `feature-state.py`; 20 sin trackear = evidencia de review/delta de D1–D4 y 4 decisiones).
  Eso hay que commitearlo, no descartarlo: es la evidencia de los paquetes aceptados.
- Feature **025 — consola mínima y flexible**: `phase=PACKAGE_IMPLEMENTATION`.
  - **D1 superficie-humana → accepted** (1 ciclo de review; `D1-F04` quedó `refuted` por
    finding-verifier, con evidencia en `ai/scripts/tui.py:720-734`).
  - **D2 trabajo-visible → accepted** (2 ciclos de repair).
  - **D3 posturas-de-autonomia → accepted** (2 ciclos; el contrato de postura quedó atado en los
    cinco `agents/orchestrator.*` de `Global/`).
  - **D4 harness-por-CLI → accepted** (3 repairs; los dos blockers de presupuesto están
    `resolved` con autorización explícita de Federico).
  - **D5 vault-en-todo-spawn → `package_implementation`, INCOMPLETO.** Es lo único que falta
    para cerrar 025.
- Features **028** (narración que enseña), **029** (convenciones antes del código) y **030**
  (guardas que no se pueden prefijar): tienen spec en `docs/specs/`, **ninguna tiene state file**
  en `ai/state/features/`. 030 además ya tiene código integrado y instalado (el fix del RCE), pero
  el estado nunca se creó.

## Objetivo 1 — cerrar D5 y con eso la feature 025

El checkpoint del implementer está en
`docs/specs/025-consola-minima-y-flexible/evidence/D5-implementation.md`. Medí el árbol y coincide:

| lane | `vault_block` | menciones de degradación |
|---|---|---|
| `set_agents_spawn.py` | 12 | 10 |
| `claude_code_spawn.py` | 18 | 13 |
| `codex_spawn.py` | 18 | **1** |
| `opencode_spawn.py` | 18 | **2** |

El transporte del vault está en los cuatro; **la degradación honesta y el scrub sólo están en dos**.
Falta:

1. Portar a `codex_spawn.py` y `opencode_spawn.py` lo simétrico: nota explícita de
   sin-vault/degradado, y que un fallo transitorio de lookup vaya al sink JSONL protegido **sin
   cachearse**.
2. Las cuatro guardas de doctrina compartida (el fence común, no una copia por lane — ese fue
   exactamente el defecto de `claude_bash_guard` / `claude_release_guard` /
   `claude_local_gate_guard`, que tenían cuatro copias divergentes del mismo invariante).
3. Tests focales por lane, cada uno con **prueba de mordida**: romper la implementación y demostrar
   que el test se pone en rojo antes de darlo por bueno.
4. `git diff --check`, gates, review independiente, delta review, y recién ahí
   `record-package-accepted`.

Ojo con la rama `worktree-agent-a1e28ec280c592315` (`6102f96`, 482 líneas): tiene trabajo parcial
de spawners que puede servir de referencia, **pero también arrastra una reimplementación divergente
de D5 que no hay que mergear**. Leela, no la mergees.

## Objetivo 2 — crear los state files que faltan

028, 029 y 030 existen como spec y no existen como estado. Sin state file el harness no puede
ni reportarlas ni aceptarlas. Creá los tres con `feature-state.py`, y para 030 registrá lo que
**ya está hecho e instalado** (el fix del RCE en `coord_policy.py` + las tres guardas que ahora
fallan cerradas), no lo declares pendiente.

## Objetivo 3 — 028 narración que enseña

`docs/specs/028-narracion-que-ensena/spec.md` está escrita y desafiada. N3a ya está integrado
(`render_status.py:66` ahora emite el `reason` junto al `next`, así que "Próximo paso" dice *por
qué* falta algo en vez de escupir `PACKAGE_ACCEPTED`). Queda N1 (parcial en la rama
`worktree-agent-a47274084a7696ad1`, `6a1949a`, 1784 líneas), N2 y N3b.

## Objetivo 4 — 029 convenciones antes del código

`docs/specs/029-convenciones-antes-del-codigo/spec.md` está escrita, **sin una sola línea de
implementación**. Es la que pidió Federico: que el orquestador, en el intake, cierre convenciones
de arquitectura antes de implementar — sin inventar ni mentir. Referencia declarada: gentle-ai.
La skill `request-triage` y `solution-baselines` son el lugar natural donde aterriza.

## Objetivo 5 — cierre

Suite limpia, `ai/scripts/verify.sh` → `VERIFY_PASS`, `./build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, instalar (`./build.sh --install --home`), commitear
todo, y pushear los 30+ commits.

## Reglas que costaron caro — no las re-aprendas

1. **Nunca leas `$?` después de un pipe.** Devuelve el exit code del último comando del pipe, no
   del que te importa. Usá `${PIPESTATUS[0]}` o redirigí a archivo. Este error me hizo reportar un
   paquete como integrado cuando el commit no tenía los archivos.
2. **Medí sobre el árbol integrado, no sobre el worktree del agente.** Una medición correcta en el
   worktree equivocado no prueba nada.
3. **Verificá el artefacto antes de aceptar un reporte de agente.** `git rev-parse` de la rama +
   `grep` de un símbolo que el trabajo debería haber creado. Un agente reportó cuatro spawners y
   cinco mordidas sobre una rama byte-idéntica a su base.
4. **Dale a cada agente un SHA fijo**, nunca `main`, si vos vas a commitear en `main` mientras
   corre. Perdí 728 líneas correctas por eso.
5. **Nunca `git checkout` / `git restore` / `git stash`** sobre archivos de trabajo. Para la
   mordida, copiá con `cp` y restaurá con `cp`.
6. **Watchdog: un agente sin output por 600s muere.** Los procesos en background se cortan a ~650s
   y la suite tarda ~700s → corré la suite con `setsid nohup` y redirección a archivo, y hacé que
   los agentes emitan progreso.
7. **Nunca toques nada bajo `~`.** `./build.sh --install` sin `--home` puede pisar cosas.

## Cómo verificar que arrancás bien

```bash
git log --oneline -1                                   # 24b4d8a
git status --short | wc -l                             # 51
python3 -c "import json;d=json.load(open('ai/state/features/025-consola-minima-y-flexible.json'));[print(p['package_id'],p['status']) for p in d['packages']]"
grep -c degrad ai/scripts/codex_spawn.py               # 1 → tiene que subir
```
