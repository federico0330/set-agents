# Generación de árboles de agentes

<!-- notas:auto -->
## Responsabilidad

Compila roles.tsv + models.toml + prompts canónicos en los árboles nativos por runtime (Claude Code, OpenCode, Codex, Pi) que build.sh instala.

## Posee

- `ai/scripts/generate.py`
- `ai/scripts/models_config.py`
- `Global/_canonical/**`

## Últimos cambios estructurales

- 2026-08-19 034-cuota-organica-y-writer-barato/PKG-B — El orquestador canónico documenta un solo salvage por paquete: si el escritor code-rw barato deja el gate rojo, repair-agent corre una vez más con override de invocación; el pin de repair-agent sigue…
- 2026-08-19 034-cuota-organica-y-writer-barato/PKG-D — generate.py emite model: por rol en Cursor; inherit en un reviewer (review-ro + audit/judge) muere en load_roles y validate_cursor_target. El escritor y repair-agent quedan en composer-2.5; los juece…
- 2026-08-19 034-cuota-organica-y-writer-barato/PKG-A — La doctrina canónica (triage y orquestador) unifica el default 1-3 con el error nombrado del CLI; los espejos de cada runtime se regeneran desde canónico.
- 2026-08-19 033-menos-espera-menos-cuota/PKG-1 — Tres lanes OpenCode (go-zen/zen/openai-only) colapsaron a un string. active_profile, auto_profile, --profile y active-profile desaparecieron. Si el proveedor esta exhausto, falla en voz alta en vez d…
- 2026-08-19 033-menos-espera-menos-cuota/PKG-2 — El wizard de modelos pinta el primer frame desde disco antes de probear suscripciones. El probe vivo corre despues, o con la tecla Refrescar.
- 2026-08-14 024-listo-para-terceros/C2-modelstoml-neutro — models.toml neutro, overlay del usuario en STATE_DIR, y la lane 'local' renombrada a 'openai-only'
- 2026-08-13 022-disponibilidad-real/P4-proveedores-del-usuario — El bloque provider de opencode.json se renderiza desde providers.toml en vez de estar hardcodeado en _shared
- 2026-08-12 021-gates-que-no-mienten-ni-callan/P2-gates-que-no-callan — Nuevo ai/scripts/heartbeat-run.py: corre un comando largo streameando su salida linea a linea e inyectando un latido sintetico si pasa el intervalo sin emitir. La doctrina contra el antipatron quedo …
- 2026-08-12 021-gates-que-no-mienten-ni-callan/P1-check-que-verifica — build.sh --check dejo de ser un no-op: genera con --profile go-zen FIJO y compara contra los cuatro arboles de Global/, fallando con rc distinto de cero y nombrando los archivos. Antes solo cotejaba …
- 2026-08-11 019-harness-evolution/P4-doctrine-human-layer — El arbol canonico (Global/_canonical/) sumo un comando nuevo, /explicar, con su skill, y la doctrina de tres roles (orchestrator, integrator, architect) mas request-triage y las 4 fuentes de Global/_…

_Debajo de esta línea la prosa es mantenida a mano — contrastala con la fecha del último cambio estructural._
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._

## Puntos de entrada

- `ai/scripts/generate.py:450` `generate(out, profile, roles_path=None, models_path=None,
  routes_path=None)` — compila un árbol completo a `out`.
- `ai/scripts/generate.py:716` `main()` — CLI (`--output`, `--profile`, `--check`, `--diff`).
- `build.sh` (raíz del repo) es el wrapper real: staging en tempdir, compara/copia contra los
  4 árboles de `Global/` + `PROYECTO/`, `--check` para verificar cero drift.

## Componentes

- `generate.py:55` `load_roles(profile, roles_path=None, models_path=None)` — lee
  `roles.tsv` + `models.toml`.
- `generate.py:129` `oc_permissions(...)` — arma los permisos por capacidad/rol para
  OpenCode (incluida la entrada `SAFE`/`deny` de `transition INTEGRATION*` que este mismo
  paquete no toca, ver ADR-0024).
- `generate.py:376` `generate_pi_prompts(out)` — arma los prompts que la lane Pi pasa
  vía `--append-system-prompt` (ADR-0007), sin árbol generado propio.
- `generate.py:657` `validate_pi_target(roles)` / `generate.py:678` `validate(...)` —
  chequeos de coherencia post-generación.
- `ai/scripts/models_config.py` — inventario descubierto (ADR-0029/0034), leído por
  `load_roles`/`generate` para resolver el perfil activo.

## Flujo

`build.sh` → `generate.py generate(out=staging, profile)` → lee `roles.tsv` + `models.toml`
+ `Global/_canonical/**` → escribe los árboles nativos (`Global/claude-code/`,
`Global/opencode/`, `Global/codex/`, prompts Pi) en el staging dir → `build.sh` copia el
staging sobre los 4 árboles de `Global/` y `PROYECTO/ai/scripts/` (incluida
`feature_state_lib/`, ver módulo `estado`) → `--check` vuelve a generar y diffea para
confirmar cero drift.

## Posee / Depende de

Posee: ver "Posee" arriba (`Global/_canonical/**` son las fuentes canónicas: prompts,
comandos, skills). Depende de `roles.tsv` y `models.toml` (raíz del repo, fuera de
`ai/scripts/`) como entrada de datos.

## Invariantes

- `Global/**` (git-tracked) nunca lleva paths absolutos: siempre el placeholder
  `__SET_AGENTS_ROOT__`, sustituido recién en `install.py` (ADR-0008,
  `docs/architecture/overview.md`).
- `./build.sh --check` sin drift es un gate real de la suite (`tests/test_harness.py`
  `test_check_and_native_codex_agents` lo corre primero).
- `feature_state_lib/` se copia byte-idéntica a los 3 `Global/*/hooks/` y a
  `PROYECTO/ai/scripts/` — un test de la suite pinea esa igualdad.

## Decisiones

- ADR-0007 (Pi lane, sin árbol generado propio), ADR-0008 (dos raíces: HARNESS_HOME vs
  PROJECT_ROOT, placeholder en `Global/**`), ADR-0017 (Pi interactive target).
