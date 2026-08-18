# Traspaso a Copilot (segunda tanda) — 2026-08-18

Continuación desde `68d07c6`. Objetivo: dejar el estado del repo **limpio**, sin nada pendiente
salvo lo que depende de un tercero. Ver [[TRASPASO-COPILOT]] para la tanda anterior.

---

Sos el orquestador del harness SET-AGENTES, sobre el harness mismo, en `/home/federico/SET-AGENTES`,
branch `main`, base `68d07c6`. El repo es **público**.

File-first y gate-driven. El estado durable se muta **sólo** con
`python3 ai/scripts/feature-state.py <verbo>`, nunca editando JSON a mano.

## Estado medido hoy

- `HEAD` = `origin/main` = `68d07c6`. Árbol limpio, nada sin pushear, instalación al día.
- Gate **local**: `Ran 1266 tests in 866.950s, OK (skipped=4), VERIFY_PASS` + `BUILD_CHECK_PASS`.
- **25 de 28 features en DONE.** Abiertas: 002 y 011 (BLOCKED por causas externas), 024 (BLOCKED por
  una causa que ya no existe).

## Objetivo 1 — la CI está ROJA en las tres plataformas. Es lo más importante.

El gate local pasa y la CI falla en **todos** los pushes. Último run: `32088363836`.

```
windows-bootstrap  failure
verify-linux       failure   Ran 1266 tests -> FAILED (failures=3, errors=3, skipped=7)
verify-macos       failure   Ran 1266 tests -> FAILED (failures=4, errors=4, skipped=7)
```

Un gate verde local con CI roja es peor que no tener CI: entrena a todos a ignorarla. Tres causas
distintas, ya diagnosticadas — **verificalas antes de reparar, no me creas**.

### Causa A — tests que leen estado local no rastreado (Linux y macOS)

`.gitignore:53` ignora **todo** `/ai/state/` (decisión de 024/C1: el historial no viaja en el clon;
`ai/scripts/seed-state.py` lo reconstruye desde `ai/state.seed/`). En un clon limpio ese directorio
está vacío. Pero hay tests que leen de ahí **datos de la historia real de Federico**:

```
tests/test_routing.py:2867
    identity = json.loads((ROOT / "ai/state/project.json").read_text())["project_key"]
    -> FileNotFoundError en CI

tests/test_harness.py:6156
    self.assertIn("ac09-ac10-pi-minimal-target-accepted", decisions_log.read_text())
    -> FileNotFoundError en CI
```

Afectados: `test_routing_migrate_uses_harness_identity_and_test_store`,
`test_comment_only_divergence_migrates_and_opens`,
`test_routing_migrate_prints_the_divergence_to_stderr`,
`test_the_migration_banner_reports_the_versions_it_observed`,
`test_adr_0017_and_0007_amendment_and_superseding_decision_recorded`.

Es la misma familia que ADR-0051 (aislamiento de tests) que reparó la feature 027 — un test que
depende del estado de producción. **La reparación correcta es que cada test arme su propio fixture**,
no que se saltee en CI ni que se commitee `ai/state/`.

### Causa B — la generación no es reproducible entre máquinas (Linux y macOS)

`test_guest_copy_scaffolds_and_verifies_portably` falla porque el árbol generado **rastreado** difiere
del que produce una generación fresca en CI:

```
--- Global/opencode/agents/agent-factory.md        (rastreado)
+++ .../set-agents-guest-.../opencode/agents/agent-factory.md   (generado en CI)
-model: openai/gpt-5.4-fast
+model: openai/gpt-5.5
```

Los dos valores salen de `models.toml`: la línea 107 mapea `go-zen = "openai/gpt-5.4-fast"` y la 137
mapea, para otra área, `go-zen = "openai/gpt-5.5"` — con un comentario en la 135 que dice
*"Realigned to openai/gpt-5.5 ... which collides with"*. Cuál gana depende de algo que difiere entre
mi máquina y CI (sospecha fuerte: CI reporta `PROVIDERS_NONE`, sin ninguna suscripción detectada, y
la generación consulta proveedores vivos). **Confirmá la dependencia real antes de tocar.**

Esto **es** el hallazgo `F-04` de `020-honest-dashboard`, que sigue `open` y dice textualmente que
`CHECK_PASS` y `SELF_SCAFFOLD_SYNC_OK` *"no comparan contra el estado real de `Global/`"*. Repararlo
cierra las dos cosas: la CI y el hallazgo.

### Causa C — Windows importa un módulo POSIX (windows-bootstrap)

```
import pwd
ModuleNotFoundError: No module named 'pwd'
```

`pwd` no existe en Windows. Import incondicional en algún módulo que la suite carga. Y `install.ps1`
existe, o sea que Windows es plataforma soportada declarada.

**Criterio de cierre del objetivo 1**: los tres jobs en verde en un push real, no en tu máquina.
Si alguna causa exige una decisión de producto (por ejemplo: "Windows deja de ser soportado"),
**preguntá** en vez de decidir.

## Objetivo 2 — cerrar 024

**Federico autoriza explícitamente**, en la conversación del 2026-08-18:

> *"Ok, entonces habria que darle un prompt a copilot para que resuelva todo eso que queda."*

El blocker de 024 dice *"generate.py:475 shippea el codename de un cliente real"*. Ya **no** lo
shippea: lo removiste en `68d07c6`. La causa del bloqueo no existe.

Verificalo vos mismo antes de resolver
(`grep -rn "replenishment-v2\|RPL-P0A" ai/scripts/generate.py Global/ TIPS-USO.md` tiene que dar
vacío), después `reopen` con `--authorized-by "Federico — autorización explícita 2026-08-18"` y
llevala a `DONE`. Los cuatro paquetes ya están aceptados con review independiente.

**No** toques los codenames que quedan en `tests/test_harness.py` como nombres de fixture
(`pymepilot` 97 veces, `iey` 12, `replenishment-v2` 7). 024/C4 los evaluó y los mandó a un paquete
dedicado a propósito, porque renombrarlos toca decenas de asserts
(`docs/specs/024-listo-para-terceros/evidence/C4-implementer.md`, sección "Cuarto"). Está documentado,
no olvidado.

## Objetivo 3 — el residuo del borrado del codename

Al irse la regla, se fue también la frase que decía que `package-gate-runner` estaba *"unavailable for
every other feature, package, worktree, and baseline"*. El agente **sigue permitido** en
`Global/opencode/agents/orchestrator.md:42` (`"package-gate-runner": allow`), así que ahora un
orquestador de opencode podría rutearle gates de cualquier paquete.

Fallaría cerrado —su definición tiene `read: "*": deny` y todos los `allow` apuntan a marcadores
`<ABS_REPO_ROOT>`/`<FEATURE_ID>` que **nada sustituye** (lo verifiqué: no hay sustitución en
`generate.py`, `install.py` ni `set_agents_app.py`)—, así que es inútil, no peligroso. Pero es un
cambio de conducta que nadie probó.

Agregá al agente una línea que diga que es una **plantilla**, no un agente activo, y un test que lo
afirme. Si te parece mejor sacarlo del allowlist, proponelo y preguntá — es cambio de producto.

## Objetivo 4 — los dos hallazgos abiertos dentro de features cerradas

Hay hallazgos `open` en features que figuran `DONE`. Con los verbos de 031 ya existe el camino para
cerrarlos como corresponde.

- **`016-audit-debt-repayment` / `P1-harness-debt` / `P1F-01`** — severidad low.
  *"El pop de `repair_entry` en `cmd_transition` está anidado bajo `if args.package_id` (opcional)"*,
  en `ai/scripts/feature-state.py:2014-2027`. `transition PACKAGE_REPAIR` sin `--package-id` es legal
  y saltea el pop. El propio hallazgo trae `suggested_fix`. Daño acotado, pero es real.
- **`020-honest-dashboard` / `P2-anclas-verificables` / `F-04`** — es la Causa B del objetivo 1.
  Cerralo con esa reparación, no por separado.

Los tres hallazgos de `004-adaptive-dispatch` con estado `accepted` (`SEC-A02`, `PKG-N03`, `PKG-N04`)
son desvíos aprobados a propósito. **No los toques.**

## Objetivo 5 — higiene de repo público

- **`ai/scripts/set_agents_app.py.bak` está rastreado en git**: 11.985 líneas contra las 4.372 del
  archivo vivo. Entró en `2f199d5` (025/D1). Es un backup accidental. Borralo del índice y agregá
  `*.bak` al `.gitignore` con un test que impida que vuelva a entrar — 024 fue literalmente la feature
  de higiene de repo público y esto se le escapó.
- **20 ramas `worktree-agent-*` y 8 worktrees en `.claude/worktrees/`**. El directorio está
  gitignoreado, pero las ramas están en el repo. **Antes de borrar ninguna, verificá que su trabajo
  ya esté en `main`** (`git log main..<rama> --oneline`); si alguna tiene commits únicos, decilo en vez
  de borrarla. `git worktree prune` para las que ya no tengan directorio.

## Objetivo 6 — `D5-vault-en-todo-spawn` sigue con un worktree como `diff_ref`

En `ai/state/features/025-consola-minima-y-flexible.json`, ese paquete tiene
`diff_ref: "WORKTREE-D5-2026-08-17"` — un worktree de agente, no un SHA. El paquete `D5-correctiva`
que creaste sí tiene el rango real. Corregí el viejo con `amend-package` (o el verbo que corresponda)
para que el registro deje de decir dónde NO se midió.

## Objetivo 7 — dejar declarado por qué 002 y 011 siguen abiertas

"Limpio" no quiere decir "todo en DONE": quiere decir que **lo que está abierto explica por qué**.
Las dos están BLOCKED por causas que no son código:

- **`002-adaptive-pi-orchestration`**: `P1-routing-core` en `repair_required` con **cinco hallazgos
  altos vivos** (`P1-DR2-001`, `002`, `003`, `007`, `008`), 12 spawns y 2 ciclos de deep review
  agotados. El blocker pide rediseño.
- **`011-quota-failover`**: AC-06 exige una suscripción de Anthropic genuinamente agotada junto a un
  proveedor alterno usable. No se puede fabricar.

Revisá que el texto de cada blocker siga siendo **cierto hoy** (el de 024 no lo era) y actualizalo si
cambió. No las cierres ni las toques más allá de eso.

## Reglas que costaron caro — no las re-aprendas

1. Nunca leas `$?` después de un pipe: devuelve el exit code del último comando, no del que importa.
   Usá `${PIPESTATUS[0]}` o redirigí a archivo.
2. Medí sobre el árbol integrado, nunca sobre el worktree del agente. Un `diff_ref` que dice
   `WORKTREE-...` es la señal de que esto ya pasó.
3. Verificá el artefacto antes de aceptar el reporte de un agente: `git rev-parse` + `grep` de un
   símbolo que el trabajo debería haber creado.
4. Un revisor no puede citar como evidencia el documento que escribió el implementer. Así se aceptó
   D5, y se le coló una regresión de seguridad.
5. **Un commit no toca archivos fuera de su alcance declarado.** `f688531` revirtió un arreglo de
   seguridad y reescribió el comentario para justificarlo, bajo un rótulo que hablaba de otra feature.
6. **Si escribís que una decisión es de Federico, no la apliques en el commit siguiente.** Pasó con la
   Opción A de 024: `f0e281a` dijo *"no se aplica ninguna opción sin confirmación explícita"* y
   `68d07c6` la aplicó. Acertaste, pero decidiendo algo que dijiste que no ibas a decidir.
7. Toda prueba nueva se demuestra en las **dos** direcciones: rompé la implementación, mirá el test
   en rojo, restaurá, mirá el verde. Y si un test **existente** se pone rojo por tu cambio, entendé
   por qué antes de tocarlo — a veces tiene razón.
8. Nunca `git checkout` / `git restore` / `git stash` sobre archivos de trabajo. Para la mordida,
   `cp` y `cp`.
9. Watchdog: un agente sin output por 600s muere; el background se corta a ~650s y la suite tarda
   ~870s. Corré la suite con `setsid nohup` redirigiendo a archivo.
10. Nunca toques nada bajo `~` salvo `./build.sh --install --yes`, que es el camino sancionado.
11. El espejo `PROYECTO/ai/scripts/` tiene que quedar byte-idéntico a `ai/scripts/` para
    `narration_lint.py`, `feature-state.py` y `feature_state_lib/cli_reporting.py`. Hay un test que lo
    exige. Después de tocar `Global/_canonical/` o `Global/_shared/`, corré `./build.sh`.

## Cómo verificar que arrancás bien

```bash
git log --oneline -1                                          # 68d07c6
git status --short | wc -l                                    # 0
gh run list --limit 1                                         # tiene que decir failure — ese es el trabajo
grep -rn "replenishment-v2" ai/scripts/generate.py            # vacío
git ls-files | grep "\.bak$"                                  # ai/scripts/set_agents_app.py.bak
```

## Criterio de cierre

Los tres jobs de CI en verde en un push real; `ai/scripts/verify.sh` → `VERIFY_PASS`;
`./build.sh --check` → `GLOBAL_TREE_SYNC_OK` + `BUILD_CHECK_PASS`; instalado; cero hallazgos abiertos
fuera de 002; 26 features en DONE y sólo 002 y 011 abiertas, cada una con un blocker cuyo texto es
cierto hoy; árbol limpio y pusheado.
