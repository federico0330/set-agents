# 026 — El orquestador elige el modelo

- **Estado**: aprobado por pedido directo de Federico (2026-08-13), en respuesta a dos preguntas
  del orquestador. Sus palabras: *"elimina el hecho de que el modelo orquestador necesariamente
  tenga que correr en fast, y dejalo en la politica de cada modelo"* y *"que el orquestador pueda
  elegir que modelo quiere asignarle a cada instancia de agente. No quiero que este obligado a
  usar gpt para esos roles siempre"*.
- **Origen**: al intentar sacar a GPT del rol coordinador aparecieron dos obstáculos estructurales,
  los dos medidos.
- **ADR**: 0044.

## Los dos obstáculos, medidos

### D-1 — La política de latencia obliga a GPT en el camino caliente

`tests/test_harness.py:272-274` exige que `orchestrator`, `implementer` y `product-analyst` tengan
un `opencode_model` terminado en **`-fast`**. Medido: **`-fast` es una convención de nombre que
sólo existe en los modelos servidos por el proveedor `openai` de opencode** —
`openai/gpt-5.6-luna-fast`, `openai/gpt-5.6-sol-fast`, `openai/gpt-5.6-terra-fast`. Ni
`opencode-go` (18 modelos) ni `opencode-zen` (61) tienen **una sola** variante `-fast`.

Consecuencia: la política de latencia y la preferencia de proveedor son incompatibles por
construcción. Cambiar `[areas.coord]` a un modelo no-GPT pone la suite en rojo, y el orquestador
**no debilitó el test** para que su cambio pasara.

### D-2 — El orquestador no puede elegir el modelo de un spawn

`set_agents_app.py:605`, el conjunto cerrado de claves del descriptor de `--route-decide`:

```
{"role", "task_class", "risk", "review_of_run_id", "selected_runtime", "feature_id", "package_id"}
```

No hay ningún campo de modelo ni de proveedor. El orquestador puede pedir un **rol** y un
**runtime**, y el servicio decide el resto. Hoy la única forma de influir es
`--model-pin-set ROLE PROVIDER/MODEL`, que es **global y persistente por rol**, no por instancia.

Medido: con `[areas.coord]` sin tocar, los roles de juicio caen todos en GPT —
`adversarial-judge`, `package-reviewer`, `spec-challenger` y `architect` →
`openai-codex/gpt-5.6-luna`.

## Objetivo

Que la elección de modelo sea del orquestador, por instancia, dentro de las barreras que ya
existen — y que ninguna política del repo lo obligue a un proveedor.

## Paquetes

### PKG-1 — `latencia-por-modelo-no-por-sufijo`

- **AC-01**: el rol `orchestrator` deja de estar obligado al sufijo `-fast`. La política de
  latencia del camino caliente **sigue vigente para `implementer` y `product-analyst`**, que son
  los de alto volumen; el coordinador es una instancia larga y única, donde el criterio de
  elección es otro. El test se **reescribe con esa razón explícita**, no se borra ni se relaja:
  tiene que seguir fallando si `implementer` o `product-analyst` pierden su variante rápida.
- **AC-02**: `[areas.coord].opencode` pasa a un modelo no-GPT de **suscripción**
  (`opencode-go/grok-4.5` en `go-zen`; `opencode/grok-4.5` en `zen` y `local`). Se eligió
  `opencode-go` porque es suscripción: no consume la de Copilot ni el medido por token de zen.
  **Verificado al aplicarlo**: `grok-4.6` **no** está en `[catalog].opencode_zen`, por eso las
  lanes `zen` y `local` usan `grok-4.5`.
- **AC-03**: ADR-0044 registra que la latencia pasa a ser **una propiedad del modelo elegido, no
  un requisito del sufijo del nombre**, y por qué la regla se conserva para los dos roles de
  volumen. Deja escrito el límite: **en la lane de `codex` el coordinador sigue siendo GPT y no
  puede ser otra cosa** — el CLI de codex sólo sirve modelos de OpenAI.

### PKG-2 — `modelo-por-instancia`

- **AC-04**: el descriptor de `--route-decide` acepta una **preferencia de modelo por instancia**.
  El conjunto de claves permitido es cerrado a propósito (`set_agents_app.py:605`) y **sigue
  siéndolo**: se agrega la clave nueva al conjunto, nunca se abre.
- **AC-05**: la preferencia **no puede saltear ninguna barrera existente**. Un modelo pedido que
  viole independencia de reviewer, techo de catálogo, par auditado o tier requerido se **excluye
  con su razón nombrada**, exactamente como cualquier candidato. La preferencia mueve el orden,
  **nunca** abre la puerta. Test por cada barrera.
- **AC-06**: cuando el modelo pedido no es elegible, la decisión **lo dice**: un `reason_code`
  propio que nombre el modelo pedido y por qué no entró, en vez de degradar en silencio a otro.
  Precedente de código nombrado: `CATALOG_CEILING_REQUIRED` (022 PKG-2).
- **AC-07**: la preferencia por instancia es **efímera**. No se escribe en
  `model-preference.toml`, no altera el pin global, y no sobrevive al spawn. Los tres mecanismos
  quedan documentados juntos, con su alcance: `[areas.*]` (por área, en el repo), `--model-pin-set`
  (por rol, persistente, del usuario) y esta (por instancia, efímera).

## No-goals

- No se toca el sort key (`service.py:382`) ni se le agrega un factor.
- No se relaja la independencia de reviewer: sigue siendo exclusión dura por proveedor.
- No se cambia la política de latencia de `implementer` ni de `product-analyst`.
- No se convierte la preferencia en una autorización: la ruteabilidad sigue exigiendo probe vivo.
- No se toca `models.toml` más allá de `[areas.coord]`.

## Riesgos

1. **Que la preferencia se vuelva un bypass.** Es el riesgo central: AC-05 exige un test por
   barrera, y la preferencia entra **después** de las exclusiones, nunca antes.
2. **Que el test reescrito pierda poder.** En 022 aparecieron **cuatro** guardas que pasaban en
   verde con la fuente rota. El test de AC-01 tiene que ponerse rojo si `implementer` pierde su
   variante rápida: mordida obligatoria en las dos direcciones.
3. **Que la latencia empeore sin que nadie lo note.** El coordinador pasa a un modelo sin garantía
   de baja latencia. Se acepta explícitamente; si molesta, se cambia una celda de `models.toml`.

## Gates

Por paquete: `python3 -m unittest discover -s tests` en verde (**`pytest` no está instalado**;
base **1065 OK / 3 skips**), `./ai/scripts/verify.sh` → `VERIFY_PASS`, `./build.sh --check` →
`GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`, ACs con evidencia `file:line`. Review independiente en
otro proveedor, repair consolidado, delta review.

## Criterio de cierre

Abrir `opencode` y que el coordinador sea un modelo no-GPT de suscripción. Y que el orquestador
pueda pedir un modelo para un spawn puntual y **que se lo nieguen con una razón nombrada** cuando
ese modelo viole una barrera.
