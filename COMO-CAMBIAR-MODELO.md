# Changing agent models

Model routing lives in **`models.toml`**: active subscriptions, the model catalog, one model
set per **area** (the `duty` column of `roles.tsv`), and per-role overrides. `roles.tsv` holds
structure only (role, mode, temperature, capability, duty). `active-profile` still selects the
opencode lane (`go-zen`/`zen`/`local`) without rewriting anything.

## The fast path: `./setup-models.sh`

```bash
./setup-models.sh                 # interactive wizard: pick area/role -> field -> model
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
Code) has nothing to run on; its config is kept but unused.

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
`opencode-go/*`, `zen` uses `opencode/*` routers, and `local` uses `openai/*` only. `claude`/`codex`
assignments are lane-independent (hosted).

## Codex reasoning effort (`codex_effort`)
Only Codex has a per-agent reasoning-effort knob (`codex_effort` → `model_reasoning_effort`). It is tuned by
activity: **xhigh** for auditors and the judge (best of the best), **high** for coordination/root-cause/spec
and the frontend aesthetic gate, **medium** for implementation (which is audited afterward), **low** for
mechanical/script-gated roles. OpenCode and Claude Code have no effort field — there, the "effort" is expressed
by which model the role gets.
