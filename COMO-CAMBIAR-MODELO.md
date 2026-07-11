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
coordination and final judgment while keeping repetitive work on Go:
- **Code-writers** (`implementer`, `frontend-engineer`, `refactor-specialist`) → a cheap but code-specialized
  model, `kimi-k2.7-code` (`opencode-go/` in go-zen, `opencode/` in zen, `openai/gpt-5.4-mini` in local). The
  bet is still "build cheap, review strong": the `frontend-engineer` output gets a mandatory strong
  `ux-ui-designer` aesthetic review.
- **Mechanical/script-gated** (`gate-runner`, `github-release-manager`, `memory-scribe`, `app-runner`) → the
  cheapest tier, `deepseek-v4-flash` (`-free` in zen), since they don't write feature code.

`test-writer` stays above flash in go-zen (`deepseek-v4-pro`) because end-stage regressions need real
assertions. General/performance/blue-team review use `minimax-m3` in go-zen to avoid the GLM 5.1 latency and
Qwen Max budget spike; security, red-team, db audit, and the final judge use GPT-5.6 through OpenAI.

The three profiles differ in the hosted model column selected by `active-profile`: `go-zen` mixes OpenAI
subscription models with `opencode-go/*`, `zen` uses `opencode/*` routers, and `local` uses `openai/*` only.
Only OpenCode has a local-model column; `claude_model`/`codex_model` are profile-independent (hosted).

## Codex reasoning effort (`codex_effort` column)
Only Codex has a per-agent reasoning-effort knob (`codex_effort` → `model_reasoning_effort`). It is tuned by
activity: **xhigh** for auditors and the judge (best of the best), **high** for coordination/root-cause/spec
and the frontend aesthetic gate, **medium** for implementation (which is audited afterward), **low** for
mechanical/script-gated roles. OpenCode and Claude Code have no effort field — there, the "effort" is expressed
by which model the role gets (Ollama for manual opt-in leaf work, GPT-5.6 Sol for Codex auditors).

Validation rejects duplicate roles, unknown capabilities, missing canonical prompts, invalid native formats,
and implementation-model reuse by an auditor or judge.
