# Context pack — P2-modelo-por-instancia

Spec: `docs/specs/026-orquestador-elige-modelo/spec.md`, **AC-04..AC-07**. Depende de **P1**, ya
aceptada.

## El pedido, en las palabras de Federico

*"Que el orquestador pueda elegir qué modelo quiere asignarle a cada instancia de agente. No quiero
que esté obligado a usar gpt para esos roles siempre."*

## El defecto, medido

`ai/scripts/set_agents_app.py:605`, el conjunto **cerrado** de claves del descriptor de
`--route-decide`:

```python
allowed = {"role", "task_class", "risk", "review_of_run_id", "selected_runtime", "feature_id", "package_id"}
```

No hay ningún campo de modelo ni de proveedor. El orquestador puede pedir un **rol** y un
**runtime**; el resto lo decide el servicio.

Los tres mecanismos que existen hoy, y por qué ninguno alcanza:

| Mecanismo | Alcance | Por qué no alcanza |
|---|---|---|
| `[areas.*]` en `models.toml` | por área, en el repo | global y versionado; no es por instancia |
| `--model-pin-set ROLE M` | por rol, persistente, del usuario | **pega a todos** los spawns de ese rol |
| — | por instancia | **no existe** |

Medido: con el pin puesto, `--route-decide` para `orchestrator` devuelve
`MODEL_PINNED opencode-go/grok-4.5`. Funciona, pero es global: no podés pedir un modelo para *este*
spawn y otro para el siguiente.

## TAREA

**AC-04** — El descriptor acepta una preferencia de modelo por instancia. **El conjunto de claves
es cerrado a propósito y sigue siéndolo**: agregás la clave nueva al conjunto, nunca lo abrís. Una
clave desconocida tiene que seguir dando `ROUTING_INPUT_INVALID` con `rc=2`, como hoy.

**AC-05 — es el corazón del paquete.** La preferencia **no puede saltear ninguna barrera**. Un
modelo pedido que viole cualquiera de estas se excluye con su razón nombrada, igual que cualquier
candidato:

- independencia de reviewer (`service.py:353`, `REVIEW_PROVIDER_CONFLICT` — exclusión **dura** por
  proveedor)
- `REVIEW_MODEL_CONFLICT` (`:347`)
- techo de catálogo (`resolve_ceiling`, 022/P2)
- par auditado (`_PAIR_COMMANDS`)
- tier insuficiente (`TIER_INSUFFICIENT`)
- `CONTEXT_MISSING`

**La preferencia mueve el ORDEN, nunca abre la puerta.** Entra **después** del bucle de exclusiones,
como factor de sort — no antes. Mirá cómo lo hace `_bias_rank` (`service.py`, insertado *entre*
tier y `curated_priority`, "never before the independence/tier boundary"): ese es el precedente
exacto y la posición correcta.

**Un test por barrera.** Cada uno pide explícitamente un modelo que la viola y assertea que **no**
se eligió y que la exclusión trae su razón.

**AC-06** — Cuando el modelo pedido no es elegible, la decisión **lo dice**: un `reason_code` propio
que nombre el modelo pedido y por qué no entró, en vez de degradar en silencio a otro. Precedente
de código nombrado: `CATALOG_CEILING_REQUIRED` (022/P2), que existe justamente porque el genérico
no decía nada.

**AC-07** — La preferencia es **efímera**: no se escribe en `model-preference.toml`, no altera el
pin global, no sobrevive al spawn. Y los **tres** mecanismos quedan documentados juntos con su
alcance, en ADR-0044 (extendelo, no crees uno nuevo).

## La trampa de este paquete

Es el paquete más fácil de convertir en un bypass. Si la preferencia se aplica **antes** de las
exclusiones, o si "no elegible" degrada en silencio, construiste exactamente lo que la spec prohíbe
— y con buena intención, porque "el usuario lo pidió".

**El usuario pidió poder elegir, no poder saltear.** Un modelo que viola la independencia del
reviewer tiene que ser negado, aunque lo haya pedido el orquestador.

## Restricciones

- **No toques el sort key en su orden relativo existente** (`service.py:382`). Insertás, no
  reordenás.
- No relajes la independencia de reviewer.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- No conviertas la preferencia en autorización: la ruteabilidad sigue exigiendo probe vivo.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1065 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`. La
suite tarda ~12 min; sin `-f`, `tail` no emite un byte hasta EOF y el watchdog te mata a los 600 s
(ADR-0041).

## Evidencia

`docs/specs/026-orquestador-elige-modelo/evidence/P2-implementer.md`, escrito **en el primer
minuto**: tabla AC → cambio (`archivo:línea`) → prueba; **un test por barrera** con la salida
literal de cada negación y su razón; la prueba de que la preferencia entra después de las
exclusiones (no antes); la prueba de que no escribe nada en disco; y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En 022
aparecieron **cuatro** guardas que decían cubrir algo que no miraban. En 026/P1 el test reescrito sí
conservó poder de detección — mantené esa racha.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

El sort key en su orden existente · los otros roles que caen en GPT por default (eso se resuelve
usando esta capacidad, no cambiando `models.toml`) · el consumo (023) · el aislamiento roto de los
módulos de test (preexistente, registrado).
