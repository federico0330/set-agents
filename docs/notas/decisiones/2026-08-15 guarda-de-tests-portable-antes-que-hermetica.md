# La guarda de escritura de tests degrada en vez de exigir bubblewrap

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P2-nada-escribe-afuera|P2-nada-escribe-afuera]]

## Contexto

Para cerrar P2-F01 (los procesos hijos no heredan el audit hook de Python), la implementacion de 027/P2 envolvio todo subprocess.Popen en /usr/bin/bwrap y copio el repo entero (31 MB) en cada corrida. Medido: la suite paso de ~1050 s con 1123 tests a 1809 s con 1130 (docs/specs/027-controles-que-miran/evidence/P2-gates-retry.md:61). Y .github/workflows/ci.yml corre verify.sh en ubuntu-latest y macos-latest y la suite completa en windows-latest, los tres con timeout-minutes 20: bubblewrap no existe en macOS ni Windows, asi que ahi cada subproceso de test moriria con FileNotFoundError. ai/scripts/verify.sh:57 declara explicitamente que CI corre en Linux y macOS, y el README recien reescrito promete instalacion multi-OS.

## Decisión

Degradacion portable, decidida por Federico el 2026-08-14. El audit hook in-process queda activo siempre y en todo sistema operativo: es la capa que cumple AC-04 y AC-05. La frontera de bubblewrap para procesos hijos se activa solo si shutil.which('bwrap') la encuentra, la copia del repo pasa a ser lazy y solo ocurre cuando esa frontera se monta de verdad, y los tres tests que dependen de la frontera se skipean cuando no esta. Al degradar se emite una linea unica por stderr: una guarda que se apaga en silencio es el defecto que esta feature entera vino a reparar.

## Consecuencias

Linux con bubblewrap conserva la garantia fuerte contra un hijo que escriba a una ruta absoluta externa. macOS, Windows y Linux sin bubblewrap conservan la guarda in-process mas la reubicacion de HOME/TMPDIR/SET_AGENTS_STATE que los hijos heredan, que es lo que cubre el caso real de 024/C2. El limite queda declarado, no disimulado: un hijo con ruta absoluta hardcodeada no se ataja fuera de Linux. CI vuelve a ser ejecutable en los tres sistemas.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
