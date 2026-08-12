# build.sh --check compara siempre con --profile go-zen fijo, no con el perfil local

<!-- notas:auto -->
- fecha: 2026-08-12 · actor: orchestrator
- alcance: [[features/021-gates-que-no-mienten-ni-callan|021-gates-que-no-mienten-ni-callan]]

## Contexto

Hacer que --check compare STAGING contra Global/ implica elegir con que perfil generar el STAGING. active-profile esta en .gitignore y lo resuelve models_config.auto_profile() por maquina; los perfiles go-zen, zen y local difieren en 19 archivos; y Global/ esta commiteado bajo go-zen. Con el perfil local, install.sh:370 fallaria en toda maquina sin el par go vivo (rompiendo el onboarding antes de instalar nada) y setup_models.py:397,570 fallaria en todo cambio de modelo, que es su proposito. Lo encontro el spec-challenger como F-01 bloqueante, con los 19 archivos de diferencia medidos.

## Decisión

Federico eligio el perfil canonico fijo: --check genera el STAGING con --profile go-zen sin importar el active-profile local. El gate responde asi la pregunta de repositorio -- 'lo commiteado en Global/ es lo que genera _canonical?' -- y no la de maquina. install.sh y setup_models.py siguen funcionando sin tocarlos.

## Consecuencias

Un usuario con perfil local distinto no recibe un falso positivo de drift. A cambio, --check no verifica que el arbol generado para SU perfil sea correcto; eso lo cubre verify.sh, que genera con el perfil resuelto y comparaba ya. Queda documentado en ADR-0041.
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

**Rectificación 2026-08-12** (no borra lo de arriba): la frase del bloque auto "install.sh y
setup_models.py siguen funcionando sin tocarlos" es correcta para `install.sh`, pero **falsa para
`setup_models.py`** — sí se rompía (por una razón distinta al perfil: corre `--check`
inmediatamente después de escribir un `models.toml` nuevo, antes de que nada regenere `Global/`).
Detalle y arreglo en
[[decisiones/2026-08-12 correccion-setup-models-si-habia-que-tocarlo|correccion-setup-models-si-habia-que-tocarlo]].
