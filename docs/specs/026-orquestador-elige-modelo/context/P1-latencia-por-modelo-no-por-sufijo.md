# Context pack — P1-latencia-por-modelo-no-por-sufijo

Spec: `docs/specs/026-orquestador-elige-modelo/spec.md`, **AC-01, AC-02, AC-03**. Paquete chico y
acotado. Nace de un pedido directo de Federico y de un intento previo del orquestador que **fue
revertido a propósito** por poner la suite en rojo.

## Lo que ya se intentó y por qué se revirtió

El orquestador cambió `[areas.coord].opencode` a un modelo no-GPT y la suite dio rojo en
`tests/test_harness.py:266`
(`test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`). **No tocó el test
para que su cambio pasara** y revirtió `models.toml` a verde. Ese es el trabajo de este paquete,
hecho bien.

## La medición que justifica el cambio

`tests/test_harness.py:272-274`:

```python
# Hot path (coord/analysis/implement/docs) runs on low-latency -fast variants.
for role in ("orchestrator", "implementer", "product-analyst"):
    self.assertTrue(rows[role]["opencode_model"].endswith("-fast"), role)
```

Medido con `opencode models <provider> --pure`: el sufijo `-fast` **sólo existe en el proveedor
`openai` de opencode** (`gpt-5.6-luna-fast`, `gpt-5.6-sol-fast`, `gpt-5.6-terra-fast`).
`opencode-go` (18 modelos) y `opencode-zen` (61) **no tienen ninguno**.

O sea: la aserción no expresa "baja latencia", expresa **"tiene que ser de OpenAI"**. Ese es el
defecto conceptual que este paquete corrige.

## TAREA

**AC-01** — El rol `orchestrator` deja de estar obligado al sufijo. **La regla se conserva para
`implementer` y `product-analyst`**, que son los de alto volumen; el coordinador es una instancia
larga y única donde el criterio es otro.

**El test se reescribe con esa razón escrita adentro, no se borra ni se relaja.** Tiene que seguir
poniéndose **rojo** si `implementer` o `product-analyst` pierden su variante rápida. Probalo en las
dos direcciones y pegá el rojo.

**AC-02** — `[areas.coord].opencode` pasa a:

```toml
opencode = { "go-zen" = "opencode-go/grok-4.5", "zen" = "opencode/grok-4.5", "local" = "opencode/grok-4.5" }
```

**Ojo, ya verificado**: `grok-4.6` **no** está en `[catalog].opencode_zen`, por eso zen y local
usan `grok-4.5`. Se eligió `opencode-go` en la lane principal porque es **suscripción**: no consume
la de Copilot ni el medido por token de zen.

**AC-03** — **ADR-0044**: la latencia pasa a ser una propiedad del modelo elegido, no un requisito
del sufijo del nombre. Escribí por qué la regla se conserva para los dos roles de volumen, y el
límite honesto: **en la lane de `codex` el coordinador sigue siendo GPT y no puede ser otra cosa**,
porque el CLI de codex sólo sirve modelos de OpenAI.

## Restricciones

- **No toques la parte del test que separa a los reviewers** (`:285-291`, `package-reviewer` y
  `adversarial-judge` en `openai/gpt-5.5`, familia distinta de la del implementer). Es otra
  garantía, de 015, y no es de este paquete.
- No toques `models.toml` más allá de `[areas.coord]`.
- **No uses `git checkout`, `git restore` ni `git stash`.** Para morder y restaurar: `cp` y `cp`.
- Después de tocar `models.toml`: `./build.sh` y después `./build.sh --check`.

## Validación

`python3 -m unittest discover -s tests` (**`pytest` NO está instalado**; base **1065 OK / 3 skips**)
· `./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `GLOBAL_TREE_SYNC_OK` +
`BUILD_CHECK_PASS` · `git diff --check` limpio.

**Corré los comandos largos así:** `ai/scripts/heartbeat-run.py --interval 20 -- <comando>`. La
suite tarda ~12 minutos; sin `-f`, `tail` no emite un byte hasta EOF y el watchdog te mata a los
600 s (ADR-0041).

## Evidencia

`docs/specs/026-orquestador-elige-modelo/evidence/P1-implementer.md`, escrito **en el primer
minuto**: tabla AC → cambio (`archivo:línea`) → prueba; **la mordida del test reescrito en las dos
direcciones** (romper `implementer` ⇒ rojo; el orquestador con un modelo no-GPT ⇒ verde); la salida
de `Global/opencode/opencode.json` mostrando el `model` nuevo; y los gates.

En la feature anterior aparecieron **cuatro** guardas que decían cubrir algo que no miraban, todas
verdes con la fuente rota. **Este paquete reescribe un test: si el reescrito pierde poder de
detección, sos la quinta.**

**Cada bloque literal, o marcado como recortado.** Si no lo corriste, "sin verificar".

## Fuera de alcance

La preferencia de modelo por instancia (P2) · el sort key · los otros roles que caen en GPT
(`adversarial-judge`, `package-reviewer`, `spec-challenger`, `architect`) · la política de latencia
de `implementer` y `product-analyst` · el aislamiento roto de los módulos de test (preexistente,
registrado).
