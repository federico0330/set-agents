# P1-dispatch-core — implementation evidence

Baseline: `03939b103ca49f35457529c4cf8f889873ac8068`. Contract 1.1.0, tasks T-100..T-105.

## T-100 — ADR-0006
`docs/adr/0006-adaptive-dispatch-cache-and-facts.md`: AM-1 per-field derivation table (risk raise-only),
AM-2 cache mechanics (store-root location, uid+config-digest+pair key, TTL 300s, atomic 0600, corrupt ⇒
ignored, fresh-selected authority before writer authorization).

## T-101 — tiered catalog v2
`ai/catalogs/routes.v1.toml`: catalog_version 2, six single-tier rows (openai-codex: luna/low=fast,
sol/medium=balanced, terra/high=frontier; anthropic: haiku/sonnet/opus, effort medium). `build_snapshot`:
version==2, closed row schema with allowlisted-optional `runtimes` (validated against the audited pair
table, outside the canonical ID tuple, runtime-only duplicates still CATALOG_INVALID), tier enum, effort ∈
codex_effort, xhigh rejected while unbenchmarked, anthropic effort pinned medium. Tier encodes as a
one-element group — 003's binding shape untouched.

## T-102 — tier-aware selection
`domain.py`: `TIER_ORDER`, `required_tier()` (CRITICAL/high ⇒ frontier; mechanical/documentation/
inspection + low ⇒ fast; else balanced). `service.py`: `TIER_INSUFFICIENT` exclusion, ordering
(reviewer-provider preference, tier asc, curated_priority, route_id). Full (task_class × risk) matrix
unit-tested; fast tier WINS for mechanical/low (asserted).

## T-103 — dispatch CLI + SCHEMA 4
`store.py`: SCHEMA 4, terminal state `abandoned` (from authorized only, failure semantics, never a review
identity), `abandon()/open_runs()/recent_writers()`. `set_agents_app.py`: `--route-decide` (descriptor →
AM-1 derivation in-process; writers get durable run_id; reviewers without run_id get non-executable
tier/model with `REVIEW_IDENTITY_UNVERIFIED`; docs-rw/other get non-executable decisions),
`--route-dispatched`, `--route-terminal` (authorized→abandoned on failure), `--routing-open-runs`,
`--routing-recent-writers`; total mode exclusion with per-mode exempt modifiers (`--fresh-probes`,
`--latency-ms`); malformed run_id ⇒ exit 2 before any DB touch.

## T-104 — probe cache + fresh-selected
`catalog.py`: ADR-0006 cache; identical probe argvs deduped per invocation; **two field defects found and
fixed while wiring** (would have kept FD-003 broken in production): `codex login status` prints to STDERR,
and `opencode` blocks forever on non-TTY stdout without `CI=1/TERM=dumb` env; probe timeout 20s.
`service.py`: `_reprobe` of the selected (+differing fallback) pair before `_authorize_issued`; failed
fresh probe ⇒ `PROVIDER_UNAUTHENTICATED`, nothing durable; unverified fallback is dropped.

## T-105 — backlog + suite
N-1 (unhashable required_tools ⇒ FACTS_INCOMPLETE), N-2 (`_compose_for_tests` requires explicit root),
N-3 (explain reuses cache; 003's "no state" invariant re-scoped to decision state — DB bytes asserted
untouched, cache exempted), N-4 (`verify.sh` compiles `routing_core/*.py`). Suite 19 → **29 tests**.

## Live verification (real machine, 2026-07-26)

| Check | Result |
|---|---|
| Cold probe (3 pairs authenticated) | 28.9s → cache written |
| Warm `--route-decide` (reviewer, documentation) | **0.25s**, tier fast, gpt-5.6-luna, `REVIEW_IDENTITY_UNVERIFIED` |
| `--route-decide` security + feature_id | tier **frontier**, gpt-5.6-terra, effort high |
| security sin feature_id resoluble | flags contexto false ⇒ `NO_ELIGIBLE_ROUTE` (conservador AM-1) |
| Writer decide → dispatched → terminal success | run1_817c… full lifecycle exit 0/0/0, report counters 3 events |
| Repeat terminal | exit 1 `STATE_CONFLICT` (stable, no traceback) |
| `--route-decide --json --yes` | **corrected (repair R1, F08/N11)**: `--route-decide` takes ONE value; `--json` here is consumed as argparse's "expected one argument" usage/error text on stderr, exit 2 — this is argparse's own error, never our `ROUTING_INPUT_INVALID` JSON envelope (the row above previously claimed the latter). The actual total-mode-exclusion case (`--route-decide <file> --yes`) IS `ROUTING_INPUT_INVALID`, exit 2, and is covered by `test_dispatch_cli_mode_and_modifier_exclusion` / `test_cli_mode_exclusion_covers_every_non_routing_argument`. |

## Local gates

unittest 29/29 (3.1s warm) · HarnessTests 2/2 · setup_models --check PASS · py_compile (incl.
routing_core) PASS · `./ai/scripts/verify.sh` **VERIFY_PASS** (127 tests).

## Operator note

`~/.local/state/set-agentes/routing-v2` (DB schema 2 de la 003, telemetría de prototipo con 8 dispatches)
fue MOVIDA a `~/.local/state/set-agentes/routing-v2.schema2.bak` — reversible; borrala cuando quieras. El
root nuevo se creó solo con el primer despacho (SCHEMA 4).
