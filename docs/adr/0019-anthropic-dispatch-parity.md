# ADR-0019 — Anthropic dispatch parity: the Claude-Code-lane redirect, its tool ceiling, and the day-13 boundary

- Estado: Accepted (2026-08-01). Feature `015-anthropic-dispatch-parity`, package
  `P1-anthropic-dispatch-parity` (contract 3.1.0, three spec-challenge rounds; approved by the user
  2026-07-31). Supersedes contract 1.0.0's own never-materialized planned ADR (`## Contexto` §F of the
  spec: 1.0.0 planned OpenCode-lane Anthropic tier-variant files; that design was replaced entirely, not
  amended, once the user reported OpenCode can only authenticate Anthropic via a metered API key, never
  the real OAuth subscription).
- Context: `ai/scripts/routing_core/service.py` (`_effective_runtime`, the exclusion loop),
  `ai/scripts/claude_code_spawn.py` (new file), `Global/_canonical/agents/orchestrator.md` ("Tiered
  dispatch" section), `models.toml` (`[areas.audit]`/`[areas.judge]`), `docs/adr/0007-pi-lane.md`
  (structural precedent, spawner lifecycle shape), `docs/adr/0011-uninterrupted-delegation.md` D4
  (halt rule — preserved here, not relaxed).

## Contexto

The user runs two ~$100/month subscriptions, Anthropic (Claude) and OpenAI (GPT). In roughly twelve days
from this package's delivery the OpenAI subscription drops (replaced by an unrelated, cheaper product,
out of this contract's scope). Once that happens `anthropic` becomes the harness's sole
enabled-and-authenticated provider — a certain, scheduled event, not a hypothetical outage.

Before this package, every tiered routing decision was evaluated with `facts.selected_runtime ==
"opencode"` unconditionally (the orchestrator's own descriptor never named `selected_runtime`, and
`cmd_route_decide` defaults it to `"opencode"`), and OpenCode's own credential store can only
authenticate Anthropic via a metered API key — never the user's real OAuth subscription. The practical
effect, live-verified on this machine before the fix: every `anthropic` candidate was excluded via
`PROVIDER_UNAUTHENTICATED` on every decision, so every package review following an `openai-codex` writer
already hard-halted with `REVIEWER_INDEPENDENCE_UNAVAILABLE` — a severe but fail-closed defect (blocks
throughput, does not silently degrade safety), not the fail-open "silently defeated independence" a
first draft of this contract mischaracterized it as.

Claude Code itself, however, already authenticates against Anthropic via OAuth against the user's real
subscription — this very orchestrator session runs as Claude Code, right now, using exactly that OAuth
path. The user chose explicitly: redirect delegation to Claude Code when a routed decision resolves to
`anthropic`, rather than trying to make OpenCode itself spawn Anthropic-backed agents (which would incur
new, unapproved, per-token metered cost on top of a subscription already paid for).

This ADR records that redirect design, its security posture, and its known, time-boxed limitation.

## Decisión

### D1 — A provider-scoped, pair-conditional runtime redirect, never a lane override

`RoutingService._effective_runtime(runtime, provider)` (`service.py`) resolves a route's identity/auth
against an **effective runtime** — the requested `facts.selected_runtime` unchanged for every provider
without a configured redirect (byte-identical behavior for `openai-codex`), or the one configured
alternate (`anthropic` → `claude-code`) for a provider that has one. The redirect is a closed,
single-entry map (`_PROVIDER_RUNTIME_REDIRECTS = {"anthropic": "claude-code"}`), deliberately not
generalized to a config table or extended to other providers — extending it is explicitly future,
separately-scoped work, not silently opened here.

The redirect fires **only** when the REQUESTED `(runtime, provider)` pair has no inventory entry AT ALL
— a pair-level PRESENCE check, never per-model completeness. This is the one requirement that keeps
this contract's own Non-goal true in code, not merely in prose: an already-authenticated
`("pi","anthropic")` decision (`013-pi-interactive-target`'s own accepted tiering story) is never
redirected away from `pi`, and a pi-hosted decision for a model genuinely absent from pi's own live-probed
list (a present-but-incomplete pair) stays excluded via the ordinary `PROVIDER_UNAUTHENTICATED` path,
never silently jumping to `claude-code` just because that lane happens to carry the missing model. Four
hermetic fixtures prove all four shapes against a live-machine-shaped inventory (no
`("opencode","anthropic")` key at all — the shape that would otherwise fool a looser fixture):
no-redirect-target-credential still hard-halts; pair-absent redirects; an already-authenticated `pi` pair
is never redirected; a present-but-incomplete `pi` pair stays excluded, never redirected.

The resolved effective runtime is what the persisted `RouteDecision.runtime` field reports (the existing
wire field, no new one added) — a decision that will actually execute on the Claude-Code lane says so in
its own audit trail, not the merely-requested lane.

Rejected: an unconditional `[runtime.redirects]` table or a closed code constant applied regardless of
the requested lane's own auth state. Both are provider-scoped but lane-blind, and would redirect a
`pi`-hosted `anthropic` decision away from its own already-working lane — silently breaking the `pi`
Non-goal.

### D2 — No OpenCode-lane Anthropic artifacts; the catalog/snapshot layer needed zero change

Contract 1.0.0 planned new `<role>@<tier>` OpenCode-lane Anthropic tier-variant files. This design adds
none: `build_snapshot`'s existing identity computation (`catalog.py:565-567`) already admits
`(route_id, "claude-code", "anthropic", ...)` for all three curated anthropic routes, because none of
them declares an optional `runtimes` catalog key — the identity is valid under every runtime
`_PAIR_COMMANDS` audits for that provider, already, with zero catalog change. `Snapshot.identity_allowed`
already accepted this identity before this package began. `catalog.py`, `routes.v1.toml`,
`set_agents_spawn.py`, and `models_config.py`'s tier schema are read-only reference for this package —
verified, not merely asserted, by a regression test walking `build_snapshot`'s output directly.
`_opencode_projected_route`'s existing docstring ("the only routes.v1.toml provider reachable from the
OpenCode lane — anthropic runs through claude-code, not OpenCode") was correct all along and needed no
amendment.

### D3 — A new, separate spawn module; lifecycle SHAPE reused from the Pi lane, never its function body

`ai/scripts/claude_code_spawn.py` is a new module, never a call into `set_agents_spawn.route_and_spawn`
— it reuses that module's lifecycle SHAPE (decide→dispatch→spawn→terminal for writers; the "AC-11
refusal path" of doing zero bookkeeping for review-class decisions, `set_agents_spawn.py:374-377`) as
structural precedent only, per ADR-0007's own pi-lane pattern (a CLI subprocess is needed because
neither OpenCode nor Claude Code has an in-process mechanism to spawn a child hosted under a *different*
CLI). The two dispatch functions are asymmetric by design:

- `dispatch_writer` CONSUMES an already-authorized `run_id` from the caller's own prior `--route-decide`
  call — it never calls `--route-decide` itself, and never re-authorizes. A second decide call would burn
  a second one-use `single_writer` authorization (`models.toml:48`) for one actual spawn; this module's
  interface makes that structurally unreachable rather than merely documenting it as a rule to follow.
- `dispatch_review` gets NO run/usage bookkeeping through the routing store at all — review decisions
  have `execution_enabled=false`/`run_id=None` by construction, on every lane, today; this is not a
  regression introduced here.

Invocation: `claude --print --agent <role> --model <catalog-short-name> --output-format json
--no-session-persistence --setting-sources user --tools <ceiling> [--permission-mode acceptEdits]`, task
delivered via **stdin**, never a trailing positional (a positional prompt after a variadic `--tools` flag
is silently swallowed into the flag's own token list — live-reproduced during the spec-challenge session
before the fix, `Error: Input must be provided either through stdin or as a prompt argument`). cwd is
always the repository root; `--add-dir` is never composed.

Rejected: extending `set_agents_spawn.route_and_spawn` itself for this lane. That function's own decision
shape assumes a writer-only, always-bookkept lifecycle and explicitly refuses to open a session for a
review decision — extending it would have required either weakening that refusal (reopening the risk
`route_and_spawn`'s "AC-11 refusal path" exists to close) or bolting a second, incompatible lifecycle
branch onto an already-accepted, narrowly-scoped file outside this package's owned paths.

### D4 — The CLI-level tool ceiling: a DECIDED security control, never frontmatter-trusted

A headless `claude --print --agent <code-rw-role>` spawn, live-tested during this contract's own
spec-challenge, executed an arbitrary Bash command with `permission_denials: []` — no interactive human
exists in `--print` mode to answer the permission prompt the same tool call would raise interactively,
and the `PreToolUse` guard-hook path that is supposed to gate Bash falls through to ALLOW, not DENY, when
nothing answers it (R2-03).

Decision: mirror the pi-lane's already-accepted strict posture (`set_agents_spawn.py:70,332-335` hardcodes
`GUARD_TOOLS_READONLY` with no `guard_tools` parameter at all, so a code-rw child is never reachable
through that routed entry point). `claude_code_spawn.py`'s tool ceiling is enforced at the CLI level —
`--tools`, a real, live-verified argv flag that removes a tool from the session entirely (a strictly
stronger guarantee than a hook, which can fail open) — never derived from, or overridable by, a role's
own installed frontmatter:

- **Review-class** (`review-ro`/`audit`|`judge` duty): `--tools "Read,Grep,Glob"`, no `--permission-mode`.
  Live-proven to hold even against a `code-rw` role's own, more permissive frontmatter, and even absent
  any `hooks:` block: the tool is categorically absent from the session, and the spawned model's own reply
  confirmed it ("I only have Read, Grep, and Glob... There is no Bash execution tool in my current
  toolset.").
- **Writer-class** (`code-rw`, cross-lane-redirect dispatch only): `--tools
  "Read,Grep,Glob,Edit,Write" --permission-mode acceptEdits`. `Bash` is categorically excluded — the
  proven arbitrary-execution vector — never granted through this mechanism under any parameter. This
  grants real, controlled file writes (the role's actual job) but explicitly **not** the roster's normal
  `code-rw` capability set (`Edit, Write, Bash`, `generate.py:255`): `implementer`/`debugger` dispatched
  cross-lane through this mechanism CANNOT run Bash-based local validation (tests, build, `verify.sh`)
  within the same spawn — a real, named, narrower guarantee than "full code-rw", not a bug. A bare
  `--tools "...,Edit,Write"` without `--permission-mode acceptEdits` was live-tested and found
  insufficient on its own (Write denied, `permission_denials` populated) — Edit/Write go through Claude
  Code's own native, file-path-bounded permission path, which (unlike the Bash guard-hook path) defaults
  to DENY, not ALLOW, in headless mode.

Rejected: `--bare` (forces `ANTHROPIC_API_KEY`-only auth, defeating this whole contract's cost rationale
of reusing the user's real OAuth subscription) and `--safe-mode` (disables custom agents outright,
breaking `--agent <role>` itself, the mechanism this module depends on). Rejected: `--permission-mode
plan` as a "safer-looking" default — live-tested and found to break headless execution outright
(`error_during_execution` the instant any tool is invoked, no headless exit path).

### D5 — A second, deeper containment gap one hop past the tool ceiling: `--setting-sources user`

A tool ceiling alone (`--tools ""` or the narrower allowlists above) gives **zero** protection against a
project-scope `.claude/settings.json` `SessionStart`/`PreToolUse` hook, or a project-scope
`.claude/agents/<role>.md` file (which can itself carry a `PreToolUse` hook — this repo's own
`generate.py:258-279` `frontmatter_hook` already generates exactly this shape for hooked capabilities,
confirming the pattern is real on this tree, not hypothetical) — both operate at a layer `--tools` does
not gate, and both can execute arbitrary shell or substitute the role prompt entirely, even with an empty
tool list. This was found and closed during the same spec-challenge round that produced the tool-ceiling
design above (R3-01), one round after the tool ceiling itself was believed sufficient.

Decision, mandatory on every spawn, both role classes, no exception:

1. `--setting-sources user` — live-verified real flag and wording (`claude --help`: "Comma-separated list
   of setting sources to load (user, project, local)"). `user` alone means project-scope
   `.claude/settings.json` hooks never load and project-scope `.claude/agents/<role>.md` files are
   ignored, while installed USER-scope agents remain resolvable, so `--agent <role>` still works exactly
   as this mechanism needs.
2. cwd is always the repository root, and `--add-dir` is never composed — the write-containment boundary
   this whole mechanism relies on. Live-confirmed `git rev-parse --show-toplevel` resolves to the repo
   root, genuinely distinct from `$HOME`, so this boundary genuinely excludes `~/.claude/**`, where a
   shadowing agent/settings file could otherwise be planted.

**Residual, recorded rather than fixed (`ai/state/decisions-log.jsonl`, slug
`setting-sources-user-confía-en-scope-generado-desde-el-propio-repo`, logged 2026-08-01, an
implementation-time security-checkpoint finding, closed as "record, don't fix"):** `--setting-sources
user` trusts `~/.claude/**`, which `build.sh --install` populates from `Global/claude-code/**` of this
same repository. A writer-class spawn (bounded by its own cwd containment) can legitimately edit those
source files, and the next `--install` promotes them into the trusted scope. This is not a new privilege
— an interactive implementer can already edit `Global/**` today, and the promotion path is governed by
`check-owned-paths.py` — but the mitigation above reads as absolute if left implicit, and it is not: it
closes the project/local-scope shadowing vector, not a hypothetical where the repo's own generated output
is itself compromised through an unrelated path.

### D6 — The calling contract for a Bash-less review-class spawn: the caller supplies the diff

A review-class spawn has no Bash and cannot run `git diff`/gate commands to see what it is reviewing.
Decision (user decision 2, round 3 of this contract's spec-challenge, R3-04): the CALLER invoking
`dispatch_review` — the orchestrator's own doctrine, per D7 below — is responsible for supplying the
diff/relevant review content directly, via `compose_task`'s `supplementary` parameter (the CLI's own
`--supplementary <FILE|->` flag) — a real path (inside the cwd write-containment boundary, real content the
reviewer's `Read` tool can also reach) or `-` for stdin. **`supplementary` is the SOLE channel for content
under review; `task` carries harness instruction only, and content originating from the artifact under
review must never be placed there** (015 repair, panel RP-01, SEC-P1-001: an earlier draft of this doctrine
also offered "or embedded directly in the task text" as an alternative — since `task` carries no
nonce-fencing at all, that alternative defeated the injection protection below entirely whenever a caller
took it, which the orchestrator's own read-only, file-write-incapable posture made the realistic path; that
alternative is struck, with no replacement, from both this ADR and the generated doctrine). `content` is
wrapped in a per-call random nonce delimiter (`secrets.token_hex`, never a fixed public string — SEC-004
below) explicitly marking it as untrusted, caller-supplied data under review, never instruction. A
review-class spawn invoked without real `supplementary` content is a caller defect, not something the spawn
primitive itself can detect or repair — the end-to-end regression test for this shape asserts the real diff
content reaches the composed stdin payload, not merely that dispatch mechanics fire, per a round-3 finding
that an earlier draft's test only checked which branch fired, PLUS a doctrine-consistency test asserting the
struck alternative-channel phrasing is absent from every generated harness copy and that `supplementary`/
`--supplementary` is named as the sole channel in each.

### D7 — Doctrine: same-lane / cross-lane-redirect / true-off-lane, self-aware of its own host harness

`Global/_canonical/agents/orchestrator.md`'s "Tiered dispatch" section now branches on `data.runtime`
(already present on every decision, D1 above) before choosing a spawn mechanism: **same-lane**
(`data.runtime` equals the orchestrator's own host harness, whatever it currently is — a
runtime-agnostic check, never hardcoded to `"opencode"`, since this very orchestrator session may itself
be Claude-Code-hosted); **cross-lane redirect** (`data.runtime == "claude-code"` and the host harness is
not — spawn via `claude_code_spawn.py`'s `dispatch_writer`/`dispatch_review`, using the BASE
`.claude/agents/<role>.md` file with `--model data.model`, never a new tier-variant file); **true
off-lane** (neither — not reachable on today's two-provider/two-lane catalog, but the doctrine does not
assume it stays that way — a legitimate degrade to the BASE static agent, generalized past the previous
single hardcoded `"openai-codex"` string check). The doctrine's own regression test
(`tests/test_harness.py::test_orchestrator_doctrine_branches_on_route_decide_reason_taxonomy`) iterates
every generated harness copy that exists, discovered generically rather than a hardcoded three-tuple, so
a fourth copy (`Global/pi/...`, once `013-pi-interactive-target` lands) is covered automatically rather
than silently dropped from coverage.

The everyday verified-review shape (`ok=true`, `reason_codes=()`, `execution_enabled=false`,
`independence_verified=true`) is a new, explicit, non-degrade branch — it spawns the matching artifact via
the same same-lane/cross-lane rule, never the BASE reviewer by default. The existing benign
`REVIEW_IDENTITY_UNVERIFIED` shape (no `review_of_run_id` offered) is untouched, and its OpenAI-only
static exposure remains a named, accepted residual (D9 below).

**Residual, recorded rather than fixed (`ai/state/decisions-log.jsonl`, slug
`redirect-de-effective-runtime-es-silencioso-sin-reason-code`, logged 2026-08-01, an
implementation-time security-checkpoint finding, closed as "record, don't fix"):** `_effective_runtime`
redirects silently — no dedicated `reason_code` or `exclusions` entry names that a redirect happened; the
only observable trace is the `RouteDecision.runtime` field itself reporting the effective, not requested,
lane. This is not a vulnerability (the audit trail is truthful, just not maximally legible), but a future
observability pass should consider emitting an explicit signal when a decision's effective runtime
diverges from its requested one, rather than requiring a reader to notice the divergence by comparing two
fields.

### D8 — `fable`, not `sonnet`, closes the `.claude`-axis same-model collision with zero residual

Once the Claude-Code lane became a real dispatch target (D1-D3), `[areas.audit].claude`/
`[areas.judge].claude` (both `"opus"`) collided with the anthropic-frontier route's curated `"opus"`
model: a frontier-tier writer redirected to `anthropic`/`opus` could be paired, on an unverified review,
with a BASE audit/judge reviewer whose static default was also `opus` — same provider, same model,
exactly the bar `ADR-0011` D3 states is "not accepted while an alternative exists".

An earlier pass of this contract's own spec-challenge chose `"sonnet"` as the fix, on the strength of a
live test reported as showing `fable` and `opus` resolve to the identical canonical model. A later
adversarial round re-reproduced that exact test and found the earlier result **wrong**: `--model fable`
resolves to `modelUsage.canonicalModel: "claude-fable-5"`; `--model opus` resolves to `"claude-opus-5"` —
genuinely distinct, corroborated independently by `claude --help`'s own worked example pairing the
`fable` alias with the `claude-fable-5` full name. `"sonnet"` would in fact have introduced a NEW
collision, with `[areas.implement].claude` (also `"sonnet"`) — a BASE-implementer collision the earlier
pass never checked for.

Decision: `[areas.audit].claude`/`[areas.judge].claude` are `"fable"` (`models.toml:93,99` at the time of
this ADR). `"fable"` collides with nothing on this tree: not the three curated anthropic route models
(`haiku`@fast, `sonnet`@balanced, `opus`@frontier), not `[areas.implement].claude`, and not any other
`[areas.*]`/`[roles.*].claude` value — a full elimination, not a highest-severity-pairing reduction. A
regression test builds this claim generically off the live `models.toml`/`routes.v1.toml` tables (never
hardcoded strings), so a future re-tiering of any anthropic route, or a future new area/role `.claude`
default, is caught too.

A second, unrelated, pre-existing same-provider-and-same-model collision — `[areas.audit].opencode."go-zen"`
(also colliding with `[roles.implementer.tiers.balanced].opencode."go-zen"`, both `"openai/gpt-5.6-sol"`)
— is fixed the same values-only way, realigned to `"openai/gpt-5.5"` (matching `[areas.audit]`'s own
zen/local lanes), collision-free against every implement-duty role's tiered ladder.

**F-02 (015 repair, panel RP-01): the `[areas.judge]` residual named below is now CLOSED, not merely
accepted — superseding the original text of this section.** An earlier pass of this ADR recorded
`[areas.judge].opencode."go-zen"` (identical `"openai/gpt-5.6-sol"`, the same latent collision class) as a
deliberate, out-of-scope residual, reasoning the approved Non-goals named only two `models.toml` cells. The
package review panel found the test proving AC-06(a)'s own regression coverage used TWO narrowed universes
at once — area-side to `[areas.audit]` alone, and role-side to `models_config.IMPLEMENT_DUTIES`, which
misses the four AUDIT-duty tiered roles (`package-reviewer`, `delta-reviewer`, `security-auditor`,
`finding-verifier`) entirely — an internal inconsistency against AC-06(i)'s own spec wording ("generic over
ALL `[areas.*]` cells vs ALL tiered roles"). The user was asked and chose explicitly: widen AC-06(a) to fix
`[areas.judge].opencode."go-zen"` too, the identical one-value fix pattern, now also `"openai/gpt-5.5"`
(`models.toml:115` at the time of this repair) — collision-free against every tiered role's ladder,
regardless of duty. The regression test is rebuilt exactly as originally specified: generic over every
`[areas.*].opencode."go-zen"` cell and every role carrying a `tiers` table, no duty filter.

**F-03 (015 repair, round 2): the `[areas.ops]` residual named below is now CLOSED too, in the same
repair session — superseding the paragraph immediately below.** That same widened, generic scan surfaced a
THIRD, previously undiscovered instance of the SAME collision class: `[areas.ops].opencode."go-zen"` was
`"openai/gpt-5.6-terra"`, identical to the frontier-tier value of the same six-role tiered ladder. It was
new information discovered mid-repair, not covered by the user's F-02 decision (scoped explicitly to
`[areas.judge]`), so the repair pass correctly did not fix it unilaterally — it was named as an explicit
residual (asserted in the regression test, not silently passed) and reported to the orchestrator/user as
its own pending decision, via a companion decisions-log entry. The user then explicitly approved closing
it, same pattern as audit/judge. Realigned to `"openai/gpt-5.4-mini"` (`models.toml:141` at the time of
this repair) — matching `[areas.ops]`'s own zen/local lanes AND its sibling operational areas
(`[areas.gate]`, `[areas.release]`, `[areas.memory]`, which share this area's `claude`/`codex`/
`codex_effort` triplet and already used this exact go-zen value) — collision-free against every tiered
role's ladder (every tiered value is one of luna/sol/terra, never `gpt-5.4-mini`). The regression test now
asserts the invariant is genuinely, fully closed: `colliding_sites == set()`, no named exception anywhere.

Original text, preserved for the historical record (now superseded by F-03 above): "New residual surfaced
by that same widened, generic scan, named — not fixed — here: `[areas.ops].opencode."go-zen"` is
`"openai/gpt-5.6-terra"`, identical to the frontier-tier value of the same six-role tiered ladder — the SAME
collision class, on a THIRD cell nobody had named until this repair's own generic test found it. This is
new information discovered mid-repair, not covered by the user's F-02 decision (scoped explicitly to
`[areas.judge]`) or by any of this package's other findings — widening to fix it would have been an
unapproved scope expansion by the repair pass itself. Named here, in the regression test (which asserts
this exact, single residual, not a silent pass), and via a companion decisions-log entry, as a residual for
the orchestrator/user to decide on explicitly, not silently left undocumented and not silently fixed
without authorization."

### D9 — What this contract does not fix: the benign review path, and the day-13 halt

`REVIEW_IDENTITY_UNVERIFIED` (no `review_of_run_id` offered) still spawns the BASE reviewer/judge, whose
static OpenCode-lane default is `openai/…` on every profile, never `anthropic` — unchanged from before
this contract, `ADR-0003`'s seam, not fixed here.

More importantly: **`REVIEWER_INDEPENDENCE_UNAVAILABLE` still halts, in every runtime, unchanged — `ADR-0011`
D4 is preserved, not relaxed.** Once the OpenAI subscription drops (day 13), `anthropic` becomes the sole
authenticated provider on any lane this contract wires up, and `REVIEW_PROVIDER_CONFLICT` excludes it from
serving as a reviewer's provider on every decision whose writer also resolved to `anthropic` — there is no
remaining second provider to pick a reviewer from. Automatic review-independence correctly pauses from that
day forward (a human reviews manually) until a real second provider exists (a different, future,
not-yet-scoped feature). This is a certain, scheduled, honestly-framed limitation — not a hypothetical
outage, and not a defect this contract silently leaves behind.

A regression test proves this is real, not merely asserted: the PRIMARY fixture is the non-vacuous day-13
shape — `anthropic` authenticated (via the `claude-code` redirect), `openai-codex` NOT authenticated
anywhere, a writer decision that genuinely goes THROUGH the D1 redirect (proving the redirect fired, not
merely assumed) — and the reviewer still correctly halts with `REVIEWER_INDEPENDENCE_UNAVAILABLE`, never
silently redirected to a same-provider-same-model reviewer on `claude-code`. An earlier draft of this test
used a fully-empty inventory, which halts trivially and proves nothing about whether the redirect itself
weakened the invariant; that case is kept as a secondary assertion only.

## Scale / Data / Security decisions

This package touches auth/authorization (review-independence) and untrusted-code-execution containment
(a headless Bash-capable CLI spawn vector). No data migration, money, or identity path is touched. The
security posture is: (1) Bash is categorically excluded from every composed argv, both role classes, no
parameter widens it (mirrors `set_agents_spawn.py`'s own SEC-A02 precedent); (2) the tool ceiling is
enforced at the CLI level, never derived from or overridable by a role's installed frontmatter (D4); (3)
`--setting-sources user` plus cwd containment close the deeper hook/agent-file-shadowing vector one hop
past the tool ceiling (D5), with its own residual named rather than left implicit; (4)
`ADR-0011` D4's halt rule is verified, by a non-vacuous regression fixture, to still hold under the exact
shape this contract's own redirect produces (D9). Six implementation-time findings from this package's own
security checkpoint (before AC-03/AC-04 doctrine wiring proceeded, per the package's own early-checkpoint
gate) are closed in `claude_code_spawn.py` itself, cited inline at their fix sites: **SEC-001** (a
deny-by-default role-class binding, checked first in both `dispatch_writer`/`dispatch_review` and as a
second, independent guard inside `spawn()` itself via `expect_class`, so a future third caller cannot
enter the wrong door either); **SEC-002** (a purely observational audit-trail log of the actual
decision-to-spawn binding used, so a future divergence from the authorizing `--route-decide` envelope is
at least detectable after the fact); **SEC-003** (`compose_argv`'s `tools`/`permission_mode` validated as
an ALLOWLIST of exactly the two known-good ceilings, never a denylist of known-bad flags — closing a gap
where an arbitrary `tools` string, an arbitrary `permission_mode` including `bypassPermissions`, or a
leading-dash role/model token composed cleanly before this fix); **SEC-004** (the `supplementary`
delimiter is a per-call random nonce, never a fixed public string, so untrusted diff content cannot forge
a boundary and escape into apparent harness instruction — D6 above); **SEC-005** (`dispatch_writer`'s own
`spawn_cwd` containment check runs BEFORE the routing store's one-use authorization is ever touched, not
merely downstream at the child-spawn step); **SEC-006** (the child subprocess's text encoding is pinned
explicitly to UTF-8 with `errors="replace"`, rather than left to the platform's preferred locale encoding,
since this repo's own diffs/docs are routinely non-ASCII).

## Consecuencias

- The review-independence gap this contract closes is real for the ~12-day window while two providers
  remain authenticated, and correctly, honestly stops being closeable from day 13 onward — a known,
  time-boxed, documented limitation, not a permanent fix.
- A cross-lane-dispatched writer (`implementer`/`debugger`) gets a real but narrower capability than
  normal `code-rw`: no Bash, no local validation inside that spawn. Any future doctrine or
  package-planning decision that assumes otherwise is wrong and must route local validation through a
  different, already-existing mechanism.
- No new provider, catalog entry, or `routes.v1.toml` row was added; the redirect and spawn mechanism are
  confined to `service.py`'s auth-check sites, a new spawn module, doctrine text, and two values-only
  `models.toml` cells — `catalog.py` needed, and got, zero diff.
- Two residuals are recorded rather than fixed, each named above at its own decision and cross-referenced
  in `ai/state/decisions-log.jsonl`: the silent (`reason_code`-less) redirect trace (D7) and the
  `~/.claude/**` trust-scope-generated-from-this-repo caveat on `--setting-sources user` (D5). The
  `[areas.judge]` and, later in the same repair session, `[areas.ops]` `opencode."go-zen"` collision twins
  named in D8 were both fixed values-only within this repair (F-02, F-03) — not left as residuals.
- `011-quota-failover`'s current scope stays pi-only; this package's own Claude-Code-lane subprocess can
  also observe a real anthropic-exhaustion error/usage payload but does not record it as a quota-failover
  signal anywhere — a separate, future, not-yet-scoped widening of `011` itself.

### Repairs outside the state machine (review panel RP-01, PACKAGE_REPAIR)

- **The "or embedded directly in the task text" alternative channel is struck (SEC-P1-001, CRITICAL).** D6
  above is amended in place — see its current text. The prior wording offered two channels for review
  content, only one (`supplementary`) nonce-fenced; since the orchestrator cannot write files, the unfenced
  channel was the realistic path, and it defeated SEC-004's injection protection outright. `supplementary`
  is now stated as the sole channel, in this ADR and in the generated doctrine, with a regression test
  asserting the struck phrasing is absent from every generated harness copy.
- **`claude_code_spawn.py` gains a real, narrow CLI entry point (SEC-P1-002, CRITICAL).** D3's module had no
  `argparse`/`__main__` at all — the doctrine mandated calling `dispatch_writer`/`dispatch_review` with no
  approved way to actually invoke them from the orchestrator's deny-by-default Bash. `main()` now exposes
  exactly `--dispatch-writer`/`--dispatch-review` with an exhaustively enumerated flag grammar (no free-form
  passthrough). Closing this gap required TWO paired changes, one per harness's own permission surface —
  **not** the single `coord_policy.SAFE_ARGV` change the round-1 repair made alone (see DR-01 below, which
  reopened this finding as CRITICAL after that gap was found): `coord_policy.SAFE_ARGV` gains a matching
  entry (the `--context` precedent's `modifiers`-enumerated form) for the **Claude-Code lane**, whose Bash
  policy IS `coord_policy.py`; and `generate.py`'s `oc_permissions` (the function that emits the `bash:`
  permission map baked into `Global/opencode/agents/orchestrator.md`) gains two matching allow-lines,
  enumerated per `claude_code_spawn.main()`'s own two modes, for the **OpenCode lane** — the lane whose own
  Bash policy is generated separately and was never touched by the round-1 repair, and the lane the
  cross-lane-redirect doctrine branch actually fires from today (D7). `--task`/`--supplementary` both take a
  `FILE|-` value (the same convention `--route-decide` already uses) — the untrusted content itself never
  becomes a shell-quoted argv token.
- **The SEC-002 audit-trail log is now durably persisted, not merely logged (SEC-P1-003, MEDIUM).**
  `logging.getLogger(__name__).info(...)` was never actually emitted — no handler is configured anywhere in
  this repo, so the record was silently dropped at Python's default WARNING threshold, the only compensating
  control `dispatch_writer` names for a binding it says it cannot structurally enforce. The binding
  (`run_id`/`role`/`provider`/`model`) is now also appended as a JSONL line under the routing store's own
  0700-permissioned directory, independent of `logging` configuration.
- **F-01 (HIGH): `model_mismatch` classification used the wrong lane's alias table.** `_classify_result`
  compared against `routing_core.catalog.canonical_model`, built from `PI_MODEL_MAP` — the Pi CLI's own
  curation, not Claude Code's. Live-verified: `claude --print --model opus ...` resolves to
  `canonicalModel: "claude-opus-5"`; `PI_MODEL_MAP["anthropic"]["opus"]` is `"claude-opus-4-8"` — a real,
  different model, not a naming skew. Every real frontier-tier spawn was misclassified as `model_mismatch`,
  discarding `dispatch_review`'s real verdict. `claude_code_spawn.py` now carries its own, lane-scoped,
  independently-curated `CLAUDE_CODE_CANONICAL_MODEL` table (live-verified this session for `haiku`/
  `sonnet`/`opus`/`fable`), never falling back to `PI_MODEL_MAP`/`catalog.canonical_model`. `--model` itself
  keeps composing the catalog short name verbatim (AC-02's own literal spec text); only the classification
  lookup changed. Composing the fully-qualified canonical id directly as `--model` instead (also
  live-verified to resolve unambiguously) was considered and rejected — it would diverge from AC-02's own
  approved argv text for no gain over fixing the lookup table alone.
- **F-03 (MEDIUM): the redirect could fire for a genuinely absent `("pi","anthropic")` pair.** D1's
  pair-presence check alone would have redirected a `pi`-requested decision to `claude-code` whenever that
  pair was wholly absent from inventory — but `set_agents_spawn.route_and_spawn` (the real `pi`-lane
  spawner) never reads `RouteDecision.runtime` and always spawns on `pi` regardless, converting a
  fail-closed `NO_ELIGIBLE_ROUTE` into a fail-open authorization executed on the wrong lane.
  `_effective_runtime` now also checks a `_NEVER_REDIRECT_FROM_RUNTIMES = {"pi"}` exemption — `pi` never
  redirects as a requested lane, regardless of pair presence/absence, superseding the pair-presence check
  alone for this one lane.
- **F-04 (MEDIUM): the same-lane doctrine action was OpenCode-shaped under a runtime-agnostic condition.**
  The same-lane branch's condition already checked "the orchestrator's own host harness, whatever it
  currently is" — but its action still said "spawn the matching `<role>@<tier>` variant," and Claude
  Code/Codex have zero `@tier` files. The action now states the fallback explicitly: the tier-variant where
  the lane has one (OpenCode today), otherwise the BASE agent with `data.model` applied at spawn time.
- **F-05/F-06 (LOW): the ownership gate's stale baseline, and the AC-04(a) test's routing-layer-only
  assertion.** F-05 (stale `diff_ref` baseline predating other accepted, uncommitted work) is outside this
  package's own authority to fix — named for the orchestrator to resolve at the baseline/commit-sequencing
  level, not a code change here. F-06's test now also reads a generated orchestrator copy and confirms the
  CROSS-LANE branch specifically (not the true-off-lane degrade, not the benign-unverified sub-case) is what
  is instructed for the tested decision shape, closing a gap where deleting the cross-lane condition from
  the canonical doctrine left the test passing.

### Repairs, round 2 (delta-review after the round-1 repair, PACKAGE_REPAIR)

- **DR-01 (HIGH, reopens SEC-P1-002 as incomplete): the round-1 `coord_policy.SAFE_ARGV` fix never reached
  the OpenCode lane, where the cross-lane-redirect branch actually fires.** `coord_policy.py` (and its
  generated copy under `Global/claude-code/hooks/`) ships ONLY to the Claude-Code harness — but D7's
  cross-lane-redirect branch fires precisely when the orchestrator's OWN host harness is NOT Claude Code
  (today, typically OpenCode). OpenCode's own Bash permission surface is not `coord_policy.py` at all; it is
  generated separately by `generate.py`'s `oc_permissions`, baked into `Global/opencode/agents/orchestrator.md`
  as a `bash:` allow/deny map. That map was never updated, so the deny-by-default `"*": deny` catch-all
  refused the exact `claude_code_spawn.py --dispatch-writer`/`--dispatch-review` command the doctrine had just
  instructed — the same dead end SEC-P1-002 originally named, now on the one lane where it is actually
  reachable. Fixed as the PAIRED change the ADR-0012/AC-19 `--context` precedent already established:
  `generate.py`'s `oc_permissions` (the `coord-ro` capability's `bash:` block) now also emits
  `"python3 __SET_AGENTS_ROOT__/ai/scripts/claude_code_spawn.py --dispatch-writer*": allow` and the matching
  `--dispatch-review*` line, one entry per `claude_code_spawn.main()`'s own two mutually-exclusive modes —
  the same one-entry-per-sanctioned-shape granularity `--route*`/`--context*` already use, never a bare
  `claude_code_spawn.py*` catch-all. `ai/scripts/generate.py` gained a new, recorded `approved_exceptions`
  ownership entry for this package (it was outside `owned_paths`, the same mechanism the round-1 repair
  already used for `coord_policy.py`). A new regression test
  (`test_opencode_orchestrator_permission_map_actually_admits_the_spawn_cli`) reads the REAL, generated
  `Global/opencode/agents/orchestrator.md` after `./build.sh` and asserts the allow-lines are actually
  present in the `bash:` block — closing the gap where the prior regression test asserted only that the
  DOCTRINE TEXT names the CLI, never that any permission map actually admitted it. The false claim this
  section previously made ("every generated orchestrator's bash-permission map allows exactly this narrow
  shape") is corrected above, in the SEC-P1-002 bullet itself, not left standing alongside this correction.
- **DR-02 (MEDIUM): `--routing-test-root` was reachable via the real CLI and allowlisted, letting the
  SEC-P1-003 audit-binding control be silently redirected away from the production store.**
  `claude_code_spawn.py`'s `main()` exposed `--routing-test-root DIR` as a real, user-facing flag, and
  `coord_policy.SAFE_ARGV`'s modifier map allowlisted it — an allowlisted invocation could cause the
  SEC-P1-003 audit record to land outside the real 0700 production store, with the production `run_id` never
  marked dispatched/closed in the real ledger. `set_agents_spawn.py`'s own `main()` deliberately never exposes
  this kind of test-only seam even though the underlying function accepts it. Fixed: `--routing-test-root`
  removed from `main()`'s `argparse` setup and from `coord_policy.SAFE_ARGV`'s modifier map; the parameter
  stays on `dispatch_writer`/`_persist_audit_binding` themselves for direct-Python test use.
- **DR-03 (LOW): the audit JSONL file was opened with the default process umask instead of the routing
  store's own 0600 discipline.** `_persist_audit_binding` used a plain `open(path, "a")`, landing at whatever
  the ambient umask produced (typically 0644) — inconsistent with `routing_core/store.py`'s own requirement
  that every file the store fingerprints be 0600. Already inside an 0700 directory, so no practical exposure,
  but fixed for consistency: an explicit `os.chmod(path, 0o600)` now follows every write.
- **DR-04 (LOW): `--task -` combined with `--supplementary -` silently produced an empty, unfenced review.**
  Both flags accept `-` (stdin); passing both meant the first read consumed all of stdin and the second
  returned `""`, which `compose_task` treats as "no supplementary content" — a Bash-less review-class spawn
  would silently proceed with no diff content and no nonce fence, with nothing reporting the caller's
  mistake. `main()` now refuses this exact combination via `parser.error(...)` before either file is read.
- **DR-05 (LOW): the new CLI's tests leaked `main()`'s own stdout into the real suite's console output.**
  Three tests exercising `claude_code_spawn.main()` did not patch `sys.stdout`, so `main()`'s
  `print(json.dumps(result))` polluted `verify.sh`'s own console output. Fixed by applying the same
  `mock.patch("sys.stdout", buf)` pattern the sibling
  `test_cli_reports_failure_exit_code_when_a_task_file_is_unreadable` test already used.
