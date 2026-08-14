# Changing agent models

**Cómo conviven la tabla y el router (ADR-0030):** la tabla por área de `models.toml` son los
**defaults curados** que se hornean en el frontmatter de cada agente al buildear — el fallback.
La selección viva la hace el router en cada spawn (`set-agents --route-decide`, para los 28
roles): en los lanes claude-code y pi la decisión pisa el frontmatter vía `--model`; en opencode
se materializa con las variantes `@tier` (6 roles tiered) y, para el resto, corre el default
curado registrando `MODEL_STATIC_FALLBACK` — visible, nunca silencioso. Fijar algo acá NO apaga
el router: es curar el fallback y las preferencias que el router respeta. El **effort** de la
decisión también viaja donde el runtime tiene la perilla: en el lane pi va como `--thinking`;
en claude-code no existe la perilla (y el catálogo clava anthropic en medium); en opencode/codex
el effort vive en la propia escalera de modelos y en la columna EFFORT estática.

Model routing lives in **`models.toml`**: active subscriptions, the model catalog, one model
set per **area** (the `duty` column of `roles.tsv`), and per-role overrides. `roles.tsv` holds
structure only (role, mode, temperature, capability, duty). `active-profile` selects the opencode
lane (`go-zen`/`zen`/`openai-only`) and is **auto-derived from the credentials probe** on the
first `./build.sh` (both opencode pairs live → go-zen, only zen → zen, none → openai-only).
Override with `PROFILE=<lane> ./build.sh --install`, or delete `active-profile` to re-derive.

## Suscripciones: tri-estado (ADR-0029) + overlay por máquina (ADR-0048)

Cada clave de `[subscriptions]` acepta tres estados:

- `true` — pin curado: confiás en que está activa (comportamiento histórico).
- `false` — exclusión dura: el build **muere** si algún modelo la referencia (histórico).
- **ausente** — automático: el harness la detecta con el probe de credenciales. El build sigue
  verde con un `WARN degraded` y el routing en vivo excluye ese proveedor solo
  (`PROVIDER_UNAUTHENTICATED`).

El `models.toml` trackeado **no declara ninguna suscripción** (ausente = auto para las cuatro,
siempre) — es el default neutro para que un tercero que clone el repo no herede las tuyas.
Tus valores reales viven **al lado**, en un overlay por máquina
(`~/.local/state/set-agentes/subscriptions.local.toml`, mismo precedente que
`model-preference.toml`): `./setup-models.sh` (opción "Suscripciones") o
`./setup-models.sh --add|--drop <nombre>` lo escriben ahí, de inmediato, nunca en el archivo
trackeado — así que usarlos no ensucia el árbol ni bloquea `--update`.

`SET_AGENTS_STRICT_MODELS=1` (CI) desactiva la tolerancia del estado ausente.

## The fast path: `./setup-models.sh`

```bash
./setup-models.sh                 # interactive wizard: pick area/role -> field -> model
                                  # (también: suscripciones tri-estado, detalle completo a
                                  #  demanda, y toggle de proveedores descubiertos ADR-0029)
./setup-models.sh --status        # current assignment per area + overrides + subscriptions
./setup-models.sh --check         # validate all three lanes without changing anything
```

Scriptable one-shots (validated, atomic, chained into build --check/--install):

```bash
./setup-models.sh --set audit.codex=gpt-5.6-sol
./setup-models.sh --set implement.opencode.go-zen=openai/gpt-5.6-terra
./setup-models.sh --set role:debugger.codex_effort=high
./setup-models.sh --add-model codex=gpt-6-nova     # extend the catalog when a model ships
```

### Subscriptions changed?

```bash
./setup-models.sh --add zen        # new subscription available
./setup-models.sh --drop zen       # cancelled one
```

`--drop` refuses to write while any role/lane still resolves to a model of that subscription:
it prints `AFFECTED=<n>` with every orphaned cell so you reassign them first (wizard or
`--set`). Dropping `openai`/`anthropic` also means the matching native harness (Codex/Claude
Code) has nothing to run on; its config is kept but unused. Both flags write your per-machine
overlay (ADR-0048), never `models.toml` — `git status` stays clean after either one.

Editing `models.toml` by hand is fine too — run `./setup-models.sh --check` afterwards. The
wizard rewrites the file deterministically and does not preserve standalone comments.

Validation (always on, doctrine): duplicate roles, unknown capabilities, missing canonical
prompts, catalog membership, inactive subscriptions, and **implementation-model reuse by an
auditor or judge** (family map in `[families]` for exceptions). Generated files under
`Global/{opencode,claude-code,codex}` and live harness directories must not be edited directly.

## Cheap-but-capable hosted models for the leaf roles (Ollama was pulled)
Ollama local was tried for the repetitive leaf/mechanical roles and **removed from the default path**: a 7B on
this CPU-only machine was too slow *and* not reliable enough — without repo grounding it hallucinated files and
classes that don't exist (`PrizeObligationRepository.cs`), so it burned audit round-trips instead of saving
money. It survives only as a **manual opt-in fallback** (point a cell at `ollama/...` and enable the `ollama`
subscription in `models.toml`); the provider stays defined in `Global/_shared/opencode.json` and
`ollama serve` on `:11434` for that case.

The leaf roles run on cheap **hosted** models, with the go-zen profile spending OpenAI subscription on
almost all daily work and keeping OpenCode Go as a single external audit lane:
- **Code-writers** (`implementer`, `frontend-engineer`, `refactor-specialist`) → `openai/gpt-5.3-codex-spark`
  in go-zen, so implementation does not burn the OpenCode Go five-hour quota. The `frontend-engineer` output
  still gets a mandatory strong `ux-ui-designer` aesthetic review.
- **Mechanical/script-gated** (`gate-runner`, `github-release-manager`, `memory-scribe`, `app-runner`) →
  `openai/gpt-5.4-mini` in go-zen; these roles should not spend Go quota.

`test-writer` uses `openai/gpt-5.6-terra` in go-zen because end-stage regressions need real assertions. The
review roster (`package-reviewer` — correctness/data-integrity/scalability in one pass, `security-auditor` —
offensive+defensive in one pass, `delta-reviewer`, `spec-challenger`) and the final judge all use GPT-5.6 Sol
through OpenAI. No role currently uses `opencode-go/*` in the go-zen profile — the standalone `auditor` role
that held that OpenCode Go "non-OpenAI second opinion" lane was folded into `package-reviewer` (same criteria,
same GPT-5.6 Sol model as the rest of the review panel). If you want that provider-diversity lane back, pick a
review-ro role and set its go-zen lane to an `opencode-go/*` model
(`./setup-models.sh --set role:package-reviewer.opencode.go-zen=opencode-go/...`).

The three lanes differ only in the opencode dimension: `go-zen` mixes OpenAI subscription models with
`opencode-go/*`, `zen` uses `opencode/*` routers, and `openai-only` uses `openai/*` only (the name is
literal — it is the lane the probe derives when neither OpenCode pair is live, ADR-0048).
`claude`/`codex` assignments are lane-independent (hosted).

## Codex reasoning effort (`codex_effort`)
Only Codex has a per-agent reasoning-effort knob (`codex_effort` → `model_reasoning_effort`). It is tuned by
activity: **xhigh** for auditors and the judge (best of the best), **high** for coordination/root-cause/spec
and the frontend aesthetic gate, **medium** for implementation (which is audited afterward), **low** for
mechanical/script-gated roles. OpenCode and Claude Code have no effort field — there, the "effort" is expressed
by which model the role gets.
