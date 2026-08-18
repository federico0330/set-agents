# Bitácora — 025-consola-minima-y-flexible

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T14:19:56+00:00

[2026-08-14T11:11:13+00:00] D1-superficie-humana · implementer · started · modelo anthropic/sonnet · effort medium
Cliente: Que la aplicacion de terminal muestre solo lo que te sirve, sin caracteres raros ni comandos que no vas a usar.
Ingeniería: AC-01..03. Medido: MENU_ITEMS son 10 items con emoji (set_agents_app.py:3523-3534), y dos de ellos ya llevan DOS espacios en vez de uno porque sus glifos miden distinto -la prueba del problema-. El CLI expone 68 flags. Ocultar es help=argparse.SUPPRESS, nunca borrar: coord_policy las tiene en su allowlist y los spawns las invocan. Y --json debe preservar el formato actual byte por byte porque el … _(truncado al render)_

[2026-08-16T20:16:51+00:00] D1-superficie-humana · package-reviewer · started · modelo anthropic/claude-opus-5 · effort high
Cliente: Una mirada ajena intenta romper la consola nueva antes de darla por buena.
Ingeniería: Independencia degradada ADR-0011, declarada. El reviewer renderizo el menu real, conto las 59 flags visibles una por una y audito Global/, no solo ai/scripts.

[2026-08-16T20:16:52+00:00] D1-superficie-humana · repair-agent · started · modelo anthropic/claude-sonnet-5 · effort medium
Cliente: Arreglar lo que la revision encontro, incluido el comando que el harness se rompia a si mismo.
Ingeniería: Pase consolidado D1-F01 a F09. F08 y F10 los resolvio el orquestador.

[2026-08-17T01:55:49+00:00] D1-superficie-humana · finding-verifier · started
Cliente: Mirada adversaria sobre los 8 hallazgos de D1 antes de reparar
Ingeniería: PACKAGE_REPAIR exige verification. Spawn BASE finding-verifier por Task host. MODEL_STATIC_FALLBACK: sin descriptor para route-decide por superficie bash.

[2026-08-17T01:59:27+00:00] D1-superficie-humana · finding-verifier · done
Cliente: De ocho objeciones a la consola, una no era real y las otras siete si merecian arreglo.
Ingeniería: 7 upheld 1 refuted D1-F04. Evidence D1-verification.md. SPAWN-004 closed.

[2026-08-17T02:03:18+00:00] D1-superficie-humana · delta-reviewer · started
Cliente: Revisa el arreglo de la consola
Ingeniería: DELTA_REVIEW repair 2f199d5. BASE Task host.

[2026-08-17T02:04:31+00:00] D1-superficie-humana · delta-reviewer · done
Cliente: El arreglo de la consola se confirmo: los siete defectos reales quedaron cerrados.
Ingeniería: delta pass. D1-DLR-01 low bak tracked. phase next testing.

[2026-08-17T02:11:21+00:00] D1-superficie-humana · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Confirmar que la consola quedó lista para usar antes de declararla terminada.
Ingeniería: Precondición PACKAGE_TESTING: una instancia independiente ejecuta validaciones y QA; MODEL_STATIC_FALLBACK por descriptor de routing no disponible sin archivo auxiliar.

[2026-08-17T02:14:29+00:00] D1-superficie-humana · gate-runner · done
Cliente: La consola fue comprobada como se usa de verdad: sigue siendo simple y mantiene intacta la salida para automatizaciones.
Ingeniería: Testing y QA independientes pass, con evidencia en D1-testing-runtime-qa.md; el siguiente precondición es declarar impacto de módulo antes de aceptar el paquete.

[2026-08-17T02:15:23+00:00] D1-superficie-humana · integrator · done
Cliente: La interfaz diaria quedó más clara sin quitar capacidades ni romper integraciones existentes.
Ingeniería: D1 aceptado tras testing, QA y record-module-impact: App de consola (set-agents); el próximo paquete verifica que las operaciones largas muestren progreso sin contaminar pipes.

[2026-08-17T02:15:47+00:00] D2-trabajo-visible · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Comprobar que las operaciones largas den señales claras sin romper el uso automático.
Ingeniería: Recuperación file-first de PACKAGE_IMPLEMENTATION: gate-runner mide AC-04/05 sobre 211df01 antes de la revisión independiente; MODEL_STATIC_FALLBACK declarado.

[2026-08-17T02:18:38+00:00] D2-trabajo-visible · package-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Una segunda mirada busca defectos antes de terminar el comportamiento de progreso.
Ingeniería: PACKAGE_REVIEW exige independencia del gate-runner; revisión read-only sobre 211df01 y D2-gates-runtime-qa.md; MODEL_STATIC_FALLBACK declarado.

[2026-08-17T02:29:32+00:00] D2-trabajo-visible · package-reviewer · done
Cliente: Detectamos dos casos donde una tarea podría parecer congelada o imprimir después de terminar; se corrigen antes de entregar.
Ingeniería: Review independiente finalizó con D2-F01 high y D2-F02 medium en D2-review.md; PACKAGE_REPAIR requiere verification antes de reparación.

[2026-08-17T02:33:16+00:00] D2-trabajo-visible · finding-verifier · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que los dos problemas detectados son reales antes de modificar la consola.
Ingeniería: Precondición física de PACKAGE_REPAIR para findings high/medium; verificador independiente, read-only, sobre evidencia D2-review.md; MODEL_STATIC_FALLBACK declarado.

[2026-08-17T02:39:33+00:00] D2-trabajo-visible · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Asegurar que cualquier tarea lenta dé una señal clara y termine sin mensajes atrasados.
Ingeniería: Ambos findings upheld; único repair batch admitido por ciclo, limitado a owned_paths D2; MODEL_STATIC_FALLBACK declarado.

[2026-08-17T02:47:58+00:00] D2-trabajo-visible · delta-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que el arreglo solucionó ambos problemas sin introducir otros.
Ingeniería: DELTA_REVIEW tras repair batch; reviewer read-only independiente sobre commit 489ecff y evidencia D2-repair.md; MODEL_STATIC_FALLBACK declarado.

[2026-08-17T02:54:51+00:00] D2-trabajo-visible · delta-reviewer · done
Cliente: El control independiente detectó dos bordes a corregir antes de cerrar el paquete: una espera lenta sin aviso y un indicador que puede tapar una pregunta interactiva.
Ingeniería: Delta-review repair_required: F02 cerrado; F01 reabierto; DR01 y DR02 nuevos. Se inicia el segundo ciclo de reparación, dentro del máximo permitido.

[2026-08-17T02:55:31+00:00] D2-trabajo-visible · finding-verifier · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que los dos problemas nuevos son reales antes de hacer otro arreglo.
Ingeniería: F01 reabierto y DR01 alto requieren finding-verifier en PACKAGE_REPAIR; se preservan dos spawns para repair y delta final.

[2026-08-17T03:00:43+00:00] D2-trabajo-visible · finding-verifier · done
Cliente: La verificación confirmó los dos bordes; se corrigen antes de cerrar el paquete.
Ingeniería: D2-F01 y D2-DR01 upheld mediante reproducciones focales sobre 489ecff; DR02 bajo se incorpora al mismo repair batch.

[2026-08-17T03:01:09+00:00] D2-trabajo-visible · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Corregir el aviso faltante y evitar que el indicador tape preguntas interactivas.
Ingeniería: Segundo y último repair batch de D2; findings altos verificados y DR02 bajo documental. Queda un spawn para delta-review final.

[2026-08-17T03:07:52+00:00] D2-trabajo-visible · delta-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar el arreglo final sin abrir un tercer ciclo.
Ingeniería: Spawn 8/8: revisa d30f94f y 0d202873; el presupuesto de reparación queda agotado tras su dictamen.

[2026-08-17T03:13:07+00:00] D2-trabajo-visible · delta-reviewer · done
Cliente: La última mirada cerró los tres puntos: aviso claro y preguntas interactivas sin interferencia.
Ingeniería: Delta final pass sobre d30f94f/0d202873: F01, DR01 y DR02 cerrados; 13 focales y repair ceiling pass; no requiere full review.

[2026-08-17T03:13:36+00:00] D2-trabajo-visible · orchestrator · done
Cliente: El paquete de trabajo visible quedó cerrado: avisa cuando corresponde y respeta las preguntas interactivas.
Ingeniería: D2 aceptado tras delta final, testing/runtime QA y module impact; se avanza al paquete dependiente D3.

[2026-08-17T03:14:03+00:00] D3-posturas-de-autonomia · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Verificar que las opciones de autonomía y método funcionen como se explican.
Ingeniería: D3 ya integrado en bec3dcf; gate-runner valida AC-06..08 contra SHA fijo 0d20287, antes de review independiente.

[2026-08-17T03:17:22+00:00] D3-posturas-de-autonomia · package-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Una mirada independiente revisa que las opciones no sean sólo texto sino comportamiento real.
Ingeniería: PACKAGE_REVIEW de D3 tras gates verdes; inspector read-only sobre SHA fijo 0d20287 y D3-gates-runtime-qa.md.

[2026-08-17T03:23:43+00:00] D3-posturas-de-autonomia · package-reviewer · done
Cliente: La revisión detectó que había que probar el comportamiento que usa el orquestador y alinear las configuraciones inválidas.
Ingeniería: D3 review repair_required: F01 high desconexión runtime; F02/F03 medium sobre canal metodológico y fallback TOML.

[2026-08-17T03:23:50+00:00] D3-posturas-de-autonomia · finding-verifier · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar los tres problemas de conducta real antes de corregirlos.
Ingeniería: PACKAGE_REPAIR: tres hallazgos high/medium requieren verificación read-only sobre SHA fijo 0d20287.

[2026-08-17T03:28:54+00:00] D3-posturas-de-autonomia · finding-verifier · done
Cliente: La comprobación confirmó los tres puntos; ahora se corrigen sobre el camino que usa el orquestador.
Ingeniería: D3 F01/F02/F03 upheld; repair limitado a canal runtime de posturas/metodologías y sus pruebas focales.

[2026-08-17T03:28:55+00:00] D3-posturas-de-autonomia · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Conectar las opciones de autonomía y metodología con el comportamiento real, incluso ante una configuración inválida.
Ingeniería: Tres findings upheld; repair-agent limitado al canal D3, doctrina y tests. Quedan cuatro spawns para delta y gates de cierre.

[2026-08-17T03:35:32+00:00] D3-posturas-de-autonomia · delta-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que el arreglo conecta las preferencias con la conducta real sin agregar otro mecanismo.
Ingeniería: DELTA_REVIEW de repair batch 5745537; revisión read-only focal sobre canal, fallback y tests.

[2026-08-17T03:41:19+00:00] D3-posturas-de-autonomia · finding-verifier · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que la relación entre cada postura y su acción sea realmente comprobable.
Ingeniería: Segundo ciclo D3: F01 high reabierto exige verificación; quedan repair y delta final dentro del budget 8.

[2026-08-17T03:44:05+00:00] D3-posturas-de-autonomia · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Hacer que cada postura tenga una acción única y comprobable.
Ingeniería: Segundo y último repair batch D3: F01 high upheld; quedan un delta final en el presupuesto.

[2026-08-17T03:49:03+00:00] D3-posturas-de-autonomia · delta-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que cada postura lleva a una acción inequívoca.
Ingeniería: Spawn 8/8 D3: última revisión read-only del repair bbed1d3/3b2324f; sin presupuesto de tercer repair.

[2026-08-17T03:52:35+00:00] D4-harness-por-CLI · gate-runner · started · modelo openai-codex/gpt-5.6-luna · effort low
Cliente: Comprobar que instalar o desinstalar un carril no toca los otros.
Ingeniería: D4 integrado bec3dcf; gate-runner debe usar sandbox y probar AC-09..11 sin instalaciones reales.

[2026-08-17T03:58:21+00:00] D4-harness-por-CLI · gate-runner · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Medir en forma concreta y aislada que los carriles no se afecten entre sí.
Ingeniería: Reintento único: el gate previo no produjo evidencia ni veredicto; órdenes cerradas, sin suite global.

[2026-08-17T04:00:09+00:00] D4-harness-por-CLI · package-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Una mirada independiente comprueba que los carriles no puedan pisarse entre sí.
Ingeniería: PACKAGE_REVIEW D4 tras sandbox verde; inspección read-only del código y evidencia D4.

[2026-08-17T04:03:59+00:00] D4-harness-por-CLI · package-reviewer · started · modelo openai-codex/gpt-5.6-terra · effort high
Cliente: Confirmar con evidencia simple si la opción de usar un carril virgen realmente existe.
Ingeniería: Relanzamiento único tras policy interruption; read-only y excluye security PoCs. Solo AC-11 y coherencia docs/runtime.

[2026-08-17T04:06:45+00:00] D4-harness-por-CLI · finding-verifier · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar la ausencia del modo de uso único antes de implementarlo.
Ingeniería: F01 high AC11: verificación focal read-only de CLI/docs sin análisis de rutas ni cambios.

[2026-08-17T04:08:27+00:00] D4-harness-por-CLI · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Usar una herramienta virgen una sola vez sin desinstalar ni modificar lo ya instalado.
Ingeniería: D4-F01 upheld; repair limitado a CLI one-shot, aislamiento HOME/XDG, tests y evidencia; no tocar otros carriles.

[2026-08-17T04:17:35+00:00] D4-harness-por-CLI · delta-reviewer · started · modelo openai-codex/gpt-5.6-sol · effort xhigh
Cliente: Confirmar que la sesión virgen no modifica ni lee los carriles instalados.
Ingeniería: DELTA_REVIEW del repair bfe7b2d; revisión read-only focal de aislamiento runtime y evidencia.

[2026-08-17T04:23:43+00:00] D4-harness-por-CLI · repair-agent · started · modelo openai-codex/gpt-5.6-terra · effort medium
Cliente: Permitir que la sesión virgen se abra también sin argumentos y actualizar su explicación.
Ingeniería: Spawn 8/8; F01/DR02 probados por delta, repair mínimo sin cambios de aislamiento.

[2026-08-17T04:54:11+00:00] D5-vault-en-todo-spawn · implementer · started · modelo openai/gpt-5.6-terra · effort medium
Cliente: Cada spawn debe recibir la bóveda por stdin cuando corresponde, limpiar SET_AGENTS_PROJECT en los cuatro carriles, degradar honestamente y respetar el fence de prompts.
Ingeniería: Base fija 8a9f62bb5fa7dc1ed3f4275a1261de7c88ea9208; usar la rama rescatada sólo como referencia selectiva, nunca mergear su D5 divergente.

[2026-08-18T01:13:45+00:00] D5-correctiva · package-reviewer · started · modelo anthropic/claude-sonnet-4.6
Cliente: Federico pidió la revisión que nunca ocurrió en D5. El revisor la hizo con contexto limpio, proveedor distinto.
Ingeniería: revisión correctiva del paquete D5-vault-en-todo-spawn: D5 fue aceptado con diff_ref=WORKTREE (no SHA), evidencia del implementer mismo, y cero delta reviews. La revisión correctiva (docs/specs/025-consola-minima-y-flexible/evidence/D5-delta-review-correctiva.md) encontró D5-DR01 (alta) y D5-DR02 (media).
