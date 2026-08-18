# Bitácora — 033-menos-espera-menos-cuota

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T20:06:44+00:00

[2026-08-18T15:48:35+00:00] PKG-4 · package-planner · started · modelo cursor/inherit
Cliente: Se estan armando las hojas de ruta de cada paquete para que quien implemente no tenga que rebuscar el repo.
Ingeniería: package-planner nativo Cursor, model inherit, sin route-decide. Completa PACKAGE_PLANNING: un context pack por paquete en docs/specs/033-menos-espera-menos-cuota/context/ y update-package --context-pack. No re-descompone.

[2026-08-18T16:02:10+00:00] PKG-4 · implementer · started · modelo cursor/inherit
Cliente: Se empieza a corregir lo que Windows y macOS todavia tienen roto, y a ponerle un techo a los tests que se saltan para que no crezcan en silencio.
Ingeniería: implementer nativo Cursor, model inherit, sin route-decide. Context pack docs/specs/033-menos-espera-menos-cuota/context/PKG-4.md. Si hace falta set_agents_app.py o tui.py, para y reporta: no estan en owned_paths.

[2026-08-18T16:02:41+00:00] package-planner · done
Cliente: Quedaron escritas las hojas de ruta de los seis paquetes: que archivos tocar, que pruebas correr y que no hay que tocar. El primero a implementar es el de Windows y la integracion continua, para que el resto no se apoye sobre fallas ya conocidas.
Ingeniería: Los seis paquetes ya existian pero sin hoja de ruta, asi que cada worker iba a reexplorar el repo. Ahora cada uno tiene un archivo corto en docs/specs/033-menos-espera-menos-cuota/context/ (58 a 61 lineas) y el estado durable apunta a esa ruta. El presenter del gate no tiene app que un verificador de runtime deba levantar; el menu de consola no es el frontend HTML que revisa el rol de interfaz.
Aprendimos: El freeze de trece segundos vive en el call site del wizard. El caso de stdin en Windows tambien llama bash directo. El flaky de macOS es la clase ProviderVerifyLivenessScopeTests.
Conviene ahora: Implementar el paquete de Windows y CI hasta aceptado: los cuatro tests que llaman bash directo, los otros cuatro casos, techo de skips, y el test de liveness sin reloj de pared.
Por qué ahora: Si el resto avanza con la CI y el gate todavia mentirosos, una regresion de Windows o un test flaky se come el presupuesto y no se puede atribuir al cambio nuevo.
Alternativa: Empezar por colapsar las lanes de OpenCode o por el menu que congela. Se descartan ahora: primero hay que dejar la CI y el gate en condiciones de sostener esos cambios.

[2026-08-18T16:42:26+00:00] PKG-4 · implementer · done
Cliente: Se corrigieron las fallas de Windows que quedaban y el test de macOS que fallaba por el reloj. Tambien hay un techo para que los tests saltados no crezcan en silencio.
Ingeniería: Los cuatro tests que llamaban bash directo ahora pasan por el helper run() en tests/test_harness.py:43-71. El planificador del vault escribe rutas con barras normales (vault_ops.py:272-279). El techo de skips del job Windows queda en 660 en .github/workflows/ci.yml:70-85. El test de liveness espera el texto en stderr, sin subir el sleep (tests/test_provider_registry.py:297-330).
Aprendimos: TOOL_UNKNOWN en el catalogo local era un TOML invalido por barras invertidas de Windows dentro de un string, no un bash. El ERROR del ADR era FileNotFound: el log vivo esta gitignored y el job de Windows no lo siembra.
Conviene ahora: Correr los gates del paquete: chequeo de build, la suite completa y el control de archivos tocados. Despues revision independiente. El SHA de los tres jobs de CI se cita al cierre.
Por qué ahora: Sin la suite completa y el control de alcance, un arreglo de tests puede haber roto otra cosa o escrito fuera de los paths del paquete.

[2026-08-18T16:42:29+00:00] PKG-4 · gate-runner · started · modelo cursor/inherit
Cliente: Se corre la verificacion completa del paquete, sin tocar codigo, para confirmar que los arreglos de Windows no rompieron otra cosa.
Ingeniería: gate-runner nativo Cursor, readonly, model inherit, sin route-decide. Comandos: check-owned-paths --baseline HEAD, heartbeat-run build.sh --check, heartbeat-run verify.sh, git diff --check. No repara.

[2026-08-18T17:39:00+00:00] PKG-4 · gate-runner · done
Cliente: La verificacion del paquete de Windows paso: el chequeo de build, la suite completa y el control de archivos tocados estan verdes. Queda la revision independiente y, para cerrar del todo, el SHA de la integracion continua cuando se publique.
Ingeniería: check-owned-paths OWNERSHIP_PASS contra HEAD. build.sh --check: BUILD_CHECK_PASS y GLOBAL_TREE_SYNC_OK harnesses=5. verify.sh: Ran 1290 tests in 1392.749s, VERIFY_PASS (linea base del spec: 1286 tests en 1237 s). git diff --check vacio. Candidato congelado en 1f5a24f. classify-risk RISK_LEVEL high por subprocess-spawn.
Aprendimos: La suite local ahora corre 1290 tests en unos 1393 s: cuatro tests nuevos respecto de la linea base, un poco mas lenta. El clasificador de riesgo marca high si un archivo menciona subprocess, incluso un markdown.
Conviene ahora: Revision independiente del paquete, con el revisor de paquetes y el auditor de seguridad porque el clasificador salio high. El SHA de los tres jobs de CI se cita al aceptar.
Por qué ahora: Sin revision de un contexto limpio, el que implemento se estaria aprobando solo. El SHA de CI es el criterio que todavia no se puede mentir en verde local.

[2026-08-18T17:39:02+00:00] PKG-4 · package-reviewer · started · modelo cursor/inherit
Cliente: Un revisor que no escribio el codigo mira si los arreglos de Windows y macOS cumplen lo pedido y no esconden un skip.
Ingeniería: package-reviewer nativo Cursor, readonly, model inherit (degradacion same-model/clean-context). Diff git show 1f5a24f. Context pack PKG-4.md. No parchea.

[2026-08-18T17:39:02+00:00] PKG-4 · security-auditor · started · modelo cursor/inherit
Cliente: Un auditor de seguridad mira si los cambios de rutas y de tests abren un agujero, no si el test pasa.
Ingeniería: security-auditor nativo Cursor, readonly, model inherit, same-model degradation. Superficie: vault_ops.py as_posix, tests que invocan bash via run(), job CI. No parchea.

[2026-08-18T17:48:37+00:00] PKG-4 · package-reviewer · done
Cliente: Un revisor que no escribio el codigo y un auditor de seguridad miraron el paquete de Windows y no encontraron nada que reparar. Falta publicar el commit para tener el sello de la integracion continua.
Ingeniería: Panel RP-01 pass. package-reviewer: AC-4.1 a 4.4 cubiertos en 1f5a24f, techo 660=654+6, probe intacto. security-auditor: SECURITY_PASS, relative_to no emite puntos-puntos, run() sin shell. Independencia degradada a contexto limpio, mismo modelo. AC-4.5 residual.
Aprendimos: El clasificador marca high si un archivo menciona subprocess, incluso un markdown. El techo honesto es linea base mas addends nombrados, no un redondeo.
Conviene ahora: Registrar la suite ya corrida como testing del paquete, documentar que no hay app que levantar, y aceptar. El SHA de CI queda pendiente de publicar.
Por qué ahora: Sin cerrar testing y runtime en el estado, el paquete no se puede aceptar aunque la revision haya pasado.

[2026-08-18T17:48:59+00:00] PKG-4 · orchestrator · done
Cliente: El primer paquete quedo aceptado: Windows y macOS dejan de mentir en las pruebas, y hay un techo para que los tests saltados no crezcan en silencio. Falta publicar el commit para ver los tres jobs verdes juntos.
Ingeniería: PKG-4 accepted. Candidato 1f5a24f. Gates VERIFY_PASS 1290/1393s. Panel RP-01 pass. AC-4.5 residual: SHA de verify-linux, verify-macos y windows-bootstrap en la misma corrida, pendiente de push. Spawns 5/8.
Aprendimos: Freeze exige commit (candidate_identity.py:7-8). runtime_surface true en un paquete de tests obliga a documentar contratos observables, no a levantar una app que no existe.
Conviene ahora: Implementar el paquete del gate visible: progreso en vivo, falla temprana, resumen y los diez tests mas lentos. Paralelizar solo si se prueba aislamiento.
Por qué ahora: Sin un gate que se pueda mirar, los cinco paquetes que siguen van a quemar veinte minutos opacos por cierre.

[2026-08-18T17:49:42+00:00] PKG-5 · implementer · started · modelo cursor/inherit
Cliente: Se hace que los veinte minutos de chequeo se puedan mirar: una linea de progreso, la falla apenas ocurre, y un resumen al final.
Ingeniería: implementer nativo Cursor, inherit, sin route-decide. Context pack PKG-5.md. Archivos: verify.sh, ai/scripts/verify_reporter.py, tests/test_verify_reporter.py. No paralelizar.

[2026-08-18T18:04:13+00:00] PKG-5 · gate-runner · started · modelo cursor/inherit
Cliente: Se corre la verificacion completa, ahora con la linea de progreso, para confirmar que el conjunto de tests no cambio.
Ingeniería: gate-runner nativo Cursor, readonly, inherit, sin route-decide. heartbeat-run verify.sh ~20 min. No repara.

[2026-08-18T18:07:06+00:00] PKG-5 · implementer · started · modelo cursor/inherit
Cliente: El chequeo se cayo al arrancar: no encontraba la carpeta de tests. Se corrige eso y se agrega una prueba que lo hubiera visto.
Ingeniería: implementer Cursor inherit. Causa: sys.path[0]=ai/scripts al invocar el archivo; chdir ROOT no alcanza. Bite: rojo contra el crash, luego verde.

[2026-08-18T18:18:55+00:00] PKG-5 · gate-runner · started · modelo cursor/inherit
Cliente: Se vuelve a correr la verificacion completa ahora que el chequeo encuentra los tests.
Ingeniería: gate-runner Cursor inherit readonly. heartbeat-run verify.sh. No repara. Gate failures 1/3 ya gastado.

[2026-08-18T18:46:41+00:00] PKG-5 · package-reviewer · started · modelo cursor/inherit
Cliente: Un revisor mira si el chequeo se puede seguir de verdad y si el conjunto de tests sigue siendo el mismo.
Ingeniería: package-reviewer Cursor inherit readonly. Diff 779671b. same-model inherit / clean-context only. No parchea.

[2026-08-18T18:46:41+00:00] PKG-5 · security-auditor · started · modelo cursor/inherit
Cliente: Un auditor mira si el reporter o el script del gate abren un agujero.
Ingeniería: security-auditor Cursor inherit readonly. same-model inherit / clean-context only. Superficie: verify.sh y verify_reporter.py. No parchea.

[2026-08-18T19:36:51+00:00] PKG-5 · orchestrator · done
Cliente: El segundo paquete quedo aceptado: los veinte minutos de chequeo ahora muestran progreso, la falla apenas ocurre, y un resumen con los tests mas lentos. Un primer intento se cayo porque el reporter no encontraba los tests; se arreglo y se clavo con una prueba.
Ingeniería: El presenter del gate vive en un modulo Python que verify.sh invoca. La ETA sale del ritmo medido. La suite completa paso: mil doscientos noventa y ocho tests en veinticuatro minutos, cero fallas. El panel de revision paso. Un fallo de gate se gasto en el ImportError, despues verde. No se paralelizo.
Aprendimos: Invocar un script deja el path de import en la carpeta del archivo; cambiar el directorio de trabajo no lo arregla. Un probe dentro del mismo proceso no ve ese crash porque tests ya era importable.
Conviene ahora: Implementar el paquete del menu Modelos para que pinte en menos de 300 ms con lo que ya esta en disco, y los datos vivos lleguen despues.
Por qué ahora: Sin eso, abrir Modelos sigue congelando unos dieciseis segundos, que es lo que mas se siente al usarlo.

[2026-08-18T19:37:08+00:00] PKG-2 · implementer · started · modelo cursor/inherit
Cliente: Se arregla el menu Modelos para que deje de congelarse dieciseis segundos: primero pinta lo de disco y despues refresca.
Ingeniería: implementer Cursor inherit. Context pack PKG-2.md. owned setup_models.py models_config.py mas excepciones de tests. No reescribir tui.with_progress. No sacar lanes (PKG-1).

[2026-08-18T19:52:21+00:00] PKG-2 · gate-runner · started · modelo cursor/inherit
Cliente: Se verifica que el menu ya no congela y que la suite completa sigue verde.
Ingeniería: gate-runner Cursor inherit readonly. heartbeat-run verify.sh. No repara.
