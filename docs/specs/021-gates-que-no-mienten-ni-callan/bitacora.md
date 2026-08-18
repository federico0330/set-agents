# Bitácora — 021-gates-que-no-mienten-ni-callan

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-18T15:34:35+00:00

[2026-08-12T13:35:29+00:00] P1-check-que-verifica · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Arreglar el control que decia verificar que los archivos generados estaban al dia y en realidad no verificaba nada.
Ingeniería: P1 de 021 (AC-01..05): --check compara el STAGING contra los 4 arboles con --profile go-zen FIJO (decision de Federico: con perfil local rompe install.sh:370 y setup_models.py). Reusa el diff de verify.sh:26-28, no el de --diff que lleva || true. AC-04 se resuelve por ORDENAMIENTO, sin tocar los 17 call sites.

[2026-08-12T14:28:51+00:00] P1-check-que-verifica · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente comprueba que el control arreglado detecta de verdad, y que no rompio el instalador ni el cambio de modelos.
Ingeniería: package-reviewer sobre 021/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje critico: el implementer TOCO setup_models.py, que el context pack no listaba en owned_paths, porque encontro que la nota del orquestador ('sigue funcionando sin tocarlo') era falsa. Hay que validar el hallazgo, el arreglo y la ampliacion de alcance.

[2026-08-12T15:59:43+00:00] P2-gates-que-no-callan · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Ultimo tramo de esta feature: que cuando el harness este trabajando varios minutos, se note, en vez de parecer colgado.
Ingeniería: P2 de 021 (AC-06..09). Causa raiz CORREGIDA: no es buffering del escritor sino que tail -N sin -f no puede emitir hasta EOF; stdbuf NO lo arregla, verificado. AC-09 es prevencion hacia adelante, no correccion: el patron no esta en ningun archivo versionado (grep da cero en Global/_canonical y en los context packs), vivia en texto efimero de spawn. Patron de grep ya fijado en la spec: barra-vertic… _(truncado al render)_

[2026-08-12T18:07:34+00:00] P2-gates-que-no-callan · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Ultima verificacion independiente antes de cerrar esta feature.
Ingeniería: package-reviewer sobre 021/P2: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-luna. Re-decidido con risk=medium tras un primer decide con risk=low que devolvia haiku: el paquete agrega un script ejecutable que corren los agentes y doctrina que propaga a los 4 arboles, no es low. El paquete se completo en DOS instancias: la primera murio por limite de sesion dej… _(truncado al render)_

[2026-08-12T20:21:56+00:00] P2-gates-que-no-callan · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Primera mitad de la verificacion independiente, en dos partes chicas porque la version completa murio dos veces.
Ingeniería: Review PARTIDO tras dos muertes por stall del encargo completo (decision registrada en slug sexto-stall-segunda-muerte-del-mismo-encargo, Federico eligio la opcion a). Parte A: AC-06 heartbeat-run.py y sus bordes, mas AC-08. Sin suite completa. Misma decision de routing para las dos mitades.

[2026-08-12T20:21:56+00:00] P2-gates-que-no-callan · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Segunda mitad de la verificacion independiente.
Ingeniería: Parte B: AC-07 (donde vive la doctrina y si propaga de verdad), AC-09 (el test y su mordida), residuos del antipatron, y la pregunta de si AC-07 promete mas de lo que entrega dado que la doctrina la carga el que REDACTA y no el que ejecuta. Sin suite completa.

[2026-08-12T21:09:05+00:00] done
Cliente: La feature 021 quedo cerrada. El control que decia verificar que los archivos generados estaban al dia ahora los verifica de verdad, y cuando el harness trabaja varios minutos se nota en vez de parecer colgado.
Ingeniería: 021 DONE. 2 paquetes, ADR-0041. build.sh --check pasa de no comparar nada a comparar los 4 arboles con perfil go-zen fijo; heartbeat-run.py mas la doctrina imperativa en spawn-prompt y punteros en los skills del ejecutor. Suite 970 -> 979. Los gates finales se corrieron CON heartbeat-run.py y emitio 4 latidos en 489s.
