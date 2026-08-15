# P2-F11: run_gate filtra el entorno y el hijo escribe bytecode en el repo real, sin bwrap

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P2-nada-escribe-afuera|P2-nada-escribe-afuera]]

## Contexto

Hallazgo del segundo delta review independiente de 027/P2, encontrado corriendo y no leyendo. run_gate (ai/scripts/routing_core/gates.py:20-22) filtra el env del proceso hijo a las claves declaradas por su GateSpec, que son ('PYTHONUTF8',). El hijo pierde PYTHONDONTWRITEBYTECODE y py_compile escribe bytecode. Medido con tests/test_routing.py:1441 aislado y SET_AGENTS_TEST_NO_BWRAP=1: 7 archivos .pyc escritos en el repo real bajo ai/scripts/__pycache__ y ai/scripts/routing_core/__pycache__. Con bwrap: 0. La medicion de cierre de AC-04 no lo vio porque __pycache__ esta gitignoreado, no vive bajo Global/, y el .pyc es determinista -contenido identico, asi que ni el sha256 lo delata; lo cazo el mtime-.

## Decisión

Se acepta P2 con esta limitacion DECLARADA, no reparada. No es reparable dentro del paquete: la guarda de escritura es por interprete y gates.py es codigo de produccion, fuera de los owned_paths de P2. La afirmacion de cierre de AC-04 se corrigio en la evidencia: pasa de 'cero drift, byte-identico' a 'cero drift trackeado y cero drift de Global/, con un residuo medido de bytecode en el camino sin bwrap'. Es hermano de P2-F08.

## Consecuencias

El residuo es bytecode regenerable en un directorio ignorado, no estado ni credenciales, y los destinos que AC-04 nombra por escrito estan cubiertos en los dos modos. Pero la leccion de metodo es mas grande que el hallazgo: un manifiesto sha256 acotado a un directorio trackeado es ciego a lo gitignoreado, y un archivo determinista no cambia de hash aunque se reescriba. La medicion honesta necesita arbol completo, gitignoreados incluidos, y mtimes. La misma ceguera cubre ai/state/, active-profile, tools.local.toml, .build/, .staging/, .backups/ y todo .git/.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
