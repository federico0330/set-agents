# ADR-0052 — A bare directory declaration in `owned_paths`/`read_only_paths`/`approved_exceptions`
# means the whole subtree, canonicalized before it is ever compared

- Estado: Accepted (2026-08-14). Feature 027-controles-que-miran, PKG-4
  (`P4-owned-paths-matchea-directorios`). AC-08, AC-09.

## Contexto

Discovered **by** P1: making `check-owned-paths.py` see untracked files (ADR-0051) exposed a false
positive that had been silently masked before. `matches()` fed a bare `owned_paths` entry (e.g.
`"tests"`) straight to `fnmatch`, which never treats a directory declaration as covering the files
inside it — `matches("tests/test_harness.py", ["tests"])` measured `False`. Consequence measured
live: P1's own gate run reported **18 in-scope files** (including `tests/test_harness.py` itself) as
`out_of_scope`. This is the mirror of P1's bug: P1 made the gate SEE new files; this closed the false
positive that seeing them exposed.

The straightforward first fix (`path == directory or path.startswith(directory + "/")`, gated behind
a metacharacter-free check so `src/**` and other globs keep their pre-existing `fnmatch`-only
behavior) shipped in the implementer's pass. A subsequent independent review of that pass
(`docs/specs/027-controles-que-miran/evidence/P4-repair.md`) found the boundary check itself was not
normalized, producing two further defects, plus one evidence error and one hollow test guard,
repaired together with this ADR:

1. **P4-F01 (medium) — path traversal through the boundary.** `path.startswith(directory + "/")` on
   raw, un-normalized text lets a `..` segment in the changed-path string borrow a directory's
   ownership: `"tests/../ai/scripts/pwn.py".startswith("tests/")` is `True`, even though the file it
   actually names (once `..` is resolved) is `ai/scripts/pwn.py`, not anything under `tests/`.
   Measured live against the unpatched (implementer) script: `owned_paths: ["tests"]` let
   `tests/../ai/scripts/pwn.py` and `tests/../../etc/passwd` both through as `OWNERSHIP_PASS` — a
   genuine relaxation AC-09 forbids, introduced by this same diff (the pre-existing `fnmatch`-only
   code rejected both, since neither is a literal or glob match for `"tests"`).
2. **P4-F04 (low) — declaration-spelling asymmetry.** The literal-`fnmatch` branch already tolerates
   a leading-slash-style pattern (`fnmatch("/" + normalized, pattern)`), and the changed-path side of
   `matches()` already normalizes backslashes (`path.replace("\\", "/")`) — but the directory-
   descendant boundary read the declaration text verbatim. `/tests`, `./tests`, `docs//adr` and
   `tests\sub` (Windows-style) each failed to cover their own descendants even though the equivalent
   "plain" spellings (`tests`, `docs/adr`) did. All rows failed toward the strict side (never a false
   `PASS`), but `feature_state_lib/cli_lifecycle.py:277` stores `args.owned_path` verbatim, so any
   package declaration can end up in one of these spellings by accident.
3. **P4-F02 (medium) — a false claim in the implementer's own decision record.** The evidence's
   reason #4 for accepting `approved_exception` directory-widening asserted a directory-wide
   exception "can only pull a file out of `out_of_scope`, never out of `read_only_violations`". The
   loop is `if matches(path, read_only) and not approved_exception(package, path):` — the exception
   DOES cancel a `read_only` match too, for any descendant of the approved directory. Measured live:
   `read_only_paths: ["Global"]` plus `approved_exceptions: [{"path": "Global", "status":
   "approved"}]` turns `Global/claude-code/settings.json` from `read_only_violations` (pre-P4
   behavior) into a silent `OWNERSHIP_PASS` — and neither of the two review tests written for this
   trap (`…never_overrides_read_only_precedence`, `…widens_to_cover_descendants_by_design`) actually
   exercised both fields non-empty at once, so the false claim went untested.
4. **P4-F03 (low) — a hollow regression guard.** The test meant to pin "the directory-descendant
   rule stays off for glob patterns" used `src/**` for both its positive and negative case. `fnmatch`
   translates `*` to `.*`, which already matches across `/` — so both cases already passed/failed
   correctly through plain `fnmatch` alone, with or without the metacharacter carve-out. Measured
   live: deleting `_is_bare_directory_pattern`'s body entirely (`return bool(pattern)`) still left
   the test green, 5/5.

## Decisión

### 1. AC-09 (P4-F01) — canonicalize the changed path before any boundary check

`ai/scripts/check-owned-paths.py`'s `matches()` now computes `normalized = _canonical_path(path)`,
where `_canonical_path` is `posixpath.normpath` applied after a `\\` → `/` swap. `posixpath.normpath`
is what collapses a `..` segment to the real location it names (`tests/../ai/scripts/pwn.py` →
`ai/scripts/pwn.py`; `tests/../../etc/passwd` → `../etc/passwd`) before either the literal-`fnmatch`
branch or `_is_directory_descendant`'s `startswith` ever sees the raw text. This is a general fix,
not a `..`-specific reject list: after normalization, a path is compared in the same canonical form
whether or not it happens to contain `..`, so a legitimately-nested file that merely spells its own
path awkwardly (`tests/./real.py`) is unaffected, and a genuinely escaping one no longer borrows a
boundary it does not cross.

### 2. AC-08 (P4-F04) — canonicalize the declaration the same way, minus the leading-slash exception

`_is_directory_descendant` now computes its `directory` via `_canonical_declaration(pattern)`: same
`\\` → `/` swap and `posixpath.normpath`, plus a leading `/` stripped first — a leading `/` on a
*declaration* is a repo-root anchor (the existing literal-`fnmatch` branch already tolerates that
spelling), not a filesystem-absolute path, so it must not survive into `normpath` as one (which would
keep it absolute and make it never match a relative changed path). `/tests`, `./tests`, `docs//adr`,
`tests//` and `tests\sub` now all canonicalize to the same boundary as their "plain" form.

### 3. P4-F02 — the record is corrected, the decision is not reopened

The false reason #4 in `docs/specs/027-controles-que-miran/evidence/P4-implementer.md` is corrected
in place (marked as a post-repair correction, not silently rewritten) to state the real effect:
`approved_exception` directory-widening cancels a `read_only_violations` match too, for any
descendant. **The orchestrator accepts this as the intended consequence of the same widening
decision**, for the same reasons already on record (reasons 1-3, unchanged and still true): an
`approved_exception` is already a human-reviewed, package-specific override (`status: "approved"`),
and giving the same declared pattern two different meanings depending on which of the three call
sites (`owned`, `read_only`, `approved_exception`) reads it would be exactly the kind of late-
discovered inconsistency this package exists to close. What changes is that this consequence is now
named, tested (`test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants`),
and no longer only asserted narratively against a claim that measured false.

### 4. P4-F03 — replace the hollow control with one that actually discriminates

`test_owned_paths_directory_descendant_rule_does_not_relax_existing_glob_patterns` gains a third,
adversarial case: `owned_paths: ["config/*.json"]` (a pattern with a metacharacter, this time NOT at
the tail) against `config/*.json/evil/x.py` — a changed-path string that literally contains the
pattern's glob text as a path segment. Plain `fnmatch` correctly rejects it (the string does not end
in `.json`). A `path.startswith(pattern.rstrip("/") + "/")` check, if it were allowed to run on a
pattern that still carries metacharacters, would wrongly accept it, because the raw text
`"config/*.json/evil/x.py".startswith("config/*.json/")` is `True`. Bitten live: with
`_is_bare_directory_pattern` neutralized to `return bool(pattern)`, this exact case flips from
`OWNERSHIP_FAIL` to `OWNERSHIP_PASS`; restored, `OWNERSHIP_FAIL` again. The original `src/**` case is
kept as a plain sanity check, not as the discriminating control anymore.

## Effect by consumer (the semantics this ADR fixes in one shared place)

`matches()` feeds three call sites, and the canonicalization above applies to all three identically —
there is no way to apply it to only `owned`/`read_only` without bifurcating `matches()` or
duplicating the boundary logic in a fourth place:

- **`owned_paths`** (`check-owned-paths.py:158`): a bare directory declaration owns every file below
  it, on the canonical form of both sides. AC-08's whole point.
- **`read_only_paths`** (`:155`): same canonicalization, checked BEFORE `owned_paths` in the loop
  (`continue` on match) — the directory-descendant rule never demotes a `read_only_violations` hit
  into an `out_of_scope` one; it only changes what counts as a match in the first place. Pinned by
  `test_owned_paths_directory_descendant_never_overrides_read_only_precedence`.
- **`approved_exceptions`** (`:88`, via `matches(path, [pattern])` with one pattern): same
  canonicalization, and therefore the same widening AC-08 grants `owned_paths` — including the
  ability to cancel a `read_only_violations` match for a descendant, per the corrected P4-F02
  decision above. Pinned by two tests: the `owned_paths`-empty case
  (`test_approved_exception_directory_declaration_widens_to_cover_descendants_by_design`) and the
  `read_only_paths` interaction
  (`test_approved_exception_directory_declaration_also_cancels_read_only_violation_for_descendants`).

## Alternativas rechazadas

- **P4-F01: reject any changed path containing a literal `..` substring, instead of normalizing.**
  Rejected — a reject-list is narrower than the actual invariant (a path must resolve to where it
  claims to be) and would not fix P4-F04's separate declaration-spelling gap, which has nothing to do
  with `..`. `posixpath.normpath` is the one mechanism that satisfies both AC-08 (equivalent
  spellings match) and AC-09 (no escaped path borrows a boundary).
- **P4-F01: strip a leading `/` from the *changed path* too (symmetric with the declaration side).**
  Rejected — git-derived changed paths are never absolute in practice, and doing so on the path side
  (rather than only the declaration side) would silently relativize a genuinely malformed
  `--changed-file` argument instead of leaving it to fail a literal comparison. Only the declaration
  side needed the leading-slash tolerance, to match the literal-`fnmatch` branch's existing behavior.
- **P4-F02: narrow `approved_exception`'s directory-widening instead of correcting the record.**
  Rejected — reopening a decision already accepted by the orchestrator (with reasons 1-3 still valid
  and unchallenged) is a scope expansion a repair pass does not get to make unilaterally; the finding
  asked for the record and the coverage to be fixed, not the semantics.
- **P4-F03: keep the `src/**` case as the sole control and add a comment noting its limits.**
  Rejected — a comment does not fail when the exclusion regresses; only a genuinely discriminating
  assertion does, which is what a repair test exists to provide.

## Consecuencias

- A `owned_paths`/`read_only_paths`/`approved_exceptions` directory declaration means "this directory
  and everything below it" consistently across all three fields and across `/tests`, `./tests`,
  `tests/`, `tests//`, `docs//adr` and `tests\sub` spellings — never a different boundary depending
  on which field or which spelling a package happened to use.
- A changed-path string containing a `..` segment is resolved to the real location it names before
  any ownership/read-only/exception check runs; it can no longer borrow a directory's boundary by
  spelling itself with a traversal segment.
- `approved_exceptions` declared over a bare directory widen to cover the whole subtree for all three
  consumers that read `matches()`, including canceling a `read_only_violations` hit — documented here
  and in the corrected implementer evidence, not left to be rediscovered from the code.
- Both copies of the script (`ai/scripts/check-owned-paths.py`,
  `PROYECTO/ai/scripts/check-owned-paths.py`) stay byte-identical, verified by `cmp` and
  `build.sh --check`'s `SELF_SCAFFOLD_SYNC_OK`.

## Evidencia

`docs/specs/027-controles-que-miran/evidence/P4-implementer.md` (original AC → cambio → prueba table,
corrected reason #4) and `docs/specs/027-controles-que-miran/evidence/P4-repair.md` (this ADR's
finding → change → verification table; the F01/F04 matrices re-run after the fix; each new/changed
test neutralized, confirmed red, reverted, with literal output; the `cmp` proof of script identity;
`build.sh --check`).
