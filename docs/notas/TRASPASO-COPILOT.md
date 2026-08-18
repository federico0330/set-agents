# Traspaso a Copilot — 2026-08-17

Continuación desde `5bf4820`. Estado medido, no recordado. Ver también [[TRASPASO]] y
[[TRASPASO-CURSOR]].

---

Sos el orquestador del harness SET-AGENTES, trabajando **sobre el harness mismo**, en
`/home/federico/SET-AGENTES`, branch `main`, base `5bf4820`. El repo es **público**.

File-first y gate-driven. El estado durable vive en `ai/state/features/*.json` y **sólo se muta con
`python3 ai/scripts/feature-state.py <verbo>`**, nunca editando el JSON a mano. Si un verbo te niega
algo, la negativa es información: el motor casi siempre tiene razón. No la esquives editando el
archivo — ese es exactamente el defecto que esta tanda de trabajo vino a corregir.

## Estado medido hoy

- `HEAD` = `origin/main` = `5bf4820`. **Árbol limpio, cero sin pushear.** Instalado
  (`INSTALL_PASS`, backup en `~/.local/state/set-agentes/backups/`).
- Gate global sobre ese árbol: **`Ran 1261 tests in 820.239s, OK (skipped=4), VERIFY_PASS`** +
  `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`, `BUILD_CHECK_PASS`.

| feature | fase | qué falta |
|---|---|---|
| 025 consola mínima | **DONE** | nada |
| 029 convenciones | **DONE** | nada |
| 030 guardas RCE | **DONE** | nada |
| 028 narración | **BLOCKED** | objetivo 1 y 2 |
| 006 execution-graph | PACKAGE_ACCEPTED | objetivo 4 — un comando |
| 010 spawn-provenance | PACKAGE_ACCEPTED | objetivo 4 — un comando |
| 024 listo-para-terceros | BLOCKED | objetivo 5 — **decisión de Federico** |
| 002 adaptive-pi | BLOCKED | fuera de alcance, ver al final |
| 011 quota-failover | BLOCKED | fuera de alcance, ver al final |

---

## Objetivo 1 — feature 031: el verbo de corrección de registro

**Es la llave de todo lo demás. Hacelo primero.**

El harness tiene una carencia que apareció **dos veces** en la última tanda, y las dos veces obligó a
dejar evidencia real fuera del registro:

1. **Una feature en `DONE` no tiene camino de vuelta.** `record-spawn` corta con
   `cannot record spawn from phase DONE` (`ai/scripts/feature-state.py:407-408`, guarda `TERMINAL`),
   `record-delta-review` exige fase `DELTA_REVIEW`
   (`ai/scripts/feature_state_lib/cli_repair.py:279-280`) y `reopen` sólo aplica desde `BLOCKED`
   (`ai/scripts/feature_state_lib/cli_lifecycle.py:527-528`). Consecuencia real: la delta review
   correctiva de 025/D5 —que encontró una regresión de seguridad viva— **no pudo registrarse en el
   paquete** y vive sólo como archivo.

2. **Un paquete creado sin work items no se puede reparar.** `package_review_ready` exige
   `tasks_complete`, que pide `bool(tasks) and all(completed)`
   (`ai/scripts/feature_state_lib/model.py:481-482`). `create-package` no-opea sobre un `package_id`
   existente (`cli_lifecycle.py:307-308`), `update-package` no tiene `--task`, y `LEGAL_TRANSITIONS`
   sólo llega a `PACKAGE_PLANNING` desde `PACKAGE_ACCEPTED` (`model.py:36-49`) — para aceptar hacen
   falta justamente los work items que no se pueden crear. **Es circular.** Consecuencia real: 028
   está `BLOCKED` con el código implementado, revisado y reparado, y su gate en verde.

El propio repo ya vio la punta de esto: leé el docstring de `cmd_record_late_review`
(`ai/scripts/feature-state.py:584-625`). Dice *"the gap is registered as debt rather than simulated
closed"* — alguien prefirió negarse antes que simular, y tuvo razón. Lo que falta es la salida.

**Lo que hay que construir** (dos verbos; escribí spec antes de código, esto toca la máquina de
estados):

- **`amend-package`** — agrega work items a un paquete **no aceptado** que se creó sin ellos.
  Escribe en el historial que fue una corrección de registro, con `--reason` obligatorio. Nunca sobre
  un paquete `accepted`: ahí el camino sigue siendo un paquete nuevo.
- **`reopen --from-done`** — sale de `DONE` con `--reason` y `--authorized-by` obligatorios, dejando
  el evento en el historial. No es un `reopen` silencioso: la feature tiene que quedar visiblemente
  reabierta, y su cierre anterior visible también.

**Riesgos que la spec tiene que cerrar, porque son la razón por la que estas puertas no existían:**

- Un verbo que agrega tasks puede hacer que un paquete se acepte con work items inventados **después**
  de que se corrió el gate. La spec tiene que decir qué evidencia exige `amend-package` y si invalida
  gates previos.
- `reopen --from-done` puede convertirse en la puerta por la que se reabre cualquier cosa para
  maquillarla. La autorización explícita tiene que quedar registrada como quedó la de D4
  (ver `ai/state/features/025-consola-minima-y-flexible.json`, campo `blockers`, entradas con
  `resolved_by: "Federico — autorización explícita en conversación 2026-08-17"`).
- **No debilites `record-late-review`.** Su negativa a registrar sobre un paquete `accepted` es
  correcta y está razonada en su docstring; 031 le da una puerta previa, no la abre a la fuerza.

Decisiones ya tomadas y registradas — leelas antes de diseñar, están en
`ai/state/decisions-log.jsonl`:
`d5-revision-correctiva-sin-camino-de-estado`, `replanteo-028-paquetes-sin-work-items`,
`replanteo-028-imposible-el-motor-no-tiene-salida`.

## Objetivo 2 — cerrar 028 con lo que construyó 031

El **código de 028 está terminado, revisado de forma independiente y reparado**. No hay trabajo de
implementación pendiente. Lo que falta es el trámite que el motor no dejaba hacer:

1. `amend-package` sobre `N1-campos-que-obligan`, `N2-doctrina-que-explica` y
   `N3b-los-campos-donde-se-leen`, con sus work items reales (salen de la evidencia, ver abajo).
2. `update-package --integrated true` en los tres. El `diff_ref` ya está puesto con SHA real
   (`f688531..d1da7a0`).
3. `record-review` con los cinco hallazgos, `record-repair`, delta review, testing, runtime QA,
   `accept-package`.

**Toda la evidencia ya está escrita**: `docs/specs/028-narracion-que-ensena/evidence/N-package-review.md`
tiene los cinco hallazgos con su reproducción medida, qué se reparó y con qué test. No la reescribas,
citala.

Los cinco hallazgos, para que los cargues sin releer todo:

| id | sev | qué |
|---|---|---|
| N1-F01 | high | La guarda de punteros era ciega a la caja: `pkg 007` la atravesaba, `PKG 007` no |
| N1-F02 | high | Rellenar con muletillas diluía la densidad: `"listo, bien, …, PKG-007 reparado, ok."` daba 0.111 y pasaba |
| N1-F03 | medium | `--result started` salía sin verificación alguna si se omitían los flags delatores |
| N2-F01 | high | AC-18 no implementado: ningún archivo decía **cuándo** correr `digest`, y su test era un `assertIn` del nombre del comando |
| N3b-F01 | medium | Escribir concedía 400 y renderizar cortaba en 300; un `tech` legal de 350 salía siempre mutilado |

Los cinco están **reparados** en `d1da7a0`, cada uno con su prueba de mordida corrida.

Quedan tres hallazgos de proceso **no reparados**, decidí vos si entran o se anotan como deuda:
la spec asignaba un archivo `tests/test_narracion_digest.py` que nunca se creó (la cobertura vive
dentro de `tests/test_digest.py`); AC-16 pedía confirmar *antes* de unificar si la divergencia de
`AGENTS.codex.md` era deliberada y esa confirmación no quedó registrada (el revisor la verificó por
su cuenta: `git show 7ee50fd --stat` muestra que el commit de ADR-0027 tocó `CLAUDE.md`,
`AGENTS.opencode.md` y `AGENTS.pi.md` pero **no** `AGENTS.codex.md` — fue deriva, no decisión).

## Objetivo 3 — que la delta review de D5 aterrice donde corresponde

Con `reopen --from-done`, reabrí 025, registrá la delta review correctiva sobre
`D5-vault-en-todo-spawn` y volvé a cerrarla.

La evidencia está en `docs/specs/025-consola-minima-y-flexible/evidence/D5-delta-review-correctiva.md`.
El hallazgo grave, ya reparado en `d1da7a0`, vale que lo entiendas antes de tocar nada:

> `24b4d8a` arregló el carril pi para que el vault viajara por **stdin**, con un comentario que decía
> *"the fenced vault reaches pi through stdin, never argv"*. El commit `f688531` —rotulado
> **"Feature 028/029"**, tocando ese archivo **fuera de su alcance declarado**— revirtió el arreglo
> **y reescribió el comentario para justificar la forma revertida**. Ni el mensaje de commit ni
> ninguna nota lo mencionan. Efecto: hasta ~14 KB de contenido de vault (externo, sincronizado por
> Syncthing) en el argv del hijo, visible en `ps aux` para cualquier usuario local. Y el único test
> del carril **afirmaba el marcador dentro de argv**, o sea codificaba el defecto como esperado.

Mientras estés ahí, cerrá **D5-DR03** (baja, no es defecto vivo): el anti-cacheo de fallos
transitorios de vault sólo tiene test dedicado en `codex_spawn` y `opencode_spawn`
(`tests/test_spawn_materialization.py:119-145`). Falta el equivalente para `set_agents_spawn` (pi) y
`claude_code_spawn`. Por inspección la implementación es correcta en los cuatro; lo que falta es la
red que agarre una regresión futura.

## Objetivo 4 — cerrar 006 y 010 (barato, hacelo aunque no llegues al resto)

Las dos están en `PACKAGE_ACCEPTED` desde hace mucho y el motor dice exactamente qué les falta:

```
$ python3 ai/scripts/feature-state.py next 006-execution-graph
"reason": "P3-graph-view: module impact required (record-module-impact) o waived (--module-impact-waived --reason)"

$ python3 ai/scripts/feature-state.py next 010-spawn-provenance
"reason": "P1-spawn-provenance: module impact required (record-module-impact) o waived (--module-impact-waived --reason)"
```

Declarar el impacto de módulo de verdad (mirando qué módulos tocó cada paquete) y después
`transition INTEGRATION` → `transition DONE`. **No uses el waiver salvo que el impacto sea
genuinamente nulo, y si lo usás escribí por qué.**

## Objetivo 5 — 024: preparalo, no lo decidas

`024-listo-para-terceros` tiene sus **cuatro paquetes aceptados** con review independiente y no
cierra por una sola cosa: el repo es público y **shippea el codename de un cliente real**.

Ubicación exacta, medida:

- `ai/scripts/generate.py:475` — lo inyecta en el orquestador de opencode.
- `Global/opencode/agents/orchestrator.md:1066` — el artefacto generado.
- `tests/test_harness.py:7569` — **un test que exige que esté**.
- `TIPS-USO.md:114` — otra mención.

El texto es una regla de ruteo real: *"For `replenishment-v2` package `RPL-P0A` only, route
deterministic package gates to `package-gate-runner`"*.

**Esto es decisión de Federico, no tuya.** Hay al menos tres caminos y cambian el producto:
borrar la regla; volverla genérica y configurable por proyecto; o dejarla y aceptar que el codename
es público. Preparalo —dejá el diff listo para cada opción o la spec de la que corresponda— y
**preguntá**. No elijas por él y no lo borres en silencio: es una regla de ruteo que hoy alguien usa.

## Fuera de alcance

- **002-adaptive-pi-orchestration**: `P1-routing-core` en `repair_required`, cinco hallazgos altos
  vivos, 12 spawns y 2 ciclos de deep review agotados. El blocker dice que pide rediseño. No lo
  toques sin que Federico lo pida.
- **011-quota-failover**: bloqueada porque AC-06 exige una suscripción de Anthropic genuinamente
  agotada junto a un proveedor alterno usable, y esa precondición no se puede fabricar. No es
  trabajo de código.

## Reglas que costaron caro — no las re-aprendas

1. **Nunca leas `$?` después de un pipe.** Devuelve el exit code del último comando del pipe, no del
   que te importa. Usá `${PIPESTATUS[0]}` o redirigí a archivo. Este error hizo reportar un paquete
   como integrado cuando el commit no tenía los archivos.
2. **Medí sobre el árbol integrado, no sobre el worktree del agente.** Una medición correcta en el
   worktree equivocado no prueba nada. Un `diff_ref` que dice `WORKTREE-...` en vez de un SHA es la
   señal de que esto ya pasó.
3. **Verificá el artefacto antes de aceptar un reporte de agente**: `git rev-parse` de la rama +
   `grep` de un símbolo que el trabajo debería haber creado. Un agente reportó cuatro spawners y
   cinco mordidas sobre una rama byte-idéntica a su base.
4. **Un revisor no puede citar como evidencia el documento que escribió el implementer.** Así se
   aceptó D5, y por eso se le coló una regresión de seguridad.
5. **Un commit no toca archivos fuera de su alcance declarado.** El caso de `f688531` no fue un
   descuido: revirtió un arreglo de seguridad y reescribió el comentario para justificarlo, bajo un
   rótulo que hablaba de otra feature. Si tenés que tocar algo fuera de alcance, decilo en el mensaje.
6. **Toda prueba nueva se demuestra en las dos direcciones**: rompé la implementación, mirá el test
   ponerse rojo, restaurá, mirá ponerse verde. Un test que no se probó en rojo no prueba nada. Y si
   un test existente se pone rojo por tu cambio, **entendé por qué antes de tocarlo** — a veces el
   test tiene razón, y a veces te está pidiendo por escrito que lo actualices porque la heurística
   mejoró (pasó literalmente en esta tanda).
7. **Nunca `git checkout` / `git restore` / `git stash`** sobre archivos de trabajo. Para la mordida,
   copiá con `cp` y restaurá con `cp`.
8. **Dale a cada agente un SHA fijo**, nunca `main`, si vas a commitear en `main` mientras corre.
   Se perdieron 728 líneas correctas por eso.
9. **Watchdog**: un agente sin output por 600s muere; los procesos en background se cortan a ~650s y
   la suite tarda ~820s. Corré la suite con `setsid nohup` redirigiendo a archivo, y hacé que los
   agentes emitan progreso.
10. **Nunca toques nada bajo `~`** salvo `./build.sh --install --yes`, que es el camino sancionado
    (hace backup con rotación y rollback).
11. **El espejo `PROYECTO/ai/scripts/` tiene que quedar byte-idéntico** a `ai/scripts/` para
    `narration_lint.py`, `feature-state.py` y `feature_state_lib/cli_reporting.py`. Hay un test que
    lo exige. Después de tocar `Global/_canonical/` o `Global/_shared/`, corré `./build.sh`.

## Cómo verificar que arrancás bien

```bash
git log --oneline -1                                  # 5bf4820
git status --short | wc -l                            # 0
python3 ai/scripts/feature-state.py next 028-narracion-que-ensena
python3 ai/scripts/feature-state.py next 006-execution-graph
grep -c 'input=(vault_block' ai/scripts/set_agents_spawn.py   # 1 — el fix de seguridad
```

Gate de cierre para todo lo que hagas: suite en verde, `ai/scripts/verify.sh` → `VERIFY_PASS`,
`./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, instalar, commitear y pushear.
