# 047 — Lanes: agy, fx, Copilot CLI

- **Estado:** Approved (Federico, 2026-08-26) — plan "Consola viva, instancia local y hosts adaptables".
- **Modo:** feature · risk signal `public-contract` + `multi-module`.
- **ADRs:** touches 0006/003 (runtime enums), 0030 (`MODEL_STATIC_FALLBACK`), 0043 (what a probe
  proves), 0063 (Cursor is not a runtime). Architecture owns the new ADR.
- **Depends on:** 046 (host rows and state vocabulary), 045 PKG-D (the effort axis `materialize`
  consumes).

## Problem

The harness has four runtimes and no way to add a fifth without hand-editing four places. `RUNTIMES`
(`ai/scripts/routing_core/usage.py:97`) and `SELECTED_RUNTIMES`
(`ai/scripts/routing_core/domain.py:20`) are closed enums; a `selected_runtime` outside the second one
is a parse failure with rc=2 in `cmd_route_decide` (`ai/scripts/set_agents_app.py:690`). Each existing
lane is its own spawn CLI (`opencode_spawn.py`, `codex_spawn.py`, `claude_code_spawn.py`,
`set_agents_spawn.py`) with no shared contract, so "add a lane" today means rediscovering, per lane,
what detection, model probing, materialization, and harness installation each mean.

Meanwhile there are installed hosts with no lane. Measured on this machine 2026-08-26 with
`command -v`: `agy` resolves at `~/.local/bin/agy`, `copilot` at `~/.local/bin/copilot`, and `fx` does
not resolve at all. 046 will show those as `sin lane`; this feature is what turns that state into a
lane, host by host, in a fixed order.

## Scope

1. **One adapter contract, four operations**, so a lane is a filled-in table and not an
   archaeology exercise:

   | operation | contract |
   |---|---|
   | `detect` | Does the host resolve on `PATH`? `PATH`-only, no network, no auth. The same primitive 046 uses, so the two never disagree. |
   | `probe_models` | The model list, **fail-closed**, keyed by a **verified CLI id**. If no CLI id verifies the host, the result is zero models and the host is `unlistable` (046) — never a guessed or remembered list. This is the M-1 rule (`ai/scripts/routing_core/catalog.py:144-154`) generalized. |
   | `materialize(model, effort)` | Turn a routing decision into the concrete invocation for this host. Consumes 045 PKG-D's effort vocabulary; defines no second one. Keeps the ADR-0030 curated-fallback behaviour recorded as `MODEL_STATIC_FALLBACK` (`ai/scripts/codex_spawn.py:9`). |
   | `install_harness` | Apply the harness (roles, doctrine, config) to this host. Installing the *binary* is not this operation's job — that stays ADR-0038's. |

2. **A fixed landing order, one host at a time:** `agy` first, then `fx`, then Copilot CLI. Each host
   lands, is verified, and is closed before the next starts.
3. **`fx` may close as `detected, spawn deferred` with a named reason.** If its model probe is unstable
   or it does not resolve on the machine under test, deferral with a written reason is a **passing**
   outcome — not a silent skip and not a fabricated lane. Declaring it satisfies the criterion.
4. **Suite green when the binaries are absent, live evidence when present.** Absence produces a
   documented skip that names the host and the reason; presence produces recorded live evidence of
   `detect`, `probe_models`, and one `materialize`.

## Non-goals

- **Pi is not reopened.** It is already a lane (`RUNTIMES` `usage.py:97`, `SELECTED_RUNTIMES`
  `domain.py:20`, never-redirect-from at `service.py:50`) and its behaviour is untouched.
- **Cursor is not reopened.** ADR-0063 keeps Cursor a pin-host outside `RUNTIMES`; this feature does
  not make it a lane.
- Installing the host binaries. ADR-0038 propose→approve owns that
  (`set_agents_app.py:2135-2142`).
- Lifting the `github-copilot` OpenCode-provider M-1 verdict (`routing_core/catalog.py:144-154`). The
  Copilot **CLI** lane is a different axis (046 AC-06).
- Retrofitting the existing four spawn CLIs onto the new adapter contract. New lanes use it; old lanes
  keep their behaviour byte-identical.
- Any effort vocabulary of its own (045 PKG-D owns it) or any host state token of its own (046 owns
  them).

## Criteria

- **AC-01** The adapter contract exists with all four operations named, and each new lane declares all
  four — a lane with an unimplemented operation is refused at registration, not discovered at spawn.
- **AC-02** `probe_models` with no verifying CLI id returns zero models and leaves the host
  `unlistable` (046); the router receives zero pairs for it. No model list is inferred from a
  credential, a name, or a previous run.
- **AC-03** `materialize(model, effort)` produces the invocation for an `agy` decision, using 045
  PKG-D's effort vocabulary, and records `MODEL_STATIC_FALLBACK` when the curated fallback is what
  actually ran (ADR-0030).
- **AC-04** `agy` lands first and is `vivo` on a machine where its binary resolves; the routing
  decision naming it is recorded and replayable.
- **AC-05** `fx` closes either as a working lane or as `detected, spawn deferred` **with a written
  reason naming the instability or the absence**. A bare skip fails this criterion.
- **AC-06** Copilot CLI lands last, and its host state is independent of the `github-copilot` OpenCode
  provider's M-1 verdict, which is unchanged.
- **AC-07** Pi's and Cursor's behaviour is byte-identical: `RUNTIMES` still contains `pi`, Cursor is
  still absent from it, and no Cursor pin path changes.
- **AC-08** With **none** of `agy`, `fx`, `copilot` on `PATH`, the full suite plus
  `./build.sh --check && ./ai/scripts/verify.sh` is green, and each absent host produces a skip that
  names the host and the reason. With a host present, live evidence of `detect`, `probe_models`, and
  one `materialize` is recorded under the feature's `evidence/`.
- **AC-09** No test weakened, skipped, or deleted; no existing spawn CLI's behaviour changed.

## Spec audit

Checked:

- **Universe named, separate from what is installed.** The universe is the three named hosts, declared
  in a fixed order, independent of what resolves on the test machine. `fx` is the live proof: absent
  here on 2026-08-26, and AC-05 still demands an outcome for it.
- **Absence-of-record behavior defined.** AC-08 defines the absent-binary outcome (green suite with a
  named skip) and AC-02 defines the absent-CLI-id outcome (zero models, `unlistable`) — both as
  outcomes, not as gaps.
- **Data source carries the signal.** `probe_models` is only allowed to claim what a verified CLI id
  returns, because the harness has already measured a case where a credential exists and no CLI id
  verifies it (`routing_core/catalog.py:144-154`). A source that omits a host cannot prove that host's
  models.
- **Fixture that would fool AC-02.** A stubbed probe returning `[]` is indistinguishable from a
  verified-empty catalog; the criterion is on the pair count *and* the `unlistable` state. A second
  fooling fixture is a probe whose CLI id was assumed from the host name — exactly the "id/name
  heuristic" the repo already rejected once (`provider_registry.py:99-100`).
- **Fixture that would fool AC-08.** A suite that skips whenever a binary is absent goes green on any
  machine and proves nothing; AC-08 additionally requires the skip to name the host and the reason,
  and requires live evidence when the binary *is* present — which on this machine means `agy` and
  `copilot` must produce live evidence, and only `fx` may take the absent path.
- **Pairwise conflicts.** (i) 047's `materialize` effort vs 045 PKG-D's effort vocabulary → 045 owns
  it, 047 consumes it, so there can never be two effort spellings. (ii) 047's lane states vs 046's
  vocabulary → 046 owns it, 047 only moves a host between existing states. (iii) The Copilot CLI lane
  vs the `github-copilot` provider M-1 → AC-06 declares them independent axes, so a live lane never
  implies a routable OpenCode pair. (iv) A new lane in `SELECTED_RUNTIMES` vs
  `cmd_route_decide`'s rc=2 rejection of unknown runtimes (`set_agents_app.py:690`) → widening the enum
  and the rejection are the same decision and must land together, or a descriptor naming the new lane
  fails while the lane exists.
- **Could not verify.** Whether the adapter contract is a Protocol, an ABC, or a registry of dicts;
  whether new lanes must join `RUNTIMES` / `SELECTED_RUNTIMES` at all or route under an existing
  runtime; each host's real CLI id and probe command (`agy`, `fx`, `copilot` — none measured yet, and
  **no invented flags**, ADR-0026); whether `install_harness` reuses `install.sh --harness`
  (`set_agents_app.py:3857`, `HARNESS_CHOICES` `:3767-3773`); the exact `detected, spawn deferred`
  token. All **UNVERIFIED** — architecture confirms against the real CLIs before any code.

## Supersedes

- **The four-runtime enumeration**, *if and only if* architecture concludes a new lane must join it:
  `RUNTIMES = ("pi", "claude-code", "opencode", "codex")` (`ai/scripts/routing_core/usage.py:97`) and
  `SELECTED_RUNTIMES` (`ai/scripts/routing_core/domain.py:20`), together with
  `cmd_route_decide`'s rc=2 rejection of any `selected_runtime` outside that set
  (`ai/scripts/set_agents_app.py:690`). This is the one public-contract supersession 047 may request,
  and it is UNVERIFIED until architecture decides; a lane that routes under an existing runtime
  supersedes nothing.
- Not superseded: **ADR-0063** (Cursor stays a pin-host outside `RUNTIMES`); the **Pi lane**
  (003/013, `_NEVER_REDIRECT_FROM_RUNTIMES` `routing_core/service.py:50`); **ADR-0030**
  `MODEL_STATIC_FALLBACK` (`ai/scripts/codex_spawn.py:9`); **M-1** for the `github-copilot` provider
  (`routing_core/catalog.py:144-154`); **ADR-0038** for installs; the four existing spawn CLIs.
