# Context pack — C2-modelstoml-neutro

Spec: `docs/specs/024-listo-para-terceros/spec.md`, **AC-03, AC-04, AC-05**. Depende de **C1**, ya
aceptada: el estado ya no viaja en el clon.

## El defecto, medido

`models.toml:6-10` fija las suscripciones **de Federico**:

```toml
[subscriptions]
anthropic = true
ollama = false
openai = true
zen = true
```

Un tercero que clone hereda esas cuatro afirmaciones sobre su propia máquina. Y peor: los `true`
**apagan la red tri-estado** que 022 construyó. `models_config.py:379-397` implementa el
precedente de ADR-0029 — un `true`/`false` explícito es intención curada, y **ausente = auto**, que
es donde el probe decide. Con todo declarado, el probe nunca decide nada.

## AC-05 es el que desbloquea todo lo demás. Leelo primero.

Hoy el wizard **reescribe el `models.toml` trackeado**. Eso ensucia el árbol, y
`tree_clean()` (`set_agents_app.py:1079-1080`) es literalmente
`git status --porcelain == ""`. Resultado: **cualquiera que use el wizard queda con `--update`
bloqueado para siempre.**

La salida es un **overlay de configuración del usuario en `STATE_DIR`**, con el precedente que ya
existe: `MODEL_PREFERENCE_PATH` (`set_agents_app.py:106`) y sus escrituras atómicas. El repo trae
los defaults; el usuario escribe **al lado**, no encima.

Sin AC-05, AC-03 y AC-04 son cosméticos: neutralizás el archivo y el primer uso del wizard lo vuelve
a ensuciar.

## TAREA

**AC-03** — `[subscriptions]` pasa a **ausente = auto**. Sacá las declaraciones de Federico. Un
`false` explícito sigue siendo intención curada y sigue muriendo; lo que cambia es que **el default
deja de ser una afirmación sobre una máquina ajena**.

**AC-04** — Dos cosas medidas:

1. El small model exige Zen en **las tres** lanes (`models.toml:46`, incluida `"local"` con
   `opencode/north-mini-code-free`). En una lane que se llama local, eso es una contradicción.
2. **La lane `local` no es local.** Sus modelos son `openai/gpt-5.4`, `opencode/grok-4.5`,
   `openai/gpt-5.5` — todos remotos. Renombrala a lo que realmente es.

El rename toca varias tablas de `models.toml` y probablemente `models_config.LANES`. **Buscá todos
los sitios antes de tocar uno**: `grep -rn '"local"' models.toml ai/scripts/`.

**AC-05** — Overlay del usuario en `STATE_DIR`. El repo trae defaults; el usuario escribe al lado.
Y **el wizard deja de ensuciar el árbol**, que es lo que desbloquea `--update`.

## La trampa

**No le rompas la máquina a Federico.** Su `models.toml` actual tiene sus suscripciones reales y su
coordinador en `opencode-go/grok-4.5` (de 026). Si el overlay no migra lo que él ya tiene, su
próximo arranque decide distinto sin avisarle.

**La migración es parte del paquete, no un extra**: lo que hoy está en el `models.toml` trackeado y
es específico de esta máquina tiene que terminar en su overlay, y el archivo del repo quedar neutro.
Probá que después de la migración **sus decisiones de ruteo son las mismas**.

## Restricciones

- **ADR-0047 ya existe** (C1). Para esto usá **ADR-0048** (`ls docs/adr/` para confirmar, indexalo
  en `docs/adr/README.md`).
- **No toques el sort key** ni la lógica de ruteo.
- **No toques `ai/state`** ni la siembra: eso fue C1.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- Después de tocar `models.toml`: `./build.sh` y `./build.sh --check`.
- **No toques nada bajo `~`** salvo, si el diseño lo exige, escribir el overlay en `STATE_DIR` —
  y en ese caso **tomá backup antes** y decilo en la evidencia.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1110 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh && ./build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`
(ADR-0041).

## Evidencia

`docs/specs/024-listo-para-terceros/evidence/C2-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **la prueba de que las decisiones de ruteo de esta
máquina no cambian tras la migración**; la prueba de que el wizard ya **no** ensucia el árbol y
`tree_clean()` sigue verde después de usarlo; el rename de la lane con todos sus sitios; y los
gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** Ya van
cinco guardas huecas en este proyecto. No escribas la sexta.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

El primer arranque y `ROUTING_UNCONFIGURED` (C3) · `LICENSE` y la matriz de soporte (C4) · el sort
key · el aislamiento roto de los módulos de test (preexistente, registrado) · features 025 y 026.
