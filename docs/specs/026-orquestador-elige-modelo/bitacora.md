# Bitácora — 026-orquestador-elige-modelo

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T15:34:35+00:00

[2026-08-13T13:42:44+00:00] P1-latencia-por-modelo-no-por-sufijo · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el modelo que coordina no sea forzosamente de OpenAI, como pediste.
Ingeniería: AC-01..03. El test test_repo_go_zen_routes_hot_path_to_fast_variants_and_keeps_reviewers_apart (test_harness.py:266) exige sufijo -fast para orchestrator/implementer/product-analyst, y -fast solo existe en el proveedor openai de opencode: la asercion dice latencia y significa OpenAI. Se conserva para los dos roles de volumen y se libera el coordinador. models.toml [areas.coord] a opencode-go/grok… _(truncado al render)_

[2026-08-13T14:27:39+00:00] P2-modelo-por-instancia · implementer · started · modelo anthropic/opus · effort medium
Cliente: Que el orquestador pueda pedir que modelo usar para cada agente que lanza, sin quedar atado a uno solo.
Ingeniería: AC-04..07, clase public-contract: cambia el contrato del descriptor de --route-decide (set_agents_app.py:605, conjunto cerrado). El riesgo central es que se convierta en bypass: la preferencia entra DESPUES del bucle de exclusiones, como factor de sort, con el precedente de _bias_rank. Un test por barrera.
