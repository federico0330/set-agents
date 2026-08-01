# Feature 015 — anthropic-dispatch-parity, contract 3.1.0

Status: `SPEC_DRAFT v4` — FINAL CORRECTION PASS after `SPEC_CHALLENGE` round 3 against contract 3.0.0
(`revision_required`, 3 blocking + 4 lower-severity findings, R3-01..R3-07; see `## Historial de challenge`
round 3 entry). Round 3's own reviewer stated explicitly this is the **final round needed** — *"converged
architecturally... a single short revision pass, not another design cycle... I would consider the contract
ready for user approval without a further adversarial round"* once these land — so this pass is the correction
described below, not a further rescope, and this file's intended verdict is `ready_for_user_approval`, pending
the user's own final sign-off. Round 3 found one genuine, live-verified **security gap one hop past R2-03's
fix** (R3-01: `--tools ""` alone gives zero protection against a project-scope `SessionStart`/`PreToolUse` hook
or a project-scope agent-file shadowing `--agent <role>` — the real mitigation is `--setting-sources user`), a
**factual correction to round 2's own live evidence** (R3-02: `"fable"` and `"opus"` are NOT the same canonical
model, contradicting round 2's own reported test result), a **new collision round 2's chosen fix would have
introduced** (R3-03: `"sonnet"` collides with `[areas.implement].claude`), and four lower-severity findings (a
missing calling-contract requirement for how a Bash-less review-class spawn receives the diff it reviews,
R3-04; a redirect-trigger granularity ambiguity, R3-05; a repeated site-count miscount, R3-06; and a
delivery-criterion/time-box propagation gap, R3-07) — all addressed below via two explicit user decisions
(quoted where they change requirements — see `## Contexto` §G-bis and AC-02's calling-contract sub-bullet) plus
fresh live verification performed this session (2026-07-31): a real re-read of `models.toml`, `routes.v1.toml`,
`service.py`, `generate.py`, and `catalog.py` against current line numbers, a real `claude --help` re-read
confirming `--setting-sources`/`--bare`/`--safe-mode`'s exact documented wording, and a real `git rev-parse
--show-toplevel` confirming the cwd write-containment boundary genuinely excludes `~/.claude/**`. See
`## Historial de challenge` for the round-1, round-2, and round-3 records and how each finding disposes.

**Round-2 correction pass, kept below as accurate history of how contract 3.0.0 came to be** — CORRECTION PASS
after `SPEC_CHALLENGE` round 2 against contract 2.0.0
(`revision_required`, 4 blocking + 9 lower-severity findings, R2-01..R2-13; see `## Historial de challenge`
round 2 entry). This is a correction pass on the round-1 redesign, not a further rescope: the cross-lane
Claude-Code-redirect architecture itself is unchanged and re-confirmed (round 2's own "independently verified
as claimed" table). Round 2 found one genuine, live-verified **security gap** (R2-03: a headless `claude
--print --agent <code-rw-role>` spawn executed an arbitrary Bash command with `permission_denials: []`,
because the `PreToolUse` guard-hook path that is supposed to gate Bash falls through to ALLOW in headless mode,
where no human exists to answer the interactive prompt it would otherwise raise), a lifecycle/bookkeeping
impossibility (R2-02), a wrong site-count and an unguaranteed Non-goal (R2-05), a self-contradicting evidence
transcript (R2-07), a new same-model collision this very redesign introduces (R2-04), and eight further
citation/precision findings — all addressed below via four explicit user decisions (quoted where they change
requirements) plus fresh live verification performed this session (2026-07-31): a real `claude --help` re-read,
five additional live `claude --print` subprocess reproductions targeting exactly the mechanisms round 2
flagged (the `--tools`/prompt-delivery argv hazard, whether a CLI-level tool ceiling actually holds against a
code-rw role in headless mode, and whether a bounded write capability can be granted safely at the CLI level —
see `## Contexto` §H), and a full re-read of every cited line in `service.py`, `domain.py`, `catalog.py`,
`set_agents_spawn.py`, `models.toml`, `routes.v1.toml`, and `tests/test_harness.py` against their current,
live content (several citations had drifted or were simply wrong; each correction is called out inline). See
`## Historial de challenge` for both the round-1 and round-2 records and how each finding disposes.

Depends, non-blockingly, on `008-dynamic-selection`'s P1 (`accepted`) and on `004-adaptive-dispatch`'s ADR-0007
Pi-lane spawner pattern (`accepted`, reused almost verbatim below — see `## Contexto` §C). **Sibling, not
amendment, of `014-model-preference-policy`** (in progress, untouched by this file, read-only reference only
per this contract's own process constraints). No other feature's approved contract is edited by this file.

## Origen

The user runs two ~$100/month subscriptions today (Anthropic/Claude, OpenAI/GPT). **In roughly twelve days**
the OpenAI/GPT subscription is dropped (replaced by Kimi Code, $40/month, unrelated to this contract — see
Non-goals).

**Round-2 correction (R2-01), stated precisely and honestly:** this contract is a **time-boxed** fix, not a
permanent one, and its expiry date is known and certain, not hypothetical. Once the OpenAI/GPT subscription
drops, `anthropic` becomes the **sole enabled-and-authenticated provider** (`[routing].enabled_providers =
["openai-codex", "anthropic"]`, `models.toml:44`, minus one). `REVIEW_PROVIDER_CONFLICT`
(`service.py:166`) then excludes `anthropic` from serving as a reviewer's provider on **every** decision whose
writer also resolved to `anthropic` (whether via this contract's `claude-code` redirect or any other route) —
there is no remaining second provider to pick a reviewer from, so `REVIEWER_INDEPENDENCE_UNAVAILABLE` fires
and doctrine halts, permanently, from day 13 onward, **for exactly the same structural reason it fires today
before this contract's fix lands** (§D), just with the roles reversed: today the gap is "the working
credential is on the wrong lane"; from day 13 it is "there is genuinely only one provider left, on any lane."
This contract delivers real, working review-independence for the **~12-day window while two providers remain
authenticated** (`openai-codex` and, via this contract's redirect, `anthropic`) — from day 13, automatic
reviews correctly pause (a human reviews manually) until a real second provider exists (Kimi or otherwise), a
**different, future, not-yet-scoped feature**, not this contract's job. This is a **known, accepted, documented
limitation**, not a defect this contract silently leaves behind — see Non-goals.

**The invalidating fact (verbatim from the user, this session):** *"Anthropic en opencode solo podes logearte
por API Key (no por Oauth). Asi que no hay modelos disponibles de anthropic en opencode."* OpenCode's own
credential store can only be authenticated against Anthropic with a metered API key — never against the user's
real $100/month subscription via OAuth. Contract 1.0.0's entire design (AC-01: build OpenCode-lane
Anthropic-backed `<role>@<tier>` variant files, spawned by the OpenCode CLI the same way `openai-codex`
variants are) assumed that once *some* operator authenticates OpenCode against Anthropic, those variants
become spawnable. That assumption is now known to be categorically wrong: the only way to make it true is to
take on a brand-new, unapproved, **per-token metered cost** on top of a subscription the user already pays
for and does not want to pay twice for. The user was asked how to proceed and chose explicitly: **redirect
delegation to Claude Code when a routed decision resolves to `anthropic`, instead of trying to make OpenCode
itself spawn Anthropic-backed agents.** Reasoning: Claude Code already authenticates against Anthropic via
OAuth against the user's real subscription — this very orchestrator session is running as Claude Code, right
now, using exactly that OAuth path — reusing it costs nothing new.

This redesign investigates, with live evidence, what that redirect concretely requires, and finds the
required change is **smaller and more surgical than contract 1.0.0's**, not larger: no new artifact files, no
new provider onboarding, and a narrowly-scoped, well-isolated change to one routing-service code path — see
`## Contexto` for the full trail.

## Contexto

### A. Two independent model-selection mechanisms exist today; this contract touches only one of them (unchanged from 1.0.0, re-verified)

`RoutingService.route()` (`ai/scripts/routing_core/service.py:104-224`) is the harness's one **per-decision,
credential-aware, dynamic** selector, invoked via `--route-decide` (`ai/scripts/set_agents_app.py:385-453`).
`models_config.py`'s `resolve_role`/`[areas.<duty>]` (`models_config.py:238-264`, governed by Accepted
`ADR-0003`) is a **separate, static, install-time-baked default**, consumed by `generate.py`'s `load_roles`
to bake one fixed `model:` line into every generated BASE (non-tiered) agent file. This contract's fix lives
on the **dynamic** side plus the doctrine that consumes its output, and makes one narrow, named, values-only
edit to the **static** side (AC-06, the `go-zen` duplicate — see §F).

### B. `anthropic` is already fully curated at the catalog layer; nothing new is onboarded there (re-verified, and now proven MORE general than 1.0.0 assumed)

- `routes.v1.toml` already carries three `provider = "anthropic"` rows, one per tier: `model = "haiku"` @
  `fast`, `model = "sonnet"` @ `balanced`, `model = "opus"` @ `frontier`, all six roles-eligible.
- `_PAIR_COMMANDS` (`ai/scripts/routing_core/catalog.py:133-140`) already audits **three** separate
  `(runtime, provider)` pairs for `anthropic`: `("opencode", "anthropic")`, `("claude-code", "anthropic")`,
  and `("pi", "anthropic")` — not just the OpenCode one contract 1.0.0 focused on.
- **New finding this session, load-bearing for the whole redesign:** `build_snapshot`
  (`ai/scripts/routing_core/catalog.py:503-568`) already computes each route's set of valid `identity` tuples
  as `frozenset((r.route_id, runtime, r.provider, r.model, r.family, r.effort) for r in routes for runtime in
  (route_runtimes[r.route_id] or audited.get(r.provider, set())))` (`catalog.py:565-567`) — i.e., for any
  route whose optional `runtimes` catalog key is absent (true of all three anthropic rows today, confirmed by
  reading `ai/catalogs/routes.v1.toml`'s anthropic rows directly), the identity is valid under **every runtime
  `_PAIR_COMMANDS` audits for that provider** — `opencode`, `claude-code`, AND `pi`, simultaneously, already,
  with zero catalog change. `Snapshot.identity_allowed` (`domain.py:156`) already accepts
  `(route_id, "claude-code", "anthropic", "haiku", ..., ...)` as a valid identity, right now, on this exact
  tree. **The catalog/snapshot layer was never the gap.** This corrects contract 1.0.0's own premise that new
  tier-variant catalog coherence work was needed (its AC-01) — it was not.

### C. Claude Code has a real, non-interactive, subprocess-invocable spawn mechanism — live-proven, not assumed

No existing Python code in this repo invokes the `claude` binary to spawn an agent — grep-verified
(`grep -rn "claude" ai/scripts/routing_core/*.py ai/scripts/*.py`) confirms the only two existing uses of
`claude` as a subprocess are (1) `_parse_claude_auth`/`("claude-code","anthropic")`'s probe,
`catalog.py:135,190-193,410-411` (`claude auth status --json`, reads `loggedIn` only), and (2) `generate.py`'s
`claude_tools`/`frontmatter_hook`/hook-script copies, none of which spawn anything. **This is genuinely new
integration work, not an extension of an existing invocation pattern** — stated plainly, per the assignment's
own instruction not to assume otherwise.

It is, however, a close structural match for the **already-accepted** ADR-0007 Pi-lane pattern
(`ai/scripts/set_agents_spawn.py`), which exists for exactly the same underlying reason: pi has no in-process
delegation of its own, so a real CLI subprocess spawns it (`--print --mode json --no-session --no-extensions
--tools <allowlist> --append-system-prompt <role.md> <task>`), wired through the shared
`--route-decide -> --route-dispatched -> spawn -> --route-terminal` lifecycle (`set_agents_spawn.py:324-442`).
OpenCode/Codex never need this because their own orchestrator, running natively inside that CLI, spawns
children via that CLI's own in-process Task/delegation tool — `set_agents_app.py` never subprocess-spawns
OpenCode/Codex children (grep-verified: no `subprocess.run(["opencode", ...])`/`["codex", ...]` spawn call
exists anywhere in this repo). The cross-lane case this contract needs — an orchestrator hosted under
**one** CLI (OpenCode, `[runtime].primary`, unchanged) needing to spawn a child under a **different** CLI
(Claude Code) — has no in-process mechanism available (OpenCode's Task tool cannot spawn a Claude-Code-hosted
child); it needs the same kind of real subprocess spawn pi already required, for the same structural reason.

**Live-verified this session** (real `claude` binary present at `~/.local/bin/claude`, real invocations run,
redacted below):

1. `claude auth status --json` → `{"loggedIn": true, "authMethod": "claude.ai", "subscriptionType": "max", ...}`
   — **confirms `("claude-code","anthropic")`'s probe already correctly detects the real OAuth subscription**,
   independent of OpenCode's API-key-only limitation, exactly as `_parse_claude_auth` (`catalog.py:190-193`)
   is built to read (`loggedIn is True`).
2. `claude --print --model haiku --output-format json --no-session-persistence "..."` → succeeded, returned a
   single JSON object (not a JSONL event stream, unlike pi) with `modelUsage: {"claude-haiku-4-5-...": {...,
   "canonicalModel": "claude-haiku-4-5", ...}}`, `total_cost_usd`, `session_id`, `result`, `is_error: false`,
   `stop_reason`. **`--print` is Claude Code's real, documented, non-interactive/headless mode** (`claude
   --help`: `"starts an interactive session by default, use -p/--print for non-interactive output"`), directly
   analogous to pi's `--print --mode json`.
3. `claude --print --agent implementer --model haiku --output-format json --no-session-persistence "Ignore
   your normal role..."` → the model **refused** to abandon its role, replying "I'm the IMPLEMENTER in this
   workflow, and the system instructions define my duties clearly" — **live proof `--agent <role>` loads the
   real, already-generated `~/.claude/agents/<role>.md` file** (confirmed present at that exact path,
   `TARGETS["claude-code"] = home / ".claude"`, `install.py:31`, and `generate.py:362-364` writes
   `Global/claude-code/agents/<role>.md` which install copies there) — AND `modelUsage` in the response showed
   `claude-haiku-4-5-...` was the model actually used, **proving the top-level `--model` flag overrides the
   agent file's own `model:` frontmatter default** (`~/.claude/agents/implementer.md:5` is `model: sonnet`,
   baked from `[areas.implement].claude = "sonnet"`, `models.toml:81`; the spawn ran on haiku anyway).
4. `claude --print --model bogus-model-xyz --output-format json --no-session-persistence "hi"` → exit code 1,
   `is_error: true`, `api_error_status: 404`, `total_cost_usd: 0`, `modelUsage: {}` — **a clean, fast-failing,
   machine-readable crash/mismatch signal**, structurally equivalent to what `set_agents_spawn.spawn()`
   already checks for pi (`proc.returncode != 0`, `model_fallback`/`observed != target_id` detection via
   `last_assistant.get("provider")/.get("model")` — here the equivalent signal is `modelUsage`'s key set,
   `is_error`, and `api_error_status`).

**What this proves, precisely:** the Claude-Code-lane cross-process spawn this contract needs can reuse
`set_agents_spawn.py`'s **entire lifecycle skeleton** (`route_and_spawn`'s decide→dispatch→spawn→terminal
loop, its crash-never-leaves-a-run-open discipline, its usage/quota plumbing) almost unchanged, swapping only
the innermost `spawn()` primitive's argv/parse logic for the `claude` CLI's own flags and single-JSON-object
output shape — **and it needs no new tier-variant FILES at all**, because `--agent <role> --model <alias>`
already reuses the existing, already-generated `.claude/agents/<role>.md` BASE file with a spawn-time model
override, a mechanism OpenCode's convention does not have and does not need to be imitated by.

### D. The routing-service gap is one specific, narrow code path — not the candidate-selection algorithm

`RoutingService.route()`'s exclusion loop (`service.py:134-169` — corrected this round, R2-13: `needs_context`
at `:134` is computed immediately before the loop and is read inside it at `CONTEXT_MISSING`, `:148`, so it is
part of the loop's own input surface, not a separate preceding statement) builds, per candidate route,
`identity = (route.route_id, facts.selected_runtime, route.provider, route.model, route.family, route.effort)`
(`service.py:137`) and gates authentication with `route.model not in self.inventory.get((facts.selected_runtime,
route.provider), frozenset())` (`service.py:145`) — **using the single, caller-supplied `facts.selected_runtime`
for every candidate, regardless of that candidate's own provider.** `cmd_route_decide`
(`set_agents_app.py:393`) defaults an absent descriptor field to `runtime = doc.get("selected_runtime",
"opencode")`, and the orchestrator doctrine's own descriptor (`Global/_canonical/agents/orchestrator.md:167-168`)
never names `selected_runtime` at all — so every tiered decision today is evaluated with `facts.selected_runtime
== "opencode"`, unconditionally, for both writer and review roles.

Combined with the live, re-confirmed fact that OpenCode's own credential store has zero Anthropic entries on
this machine (`opencode auth list --pure`, four credentials, none `Anthropic`; `opencode models anthropic
--pure` → `Error: Provider not found: anthropic`) — and now understood, per `## Origen`, to be **permanently**
true unless the user takes on new metered cost, not merely "not yet done" — every `anthropic` candidate is
excluded via `PROVIDER_UNAUTHENTICATED` (`service.py:145`) for **every** decision computed today, writer or
review, because the auth check consults `("opencode","anthropic")` no matter what. §B already showed the
catalog snapshot **allows** the `("claude-code","anthropic")` identity; §C showed Claude Code can actually
**spawn** it. The one remaining gap is that `service.py:137,144,145,195,200,201,206,208` — **this list is the
complete, correct enumeration of every `facts.selected_runtime`-keyed site in the exclusion loop and its
post-selection re-check** (corrected this round, R3-06: round 2's own prose miscounted its own already-complete
eight-entry list as "six sites, not five" — the list itself was right, the count word describing it was wrong,
the second miscount in a row; re-verified live this session by grepping every `facts.selected_runtime`
occurrence in `service.py`, confirming exactly these eight and no others). `service.py:128`'s
`request.selected_runtime not in (None, facts.selected_runtime)` conflict check also reads `facts.selected_runtime`,
but is deliberately excluded from this list — it governs a disjoint concern (whether the caller's requested
lane conflicts with the resolved one, unrelated to provider-inventory lookup) that AC-01 leaves untouched, see
AC-01's own text. Line 144 is a pi-specific simulation-mode guard, unrelated to provider inventory lookup —
AC-01 does not need to change its behavior, but it must be counted, since the Non-goals bullet that promises
"only these sites change" is inaccurate, not just incomplete, if it is silently dropped.

**Empirically proven this session** (not reasoned about — executed against the real `RoutingService` code via
its own hermetic test seam, `routing._compose_for_tests`, with an inventory shaped exactly like this
machine's live probe result — `{("opencode","openai-codex"): {...}, ("codex","openai-codex"): {...},
("claude-code","anthropic"): {"haiku","sonnet","opus","fable"}}`, no `("opencode","anthropic")` key at all):

1. **Today, pre-fix, real code, real credential shape:** a writer (`implementer`, `selected_runtime="opencode"`)
   correctly authorizes on `openai-codex`. A **verified** reviewer decision for the same package
   (`review_of_run_id` pointing at that writer's real `terminal_success` run, `selected_runtime="opencode"`,
   unchanged from what the doctrine sends today) resolves to `RouteDecision(reason_codes=
   ('REVIEWER_INDEPENDENCE_UNAVAILABLE',), execution_enabled=False, ...)` — a **hard denial** (doctrine branch
   3c: HALT, raise `HUMAN_DECISION_REQUIRED`). This is a materially more precise, and different, finding than
   contract 1.0.0's Contexto §7 walked through: 1.0.0 traced a hypothetical where an `anthropic` candidate
   reached `ok=true, execution_enabled=false` and warned the doctrine's branching was ambiguous for that shape;
   that trace implicitly assumed `("opencode","anthropic")` was authenticated (it is, in `tests/test_routing.py`'s
   own default fixture, `setUp`, line 148 — a reasonable idealized test default, not this machine's reality).
   On this real machine, the anthropic candidate never reaches that ambiguous `ok=true` shape at all today — it
   is hard-excluded earlier, by `PROVIDER_UNAUTHENTICATED`, leaving zero candidates and
   `REVIEWER_INDEPENDENCE_UNAVAILABLE`. **The corrected finding: today, on this machine, every package review
   following an `openai-codex` writer already halts, loudly, requiring a human — not a silent
   same-provider-reviewer substitution.** Severe (it blocks throughput on every single review, today), but a
   fail-closed severity, not a fail-open one — the framing must say so precisely.
2. **Post-fix (simulated by resolving the review candidate set's effective runtime to `claude-code` for the
   `anthropic` route, the exact net effect AC-01 below implements):** the same writer/review pair now resolves
   to `RouteDecision(route_id=..., runtime='claude-code', provider='anthropic', model='sonnet',
   execution_enabled=False, reason_codes=(), independence_verified=True, fallback_identity=(...,'claude-code',
   'anthropic','opus',...))`. `REVIEW_PROVIDER_CONFLICT`/`REVIEW_FAMILY_CONFLICT` still correctly exclude every
   `openai-codex` candidate (visible in the run's own exclusion list). This is exactly the shape AC-04's new
   doctrine branch must recognize and route to a real Claude-Code-lane spawn.

**R2-13 correction (citation and reading):** the sort key at `service.py:171`,
`candidates.sort(key=lambda x: ((x[0].provider == writer.provider) if writer else False, TIER_ORDER[x[0].tier],
x[0].curated_priority, x[0].route_id))`, has a first element that reads as an active "different-provider
preference" but is actually **dead for every review decision specifically**: `REVIEW_PROVIDER_CONFLICT`
(`service.py:166`) already hard-excludes, earlier in the same loop, every candidate whose `route.provider ==
writer.provider` — so by the time `candidates.sort` runs, no surviving candidate can ever make that first sort
key element `True` when `writer` is not `None`. It is unreachable, not "a soft preference layered on top of the
hard exclusion" as prior wording implied; this file states it precisely rather than describing an active
preference that cannot actually fire for review decisions (it remains dead-but-harmless code, not a bug — a
future change that legitimately widens `REVIEW_PROVIDER_CONFLICT`'s exclusion condition would need to
re-examine whether this key becomes reachable again).

### E. ADR-0011 D3/D4 — this contract does not relax the halt rule; it fixes what was wrongly triggering it

Accepted `docs/adr/0011-uninterrupted-delegation.md` D4 (`:141-145`) states the boundary precisely: **"a
`--route-decide` decision returning `REVIEWER_INDEPENDENCE_UNAVAILABLE` halts, in every runtime, unchanged.
... Making a *routed* reviewer degrade instead of halt is a routing-service change, deferred to `008-P1b` /
`008-P2`"** — packages round 1 already flagged as not existing on disk. **This contract does not implement
that deferral, and does not touch D4's halt rule at all.** §D's empirical proof shows the mechanism at work:
`REVIEWER_INDEPENDENCE_UNAVAILABLE` was firing **incorrectly**, today, because the auth check consulted the
wrong runtime lane for a provider that *is* authenticated, just not on the lane asked. AC-01 fixes that
credential-routing bug; it does not weaken what counts as independent, and does not make a same-provider
review acceptable where it wasn't before. If a future state genuinely has no independent, spawnable candidate
on *any* reachable lane — **the certain, scheduled, non-hypothetical day-13 case named in `## Origen`: the
OpenAI/GPT subscription drops, `openai-codex` leaves `[routing].enabled_providers`, and `anthropic` (reached via
this contract's `claude-code` redirect, OAuth session unaffected) is the only provider left, so no candidate on
any lane can ever satisfy independence again** (round-2 correction, R2-01: this is not "Claude Code's own OAuth
session also somehow becomes unavailable" — that framing was wrong; Claude Code's OAuth session is expected to
keep working exactly as it does today, the cause is that the *second provider* is gone, not that the redirect
lane itself fails) — `REVIEWER_INDEPENDENCE_UNAVAILABLE` still fires and still halts, exactly as D4 requires —
AC-04 below states this invariant as a test, not just prose, against precisely this day-13 shape (R2-12, see
AC-04(b)). D3 (same-provider-review tolerance for **non-tiered**
delegation, `ADR-0011:79-121`) is untouched; it governs a disjoint mechanism (`docs/adr/0011...:142-143`
explicitly scopes D3 to "delegation that carries no routing decision").

### F. `_opencode_projected_route`'s "anthropic runs through claude-code, not OpenCode" docstring was right all along — no amendment needed (reverses contract 1.0.0's Contexto §4)

`generate.py:450-460`'s docstring: *"the only routes.v1.toml provider reachable from the OpenCode lane
(anthropic runs through claude-code, not OpenCode)"* — contract 1.0.0 read this as a documented assumption
this contract must formally **amend**, because 1.0.0 planned to add OpenCode-lane Anthropic tier-variant
files, contradicting it. This redesign adds **no OpenCode-lane Anthropic artifacts of any kind** — the
redirect happens entirely at the routing-service auth-check layer (§D) and the Claude-Code spawn layer (§C),
never by creating a `<role>@<tier>` OpenCode file for `anthropic`. **The docstring's assumption is therefore
correct under this design and is left exactly as it is** — `check_variant_catalog_coherence`
(`generate.py:472-494`) and `models_config.load_role_tiers`'s tier schema (`models_config.py:308-350`,
`set(table) != {"opencode"}` at `:340`) are **untouched**: no new field, no new provider axis, no new
per-tier file convention for Claude Code. This is a real, evidence-driven reversal of 1.0.0's own planned
AC-01, stated plainly rather than silently dropped.

### G. `go-zen` static-config duplicate (user-confirmed, independent of this redesign, kept in scope)

Live-read (`models.toml:96` vs `models.toml:188`): `[areas.audit].opencode."go-zen"` and
`[roles.implementer.tiers.balanced].opencode."go-zen"` are both, literally, `"openai/gpt-5.6-sol"` — an exact
same-provider **and** same-model collision on the `go-zen` OpenCode profile, between the static base-audit
default (`ADR-0003`) and the dynamic implementer-balanced tier ladder (`004`/`008`). This is a values-only
`models.toml` edit (AC-06), independent of the routing-service/spawn-layer redesign above, kept in scope per
the user's explicit, separately-confirmed instruction.

### G-bis. A second, NEW same-model collision this redesign itself introduces on the `.claude` axis (R2-04, user decision 3; FULLY resolved round 3, user decision 1 — see below)

Live-read this session: `[areas.audit].claude` (`models.toml:93`) and `[areas.judge].claude` (`models.toml:99`)
are both, literally, `"opus"`; the anthropic frontier-tier route is also `model = "opus"`
(`routes.v1.toml:57-58`). Contract 2.0.0 did not see this as a problem because the `claude-code` lane was never
a real dispatch target before this contract; once AC-01/AC-02 make it real, a **frontier-tier writer** whose
tiered decision redirects to `anthropic`/`opus` via `claude-code` (AC-01) can be paired, on an *unverified*
review (`REVIEW_IDENTITY_UNVERIFIED`, no `review_of_run_id` offered — the same static/dynamic split named in §A
and AC-05), with a **BASE** (non-routed) `audit`/`judge` reviewer whose static `.claude` default is *also*
`opus` — same provider, same model, `ADR-0011` D3's "not accepted while an alternative exists" bar. This is a
pure **static-config-value** collision (comparing two `models.toml` table values plus `routes.v1.toml`'s
curated set, never touching `RoutingService` at runtime — same mechanism class as the `go-zen` collision in
§G, not the dynamic hard-exclusion machinery in §D, which never even sees the static `[areas.*]` defaults).

**Round-2 fix, and why it is superseded, not merely refined, in round 3.** Contract 2.0.0/round 2 changed
`[areas.audit].claude`/`[areas.judge].claude` from `"opus"` to `"sonnet"` (AC-06(b)) on the strength of a live
test that round reported as showing `claude --print --model fable ...` and `claude --print --model opus ...`,
run back to back, both resolving to the identical `modelUsage.canonicalModel: "claude-opus-5"` — round 2 read
this as proof `fable` could never be used as a genuine fourth, collision-free value, settled for `"sonnet"`
instead, and named a smaller balanced-tier residual (the new `"sonnet"` default still colliding with a
balanced-tier writer redirected to `anthropic`/`sonnet`) as an accepted, not-fully-eliminated gap.

**Round 3 re-reproduced this exact test live this session and found round 2's reported result WRONG.**
`claude --print --model fable --output-format json --no-session-persistence "..."` and the identical call with
`--model opus`, run back to back, resolved to genuinely DIFFERENT canonical models: `fable` →
`modelUsage.canonicalModel: "claude-fable-5"`; `opus` → `modelUsage.canonicalModel: "claude-opus-5"`. This is
corroborated independently by `claude --help`'s own `--model` flag documentation, re-read this round: *"Provide
an alias for the latest model (e.g. 'fable', 'opus', or 'sonnet') or a model's full name (e.g.
'claude-fable-5')"* — the help text's own worked example pairs the `fable` alias specifically with the
`claude-fable-5` full name, not `claude-opus-5`. `catalog.py`'s own curated `_ANTHROPIC_CANONICAL_EXTRA =
{"fable": "claude-fable-5"}` (`catalog.py:86`) is therefore CORRECT, not stale — round 2's claim that it needed
a future quickfix was itself the error, not the curation; AC-07 below states this plainly so a future reader
does not chase a phantom `catalog.py` bug.

**Consequence: `"fable"` collides with NOTHING.** Checked exhaustively this session against every real
`models.toml`/`routes.v1.toml` value (`grep -n 'claude = ' models.toml`: every `[areas.*].claude`/
`[roles.*].claude` value on this tree today is one of `{"sonnet", "haiku", "opus"}`, never `"fable"`; the three
curated `routes.v1.toml` anthropic rows are `{haiku, sonnet, opus}`, `## Contexto` §B) — `"fable"` collides with
none of: (1) the three curated anthropic route models (`haiku`@fast, `sonnet`@balanced, `opus`@frontier), (2)
`[areas.implement].claude` (`models.toml:81`, also `"sonnet"` — the collision `"sonnet"` as AC-06(b)'s value
would have silently introduced against the BASE implementer default, newly found this round, R3-03), or (3) any
other `[areas.*].claude`/`[roles.*].claude` value on this tree.

**User decision 1, this round: use `"fable"`, not `"sonnet"`, for `[areas.audit].claude`/`[areas.judge].claude`
(AC-06(b), below).** This eliminates all three collision residuals in one edit — the original frontier-tier
`opus`/`opus` collision this section names, round 2's own balanced-tier `sonnet`/`sonnet` residual (AC-05,
withdrawn below), and R3-03's newly-found BASE-implementer `sonnet`/`sonnet` collision the `"sonnet"` fix would
otherwise have introduced — with ZERO residual left to document as "accepted." **Full elimination WAS achieved
this round; the prior "structurally impossible to fully eliminate" claim (round 2) is retracted, not merely
revised.**

### H. Decisions 1 and 4, reconciled with fresh live evidence (R2-03/R2-06/R2-07) — the CLI-level tool ceiling is real, and a bounded write capability IS achievable, at a precisely narrower scope than "full code-rw"

Round 2 live-proved a genuine security gap (R2-03): a headless `claude --print --agent <code-rw-role>` spawn
executed an arbitrary Bash command with `permission_denials: []` — no interactive human exists in `--print`
mode to answer the permission prompt the same tool call would raise in an interactive session, and the
`PreToolUse` guard-hook path that is supposed to gate Bash for hooked roles falls through to ALLOW rather than
DENY when nothing answers it. **User decision 1: mirror the pi-lane's already-accepted strict posture** —
`set_agents_spawn.py`'s `route_and_spawn` (the ONLY routed/CLI entry point) hardcodes `GUARD_TOOLS_READONLY`
and has **no `guard_tools` parameter at all** (`set_agents_spawn.py:70,332-335`: *"this, the routed lifecycle
entry point, ALWAYS spawns with `GUARD_TOOLS_READONLY` — there is deliberately no `guard_tools` parameter
here... so a code-rw child is never reachable through this function"*, SEC-A02 repair precedent) — so AC-02's
Claude-Code spawn CLI integration must enforce a **CLI-level** (never frontmatter-level) read-only tool ceiling
for the routed/dispatch entry point, as a DECIDED requirement, not an `[UNVERIFIED for architecture]` tag.

**Live re-verification this session (2026-07-31), against the real `claude` binary (`claude --version` →
`2.1.220`), specifically to resolve R2-03/R2-06/R2-07 with evidence rather than assertion:**

1. **`claude --help`, re-read in full.** Two real, independent flags exist: `--tools <tools...>` ("Specify the
   list of available tools from the built-in set. Use `""` to disable all tools, `"default"` to use all tools,
   or specify tool names, e.g. `"Bash,Edit,Read"`") and `--permission-mode <mode>` (choices: `acceptEdits`,
   `auto`, `bypassPermissions`, `manual`, `dontAsk`, `plan`). A third, `--allowedTools`/`--allowed-tools
   <tools...>`, grants fine-grained *patterns* within an already-available tool (e.g. `"Bash(git *)"`) — a
   different, narrower axis than `--tools`, and not needed once `--tools` excludes Bash outright (below).
2. **R2-07's contradiction, reconciled — the ACTUAL validated argv delivers the prompt via stdin, never
   positional.** Reproduced round 2's own finding live: `claude --print --model haiku --output-format json
   --no-session-persistence --tools "" "say PONG"` → `Error: Input must be provided either through stdin or as
   a prompt argument when using --print` — `--tools` is variadic and, when it is the last flag before a bare
   positional, swallows that positional into its own token list, exactly as round 2 found. Placing `--tools`
   immediately before another single-value flag (not the prompt) avoids this for that one case, but is
   fragile and ordering-dependent. **The robust, order-independent fix, live-confirmed:** deliver the task via
   **stdin**, never as a trailing positional — `echo "<task>" | claude --print --model haiku --output-format
   json --no-session-persistence --tools "Read,Grep,Glob"` succeeded cleanly regardless of where `--tools`
   fell in the argv. AC-02 codifies stdin delivery as the mechanism, not the positional form `## Contexto` §C's
   original transcript implied; that transcript's own calls (item 2/3/4) used positional prompts *without*
   `--tools`, which is why they never hit this hazard — they were not, in fact, the same shape as AC-02's own
   `--tools ""` claim, which is exactly R2-07's contradiction. Both statements are now reconciled to the one
   real, tested shape.
3. **The CLI-level read-only ceiling is real and holds against a code-rw role, live-proven.** Spawned
   `--agent implementer` (capability `code-rw`, frontmatter `tools: Read, Grep, Glob, Edit, Write, Bash`,
   `generate.py:255`, and — confirmed by direct read of the installed file — **no `hooks:` block at all**,
   since `frontmatter_hook(capability="code-rw")` is outside the hooked-capability set, `generate.py:267-279`)
   with `--tools "Read,Grep,Glob"` and asked it, via stdin, to run a Bash command writing a marker file. Result:
   no file created, `permission_denials: []` (nothing to deny — the tool plainly does not exist in the
   session), and the model's own reply: *"Looking at my actual available tools, I only have Read, Grep, and
   Glob. There is no Bash execution tool in my current toolset."* This is a structurally different, and
   stronger, guarantee than a hook: the tool is **absent from the session**, not merely gated by a policy that
   can fail open.
4. **A genuine, SAFE, bounded write capability at the CLI level exists — resolving decision 4's question with
   evidence, not assumption.** `--tools "Read,Grep,Glob,Edit,Write"` (Bash deliberately excluded) alone was
   *not* sufficient — a Write attempt was denied (`permission_denials` populated, file not created) absent an
   explicit permission grant, confirming Edit/Write go through Claude Code's own native, structurally-scoped
   permission path (file-path-bounded, not shell-arbitrary), which — unlike the Bash guard-hook path — defaults
   to DENY, not ALLOW, in headless mode when nothing answers it. Adding `--permission-mode acceptEdits`
   resolved this: the identical Write call then succeeded, `permission_denials: []`, file created with the
   exact requested content. **`--permission-mode plan` was also tested and found to BREAK headless execution**
   (`subtype: "error_during_execution"`, `terminal_reason: "aborted_streaming"`, the instant any tool is
   invoked) — it is an interactive-review mode with no headless exit path, and must NOT be used for this
   mechanism; this is named so a future implementer does not reach for it as an apparently-safer default.

**The critical reconciliation (decisions 1 + 4), stated plainly:** decision 1's CLI-level read-only ceiling
does **not** block code-rw roles from being safely dispatched via this mechanism — but it forces a
**precisely narrower** capability than the roster's normal `code-rw` definition (`Edit, Write, Bash`,
`generate.py:255`). The safe, cross-lane-dispatchable capability this mechanism can grant is **`Read, Grep,
Glob, Edit, Write` — real, controlled file writes — with `Bash` categorically excluded**, because Bash is the
proven arbitrary-execution vector (R2-03) and no headless-safe way to gate *which* Bash commands run was found
or is claimed here (that would require the bash-sandbox story ADR-0007 Decision 2 already says does not exist,
the same reason pi's own `GUARD_TOOLS_CODE_RW` stays unreachable from its routed entry point). Concretely:
`implementer`/`debugger` dispatched cross-lane through AC-02 CAN write real code changes (their actual job),
but CANNOT run Bash-based local validation (tests, build, `verify.sh`) within that same spawn — that capability
is real but narrower than what an in-process, human-supervised OpenCode Task-tool delegation gives the same
role today. Decision 4's "yes, keep writer-side redirect in scope" and decision 1's "CLI-level read-only
ceiling, never frontmatter-trusted" are **reconcilable, not in conflict** — provided AC-02 states this narrowed
capability explicitly as its own contract, not as "the same as normal code-rw." AC-02 below does so.

**R2-02's lifecycle question, resolved by choosing option (a) explicitly (a NEW, separate code path).** AC-02's
Claude-Code spawner is a new module, not a literal call into `set_agents_spawn.route_and_spawn` — it therefore
never needs a scoped ownership exception on that already-accepted file (the mechanism 013-pi-interactive-target's
own AC-12 established a real precedent for, `feature-state.py update-package --exception ...`, citing
`ai/state/features/005-portable-harness.json:2316-2330` — **correcting a mis-citation surfaced this round: the
precedent is `013`'s AC-12, not `014`'s** — `014-model-preference-policy`'s spec has no AC-12 at all, verified
live this session by re-reading its Acceptance Criteria list, which stops at AC-09). See AC-02 for the full
lifecycle design this choice implies (no double-decision, and an explicit run/usage-bookkeeping answer for
review-class spawns).

## Alcance

- **AC-01** — a provider-aware effective-runtime resolution inside `RoutingService.route()`'s existing
  exclusion loop, so a route whose provider has a live, authenticated redirect lane is evaluated against that
  lane's inventory instead of blindly against `facts.selected_runtime`, for both writer and review decisions.
- **AC-02** — a new, SEPARATE Claude-Code-lane CLI subprocess spawn module (not a call into
  `set_agents_spawn.route_and_spawn`), reusing the same `--route-decide -> [--route-dispatched -> spawn ->
  --route-terminal]` lifecycle SHAPE for writer-class decisions and an explicitly narrower, no-bookkeeping path
  for review-class decisions, with a `claude`-specific spawn primitive that enforces a CLI-level, never
  frontmatter-trusted, tool ceiling (read-only for review-class; bounded Edit/Write, no Bash, for the
  cross-lane-redirected writer-class case — `## Contexto` §H).
- **AC-03** — the shared canonical "Tiered dispatch — decide→spawn protocol" doctrine
  (`Global/_canonical/agents/orchestrator.md:160-227`) is rewritten to add a same-lane vs. cross-lane-redirect
  vs. true-off-lane branch, regenerated into all three harnesses, updating the existing regression test that
  asserts the current literal off-lane condition string.
- **AC-04** — the review-independence gap (§D/§E) is closed **for the ~12-day two-provider window (see
  `## Origen`)**: an explicit doctrine branch for the everyday verified-review shape, a real cross-lane spawn
  for it, and a regression test proving `REVIEWER_INDEPENDENCE_UNAVAILABLE` still halts, unchanged, when no
  redirect exists.
- **AC-05** — the residual OpenAI-only exposure of the benign/unverified review path (`[areas.audit]`/
  `[areas.judge]`'s static default) is named, not fixed.
- **AC-06** — the `go-zen` static duplicate (§G) is fixed, values-only, AND the new `.claude`-axis
  `[areas.audit]`/`[areas.judge]` vs. anthropic-frontier-route collision (§G-bis) is fully fixed the same way
  (round 3, user decision 1 — no residual left to name).
- **AC-07** — restates, as a testable boundary, that no new catalog/probe/provider onboarding happens (the
  catalog/snapshot layer was already general enough, per §B).
- **AC-08** — a new ADR records this design, superseding contract 1.0.0's own (never-materialized) planned ADR.

## Non-goals (explicit)

- **No change to `008-dynamic-selection`'s P1 accepted candidate-selection algorithm.** AC-01 touches only the
  `facts.selected_runtime`-keyed sites in the exclusion loop and its post-selection re-check
  (`service.py:137,144,145,195,200,201,206,208` — an eight-entry list, corrected this round, R3-06: round 1/2
  first undercounted this as "five", then round 2 mislabeled its own already-complete eight-entry list as
  "six"; re-verified live this session by grepping every `facts.selected_runtime` occurrence, `:128`'s
  `request.selected_runtime` conflict check deliberately excluded, see `## Contexto` §D); the
  tier/`curated_priority`/route-id sort
  key (`service.py:171`) and every hard-exclusion reason other than the auth-check's runtime source are
  byte-for-byte unchanged. **Hard requirement, not one of several candidate shapes (corrected this round,
  R2-05): the redirect only ever applies when the REQUESTED lane's own `(facts.selected_runtime, provider)`
  pair is unauthenticated** — it never overrides an already-working, already-authenticated lane, so a
  `pi`-hosted `anthropic` decision (already served today by the accepted, working `("pi","anthropic")` pair)
  is never redirected away from `pi` toward `claude-code`; see AC-01's own text for the constraint this places
  on the redirect-shape's representation.
- **No promotion of `claude-code` to `[runtime].primary` or `.fallbacks`.** The orchestrator's own hosting
  lane stays `opencode`, unchanged (`models.toml:35-36` — corrected citation this round), this contract adds a
  narrow, provider-scoped redirect for spawning *children*, not a change to which CLI hosts the orchestrator
  itself.
- **No new OpenCode-lane tier-variant artifacts, and no change to `models_config.load_role_tiers`'s schema or
  `check_variant_catalog_coherence`'s projector** (§F) — reverses contract 1.0.0's own planned AC-01.
- **No change to `014-model-preference-policy`'s own contract or files.** Read-only reference only.
- **No new provider onboarding** (Kimi Code or otherwise). **This includes the certain, scheduled day-13 halt
  named in `## Origen`/`## Contexto` §E (round-2 correction, R2-01): once `openai-codex` drops out and
  `anthropic` is the sole authenticated provider, `REVIEWER_INDEPENDENCE_UNAVAILABLE` fires and doctrine halts
  permanently from that day forward. This is an ACCEPTED, DOCUMENTED limitation of this contract, not a defect
  it fixes — onboarding a real second provider (Kimi or otherwise) so automatic review-independence can resume
  is explicitly deferred to a different, future, not-yet-scoped feature.**
- **No named owner for Claude-Code-lane quota exhaustion inside `011-quota-failover`'s current scope
  (R2-09).** `011`'s detection scope is explicitly pi-only today ("The Pi lane owns a subprocess and can
  observe its provider error and usage payload", `docs/specs/011-quota-failover/spec.md:8`). AC-02 introduces a
  SECOND lane (`claude-code`) that can also observe a real anthropic-exhaustion error/usage payload from its
  own subprocess — this contract's spawner does NOT record it as a quota-failover signal anywhere; `011`'s
  scope would need to be widened to cover this second lane, as a separate, future decision for `011` itself,
  not delivered here.
- **No change to `[areas.<duty>]`'s static, install-time-baked default model resolution values**, except the
  two named, values-only collision fixes (AC-06: the pre-existing `go-zen` OpenCode-axis collision, and the
  new `.claude`-axis `[areas.audit]`/`[areas.judge]` vs. anthropic-frontier-route collision this redesign
  itself introduces, `## Contexto` §G-bis, R2-04) — everything else governed by Accepted `ADR-0003` is
  untouched.
- **No fix to Codex's own tiered-dispatch story.** Codex has zero tier-variant files today, same as Claude
  Code had before this contract — that gap is pre-existing, `anthropic`-unrelated, and inert while `codex` is
  neither `[runtime].primary` nor a configured fallback. Not delivered here.
- **No change to `pi`'s dispatch lane** (ADR-0007) — `("pi","anthropic")` is already an audited pair with its
  own separate, accepted tiering story (`013-pi-interactive-target`); untouched.
- **No cost/budget/quota-failover logic.** `provider_exhausted` (`service.py:143`) is untouched; an
  authenticated-but-quota-exhausted provider is still excluded the same way regardless of which runtime lane
  serves it (011's own territory, unaffected).
- **No relaxation of ADR-0011 D4's halt rule.** `REVIEWER_INDEPENDENCE_UNAVAILABLE` still halts, in every
  runtime, whenever no independent candidate is reachable on any lane this contract wires up — AC-04 tests
  this explicitly (§E).
- **No credential provisioning required from the operator.** Unlike contract 1.0.0 (which needed OpenCode
  authenticated against Anthropic, an action the user has now explicitly declined to take due to cost),
  `("claude-code","anthropic")` is **already** live-authenticated on this machine (§C) — this contract ships
  fully usable without any new operator action.
- **No opportunistic rewrite of the "Tiered dispatch" section beyond what AC-03/AC-04 require** — its
  numbering, the `ROUTING_UNAVAILABLE`/`REVIEW_IDENTITY_UNVERIFIED` branches, and step 4's review-identity
  rules stay as they are; only the off-lane/branch-selection clauses are edited.
- **Coordination note, not a scope change:** `013-pi-interactive-target` also reads the canonical
  `orchestrator.md` body verbatim (its own new pi-targeted converter) — AC-03's edit to the "Tiered dispatch"
  section is a same-file, textually-disjoint change from what 013 does (013 converts the whole body for a new
  4th harness copy; it does not edit this section's content), but both features touch this file in the same
  window — package-planning should sequence accordingly (same concern round 1's F-08 raised, re-verified
  still applicable under this redesign).

## Acceptance Criteria

- **AC-01 — Provider-aware effective-runtime resolution.** In `RoutingService.route()`'s exclusion loop
  (`service.py:134-169`, corrected citation this round, R2-13 — see `## Contexto` §D) and its post-selection
  re-check/re-probe (`service.py:187-209`), a route's authentication/identity is resolved against an
  **effective runtime** — `facts.selected_runtime` for a provider with no configured redirect (all behavior for
  `openai-codex` today is byte-identical to now), or a named alternate runtime for a provider that has one
  (`anthropic` → `claude-code`, the only redirect this contract configures). The resolved effective runtime is
  what the persisted `RouteDecision.runtime` field (`domain.py:166`, already exposed today as `data.runtime` in
  the `--route-decide` JSON envelope, `set_agents_app.py:440`) reports — so a decision that will actually
  execute on the Claude-Code lane says so in its own audit trail, not the merely-requested lane, using the
  existing field (no new wire field). The request's own `selected_runtime` (used by the `request.
  selected_runtime not in (None, facts.selected_runtime)` conflict check, `service.py:128`) keeps its current
  meaning — "which lane the caller is asking from" — unaffected by this AC. `build_snapshot`/`identity_allowed`
  (§B) require **no change** — the identities they already compute already admit the `claude-code`/`anthropic`
  pair.
  **Hard requirement (round-2 correction, R2-05 — no longer one of several candidate shapes): the redirect
  fires ONLY when the REQUESTED lane's own `(facts.selected_runtime, route.provider)` pair is unauthenticated.**
  It must never override an already-working, already-authenticated lane for the same provider. This is the
  ONE requirement that keeps AC-01's own Non-goal — "no change to `pi`'s dispatch lane" — actually guaranteed
  by the code, not merely asserted in prose: two of the three redirect-shape candidates this spec previously
  left equally open (an unconditional `[runtime.redirects]` table, or a closed code constant applied
  regardless of the requested lane's own auth state) are provider-scoped but lane-blind, and would redirect a
  `pi`-hosted `anthropic` decision AWAY from its own already-working, already-authenticated
  `("pi","anthropic")` pair toward `claude-code` — silently breaking that Non-goal. Only the third candidate
  shape — conditional on the REQUESTED pair genuinely failing auth — preserves it; this is now the hard
  requirement, not an option.
  **Round-3 correction (R3-05) — granularity clarified: "unauthenticated" means PAIR-LEVEL ABSENCE, not
  per-model incompleteness.** The prose above is phrased at pair granularity ("the requested pair is
  unauthenticated"), but the actual code check (`service.py:145`) operates at MODEL granularity: `route.model
  not in self.inventory.get((runtime, provider), frozenset())`. This matters because `("pi","anthropic")`'s
  inventory entry is model-listing-derived (unlike `("claude-code","anthropic")`'s wholesale login-derived
  grant, R2-08, `## Contexto` §H) — a pi-hosted decision for a model NOT in pi's own live-probed anthropic list
  must NOT be redirected to `claude-code`; it must stay excluded via the ordinary `PROVIDER_UNAUTHENTICATED`
  path, exactly as it does today. **The redirect fires if and only if the requested `(runtime, provider)` pair
  has NO inventory entry AT ALL** — `self.inventory.get((runtime, provider))` itself is `None`/absent, a
  pair-level presence check, never merely "this one model is missing from an otherwise-present pair." A
  present-but-model-incomplete pair (the pair key exists with a non-empty but partial model set) still
  correctly excludes via the existing per-model `PROVIDER_UNAUTHENTICATED` check, unchanged, and must never
  trigger a cross-lane redirect.
  **Faithful verification requirement:** the regression test must exercise the real exclusion loop end to end
  (via `RoutingService._for_tests`/`routing._compose_for_tests`, the same hermetic seam already used
  throughout `tests/test_routing.py`) with an inventory shaped like this machine's real live probe (no
  `("opencode","anthropic")` key at all — the fixture that would otherwise fool this criterion, since
  `tests/test_routing.py`'s own default `setUp` fixture, line 147-148, DOES include that key and would pass
  even without this fix), reproducing exactly the two shapes empirically captured in `## Contexto` §D:
  (a) pre-fix-shaped inventory without the code fix → `REVIEWER_INDEPENDENCE_UNAVAILABLE`; (b) with AC-01
  landed → `provider="anthropic", runtime="claude-code", independence_verified=True, reason_codes=()`. **A
  THIRD, new required fixture (R2-05's Non-goal-guarantee, not previously tested): an inventory where
  `("pi","anthropic")` IS authenticated (mirroring `pi`'s own accepted, working tiering story,
  `013-pi-interactive-target`) and a decision is requested with `facts.selected_runtime="pi"` — AC-01 must
  resolve this WITHOUT redirecting to `claude-code`, i.e. `runtime="pi"` in the resulting decision, proving the
  redirect never fires when the requested lane already works.** **A FOURTH, new required fixture (R3-05's
  granularity guarantee, not previously tested): `inventory[("pi","anthropic")] = {"haiku"}` only (the pair
  IS present but INCOMPLETE — missing every other anthropic model), `selected_runtime="pi"`, and a
  frontier-tier decision requiring a DIFFERENT anthropic model (e.g. `"opus"`, not in that set) — AC-01 must
  NOT redirect to `claude-code`; it must resolve via the ordinary `PROVIDER_UNAUTHENTICATED` path and stay
  correctly excluded on the `pi` lane, never silently jump lanes to `claude-code` even though `claude-code`'s
  own inventory might separately carry that model.**
  [UNVERIFIED for architecture: (1) the exact representation of the provider→runtime redirect map, CONSTRAINED
  to satisfy the hard requirement above (conditional on the requested pair's own auth failure, never
  unconditional) — extending `[runtime].fallbacks` semantics (currently an empty, unused list,
  `models.toml:36`) so a provider whose `facts.selected_runtime` pair is unauthenticated is retried against
  each fallback runtime IN PROVIDER-SCOPED order, vs. a new explicit `[runtime.redirects]`/similar table, vs. a
  small closed constant in code (`catalog.py`'s `_OPENCODE_CLI_IDS`-style precedent) — any of these are
  acceptable IF AND ONLY IF they are gated on the requested pair's own auth failure; none may implicitly widen
  `openai-codex`'s own reachable runtimes (that would collide with `011`'s quota-failover territory, an
  explicitly named non-goal) — architecture must choose a shape that cannot silently generalize into "try
  every fallback for every provider." (2) Whether `facts.selected_runtime` itself is left untouched and a
  parallel `effective_runtime` local is computed only at the cited call sites listed in `## Contexto` §D (this
  spec's assumption, minimal blast radius), or whether `_ObservedTaskFacts`/`identity` gain a new field —
  package-planning must confirm against the real diff, not this spec's inferred minimal shape.]
- **AC-02 — Claude-Code-lane CLI subprocess spawn integration, with a CLI-level tool ceiling as a DECIDED
  security requirement (round-2 correction, R2-02/R2-03/R2-06/R2-07/R2-08, user decisions 1/4; round-3
  correction, R3-01/R3-04, user decision 2 — `## Contexto` §H).** A new, SEPARATE spawn module (never a call
  into `set_agents_spawn.route_and_spawn`
  itself — see the lifecycle/ownership sub-bullet below) delivers the task via **stdin** (never as a trailing
  positional argument — R2-07, live-confirmed this session: a positional prompt after a variadic `--tools`
  flag is silently swallowed into the flag's own token list and the run then fails with `Error: Input must be
  provided either through stdin or as a prompt argument`) and invokes `claude --print --agent <role> --model
  <catalog-short-name> --output-format json --no-session-persistence --setting-sources user --tools <ceiling>
  [--permission-mode acceptEdits]` (cwd = repository root, `--add-dir` never passed — `--setting-sources user`
  is MANDATORY on every invocation, both role classes, round 3, R3-01, see the security sub-bullet below), where
  `<ceiling>` and the optional `--permission-mode` are set by role class, never by the
  agent file's own frontmatter, and classifies the result the same three ways `set_agents_spawn.spawn()`
  already does for pi: `success` (`is_error=false`, `modelUsage` keys resolve to the requested model's
  canonical id), `model_mismatch` (`modelUsage` names a different canonical model than requested, or is
  empty/absent — never silently trusted), `failure` (nonzero exit, `is_error=true`, or an unparseable/missing
  JSON object). Reuses the BASE `.claude/agents/<role>.md` file already generated and installed for every
  role (`generate.py:357-364`, `install.py:31`) via `--agent <role>` — **no new tier-variant files, no
  extension of `models_config.load_role_tiers`'s schema** (§F).
  **CLI-level tool ceiling — DECIDED, not UNVERIFIED (user decision 1, live-verified this session, `## Contexto`
  §H):**
  - **Review-class dispatch (package-reviewer, delta-reviewer, security-auditor, finding-verifier —
    `roles.tsv:20-23`):** `--tools "Read,Grep,Glob"`, no `--permission-mode` override. Live-proven this session
    to hold even against a `code-rw` role's own, more permissive frontmatter (`generate.py:255`) and even
    absent any `hooks:` block at all — the tool is categorically absent from the session, not merely
    hook-gated, which is a strictly stronger guarantee than relying on frontmatter/hooks. `--permission-mode
    plan` was tested and found to BREAK headless execution (`error_during_execution` the instant any tool is
    invoked) — it must NOT be used.
  - **Round-3 addition (R3-04, user decision 2) — review-class spawns have no Bash, so they cannot fetch their
    own diff; the CALLER must supply it.** Review-class dispatch (`--tools "Read,Grep,Glob"`, no Bash) cannot
    run `git diff`/gate commands itself to see what it is reviewing. **The caller invoking AC-02's spawn
    primitive (the orchestrator, or whichever code path drives a review-class dispatch) is responsible for
    supplying the diff/relevant review content directly** — either (i) as a file the reviewer's `Read` tool
    can access, written within the cwd write-containment boundary already established (never outside the repo
    root), or (ii) embedded directly in the task/prompt text delivered via stdin (see the stdin-delivery
    mechanism above). This is a real requirement on AC-02's CALLING CONTRACT — what the caller must provide
    before invoking a review-class spawn — not merely a narrowing note about what the reviewer lacks. A
    review-class spawn invoked without either (i) or (ii) is a caller defect, not something AC-02's spawn
    primitive itself can detect or repair.
  - **Writer-class cross-lane-redirect dispatch (decision 4's scope, `implementer`/`debugger` — see the
    reconciliation sub-bullet below for the precise, narrowed capability this actually grants):** `--tools
    "Read,Grep,Glob,Edit,Write" --permission-mode acceptEdits`. `Bash` is CATEGORICALLY EXCLUDED — this is the
    proven arbitrary-execution vector (R2-03) and is never granted through this mechanism, full stop, no
    parameter or override widens it, mirroring `set_agents_spawn.py:70,332-335`'s own SEC-A02 precedent
    (`route_and_spawn` hardcodes `GUARD_TOOLS_READONLY`, no `guard_tools` parameter exists on the routed
    entry point at all). `--permission-mode acceptEdits` is REQUIRED for Write/Edit to actually succeed in
    headless mode — live-verified this session: the identical Write call is DENIED (`permission_denials`
    populated, no file created) without it, and SUCCEEDS (`permission_denials: []`, file created with exact
    content) with it.
  - **Decision 1 + 4 reconciliation, stated as a hard requirement, not left implicit:** this mechanism grants a
    code-rw role dispatched cross-lane the capability set `{Read, Grep, Glob, Edit, Write}` — real, controlled
    file writes, i.e. its actual job of writing code — but explicitly NOT the roster's normal `code-rw`
    capability set `{Read, Grep, Glob, Edit, Write, Bash}` (`generate.py:255`). Concretely: `implementer`/
    `debugger` dispatched this way CANNOT run Bash-based local validation (tests, build, `verify.sh`) within
    the same spawn. This is a real, named, narrower guarantee than "full code-rw" — AC-08's ADR must record it
    as such, and any doctrine text or package-planning decision that assumes cross-lane-dispatched writers can
    self-validate via Bash is wrong and must route local validation through a different, already-existing
    mechanism instead (out of scope to design here).
  - **Spawn ceiling — mandatory CLI-level containment flags for BOTH role classes (round 3, R3-01, SECURITY,
    live-verified this session).** Round 3 found, live-verified: a project-scope `.claude/settings.json` with a
    `SessionStart` hook, or a project-scope `.claude/agents/<role>.md` file (which can itself carry a
    `PreToolUse` hook — this repo's OWN `generate.py:258-279` `frontmatter_hook` already generates exactly this
    shape for hooked capabilities, confirming the pattern is real, not hypothetical, on this very tree),
    executes arbitrary shell OR substitutes the role prompt — **even when `--tools ""` is passed**: an empty
    tool list provides ZERO protection against hooks or agent-file shadowing, because both operate at a layer
    `--tools` does not gate. **The verified, working mitigation, MANDATORY on every AC-02 spawn, both role
    classes, no exception:**
    (1) **`--setting-sources user`** — confirmed the real flag and exact wording via `claude --help`, re-read
    this session: `--setting-sources <sources>` — "Comma-separated list of setting sources to load (user,
    project, local)." Passing `user` alone means project-scope `.claude/settings.json` hooks never load and
    project-scope `.claude/agents/<role>.md` files are ignored, while installed USER-scope agents remain
    resolvable, so `--agent <role>` still works exactly as AC-02 needs.
    (2) **the spawn cwd is the repository root, and `--add-dir` is NEVER passed** — cwd is the
    write-containment boundary this whole mechanism relies on; confirmed live this session: `git rev-parse
    --show-toplevel` resolves to the repo root (`/home/federico/SET-AGENTES` on this machine), genuinely
    distinct from `$HOME`, so this boundary genuinely excludes `~/.claude/**`, where a shadowing agent/settings
    file could otherwise be planted. Passing `--add-dir` would widen this boundary and is categorically
    forbidden.
    (3) **do not reach for `--bare` or `--safe-mode` as a substitute or additional hardening measure** — both
    checked against `claude --help`'s own documentation this session and are the wrong tool for this job:
    `--bare` ("Minimal mode: skip hooks... Anthropic auth is strictly `ANTHROPIC_API_KEY` or `apiKeyHelper` via
    `--settings` (OAuth and keychain are never read)") breaks OAuth entirely — this whole contract's premise is
    reusing the user's existing OAuth subscription (`## Contexto` §C), so `--bare` would silently force a
    metered API-key path, defeating the contract's entire cost rationale; `--safe-mode` ("Start with all
    customizations (CLAUDE.md, skills, plugins, hooks, MCP servers, custom commands and agents, ... ) disabled")
    disables custom agents outright, breaking `--agent <role>` itself, the mechanism AC-02 depends on. Neither
    is a substitute for `--setting-sources user`. Also confirmed this session: `--permission-mode acceptEdits`
    already denies writes outside cwd AND denies any write under `<cwd>/.claude/**` even under `acceptEdits` —
    so an AC-02 spawn cannot plant these shadowing files itself, but it WOULD honor them if they arrive via any
    other path (a different lane's writer, a branch checkout, a human edit); `--setting-sources user` is what
    closes that remaining gap, independent of how the shadowing file got there.
  **Lifecycle and ownership (R2-02, resolved by choosing option (a) explicitly — a NEW, separate code path,
  `## Contexto` §H):** this spawn module does NOT call `set_agents_spawn.route_and_spawn` and therefore never
  needs a scoped ownership exception on that already-accepted file (contrast `013-pi-interactive-target`'s own
  AC-12, the real precedent for that mechanism when it IS needed — corrected citation this round, it is not
  `014`'s AC-12, which does not exist; `014-model-preference-policy`'s own Acceptance Criteria list stops at
  AC-09, verified live this session). It reuses the LIFECYCLE SHAPE, not the function body, and the two role
  classes get explicitly different, non-symmetric treatment:
  - **Writer-class (`execution_enabled=True`, real `run_id`):** the orchestrator has ALREADY called
    `--route-decide` (per AC-03/AC-04's doctrine) before choosing which spawn mechanism to invoke; this
    module CONSUMES that existing decision's `run_id` — it never calls `--route-decide` a second time (a
    second call would burn a second one-use `single_writer` authorization, `models.toml:48`, for one actual
    spawn — the double-decision bug this AC explicitly avoids). It then drives `--route-dispatched <run_id> ->
    spawn -> --route-terminal <run_id> <outcome>` itself, the same three-call shape `route_and_spawn` uses,
    reusing its crash-never-leaves-a-run-open discipline, its secret-redaction discipline (`_redact`,
    `set_agents_spawn.py:97-103`), and its usage-attachment contract, adapted to the single-JSON-object output
    shape (not pi's JSONL event stream).
  - **Review-class (`execution_enabled=False`, `run_id=None` BY CONSTRUCTION — `service.py:175-182`,
    `domain.py:169` — a review decision is selected but never becomes a writer authorization, "P1R persists
    only writers", `service.py:116`):** this module gets **NO run/usage bookkeeping through the routing store
    at all**, and this is stated here explicitly rather than silently assumed compatible with `route_and_spawn`'s
    lifecycle (which itself REFUSES to open a session for exactly this decision shape —
    `set_agents_spawn.py:374-377`, "AC-11 refusal path: no session, ever, for a non-executable decision"). This
    is not a regression: review-class decisions on ANY lane, today, already never get routing-store run/usage
    bookkeeping (they are structurally never durably authorized) — a review-class Claude-Code spawn is simply a
    plain, un-authorized dispatch of the artifact AC-01's decision named, with NO `--route-dispatched`/
    `--route-terminal` call at all, consistent with how review decisions already behave everywhere else.
  **Model-mismatch testing (R2-08):** `catalog.py`'s `("claude-code","anthropic")` inventory entry is
  login-presence-derived, not model-listing-derived (`_parse_claude_auth`, `catalog.py:190-193`, reads only the
  boolean `loggedIn` and, on success, grants the WHOLE configured `[catalog].claude` allowlist wholesale) — so
  `PROVIDER_UNAUTHENTICATED` can never fire for an anthropic model the user's actual plan tier does not
  actually serve. AC-02's own spawn-time `model_mismatch` classification (above) is therefore the ONLY
  model-level guarantee in this lane, and its regression test must be exercised against a realistic
  overload/fallback shape (e.g. a model the plan tier genuinely does not serve, or a fallback substitution),
  not only a bogus/nonexistent-model-name 404 case (this spec's own live evidence for the 404 case, `##
  Contexto` §C item 4, remains valid but is not sufficient on its own).
  [UNVERIFIED for architecture: (1) exact module boundary/file name for the new spawn code — package-planning's
  choice, not asserted here. (2) The precise mechanism by which the writer-class spawn module obtains the
  orchestrator's already-decided `run_id`/`provider`/`model` (a CLI argument, an env var, a small file handoff)
  — package-planning's choice, constrained only by "never re-decides."]
- **AC-03 — Orchestrator doctrine: same-lane / cross-lane-redirect / true-off-lane.** Edit
  `Global/_canonical/agents/orchestrator.md`'s "Tiered dispatch" section (`:160-227`), specifically step 2
  ("Match by MODEL", `:171-177`) and the "Off-lane model" bullet (`:186-190`), so that once matched by model
  (never a hardcoded prose model→tier table — preserved invariant), the orchestrator branches on
  `data.runtime` (already an existing field, per AC-01): (a) **same-lane** — `data.runtime` EQUALS THE
  ORCHESTRATOR'S OWN HOST HARNESS, WHATEVER IT CURRENTLY IS (round-2 correction, R2-04/R2-10b: previous wording
  hardcoded "today, always `opencode`", contradicting `## Origen`'s own statement that THIS session's
  orchestrator is Claude-Code-hosted — the doctrine text must be self-aware/runtime-agnostic, never assume a
  specific harness; `[runtime].primary` happening to be `"opencode"` today, `models.toml:35`, is a config fact,
  not a doctrine assumption) — spawn the matching `<role>@<tier>` variant for that lane exactly as today,
  unchanged; (b) **cross-lane redirect** — `data.runtime == "claude-code"` and the orchestrator's own host
  harness is not `claude-code` — spawn via AC-02's new subprocess mechanism, using the BASE
  `.claude/agents/<role>.md` with `--model data.model`; (c) **true off-lane** — `data.provider`/`data.runtime`
  names neither the orchestrator's own lane nor a configured cross-lane redirect (not reachable on today's
  two-provider/two-lane catalog, but the branch must not assume it stays that way) — close as abandoned and
  spawn the BASE static agent, generalized from the current single hardcoded `"openai-codex"` string.
  Regenerated into all three harnesses via `./build.sh`, per the existing shared-canonical-body precedent
  (`generate.py:336`) — never hand-edited. **Existing regression test this AC must update, not weaken:**
  `tests/test_harness.py:2864-2895` (`test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`)
  currently asserts the literal string `` 'data.provider != "openai-codex"' `` in all three generated files;
  its assertions are updated to the corrected same-lane/cross-lane/true-off-lane condition in the same pass,
  and the test must still fail if a real true-off-lane case is silently swallowed. **Restated as
  forward-compatible, not hardcoded to three files (R2-10a):** the test iterates "every generated harness
  file the doctrine is copied into — three today (`Global/opencode/agents/orchestrator.md`,
  `Global/claude-code/agents/orchestrator.md`, `Global/codex/agents/orchestrator.toml`), four once
  `013-pi-interactive-target` lands (`Global/pi/agents/orchestrator.md`, currently in `PACKAGE_PLANNING`,
  verified live this session) — never a literal three-tuple that silently stops covering a newly-added
  harness copy." Both this fix and the branch-(a) runtime-agnostic fix above must land as the SAME corrected
  text (R2-10b) — package-planning must not fix the "opencode" assumption once here and again, differently,
  under R2-04's own citation.
  [UNVERIFIED for architecture: the exact rewritten prose — the requirement is a truth condition (self-aware
  of the orchestrator's own host harness, correctly distinguishing the three branches above), not specific
  wording.]
- **AC-04 — Review-independence gap closed for the ~12-day two-provider window (see `## Origen`) via the
  redirect, with the ADR-0011 D4 halt guarantee preserved.**
  Add an explicit branch to "Branch on the decision outcome" (`:178-223`) for the everyday verified-review
  shape (`ok=true`, `reason_codes=()`, `execution_enabled=false`, `independence_verified=true`) — spawn the
  matching artifact for `data.provider`/`data.runtime` via the SAME same-lane/cross-lane rule AC-03 defines
  for writers, never the BASE reviewer by default for this shape. The existing "Benign non-executable review"
  branch (`reason_codes == ["REVIEW_IDENTITY_UNVERIFIED"]`) is untouched (AC-05 names its residual). **Two
  faithful regression tests, not one:** (a) an end-to-end hermetic pipeline test reproducing `## Contexto` §D's
  post-fix shape exactly (writer→`openai-codex` on `opencode`, reviewer→`anthropic` on `claude-code`,
  asserting the doctrine's new branch — not the off-lane/BASE-agent branch — is what the generated
  orchestrator text instructs, and that AC-02's spawn primitive is what actually gets invoked) — **extended
  this round (R3-04/decision 2):** the test also asserts the diff payload the orchestrator supplies actually
  reaches the reviewer via the mechanism AC-02's calling contract requires (a file the reviewer's `Read` tool
  can access, or content embedded in the stdin-delivered task/prompt) — round 3 found the prior draft's test
  only checked which branch fires and which spawn primitive is invoked, never that the reviewer can actually
  see the diff it is reviewing; this gap is fixed by asserting the composed task/prompt or provided-file
  payload contains the real diff content, not merely that AC-02's primitive was invoked; (b) a
  regression test asserting `REVIEWER_INDEPENDENCE_UNAVAILABLE` is UNCHANGED (still returned, still a hard
  denial per doctrine branch 3c, never silently downgraded to a degrade). **Fixture corrected this round
  (R2-12) — the PRIMARY case must be the real, non-vacuous day-13 shape, not the fully-empty-inventory case:**
  the prior fixture had NEITHER provider authenticated on any lane, which returns
  `REVIEWER_INDEPENDENCE_UNAVAILABLE` trivially — even without any of this contract's own changes — and so
  proves nothing about whether AC-01's redirect logic weakened the invariant. The PRIMARY fixture is now: only
  `anthropic` authenticated (via `claude-code`, as it will be for the ~12-day window `## Origen` describes,
  and permanently from day 13 onward), `openai-codex` NOT authenticated, writer resolves to `anthropic` →
  reviewer must STILL correctly halt with `REVIEWER_INDEPENDENCE_UNAVAILABLE`, never incorrectly redirect to a
  same-provider-same-model reviewer on `claude-code`. This is the exact day-13 shape named in `## Contexto`
  §E's corrected framing (R2-01) — this test is what proves that limitation is real and correctly enforced,
  not merely asserted in prose. The fully-empty-inventory case is kept as a secondary/additional assertion in
  the same test, not the sole one.
- **AC-05 — Residual OpenAI-only exposure named, not fixed (extended round 2, R2-04/G-bis; the `.claude`-axis
  balanced-tier residual round 2 added here is WITHDRAWN in round 3, decision 1 — see below).** Once AC-04
  lands, the benign/unverified review path (`REVIEW_IDENTITY_UNVERIFIED`, no `review_of_run_id` offered) still
  spawns the BASE reviewer/judge agent, whose static OpenCode-lane default (`[areas.audit].opencode`/
  `[areas.judge].opencode`, `models.toml:96,102`) is `openai/…` on every lane profile, never `anthropic` —
  unchanged from contract 1.0.0's own AC-04, renumbered. Not fixed here (`ADR-0003`'s seam, same as `014`
  declines to touch). **Round-2's `.claude`-axis balanced-tier residual is WITHDRAWN this round (R3-02/R3-03,
  `## Contexto` §G-bis).** Round 2 named a residual here: with AC-06(b)'s then-fix value `"sonnet"`, a
  balanced-tier writer redirected to `anthropic`/`sonnet` via AC-01 would still collide, on this same
  benign/unverified static path, with `[areas.audit].claude`/`[areas.judge].claude = "sonnet"`. That residual's
  premise — that `"fable"` was unusable as a fully collision-free alternative because it resolves to the same
  canonical model as `"opus"` — was live-reproduced again this round and found FALSE (`fable`→`claude-fable-5`,
  `opus`→`claude-opus-5`, genuinely distinct). The user chose `"fable"` for AC-06(b) instead of `"sonnet"`
  (decision 1); `"fable"` collides with no tier and no other `.claude` default on this tree — this residual is
  fully closed, not merely named-and-accepted.
- **AC-06 — Two same-provider-and-same-model static-config collisions fixed, values-only (extended round 2,
  R2-04, to cover the `.claude` axis; (b) below corrected round 3, decision 1, to achieve FULL elimination
  rather than a highest-severity-only reduction — `## Contexto` §G-bis).**
  (a) `[areas.audit].opencode."go-zen"` (`models.toml:96`) is changed to a curated OpenAI model that differs
  from `[roles.implementer.tiers.balanced].opencode."go-zen"`'s `"openai/gpt-5.6-sol"` (`models.toml:188`) — a
  `models.toml` values-only edit, no code change.
  (b) **Corrected this round (round 3, decision 1):** `[areas.audit].claude` and `[areas.judge].claude`
  (`models.toml:93,99`) are changed from `"opus"` to `"fable"` — also values-only. Round 2 chose `"sonnet"` on
  the strength of a now-corrected false claim that `"fable"` and `"opus"` resolve to the same canonical model;
  round 3 re-reproduced the live behavior this session and found `"fable"`→`claude-fable-5` and
  `"opus"`→`claude-opus-5`, genuinely distinct canonical models, corroborated independently by `claude --help`'s
  own `--model` documentation. `"fable"` collides with NONE of: the three curated anthropic route models
  (`haiku`/`sonnet`/`opus`), `[areas.implement].claude` (also `"sonnet"`, `models.toml:81` — the collision
  `"sonnet"` as AC-06(b)'s value would have silently introduced, newly found this round, R3-03), or any other
  `[areas.*].claude`/`[roles.*].claude` value on this tree — a FULL elimination, not merely a
  highest-severity-pairing reduction; AC-05's balanced-tier residual and R3-03's BASE-implementer collision
  concern are both withdrawn, not merely accepted (`## Contexto` §G-bis).
  A regression test asserts (i) no two of `[areas.*].opencode."go-zen"` and any `[roles.<tiered-role>.tiers.*]
  .opencode."go-zen"` value collide identically, generalizing beyond this one instance so a future
  re-introduction fails the build, not just this specific pair; AND (ii), **rebuilt this round to prove FULL,
  not partial, elimination, and built generically from the live tables rather than hardcoded strings (round
  3's own recommendation):** `[areas.audit].claude`/`[areas.judge].claude`'s value does not equal ANY value in
  the union of (I) `routes.v1.toml`'s live curated anthropic model set (today `{haiku, sonnet, opus}`, read
  from its three anthropic rows, `:16-19`, `:36-39`, `:56-59`, not a hardcoded string, so a future re-tiering
  of any anthropic route is caught), and (II) every other `[areas.<duty>].claude`/`[roles.<role>].claude` value
  present in the live `models.toml` at test time (read generically via the same table-walk `models_config.py`
  itself already performs, not an enumerated string list, so a future new area/role with its own `.claude`
  default is caught too, not only the `implement` collision known today) — proving `"fable"` collides with
  nothing, not merely with the one pairing this round happened to name.
- **AC-07 — Nothing new onboarded at the catalog/probe layer; the snapshot layer was already general.**
  Restates, as a testable record: no new `[catalog]`, `[subscriptions]`, `_PAIR_COMMANDS`, or `routes.v1.toml`
  entries are added by this contract (unchanged claim from 1.0.0's own AC-05); AND, new this session, a
  regression test proving `build_snapshot`'s existing identity computation (`catalog.py:565-567`) already
  admits `(route_id, "claude-code", "anthropic", ...)` for all three anthropic rows, with **zero** change to
  `catalog.py`'s snapshot-construction code — the redesign's entire code footprint is confined to
  `service.py`'s auth-check sites (AC-01), a new spawn module (AC-02), doctrine text (AC-03/AC-04), and the
  values-only `models.toml` edits (AC-06) — none of which touch `catalog.py`. **Round-3 correction, withdrawing
  a round-2 flag:** round 2's `## Contexto` §G-bis previously flagged `catalog.py`'s curated
  `_ANTHROPIC_CANONICAL_EXTRA = {"fable": "claude-fable-5"}` (`catalog.py:86`) as "stale relative to live
  reality." Round 3 re-reproduced the live `fable`/`opus` model-resolution test this session and found this
  curation is actually CORRECT, not stale — `fable` genuinely canonicalizes to `claude-fable-5`, distinct from
  `opus`'s `claude-opus-5`, exactly as `catalog.py` already states. This flag is withdrawn; there is no known
  `catalog.py` defect to chase, and AC-07's zero-diff commitment stands with nothing outstanding to name.
- **AC-08 — Design recorded in a dedicated ADR, required as a delivery criterion, not before `USER_APPROVAL`.**
  Records: (a) the provider-aware effective-runtime redirect (AC-01) and why it is scoped to `anthropic`→
  `claude-code` only, never generalized to other providers, and constrained to fire only when the requested
  lane's own pair is unauthenticated at PAIR granularity, not merely model-incomplete (R2-05/R3-05, preserving
  `pi`'s Non-goal) — the `011`/quota-failover boundary named in Non-goals; (b) why no OpenCode-lane Anthropic
  artifacts are created, reversing contract 1.0.0's own planned AC-01 (`## Contexto` §F); (c) the corrected
  review-independence finding (`## Contexto` §D/§E) and its resolution, explicitly stating the ADR-0011 D4 halt
  guarantee is preserved, not relaxed, AND the certain, scheduled, accepted day-13 re-halt limitation (R2-01,
  `## Origen`); (d) the new Claude-Code CLI spawn mechanism, its relationship to the ADR-0007 Pi-lane precedent
  it structurally reuses (lifecycle SHAPE, not the function body — R2-02, `## Contexto` §H), the CLI-level
  tool-ceiling security design (decisions 1/4, R2-03/R2-06/R2-07) including the precise,
  narrower-than-full-code-rw capability a cross-lane-dispatched writer actually gets, the mandatory
  `--setting-sources user`/cwd-boundary/no-`--add-dir` containment requirements closing the deeper hook/agent-
  file-shadowing vector (R3-01), and the calling-contract requirement that the caller supplies the diff to a
  Bash-less review-class spawn directly (R3-04, decision 2); (e) the two same-provider-same-model static-config
  collisions this round's `.claude`-axis fix addresses, and how round 3's `"fable"` correction (decision 1)
  achieved FULL elimination with no residual, not merely a highest-severity-pairing reduction (R2-04/R3-02/
  R3-03, AC-06). Per `014`'s own precedent for un-pinned ADR numbers:
  `docs/adr/` lists through `0016` on disk today (`0016-discovered-inventory.md`); `0017` is
  claimed-not-materialized by `013-pi-interactive-target`, `0018` by `014-model-preference-policy`'s own AC-09
  — the next unclaimed candidate at spec-writing time is `0019`, same candidate contract 1.0.0 already named,
  re-confirmed live by re-listing `docs/adr/` this session; package time must re-check live rather than assume
  this holds.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → scaffold sync clean · `python3 -m unittest
discover -s tests -v` — test count measured at package-planning time, must rise, never fall, no test skipped,
covering at minimum: AC-01's four-shape hermetic proof (pre-fix `REVIEWER_INDEPENDENCE_UNAVAILABLE`, post-fix
`provider=anthropic, runtime=claude-code, independence_verified=true`, the `("pi","anthropic")`-already-
authenticated non-redirect proof (R2-05), and the `("pi","anthropic")`-present-but-model-incomplete
non-redirect proof (R3-05, new this round)) against a live-machine-shaped inventory, not
`tests/test_routing.py`'s own more generous default fixture; AC-02's subprocess-mocked spawn tests
(success/model_mismatch/failure, mirroring the existing pi-lane test precedents in `tests/test_routing.py` for
`set_agents_spawn.spawn`), PLUS the CLI-ceiling-argv tests for both role classes (read-only `--tools
"Read,Grep,Glob"` with no `--permission-mode`, and bounded-write `--tools "Read,Grep,Glob,Edit,Write"
--permission-mode acceptEdits` with `Bash` provably absent from the composed argv, AND — round 3, R3-01 —
`--setting-sources user` provably PRESENT and `--add-dir` provably ABSENT from every AC-02-composed argv, both
role classes), PLUS the review-class diff-payload assertion (round 3, R3-04/decision 2: the task/prompt text
or the provided-file payload actually contains the diff content for a review-class spawn, not merely that
spawn mechanics fire), PLUS the realistic overload/fallback `model_mismatch` case (R2-08), PLUS the
review-class no-run-bookkeeping assertion and the writer-class run-id-consumption (never re-decides) assertion
(R2-02); AC-03's updated `test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`
(`tests/test_harness.py:2864`) across every generated harness (three today, four once `013` lands, R2-10a) plus
a new true-off-lane case, plus the runtime-agnostic same-lane condition (R2-04/R2-10b); AC-04's end-to-end
pipeline test AND its D4-preservation test rebuilt on the non-vacuous day-13 fixture (R2-12), AND the
diff-payload-reaches-the-reviewer assertion (R3-04/decision 2); AC-05's unchanged-benign-path assertion (its
round-2 balanced-tier `.claude`-axis residual claim withdrawn round 3, decision 1); AC-06's
go-zen-collision-generalized assertion AND the `.claude`-axis FULL-elimination assertion, built generically
from the live `models.toml`/`routes.v1.toml` tables rather than hardcoded strings (R2-04, corrected round 3 to
prove full elimination via `"fable"`, not partial reduction via `"sonnet"`); AC-07's zero-catalog-diff
assertion; AC-08's ADR file exists and records items (a)-(e) (round 3, R3-07). `git diff --check` · ownership
vs. baseline.

### Audit (self-review)

- **Universe named:** yes. (1) The "provider needs a runtime redirect" universe is exactly one entry today
  (`anthropic` → `claude-code`) — enumerated from `_PAIR_COMMANDS`'s three anthropic pairs minus the one
  (`opencode`) now known permanently unusable without new cost (`## Origen`), not inferred. (2) The
  "review-independence gap" universe is the same closed set contract 1.0.0 named — the four audit-duty tiered
  roles (`package-reviewer`, `delta-reviewer`, `security-auditor`, `finding-verifier`, `roles.tsv:20-23`) —
  `adversarial-judge`/`spec-challenger` remain outside the tiered mechanism entirely, untouched.
- **Absence behavior defined:** yes. A route whose provider has no configured redirect and fails auth on the
  requested lane still excludes via `PROVIDER_UNAUTHENTICATED`, unchanged (AC-01). A review decision with no
  reachable independent candidate on any lane still returns `REVIEWER_INDEPENDENCE_UNAVAILABLE` and halts,
  unchanged (AC-04b, ADR-0011 D4 preserved). The benign/unverified review path still spawns the OpenAI-only
  BASE agent, unchanged (AC-05).
- **Data source proven to carry the signal:** yes, and more rigorously than contract 1.0.0 — every absence/
  presence claim in `## Contexto` was checked by direct code execution this session (a real `claude auth
  status`/`claude --print` subprocess call, a real hermetic `RoutingService` run reproducing both the pre-fix
  and post-fix decision shapes), not only static file reads.
- **Pairwise conflict pass:** AC-01 (routing fix) must land before AC-03/AC-04 (doctrine text that reads
  `data.runtime`) can be correct — sequenced, not contradictory. AC-02 (spawn mechanism) is independent of
  AC-01 and can build in parallel. AC-06 (go-zen + `.claude`-axis values fix) is fully independent of every
  other AC — checked against AC-01/AC-04 to confirm neither reads `[areas.audit]`'s values at all (confirmed:
  `RoutingService.route()` never reads `[areas.*]`, only `routes.v1.toml` + inventory). AC-07's zero-catalog-diff
  assertion is checked against AC-01 specifically to confirm the redirect fix never touches `catalog.py`'s
  snapshot construction (confirmed: all eight touched sites, R2-05/R3-06, are in `service.py`, none in
  `catalog.py`). AC-02's writer-class run-id-consumption (never re-decides) checked against `models.toml`'s
  `single_writer = true` (`:48`) to confirm a double-decision would burn two one-use authorizations for one
  spawn — this is exactly why AC-02 states the consume-not-decide rule as a hard requirement, not left to
  package-planning's judgment. AC-04(b)'s corrected day-13 fixture (R2-12) checked against AC-01's redirect
  constraint (R2-05) to confirm the two do not contradict: the fixture's "`anthropic` authenticated via
  `claude-code`, `openai-codex` not authenticated" shape is exactly what AC-01 is SUPPOSED to enable (a
  correctly-redirected writer), and AC-04(b) then confirms the review side still, correctly, has no
  independent candidate — not a conflict, a composition of the two fixes working as intended. **New this round
  (round 3):** AC-06(b)'s `"fable"` value checked against AC-01/AC-02/AC-03/AC-04's own values — confirmed
  `"fable"` is a `.claude`-axis static-config value only, never read by `RoutingService.route()`, `catalog.py`,
  or the doctrine text, so this fix cannot interact with any of those AC's own mechanisms, only with the other
  static `[areas.*]`/`[roles.*].claude` values AC-06's own regression test now checks generically. AC-02's new
  mandatory `--setting-sources user`/no-`--add-dir` requirement (R3-01) checked against AC-02's own `--agent
  <role>` mechanism to confirm it does not conflict: `--setting-sources user` keeps USER-scope installed agents
  resolvable (`~/.claude/agents/<role>.md`, `install.py:31`), which is the exact scope AC-02 already reads from
  — no interaction, the mitigation narrows only the PROJECT/local scopes AC-02 never needed.
- **UNVERIFIED-for-architecture tags:** the exact provider→runtime redirect config shape, CONSTRAINED to fire
  only on the requested pair's own PAIR-LEVEL auth failure (AC-01, R2-05/R3-05 — no longer unconstrained, and
  now stated at the correct granularity); whether `facts.selected_runtime` itself changes meaning or a parallel
  value is computed (AC-01); exact module boundary/file name for the new spawn code, and the exact mechanism
  for handing an already-decided `run_id`/`provider`/`model` to it (AC-02 — the tool-ceiling mechanism and the
  mandatory containment flags are NO LONGER UNVERIFIED, both DECIDED and live-verified, `## Contexto` §H and
  round 3, R3-01); the exact rewritten doctrine prose (AC-03/AC-04, stated as a truth condition, now explicitly
  runtime-agnostic and harness-count-agnostic).
- **What changed from contract 1.0.0's own audit, corrected here:** 1.0.0 characterized the review-independence
  gap as "already silently defeated in practice, today" (a fail-open framing). This session's live execution
  (`## Contexto` §D.1) shows the real, current behavior is `REVIEWER_INDEPENDENCE_UNAVAILABLE` — a fail-closed
  hard denial — because 1.0.0's own trace implicitly relied on `tests/test_routing.py`'s more generous default
  test fixture rather than this machine's real credential shape. Both severity readings are real defects
  (one silently degrades safety, the other blocks all throughput) but they are different defects, and AC-04's
  fix and its regression tests target the one that is actually live on this machine.
- **What changed from contract 2.0.0's own audit, corrected here (round 2):** 2.0.0 left AC-02's tool-restriction
  mechanism as `[UNVERIFIED for architecture]` and flagged, but did not resolve, "whether hooks are honored in
  headless mode" as load-bearing for safety. Round 2's own live reproduction (R2-03) proved the underlying
  concern real (a code-rw role's Bash ran unguarded, headless) — this revision does not merely re-flag it, it
  replaces frontmatter/hook-reliance with a live-verified, DECIDED CLI-level ceiling (`## Contexto` §H) and
  states the resulting capability narrowing explicitly (AC-02's reconciliation sub-bullet) rather than leaving
  the safety question open into implementation.
- **What changed from contract 3.0.0's own audit, corrected here (round 3):** 3.0.0 believed its `--tools ""`/
  CLI-level ceiling closed the headless-Bash vector R2-03 found, and separately believed `"fable"` could not be
  used to fully eliminate the `.claude`-axis collision because it resolves to the same canonical model as
  `"opus"`. Round 3 found both beliefs incomplete or wrong, live, this session: `--tools ""` alone leaves a
  second, deeper vector open (project-scope hooks/agent-file shadowing, unaffected by `--tools`, R3-01), closed
  by adding `--setting-sources user` as a mandatory flag; and the `fable`/`opus` canonical-model claim was
  simply wrong (`fable`→`claude-fable-5`, `opus`→`claude-opus-5`, distinct), which round 3 used to fully
  eliminate the `.claude`-axis collision rather than merely reduce it (decision 1). This revision closes both
  gaps with live evidence, not further hedging, and this is the round-3 reviewer's own basis for calling this
  pass final.

## Historial de challenge

### Round 1 (contract 1.0.0, pre-redesign)

Verdict: `revision_required`, 13 findings. This redesign is **not** a normal "address the findings and
resubmit" revision — a live fact reported directly by the user during the same session (`## Origen`) shows
contract 1.0.0's entire spawn-target premise (OpenCode-lane Anthropic tier-variant files, spawnable once
*some* operator authenticates OpenCode against Anthropic) is categorically unusable without a new, unapproved,
metered cost the user explicitly declined. The redesign in this file replaces that premise entirely (cross-lane
redirect to Claude Code, `## Contexto` §C-F) rather than patching around it. Per-finding disposition, to the
extent each finding's content was available to this pass (F-01's original text was not relayed into this
redesign brief and could not be independently re-derived from the repository alone — flagged for the
orchestrator to confirm separately, possibly a citation/formatting finding folded into the general re-citation
pass below):

| Finding | Round-1 subject | Disposition under contract 2.0.0 |
|---|---|---|
| F-01 | (content not available to this pass) | **UNKNOWN — flag for orchestrator**, not independently re-derivable |
| F-02 | ADR-0011 D3/D4 reconciliation + `go-zen` same-provider-same-model | **CHANGED** — D3/D4 reconciled precisely in `## Contexto` §E (halt rule preserved, not relaxed); `go-zen` fixed as AC-06 |
| F-03 | Reviewer-independence, biggest blocking finding | **CHANGED** — corrected from "silently defeated" to "hard denial today" (`## Contexto` §D.1, live-executed); fixed by AC-01+AC-04 without relaxing ADR-0011 D4 |
| F-04 | Wrong OpenCode-lane Anthropic model-id inference | **MOOT** — no OpenCode-lane Anthropic artifacts of any kind are built under this design (`## Contexto` §F); model ids are bare catalog short names passed to `claude --model`, live-confirmed |
| F-05 | Lockstep tier-variant file sites / `models_config.emit` silent-drop | **MOOT for this contract** — AC-02 needs no new tier-variant files and no schema extension; the existing OpenCode/`openai-codex` mechanism this finding also touched stays untouched either way |
| F-06 | Testability of "genuine end-to-end" | **STILL VALID, addressed** — AC-01/AC-04 specify the exact hermetic seam and the exact two decision shapes to reproduce, empirically validated this session |
| F-07 | Citation fixes | **re-verified** — every citation in this file was re-read live this session against current line numbers |
| F-08 | `013-pi-interactive-target` interaction (shared canonical `orchestrator.md`) | **STILL VALID, re-verified** — restated in Non-goals' coordination note under the new design |
| F-09 | `011-quota-failover` interaction | **STILL VALID, re-verified** — `provider_exhausted` untouched; AC-01's UNVERIFIED tag explicitly guards against the redirect mechanism silently widening into quota-failover territory |
| F-10 | Q1 — review roles blocked post-deadline; user wants 015 expanded to cover review roles | **CHANGED, resolved** — AC-04 explicitly covers review-class roles, per the user's separately-confirmed request |
| F-11 | Citation fix | **re-verified** against current line numbers |
| F-12 | Citation fix | **re-verified** against current line numbers |
| F-13 | Citation fix | **re-verified** against current line numbers |

### Round 2 (contract 2.0.0, the cross-lane-redirect redesign) — 4 blocking + 9 lower-severity findings

Verdict: `revision_required`. Unlike round 1, this round is a **correction pass on an accepted architectural
direction**, not a further rescope — round 2's own "independently verified as claimed" table re-confirmed the
core cross-lane-redirect design, the real `claude` CLI flags/`--agent`/`--model` mechanism, `build_snapshot`
already supporting the identity tuple, `_opencode_projected_route`'s reversal, and the routed↔routed
same-provider-same-model exclusion's structural impossibility. What round 2 found is corrected below, via four
explicit user decisions (quoted in full where they changed a requirement — see the top of `## Origen` and
`## Contexto` §H) plus fresh live verification this session. **This round closed a genuine, live-verified
security gap (R2-03) — not a documentation-only or citation-only revision**, even though most of the remaining
findings ARE citation/precision fixes; R2-03's finding is a real, reproducible defect this contract's prior
draft would have shipped had it gone to implementation unchanged.

| Finding | Severity | Round-2 subject | Disposition under contract 3.0.0 |
|---|---|---|---|
| R2-01 | Blocking | The contract's core purpose expires in ~12 days; misleading "13th day OAuth outage" framing | **FIXED** — `## Origen` and `## Contexto` §E rewritten to state the certain, scheduled day-13 cause precisely (`anthropic` becomes the sole authenticated provider once `openai-codex` drops out, not a hypothetical OAuth failure); Non-goals now names this as an accepted, documented, time-boxed limitation, not a defect this contract fixes; AC-04(b)'s regression test rebuilt on exactly this shape (R2-12) |
| R2-02 | Blocking | AC-02's claimed reuse of `route_and_spawn`'s lifecycle is structurally impossible for review-class decisions (`execution_enabled=False`, `run_id=None` by construction; the refusal path explicitly never spawns for that shape); double-decision risk unresolved | **FIXED** — AC-02 rewritten to select option (a) explicitly: a NEW, separate spawn module, never calling `route_and_spawn` (no ownership exception needed, correcting a mis-citation of `013`'s own AC-12 precedent along the way); review-class gets NO run/usage bookkeeping (named explicitly, not silently assumed compatible); writer-class CONSUMES the orchestrator's already-existing `--route-decide` output (never re-decides), checked against `single_writer=true` (`models.toml:48`) to confirm no double-authorization-burn |
| R2-03 | Blocking, SECURITY, live-verified | A headless `claude --print --agent <code-rw-role>` spawn executed an arbitrary Bash command with `permission_denials: []` — the guard path that is supposed to gate Bash fails open in headless mode | **FIXED** — decision 1: AC-02 now mandates a CLI-level, never-frontmatter-trusted tool ceiling, mirroring the pi-lane's already-accepted `GUARD_TOOLS_READONLY`-hardcoded, no-`guard_tools`-parameter posture; live re-verified this session (`## Contexto` §H) that `--tools "Read,Grep,Glob"` genuinely removes Bash from a code-rw role's own session, even absent any hook |
| R2-04 | Blocking | A NEW same-model collision this redesign itself introduces: `[areas.audit]`/`[areas.judge].claude` both `"opus"`, colliding with the anthropic-frontier route's `"opus"` once `claude-code` is a real dispatch target; separately, `## Origen` vs. AC-03 branch (a) contradict on which harness hosts the orchestrator | **FIXED in round 2 via `"sonnet"`, SUPERSEDED in round 3 via `"fable"`** — decision 3 (round 2): AC-06 extended to the `.claude` axis (changed to `"sonnet"`), with a structural balanced-tier residual named honestly, `## Contexto` §G-bis, on the belief that round 2's own live test showed `"fable"` resolves to the same canonical model as `"opus"`. **Round 3 correction (R3-02): this belief was WRONG** — round 3 re-reproduced the identical test live and found `fable`→`claude-fable-5` vs. `opus`→`claude-opus-5`, genuinely distinct models. AC-06(b) now uses `"fable"` (user decision 1, round 3), fully eliminating the collision with no residual, not merely reducing it. AC-03 branch (a) restated runtime-agnostic, landing consistently with R2-10b's own citation of the same fix |
| R2-05 | High | Wrong pi-lane site count (five, not six); AC-01's "no change to pi's dispatch lane" Non-goal not actually guaranteed by two of three candidate redirect shapes | **FIXED** — site count corrected to six (`service.py:144`'s `PI_SIMULATION_ONLY` check added, `## Contexto` §D); AC-01 now hard-requires the redirect to fire only when the requested lane's own pair is unauthenticated, with a new third regression-test fixture proving `("pi","anthropic")` is never redirected away from `pi` |
| R2-06 | (scope question) | Is code-rw writer-role redirect actually deliverable given decision 1's read-only-ceiling constraint? | **RESOLVED, reconciled, not in conflict** — decision 4 confirmed writer-side redirect stays in scope; live investigation this session (`## Contexto` §H) found a real, distinct, CLI-level bounded-write mechanism (`--tools "...,Edit,Write" --permission-mode acceptEdits`, Bash categorically excluded) — code-rw roles CAN be safely dispatched, with a capability precisely narrower than full `code-rw` (no Bash/no local test-running through this mechanism), stated explicitly in AC-02 rather than assumed |
| R2-07 | High | The spec's own live-test evidence contradicts its own safety claim: the transcript shows no `--tools`, but AC-02 claims `--tools ""` was used, and `--tools` is variadic and swallows a trailing positional prompt | **FIXED** — reconciled live this session: the transcript's calls never used `--tools`, so they never hit the hazard; AC-02 now codifies the ACTUAL validated, robust shape — prompt delivered via stdin, never positional — reproducing round 2's own failure case exactly (`Error: Input must be provided either through stdin or as a prompt argument`) to confirm the hazard is real before fixing it |
| R2-08 | Medium | `("claude-code","anthropic")` inventory is login-presence-derived, not model-listing-derived — a real asymmetry now that this lane is used for redirect | **FIXED** — named explicitly in AC-02; its `model_mismatch` regression test requirement extended to a realistic overload/fallback shape, not only a bogus-model-name 404 case |
| R2-09 | Medium | `011-quota-failover`'s pi-only detection scope vs. this contract's second, new claude-code-lane exhaustion-observing subprocess — unnamed owner | **FIXED** — new explicit Non-goals sentence: AC-02's spawner does not record exhaustion; `011`'s scope would need widening to cover this second lane, as a separate future decision, not delivered here |
| R2-10 | Medium | (a) AC-03's regression test hardcodes three generated harness files; `013` adds a fourth; (b) the same "always opencode" host-harness assumption as R2-04, must land as the SAME fix, not two different ones | **FIXED** — AC-03 restated as "every generated harness — three today, four once `013` lands" (verified `013` is in `PACKAGE_PLANNING` this session); explicitly cross-referenced to R2-04's own runtime-agnostic fix so both land as one consistent text |
| R2-11 | Medium (informational) | `015`'s own reviewer-independence "fails closed and halts" framing reconfirmed accurate by round 2; `014`'s stale citation of it already fixed elsewhere (014 now at 3.1.0), no action needed on `015` | **CONFIRMED, no change needed** — noted here per the optional invitation; `015`'s substance was already correct |
| R2-12 | Medium | AC-04(b)'s regression fixture is vacuous — neither provider authenticated proves nothing about whether AC-01 weakened the invariant | **FIXED** — fixture rebuilt: PRIMARY case is now the real, non-vacuous day-13 shape (`anthropic` authenticated via `claude-code`, `openai-codex` not), proving the reviewer still correctly halts rather than incorrectly redirecting to a same-provider-same-model reviewer; the fully-empty-inventory case kept as a secondary assertion only |
| R2-13 | Low | Exclusion-loop citation should start at `:134`, not `:135`; the sort key's "different-provider preference stays first" reading is actually dead code for review decisions | **FIXED** — citation corrected throughout (`service.py:134-169`); the sort-key description rewritten to state precisely that the first key element is unreachable for review decisions, since `REVIEW_PROVIDER_CONFLICT` already hard-excludes same-provider candidates earlier in the same loop |

### Round 3 (contract 3.0.0, the round-2-corrected cross-lane-redirect design) — 3 blocking + 4 lower-severity findings

Verdict: `revision_required`. Round 3's own reviewer stated explicitly this is a **short revision pass, not
another design cycle** — the architecture is converged (round 3's own "independently verified as claimed"
table re-confirmed: the `--tools`/`--permission-mode` CLI-level ceiling mechanism itself, Bash categorically
absent verified via `system/init` telemetry not model self-report; the R2-02 lifecycle split; the day-13 honest
framing in `## Origen`/§E; the `build_snapshot`/catalog claims; the ADR number candidate; the
architecture-axis conclusion that no data-store/API-gateway/deploy-platform decision is missing) — and the
reviewer stated it would consider the contract ready for user approval without a further adversarial round
once these seven findings land. Two of the three blocking findings (R3-02, R3-03) are closed together by a
single user decision (decision 1: use `"fable"`, not `"sonnet"`, for AC-06(b)); the third (R3-01) is a genuine,
live-verified security gap one hop past R2-03's fix, not a documentation-only finding.

| Finding | Severity | Round-3 subject | Disposition under contract 3.1.0 |
|---|---|---|---|
| R3-01 | Blocking, SECURITY, live-verified | A second, deeper vulnerability one hop past R2-03's fix: a project-scope `.claude/settings.json` `SessionStart` hook, or a project-scope `.claude/agents/<role>.md` file (which can itself carry a `PreToolUse` hook, per this repo's own `generate.py:258-279` `frontmatter_hook` shape), executes arbitrary shell OR substitutes the role prompt — even when `--tools ""` is passed; an empty tool list gives zero protection against hooks or agent-file shadowing, because both operate at a layer `--tools` does not gate | **FIXED** — AC-02's ceiling sub-bullet now requires, for BOTH role classes: `--setting-sources user` MANDATORY on every spawn (verified the real flag and exact wording via `claude --help`: "Comma-separated list of setting sources to load (user, project, local)"); spawn cwd is the repository root with `--add-dir` NEVER passed (verified `git rev-parse --show-toplevel` resolves to the repo root, `/home/federico/SET-AGENTES`, genuinely distinct from `$HOME`); an explicit note against `--bare` (verified exact wording: breaks OAuth entirely, "OAuth and keychain are never read") or `--safe-mode` (verified exact wording: disables "custom commands and agents", breaking `--agent <role>`); `## Verificación`'s CLI-ceiling-argv test extended to assert `--setting-sources user` present and `--add-dir` absent from every AC-02-composed argv |
| R3-02 | Blocking, evidence correction | Round 2's live-tested claim that `--model fable` and `--model opus` resolve to the same canonical model was WRONG — round 3 re-reproduced live this session: `fable`→`modelUsage.canonicalModel: "claude-fable-5"`, `opus`→`"claude-opus-5"`, genuinely distinct models, corroborated independently by `claude --help`'s own `--model` documentation pairing the `fable` alias with the `claude-fable-5` example | **FIXED, closed together with R3-03 via user decision 1** — `## Contexto` §G-bis rewritten to state the real, reproduced result; the false "structurally impossible to fully eliminate" claim retracted, replaced with "full elimination WAS achieved"; `catalog.py`'s `_ANTHROPIC_CANONICAL_EXTRA = {"fable": "claude-fable-5"}` (`catalog.py:86`) confirmed CORRECT, not stale — AC-07's now-incorrect staleness flag withdrawn; round-2 Historial's R2-04 row annotated with this correction |
| R3-03 | Blocking, new collision found | Round 2's chosen fix value `"sonnet"` for `[areas.audit].claude`/`[areas.judge].claude` (AC-06(b)) would have collided with `[areas.implement].claude` (also `"sonnet"`, `models.toml:81`) — a new BASE-implementer collision round 2 did not check for | **FIXED, closed together with R3-02 via user decision 1** — AC-06(b) now uses `"fable"` instead of `"sonnet"`, which collides with nothing: not the three curated anthropic route models, not `[areas.implement].claude`, not any other `[areas.*]`/`[roles.*].claude` value (verified exhaustively this session via `grep -n 'claude = ' models.toml`, every real value on this tree is one of `{sonnet, haiku, opus}`, never `fable`); AC-06's regression test (ii) rebuilt generically off the live `models.toml`/`routes.v1.toml` tables (round 3's own recommendation), not hardcoded strings; AC-05's balanced-tier residual withdrawn |
| R3-04 | Medium | Review-class roles have no Bash (`--tools "Read,Grep,Glob"`), so they cannot run `git diff`/gate commands to see what they are reviewing — AC-02 never stated who supplies the diff | **FIXED** — user decision 2: the orchestrator (or whichever caller invokes AC-02's spawn primitive) supplies the diff/relevant content directly, as a file the reviewer's `Read` tool can access (within the cwd write-containment boundary) or embedded in the task/prompt delivered via stdin — stated as a real requirement on AC-02's calling contract, not just a narrowing note; a new `## Verificación` check asserts the task/prompt or provided-file payload actually contains the diff content; AC-04(a)'s end-to-end test extended to confirm the diff payload reaches the reviewer this way, not only which branch/primitive fires |
| R3-05 | Medium | Redirect-trigger granularity ambiguity: AC-01 is phrased at pair granularity ("the requested pair is unauthenticated") but the actual code check (`service.py:145`) operates at MODEL granularity — a pi-hosted decision for a model NOT in pi's own live-probed anthropic list could get incorrectly redirected to `claude-code`, violating the pi-lane Non-goal | **FIXED** — AC-01 now states explicitly the redirect fires ONLY if the requested `(runtime, provider)` pair has NO inventory entry AT ALL (pair-level presence check); a present-but-model-incomplete pair still correctly excludes via the existing `PROVIDER_UNAUTHENTICATED` path, unchanged, never triggering a cross-lane redirect; a new, discriminating fourth test fixture added (`inventory[("pi","anthropic")] = {"haiku"}` only, a frontier-tier decision requiring a different anthropic model, `selected_runtime="pi"` → must NOT redirect) |
| R3-06 | Low | Wrong site count, second time: the spec said "six" `facts.selected_runtime` sites in three places, but a fresh grep found EIGHT real occurrences (excluding `:128`'s `request.selected_runtime` conflict check, which AC-01 leaves untouched) | **FIXED** — re-verified live this session (`grep -n "selected_runtime" service.py`): eight occurrences at `:137,144,145,195,200,201,206,208`, `:128` correctly excluded (it reads `request.selected_runtime`, a different field, for the unrelated conflict check AC-01 does not touch); every prose occurrence corrected (`## Contexto` §D, Non-goals, AC-01's own UNVERIFIED tag, the Audit pairwise-conflict-pass bullet) — per round 3's own recommendation, the numeral is dropped where practical in favor of citing the list directly, to avoid a third miscount |
| R3-07 | Low | (a) `## Verificación` has no line for AC-08 despite it being a delivery criterion; (b) `## Alcance`'s AC-04 bullet and AC-04's own heading say the review-independence gap "is closed" with no time-box qualifier, unlike every other mention (a propagation miss from the round-2 fix) | **FIXED** — (a) `## Verificación` now includes "AC-08's ADR file exists and records items (a)-(e)"; (b) both `## Alcance`'s AC-04 bullet and AC-04's own heading now read "closed for the ~12-day two-provider window (see `## Origen`)", matching `## Origen`/§E/Non-goals/AC-04(b)'s existing time-box qualifier |

**This is the final revision pass before user approval.** Per round 3's own explicit recommendation, no
further adversarial round is planned once R3-01 through R3-07 land, as they do above; this file's own status
line states the intended verdict as `ready_for_user_approval`, pending the user's own final sign-off, not a
further spec-challenge cycle.
