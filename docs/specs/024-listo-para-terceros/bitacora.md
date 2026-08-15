# Bitácora — 024-listo-para-terceros

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-15T12:56:16+00:00

[2026-08-14T05:11:39+00:00] C1-estado-fuera-del-producto · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que quien clone el proyecto no herede tu historial de trabajo, y que vos no pierdas el tuyo.
Ingeniería: AC-01/02, clase migration. Medido: ai/state pesa 2,3 MB con 23 features, y ONCE modulos de ai/scripts lo leen. El path se MANTIENE -historial a docs/historia/estado-2026-08, ai/state gitignoreado y sembrado desde ai/state.seed-, que es lo que baja el cambio de 11 modulos a cero. Regla que protege al dueno: la siembra solo puebla un ai/state ausente, nunca pisa uno existente.

[2026-08-14T06:25:19+00:00] C2-modelstoml-neutro · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que quien clone el proyecto no herede tus suscripciones, y que usar el asistente de modelos no te bloquee las actualizaciones.
Ingeniería: AC-03/04/05, clase migration. AC-05 desbloquea a los otros dos: hoy el wizard reescribe el models.toml trackeado y tree_clean() es literalmente 'git status --porcelain == vacio', asi que cualquiera que use el wizard queda con --update bloqueado para siempre. Ademas los true de [subscriptions] apagan la red tri-estado de ADR-0029 (models_config.py:379-397). Y la lane 'local' no es local: sus model…

[2026-08-14T08:35:16+00:00] C3-primer-arranque-honesto · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que instalar el harness por primera vez no cuelgue, te diga como loguearte, y no te cambie configuracion tuya sin mostrartelo.
Ingeniería: AC-06/07/08. Medido: confirm() en install.sh:56-62 devuelve 0 siempre con --yes, y :309-311 es un 'while confirm ...' que nunca termina. NO_ELIGIBLE_ROUTE (service.py:437) es correcto como fail-closed pero mudo: falta ROUTING_UNCONFIGURED ADITIVO cuando todas las exclusiones fueron PROVIDER_UNAUTHENTICATED. Y merge_codex (install.py:237, roster_codex_orchestrator :267) le cambia el model del ~/.c…

[2026-08-14T09:50:40+00:00] C4-higiene-de-repo-publico · implementer · started · modelo anthropic/haiku · effort low
Cliente: Que el proyecto tenga licencia, guia de contribucion y una tabla honesta de que funciona en cada CLI.
Ingeniería: AC-09..12, clase documentation. Medido: no existen LICENSE, CONTRIBUTING, CHANGELOG ni SECURITY; HANDOFF-PASO9.md esta en la raiz; y origin/main esta hardcodeado en set_agents_app.py:1145,1194,1206, asi que un fork mide contra el lugar equivocado. La licencia NO se elige: las skills canonicas ya declaran license: MIT en su frontmatter, el LICENSE formaliza lo que el repo ya afirma.
