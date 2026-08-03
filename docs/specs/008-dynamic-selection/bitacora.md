# Bitácora — 008-dynamic-selection

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-03T00:38:55+00:00

[2026-07-28T13:04:40+00:00] P1-quota-failover · spec-challenger · done
Cliente: El desafio encontro que el failover automatico que planee no puede alcanzar tu caso. El arnes solo controla como subproceso el carril Pi; cuando se queda sin tokens un subagente de Claude Code -- que es exactamente lo que te pasa -- no hay ningun proceso que el arnes pueda clasificar ni volver a lanzar. Ademas encontro que uno de mis argumentos era falso: cite una restriccion de la base de datos …
Ingeniería: SPEC_CHALLENGE returned revision_required, 15 findings, 7 blocking. F-01 (scope): set_agents_spawn.py is the harness's ONLY spawner and it is pi-only (route_and_spawn pins selected_runtime=pi); there is no harness-controlled subprocess for opencode/claude-code/codex, so AC-01..AC-06 can all pass their tests while the reported symptom persists. F-02: my rejection of window-reopening cited store.py…

[2026-07-28T13:50:57+00:00] P1-uninterrupted-delegation · implementer · started
Cliente: Arranco el arreglo de los parones: el asistente va a dejar de cortar la conversacion para contarte que termino un paso cuando no necesita nada de vos.
Ingeniería: Se escribe primero el test de tres runtimes que hoy tiene que fallar (prueba adversarial exigida por el spec), y recien despues la doctrina en orchestrator.md y en los tres globales de Global/_shared.

[2026-07-28T14:01:17+00:00] P1-uninterrupted-delegation · package-reviewer · started
Cliente: Antes de dar por bueno el arreglo, alguien que no lo escribio lo revisa entero: que la regla nueva no contradiga otra vieja y que de verdad haga lo que promete.
Ingeniería: Panel concurrente RP-01 (006-P1). El paquete toca doctrina ya testeada: REVIEWER_INDEPENDENCE_UNAVAILABLE como HARD DENIAL (test_harness.py) y el bloque de cierre de turno. Contexto limpio y modelo distinto al del writer segun ADR-0011 D3.

[2026-07-28T14:01:17+00:00] P1-uninterrupted-delegation · architect · started
Cliente: Y en paralelo, alguien mira si la decision de fondo esta bien tomada y bien documentada, para que dentro de seis meses se entienda por que se hizo asi.
Ingeniería: Segundo miembro del mismo panel RP-01, en el mismo batch. Verifica ADR-0011: alcance, alternativas rechazadas, umbral de reversion, y que el diferimiento del carril Pi sea coherente con service.py:148,154.

[2026-07-28T14:43:07+00:00] P1-uninterrupted-delegation · finding-verifier · started
Cliente: Antes de tocar nada por lo que dijeron los revisores, alguien mas trata de demostrar que se equivocaron, para no cambiar cosas por un reclamo falso.
Ingeniería: ADR-0009: refutacion adversarial entre panel y reparacion. Tercer modelo (Fable 5), distinto del writer y de los dos reviewers. Los seis hallazgos por encima de low sobrevivieron.

[2026-07-28T14:43:07+00:00] P1-uninterrupted-delegation · delta-reviewer · started
Cliente: Y despues del arreglo, otra persona revisa solo lo que cambio, no todo de nuevo.
Ingeniería: Delta review acotada al delta reparado. Cerro los once y abrio dos nuevos de prosa, requires_full_review=false.

[2026-07-28T14:43:07+00:00] P1-uninterrupted-delegation · finding-verifier · started
Cliente: Lo mismo para el hallazgo nuevo: primero se intenta refutar, despues se corrige.
Ingeniería: El estado rechazo record-repair con 'finding was never verified: D-01'. La maquina aplica ADR-0009 sobre los hallazgos del delta igual que sobre los del panel.

[2026-07-28T14:49:25+00:00] P1-uninterrupted-delegation · implementer · done
Cliente: Listo: el asistente ya no corta la conversacion para contarte que termino un paso cuando no necesita nada tuyo, y si un modelo se queda sin cupo lo reemplaza solo en vez de frenar. Quedo escrito en las instrucciones que se cargan en las tres herramientas que usas.
Ingeniería: Paquete P1-uninterrupted-delegation aceptado. Doctrina Turn continuity en orchestrator.md y en los tres archivos de Global/_shared, ADR-0011, dos tests de tres runtimes (209 -> 211). Panel RP-01 concurrente devolvio 11 hallazgos, uno critico: la frontera de alcance estaba trazada por carril cuando --route-decide es agnostico al carril. Refutacion adversarial sostuvo los seis por encima de low. Re…

[2026-07-30T17:44:00+00:00] started
Cliente: Arrancamos el catálogo dinámico de modelos: hoy el orquestador solo conoce dos proveedores escritos a mano, y no ve los modelos propios de OpenCode ni los que agregues en el futuro.
Ingeniería: product-analyst redacta P2-discovered-inventory como enmienda real de 008 (hoy es un párrafo sin ACs). No depende de 007-P2 ni de 011/P1b — solo de sondear el entorno. Ownership acotado a docs/specs/008-dynamic-selection/spec.md; sin tocar código todavía.

[2026-07-30T17:58:01+00:00] done
Cliente: El contrato de P2 (catálogo dinámico) ya está escrito con reglas concretas — incluida una fricción real que encontró al probar en vivo: el nombre de la credencial de OpenCode no coincide con el id que pide su propio comando para listar modelos.
Ingeniería: product-analyst entregó AC-11..AC-20 en docs/specs/008-dynamic-selection/spec.md (1.0.0->1.1.0), verificado contra catalog.py/domain.py/service.py y una corrida real de 'opencode auth list'/'opencode models'. No tocó P1/P1b/P3. Mando un spec-challenger de contexto limpio antes de iniciar el paquete.

[2026-07-30T19:29:30+00:00] started
Cliente: El contrato de P2 volvió corregido: el mapa de nombres estaba al revés (el par nuevo hubiera quedado invisible en toda máquina), dos afirmaciones 'verificadas en vivo' resultaron mal medidas, y se agregó el campo que distingue suscripción de pago-por-uso que me confirmaste vos.
Ingeniería: product-analyst entregó contract 1.2.0 resolviendo los 3 bloqueantes + 4 highs + 6 mediums + 6 lows del primer challenge. Mando al mismo spec-challenger (contexto ya cargado) a una segunda pasada, acotada a verificar que las correcciones sean reales y no haya nada nuevo.

[2026-07-30T19:46:48+00:00] started
Cliente: Última vuelta del contrato de P2: el único punto flojo que quedaba era cómo evitar que el mismo modelo, ofrecido bajo dos proveedores con nombres distintos, se revisara a sí mismo creyendo que era independiente.
Ingeniería: product-analyst reescribió AC-17/AC-18 quirúrgicamente (contract 1.3.0): family pasa a ser curada con regla de colisión para ids compartidos entre providers, subscription/metered pasa a mapa curado por provider en vez de columna de fila (evita el esquema cerrado de catalog.py). Tercera pasada del mismo spec-challenger, acotada.

[2026-08-02T14:44:35+00:00] P1-uninterrupted-delegation · integrator · started
Cliente: Un integrador confirma que la seleccion dinamica de modelos convive bien con el resto del sistema antes de darla por terminada.
Ingeniería: INTEGRATION entry: read-only validation of P1-uninterrupted-delegation against approved spec 008; P3 budget-aware-selection stays blocked on 011 and is out of scope.

[2026-08-02T14:53:27+00:00] P1-uninterrupted-delegation · integrator · done
Cliente: El integrador reviso la pieza que evita pausas innecesarias al delegar trabajo: las diez condiciones acordadas estan cumplidas y conviven bien con lo entregado despues. Solo falta la corrida final de pruebas globales antes del sello de terminado.
Ingeniería: Integration validation PASS: AC-01..AC-10 verified in current tree (doctrine in 3 shared runtimes, build.sh --check CHECK_PASS SELF_SCAFFOLD_SYNC_OK, ADR-0011 linked, no conflict with 015 lane logic). P3 budget-aware-selection out of scope (blocked on 011). Pending: feature-level global gate (full verify.sh + unittest) before transition DONE.

[2026-08-02T14:53:45+00:00] orchestrator · done
Cliente: La seleccion dinamica de modelos quedo oficialmente terminada: todas las pruebas del proyecto pasaron y la pieza convive bien con el resto. La parte que depende de medir cuotas reales queda en pausa hasta que eso sea posible.
Ingeniería: 008 DONE: transition PACKAGE_ACCEPTED->INTEGRATION->DONE with global gate feature-008-integration pass (verify.sh 558 OK, build check). P3 budget-aware-selection remains deferred behind 011 (BLOCKED by design).
