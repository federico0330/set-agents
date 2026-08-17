# D5-vault-en-todo-spawn — delta review correctiva

**Fecha**: 2026-08-17. **Base**: `1014b02`. **Diff auditado**: `git diff 8091b0b..1014b02` acotado a
los cuatro spawners.

## Por qué existe este documento

D5 figuraba `accepted` con:

- `diff_ref = WORKTREE-D5-2026-08-17` — un worktree de agente, no un SHA.
- una sola review cuya evidencia era `D5-implementation.md`, **escrito por el propio implementer**.
- cero delta reviews, `verifications: 0`.

Sus hermanos D1–D4 tenían 2–4 gates y 1–2 delta reviews cada uno. Federico pidió la revisión que
nunca ocurrió.

**No pudo registrarse en el paquete**: 025 está en `DONE`, `record-spawn` falla con
`cannot record spawn from phase DONE` (`ai/scripts/feature-state.py:407-408`), `record-delta-review`
exige `DELTA_REVIEW` (`ai/scripts/feature_state_lib/cli_repair.py:279-280`) y `reopen` sólo aplica
desde `BLOCKED` (`ai/scripts/feature_state_lib/cli_lifecycle.py:527-528`). Registrado en
`ai/state/decisions-log.jsonl`, slug `d5-revision-correctiva-sin-camino-de-estado`. El hueco —una
feature cerrada cuya aceptación resulta defectuosa no tiene camino de corrección— queda expuesto.

**Independencia (ADR-0011)**: delta-reviewer con contexto limpio, proveedor y modelo distintos al
escritor (el implementer fue Cursor/Copilot).

## Veredicto: **fail** → reparado

### D5-DR01 — alta — fuga de contenido no confiable por argv

`ai/scripts/set_agents_spawn.py`. El carril pi era el único de los cuatro que transportaba el bloque
de vault por **argv** en vez de **stdin**. Los otros tres, confirmados: `claude_code_spawn.py:567`
(`input=stdin_text`), `codex_spawn.py:263`, `opencode_spawn.py:290`.

**Causa raíz, y es lo importante**: `24b4d8a` ("025/D5 checkpoint vault transport fixes") **había
arreglado esto** —`input=(vault_block or "")`, con un comentario que decía *"the fenced vault reaches
pi through stdin, never argv"*—. El commit `f688531`, rotulado **"Feature 028/029"** y tocando este
archivo fuera de su alcance declarado, **revirtió el arreglo y reescribió el comentario para
justificar la forma revertida**. Ni el mensaje de commit ni ninguna nota lo mencionan.

**Escenario**: cualquier spawn por pi con vault vinculado → hasta ~14 KB de contenido de vault
(fuente externa, sincronizada por Syncthing, no escrita por el harness) en el argv del hijo, visible
en texto claro por `ps aux` y `/proc/<pid>/cmdline` para cualquier usuario local. Es el vector que la
propia suite documenta y prohíbe para los otros tres carriles
(`tests/test_spawn_materialization.py:64-67`).

**Reparado**: transporte por stdin restaurado; el comentario ahora explica por qué, y nombra el
revert para que no vuelva a pasar en silencio.

### D5-DR02 — media — el test codificaba el defecto

`tests/test_harness.py:4156` era el único test del transporte de vault del carril pi, y a diferencia
de sus tres hermanos —que capturan `kwargs.get("input")`— capturaba `captured["tail"]` y afirmaba el
marcador de vault **en el último posicional de argv**. No sólo no detectaba D5-DR01: lo fijaba como
comportamiento esperado. El carril que filtraba era también el único cuyo test no podía ponerse rojo.

**Reparado**: el test captura stdin como sus hermanos, y agrega la aserción que faltaba —
`assertNotIn(marcador, argv)`, la propiedad de seguridad afirmada directamente.

**Mordida (RED→GREEN)**, con la implementación rota reintroducida a mano:

```
AssertionError: '<<<VAULT-MARKER-PI>>>' not found in ''
FAILED (failures=1)
```

restaurada:

```
Ran 1 test in 0.019s
OK
```

### D5-DR03 — baja — asimetría de cobertura, no defecto vivo

El anti-cacheo de fallos transitorios tiene test dedicado sólo en `codex_spawn` y `opencode_spawn`
(`tests/test_spawn_materialization.py:119-145`). Por inspección la implementación es idéntica y
correcta en los cuatro. No reparado: no hay defecto vivo, y queda anotado como deuda.

## Lo que sí se sostiene (verificado, no asumido)

- El fence de contenido no confiable es **uno solo** (`ai/scripts/context_pack.py:168`,
  `_mark_untrusted`), no cuatro copias divergentes. Se intentó atravesarlo con marcador literal
  falso, homoglifos fullwidth (`＜＜＜`/`＞＞＞`) y códigos invisibles intercalados: los tres fueron
  neutralizados.
- `ai/scripts/spawn_task_fence.py` unifica claude_code/codex/opencode.
- Degradación honesta: `_VAULT_NONE_LINKED_NOTE` y `_VAULT_DEGRADED_NOTE` distinguen "no hay vault"
  de "el lookup falló", idénticos en los cuatro. Ningún caso miente por omisión.

## Paridad de los cuatro carriles

| Carril | Transporte | Evidencia | Cachea sólo asentados | Tests de vault |
|---|---|---|---|---|
| `claude_code_spawn.py` | stdin | `:567 input=stdin_text` | sí | 7 |
| `codex_spawn.py` | stdin | `:263 input=compose_task(...)` | sí | 2 |
| `opencode_spawn.py` | stdin | `:290 input=stdin_text` | sí | 2 |
| `set_agents_spawn.py` (pi) | stdin *(reparado)* | `input=(vault_block or "")` | sí | 1 *(reescrito)* |
