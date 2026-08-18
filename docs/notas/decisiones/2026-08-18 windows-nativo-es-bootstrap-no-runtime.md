# Windows nativo es objetivo de bootstrap, no de runtime

<!-- notas:auto -->
- fecha: 2026-08-18 · actor: orchestrator

## Contexto

La CI estuvo roja en las tres plataformas desde el 2026-07-24. El paso 'Full unittest suite' del job windows-bootstrap entro el 2026-08-01 y fallo en TODAS las corridas posteriores: nunca estuvo verde una sola vez. La ultima medida, run 32102631508, cerro en FAILED (failures=21, errors=96). Causa raiz: la suite invoca la toolchain POSIX del harness (bash + python3: set-agents, build.sh, install.sh) y Windows nativo no la tiene.

## Decisión

No se construye soporte nativo de Windows. README.md:107 ya declara el camino de Windows como install.ps1 -> WSL administrado, o sea que el harness corre sobre Linux aunque la maquina sea Windows, y verify-linux es el gate que lo cubre. Los tests que necesitan la toolchain POSIX saltan con la razon nombrada (tests/__init__.py, require_posix_toolchain), que es el mecanismo que el repo ya usaba en tests/test_provider_registry.py:463. Se corrige ADR-0041, cuyo punto 4 certificaba que 'la suite pasa en Windows'.

## Consecuencias

Windows prueba lo que su nombre dice: install.ps1 parsea, corre en -DryRun, los fuentes Python compilan, y el nucleo independiente de plataforma. En Linux y macOS no cambia nada, y test_the_posix_toolchain_is_present_on_every_platform_that_declares_it falla ruidosamente si la toolchain faltara ahi, para que el salto no pueda volverse un verde vacio. Si en algun momento se quisiera Windows nativo como runtime, es una feature nueva y contradice README:107.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Causa raíz medida (2026-08-18, run 32144718950)

El bloque de arriba nombró la causa en general ("Windows nativo no tiene la toolchain POSIX"),
pero las dos primeras versiones del probe midieron la capa equivocada y por eso el salto nunca se
activó: los skips subieron 357 → 361 y la suite siguió corriendo entera. El paso `Diagnose the
POSIX toolchain` imprimió el motivo real:

```
set_agents_app.py:1266  subprocess.run([str(script), "--quiet"], ...)
OSError: [WinError 193] %1 is not a valid Win32 application
```

`bash` 5.3 y `python3` 3.12 existen, y la ruta que bash calcula (`/d/a/set-agents/set-agents`)
Python la statea sin problema — o sea que las dos hipótesis anteriores (falta python3; las rutas
de Git Bash no componen) eran **falsas, y medirlas fue lo que las descartó**. Lo que falla está
una capa más abajo: `CreateProcess` no interpreta shebang, así que un `.sh` pasado como argv[0]
no es una imagen ejecutable. `ai/scripts/check-drift.sh` es sólo el primero de varios sitios así.

`tests/__init__.py:_detect_posix_toolchain` mide ahora exactamente eso: escribe un `.sh` con
shebang, lo hace ejecutable y lo exec-uta directo. `test_the_toolchain_probe_measures_exec_of_a_shebang_not_mere_presence`
lo fija, para que una tercera versión del probe no pueda volver a medir otra cosa.
