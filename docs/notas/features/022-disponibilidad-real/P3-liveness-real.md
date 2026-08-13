# 022-disponibilidad-real · P3-liveness-real

<!-- notas:auto -->
## Motivo

- objetivo: Que dar de baja una credencial se note en la decision siguiente, en los cuatro runtimes, y que haya una sola cache
- complejidad: high
- paths: `ai/scripts/routing_core/catalog.py`, `ai/scripts/set_agents_app.py`, `ai/scripts/models_config.py`, `tests/test_routing.py`
- depende de: P2-techo-catalogo-tri-estado

## Tareas

- [x] Firma de credencial por runtime en la clave de cache, todo stat local (AC-07) (completed) · unittest discover -s tests: 1006 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Las dos propiedades: refresh no invalida, logout si -- cada una con su test (AC-08) (completed) · unittest discover -s tests: 1006 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Validar con captura A/B real que los campos de claude no rotan en un refresh (AC-08) (completed) · PARCIAL Y DECLARADO ASI, no cerrado. Metodo cambiado por seguridad: se OBSERVA un refresh natural en vez de forzarlo, porque forzarlo puede rotar el refresh_token del usuario del lado del servidor y el usuario duerme y depende de esas credenciales manana. HECHO: snapshot A tomado (hashes POR CAMPO, nunca valores) de ~/.claude/.credentials.json y ~/.codex/auth.json; medido que claudeAiOauth.expiresAt vence a las 04:57 (195 min), asi que el refresh natural ocurre dentro de esta misma noche; verificado que a esa hora ningun campo habia cambiado todavia. PENDIENTE: snapshot B y la comparacion. COMPROMISO REGISTRADO en la nota de decision captura-ab-del-refresh-se-observa-no-se-fuerza: si B muestra que scopes, subscriptionType o rateLimitTier rotan, la firma de claude-code esta mal disenada y P3 SE REABRE. El diseno es robusto a esa incertidumbre por construccion -no lee campos rotantes- pero eso es un argumento, no una medicion, y asi queda escrito.
- [x] Disciplina de la firma y bump de _CACHE_SCHEMA_VERSION con test (AC-09) (completed) · unittest discover -s tests: 1006 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio
- [x] Una sola cache en la raiz del store, la legada podada con validaciones (AC-10) (completed) · unittest discover -s tests: 1006 OK / 3 skips (corrida del orquestador); verify.sh: VERIFY_PASS; build.sh --check: GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS; git diff --check limpio

## Hallazgos

- P3-F01 [critical] closed
- P3-F02 [high] closed
- P3-F03 [critical] closed

## Recorrido

- review: repair_required (2 hallazgos)
- verificación: 0 refutados, 2 sostenidos
- verificación: 0 refutados, 1 sostenidos
- repair: P3-F01, P3-F02 → 2 archivos
- repair: P3-F03 → 2 archivos
- delta review: repair_required
- delta review: pass
- testing: pass
- runtime QA: pass
- gate `unittest-suite`: pass
- gate `verify-sh`: pass
- gate `build-check`: pass
- gate `git-diff-check`: pass

## Spawns

- SPAWN-001 implementer · modelo anthropic/opus · effort medium · route run1_b2ca9919d72a9e94b1d918258278aae8
- SPAWN-002 package-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_1b7703d7fd206d4b0ea5ccffa15f1c71
- SPAWN-003 repair-agent · modelo anthropic/opus · effort medium · route run1_a9a7445cbce472688bae8ec45917d0f2
- SPAWN-004 delta-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_2eeb028ad4d02cd7141f3dd0381cc24e
- SPAWN-005 repair-agent · modelo anthropic/opus · effort medium · route run1_ccfef5c2dfb198444c20a5671ea4a1a9
- SPAWN-006 delta-reviewer · modelo openai-codex/gpt-5.6-terra · effort high · route dec1_686d159010ad27a477ce1f70d2ac5975

context pack: `docs/specs/022-disponibilidad-real/context/P3-liveness-real.md`

↩ [[features/022-disponibilidad-real|022-disponibilidad-real]]
<!-- /notas:auto -->

## Notas propias

_Lo que escribas fuera del bloque auto se preserva en cada regeneración._
