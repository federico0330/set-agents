# Bitácora — 007-quota-visibility

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-02T15:03:09+00:00

[2026-07-28T10:43:12+00:00] P1-schema-normalize · spec-challenger · done
Cliente: El desafio del contrato encontro cuatro problemas serios, y dos tumban premisas centrales. El mas importante: medir el gasto de Pi como lo planteamos NO puede responder tu pregunta original, porque el ruteo en produccion siempre elige el carril de OpenAI y nunca el de Anthropic, asi que nunca habria con que comparar. Ademas la base de datos de ruteo ya no esta donde estaba: su historia sobrevive …
Ingeniería: SPEC_CHALLENGE returned revision_required, 13 findings, 4 blocking. F-03: routes.v1.toml gives openai-codex curated_priority=10 vs anthropic 20 at every tier and enabled_providers is all-or-nothing, so a production route-decide can never produce an anthropic row -- AC-11/AC-12 would ship a collector that structurally cannot answer the motivating question. F-02: routing.db is absent (orphan -wal/-…

[2026-07-29T00:42:18+00:00] P1-schema-normalize · orchestrator · done
Cliente: Antes de tocar una linea de codigo puse el expediente de esta funcionalidad en orden. Habia quedado con un paquete viejo marcado como 'necesita arreglo' sobre codigo que vos ya mandaste a revertir, con un bloqueo que figuraba resuelto pero seguia contado como abierto, y afirmando que aprobaste una version del documento que ya no existe. Con eso, esta funcionalidad no podia darse por terminada nun…
Ingeniería: 007 re-inicializada con acta (tercera vez, tras 008 y 009). Estado previo volcado a docs/specs/007-quota-visibility/evidence/state-before-reinit.json: revision 29, 30 entradas de historia, 4 paquetes, 22 AC. Cuatro defectos cerrados de una: P0 en repair_required con 6 hallazgos abiertos bloqueando done_ready:481-496; blocker resuelto pero presente, que done_ready:490-491 cuenta por verdad de list…

[2026-07-29T01:01:08+00:00] P1-schema-normalize · package-reviewer · started
Cliente: Dos revisores independientes miran el cambio al mismo tiempo y ninguno de los dos puede tocar el codigo. Uno busca errores concretos en como se compara la estructura de la base; el otro se pregunta si al arreglar la comparacion no la aflojamos, y si el mensaje de error nuevo puede filtrar algo que venga del archivo.
Ingeniería: Panel concurrente RP-01 (regla de 006-P1: un solo lote, sin serializar). package-reviewer cubre la maquina de estados de _normalize_ddl (escapes, delimitador sin cerrar, orden comentarios-antes-de-espacios), la equivalencia de _ddl_divergence con la desigualdad de dicts que reemplaza, la salida isinstance angosta en el except de _validate_existing_readonly, y si alguno de los 11 tests promete mas…

[2026-07-29T01:01:08+00:00] P1-schema-normalize · security-auditor · started
Cliente: -
Ingeniería: Segundo miembro del mismo panel acotado RP-01.

[2026-07-29T03:06:26+00:00] P1-schema-normalize · orchestrator · blocked
Cliente: Los dos revisores se cortaron a mitad de camino porque se agoto la cuota del proveedor, no porque hayan fallado. Los relanzo con otro modelo; no hace falta que hagas nada.
Ingeniería: Panel RP-01: package-reviewer y security-auditor terminados por API error 'session limit, resets 11pm America/Argentina/Buenos_Aires' sin devolver veredicto. Por AC-02/AC-03 de 008-P1 el agotamiento de cuota NO es falla del subagente y NO consume presupuesto de reintento: se relanza una vez con otro modelo, sin preguntar. Se relanza primero uno solo para medir si el tope es de cuenta o de tier an…

[2026-07-29T03:25:44+00:00] P1-schema-normalize · architect · started
Cliente: Sumo un tercer par de ojos, especializado en decisiones de arquitectura, porque apareció algo que ninguno de los dos primeros tenía el encargo de juzgar: el documento de diseño que escribimos puede estar diciendo que el sistema se protege menos de lo que realmente se protege.
Ingeniería: Tercer miembro del panel RP-01 via extend-review-panel: NO abre un segundo ciclo de review profundo ni toca deep_review_cycles. Dictamina AC-07 con la reproduccion en mano.

[2026-07-29T03:39:59+00:00] P1-schema-normalize · orchestrator · done
Cliente: Listo el primer paquete de esta funcionalidad. La comparacion que decide si una base de datos de ruteo se puede abrir ahora compara estructura y no prosa: un comentario agregado al codigo despues de que la base existia ya no la deja inutilizable para siempre, y eso valia para cualquier instalacion previa, no solo la tuya. Y cuando una base genuinamente no se puede migrar, ahora dice cual pieza no…
Ingeniería: P1-schema-normalize aceptado. 250 tests (base 238): 11 del paquete mostrados en rojo antes de su arreglo, mas 1 salido de la refutacion. Cuatro mutaciones del codigo cazadas ademas de una quinta sobre el test nuevo. Panel RP-01 con tres miembros, el architect sumado a mitad via extend-review-panel sin abrir segundo ciclo: package-reviewer pass, security-auditor pass, architect repair_required con…

[2026-07-29T04:17:58+00:00] P2-spawn-accounting · orchestrator · done
Cliente: Antes de arrancar el paquete grande corregi el documento del contrato. Cuatro de sus referencias apuntaban a lugares equivocados del codigo porque el paquete anterior lo movio de lugar ayer, y tres mas ya estaban mal de antes. Ademas cambie la forma de citar: en vez de numero de linea, el nombre de la funcion, que no se pudre cuando alguien edita el archivo.
Ingeniería: Contrato elevado a 1.3.0 con tercer log de enmiendas B-01..B-07. Siete citas file:line corregidas y la convencion cambiada a file:simbolo. B-02: AC-08 solo tiene sentido si una dimension no reportada queda NULL -- Pi no manda cache ni reasoning en la unica muestra viva, asi que un 0 seria el cero-de-antemano que el propio AC prohibe. B-03: round-half-up no es implementable sobre el float parseado…

[2026-07-29T13:29:15+00:00] P2-spawn-accounting · package-reviewer · started
Cliente: Antes de aceptar el paquete que hace visible cuanto gasta cada delegacion, un revisor independiente mira todo el codigo para asegurarse de que funcione bien, no rompa nada de lo que ya andaba, y sea facil de mantener.
Ingeniería: Separacion de responsabilidades: el implementador nunca aprueba su propio trabajo. Panel RP-01, package-reviewer + security-auditor declarados juntos en la apertura.

[2026-07-29T13:29:15+00:00] P2-spawn-accounting · security-auditor · started
Cliente: El mismo paquete agrega un lugar nuevo donde el arnes recibe datos de afuera (el costo y los tokens de cada delegacion) y una herramienta que lee la base de datos de ruteo. Un auditor de seguridad revisa especificamente esos dos puntos.
Ingeniería: El parseo en el borde CLI (parse_usage) y el borde del store (_usage_row) son la superficie nueva de entrada no confiable de este paquete; cost-report.py agrega lectura de un sqlite ajeno via --home. Mismo panel RP-01.

[2026-07-29T14:18:54+00:00] P2-spawn-accounting · delta-reviewer · started
Cliente: Reviso solo lo que se toco al arreglar los 9 problemas encontrados antes, para confirmar que quedaron bien resueltos y que no se rompio nada mas.
Ingeniería: DELTA_REVIEW tras record-repair (F-SEC-01 critical descarta --skip-delta). Ambito: 7 archivos del repair batch, 9 finding-ids cerrados. Produce veredicto pass/repair_required/blocked para record-delta-review.

[2026-07-29T14:52:50+00:00] P2-spawn-accounting · delta-reviewer · started
Cliente: El primer chequeo encontro que uno de mis propios arreglos anteriores dejaba abierta una falla parecida a otra que ya habiamos cerrado. La corregi, y ahora mando a revisarla de nuevo, acotado solo a lo que toque esta vez.
Ingeniería: Segundo ciclo de DELTA_REVIEW (mismo panel logico, delta-reviewer). Ambito: 5 archivos del segundo repair batch, 3 finding-ids cerrados (N-01 verificado, N-02 y N-03 low sin verificacion obligatoria). Objetivo: confirmar que N-01/N-02/N-03 quedaron resueltos y que no se introdujo una tercera vuelta.

[2026-07-29T15:33:23+00:00] P3-correct-record · package-reviewer · started
Cliente: Antes de dar por cerrada esta funcionalidad, alguien que no escribio el texto corregido lo revisa: que lo que ahora dice coincida con lo que de verdad se probo, y que no haya quedado ninguna afirmacion vieja sin corregir en esa misma seccion.
Ingeniería: Panel RP-01, un solo miembro (complexity: small, sin superficie de codigo ni de seguridad). package-reviewer, read-only, chequea las dos correcciones contra las citas de spec.md (Contexto, P1, P2) palabra por palabra, y que la excepcion de ownership sobre docs/specs/007-quota-visibility/** este bien justificada.

[2026-07-29T15:42:58+00:00] P3-correct-record · finding-verifier · started
Cliente: Antes de dar por buena la segunda version del texto, un tercer par de ojos con la consigna invertida: su trabajo es tratar de tirar abajo cada uno de los ocho problemas que encontro el revisor anterior, no confirmarlos. Lo que sobrevive a eso es lo unico que queda registrado como corregido.
Ingeniería: Read-only, sin panel nuevo -- es el paso finding-verifier entre PACKAGE_REVIEW y PACKAGE_REPAIR que exige record-verification para severidad > low. Los 8 hallazgos ya fueron reparados en el arbol (orden invertido respecto del flujo canonico: yo verifique 3 de ellos directo contra la base sqlite antes de aplicar el fix); el verificador chequea independientemente que cada uno era real Y que el text…

[2026-07-29T15:59:35+00:00] P3-correct-record · delta-reviewer · started
Cliente: Ultimo control: un revisor nuevo mira solo lo que se cambio para arreglar los ocho problemas que encontraron los dos anteriores, no el paquete entero. Confirma que quedaron bien resueltos y que arreglarlos no metio un problema nuevo.
Ingeniería: Sonnet, contexto limpio, read-only, alcance acotado a docs/notas/BUENOS-DIAS.md y ai/state/decisions-log.jsonl (las dos entradas de decision). F-01/F-02 high descartan --skip-delta. Foco: si las correcciones de la segunda pasada (slug de decision, alcance del encabezado, matiz de fallback_provider) resuelven de verdad las observaciones del finding-verifier, y si algo mas quedo sin resolver.

[2026-07-29T16:07:21+00:00] P3-correct-record · finding-verifier · started
Cliente: Un ultimo chequeo, muy chico: el revisor de delta encontro que el propio archivo de esta funcionalidad todavia repetia, en un lugar que no habiamos mirado, una de las frases que ya habiamos corregido. Antes de cerrar eso tambien, alguien independiente confirma que la correccion que le puse encima es la correcta.
Ingeniería: finding-verifier, read-only. 3 hallazgos: N-01 medium (local_validations del task rendido en la nota del paquete), N-02/N-03 low (notas de decision sin marca de supersesion / con razon contradicha). Los tres ya tienen una correccion aplicada via la seccion Notas propias de los archivos afectados (canal fuera del bloque notas:auto). Verificar que la correccion es fiel.

[2026-07-29T16:14:23+00:00] P3-correct-record · delta-reviewer · started
Cliente: Un ultimo control mas, sobre lo minimo que quedaba: si las tres correcciones chiquitas que hice recien -- incluida una que el mismo verificador anterior me hizo corregir por una fecha mal puesta -- estan bien esta vez.
Ingeniería: Sonnet, contexto limpio, read-only. Alcance: docs/notas/features/007-quota-visibility/P3-correct-record.md y las dos notas de decision, seccion Notas propias unicamente. No re-revisar BUENOS-DIAS.md ni el primer lote (ya con pass implicito del delta-review anterior salvo por estos 3).

[2026-07-29T16:55:25+00:00] P3-correct-record · integrator · started
Cliente: Mismo control para la parte que hace visible cuanto gasta cada delegacion.
Ingeniería: Integracion de 007-quota-visibility: confirma que P1 (normalizacion de schema) + P2 (contabilidad de spawns) + P3 (correccion de la nota) juntos satisfacen el contrato 1.3.0, incluyendo la deuda de la clausula de AC-19 que quedo registrada para un futuro 1.4.0.
