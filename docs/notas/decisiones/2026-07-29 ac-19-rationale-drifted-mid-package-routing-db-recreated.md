# AC-19 del contrato 007 quedo con una frase falsa por la propia QA en vivo de P2

<!-- notas:auto -->
- fecha: 2026-07-29 · actor: orchestrator
- alcance: [[features/007-quota-visibility|007-quota-visibility]] · [[features/007-quota-visibility/P3-correct-record|P3-correct-record]]

## Contexto

AC-19 (spec.md, seccion P3) dice textual: 'The rm remediation offered in that note is also withdrawn -- the database it names no longer exists and routing is not blocked.' Eso fue verificado true el 2026-07-28/29 temprano, contra el contexto de la seccion Contexto de spec.md (linea 42-44: 'routing.db is absent from ...'). A las 10:10 del mismo 2026-07-29, la verificacion en vivo de 007-P2 (parte de su propia Verificacion, ítem 2: 'a real spawn through the openai-codex lane') recreo esa base en schema 6 con un dispatch real. El finding-verifier de 007-P3 lo encontro al chequear F-01: BUENOS-DIAS.md, corregido para decir la verdad de hoy (la base existe, en schema 6, sin bloqueo), ahora contradice la letra literal de AC-19 y de spec.md:42-44, aunque cumple la intencion real del AC ('replaced by what was verified').

## Decisión

No se edita spec.md desde P3: owned_paths de este paquete es solo AC-19 (prosa de una nota), y el hash del contrato aprobado (31d6e65a...) no se re-verifica salvo en un re-init explicito, que perderia historia sin necesidad. BUENOS-DIAS.md queda escrito contra el estado real de la maquina (verificado por finding-verifier, no solo por el implementador), no contra la letra de un AC cuyo supuesto de hecho quedo viejo un rato despues de aprobarse. Se registra la contradiccion en vez de esconderla: quien lea AC-19 despues de este paquete tiene que saber que 'the database it names no longer exists' ya no es cierto, y que el texto real de BUENOS-DIAS.md sigue la verdad verificada, no esa clausula.

## Consecuencias

Si una futura feature vuelve a citar AC-19 como fuente de verdad sobre el estado de routing.db, esta decision es la correccion. Patron repetido: 007 ya amendo su contrato tres veces (1.0->1.1->1.2->1.3) por citas que se pudrieron con el tiempo entre package y package; esta es la primera vez que la cita se pudre DENTRO del mismo paquete que la escribio, por su propio efecto colateral (P2 corriendo un spawn real de verificacion). Vale como caso de estudio para el proximo spec-challenger: un AC que depende de 'esta base no existe' es fragil mientras el propio contrato siga corriendo codigo que puede recrearla.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**Corrección 2026-07-29 (hallazgo N-03 de DELTA_REVIEW):** la `## Decisión` de arriba dice "owned_paths de
este paquete es solo AC-19 (prosa de una nota)" como si eso impidiera tocar `spec.md`. Es inexacto: P3 sí
tiene una excepción de ownership **aprobada** sobre `docs/specs/007-quota-visibility/**` (registrada antes de
los gates, para que `bitacora.md` pudiera regenerarse). La razón real para no editar `spec.md` desde acá es la
que la misma entrada da a continuación y es la que pesa: el hash del contrato aprobado no se re-verifica salvo
en un `init --force` explícito, que perdería historia sin necesidad, y enmendar el contrato desde adentro de
la reparación de un paquete que se está juzgando contra ese mismo contrato es el implementador editando el
examen. La corrección de la cláusula vencida de AC-19 queda recomendada para un corte formal 1.3.0 → 1.4.0 en
`INTEGRATION`, no para P3.
