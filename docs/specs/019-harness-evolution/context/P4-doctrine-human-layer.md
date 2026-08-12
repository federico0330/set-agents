# Context pack — P4-doctrine-human-layer (ADR-0036 + ADR-0037)

Spec: `docs/specs/019-harness-evolution/spec.md`, AC-25..AC-29. Este paquete **no toca código de
producción**: es doctrina, comandos y skills. Depende de P3, que ya está implementado y en gate final.

## Objetivo

Cuatro cosas que cierran la capa humana que P3 dejó lista por debajo:

1. Que el cierre de paquete diga en la narración **qué cambió en tu cabeza**, no solo qué se hizo.
2. Que el `integrator` y el `architect` mantengan `docs/modules/` vivo por procedimiento, no por
   buena voluntad.
3. Que el orquestador **resuelva antes de preguntar** (ADR-0037).
4. Que exista `/explicar`: leer un módulo y devolver un trace humano del código real.

## Estado de P3 que heredás (leelo antes de escribir doctrina)

- `docs/modules/modules.toml` + 5 docs sembrados: `routing`, `estado`, `generacion-arboles`,
  `consola`, `narracion-notas`.
- Comandos ya existentes: `feature-state.py record-module-impact <fid> --package-id P --module <slug>
  --cambio "..." --modelo-mental "..."`, `module-impact-detect <fid> --package-id P` (no muta,
  reporta `candidates` y `unmatched_paths`), y `--module-impact-waived --reason "..."`.
- El gate: entrar a `INTEGRATION` exige `module_impacts` no vacío **o** waiver por cada paquete
  accepted; `done_ready` tiene el mismo check.
- **Partición del doc de módulo** (decisión registrada del orquestador, `ai/state/decisions-log.jsonl`,
  y ADR-0036 decisión 3): el bloque máquina emite `## Responsabilidad`, `## Posee` y
  `## Últimos cambios estructurales`; los otros seis headings son prosa humana sembrada y preservada.
  Hay una línea visible al final del bloque máquina que se lo avisa al lector. **Cuando escribas la
  doctrina de `architect` e `integrator`, esa partición es el hecho: no prometas regeneración
  automática de lo que es prosa humana.**
- `record-module-impact` ya imprime el bloque **Impacto humano**; AC-25 define su formato en la
  narración.

## AC-25 — `Global/_canonical/agents/orchestrator.md`

La sección `## Narración — protocolo de transparencia` empieza en `:637`. Los milestones narrados
están listados en `:645-650` y el cierre de paquete es uno de ellos.

Agregá al bloque de **cierre de paquete** un sub-bloque fijo:

```
Impacto humano:
Módulo: <slug>
Cambio de modelo mental: <qué cambió en cómo hay que pensar el sistema>
Tenés que saber: <lo que el usuario necesita tener presente de ahora en más>
```

Sale del `record-module-impact`, no se improvisa. Y **no toques** los registros `Cliente:`/
`Ingeniería:` (ADR-0027) ni el bloque de fin de turno (ADR-0033): son contratos vigentes, este
sub-bloque es aditivo.

## AC-26 — `integrator.md` y `architect.md`

- `Global/_canonical/agents/integrator.md`, `## Procedure` en `:15-22`: insertá un paso —
  correr `module-impact-detect`, registrar `record-module-impact` por cada módulo afectado (o el
  waiver con su razón), y verificar que `docs/architecture/overview.md` y los docs de los módulos
  tocados no queden stale. Es el rol natural: ya consolida la evidencia de entrega en `:20-22`.
- `Global/_canonical/agents/architect.md`, paso 7 en `:44-47` (el que manda mantener
  `docs/architecture/overview.md`): al diseñar un **módulo nuevo**, crear su entrada en
  `modules.toml` y su doc inicial. Encaja al lado del paso que ya existe; no lo reescribas entero.

## AC-27 — ADR-0037, "Resolvé antes de preguntar"

La `## Question policy` está en `Global/_canonical/agents/orchestrator.md:517-553`. Hoy tiene la
lista de lo askable y lo no-askable, y el único "no preguntes lo ya dicho" es el carve-out de
plataforma nombrada (ADR-0025.2, `:546-550`).

Insertá **ANTES** de la lista askable un protocolo con encabezado **exacto y testeable**:
`**Resolvé antes de preguntar (ADR-0037)**`. Contenido: ninguna pregunta sale sin pasar por cuatro
fuentes, en orden — (1) el pedido original del turno o de la feature, (2) `docs/notas/` (secciones
"Qué falta" y "Approach y decisiones"), (3) `ai/state/decisions-log.jsonl`, (4) la spec aprobada y
los ADRs. Lo que alguna fuente ya resuelve **se ejecuta con `log-decision`, no se pregunta**. El
carve-out de plataforma nombrada queda como **caso particular** de esta regla general, no como
excepción suelta.

Espejos de 2-3 líneas (no el texto entero) en las **fuentes** de `Global/_shared/` — rutas ya
verificadas por el orquestador con `ls`: `Global/_shared/CLAUDE.md`, `Global/_shared/AGENTS.pi.md`,
`Global/_shared/AGENTS.opencode.md`, `Global/_shared/AGENTS.codex.md` — y en la skill
`request-triage` (`Global/_canonical/skills/request-triage/SKILL.md`). Ojo: `Global/codex/AGENTS.md`,
`Global/opencode/AGENTS.md` y `Global/pi/AGENTS.md` son **generados** desde `_shared`; no los edites,
se regeneran con `./build.sh`.

## AC-28 — `/explicar`

Nuevo `Global/_canonical/commands/explicar.md` + skill `Global/_canonical/skills/explicar/SKILL.md`.
`generate.py` ya propaga commands y skills a los 4 árboles — no copies a mano, corré `./build.sh`.

Molde: `Global/_canonical/commands/consult.md` (frontmatter `description` + `agent`, cuerpo con
`$ARGUMENTS`). Contrato de `/explicar`:

- **read-only, sin estado de feature** (como `/consult`: no `init`, no pipeline).
- Entrada: una pregunta o el nombre de un módulo.
- Procedimiento: leer `modules.toml` y el doc del módulo → **seguir el código real desde los puntos
  de entrada** → devolver el trace en lenguaje humano, en registros `Cliente:` e `Ingeniería:`, con
  `file:line` como evidencia (ADR-0026).
- Si el doc del módulo está **stale** respecto del código, decirlo explícitamente y ofrecer
  regenerarlo. Esto es importante: es el mitigante que la decisión registrada sobre la partición del
  doc nombra como la red de contención de las cinco secciones humanas. No lo dejes como detalle.

## Restricciones

- **Editá SOLO `Global/_canonical/`.** Los otros cuatro árboles y `PROYECTO/` son **generados**:
  se regeneran con `./build.sh` y se verifican con `./build.sh --check`. Editar una copia a mano es
  un defecto.
- `tests/test_harness.py` assertea frases doctrinales **por grep**. Toda frase que agregues y que el
  AC nombre como exacta necesita su test. Y toda frase existente que muevas puede romper un grep:
  buscá antes (`grep -n "<frase>" tests/test_harness.py`).
- **`roles.tsv` NO cambia** (AC-29). `/explicar` no es un rol nuevo: es un comando que corre el
  orquestador.
- ADR-0037 primero, después test, después texto. Re-verificá con `ls docs/adr/` que `0037` esté
  libre e indexalo en `docs/adr/README.md`. AC-25/AC-26 son de ADR-0036, que ya existe: **extendelo**,
  no escribas un ADR nuevo para eso.
- Sin refactors oportunistas sobre los briefs de rol: la superficie mínima que el AC pide.

## Advertencia de proceso (leela, no es genérica)

Este paquete acumula, en la misma feature, **tres afirmaciones de verificación fabricadas** del rol
reparador — tablas que decían "verificado con tal comando" cuando el comando no decía eso. Está
registrado en `ai/state/decisions-log.jsonl`. **Cada afirmación de verificación tuya viene con el
comando pegado y su salida real.** Si no lo corriste, escribí "sin verificar": una conjetura marcada
es honesta, una sin marcar es un defecto.

## Validación local

`python3 -m unittest discover -s tests` (**`pytest` no está instalado**; el conteo sube, nunca baja) ·
`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh` y después `./build.sh --check` sin drift ·
`git diff --check` limpio.

Nota: correr `tests.test_harness` **aislado** produce ~72 errores `KeyError: 'set_agents_app'`
preexistentes (aislamiento de import), no son regresión tuya; usá `discover` o `verify.sh`.

Prueba viva que va como evidencia: verificar que `/explicar` quedó disponible en los **4 runtimes**
(listá los archivos generados) y que su contenido es idéntico al canónico.

## Evidencia esperada

`docs/specs/019-harness-evolution/evidence/P4-implementer.md`: tabla AC → cambio (`archivo:línea`) →
prueba; las frases doctrinales exactas que agregaste, con el test que las assertea; la lista de los 4
árboles con `/explicar` presente; y los gates pegados.

## Checkpoint

Si te acercás al límite de ejecución, escribí primero el progreso parcial y los próximos pasos
exactos en el archivo de evidencia, y recién ahí pará.

## Fuera de alcance

Código de producción (`ai/scripts/**`) salvo que un test lo exija · `docs/modules/**` y el motor de
render (P3, ya cerrado) · tools discovery y `coord_policy.py` (P5) · routing, billing y consola
(P1/P2, aceptados) · `roles.tsv`.
