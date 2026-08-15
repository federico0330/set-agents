# P2-F12 a P2-F15: la guarda cierra los casos nombrados, no las clases

<!-- notas:auto -->
- fecha: 2026-08-15 · actor: orchestrator
- alcance: [[features/027-controles-que-miran|027-controles-que-miran]] · [[features/027-controles-que-miran/P2-nada-escribe-afuera|P2-nada-escribe-afuera]]

## Contexto

Cuatro hallazgos low/medium del segundo delta review de 027/P2, ninguno bloqueante, ninguno con call site vivo que los aproveche. P2-F12 (tests/test_harness.py:77-284): el lint estatico caza los tres bypasses de la review anterior pero el reviewer escribio nueve nuevos de las mismas familias y ocho pasan invisibles -constante de modulo como --output, 'bash ./build.sh', str(ROOT/'build.sh'), subprocess.check_output, alias 'import subprocess as sp', 'from subprocess import run as srun', async def, y sentencia a nivel modulo-. P2-F13 (tests/__init__.py:226): ATTACH DATABASE y VACUUM INTO desde una conexion :memory: exenta crean archivos arbitrarios sin emitir sqlite3.connect. P2-F14 (tests/__init__.py:241-282): sonda de 13 APIs de C; escapan os.mkfifo, os.mknod, socket.bind AF_UNIX y os.setxattr, y mkfifo ya se usa hoy en tests/test_routing.py:3258. P2-F15 (tests/__init__.py:189): la mitad 'preservar la entrada final lexicamente' de la reparacion de P2-F02 no tiene mordida: el mutante que la revierte deja el test en verde.

## Decisión

Se aceptan como deuda declarada y van a una feature de seguimiento, no a un tercer ciclo de reparacion de P2. El paquete ya consumio sus dos ciclos de deep review, ninguno de los cuatro tiene call site vivo, y P2-F14 en particular no es cerrable con addaudithook -mkfifo y mknod no emiten evento en CPython-, o sea es P2-F08 otra vez.

## Consecuencias

El patron que comparten los cuatro es el mismo y es la leccion: la guarda cierra los CASOS NOMBRADOS y no las CLASES. Un lint que enumera receptores ('subprocess'), nombres de funcion ('run', 'Popen') y tipos de nodo AST (FunctionDef) tiene por techo su propia enumeracion, igual que AC-19 de la feature 029 tiene por techo la enumeracion de su AC-18. La contramedida de metodo, que vale para todo el harness: los modos de falla se enumeran DESPUES de intentar burlar la regla, y la evidencia de una guarda debe incluir los ataques conocidos corriendo en rojo.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
