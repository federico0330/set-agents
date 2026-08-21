# Context pack — PKG-C · `TIPS-USO.md` al día (y el puntero que evita la contradicción)

Spec: `docs/specs/035-panel-honesto-consola-y-tips/spec.md`
(hash `296e051fccfd0cea2f222cc7061987f6b66507d9ed2b10539d7e58ea3169331c`).
Aceptación: `acceptance.md` § PKG-C. Tareas: `tasks.md` T-201..T-204.
**ACs:** AC-C.1 … AC-C.6.

**Objetivo.** `TIPS-USO.md` deja de afirmar un control plane único y de omitir árboles que
el repo genera; `docs/COMO-FUNCIONA.md` deja de decir que TIPS está atrasado. Las dos
superficies se mueven en el **mismo** paquete (DEC-TIPS-POINTER) o el repo se contradice al
revés. Solo se corrigen afirmaciones **medidamente falsas**.

## Paths (qué tocar y por qué)

- `TIPS-USO.md` (156 líneas, `wc -l` 2026-08-20) — las cuatro zonas medidas:
  - `:5-14` "**OpenCode is the orchestration control plane**" … "The other two harnesses
    are single-task lanes, not orchestrators" → falso: Cursor es anfitrión desde 032 y
    Claude tiene el roster completo (AC-C.1). **La advertencia sobre Codex de `:12-14`
    (`spawn_agent` hereda el modelo de sesión y puede forkear el transcript) se CONSERVA**:
    es una medición, no doctrina vieja.
  - `:3` "versioned source for OpenCode, Claude Code, and Codex" → `ls Global/` da
    **cinco** árboles (`claude-code`, `codex`, `cursor`, `opencode`, `pi`) más `_canonical`
    y `_shared` (AC-C.2).
  - `:45` `Global/{opencode,claude-code,codex}` → falta `cursor` y `pi` (AC-C.2).
  - `:127-129` "Native agents" (tres bullets) → falta Cursor (`~/.cursor/agents/*.md`,
    032/ADR-0063) y `pi` (AC-C.2).
  - `:133-134` "the three harnesses' own session stores … plus a fourth `pi` lane" →
    `ai/scripts/cost-report.py:20-23` y `:836-843` cubren Cursor explícitamente ("every
    runtime including Cursor"; vacío en la lane de routing porque los subagentes nativos de
    Cursor no pasan por los CLIs). La redacción nueva **no promete más que lo medido**
    (AC-C.3).
- `docs/COMO-FUNCIONA.md` (492 líneas) — el lazo:
  - `:227-230` hoy dice "`TIPS-USO.md` todavía dice 'OpenCode es el control plane'" → deja
    de afirmarlo (AC-C.4).
  - `:439-448` (§11, las tres piezas diferidas) → apunta a este spec en vez de
    presentarlas como pendientes sin dueño (AC-C.4).
  - `:221` (celda "control plane histórico en `TIPS-USO.md`") → se revisa junto con las
    anteriores (AC-C.4).
  - `:219-230` es la medición que **respalda** la corrección de TIPS: ya documenta que los
    tres orquestan. Leerla antes de escribir.
- `README.md:305` — "TIPS-USO.md — flujo de trabajo del harness (control plane, lanes,
  drift)". **Condicional** (AC-C.6): se ajusta **si** la corrección la volvió falsa, se deja
  si sigue siendo cierta como índice. Lo que no se acepta es no haberla mirado; la decisión
  se registra en la evidencia de cualquiera de las dos formas.
- **Contra-mediciones** (read-only, no se editan): `ai/scripts/cost-report.py:20-23`,
  `:836-843`; el listado de `Global/`.

## ADRs / invariantes que constriñen

- **DEC-TIPS-POINTER** (`spec.md:159`): TIPS y `COMO-FUNCIONA` viajan juntos. Separarlos
  produce la contradicción inversa — es el defecto que este paquete existe para evitar.
- **AC-C.5, lista cerrada de lo que NO se toca en `TIPS-USO.md`:** "Required lifecycle"
  (`:117-121`), la política de MCP (`:150-156`, **incluida la mención de Engram**) y el
  bloque de bootstrap/instalación (`:25-32`). El diff no puede incluir esas líneas.
- **Invariante 2 (ADR-0064):** "los tres pueden orquestar" **no** significa "hay panel en
  cualquiera". Lo que no cambia por runtime es la lane y la ceremonia: sin `init` con señal
  de riesgo no hay panel. AC-C.1 exige decirlo explícito.
- `TIPS-USO.md` y `docs/COMO-FUNCIONA.md` son **documentos humanos**, no bloques
  `notas:auto`: nada de lo que este paquete escribe entra a un bloque regenerado por
  `feature-state.py` (`spec.md:487-489`).
- No se reescribe TIPS de punta a punta. Esto no es una pasada de estilo.

## Validación local

```
ls Global/                                        # cinco árboles + _canonical + _shared
rg -i cursor ai/scripts/cost-report.py            # contra-medición de AC-C.3
rg -n "control plane" TIPS-USO.md docs/COMO-FUNCIONA.md README.md
git diff -- TIPS-USO.md                           # ninguna línea de :25-32, :117-121, :150-156
./ai/scripts/verify.sh
```

La verificación de este paquete es **lectura contra las mediciones citadas**: ninguna
afirmación de los tres archivos puede contradecir a otra al terminar.

## Reviewers / runtime / tests

- `required_reviewers`: **`["package-reviewer"]`**. `complexity=small` + `risk=low` →
  `SINGLE_REVIEW_PANEL` (`model.py:565-575`, `:95`) y `record-review` sigue siendo su puerta
  legítima. Es honesto: tres archivos de documentación, alcance cerrado, cero código, cero
  auth/pagos/secretos/PII y cero superficie de usuario nueva. Meter un `security-auditor`
  acá sería gastar despachos del techo sin superficie que auditar.
- `runtime_surface`: **false** — solo documentación, sin comportamiento observable.
- test owner: **implementer**. No hay tests; la validación es lectura + `rg`, y su salida va
  a `docs/specs/035-panel-honesto-consola-y-tips/evidence/` (convención medida en 034).
- `strict_tdd`: **false** — no hay código que testear primero.
- `selected_role` / `selected_model`: `implementer` / `composer-2.5`. Pin de host Cursor
  (034/ADR-0063), **no** una lane de routing: `--route-decide` sigue prohibido.

## Fuera de alcance (aunque tiente)

Reescribir `TIPS-USO.md` completo · tocar `:25-32`, `:117-121`, `:150-156` · relitigar
Engram o la política de MCP (no-goal 5) · reabrir 032/033/034 como producto · tocar
`ai/scripts/**`, `Global/**` o `tests/**` · el ADR de PKG-A · `set_agents_app.py` (PKG-B) ·
editar `docs/notas/**` dentro de bloques `notas:auto`.

## Mordida

Sin tests. El observable es grepeable y se deja en la evidencia: después del diff,
`rg -n "control plane" TIPS-USO.md docs/COMO-FUNCIONA.md README.md` no devuelve dos
afirmaciones que se contradigan, ninguno de los tres inventarios de TIPS (`:3`, `:45`,
`:127-129`) omite un árbol que `Global/` genera, y `docs/COMO-FUNCIONA.md:227-230` ya no
declara atrasado a un archivo que este mismo diff acaba de corregir.
