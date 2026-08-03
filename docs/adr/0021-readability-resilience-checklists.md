# ADR-0021 — Legibilidad/resiliencia como dimensiones de checklist en `package-reviewer`, no agentes nuevos

- Estado: Accepted (2026-08-03). Segunda de cinco ADRs (0020-0024) del estudio de RDD de `gentle-ai`; ver
  ADR-0020 para el contexto compartido.

## Contexto

gentle-ai escala 4 "lentes" de revisión (riesgo, legibilidad, confiabilidad, resiliencia) como agentes
separados, activados 0/1/4 según severidad evidenciada. El usuario decidió explícitamente NO crear 4 agentes
nuevos: `package-reviewer` ya cubre correctness/architecture/test-gaps/data-integrity/scalability en un solo
pase, y esa disciplina se extiende con dos checklists más (legibilidad, resiliencia) en el mismo rol, en vez
de fragmentar la revisión en agentes paralelos. Al tocar el enum `category` para sumar estas dos dimensiones,
se encontró y corrigió una deriva preexistente: `package-reviewer.md` usaba `data-integrity` en su propio
checklist mientras `structured-findings/SKILL.md` (la fuente compartida por `delta-reviewer`, `security-auditor`,
`finding-verifier`, `repair-agent`) documentaba `stability` para el mismo campo — sin ningún consumidor de
código que dependiera literalmente de ninguna de las dos strings (verificado por grep en `ai/scripts/` y
`tests/`). `data-integrity` es la que efectivamente se enforcea (el checklist real lleva ese nombre), así que
es la que se conserva.

## Decisión

1. `package-reviewer.md` gana dos checklists nuevos, mismo formato y nivel de detalle que los ya existentes de
   Data-integrity/Scalability: **Legibilidad** (naming, complejidad por responsabilidad, código muerto, lógica
   duplicada, comentarios que explican el *por qué*) y **Resiliencia** (timeouts en llamadas externas, manejo
   explícito de fallas, retries acotados, degradación elegante, observabilidad en el camino de falla).
   Legibilidad se camina en TODA revisión (aplica a cualquier diff); Resiliencia se camina cuando el diff toca
   una llamada externa o un camino de falla — mismo patrón condicional que ya usan Data-integrity/Scalability.
2. El enum `category` de `structured-findings/SKILL.md` se corrige de `stability` a `data-integrity`
   (reconciliando la deriva) y suma `readability|resilience`. `package-reviewer.md`'s propio enum en su
   sección de salida se actualiza igual.
3. No se crea ningún skill file compañero (`readability-review`/`resilience-review`) — los checklists nuevos
   quedan autocontenidos en `package-reviewer.md`, igual que el bloque de "Frontend render cost" ya lo está
   dentro del checklist de Scalability, para mantener este paquete acotado.
4. La escalación de panel por riesgo evidenciado (agregar `security-auditor` u otro revisor cuando el
   `risk-classification` gate marca `high`) es una decisión separada, cubierta por ADR-0021 en su forma
   completa recién cuando el script de clasificación de riesgo exista (PKG-05) — este ADR cubre únicamente
   los checklists y el enum.

## Rejected alternatives

- **4 agentes-lente nuevos, calcados de gentle-ai.** Rechazado explícitamente por el usuario: duplicaría
  superficie (roles nuevos, costos, entradas en `roles.tsv`) sobre un panel que ya funciona.
- **Dejar `stability` como está y agregar un tercer nombre para lo mismo.** Habría creado tres formas
  distintas de nombrar el mismo campo entre dos archivos — se corrige a una sola vez que de todos modos había
  que tocar el enum.

## Consecuencias

- `package-reviewer` sigue siendo el único rol de revisión "de fondo" — ningún agente nuevo, ningún cambio al
  modelo de costos/paneles existente.
- La reconciliación de `stability`→`data-integrity` es puramente documental (ningún código dependía de la
  string vieja), pero cierra una fuente real de confusión para un lector futuro de ambos archivos.
- `readability`/`resilience` quedan disponibles como categorías de finding en todo el pipeline (delta-review,
  refutación adversarial, repair) sin cambio de código, porque `structured-findings` es la fuente única que
  todos esos roles ya leen.

## Amendment (2026-08-03, PKG-05) — escalación de panel por riesgo evidenciado, ahora completa

La decisión 4 quedó explícitamente diferida hasta que existiera el script de clasificación. Ya existe
(`ai/scripts/classify-risk.py`, hermano estructural de `check-owned-paths.py`, twin en `PROYECTO/`) y su
wiring en doctrina, cerrando esta ADR por completo:

5. `classify-risk.py --state-file <path> --package-id <PKG>` lee el `candidate_identity` ya congelado del
   paquete (ADR-0020 — depende de `freeze-candidate`, nunca del worktree vivo) y clasifica `low|medium|high`
   por EVIDENCIA únicamente, nunca por tamaño de diff: señales de path de alto riesgo (`auth`, `payments`,
   `pii`, `secrets`, `tenant`, `migrations`) escalan a `high`; un archivo de workflow/shell (`.github/
   workflows/*`, `*.sh`) sin otra señal escala a `medium`; el bit ejecutable agregado o contenido con
   `subprocess`/`os.system`/`child_process`/`Process.Start` en los primeros 8KB escalan a `high`. Un rename
   mecánico de 200 líneas sin ninguna señal nombrada se clasifica `low` — el mismo principio que gentle-ai
   documenta ("el tamaño nunca selecciona el tier").
6. `gate-runner` corre `freeze-candidate` y luego `classify-risk.py` en `PACKAGE_GATES`, justo antes del panel
   (`orchestrator.md` paso 7), y registra el resultado con `record-gate --name risk-classification --status
   pass --evidence '<JSON>'` — la clasificación en sí nunca falla el gate (es informativa), solo el gate de
   ownership puede fallar ahí.
7. El orquestador (`orchestrator.md` paso 8) lee ese gate antes de spawnear el panel: si `level == "high"` y
   `security-auditor` no está ya en `required_reviewers`, lo agrega con `extend-review-panel --role
   security-auditor --reason "risk-classification: <razón principal>"` — reusando el lever YA existente de
   `package-planner` (decisión 1 original de este ADR más arriba), nunca un mecanismo paralelo. `medium`/`low`
   no cambian nada; la declaración estática de planning queda como está.
8. `package-planner.md` documenta que su declaración estática de `required_reviewers` no es el único lever:
   la clasificación evidenciada es una cobertura ADITIVA para lo que el planning no podía ver todavía (el
   código no existía aún cuando se planificó el paquete) — nunca un reemplazo del juicio del planner.

### Rejected alternatives (amendment)

- **Correr `classify-risk.py` en `PACKAGE_PLANNING`.** Imposible por construcción: la clasificación lee el
  `candidate_identity` congelado, que no existe hasta que hay código implementado y congelado en
  `PACKAGE_GATES`. Confirma por qué la decisión 4 original tuvo que diferirse hasta este momento.
- **Hacer que `classify-risk.py` pueda fallar el gate.** Rechazado: es una clasificación, no una validación
  binaria — gentle-ai mismo la trata como informativa para decidir cuántos lentes activar, nunca como un
  pass/fail. `check-owned-paths.py` sigue siendo el único gate de `PACKAGE_GATES` que falla de verdad.
