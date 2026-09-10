# 047 — Design handoff

> `product-analyst`, 2026-08-26. Written to satisfy ADR-0067 §4. **The architect owns the adapter's
> real shape, the runtime-enum decision, and the new ADR.** Every HOW below is UNVERIFIED. In
> particular, **no flag or subcommand of `agy`, `fx`, or `copilot` is asserted anywhere in this
> feature** — none has been measured (ADR-0026: `sin verificar`).

## Supersedes

| shipped clause | where it lives today | what 047 changes |
|---|---|---|
| The runtime set is four values, and a `selected_runtime` outside it is a parse failure | `ai/scripts/routing_core/usage.py:97` (`RUNTIMES = ("pi", "claude-code", "opencode", "codex")`), `ai/scripts/routing_core/domain.py:20` (`SELECTED_RUNTIMES`), rejection at `ai/scripts/set_agents_app.py:690` | **Conditional.** Only if architecture concludes a new lane must join the enums. Widening the set and widening the rejection are one decision that must land together. If the new lanes route under an existing runtime, 047 supersedes nothing. |

**Explicitly not superseded:**

- **ADR-0063.** Cursor stays a pin-host outside `RUNTIMES`. This feature does not make it a lane.
- **The Pi lane** (003 / 013). `pi` keeps its membership and its never-redirect-from behaviour
  (`ai/scripts/routing_core/service.py:50`, `_NEVER_REDIRECT_FROM_RUNTIMES`).
- **ADR-0030** `MODEL_STATIC_FALLBACK` — the curated fallback recorded on the spawn record
  (`ai/scripts/codex_spawn.py:9`) keeps its meaning for new lanes.
- **M-1** for the OpenCode `github-copilot` provider (`ai/scripts/routing_core/catalog.py:144-154`):
  authenticated credential, no verifying CLI id, no pair added. Reaffirmed.
- **ADR-0038** owns installing binaries (`set_agents_app.py:2135-2142`); `install_harness` applies the
  harness to an already-installed host and nothing more.
- **The four existing spawn CLIs** (`opencode_spawn.py`, `codex_spawn.py`, `claude_code_spawn.py`,
  `set_agents_spawn.py`) keep byte-identical behaviour; they are not retrofitted onto the new contract.

## Mother functions this feature enters

| entry | anchor | why it is the entry |
|---|---|---|
| `cmd_route_decide()` | `ai/scripts/set_agents_app.py:671` | Validates `selected_runtime` against the closed set and rejects with rc=2 at `:690`; any new lane's descriptor passes through here. |
| `RUNTIMES` | `ai/scripts/routing_core/usage.py:97` | The usage/quota axis's runtime vocabulary. |
| `SELECTED_RUNTIMES` | `ai/scripts/routing_core/domain.py:20` | The descriptor-side runtime vocabulary, read by the request validator at `domain.py:176`. |
| `_effective_runtime` / redirect loop | `ai/scripts/routing_core/service.py:50`, `:258-260` | Where a lane can or cannot be redirected away from; Pi's exemption lives here. |
| M-1 fail-closed precedent | `ai/scripts/routing_core/catalog.py:144-154` | The measured case that defines what `probe_models` is allowed to claim. |
| `install.sh --harness` | `ai/scripts/set_agents_app.py:3857`, `HARNESS_CHOICES` `:3767-3773` | The existing "apply the harness to a CLI" path `install_harness` should reuse rather than duplicate. |

## UNVERIFIED — architecture must resolve before implementation

1. **Adapter mechanism.** Protocol, ABC, or a registry of dicts; where it lives; and how "refused at
   registration" (AC-01) is enforced without a new import cycle
   (`provider_registry.py:10-16` documents why `routing_core` cannot be imported casually).
2. **Runtime-enum question.** Whether the new lanes join `RUNTIMES`/`SELECTED_RUNTIMES` or route under
   an existing runtime. This is the whole public-contract risk of the feature and decides whether the
   supersession above fires at all.
3. **Per-host reality.** Each host's real CLI id, model-listing command, and invocation shape for
   `agy`, `fx`, and `copilot`. **None measured.** Live measurement precedes any code; an invented flag
   is a defect, not a placeholder.
4. **Deferral token.** The exact spelling of `detected, spawn deferred` and where it is recorded so
   AC-05's written reason is durable rather than chat-only.
5. **Evidence layout.** Where AC-08's live evidence lands under
   `docs/specs/047-lanes-agy-fx-copilot/evidence/`, and how a skip names its reason in a way a gate can
   read.
6. **Ordering against 045 and 046.** 045 PKG-D must define the effort vocabulary and 046 must define
   the host states before `materialize(model, effort)` and the lane states can be implemented without
   inventing a second vocabulary. Architecture confirms the sequence.
