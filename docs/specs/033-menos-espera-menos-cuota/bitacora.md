# Bitácora — 033-menos-espera-menos-cuota

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T17:37:05+00:00

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
