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
