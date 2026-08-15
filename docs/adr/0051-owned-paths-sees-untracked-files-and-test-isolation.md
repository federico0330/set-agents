# ADR-0051 — `check-owned-paths.py` sees untracked files, and the test suite stops depending on
# import order for its own isolation

- Estado: Accepted (2026-08-14). Feature 027-controles-que-miran, PKG-1
  (`P1-alcance-y-aislamiento`). AC-01, AC-02, AC-03.

## Contexto

Two defects in the controls that are supposed to catch a package doing the wrong thing, both
measured live rather than assumed.

### AC-01 — the ownership gate never saw new files

`ai/scripts/check-owned-paths.py`'s default path (no `--changed-file`, the way every real
orchestrator invocation calls it per `ai/scripts/generate.py:177` and the agent prompts) built its
file list from `git diff --name-only <baseline> --` alone (`changed_files_from_git`, before this
ADR). `git diff` only ever compares **tracked** content; a file that was created and never `git
add`-ed is invisible to it. Measured live: `touch ai/scripts/_probe_new_file.py` then running the
gate against this same package's own state reported `out_of_scope` with the probe absent from
both `changed_files` and `out_of_scope` — silent, not merely "allowed". This is not hypothetical:
022/P1 created `ai/scripts/provider_registry.py` (the registry seven tables now derive from) and
the gate never flagged it, simply because it stayed untracked long enough for a gate run to miss
it.

### AC-02 — the test modules don't pass standalone

`python3 -m unittest tests.test_harness` alone produced 118 errors (all `ModuleNotFoundError`);
the full `python3 -m unittest discover -s tests` suite passes. Root cause, traced to one line:
`ai/scripts/models_config.py:28` does `import provider_registry` (a bare sibling import), which
only resolves once `ai/scripts/` is already on `sys.path`. `tests/test_harness.py` itself never
inserts that path — dozens of its tests (`self._import("models_config")`, ~200 call sites) rely
entirely on SOME other `tests/test_*.py` module having done `sys.path.insert(0, .../"ai/scripts")`
at its own import time, as a side effect, before `test_harness` needed it. Under `discover`,
alphabetically-earlier modules (`test_autonomy_policy.py` and over a dozen others) happen to
provide that side effect. Run `test_harness` alone and the accident never happens.

## Decisión

### 1. AC-01 — `changed_files_from_git` adds `git status --porcelain -z --untracked-files=all` as a
   second, independent source

`ai/scripts/check-owned-paths.py:40-` (`changed_files_from_git`): the existing `git diff
--name-only <baseline> --` call is kept as-is (it still owns tracked edits/renames against an
arbitrary baseline commit, which `git status` cannot express) and its result is now merged with
the `??` entries of `git status --porcelain -z --untracked-files=all` (the `--untracked-files=all`
flag matters: without it, an untracked directory collapses to one line instead of listing its
files, which would still hide most of the `provider_registry.py` class of bug). An untracked file
is treated exactly like a tracked one from that point on: it goes through the same
`owned_paths`/`read_only_paths`/`approved_exceptions` matching as everything else, so it can as
easily land in `out_of_scope` as pass. Both copies of the script that must stay byte-identical for
`build.sh --check`'s `SELF_SCAFFOLD_SYNC_OK` (`ai/scripts/check-owned-paths.py` and
`PROYECTO/ai/scripts/check-owned-paths.py`) got the same edit.

`-z` on the `git status` call is load-bearing, not cosmetic, and was caught while building this
fix rather than assumed away: plain (newline) `--porcelain` C-quotes any path containing a space —
measured live in this very repo (`docs/notas/00 - Proyecto.md` came back from `git status
--porcelain` as the literal string `"00 - Proyecto.md"`, quote characters included), while `git
diff --name-only` never quotes that same path. Parsing the quoted form would have fed a corrupted,
unmatchable path into `matches()` for any real untracked file with a space in its name — not a
synthetic edge case in a repo that already has one. `-z` (NUL-separated, always-unquoted paths per
`git status(1)`) is what the final code uses; `tests/test_harness.py` pins this with its own
bitten-red test (`test_owned_paths_gate_sees_untracked_files_with_spaces_in_their_name`), separate
from the plain-untracked-file test, so a reversion to plain `--porcelain` fails loudly instead of
only showing up the next time someone's untracked file happens to contain a space.

**The trap this ADR does not step in**: verified BEFORE touching the script what it already
reported on the live repo (`docs/specs/027-controles-que-miran/evidence/P1-implementer.md`). It
was already `OWNERSHIP_FAIL` for this package's own baseline — not from this bug, but from
unrelated tracked edits by other agents sharing the same working tree (`README.md`, under an
`approved_exceptions` waiver already; three `docs/notas/` files from a concurrent, unrelated
feature, not waived and not this package's to touch). After the fix, the same command still
reports `OWNERSHIP_FAIL` — the verdict does not flip — but the untracked-file set (this package's
own in-progress evidence/notas/context files, also not declared in `owned_paths` for this specific
package) is now additionally visible in `out_of_scope`. That is legitimate noise from the fix
doing its job in a shared, concurrently-edited tree, not a reason to loosen the match — nothing in
`matches()`/`owned_paths` was touched.

### 2. AC-02 — one insertion in `tests/__init__.py`, nothing else touched

`tests/__init__.py` gains a single `sys.path.insert(0, str(Path(__file__).resolve().parent.parent
/ "ai/scripts"))`. Python guarantees a package's `__init__.py` runs before any of its submodules
are imported, regardless of which submodule `unittest` loads first or whether the rest of the
suite ever runs — so this is the one choke point that fixes the accident structurally instead of
hoping some other module keeps volunteering the side effect. The ~18 individual
`sys.path.insert(0, ...)` lines already present at the top of other `test_*.py` files are left
untouched: they are redundant now, not wrong, and touching dozens of files for a problem one line
already closes would have been exactly the "solución de cien" the context pack asked to avoid.

A first clean, isolated `tests.test_harness` run WITH the `tests/__init__.py` fix in place still
did not come back at zero errors — ~119 tests failed with a NEW shape,
`KeyError: 'set_agents_app'` at `set_agents_app.py:32`
(`sys.modules.setdefault("set_agents_app", sys.modules[__name__])`), not the one the context pack
measured. That line requires `sys.modules[__name__]` to already exist, true for a real `import
set_agents_app` (Python registers a module before running its body precisely so a self-lookup like
that works) and false for `HarnessTests._import()` (`tests/test_harness.py:268`, ~200 call sites
via `self._import("set_agents_app")`, direct or through `_context_fixture`), which built the
module via `importlib.util.module_from_spec` + `exec_module` without ever registering it first.
Same accident shape as the sys.path one, invisible under `discover` only because some other test
module's real `import set_agents_app` populated `sys.modules` first. This file already had a
similar pattern in a sibling class (`TuiTests._import`, loading `tui.py`, with its own comment
explaining exactly why the registration is required for `dataclass`/self-referential machinery):
register `sys.modules[name] = module`, pop it back out on exception, otherwise leave it.

Copying that exact pattern into `HarnessTests._import` fixed the standalone case and broke the
FULL suite instead, caught only by the `discover` gate, not by any single-file isolation run:
`routing_cli.py`'s `_resolve_context_pack`/`_validate_context_pack_path` do a LAZY `import
set_agents_app` inside their own bodies (`set_agents_app.py`'s own module docstring names this
pattern), resolved against `sys.modules` at CALL time, not import time. Leaving `HarnessTests
._import`'s freshly-`exec`ed module sitting in `sys.modules["set_agents_app"]` after returning
meant `tests/test_routing.py`'s own top-level `import set_agents_app` — and any later lazy
self-import from `routing_cli.py` — resolved to THAT stale module (built under whatever env this
helper happened to mock for some earlier `HarnessTests` test) instead of a canonical one, once
both files' tests share one process under `discover`. Symptom:
`test_resolve_context_pack_opens_only_the_named_file`,
`test_resolve_context_pack_phase_freshness_and_default_resolution`, and
`test_validate_context_pack_path_rejects_unsafe_values` (`tests/test_routing.py`) started
resolving paths against this process's real repo root instead of each test's own temp dir.

The fix scopes the registration to the exact duration of `exec_module`: `HarnessTests._import`
saves whatever `sys.modules.get(name)` held before the call (present or absent) and restores that
exact value in a `finally`, regardless of success or failure — never TuiTests' "leave it or pop
it", always "put back exactly what was there". `HarnessTests._import` gained this at its one call
site rather than auditing its ~200 callers.

### 3. AC-03 — a regression guard for each fix in (2), not a re-run of the whole suite

`tests/test_harness.py`'s `HarnessTests` gains
`test_module_isolation_gate_fails_if_the_sys_path_fix_regresses`: it runs, as a subprocess, the
exact command family AC-02 is measured by (`python3 -m unittest tests.test_harness.<target>`)
against a single method already known to require the `tests/__init__.py` fix
(`test_models_config_resolves_area_and_role_override`, which calls `self._import("models_config")`
→ `models_config.py`'s bare `import provider_registry`), and asserts it exits 0 with no
`ModuleNotFoundError` in stderr. Bitten live: `tests/__init__.py` was reverted to its pre-fix
content (`cp`, never `git checkout`), the new test went red with the exact `ModuleNotFoundError:
No module named 'provider_registry'` this ADR's AC-02 section describes, then the fix was restored
(`cp` back) and the test went green again. Deliberately not "re-run the entire ~500-method
`test_harness` module inside itself" — that would multiply CI runtime for the same causal
guarantee this single, pinned target already provides.

A second, equally pinned test,
`test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses`, covers the
`HarnessTests._import` registration fix the same way, against
`test_app_config_writers_never_clobber_each_other` (known to call
`self._import("set_agents_app")`). Bitten the same way: `HarnessTests._import` was reverted to its
pre-fix body, the new test went red with `KeyError: 'set_agents_app'`, the fix was restored and it
went green.

A third test, `test_import_helper_leaves_sys_modules_exactly_as_it_found_it`, pins the
save-and-restore invariant directly and in-process (no subprocess needed): it seeds
`sys.modules["set_agents_app"]` with a sentinel, calls `self._import("set_agents_app")`, and
asserts the sentinel — not `_import`'s own module — is what's left behind; then repeats with the
name absent beforehand and asserts it is absent afterward. This is the one that would have caught
the cross-file pollution bug described above BEFORE it needed the full `discover` gate to surface:
bitten live by temporarily reverting `HarnessTests._import` to the naive "register and leave it"
version (the one that broke `tests/test_routing.py`), which failed this new test directly with
`AssertionError: <module 'set_agents_app' from '.../ai/scripts/set_agents_app.py'> is not
<module 'set_agents_app'>` — the exact defect, without needing the slower cross-file reproduction
— then restored, green again.

## Alternativas rechazadas

- **AC-01: relax `owned_paths`/`approved_exceptions` matching so the newly-visible files stop
  failing.** Rejected — the context pack named this trap explicitly. The newly-visible
  out-of-scope entries in the live repo are real (other agents' concurrent, unrelated edits); the
  fix is to see them, not to make the gate blind to more things.
- **AC-01: replace `git diff --name-only <baseline> --` with `git status --porcelain` alone.**
  Rejected — `git status` has no `<baseline>` concept; it only compares the working tree to the
  index/HEAD. A package gated against an older baseline commit would lose visibility into tracked
  edits made since that commit. Both sources are kept, merged.
- **AC-02: add `sys.path.insert` to every `test_*.py` that needs `ai/scripts/` on the path, or
  delete the now-redundant ones.** Rejected — decenas of edits for a problem one line in
  `tests/__init__.py` already closes; the existing per-module inserts are harmless duplicates, not
  a defect to clean up under this package's scope.
- **AC-02: a `conftest.py` or a `sitecustomize.py`.** Rejected — `pytest` is not installed in this
  environment (`conftest.py` is a pytest-only mechanism, dead weight here), and
  `sitecustomize.py` patches every `python3` invocation on the machine, not just this suite's —
  broader blast radius than the problem calls for. `tests/__init__.py` is scoped to exactly the
  package that has the problem.
- **AC-03: re-run the full `tests.test_harness` module (or `discover -s tests`) inside the new
  regression test.** Rejected — same causal guarantee (the `tests/__init__.py` sys.path insertion)
  is already exercised by one pinned, fast target; multiplying the full suite's runtime inside
  itself buys no additional coverage of the actual regression this ADR closes.
- **AC-02 (`HarnessTests._import`): copy `TuiTests._import`'s "register and leave it" pattern
  verbatim.** Tried first, rejected after measuring: it fixed `tests.test_harness` standalone and
  broke `tests/test_routing.py` under the full `discover` suite, because `set_agents_app` (unlike
  `tui`) is lazily self-imported at call time from another module (`routing_cli.py`). The
  save-and-restore version fixes both without special-casing which names are "safe" to leave
  registered.

## Consecuencias

- `check-owned-paths.py`'s default (git-derived) invocation now reports untracked files exactly
  like tracked ones — a package creating a new file outside `owned_paths` can no longer do so
  silently. Any in-flight package with an undeclared untracked file inside its own working tree
  will see it in `out_of_scope`/`changed_files` where it did not before; this is the control
  working, not a regression, and no package's `owned_paths` were touched to compensate.
  `--changed-file`-driven invocations (used by every pre-existing test of this script) are
  unaffected — the git-derived path is additive, exercised by four dedicated tests.
- `python3 -m unittest tests.test_harness` and `python3 -m unittest tests.test_routing` both pass
  standalone now, not only under `discover`. `python3 -m unittest discover -s tests` (the full
  suite, all files together) stays green too — this is what caught the cross-file pollution the
  save-and-restore fix closes. No test file other than `tests/__init__.py` and
  `tests/test_harness.py` (six new/guard tests total, no other file) was touched.
- A regression of the `tests/__init__.py` fix is caught by
  `test_module_isolation_gate_fails_if_the_sys_path_fix_regresses`, which fails with the same
  `ModuleNotFoundError` this ADR's AC-02 section reproduces, not a generic assertion. A regression
  of the `HarnessTests._import` registration fix is caught two ways: the same subprocess pattern
  by `test_module_isolation_gate_fails_if_the_set_agents_app_registration_regresses`, and directly,
  in-process, by `test_import_helper_leaves_sys_modules_exactly_as_it_found_it`.

## Evidencia

`docs/specs/027-controles-que-miran/evidence/P1-implementer.md` — tabla AC → cambio
(`archivo:línea`) → prueba; el chequeo viendo (o no) el archivo de prueba, antes y después; los dos
módulos de test corriendo aislados con su conteo, más la suite completa (`discover`); qué reportaba
el chequeo sobre el repo real antes del cambio; los seis tests nuevos mordidos en rojo
(neutralizados, confirmado el rojo, revertidos); y los gates.
