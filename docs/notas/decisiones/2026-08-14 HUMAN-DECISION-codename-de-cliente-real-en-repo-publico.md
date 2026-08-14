# HUMAN_DECISION_REQUIRED: un codename de cliente real viaja al orchestrator.md de cada tercero, y el repo es PUBLICO

<!-- notas:auto -->
- fecha: 2026-08-14 · actor: orchestrator
- alcance: [[features/024-listo-para-terceros|024-listo-para-terceros]] · [[features/024-listo-para-terceros/C4-higiene-de-repo-publico|C4-higiene-de-repo-publico]]

## Contexto

Hallazgo del implementer de C4, FUERA de su alcance, flageado por el en vez de ignorado. Verificado por el orquestador con tres mediciones: (1) 'gh repo view' devuelve visibility PUBLIC para github.com/federico0330/set-agents; (2) ai/scripts/generate.py:475 hardcodea el codename de un cliente real -replenishment-v2 / RPL-P0A- en el texto del orchestrator.md; (3) ese texto esta en Global/opencode/agents/orchestrator.md Y en el ~/.config/opencode/agents/orchestrator.md instalado, o sea viaja a la maquina de CADA persona que instale el harness. Ocho archivos del repo contienen el codename, mas corpus historico en specs, dos ADRs formales y ~50 fixtures de tests.

## Decisión

NO se toca por iniciativa del harness y 024 NO se cierra como DONE mientras esto siga abierto. La feature se llama 'listo para terceros': cerrarla con un codename de cliente filtrandose a cada tercero seria exactamente el cierre deshonesto que este harness existe para impedir. Los cuatro AC de C4 SI estan satisfechos y el paquete puede aceptarse; lo que queda abierto es la feature.

## Consecuencias

Requiere decision humana por tres razones: (a) es informacion posiblemente confidencial de un tercero, no del dueno del repo; (b) la remediacion completa toca la HISTORIA de git, que es irreversible y publica; (c) el repo era privado cuando esto se registro como deuda en 016-audit-debt-repayment, y paso a PUBLIC alrededor del 2026-08-07, lo que cambia la severidad de deuda tecnica a exposicion viva. Opciones que el humano puede tomar: sanear solo el arbol actual y aceptar el historial; reescribir historia con filter-repo y forzar push; o volver el repo privado mientras se decide. Ninguna la toma el harness.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
