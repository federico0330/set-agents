# 047 — Acceptance criteria (BDD)

## Flow

```
   046 host row: "sin lane"
            |
            v
   +--------------------------------------------------+
   |  ADAPTER CONTRACT (all four, or refused)         |
   |                                                  |
   |  detect          PATH only, no network/auth      |
   |  probe_models    fail-closed, VERIFIED CLI id    |
   |  materialize(model, effort)   <-- 045 PKG-D      |
   |  install_harness  (NOT binary install: ADR-0038) |
   +--------------------------------------------------+
            |
            |  fixed order, one host at a time
            v
   [1] agy ------> detect ok? --yes--> probe verified? --yes--> "vivo"      AC-04
        |                 |                    |
        |                 no                   no
        |                 |                    v
        |                 v              "unlistable", 0 pairs             AC-02
        |          named skip (AC-08)
        v
   [2] fx -------> working lane  OR  "detected, spawn deferred"
                                      + WRITTEN REASON                     AC-05
                                      (a bare skip FAILS)
        |
        v
   [3] Copilot CLI ---> its own host state                                 AC-06
                        |
                        +-- independent of --> OpenCode "github-copilot" M-1
                                               (0 routable pairs, unchanged)

   untouched by construction:  pi in RUNTIMES  ·  Cursor outside RUNTIMES   AC-07
```

## AC-01 — the contract is complete or the lane is refused

**Given** a lane adapter that declares fewer than the four operations
**When** it is registered
**Then** registration is refused with a message naming the missing operation — the failure never waits
until a spawn.

## AC-02 — `probe_models` is fail-closed on a verified CLI id

**Given** a host whose binary resolves but for which no CLI id verifies
**When** `probe_models` runs and the router resolves pairs
**Then** the result is zero models, the host is `unlistable` (046), and the router receives zero pairs
**And** no model list is inferred from a credential, from the host's name, or from a previous run.

*Would-fool fixture:* a stub returning `[]`, which looks identical to a verified-empty catalog; and a
probe whose CLI id was assumed from the host name — the id/name heuristic this repo already rejected
once. The assertion is on the state token, the pair count, and the CLI id having been verified.

## AC-03 — `materialize` speaks 045's effort vocabulary

**Given** a routing decision for `agy` carrying a model and an effort
**When** `materialize(model, effort)` runs
**Then** the produced invocation carries that model and that effort, using 045 PKG-D's vocabulary and
no second spelling
**And** when the curated fallback is what actually ran, the spawn record carries
`MODEL_STATIC_FALLBACK` (ADR-0030).

## AC-04 — agy lands first

**Given** a machine where the `agy` binary resolves — measured present here on 2026-08-26
**When** the lane is registered and a decision routes to it
**Then** the host shows `vivo`, the decision is recorded, and the recorded decision is replayable from
its own evidence.

## AC-05 — fx closes with a reason, either way

**Given** the `fx` host — measured **absent** on this machine on 2026-08-26
**When** the lane work for `fx` closes
**Then** either it is a working lane with the same evidence AC-04 demands, or it closes as
`detected, spawn deferred` carrying a written reason that names the instability or the absence.
**And** a close with no written reason fails this criterion.

## AC-06 — the Copilot CLI lane is not the Copilot provider

**Given** the `copilot` binary resolving — measured present here on 2026-08-26 — and the OpenCode
`github-copilot` credential authenticated
**When** the Copilot CLI lane is registered and routable pairs are resolved
**Then** the lane's host state stands on its own
**And** the OpenCode `github-copilot` provider still contributes zero routable pairs
**And** neither value is derived from the other.

## AC-07 — Pi and Cursor are untouched

**Given** the repository after all three lanes land
**When** `RUNTIMES`, `SELECTED_RUNTIMES`, and the Cursor pin path are read
**Then** `pi` is still a runtime with its never-redirect-from behaviour intact, Cursor is still absent
from the runtime set, and no Cursor pin resolution changed.

## AC-08 — green with nothing installed, evidence with something installed

**Given** a `PATH` where none of `agy`, `fx`, `copilot` resolve
**When** the full suite plus `./build.sh --check && ./ai/scripts/verify.sh` runs
**Then** everything is green and each absent host produces a skip that names the host and the reason.
**Given** instead a machine where a host resolves
**When** the same gates run
**Then** live evidence of `detect`, `probe_models`, and one `materialize` for that host is recorded
under the feature's `evidence/`.

*Would-fool fixture:* a suite that skips whenever a binary is absent goes green everywhere and proves
nothing. This criterion requires the named reason in the skip and the live evidence when present —
which on this machine means `agy` and `copilot` must produce live evidence and only `fx` may take the
absent path.

## AC-09 — nothing else moves

**Given** the diff for this feature
**When** it is reviewed
**Then** no test is weakened, skipped, or deleted, and none of the four existing spawn CLIs changes
behaviour.
