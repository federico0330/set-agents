# 046 — Acceptance criteria (BDD)

## Flow

```
   candidate list (CLOSED, declared independently of what is installed)
   agy · fx · copilot · claude · codex · opencode · pi
                          |
                          v
                 shutil.which(candidate)          <-- PATH only, no network
                          |
          +---------------+---------------+
          |                               |
      not found                        found
          |                               |
          v                               v
      "ausente"                   lane/adapter registered?
       (a ROW,                    |                     |
      not a gap)                 no                    yes
          |                       |                     |
          |                       v                     v
          |                  "sin lane"         probe_models verified?
          |                       |              |                 |
          |                       |             no                yes
          |                       |              |                 |
          |                       |              v                 v
          |                       |        "unlistable"          "vivo"
          |                       |        0 routable pairs   routable models
          |                       |              |                 |
          +-----------+-----------+--------------+-----------------+
                      |
                      v
        Estado / Hosts  -- exactly ONE state per candidate, all seven listed
                      |
                      v
          045 live home renders these rows


   a binary on PATH that is NOT in the candidate list
                      |
                      v
        no host row, no install  --> ADR-0038 propose -> approve  (only door)


   axis independence:
        OpenCode provider "github-copilot"  --M-1--> 0 routable pairs (unchanged)
        host row          "copilot"         -------> its own state
        neither reads the other
```

## AC-01 — all seven candidates, one state each

**Given** a machine where some candidates resolve on `PATH` and some do not — measured on this machine
2026-08-26: `agy`, `copilot`, `claude`, `codex`, `opencode`, `pi` resolve and `fx` does not
**When** the operator opens Estado/Hosts
**Then** all seven candidate names appear, each with exactly one state from
`ausente | sin lane | unlistable | vivo`, and no candidate is omitted because it was not found.

*Would-fool fixture:* deriving the table from `HARNESS_CLIS` or from `PROVIDERS` — it yields rows and
passes a "table is non-empty" assertion while `agy`, `fx`, and `copilot` stay invisible. This
criterion names all seven.

## AC-02 — a host with no lane is listed, not hidden

**Given** a candidate whose binary resolves and for which no lane/adapter is registered
**When** Estado/Hosts is painted
**Then** the host appears with state `sin lane`
**And** it contributes nothing to routing.

## AC-03 — unlistable is fail-closed

**Given** a candidate whose binary resolves, has a lane, and whose model list cannot be verified
against its own CLI id
**When** the harness resolves routable models
**Then** the host shows `unlistable` and contributes **zero** routable pairs — never a guessed,
inherited, or remembered model list.

*Would-fool fixture:* a stub `probe_models` returning an empty list, which is indistinguishable from a
verified-empty catalog. The assertion is on the state token *and* the pair count.

## AC-04 — the provider axis is untouched

**Given** the repository after the change
**When** `PROVIDERS` order and membership are read, and a `--model-preference` validation error is
triggered
**Then** the four provider keys and their order are byte-identical to before, and the user-facing
validation message is unchanged.

## AC-05 — unknown CLIs go through propose→approve

**Given** a binary on `PATH` that is not one of the seven candidates
**When** Estado/Hosts is painted, and separately when the operator asks to install it by that name
**Then** no host row is created, nothing is installed, and the ADR-0038 propose→approve path is what
the harness names as the way forward.

## AC-06 — the two Copilot facts are independent

**Given** a machine where the `copilot` binary resolves and the OpenCode `github-copilot` credential
is authenticated
**When** routable pairs are resolved and Estado/Hosts is painted
**Then** the OpenCode `github-copilot` provider still contributes zero routable pairs (M-1 unchanged)
**And** the `copilot` host row carries its own state
**And** neither value is derived from the other.

## AC-07 — gates, including on a machine with nothing installed

**Given** a disposable `HOME` and a `PATH` where none of the seven candidates resolve
**When** `python3 -m unittest tests.test_harness tests.test_routing tests.test_menu_ui
tests.test_provider_registry` and `./build.sh --check && ./ai/scripts/verify.sh` run
**Then** all are green, with every candidate reported `ausente` rather than skipped
**And** no test is weakened, skipped, or deleted to reach green.
