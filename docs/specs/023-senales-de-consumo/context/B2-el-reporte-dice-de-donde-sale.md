# Context pack — B2-el-reporte-dice-de-donde-sale

Spec: `docs/specs/023-senales-de-consumo/spec.md`, **AC-04a, AC-04, AC-05**. Depende de **B1**, ya
aceptada.

## Lo que B1 dejó hecho, y lo que dejó abierto a propósito

B1 hizo dos cosas: la doctrina canónica ahora **exige** `--usage` al cerrar un run, y
`routing_core/usage.py` tiene un normalizador por runtime con la **muestra real del cable medida**
(`normalize_pi:111`, `normalize_claude_code:118`, `normalize_opencode:140`, `normalize_codex:165`,
despachados por `NORMALIZERS:180` / `normalize:188`).

Y `_usage_row` se endureció: un dict **no vacío** sin campos reconocidos ahora es `'invalid'` —un
descarte **contado**— en vez de `'ok'` con todo NULL.

**Lo que quedó abierto es tuyo.**

## AC-04a — el dato sigue perdido, ahora visiblemente

Medido por el implementer de B1:

- `ai/scripts/claude_code_spawn.py:602-605` adjunta
  `--usage '{"total_cost_usd": ..., "modelUsage": {...}}'`
- `ai/scripts/opencode_spawn.py:318-321` adjunta `--usage '{"tokens": {...}}'`

**Las dos formas ya viajan en cada dispatch** y `_usage_row` no las reconoce. Antes de B1 se
perdían en silencio; ahora se cuentan como `'invalid'`. Mejor, pero **el dato sigue perdido**.

Tu tarea: **cablear esos adaptadores a `routing_core/usage.py`** para que la forma que ya mandan se
traduzca. No inventes un formato nuevo ni cambies lo que los spawn scripts emiten: usá el
normalizador que ya existe y que ya midió el cable.

**Prueba obligatoria**: un dispatch por lane que hoy da `'invalid'` pasa a dar columnas **no-NULL**,
con `status_counts` **antes y después**. Si no podés ejercitar un lane de verdad, decilo "sin
verificar" en vez de simularlo y presentarlo como medido.

## AC-04 — el riesgo real es el doble conteo

`ai/scripts/cost-report.py` lee **los stores propios de cada CLI** (`:4-6`):

| Fuente | Path |
|---|---|
| OpenCode | `~/.local/share/opencode/opencode.db` (`:84`) |
| Claude Code | `~/.claude/projects/<enc-cwd>/**/*.jsonl` (`:113`) |
| Codex | rollouts (`:172`) |
| pi | `_pi_project_key` (`:221`) |

Y el harness ahora tiene **su propio** registro en `dispatches`. **Son dos mediciones del mismo
gasto**: si alguien las suma, cuenta doble.

El riesgo **no** es la etiqueta `"pi"` de `cost-report.py:312` —eso es cosmético—: es que las dos
fuentes se presenten juntas sin decir que son la misma plata contada dos veces.

**Dos secciones nombradas por su fuente, que nunca se suman entre sí.** Y si mostrás un total, es
por sección, jamás uno global.

## AC-05 — ninguna superficie muestra un total sin decir de dónde salió

Aplica a `cost-report.py` y a cualquier otra superficie que muestre gasto.

## Restricciones

- **Extendé ADR-0045**, no crees uno nuevo: es el mismo vocabulario de consumo.
- **No toques `_usage_row`**: B1 lo dejó como validador cerrado y endurecido. Vos traducís **antes**
  de que llegue ahí.
- **No inventes números.** Si un runtime no reporta, `absent` sigue siendo la respuesta correcta.
- **No estimes nada**: eso es B4.
- **No toques el sort key.**
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- **No toques la base real del usuario** (`~/.local/state/set-agentes/routing-v2/routing.db`) ni sus
  stores de CLI. Fixtures.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1092 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`. La
suite tarda ~12 min; sin `-f`, `tail` no emite un byte hasta EOF (ADR-0041).

## Evidencia

`docs/specs/023-senales-de-consumo/evidence/B2-implementer.md`, escrito **en el primer minuto**:
tabla AC → cambio (`archivo:línea`) → prueba; **`status_counts` antes y después** mostrando el paso
de `'invalid'` a columnas no-NULL por lane; la salida del reporte con las dos secciones nombradas;
y los gates.

**Por cada test nuevo: neutralizá el cambio, confirmá el rojo, revertí, pegá la prueba.** En 022
aparecieron **cuatro** guardas que decían cubrir algo que no miraban; en 023/B1 no hubo ninguna.
Mantené la racha.

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

Rollups y retención (B3) · estimación y etiquetas ESTIMADO (B4) · el sort key · `context_window` ·
el aislamiento roto de los módulos de test (preexistente, registrado).
