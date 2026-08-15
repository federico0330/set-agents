# Context pack — P4-owned-paths-matchea-directorios

Spec: `docs/specs/027-controles-que-miran/spec.md`; **AC-08, AC-09**. Depends on P1 because P1
made this formerly hidden ownership verdict observable.

## Objective

Let a directory in `owned_paths` own its descendants, including a trailing slash spelling,
without relaxing exact/glob matching or admitting a look-alike prefix directory. A truly outside
file must retain `OWNERSHIP_FAIL` and exit 2.

## Current evidence and candidate surface

- `matches` in `ai/scripts/check-owned-paths.py:25-27` passes bare patterns to `fnmatch`; it has
  no directory-descendant rule. `main` uses it at `:101-106`, emits JSON at `:108-117`, and emits
  `OWNERSHIP_FAIL`/2 at `:118-120`.
- Existing real-script fixtures and output semantics are in `tests/test_harness.py:8453-8617`; P1
  untracked-file coverage follows them. Verified by source read.
- `build.sh --check` reports synchronization at `build.sh:105,124,129`; P1's ADR requires both
  canonical/scaffold copies. Candidate production paths are `ai/scripts/check-owned-paths.py` and
  `PROYECTO/ai/scripts/check-owned-paths.py`.

## Tasks and ownership

Owned paths:

- `ai/scripts/check-owned-paths.py` — add normalized directory matching alongside existing
  `fnmatch`, preserving wildcard behavior.
- `PROYECTO/ai/scripts/check-owned-paths.py` — synchronized byte-identical copy.
- `tests/test_harness.py` — focused CLI regression matrix through `--changed-file`.

Read-only: feature state, P1 context/evidence, README, ADRs, docs/notas, and all other scripts.
Do not alter package declarations, approved exceptions, read-only precedence, git collection,
output fields, or exit codes to make tests pass.

## Required red/green bite

Create the matrix before changing `matches`. Demonstrate each assertion red with current bare
`fnmatch`, then green after the smallest normalization rule:

| declaration | changed file | required result |
| --- | --- | --- |
| `tests` | `tests/test_harness.py` | ownership pass |
| `tests/` | `tests/test_harness.py` | ownership pass |
| `docs/adr` | `docs/adr/0051-x.md` | ownership pass |
| `tests` | `tests-extra/x.py` | `OWNERSHIP_FAIL`, exit 2 |
| `tests` | `outside/x.py` | `OWNERSHIP_FAIL`, exit 2 |

Run against the actual script and parse its JSON, not only an invented helper. Retain a control
for existing `src/**`, exact files, `shared_paths`, `read_only_paths`, and approved exceptions
from the nearby test fixtures.

## Risks and invariants

- Prefix trap: require a boundary (`tests/…`), never `startswith("tests")`; `tests-extra/x.py` is
  mandatory negative coverage.
- Slash normalization: accept one trailing slash directory declaration without treating empty or
  arbitrary glob patterns as directories.
- Read-only checks still win at `check-owned-paths.py:101-104`; support must apply consistently
  without turning a read-only violation into scope success.
- P1 owns both script copies and `tests/test_harness.py`: begin after P1 acceptance/integration.
  P2 also shares `tests/test_harness.py`; retain its independent guard tests. No P3 source overlap.

## Local validations and package gates

Run long commands through `ai/scripts/heartbeat-run.py --interval 20 -- <command>` (ADR-0041):

- `python3 -m unittest tests.test_harness.HarnessTests.<new_P4_owned_path_tests>`
- `python3 -m unittest tests.test_harness`
- `python3 -m unittest discover -s tests`
- `./ai/scripts/verify.sh`
- `./build.sh --check`
- `git diff --check`

Expected markers: `VERIFY_PASS`; `SELF_SCAFFOLD_SYNC_OK`, `GLOBAL_TREE_SYNC_OK`,
`BUILD_CHECK_PASS`. Focused P4 names are not created yet; no gate was run for this planning pack.
Runtime surface: `true` (ownership-gate behavior). Test owner: implementer.

## Done conditions

AC-08/09 close only when directory/trailing-slash declarations match their descendants,
`tests-extra` and a true outsider retain the ownership failure signal, scaffold copies synchronize,
and all gates are green.
