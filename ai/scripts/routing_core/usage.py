"""023-senales-de-consumo PKG-B1 (ADR-0045): one consumption vocabulary, translated at the
edge -- never a second, independently-drifting copy of it.

`store._usage_row` validates and stores exactly ONE flat vocabulary: `input`, `output`,
`cache_read`, `cache_write`, `reasoning` (token counts), `totalTokens` (an optional caller-
supplied cross-check), and `cost.total` (`store.USAGE_TOKEN_FIELDS`). It stays the closed
validator (never relaxed by this module -- a value this module hands it is validated exactly
as strictly as one typed in by hand). Every runtime's OWN usage report is a genuinely
different wire shape. This module is the one place that knows all four and translates each
into the store's vocabulary, so:

- the doctrine template `Global/_canonical/agents/orchestrator.md` gives the orchestrator for
  a same-lane manual `--route-terminal ... --usage` close is a PROSE COPY of the mapping
  defined here, not an independent guess -- if a runtime's real shape ever changes, this
  module (and its tests) are what has to change first, and the doctrine follows;
- a future automated fix to `claude_code_spawn.py`'s/`opencode_spawn.py`'s own `--usage`
  composition (both already attempt to attach usage today, in shapes `_usage_row` does not
  recognize -- see the two per-runtime sections below) has one correct mapping to import
  instead of re-deriving it.

Nothing in this package wires these functions into any runtime spawn call site (out of
`ALCANCE` for 023-senales-de-consumo PKG-B1) -- they are reachable from tests and from the
orchestrator's own hand-composed `--usage` JSON, deliberately, not from `claude_code_spawn.py`/
`opencode_spawn.py`/`codex_spawn.py`, which this package's `ALCANCE` does not touch.

## Real wire samples, one per runtime, measured live this package (2026-08-13), never invented

Each sample below is the raw response captured from the cheapest reachable model with a
one-word prompt, or -- where noted -- a citation to where an existing docstring already
measured it. Where a field's semantics could not be confirmed from the sample alone (no
independent total to cross-check against, no schema doc consulted), it is marked
UNVERIFIED and deliberately left unmapped, rather than guessed.

**pi** -- already measured and cited by `store.py`'s own `_USAGE_FIELD_ALIASES` docstring
(a real spawn observed 2026-07-29):
    {"input":3321,"output":5,"reasoning":0,"totalTokens":3326,"cacheRead":0,"cacheWrite":0,
     "cost":{...}}
Already the flat vocabulary almost verbatim -- `_usage_row`'s own `_USAGE_FIELD_ALIASES`
already accepts the two camelCase cache keys directly. `normalize_pi` below is the identity
function, kept only so every runtime has the same one-call entry point.

**claude-code** -- `claude --print --model haiku --output-format json --no-session-persistence
"Reply with exactly one word: hi"`, run live this package. `claude_code_spawn.py` (`:452-457`)
already extracts exactly this shape (`total_cost_usd` + `modelUsage`) into its own `--usage`
composition (`:602-605`) -- captured real sample:
    {"total_cost_usd":0.0271811,"modelUsage":{"claude-haiku-4-5-20251001":{
     "inputTokens":10,"outputTokens":43,"cacheReadInputTokens":18101,
     "cacheCreationInputTokens":12573,"webSearchRequests":0,"costUSD":0.0271811,
     "contextWindow":200000,"maxOutputTokens":32000,"canonicalModel":"claude-haiku-4-5",
     "provider":"firstParty"}}}
No `reasoning`/`totalTokens` mapped: this shape carries no reasoning-token field at all (the
separate, unrelated `output_tokens_details.thinking_tokens` lives on the raw top-level
`usage` object, which neither the measured sample's `modelUsage` slice nor
`claude_code_spawn.py`'s own capture includes), and there is no independent total in this
shape to cross-check a derived sum against -- UNVERIFIED, left unmapped rather than guessed.

**opencode** -- `opencode run -m opencode/nemotron-3.5-lightning-free --format json "Reply
with exactly one word: hi"`, run live this package. `opencode_spawn.py` (`:255-256`) already
extracts the last `step_finish` event's `part.tokens` into its own `--usage` composition
(`:318-321`, as `{"tokens": tokens}`, missing the sibling `part.cost` entirely) -- captured
real sample (the `part` object of that event):
    {"tokens":{"total":30493,"input":30322,"output":0,"reasoning":197,
     "cache":{"write":0,"read":0}},"cost":0}
`tokens.total` is deliberately NOT mapped to `totalTokens`: measured live, `30493 !=
30322+0+197+0+0` (`30519`) -- opencode's own "total" does not sum the same five components
this vocabulary tracks (some other, unexposed accounting), so passing it through as
`totalTokens` would trip `_usage_row`'s sum-mismatch check and discard a genuine report as
`invalid`. This mismatch is the measured reason, not a guess.

**codex** -- `codex exec --ephemeral --sandbox read-only --color never --skip-git-repo-check
-m gpt-5.6-luna -c model_reasoning_effort=low --json "Reply with exactly one word: hi"`, run
live this package. `codex_spawn.py` attaches NO `--usage` at all today (a distinct, separate
gap this package does not fix -- out of `ALCANCE`) -- captured real sample (the
`turn.completed` event's `usage` object):
    {"input_tokens":16057,"cached_input_tokens":8960,"cache_write_input_tokens":0,
     "output_tokens":5,"reasoning_output_tokens":0}
`cached_input_tokens`/`cache_write_input_tokens` are UNVERIFIED as additive components of
`input_tokens` versus already included within it (no schema reference consulted this
package, and the one live sample does not disambiguate it either way) -- `cache_read`/
`cache_write` are deliberately left unmapped rather than risk double- or under-counting.
No `cost` field appears anywhere in this event stream -- this lane's JSON carries no dollar
figure to map.

## `_usage_row`'s own tightening (ADR-0045, same package)

A raw dict this module cannot recognize AT ALL for a given runtime (every function below
then returns `{}`) is `absent` once it reaches `_usage_row` -- correct when the runtime
genuinely reported nothing. A raw dict that IS non-empty but matches none of the FLAT
vocabulary's own keys is a different case -- "reported something, none of it recognized" --
and `_usage_row` now marks that `invalid`, never `ok` (see `store.py`'s `_usage_row`
docstring). This module's own `_propagate_unrecognized` helper exists so a per-runtime
sample this package cannot map to anything (a future wire-format change, or a field this
package genuinely could not verify) surfaces as `invalid` through that same path, rather
than silently vanishing as `absent`.
"""

from __future__ import annotations

RUNTIMES = ("pi", "claude-code", "opencode", "codex")


def _propagate_unrecognized(raw: dict, mapped: dict) -> dict:
    """`raw` was genuinely non-empty; `mapped` is what this module recognized from it. If
    `mapped` ended up empty, hand `raw` itself back (unrecognized, but non-empty) so
    `_usage_row`'s own tightening -- never a second copy of that rule here -- is what
    turns it into `invalid`, rather than this module silently downgrading a "reported
    something we didn't understand" case to `absent`."""
    return mapped or dict(raw)


def normalize_pi(raw: dict) -> dict:
    """Identity: pi's own wire format already IS the flat vocabulary (module docstring)."""
    if not isinstance(raw, dict) or not raw:
        return {}
    return raw


def normalize_claude_code(detail: dict) -> dict:
    """`detail` is the shape `claude_code_spawn.py` already extracts (`total_cost_usd` +
    `modelUsage`), not the raw `claude --output-format json` object -- see module docstring
    for the measured sample this maps."""
    if not isinstance(detail, dict) or not detail:
        return {}
    model_usage = detail.get("modelUsage")
    entry = next(iter(model_usage.values()), None) if isinstance(model_usage, dict) else None
    if not isinstance(entry, dict):
        return _propagate_unrecognized(detail, {})
    out: dict = {}
    for src, dst in (("inputTokens", "input"), ("outputTokens", "output"),
                     ("cacheReadInputTokens", "cache_read"), ("cacheCreationInputTokens", "cache_write")):
        value = entry.get(src)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            out[dst] = value
    cost = entry.get("costUSD", detail.get("total_cost_usd"))
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        out["cost"] = {"total": cost}
    return _propagate_unrecognized(detail, out)


def normalize_opencode(part: dict) -> dict:
    """`part` is the `step_finish` event's own `part` object (`tokens` + sibling `cost`) --
    see module docstring for the measured sample this maps and why `tokens.total` is never
    forwarded as `totalTokens`."""
    if not isinstance(part, dict) or not part:
        return {}
    tokens = part.get("tokens")
    out: dict = {}
    if isinstance(tokens, dict):
        for field in ("input", "output", "reasoning"):
            value = tokens.get(field)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                out[field] = value
        cache = tokens.get("cache")
        if isinstance(cache, dict):
            for src, dst in (("read", "cache_read"), ("write", "cache_write")):
                value = cache.get(src)
                if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                    out[dst] = value
    cost = part.get("cost")
    if isinstance(cost, (int, float)) and not isinstance(cost, bool):
        out["cost"] = {"total": cost}
    return _propagate_unrecognized(part, out)


def normalize_codex(usage: dict) -> dict:
    """`usage` is the `turn.completed` event's own `usage` object -- see module docstring
    for the measured sample this maps and why the two cache fields stay unmapped
    (UNVERIFIED inclusion semantics) and why no `cost` is ever produced."""
    if not isinstance(usage, dict) or not usage:
        return {}
    out: dict = {}
    for src, dst in (("input_tokens", "input"), ("output_tokens", "output"),
                     ("reasoning_output_tokens", "reasoning")):
        value = usage.get(src)
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            out[dst] = value
    return _propagate_unrecognized(usage, out)


NORMALIZERS = {
    "pi": normalize_pi,
    "claude-code": normalize_claude_code,
    "opencode": normalize_opencode,
    "codex": normalize_codex,
}


def normalize(runtime: str, raw: dict) -> dict:
    """`runtime` names one of `RUNTIMES`; any other value -- unknown or absent -- is
    UNVERIFIED for translation, so this returns `{}` rather than guess a mapping (the
    caller's own `raw` should be passed to `_usage_row` unmapped in that case, not through
    here)."""
    fn = NORMALIZERS.get(runtime)
    if fn is None or not isinstance(raw, dict):
        return {}
    return fn(raw)
