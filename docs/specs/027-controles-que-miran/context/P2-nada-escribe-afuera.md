# Context pack — P2-nada-escribe-afuera

Spec: `docs/specs/027-controles-que-miran/spec.md`; **AC-04, AC-05**. Dependency: none.

## Objective

Make the unittest process hermetic: a test may mutate only a per-run temporary sandbox. A write
aimed at effective `$HOME`, `STATE_DIR`, or CLI configuration below that home fails immediately
and names the resolved target. This is test infrastructure only; production CLI behavior stays
unchanged.

## Current evidence and candidate surface

- `tests/__init__.py:1-18` is the package-wide import choke point; candidate for suite guard.
  Verified by source read.
- `ai/scripts/set_agents_app.py:45-49` derives `STATE_DIR` from `SET_AGENTS_STATE` or
  `Path.home() / ".local/state/set-agentes"`; `write_app_config` writes it at `:1032-1042`.
  Classify the final destination, never merely a helper name or environment string.
- CLI config destinations: OpenCode/Claude/Codex are listed at `set_agents_app.py:2126-2136`; Pi
  auth is under `Path.home() / ".pi/agent/auth.json"` in `routing_core/catalog.py:348-385`.
- Hermetic seams already patch `STATE_DIR`/`APP_CONFIG` into `TemporaryDirectory` at
  `tests/test_harness.py:691-710` and `tests/test_routing.py:6056-6073`. Preserve them.

## Tasks and ownership

Owned paths:

- `tests/__init__.py` — install a process-wide temporary-root policy before test-module imports.
- `tests/test_harness.py` — focused regressions and the smallest needed guard helper.
- `tests/test_routing.py` — only if a Pi/home fixture needs a minimal compatibility adjustment.

Read-only: `ai/scripts/set_agents_app.py`, `ai/scripts/routing_core/catalog.py`, ADR-0051, spec,
state, scaffolds, README, and docs/notas. Do not alter production code.

Implement a destination-based guard, not a source-text grep:

1. Allocate one private `TemporaryDirectory` for the test run. Set inherited temporary/home seams
   before imports and disable bytecode writes for child Python processes.
2. Intercept write-capable filesystem operations at their common boundary (open write/create modes,
   `Path`/OS create, truncate, replace/rename, delete, and directory creation). Resolve a requested
   path without requiring it to exist; allow only the private temporary root.
3. Explicitly reject an indirect destination under the effective `Path.home()`,
   `set_agents_app.STATE_DIR`/`APP_CONFIG`, `.claude`, `.codex`, `.pi`, or `.config/opencode`.
   A variable called `tmp` is not evidence of safety.
4. Relocate any newly exposed fixture into the sandbox; never whitelist the real home or repo.

## Required red/green bite

Write the tests first. Prove each by temporarily neutralizing the guard, then restoring it:

- Green: a fixture write below a real `TemporaryDirectory` succeeds.
- Red: a write below effective `$HOME` fails before mutation; its message contains the resolved file.
- Red destination matrix: `STATE_DIR/config.toml`, `.claude`, `.codex`, `.pi`, and
  `.config/opencode` all fail by destination, not because a mock helper was called.
- Existing `write_app_config` behavior remains green with `STATE_DIR` and `APP_CONFIG` below the
  temporary root (`tests/test_harness.py:691-710`).

## Risks and invariants

- False-positive risk: imports, pycache, subprocesses, and atomic replacement use different APIs.
  A `Path.write_text`-only patch is insufficient; inherit the bytecode/temp environment too.
- Safety invariant: fail closed, name the destination, and never touch the caller's real home.
- Overlap: P1 owns `tests/__init__.py` and `tests/test_harness.py`; preserve its import-isolation
  fix. No other planned package overlaps P2 unless a P2 Pi fixture needs `tests/test_routing.py`.

## Local validations and package gates

Run long commands through `ai/scripts/heartbeat-run.py --interval 20 -- <command>` (ADR-0041):

- `python3 -m unittest tests.test_harness.HarnessTests.<new_P2_guard_tests>`
- `python3 -m unittest tests.test_routing`
- `python3 -m unittest discover -s tests`
- `./ai/scripts/verify.sh`
- `./build.sh --check`
- `git diff --check`

Expected markers: `VERIFY_PASS`; `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`,
`BUILD_CHECK_PASS`. Focused P2 names are not created yet; no gate was run for this planning pack.

## Done conditions

AC-04/05 close only when intentional home/config writes fail without mutation, an allowed temp
write passes, the error identifies the target, and all gates are green. Runtime surface: `true`.
Test owner: implementer.
