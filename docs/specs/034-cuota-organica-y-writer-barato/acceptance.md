# 034 — criterios de aceptación (BDD)

Cada escenario es observable de punta a punta. Los tests de regresión se
escriben después de que el paquete converja; el runtime-verifier confirma
lo que tenga superficie. Los HOW (flags, campos JSON, slugs Cursor) son
UNVERIFIED para architecture; el Then no.

## Diagrama (actor → acción → observable)

```
FEDERICO / ORQUESTADOR              HARNESS                         ESTADO / REPORTE
        |                              |                                    |
        | "arreglá el copy en 2 files" |                                    |
        |----------------------------->|                                    |
        |                              | clasifica: 1-3, sin señal riesgo   |
        |                              | → modo quick-fix (no init scoped)  |
        |                              | implementer-barato edita           |
        |                              | gate local                         |
        |                              | log-quickfix --result done         |
        |<-----------------------------| bitácora / JSONL del quick-fix     |
        | gate ROJO en 1–3 (sin init)  | reintento local o escala; NO salvage|
        |                              |                                    |
        | "feature con SDD, 4 pkgs"    |                                    |
        |----------------------------->| init --mode feature                |
        |                              |   + señal user-asked-full-pipeline |
        |                              | PKG: implementer-barato (BASE, no @fast) |
        |                              | gate ROJO ─────────────────────────>
        |                              | 1 salvage (override; pin repair barato) |
        |                              | gate ROJO otra vez                 |
        |<-----------------------------| HUMAN_DECISION_REQUIRED            |
        |                              | cheap-rojo+salvage-rojo = +1 consecutivo |
        |                              |                                    |
        | (2 pkges sin green-on-first) | próximo: override más pesado       |
        |                              | (pin implementer.md no cambia)     |
        |                              | salvo frontier_cap lleno → para    |
        |                              |                                    |
        | Cursor: /implementer         | agente con model: <barato pin>     |
        |         /package-reviewer    | agente con model: <otra familia>   |
        |                              | o degradación ruidosa en evidencia |
        |                              |                                    |
        | cost-report --project …      | Sección 2: % green-on-first-attempt|
        |                              | y frontier_used/cap por feature    |
```

Escalada (misma columna, si el diff toca auth/dinero/PII/…):

```
quick-fix en vuelo ──señal nombrada──▶ scoped/feature + context pack (033 AC-6.1)
```

Un 1–3 archivos metido a `scoped` **sin** señal:

```
init --mode scoped (sin riesgo) ──▶ error nombrado ──▶ test AC-A.2 ROJO si se acepta
```

---

## PKG-A — ruteo orgánico

### AC-A.1 Doctrina unificada (quick-fix es el default de 1–3)

- **Given** el texto canónico de `request-triage` y `orchestrator.md`
  (hoy contradictorio: skill `:88-98` vs tabla `:122` e `init` default
  `scoped` en `feature-state.py:875-878`)
- **When** un operador o un test lee "cuál es el modo de un cambio 1–3
  archivos sin señal de riesgo"
- **Then** las tres superficies dicen lo mismo: (1) skill
  `request-triage`, (2) `orchestrator.md`, (3) el error nombrado
  `RISK_SIGNAL_REQUIRED` al `init --mode scoped`/`feature` sin señal.
  Default = quick-fix, `implement → gate → log-quickfix`. Ninguna llama
  `scoped` "default" para ese caso. El número 3 sigue cruzado con
  ADR-0020 (`orchestrator.md:24-41`).

### AC-A.2 Test de mordida: 1–3 archivos no entra a scoped sin señal

- **Given** un trabajo cuyo blast radius son 1–3 archivos y ninguna
  señal de la lista cerrada (dinero, migración, auth/PII, contrato
  público, multi-módulo, usuario pidió pipeline)
- **When** el harness registra el modo (o se intenta `init --mode scoped`
  / `feature` sin señal persistida)
- **Then** el modo observable es `quick-fix` **o** el `init` scoped/
  feature es rechazado con error nombrado. Un test dedicado **falla**
  si ese trabajo queda en `scoped`/`feature`. El fixture que lo
  engañaría: tres archivos de copy con `--mode scoped` y sin señal,
  y el test verde — prohibido.

### AC-A.3 Scoped/feature exigen señal persistida

- **Given** un `init` a `scoped` o `feature`
- **When** no hay señal de riesgo persistida por `feature-state.py`
- **Then** el comando falla con `RISK_SIGNAL_REQUIRED` y no crea (o no
  deja válido) el estado.
- **Given** la señal es uno de los tokens cerrados o
  `user-asked-full-pipeline`
- **When** `init` corre
- **Then** el estado queda en ese modo y la señal es legible después
  (status / JSON). Un JSON editado a mano no cuenta.

### AC-A.4 Quick-fix cierra con log-quickfix

- **Given** un quick-fix que llega a `done`
- **When** se cierra
- **Then** existe un evento `log-quickfix` con `--summary`, `--result done`,
  `--file` y `--gate` (`feature-state.py:1194-1201`). El verbo no se
  volvió opcional.

### AC-A.5 Precedencia con 033 AC-6.1

- **Given** un trabajo en quick-fix
- **When** se evalúa si hace falta `docs/specs/<feature>/context/<PKG>.md`
- **Then** no: no hay paquete. 033 AC-6.1 no aplica.
- **Given** el diff revela una señal de la lista
- **When** se escala
- **Then** el modo pasa a `scoped` o `feature` con la señal nombrada, y
  a partir de ahí rige 033 (context pack, panel, P001).
- **Given** un quick-fix (sin paquete) cuyo gate queda rojo
- **When** se evalúa salvage
- **Then** no hay salvage. Reintento local o escala con señal nombrada.

### AC-A.6 Ausencia de init no es fallo

- **Given** el universo de trabajos 1–3 sin señal
- **When** el camino correcto es no crear feature
- **Then** la ausencia de `ai/state/features/<id>.json` es el éxito, no
  un 0% de cumplimiento. El test de A.2 no exige un state file en el
  camino feliz.
- **And** `init --mode quick-fix` sigue existiendo (modo liviano con
  estado). El default 1–3 **no** llama `init`. Un `init --mode quick-fix`
  no pone AC-A.2 en rojo.

---

## PKG-B — escritor barato y salvage

### AC-B.1 Default code-rw = más barato/gratis que cumpla tools

- **Given** el catálogo vivo y `billing_rank`
  (`catalog.py:196-207`)
- **When** se resuelve el modelo de un rol `capability == code-rw`
  (`roles.tsv:11-17`)
- **Then** el default es el más barato/gratis que puede editar y correr
  validación local. A igual capacidad gana `billing_rank == 0`.
  `[areas.implement].opencode` deja de anclarse a
  `openai/gpt-5.6-fast` (`models.toml:109-113`) si ese id no es el más
  barato que cumple tools.
- **And** una feature nueva (paquete 1) usa ese BASE/pin barato, **no**
  `writer_tier="fast"` ni `implementer@fast` (`models.toml:240-241`;
  `generate.py:581-585` `@tier` es OpenCode-ONLY).

### AC-B.2 El test hot-path se reescribe, no se borra

- **Given** `tests/test_harness.py:733-766`
  `test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart`
- **When** corre la suite
- **Then**:
  - `product-analyst` **no** está en ningún loop que exija `-fast`.
  - `implementer` (y al menos `debugger` o `frontend-engineer`) aserta
    barato/free-primero, con la razón nueva en el comentario del test
    (patrón ADR-0044).
  - `package-reviewer` y `adversarial-judge` siguen en familia distinta
    a `implementer` (`:750-766` conservado).
- **And** el test se vio rojo al romper el pin barato (mordida). Borrar
  el test o dejarlo en `-fast` es fallo de este AC.

### AC-B.3 product-analyst es juicio, no escritor

- **Given** `roles.tsv:4` (`docs-rw` / `docs`) y ADR-0018 clase
  `decision`
- **When** se resuelve su modelo
- **Then** puede ser frontier. Ningún test lo obliga a `-fast` ni a
  `-free`.

### AC-B.4 Un salvage caro por paquete

- **Given** un paquete cuyo implementer-barato dejó el gate rojo
- **When** el orquestador continúa
- **Then** hay exactamente un salvage: `repair-agent` (u otra mutante
  fresca) invocada con **override** al modelo pesado, persistido por
  `feature-state.py` como salvage de ese paquete. El pin permanente de
  `repair-agent` sigue barato (AC-D.1). Sin override medido →
  `HUMAN_DECISION_REQUIRED`, no se cambia el pin.
- **And** ese salvage cuenta como frontier (AC-C.2).

### AC-B.5 Segunda falla = humano

- **Given** el salvage de AC-B.4 también deja el gate rojo
- **When** se evalúa un segundo salvage automático
- **Then** no ocurre. El estado es `HUMAN_DECISION_REQUIRED`.
- **And** un relaunch por plan/cuota exhausted (ADR-0011 D2) no se
  contabiliza como salvage ni como segundo salvage.

### AC-B.6 Auto-promotion a 2 consecutivos

- **Given** dos **paquetes** consecutivos de la misma feature cuyo
  implementer-barato **no** cerró green-on-first-attempt
- **When** arranca el próximo paquete de esa feature
- **Then** ese paquete usa un nivel más pesado. En Cursor: override de
  invocación al slug más pesado medido (o `HUMAN_DECISION_REQUIRED`);
  el pin de `implementer.md` no cambia; no hay agentes `@tier`.
- **And** el grano es máximo **+1 por paquete**. Cheap-rojo +
  salvage-rojo en el mismo paquete = un consecutivo. Salvage-rojo no
  suma. Un green-on-first-attempt del barato reinicia. Una feature nueva
  arranca en BASE barato, no en `writer_tier="fast"`. No se usa un %.

### AC-B.7 Ningún test se borra para pasar B

- **Given** cualquier test que hoy ancla `-fast` en
  `implementer`/`product-analyst`
- **When** B aterriza
- **Then** cada uno está reescrito conservando el invariante que sigue
  existiendo, o justificado por escrito si el invariante dejó de existir
  (solo `product-analyst`+`-fast` califica). El conteo neto de
  aserciones de independencia no baja.

---

## PKG-C — techo frontier y métrica

### AC-C.1 Contador distinto de MODE_BUDGETS

- **Given** `MODE_BUDGETS.scoped.max_spawns_per_package == 8`
  (`feature_state_lib/model.py:123-128`)
- **When** C aterriza
- **Then** ese 8 no cambió. El estado muestra `frontier_used / 4` por
  paquete y `frontier_used / 16` por feature, mutado solo por
  `feature-state.py`.

### AC-C.2 Qué cuenta como frontier

- **Given** un `record-spawn` (o verbo equivalente)
- **When** el modelo asignado no es el default barato/free de AC-B.1
- **Then** incrementa frontier. El salvage cuenta. Un juez en modelo
  pesado cuenta. `local-gate-runner` / P001 no cuentan.

### AC-C.3 Chocar el techo para, no sube max_spawns

- **Given** un paquete con 4 frontier ya usados (o una feature con 16)
- **When** se intenta otro despacho frontier
- **Then** el CLI rechaza con error nombrado y el orquestador persiste
  `HUMAN_DECISION_REQUIRED`. `max_spawns_per_package` no sube.

### AC-C.4 El techo gana a salvage y a promoción

- **Given** el próximo movimiento legal sería salvage (AC-B.4) o
  paquete promovido (AC-B.6) y el cupo frontier está lleno
- **When** se evalúa
- **Then** `HUMAN_DECISION_REQUIRED`. No se ignora el techo.

### AC-C.5 cost-report Sección 2 muestra la métrica

- **Given** `ai/scripts/cost-report.py --project … --since …`
- **When** imprime la Sección 2 (`:14-24`)
- **Then** aparece `% green-on-first-attempt` del implementer-barato
  por feature (y un total del filtro) más `frontier_used/cap`.
- **And** no hay un total que sume Sección 1 + Sección 2.

### AC-C.6 Universo de la métrica; el salvage no es first-attempt

- **Given** el universo = spawn implementer-barato que llegó a gate
- **When** el gate queda verde **sin** salvage en ese paquete
- **Then** cuenta en el numerador.
- **When** el gate queda verde **después** del salvage
- **Then** cuenta en el denominador y **no** en el numerador.
- **When** el paquete no tuvo implementer-barato o no corrió gate
- **Then** no entra al denominador (no es 0% ni 100%).
- **And** un test de mordida que trate salvage-verde como first-attempt
  queda rojo.

---

## PKG-D — pins Cursor (032 AC-06 superseded)

### AC-D.1 Cada rol Cursor tiene pin

- **Given** `./build.sh` genera `Global/cursor/agents/*.md`
- **When** se lee el frontmatter
- **Then** hay `model:` por rol y **no** todos son `inherit`. Los
  `code-rw` — **incluido `repair-agent`** — pinnean el barato de AC-B.1
  (slug Cursor UNVERIFIED hasta medición). Salvage pesado y promoción
  son override de invocación, no pin permanente. Los jueces de
  DEC-ROLES-FRONTIER pinnean otra familia.

### AC-D.2 product-analyst / architect pueden ser frontier

- **Given** los agentes Cursor de `product-analyst` y `architect`
- **When** se lee `model:`
- **Then** no están forzados al pin barato.

### AC-D.3 Independencia o degradación ruidosa

- **Given** pins de `implementer` y `package-reviewer` (y
  `adversarial-judge`)
- **When** hay dos familias en el catálogo Cursor medido
- **Then** el reviewer no comparte familia con el implementer.
- **When** no hay dos familias
- **Then** al menos el modelo es distinto, y la review degrada con
  evidencia no vacía (`record-subreview --evidence` /
  `finalize-review-panel --evidence`). Mismo modelo que el escritor
  mientras existe alternativa = fallo.

### AC-D.4 Tests 032 de inherit se reescriben, no se borran

- **Given** `validate_cursor_target` (`generate.py:735-748`) y
  `test_no_cursor_agent_pins_a_model` (`tests/test_harness.py:14016-14022`)
- **When** D aterriza
- **Then** ya no exigen `inherit` universal. Exigen pin presente,
  roster completo, `readonly` como 032 AC-01, e independencia o
  degradación explícita. El comentario cita 034 y 032 AC-06
  superseded. Borrar el test es fallo.

### AC-D.5 032 parcialmente superseded; el resto intacto

- **Given** el contrato 032 shippeado
- **When** D cierra
- **Then** AC-06 y la cláusula `model: inherit` de AC-01 están
  superseded por 034. Siguen: roster, name/description, readonly,
  skills, install, `--check`, bootstrap `00-harness.mdc`, no
  `hooks.json`. Cursor no es lane. `--route-decide` sigue prohibido
  (`generate.py:125-132`).

### AC-D.6 Doctrina instalada deja de mentir

- **Given** `.cursor/rules/00-harness.mdc`, `Global/cursor/AGENTS.md` y
  el bloque `CURSOR_DELEGATION_OVERRIDE` (`generate.py:125-139`)
- **When** se instala / genera
- **Then** ya no dicen "No model is pinned" / "every role inherits".
  Dicen: pin por rol, independencia o degradación ruidosa, sin
  `--route-decide`.

---

## Transversal

### AC-X.1 033 no se toca

- **Given** owned_paths de 034
- **When** el paquete cierra
- **Then** no incluye el wizard/tui de 033, las lanes, ni el job CI
  de skip ceiling. SHA `8fd15fe` sigue siendo la referencia de 033.

### AC-X.2 Estado solo por feature-state.py

- **Given** frontier, métrica, salvage, promoción, señal de riesgo
- **When** se persisten
- **Then** el único escritor es `ai/scripts/feature-state.py` (y sus
  lib). Editar el JSON a mano no es un camino verde.

### AC-X.3 Engram no entra

- **Given** este feature
- **When** se busca código o MCP Engram nuevo
- **Then** no hay. El vault Obsidian (ADR-0012 / ADR-0056) sigue
  siendo la memoria. Un spawn que no lee el vault es defecto de
  005/025, fuera de 034.
