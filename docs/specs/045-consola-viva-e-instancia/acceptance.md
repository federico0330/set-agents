# 045 — Acceptance criteria (BDD)

Business language, whole-system, observable. Every scenario is measured on the real paths named in
`spec.md`, never on a fixture that only exists for the test.

## Flow

```
                                    ./set-agents
                                         |
                                         v
                        +--------------------------------+
                        |  HOME (live)                   |
                        |  hosts | providers | last      |   <-- AC-A.1 / AC-A.2
                        |  routing decision              |
                        |  postura: X | metodologia: Y    |   <-- AC-C.1
                        +--------------------------------+
                             |                    |
                 Overrides   |                    |  postura / metodologia
                             v                    v
              +---------------------------+   +---------------------------+
              | AREA/EFFORT/CURSOR matrix |   | set_postura /             |
              | edit a cell               |   | set_metodologia           |
              +---------------------------+   +---------------------------+
                             |                            |
                             v                            v
              STATE_DIR/models.local.toml          config.toml (existing store)
              (models.toml UNTOUCHED)                     |
                             |                            v
                             |                    --posturas / --metodologias
                             v                       report the new value
              git diff --name-only -- models.toml
                        => EMPTY                        <-- AC-B.1


        orchestrator                --route-decide descriptor
             |                      { role, task_class, ...,
             |                        model_request?, effort_request? }
             v                                  |
      cmd_route_decide -----------------------> validate closed set
      (set_agents_app.py:671)                          |
                            +----------------+---------+----------------+
                            |                |                          |
                       absent key     valid + eligible          invalid / unhonorable
                            |                |                          |
                            v                v                          v
                 byte-identical to    routes with that effort    named reason code,
                 pre-045 decision     and reports it             hard exclusion intact
                    AC-D.2                 AC-D.2                     AC-D.3
```

## AC-A.1 — the home is not the matrix

**Given** a machine with `models.toml` curating every area
**When** the operator runs `./set-agents`, and separately opens the models wizard
**Then** the text handed to the picker as `header=` on first paint contains no `AREA`/`EFFORT`
matrix row, and the matrix is reachable only after selecting the Overrides entry.

*Would-fool fixture:* asserting on a captured screen instead of the `header=` string — the matrix
could simply have scrolled out of view. The assertion is on the header text.

## AC-A.2 — the home names live state or names its silence

**Given** any machine, including one with no authenticated provider and no routing history
**When** the home panel is painted
**Then** it carries a line for hosts, a line for providers, and a line for the last routing decision;
each shows measured values or an explicit "not measured" / "probe failed" phrase.
**And** no host, provider, or decision row is printed with invented zero values.

*Would-fool fixture:* a machine with everything authenticated. The criterion is also measured on a
disposable `HOME` with zero credentials, where the honest output is three named-absence lines.

## AC-B.1 — user taste never dirties the repo

**Given** a working copy where `git diff --name-only -- models.toml` is already empty
**When** the operator changes an area model, a role override, an effort, or the `cursor` field from
the wizard and saves
**Then** `STATE_DIR/models.local.toml` contains the new value
**And** `git diff --name-only -- models.toml` is still empty.

*Would-fool fixture:* pointing the wizard at a temporary `models_out`, or starting from the dirty
`models.toml` this working copy carries on 2026-08-26. Measured against the real `models_out` from a
clean baseline.

## AC-B.2 — absence and malformation are defined, not crashes

**Given** `STATE_DIR/models.local.toml` absent, then truncated mid-table, then carrying a key no
field name matches
**When** the wizard paints and the router resolves a model
**Then** each case resolves to the factory value from tracked `models.toml`, with no traceback and no
partial application of the malformed file.

## AC-B.3 — precedence between factory and instance

**Given** tracked `models.toml` sets a field and the overlay sets the same field to a different value
**When** the effective configuration is resolved
**Then** the overlay value wins for that field only
**And** a curated field the overlay does not mention keeps its tracked value.

## AC-C.1 — postura and metodología are visible and editable from the menu

**Given** a machine with `postura=autonoma` and no metodología preference
**When** the operator opens the menu, reads the two values, changes each one, and then runs
`set-agents --posturas` and `set-agents --metodologias`
**Then** the menu showed both current values before the change, no `--avanzado` was needed, and both
CLI verbs report the new values.

## AC-C.2 — the Cursor field is editable

**Given** the Overrides matrix
**When** the operator picks the `cursor` field for an area or a role and chooses a value
**Then** the value is accepted only if it validates against the same catalog path the other fields
use, and a rejected value leaves the previous value in place.

## AC-D.1 — effort for every lane

**Given** the Overrides matrix
**When** the operator inspects the overridable fields
**Then** effort is offered for every lane in `AREA_FIELDS`, not only for Codex.

## AC-D.2 — `effort_request` is honored and reported

**Given** a `--route-decide` descriptor for an eligible role
**When** the descriptor omits `effort_request`
**Then** the decision is byte-identical to the pre-045 decision for the same input.
**When** the descriptor carries a valid, eligible `effort_request`
**Then** the decision routes with that effort and reports it in the envelope.

## AC-D.3 — an unhonored request names its reason

**Given** a `--route-decide` descriptor
**When** `effort_request` is not a member of the closed effort set
**Then** the run exits 2 with `ROUTING_INPUT_INVALID`, on the same parse path every other malformed
descriptor field already takes.
**When** `effort_request` is well-shaped but the routed target cannot honor it, or honoring it would
require relaxing a hard exclusion
**Then** the decision proceeds with the routed effort, the exclusion is intact, and the envelope
carries a named reason code for the unhonored request — never a silent substitution.

## AC-E.1 — gates

**Given** the repository after the change
**When** `python3 -m unittest tests.test_harness tests.test_routing tests.test_menu_ui` and
`./build.sh --check && ./ai/scripts/verify.sh` run
**Then** all are green, with no test weakened, skipped, or deleted, and `WIZARD_ITEMS[0..4]` and the
`MENU_ITEMS` branch indexes unchanged in meaning.
