# Changing an agent model

`roles.tsv` is the only role/model roster. Each role has one row with separate `opencode_go`,
`opencode_zen`, and `opencode_local` columns; `active-profile` selects one without rewriting the roster.

1. List valid provider models with `opencode models`.
2. Edit the relevant model cell in `roles.tsv`.
3. Run `./build.sh --check` and `./build.sh --diff`.
4. Run `./build.sh --install`; inspect the managed live diff and confirm once.

Use `./use-go-zen.sh`, `./use-zen.sh`, or `./use-local.sh` to switch `active-profile` and enter the same
reviewed installation flow. Generated files under `Global/{opencode,claude-code,codex}` and live harness
directories must not be edited directly.

## Cheap-but-capable hosted models for the leaf roles (Ollama was pulled)
Ollama local was tried for the repetitive leaf/mechanical roles and **removed from the default path**: a 7B on
this CPU-only machine was too slow *and* not reliable enough — without repo grounding it hallucinated files and
classes that don't exist (`PrizeObligationRepository.cs`), so it burned audit round-trips instead of saving
money. It survives only as a **manual opt-in fallback** (edit a cell in `roles.tsv` to `ollama/...`); the
provider stays defined in `Global/_shared/opencode.json` and `ollama serve` on `:11434` for that case.

The leaf roles now run on cheap **hosted** models, with the go-zen profile spending OpenAI subscription on
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
review-ro role and set its `opencode_go` cell in `roles.tsv` to an `opencode-go/*` model.

The three profiles differ in the hosted model column selected by `active-profile`: `go-zen` mixes OpenAI
subscription models with `opencode-go/*`, `zen` uses `opencode/*` routers, and `local` uses `openai/*` only.
Only OpenCode has a local-model column; `claude_model`/`codex_model` are profile-independent (hosted).

## Kimi Alegretto as the strong implementer (one-cell change)

Model-id validation is provider-agnostic: OpenCode ids are checked by shape only (`provider/model`), so a new
provider needs **no code change** — only a cell edit. Codex ids come from the extensible `CODEX_MODELS` set in
`generate.py` (add one line there for a new Codex tier). Kimi lands as an OpenCode provider alongside GPT.

To make Kimi Alegretto the strong implementer for hard logic once the subscription is live:
1. Set the `opencode_go` cell of `implementer` (and `repair-agent`, optionally `frontend-engineer` /
   `refactor-specialist`) in `roles.tsv` to the Kimi model id (e.g. `moonshot/kimi-alegretto` — confirm the real
   id with `opencode models`).
2. `./build.sh --check` → `--diff` → `--install`.

This satisfies the reviewer/implementer **family-exclusivity** invariant automatically: Kimi is a family distinct
from the review panel (`opus` on Claude, `gpt-5.6-sol` on Codex/go), so the generator's separation check passes
without forcing the implementer down a tier — which is exactly the constraint that caps the implementer today.
Precedent: the `zen` profile already routes implementer/repair/integrator/frontend/refactor to
`opencode/kimi-k2.7-code`. `package-planner` routes `high`-complexity packages to this strong tier via
`selected_model`; small/medium stay on the cheaper default.

## Codex reasoning effort (`codex_effort` column)
Only Codex has a per-agent reasoning-effort knob (`codex_effort` → `model_reasoning_effort`). It is tuned by
activity: **xhigh** for auditors and the judge (best of the best), **high** for coordination/root-cause/spec
and the frontend aesthetic gate, **medium** for implementation (which is audited afterward), **low** for
mechanical/script-gated roles. OpenCode and Claude Code have no effort field — there, the "effort" is expressed
by which model the role gets (Ollama for manual opt-in leaf work, GPT-5.6 Sol for Codex auditors).

Validation rejects duplicate roles, unknown capabilities, missing canonical prompts, invalid native formats,
and implementation-model reuse by an auditor or judge.
