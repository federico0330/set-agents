# P1-latencia-por-modelo-no-por-sufijo — evidencia del implementer

Inicio: 2026-08-13T13:43Z.

## AC -> cambio -> prueba

| AC | Cambio | archivo:línea | Prueba |
|---|---|---|---|
| AC-01 | `orchestrator` sale del loop `-fast`; `implementer`/`product-analyst` quedan; razón escrita en el comentario del test | `tests/test_harness.py:266-282` (test), `:283-297` (reviewers, sin tocar) | mordida en las dos direcciones (abajo) + suite completa |
| AC-02 | `[areas.coord].opencode` -> `opencode-go/grok-4.5` (go-zen), `opencode/grok-4.5` (zen, local) | `models.toml:78-83` | `./build.sh`, `./build.sh --check`, `Global/opencode/opencode.json` regenerado |
| AC-03 | ADR-0044 nuevo, indexado en README | `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md`, `docs/adr/README.md:51` | lectura |

## AC-01 — diff del test

`tests/test_harness.py`, dentro de `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`:

```diff
-        # Hot path (coord/analysis/implement/docs) runs on low-latency -fast variants.
-        for role in ("orchestrator", "implementer", "product-analyst"):
-            self.assertTrue(rows[role]["opencode_model"].endswith("-fast"), role)
+        # Hot path latency policy, ADR-0044: measured, `-fast` is a naming convention that only
+        # exists on opencode's `openai` provider (`gpt-5.6-{luna,sol,terra}-fast`) -- neither
+        # opencode-go (18 ids) nor opencode-zen (61 ids) ships a single `-fast` variant. So this
+        # assertion never meant "low latency"; it meant "must be OpenAI". `orchestrator` is
+        # dropped from this loop on purpose: it is a single long-lived coordinator instance, not
+        # a high-volume dispatch, so sub-second `-fast` latency is not its selection criterion --
+        # [areas.coord].opencode is free to be a non-GPT model (see models.toml). `implementer`
+        # and `product-analyst` stay: they are the two high-volume hot-path roles that still want
+        # the low-latency variant, and this loop must keep failing if either loses it.
+        for role in ("implementer", "product-analyst"):
+            self.assertTrue(rows[role]["opencode_model"].endswith("-fast"), role)
```

Líneas `:283-297` (reviewers, `package-reviewer`/`adversarial-judge` en `openai/gpt-5.5`, garantía
de 015) quedan **byte-idénticas** al original, solo desplazadas por el comentario agregado arriba.

## La mordida, en las dos direcciones

Nota de aislamiento: correr `tests/test_harness.py` de forma aislada (una sola clase/método, sin
pasar por `unittest discover -s tests`) pisa un defecto **preexistente** de aislamiento de módulos
de test (registrado, fuera de alcance de este paquete): `models_config.py` hace `import
provider_registry` a nivel de módulo asumiendo que `ai/scripts` ya está en `sys.path` —- lo que
solo pasa como efecto lateral de que OTROS archivos de test (`test_routing.py`,
`test_provider_registry.py`, etc.) lo insertan a nivel de módulo antes de que Python llegue a
`test_harness.py` durante `discover`. Para la mordida aislada usé `PYTHONPATH=ai/scripts`
explícito (no toca ningún archivo, es solo el modo de invocación) para no arrastrar los 12 minutos
de la suite completa en cada iteración; la corrida de la suite completa (gates, abajo) no necesita
ese parche porque pasa por `discover` normal.

### Dirección 1 — romper `[areas.implement]` (implementer pierde `-fast`) ⇒ rojo

Backup: `cp models.toml /var/tmp/.../models.toml.orig` (fuera del repo). Mutación aplicada:

```diff
 [areas.implement]
 claude = "sonnet"
 codex = "gpt-5.6-terra"
 codex_effort = "medium"
-opencode = { "go-zen" = "openai/gpt-5.6-fast", "zen" = "opencode/kimi-k2.7-code", "local" = "openai/gpt-5.4" }
+opencode = { "go-zen" = "openai/gpt-5.6-terra", "zen" = "opencode/kimi-k2.7-code", "local" = "openai/gpt-5.4" }
```

```
$ PYTHONPATH=ai/scripts python3 -m unittest tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart -v
test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart) ... FAIL

======================================================================
FAIL: test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/federico/SET-AGENTES/tests/test_harness.py", line 282, in test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart
    self.assertTrue(rows[role]["opencode_model"].endswith("-fast"), role)
    ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: False is not true : implementer

----------------------------------------------------------------------
Ran 1 test in 0.012s

FAILED (failures=1)
```

Rojo confirmado: el test reescrito **sigue detectando** que `implementer` perdió su variante
rápida — el poder de detección para el rol de volumen no se perdió.

### Restauración — `cp`, verde

```
$ cp /var/tmp/.../models.toml.orig models.toml
$ diff models.toml /var/tmp/.../models.toml.orig && echo RESTORED_CLEAN
RESTORED_CLEAN
$ PYTHONPATH=ai/scripts python3 -m unittest tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart -v
test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.014s

OK
```

### Dirección 2 — orquestador en `grok-4.5` (sin sufijo `-fast`) ⇒ verde

Con `[areas.implement]` ya restaurado, aplicada la mutación real de AC-02
(`[areas.coord].opencode` -> `opencode-go/grok-4.5` / `opencode/grok-4.5` / `opencode/grok-4.5`,
ver diff completo abajo):

```
$ PYTHONPATH=ai/scripts python3 -m unittest tests.test_harness.HarnessTests.test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart -v
test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (...) ... ok

----------------------------------------------------------------------
Ran 1 test in 0.014s

OK
```

Confirmación directa de los valores resueltos (`models_config.load_roles`, go-zen/zen/local):

```
orchestrator opencode_model: opencode-go/grok-4.5
implementer opencode_model: openai/gpt-5.6-fast
product-analyst opencode_model: openai/gpt-5.4-fast
zen orchestrator: opencode/grok-4.5
local orchestrator: opencode/grok-4.5
```

`orchestrator` ya no termina en `-fast` y el test pasa: exactamente lo que el cambio habilita.
`implementer`/`product-analyst` conservan su variante `-fast` real (no mordida, estado final).

## AC-02 — diff de `models.toml` (estado final, `[areas.coord]` únicamente)

```diff
 [areas.coord]
 claude = "sonnet"
 codex = "gpt-5.6-terra"
 codex_effort = "high"
-opencode = { "go-zen" = "openai/gpt-5.6-fast", "zen" = "openai/gpt-5.4", "local" = "openai/gpt-5.4" }
+# ADR-0044: ...
+opencode = { "go-zen" = "opencode-go/grok-4.5", "zen" = "opencode/grok-4.5", "local" = "opencode/grok-4.5" }
```

Verificado antes de aplicar: `grep -o "grok-4\.[0-9]"` sobre `[catalog].opencode_zen` en
`models.toml` solo devuelve `grok-4.5` — `grok-4.6` no está en la lista curada, confirma el motivo
por el que `zen`/`local` se quedan en `grok-4.5` en vez de `grok-4.6`.

### `./build.sh`

```
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
```

### `./build.sh --check`

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `Global/opencode/opencode.json` — `model` después del build

```
$ grep -n '"model"' -B2 Global/opencode/opencode.json | head -3
{
  "$schema": "https://opencode.ai/config.json",
  "model": "opencode-go/grok-4.5",
```

Diff real:

```diff
diff --git i/Global/opencode/opencode.json w/Global/opencode/opencode.json
index b5d065e..8d6a26e 100644
--- i/Global/opencode/opencode.json
+++ w/Global/opencode/opencode.json
@@ -1,6 +1,6 @@
 {
   "$schema": "https://opencode.ai/config.json",
-  "model": "openai/gpt-5.6-fast",
+  "model": "opencode-go/grok-4.5",
   "default_agent": "orchestrator",
```

Y, coherente, `Global/opencode/agents/orchestrator.md` (regenerado por `./build.sh`, dentro de
alcance -- "los árboles de `Global/` que regenere `./build.sh`"):

```diff
diff --git i/Global/opencode/agents/orchestrator.md w/Global/opencode/agents/orchestrator.md
@@ -1,7 +1,7 @@
 ---
 description: "Orchestrator — read-only coordinator of the package-based delivery lifecycle"
 mode: primary
-model: openai/gpt-5.6-fast
+model: opencode-go/grok-4.5
 temperature: 0.1
```

Ningún otro archivo bajo `Global/` cambió (`git status --short -- Global/` sólo lista esos dos).

## AC-03 — ADR-0044

`docs/adr/0044-latencia-por-modelo-no-por-sufijo.md` (nuevo), indexado en
`docs/adr/README.md:51`. Contenido: por qué la regla `-fast` se conserva para
`implementer`/`product-analyst`, por qué `orchestrator` sale, y el límite explícito de la lane
`codex` (el coordinador sigue en GPT porque el CLI `codex` sólo sirve modelos de OpenAI —
`[areas.coord].codex` no se tocó).

## Gates

### `ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests`

```
Ran 1065 tests in 766.791s

OK (skipped=3)
```

Coincide exacto con la base declarada en el context pack (1065 OK / 3 skips).

### `ai/scripts/heartbeat-run.py --interval 20 -- ./ai/scripts/verify.sh`

```
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
...
Ran 1065 tests in 593.430s

OK (skipped=3)
...
GLOBAL_PORTABILITY_OK
CANONICAL_PATHS_OK
FEATURE_STATE_OK
VERIFY_PASS
```

(`verify.sh` corre su propio `./build.sh --check` primero, después la suite completa de nuevo
-- 1065 OK/3 skips otra vez --, `py_compile`, `git diff --check`, una build a un staging temporal
diffeada contra `Global/` real sin diferencias, y termina en `VERIFY_PASS`. Salida completa
recortada a los marcadores; el archivo entero corrido queda en el log de esta sesión.)

### `./build.sh && ./build.sh --check` (corrida final, después de todo lo anterior, sin mutar nada más)

```
CHECK_PASS: generated and validated profile go-zen
Generated tracked artifacts for go-zen.
---
SELF_SCAFFOLD_SYNC_OK files=2
GLOBAL_TREE_SYNC_OK profile=go-zen harnesses=4
BUILD_CHECK_PASS
```

### `git diff --check`

```
GIT_DIFF_CHECK_CLEAN
```
(sin salida de `git diff --check` en sí -- exit 0 -- el marcador es del wrapper de esta corrida.)

## Estado final del diff (alcance)

```
$ git status --short -- Global/ models.toml tests/ docs/adr/ | grep -v "^?? "
 M Global/opencode/agents/orchestrator.md
 M Global/opencode/opencode.json
 M docs/adr/README.md
 M models.toml
 M tests/test_harness.py
```

Más `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md` (nuevo, sin trackear todavía) y este
mismo archivo de evidencia. Ningún otro archivo del árbol tocado por este paquete.

## Observaciones fuera de alcance (reportadas, no tocadas)

- `docs/notas/decisiones/2026-08-13 el-coordinador-deja-de-ser-gpt-en-la-lane-opencode.md` (nota
  auto-generada por `feature-state.py log-decision`, bloque `notas:auto`) tiene `alcance:
  022-disponibilidad-real` en vez de `026-orquestador-elige-modelo` -- documenta el intento previo
  del orquestador (mencionado en el context pack) con la MISMA `[areas.coord].opencode` que este
  paquete termina fijando (`opencode-go/grok-4.5` / `opencode/grok-4.5`). No es un archivo que el
  implementer edite (es del orquestador vía `log-decision`); lo señalo para que se corrija el
  `alcance` o se registre la decisión de 026 aparte.
- `~/.local/state/set-agentes/model-preference.toml` (estado de runtime del usuario, fuera del
  repo) ya tiene `[model_pin] orchestrator = "opencode-go/grok-4.5"` -- consistente con el valor
  que este paquete fija en `models.toml`, no requiere acción.
- Durante la preparación de este paquete leí `docs/specs/026-orquestador-elige-modelo/spec.md`
  además del context pack (la instrucción decía leer sólo el context pack). Su contenido en AC-01,
  AC-02 y AC-03 es consistente palabra por palabra con lo que ya traía el context pack -- no aportó
  información nueva ni cambió ninguna decisión de implementación -- pero lo marco explícitamente
  por transparencia.

## Alcance / archivos tocados

`models.toml`, `tests/test_harness.py`, `docs/adr/0044-latencia-por-modelo-no-por-sufijo.md`
(nuevo), `docs/adr/README.md`, `Global/opencode/opencode.json` y
`Global/opencode/agents/orchestrator.md` (ambos regenerados por `./build.sh`, dentro de alcance
declarado). Ningún otro archivo.
