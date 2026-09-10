# 046 — Discovered hosts

- **Estado:** Approved (Federico, 2026-08-26) — plan "Consola viva, instancia local y hosts adaptables".
- **Modo:** feature · risk signal `public-contract` + `multi-module`.
- **ADRs:** extends 0042 (a second, independent registry in the same neutral module), 0038
  (propose→approve for anything unknown), 0043 (what a probe proves). Architecture owns the new ADR.
- **Companions:** 045 renders these rows on the live home; 047 turns `sin lane` rows into lanes.

## Problem

The harness has no host axis. It has a **provider** axis (`PROVIDERS`,
`ai/scripts/provider_registry.py:56-73` — four OpenCode-facing provider identities) and a hardcoded
CLI list (`HARNESS_CLIS = ("opencode", "claude", "codex")`, `ai/scripts/set_agents_app.py:51`), plus a
hand-added `pi` row in the Estado panel (`:3739-3740`). A CLI that is installed and working but is not
one of those four is invisible.

Measured on this machine, 2026-08-26, with `command -v`: `agy`, `copilot`, `claude`, `codex`,
`opencode`, `pi` all resolve; `fx` does not. Of those seven, exactly three plus the hand-added `pi`
row can appear in `_estado_general_lines` (`:3721-3762`). `agy` and `copilot` are installed and
completely absent from every surface.

Pushing hosts into `PROVIDERS` is not an option: that dict's **insertion order is a contract** (its
own docstring, `provider_registry.py:18-21`) because `_MODEL_PREFERENCE_PROVIDERS` derives its ordered
tuple from `tuple(PROVIDERS)` and that order surfaces in user-facing validation messages. A host is
also a different kind of thing — a binary on `PATH` — from an OpenCode provider identity with an
`opencode_auth_key` and an `opencode_cli_id`.

## Scope

1. **A host registry, separate from `PROVIDERS`.** Same precedent ADR-0042 already set inside
   `provider_registry.py` when 022 PKG-4 added "a SECOND, INDEPENDENT registry in this same neutral
   module" (`:76-89`) for the OpenCode `provider.*` blocks. Hosts are a third axis by the same rule:
   separate table, zero effect on `PROVIDERS` order or membership.
2. **Discovery by `shutil.which` over a closed candidate list:** `agy`, `fx`, `copilot`, `claude`,
   `codex`, `opencode`, `pi`. Discovery observes; it never installs and never routes.
3. **Host rows surface in Estado/Hosts even with no lane yet**, with one state per host from a closed,
   ordered vocabulary:

   | state | meaning | resolution order |
   |---|---|---|
   | `ausente` | the binary does not resolve on `PATH` | 1 (first match wins) |
   | `sin lane` | binary resolves, no lane/adapter registered | 2 |
   | `unlistable` | binary resolves, a lane exists, its model list cannot be verified | 3 |
   | `vivo` | binary resolves, a lane exists, and the model list verified | 4 (default) |

   The order is a **total function**: exactly one state per host, first match wins, so `sin lane` and
   `unlistable` can never both be claimed for the same host.
4. **An unknown CLI is still a proposal, never an install.** Discovering a binary outside the
   candidate list does not add it to anything: the ADR-0038 propose→approve path stays the only door
   (`cmd_tools_install`'s `TOOL_UNKNOWN` tail, `set_agents_app.py:2138-2142`).
5. **`github-copilot` the OpenCode provider stays M-1.** `routing_core/catalog.py:144-154` records
   that the credential is authenticated but `opencode models github-copilot --pure` answers
   `Provider not found`, so no routable pair is added, fail-closed. That verdict stands until
   re-measured. The **Copilot CLI** (`copilot` on `PATH`) is a *different row on a different axis* and
   its host state says nothing about the OpenCode provider's.

## Non-goals

- Installing, authenticating, or routing any newly discovered host (047 owns lanes; ADR-0038 owns
  installs).
- Changing `PROVIDERS` membership or order (`provider_registry.py:56-73`), or
  `HARNESS_CLIS`'s meaning for the install/auth flows that already use it (`auth_state` `:1301`,
  `_status_data` `:1350-1353`).
- Re-measuring or lifting the `github-copilot` M-1 verdict.
- Adding a host to the curated `tools.toml` catalog. Hosts are AI CLIs, not the catalog's
  developer-tool universe (`tools.toml` `[cli.*]`: supabase, vercel, gcloud, gh, docker, jq, obsidian,
  syncthing, pnpm — none of the seven candidates).
- A network probe at menu-paint time. Discovery is `PATH`-only; anything costlier is the lane's job.

## Criteria

- **AC-01** The Estado/Hosts surface lists **all seven** candidates, each with exactly one state from
  the closed vocabulary, on a machine where some resolve and some do not.
- **AC-02** A host that resolves with no lane registered shows `sin lane` — it is listed, not hidden.
- **AC-03** A host that resolves but whose model list cannot be verified shows `unlistable`, and
  contributes **zero** routable models (fail-closed, the same discipline as the M-1 pair at
  `routing_core/catalog.py:144-154`).
- **AC-04** `PROVIDERS` order and membership are byte-identical after the change, and
  `--model-preference` validation messages are unchanged.
- **AC-05** A binary on `PATH` that is not in the candidate list produces **no** host row and no
  install attempt; the propose→approve path is the only way it can ever appear.
- **AC-06** The `github-copilot` OpenCode provider still contributes no routable pair, while a
  resolving `copilot` binary shows its own host row. The two states are independent.
- **AC-07** `python3 -m unittest tests.test_harness tests.test_routing tests.test_menu_ui
  tests.test_provider_registry` and `./build.sh --check && ./ai/scripts/verify.sh` green, with the
  suite passing on a machine where **none** of the seven candidates resolve.

## Spec audit

Checked:

- **Universe named, separate from what is present.** The universe is the seven-name candidate list
  (§ Scope 2), declared independently of what `shutil.which` happens to find. AC-01 is measured against
  that list, so a host is listed *because it should exist*, not because it was found — this is the
  absence-is-a-signal rule, and `fx` is the live proof: absent on this machine on 2026-08-26, and it
  must still produce a row.
- **Absence-of-record behavior defined.** `ausente` is a first-class state, not a missing row.
- **Data source carries the signal.** `shutil.which` is already the harness's own detection primitive
  for CLIs (`set_agents_app.py:1302`, `:1351`, `:2124`, `:2168`, `:2343-2347`), so the source proves
  presence. It proves **nothing** about model lists — hence `unlistable` as a separate state and
  AC-03's zero-pair rule, rather than treating "present" as "routable".
- **Fixture that would fool AC-01.** Seeding the host table from `HARNESS_CLIS`
  (`set_agents_app.py:51`) or from `PROVIDERS` passes a naive "the table has rows" assertion while
  leaving `agy`, `fx`, and `copilot` invisible — the exact defect. AC-01 requires all seven names by
  name. A second fooling fixture is a machine where every candidate resolves, which hides the
  `ausente` path; AC-01 is measured on a mixed machine, and AC-07 additionally on a disposable `HOME`
  with an empty `PATH` for the candidates.
- **Fixture that would fool AC-03.** A stubbed `probe_models` returning `[]` looks identical to a
  verified-empty list. The criterion is on the pair count reaching the router, plus the state token
  being `unlistable` rather than `vivo` with zero models.
- **Pairwise conflicts.** (i) `sin lane` vs `unlistable` on the same host → § Scope 3's ordered
  resolution gives a single answer. (ii) The `github-copilot` provider's M-1 verdict vs the `copilot`
  host row → AC-06 declares them independent axes, so neither alert suppresses or contradicts the
  other. (iii) Host discovery vs ADR-0038 propose→approve → AC-05 gives propose→approve exclusive
  ownership of anything outside the candidate list, so discovery can never act as a silent install.
  (iv) 046's state vocabulary vs 047's lanes → 046 owns the vocabulary; 047 may only move a host
  between existing states.
- **Could not verify.** Where the host registry file lives and its exact record shape; whether the
  candidate list is a Python constant or a tracked TOML table; how the Hosts block composes into
  `_estado_general_lines` (`set_agents_app.py:3721`) without disturbing the `Harnesses` table; whether
  `pi`'s existing `_pi_lane_state()` row (`:921`, rendered at `:3739-3740`) is replaced by a host row
  or kept alongside. All **UNVERIFIED** — architecture decides.

## Supersedes

- **The Estado panel's host universe.** `_estado_general_lines` (`set_agents_app.py:3721-3762`)
  currently derives its `Harnesses` table from `HARNESS_CLIS` (`:51`) plus one hand-added `pi` row
  (`:3739-3740`). That enumeration stops being the definition of "which AI CLIs this machine has".
- Not superseded: **ADR-0042** — `PROVIDERS` remains the one source for provider-keyed tables
  (`provider_registry.py:1-8`) and its order remains a contract (`:18-21`); the host axis is a third
  registry in the same spirit as 022 PKG-4's second one (`:76-89`), not a replacement.
  **`routing_core/catalog.py:144-154` (M-1)** is reaffirmed, not lifted. **ADR-0038** keeps exclusive
  ownership of installs. **ADR-0043** keeps defining what a probe proves.
