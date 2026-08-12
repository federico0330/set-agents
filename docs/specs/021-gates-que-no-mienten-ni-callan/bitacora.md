# Bitácora — 021-gates-que-no-mienten-ni-callan

_Generado por `feature-state.py`. Cada entrada trae la lectura para el cliente y la justificación de ingeniería. No editar a mano._

Actualizado: 2026-08-12T14:28:51+00:00

[2026-08-12T13:35:29+00:00] P1-check-que-verifica · implementer · started · modelo openai-codex/gpt-5.6-sol · effort medium
Cliente: Arreglar el control que decia verificar que los archivos generados estaban al dia y en realidad no verificaba nada.
Ingeniería: P1 de 021 (AC-01..05): --check compara el STAGING contra los 4 arboles con --profile go-zen FIJO (decision de Federico: con perfil local rompe install.sh:370 y setup_models.py). Reusa el diff de verify.sh:26-28, no el de --diff que lleva || true. AC-04 se resuelve por ORDENAMIENTO, sin tocar los 17 call sites.

[2026-08-12T14:28:51+00:00] P1-check-que-verifica · package-reviewer · started · modelo anthropic/sonnet · effort medium
Cliente: Un revisor independiente comprueba que el control arreglado detecta de verdad, y que no rompio el instalador ni el cambio de modelos.
Ingeniería: package-reviewer sobre 021/P1: anthropic/sonnet, independence_verified=true frente al writer openai-codex/gpt-5.6-sol. Eje critico: el implementer TOCO setup_models.py, que el context pack no listaba en owned_paths, porque encontro que la nota del orquestador ('sigue funcionando sin tocarlo') era falsa. Hay que validar el hallazgo, el arreglo y la ampliacion de alcance.
