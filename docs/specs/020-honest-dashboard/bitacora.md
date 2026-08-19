# Bitácora — 020-honest-dashboard

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-19T18:30:21+00:00

[2026-08-12T03:00:02+00:00] P1-digest-no-esconde · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Arranca el arreglo del informe matinal: que las cosas trabadas esperandote aparezcan primero en vez de desaparecer.
Ingeniería: P1 de 020 (AC-01..05, AC-12): un predicado compartido de feature viva reemplaza las dos copias mal escritas (cli_reporting.py:194 y _hub_body), seccion Necesita tu decision con dias desde el ultimo blocker sin resolver, marca de estancada con las bloqueadas exentas, blocked_days/stale_days en cmd_status, y tests que fallan en rojo contra el codigo de hoy.

[2026-08-12T04:10:42+00:00] P1-digest-no-esconde · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente audita el arreglo del informe matinal antes de darlo por bueno.
Ingeniería: package-reviewer sobre 020/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje especial: el implementer MODIFICO un fixture de test preexistente (final_state 'done' -> 'DONE'); hay que verificar que el invariante sigue probado y no que se ajusto el test para que pase.

[2026-08-12T05:36:28+00:00] P2-anclas-verificables · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Ultimo tramo: que la documentacion de modulos no pueda decir que algo esta en una linea donde ya no esta.
Ingeniería: P2 de 020 (AC-06..11): gramatica de dos formas de ancla con resolucion por basename acotada a los paths del modulo, comando check-anchors read-only con rc distinto de cero, verificacion semantica acotada a simbolo en backticks adyacente, enganche never-raises en sync-notes, y correccion de las anclas rotas de hoy.

[2026-08-12T05:49:58+00:00] P2-anclas-verificables · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: El primer intento murio por infraestructura sin escribir nada. Se relanza una vez.
Ingeniería: Relanzamiento unico de P2. Mitigacion: escribir evidencia en el primer minuto y guardar a disco por tramo. Si vuelve a morir, se parte en dos encargos mas chicos en vez de un tercer intento completo.

[2026-08-12T11:19:21+00:00] done
Cliente: La feature 020 quedo cerrada. El informe de la manana ahora abre con lo que necesita tu decision, y la documentacion de modulos tiene un comando que contrasta sus referencias contra el codigo real.
Ingeniería: 020 DONE. 2 paquetes, ADR-0040, suite 943 -> 970. P1: predicado compartido de feature viva; el digest, el hub y cmd_status dejaron de esconder lo bloqueado. P2: check_anchors.py y el comando check-anchors, con cobertura declarada honestamente (12/38 con chequeo semantico, margen de falso negativo 10-25% por ancla). Deuda de 019 sobre las anclas derivadas: cerrada.
