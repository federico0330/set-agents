# El CI lleva doce dias en rojo por tres causas independientes, una por sistema operativo

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator

## Contexto

Diagnosticado en la auditoria, sobre el job 31142809189 del 2026-08-07. LINUX: 4 fallas de 805. Una era el indice de ADRs y ya se arreglo sola (docs/adr/README.md:40 tiene la fila desde el 2026-08-10). Las otras tres -test_model_preference_production_plumbing_end_to_end_via_real_cli, test_route_terminal_large_but_valid_usage_still_closes_the_run y test_route_terminal_usage_flows_from_the_cli_into_the_stored_row- manejan el CLI real y exigen credenciales vivas: un runner hospedado no tiene login, toda ruta se excluye con PROVIDER_UNAUTHENTICATED y --route-decide sale con 1. NO PUEDEN pasar nunca en GitHub Actions tal como estan escritos. MACOS: 15 fallas y 57 errores, una sola causa raiz: _private_dir (store.py:381) rechaza cualquier ancestro que sea symlink, y en macOS tempfile devuelve /var/folders/... donde /var es symlink a private/var. El control es correcto para produccion; el que esta mal es el test, que deberia usar Path(td).resolve(). WINDOWS: 30 fallas, 151 errores, y solo corrio 508 de 805 tests, por 'ModuleNotFoundError: No module named pwd' desde set_agents_app.py:14, que importa pwd sin guarda de plataforma. Seis modulos de test enteros no importan. Y el paso previo 'Compile python scripts' pasa en verde porque py_compile NO importa el modulo: es un falso verde dentro del propio workflow.

## Decisión

Va a la feature 030 como paquete aparte del de seguridad, en este orden: import pwd condicional o restringir el job de Windows al subconjunto que tiene sentido; .resolve() en los tempdirs de los tests de store para macOS; y costura hermetica o skipUnless de credenciales para los tres tests de routing. RoutingStore._check_supported (store.py:376) rechaza explicitamente os.name != posix, asi que correr discover -s tests entero en Windows contradice el propio diseno del store y hay que decidirlo, no parchearlo.

## Consecuencias

Doce dias de CI rojo significan doce dias sin la unica verificacion multi-OS que el repo declara, justo cuando se hizo publico y el README promete instalacion en tres sistemas. Y el falso verde de py_compile en el workflow es de la misma familia que los seis defectos de 027: un paso que informa OK sobre algo que no mira.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
