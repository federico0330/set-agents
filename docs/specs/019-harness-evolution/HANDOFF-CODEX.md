# Handoff 019 — continuar desde P2 (prompt para Codex)

Estado al momento del handoff: **2026-08-10**, rama `main`, HEAD `76b50a7`, working tree sucio (sin
commits: todo el trabajo de P1 está en el árbol de trabajo). PKG-1 implementado, revisado y reparado.

---

## PROMPT (copiar desde acá)

Sos el orquestador del harness SET-AGENTES trabajando SOBRE el propio harness
(`/home/federico/SET-AGENTES`). Continuás la feature **019-harness-evolution**, que ya está iniciada,
con spec aprobada y con el paquete P1 terminado. Seguí el workflow del repo (paquetes → gates →
review independiente → repair consolidado → delta review → accept → integración).

### Qué leer primero (en este orden)

1. `docs/specs/019-harness-evolution/spec.md` — la spec aprobada. Los AC-01..AC-35 y las decisiones de
   producto (DEC-1..DEC-5) están **tomadas**: no las re-preguntes ni las re-litigues.
2. `docs/specs/019-harness-evolution/PROMPT-OPUS5.md` — el encargo original completo, con la auditoría
   Codex read-only de `routing_core` y los hallazgos que originaron cada AC.
3. `ai/state/features/019-harness-evolution.json` — el estado vivo (`feature-state.py`).
4. `docs/adr/0034-auto-adopted-providers.md` — lo que ya se decidió y por qué.
5. `/home/federico/.claude/CLAUDE.md` — reglas del harness.

### Lo que YA está hecho (no lo rehagas)

**P1-provider-auto-adoption (ADR-0034)** — implementado, revisado por un reviewer independiente
(PASS_CON_HALLAZGOS: 0 críticos, 0 altos, 2 medios, 4 bajos) y reparado. Cierra AC-01..AC-11.

- `discovered_providers = "auto"` es el nuevo default; `build_effective_snapshot` dejó de estar muerta.
- Fuente única `provider → prefijo CLI` compartida entre `routing_core.catalog` y `opencode_spawn.py`
  (la copia `_PROVIDER_PREFIXES` fue eliminada).
- Guardas: rutas inferidas capadas en `balanced` (`_FRONTIER_HINTS` eliminado), reason code nuevo
  `REVIEW_IDENTITY_UNRESOLVED_INFERRED` fail-closed, flag `is_inferred` explícito en el sort key.
- Probe-cache con key versionada (uid + config + schema v2 + path/mtime del binario opencode + set de
  auth fresco); re-rank tras reprobe fallido, con reason code aditivo `REPROBE_REJECTED`.
- Gates verdes: `unittest discover` 819 tests OK (skipped=3), `verify.sh` VERIFY_PASS,
  `build.sh --check` CHECK_PASS + SELF_SCAFFOLD_SYNC_OK, `git diff --check` limpio, ownership PASS.
- Evidencia: `docs/specs/019-harness-evolution/evidence/P1-implementer.md` y `…/P1-repair.md`.

**Medición viva ya hecha (opencode 1.18.14, 2026-08-10) — respetala, no la repitas.** Está en la spec
como M-1..M-4. Lo esencial:

| auth display | auth.json key | CLI id listable | modelos |
|---|---|---|---|
| `OpenCode Go` | `opencode-go` | `opencode-go` | 18 |
| `OpenAI` | `openai` | `openai` | 13 |
| `GitHub Copilot` | `github-copilot` | **ninguno** (`Provider not found`, incluso tras `--refresh`) | 0 |
| `OpenCode Zen` | `opencode` | `opencode` | 60 |

- **Copilot no es routable**: autenticado pero opencode no expone modelos suyos. Fail-closed, ya
  documentado en ADR-0034. No lo agregues a ninguna tabla.
- **`openai` no es un provider nuevo**: ya es el par `("opencode","openai-codex")`.
- `ollama` aparece sin credencial ⇒ queda fuera (la adopción es auth-gated).

### Estado abierto que tenés que atender

- **F-02 (medio, abierto)** — `models.toml:26-27`: las listas `[catalog].opencode_zen` y
  `opencode_go` tienen la medición del 2026-07-30. Como `_configured_models` (`catalog.py:157`)
  intersecta contra ese techo, `"auto"` no puede routear modelos vivos ausentes de la lista
  (`ling-3.0-tiny-free`, `longcat-2.0-free`, `mimo-v2.5-free`, `qwen3.5-plus`; go tiene 18 ids vivos
  contra 16 listados). **Ya está reasignado a P2 con excepción de ownership aprobada** en el state
  file. Re-medí en vivo antes de escribir y dejá la fecha en el comentario.
- **F-06 (bajo, abierto)** — es de procedimiento y ya está resuelto de hecho: el `OWNERSHIP_FAIL`
  provenía de la narración que genera el propio coordinador (`ai/state/STATUS.md`, `docs/notas/`).
  Corriendo `check-owned-paths.py` sobre el diff del implementer da `OWNERSHIP_PASS`. Cerralo con
  `record-delta-review --closed-finding` o dejá constancia en la integración.
- **Defecto conocido, ya registrado en `ai/state/decisions-log.jsonl`**: el nuevo default `"auto"`
  rompe `ai/scripts/setup_models.py:156` y `:364`, que hacen `list("auto")` → `['a','u','t','o']`.
  Reproducido: el panel imprime `proveedores descubiertos rutables: a, u, t, o`. **Es el primer ítem
  obligatorio de P2**, que es dueño del archivo y cuyo AC-16 reescribe esa misma línea.

### Lo que falta hacer

Cuatro paquetes, en orden. Ya están creados en el state file con sus ACs, tareas, owned/shared paths
y riesgos: `P2-billing-aware-ordering`, `P3-cognitive-module-docs`, `P4-doctrine-human-layer`
(depende de P3), `P5-tools-discovery`. La spec tiene el detalle de cada uno; el `PROMPT-OPUS5.md`
tiene el racional completo.

- **P2 (ADR-0035)** — AC-12..AC-16: `billing_rank` (0 = suscripción o modelo con sufijo `-free`, 1 =
  metered/desconocido) insertado en el sort key tras `TIER_ORDER` y antes de `_bias_rank`; las
  exclusiones duras no cambian, así que zen entra exactamente cuando es el único que satisface tier o
  independencia. Reason code aditivo. `set-agents --route-doctor`. Panel y wizard. Más el fix de
  `setup_models.py` y el refresh de `models.toml` (F-02).
- **P3 (ADR-0036)** — AC-17..AC-24: `docs/modules/` en español generado con `merge_note`/`write_note`
  de `render_notes.py`, registro `modules.toml`, motor `feature_state_lib/render_modules.py`,
  comandos `record-module-impact` / `module-impact-detect` / `--module-impact-waived`, gate de
  entrada a `INTEGRATION` + `done_ready`, sección de digest y seed real de este repo.
- **P4 (ADR-0036 + 0037)** — AC-25..AC-29: sub-bloque `Impacto humano:` en la narración, pasos nuevos
  en `integrator.md` y `architect.md`, protocolo `**Resolvé antes de preguntar (ADR-0037)**` con sus
  espejos, y el comando `/explicar` en los 4 runtimes.
- **P5 (ADR-0038)** — AC-30..AC-35: `--tools-propose` / `--tools-approve`, `tools.local.toml`,
  allowlist cerrada en `coord_policy.py`, doctrina de "tool faltante".

### Cómo trabajar

- **Un context pack por paquete**, en `docs/specs/019-harness-evolution/context/<PKG>.md`, con anclas
  `file:line` reales. Usá `docs/specs/019-harness-evolution/context/P1-provider-auto-adoption.md`
  como molde: objetivo, archivos con el porqué de cada uno, read-only, restricciones, validación
  local, evidencia esperada, checkpoint, fuera-de-alcance. Registralo con
  `feature-state.py update-package --context-pack …` (el pack tiene que ser más nuevo que el
  `updated_at` del paquete, o `--route-decide` responde `CONTEXT_MISSING`).
- **ADR primero, después test, después código.** `tests/test_routing.py` y `tests/test_harness.py`
  son suites-contrato: pinean frases doctrinales por grep, defaults y la byte-igualdad de las copias
  de `feature_state_lib` en los 4 árboles + `PROYECTO/`. Enumerá test por test qué cambiás y por qué,
  con el ADR como fuente.
- Tras tocar `Global/_canonical/` o `feature_state_lib/`: **siempre** `./build.sh` y después
  `./build.sh --check` para verificar drift.
- **`pytest` NO está instalado en esta máquina.** Usá `python3 -m unittest discover -s tests` (la
  suite completa tarda ~7 min) o `python3 -m unittest tests.test_routing -k <patrón>` para focalizar.
  `./ai/scripts/verify.sh` corre unittest y da `VERIFY_PASS`.
- El ownership del state file manda sobre el texto del context pack cuando entran en conflicto (P1 lo
  aprendió: revirtió cambios en `models.toml` por eso). Si una tarea se desplaza por ownership,
  **reasignala explícitamente** con `log-decision` + `update-package --exception`, o se pierde.
- Ownership check: corré `check-owned-paths.py` **sobre el diff del implementer**, excluyendo lo que
  genera el propio coordinador (`ai/state/`, `docs/notas/`, `docs/specs/019-*`).

### Comandos útiles verificados

```bash
# estado
python3 ai/scripts/feature-state.py status --state-file ai/state/features/019-harness-evolution.json

# decisión de ruteo (claves válidas del descriptor: role, task_class, risk,
# review_of_run_id, selected_runtime, feature_id, package_id)
echo '{"role":"implementer","task_class":"implementation","risk":"high","feature_id":"019-harness-evolution","package_id":"P2-billing-aware-ordering"}' \
  | ./set-agents --route-decide - --fresh-probes
./set-agents --routing-decisions --limit 5

# gates
python3 -m unittest discover -s tests
./ai/scripts/verify.sh
./build.sh --check
git diff --check
```

Ojo con el ciclo de findings: `record-review` toma `--finding` como **JSON** (`id` + `severity`
obligatorios); reparar un hallazgo por encima de `low` exige un `record-verification` previo
(`--verdict '{"id":"F-01","verdict":"upheld"}'`), y el waiver `--skip-reason` solo sirve si **todos**
los hallazgos abiertos son `low`.

### Criterio de cierre de la feature

(a) suite completa verde; (b) con los providers opencode autenticados, `set-agents
--routing-decisions` muestra decisiones nuevas con providers descubiertos y el billing rank;
(c) `docs/modules/` seedeado y `feature-state.py digest` muestra "Qué cambió en el software";
(d) `/explicar routing` devuelve un trace coherente; (e) ADRs 0034-0038 escritos e indexados en
`docs/adr/README.md`; (f) el bloque de fin de turno explica en registro Cliente qué cambió.

### Question policy

Solo preguntás decisiones de producto incompatibles, cambios grandes de alcance, operaciones
irreversibles, credenciales fuera de alcance tras el intento resolve-first, o bloqueos tras agotar el
presupuesto de reintentos. No preguntes por fallas de test de rutina, reruns de gates, reparaciones
exigidas ni por continuar trabajo ya aprobado. Nada de lo que ya está en la spec o en
`ai/state/decisions-log.jsonl` es preguntable.
