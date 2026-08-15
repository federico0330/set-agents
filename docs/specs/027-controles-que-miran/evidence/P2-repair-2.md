# P2 repair pass 2 — seven new findings from the independent delta review

Date: 2026-08-15 (started 2026-08-14). Repair agent, single pass, no worktree, working
directly on `/home/federico/SET-AGENTES`. Scope: `tests/__init__.py`,
`tests/test_harness.py`, `tests/test_routing.py`, and this evidence file only. `build.sh`,
`ai/scripts/`, `PROYECTO/`, and the P3/P4 in-flight files listed in the task were not
touched (confirmed below).

## Table: finding -> change -> verification

| Finding | Severity | Change (file:line) | Verification |
|---|---|---|---|
| P2-F04 | high | `tests/test_routing.py:1195-1206` — the 19th bare `subprocess.run(["./build.sh"], cwd=ROOT, ...)` call site now writes to a private `tempfile.mkdtemp(prefix="build-output-")` via `--output`, and reads the generated orchestrator copy from there instead of `ROOT/Global/...` | Focused green run below; full-suite `git status`/manifest below shows zero `Global/` drift |
| P2-F05 | medium | `tests/test_harness.py:77-284` (new module-level lint helpers: `_resolve_expr`, `_output_value_is_unsafe`, `_command_lacks_safe_guard`, `_is_unsafe_build_sh_call`, `_own_calls`, `_scan_function_body_for_build_sh`, `_find_build_sh_writes`) + `tests/test_harness.py:417-441` (`test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag`, rewritten to scan every `tests/*.py` module, not one class) | All three reviewer bypasses reproduced and caught red, by name, then reverted; see below |
| P2-F06 | medium | `tests/test_harness.py:251-264` (`_external_probe_directory` helper, using `tests._ORIGINAL_POPEN` to create/remove a `/var/tmp` sibling directory outside `_TEST_SANDBOX`) + `tests/test_harness.py:8959-8983` and `8984-9012` (both P2-F01 descendant tests now target that external, writable-without-confinement directory instead of `/etc/hosts`) | Red-bite with the whole `_sandboxed_popen` boundary deleted: both now fail (`0 == 0`); restored, both green again — below |
| P2-F07 | medium | `tests/__init__.py:194-198` (`_deny_if_outside_sandbox`, factored out), `tests/__init__.py:210-233` (`_resolved_sqlite_target`), `tests/__init__.py:244-245` (new `sqlite3.connect` branch in `_test_write_audit`) + `tests/test_harness.py:8871-8898` (new regression test) | Reviewer's exact escape probe now blocked before the file is created; red-bite (branch neutralized) reproduces the original escape; restored, green — below |
| P2-F08 | low | `tests/__init__.py:246-262` — a measured, declared-limitation comment on the `"open"` branch of `_test_write_audit` | Not fixed (CPython's `"open"` audit event carries no `dir_fd`); the gap is reproduced and measured below, then documented in the code at the exact point it applies |
| P2-F09 | low | Method only, no file changed (`build.sh` is out of my owned paths) — this evidence's own final measurement uses a sha256 manifest of `Global/` (568 files) before/after, not only `git status --porcelain` | See "Final AC-04 measurement" below |
| P2-F10 | low | `tests/test_harness.py:491-524` — new `test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook`, exercising `build.sh`'s default `MODE="generate"` branch and `ensure_drift_hook` inside a guest copy (same pattern as `test_build_check_detects_global_drift_and_names_the_file`) | Focused green run below; confirmed it never touches the real `Global/` (git status clean after) |

## P2-F04 — the 19th call site

`tests/test_routing.py:1148` (`test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin`) called `subprocess.run(["./build.sh"], cwd=ROOT, ...)` directly, bypassing the `--output <tmp>` pattern the P2-portabilidad.md seam repair applied to the 18 call sites in `tests/test_harness.py`. Fixed with the same pattern: a private `tempfile.mkdtemp(prefix="build-output-")`, `--output <tmp>` appended to the `build.sh` invocation, and the orchestrator-copy read redirected from `ROOT / "Global" / host_harness / ...` to `<tmp> / host_harness / ...`. The test still needs the write (it asserts on the generated doctrine text), so the call could not simply be deleted.

Focused green:

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v tests.test_routing.RoutingTests.test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin
test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin (...) ... ok

Ran 1 test in 5.427s

OK
```

`git status --porcelain` immediately after showed no `Global/` entries (only my own owned files plus pre-existing unrelated in-flight changes from other packages — see the full-suite section for the complete picture).

## P2-F05 — the lint's three blind spots

The old lint only ever inspected `inspect.getsource(HarnessTests)` (one class in one file) and only recognized the literal shape `run("./build.sh", "--output", ...)` with `--output` merely *present* — never verifying the destination the value actually resolved to.

Replaced with a small static analyzer (`tests/test_harness.py:77-284`) that:

- Scans every `tests/*.py` module (`test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag` now does `for path in sorted((ROOT / "tests").glob("*.py"))`), every class and every module-level function in it — not one hardcoded class.
- Resolves a build.sh command through local variable aliases within the same function (`_resolve_expr`, including `with ... as x:` bindings, not only `ast.Assign`), so `script = "./build.sh"; run(script)` is recognized.
- Recognizes a direct `subprocess.run`/`subprocess.Popen`/`os.system` bypass of the `run()` test helper, not only `run(...)` itself (`_is_unsafe_build_sh_call`), and requires an explicit `cwd` that provably does not resolve through `ROOT` — an omitted `cwd` is treated as risky, since that is this suite's own ambient default.
- Rejects a `--output` value that is not evidently temporary (`_output_value_is_unsafe`): unsafe if the value's resolution chain includes the free name `ROOT`, or if it is a fully literal/computed path that never traces through `tempfile.mkdtemp`/`mkstemp`/`TemporaryDirectory`/`_generate_output()`. A value derived from an *unresolved* free name (e.g. a function parameter like `def build_staging(staging_dir)` in `tests/test_provider_registry.py`) is given the benefit of the doubt — the lint cannot see the caller's contract across function boundaries; this is a declared, accepted limitation (see "Sin verificar" below), not a silent gap in the specific bypasses this finding named.

### Green on the current (already-clean) codebase

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag
test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag (...) ... ok

Ran 1 test in 0.567s

OK
```

### Red bite: all three reviewer bypasses, in one temporary scratch module

A throwaway file `tests/_scratch_p2f05_bypass_check.py` (never part of the suite; deleted immediately after) contained, verbatim, the three patterns from the finding:

```python
# bypass A: --output pointing at ROOT
def bypass_a():
    generated = ROOT / "Global"
    run("./build.sh", "--output", str(generated))

# bypass B: variable intermediate for the script name
def bypass_b():
    script = "./build.sh"
    run(script)

# bypass C: direct subprocess.run, bypassing run()
def bypass_c():
    subprocess.run([str(ROOT / "build.sh")], cwd=ROOT, check=True,
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
```

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag
test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag (...) ... FAIL

AssertionError: Lists differ: ['_scratch_p2f05_bypass_check.bypass_a', '[73 chars]s_c'] != []

First list contains 3 additional elements.
First extra element 0:
'_scratch_p2f05_bypass_check.bypass_a'

+ []
- ['_scratch_p2f05_bypass_check.bypass_a',
-  '_scratch_p2f05_bypass_check.bypass_b',
-  '_scratch_p2f05_bypass_check.bypass_c'] : these tests/*.py functions invoke build.sh (...) ...

Ran 1 test in 0.561s

FAILED (failures=1)
```

All three bypasses caught, by name. Scratch file removed with `rm`, then confirmed green again:

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag
test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag (...) ... ok

Ran 1 test in 0.566s

OK
```

## P2-F06 — the two P2-F01 regressions used `/etc/hosts`

`/etc/hosts` is unwritable by a plain non-root user with or without the bwrap boundary — its
`ok` result was never evidence of confinement. Both tests now target a directory created
directly under the OS temp root (`/var/tmp`, bypassing this run's own relocated
`tempfile.tempdir`), via a new `_external_probe_directory()` context manager
(`tests/test_harness.py:251-264`). That directory is a genuine discriminator: writable for
an unconfined process, but covered by bwrap's blanket `--ro-bind / /` for a confined child
(only `_TEST_SANDBOX` itself — a distinct, sibling path — is separately re-bound writable).

It is created/removed via `tests._ORIGINAL_POPEN` (the real, unwrapped `Popen`, running
`mkdir`/`rm -rf` in a genuinely separate OS process) rather than
`tempfile.mkdtemp()`/`shutil.rmtree()`, because the first attempt showed THIS
interpreter's own in-process audit hook — correctly — rejects any write outside the
sandbox from the parent process itself:

```
PermissionError: test write outside private sandbox denied: /var/tmp/set-agentes-unittest-external-probe-...
```

`test_unittest_descendant_preserves_fixture_path_inside_private_sandbox` was also extended
so the same child that successfully runs the fixture-local `fixture-probe` via `PATH` (the
original assertion) then also attempts the external write in the SAME process, proving
legitimate PATH-based execution keeps working while escaping writes do not.

### Green, bwrap present (no neutralization)

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing \
  tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox
test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing (...) ... ok
test_unittest_descendant_preserves_fixture_path_inside_private_sandbox (...) ... ok

Ran 2 tests in 0.607s

OK
```

### Correctly skipped without bwrap (unchanged behavior)

```
$ SET_AGENTS_TEST_NO_BWRAP=1 python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing \
  tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox
descendant-boundary: off (bwrap not found)
... skipped 'P2-F01 descendant boundary requires bwrap (portable degradation, 2026-08-14)'
... skipped 'P2-F01 descendant boundary requires bwrap (portable degradation, 2026-08-14)'

Ran 2 tests in 0.000s

OK (skipped=2)
```

### Red bite: the whole P2-F01 boundary deleted (exact reviewer methodology)

`tests/__init__.py:164` (`subprocess.Popen = _sandboxed_popen`) commented out (backed up
with `cp` first, never `git checkout`/`git restore`/`git stash`):

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing \
  tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox
test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing ... FAIL
test_unittest_descendant_preserves_fixture_path_inside_private_sandbox ... FAIL

FAIL: test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing
AssertionError: 0 == 0 :

FAIL: test_unittest_descendant_preserves_fixture_path_inside_private_sandbox
AssertionError: 0 == 0 : fixture-probe

Ran 2 tests in 0.044s

FAILED (failures=2)
```

Both now genuinely bite where the original `/etc/hosts`-based versions did not (per the
finding: with the guard fully removed, the originals "siguieron en ok"). Restored with
`cp` from the backup; diff against backup empty; confirmed green again (see the block
above).

## P2-F07 — sqlite3 escapes the audit hook

`sqlite3.connect` never calls `open()`/`os.*` — it talks to SQLite's own C library, so none
of the events the guard already listened for ever fired for it. `sqlite3.connect` raises
its own dedicated audit event, `"sqlite3.connect"`, with the exact `database` argument, before
the file is created — so a rejection here is still before-mutation.

Added `_resolved_sqlite_target` (`tests/__init__.py:210-233`): resolves a plain path or a
`file:` URI (honoring an explicit `?mode=ro`, which never creates/mutates), skips
`:memory:`/`""`. Factored `_deny_if_outside_sandbox` out of `_reject_write_outside_sandbox`
(`tests/__init__.py:194-207`) so both share the same final check. Added the
`"sqlite3.connect"` branch to `_test_write_audit` (`tests/__init__.py:244-245`).

### Reviewer's exact probe, now blocked

```
$ python3 -c "
import tests, sqlite3
target = '/var/tmp/sonda-p2f07-repair-escape.db'
try:
    conn = sqlite3.connect(target)
    conn.execute('CREATE TABLE t (x INT)'); conn.commit(); conn.close()
    print('sqlite3 -> ESCAPO')
except PermissionError as e:
    print('sqlite3 -> bloqueado:', e)
"
sqlite3 -> bloqueado: test write outside private sandbox denied: /var/tmp/sonda-p2f07-repair-escape.db
$ ls /var/tmp/sonda-p2f07-repair-escape.db
ls: no se puede acceder a '/var/tmp/sonda-p2f07-repair-escape.db': No existe el fichero o el directorio
```

`:memory:` and an in-sandbox path both still work (same script, additional lines):
`memory -> ok (esperado)`, `inside sandbox -> ok (esperado), exists: True`.

### New regression test, green

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_sqlite3_connect_outside_the_sandbox_before_mutation
test_unittest_write_guard_rejects_sqlite3_connect_outside_the_sandbox_before_mutation ... ok

Ran 1 test in 0.024s
OK
```

### Red bite: the `sqlite3.connect` branch neutralized

`tests/__init__.py:244-245` temporarily changed to `pass` (backed up with `cp` first):

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_sqlite3_connect_outside_the_sandbox_before_mutation
... ERROR
sqlite3.OperationalError: unable to open database file

Ran 1 test in 0.002s
FAILED (errors=1)
```

Restored with `cp` from the backup; diff against backup empty; confirmed green again
(see block above).

### Decided, not covered: `shutil.*` / `os.setxattr`

Per the finding's own instruction ("mirá si hay otros eventos de la misma clase... cubrí lo
que puedas probar, y lo que dejes afuera declaralo"):

- `shutil.*` (`copytree`, `copy2`, `rmtree`, `move`, all used across `ai/scripts/*.py`) is
  pure Python built on `open()`/`os.rename`/`os.remove`/`os.rmdir`/`os.mkdir` — all already
  audited. No separate hook needed; verified by reading CPython's `shutil` source for the
  functions actually used in this repo (`copytree`, `copy2`, `rmtree`, `move`) — none of them
  perform a raw syscall the existing branches don't already see.
- `os.setxattr` has its own audit event (`"os.setxattr"`) but is not called anywhere in
  `ai/scripts/*.py` or `ai/scripts/routing_core/*.py` (`grep -rn setxattr` — no hits). Left
  uncovered and declared here rather than added speculatively for a vector this codebase
  does not exercise.

## P2-F08 — `dir_fd` on the `open` event (declared limitation, not fixed)

CPython's `"open"` audit event carries only `(path, mode, flags)` — verified directly:

```
$ python3 -c "
import sys, os
def hook(event, args):
    if event == 'open': print(event, args)
sys.addaudithook(hook)
fd = os.open('/tmp', os.O_RDONLY)
os.open('probe.txt', os.O_WRONLY | os.O_CREAT, dir_fd=fd)
"
open ('/tmp', None, 524288)
open ('probe.txt', None, 524353)
```

The exact same `(path, None, flags)` shape fires with or without `dir_fd=`; CPython never
transmits it for this event (unlike `os.remove`/`os.rename`/etc., which do, and which
P2-F02 already made `dir_fd`-aware). Measured, concretely — a real escape:

```
$ python3 -c "
import tests, os
from pathlib import Path
external_dir = Path('/var/tmp')
dfd = os.open(str(external_dir), os.O_RDONLY)
os.chdir(str(tests._TEST_SANDBOX))
target_fd = os.open('p2-f08-probe.txt', os.O_WRONLY | os.O_CREAT, dir_fd=dfd)
os.close(target_fd)
"
$ ls -la /var/tmp/p2-f08-probe.txt
-rwxr-xr-x 1 federico federico 0 ago 14 23:48 /var/tmp/p2-f08-probe.txt
```

(cleaned up immediately with `rm`). Not closeable from the `"open"` event itself — no
dir_fd-aware variant exists in CPython. Documented in place at
`tests/__init__.py:246-262`, adjacent to the exact branch it applies to, with this
measurement summarized inline.

## P2-F09 — measurement method corrected

`build.sh` is not in this package's owned paths and was not touched. What changed is the
**method**: the final AC-04 measurement below uses a sha256 manifest of every file under
`Global/` (568 files) before and after, plus `git status --porcelain`, rather than relying
on `git status --porcelain` alone — `ensure_active_profile` (`build.sh:16-31`) writes the
gitignored `active-profile` file, which `git status` structurally cannot see. The manifest
and `git status` below are both byte-identical/unchanged across the full run.

## P2-F10 — `generate` mode and `ensure_drift_hook` regain coverage

New `test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook`
(`tests/test_harness.py:491-524`), same guest-copy pattern as
`test_build_check_detects_global_drift_and_names_the_file`: copies the checkout into a
`TemporaryDirectory`, adds a minimal `.git/hooks/` stand-in (ensure_drift_hook only checks
it exists, never that it's a real git repo), dirties `Global/opencode/AGENTS.md`, runs a
bare `bash <guest>/build.sh` (no flags), and asserts: exit 0; all four harness directories
regenerated; the dirtied file overwritten wholesale (not merely appended to); the
`post-commit` hook installed, named, and executable.

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook
test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook ... ok

Ran 1 test in 6.060s
OK
```

`git status --porcelain` immediately after showed no `Global/` entries — confirmed the
guest write never touches the real checkout.

## Combined focused run (13 tests spanning all seven findings)

```
$ python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest -v \
  tests.test_harness.HarnessTests.test_check_and_native_codex_agents \
  tests.test_harness.HarnessTests.test_no_build_sh_call_writes_to_root_without_output_or_a_readonly_flag \
  tests.test_harness.HarnessTests.test_build_check_detects_global_drift_and_names_the_file \
  tests.test_harness.HarnessTests.test_build_sh_generate_mode_regenerates_global_and_installs_the_drift_hook \
  tests.test_harness.HarnessTests.test_unittest_descendant_cannot_open_an_external_absolute_path_for_writing \
  tests.test_harness.HarnessTests.test_unittest_descendant_preserves_fixture_path_inside_private_sandbox \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_sqlite3_connect_outside_the_sandbox_before_mutation \
  tests.test_harness.HarnessTests.test_unittest_write_guard_degrades_portably_without_bwrap \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_home_and_cli_destinations_before_mutation \
  tests.test_harness.HarnessTests.test_unittest_write_guard_allows_private_temporary_directory \
  tests.test_harness.HarnessTests.test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd \
  tests.test_harness.HarnessTests.test_unittest_child_home_implicitly_moves_state_to_that_fixture_home \
  tests.test_routing.RoutingTests.test_ac04a_verified_review_shape_dispatches_via_ac02_cross_lane_with_diff_payload_reaching_stdin

Ran 13 tests in 31.140s
OK
```

`git diff --check -- tests/__init__.py tests/test_harness.py tests/test_routing.py` — exit 0
(no whitespace errors).

## Final AC-04 measurement (the mandatory long run)

`discover -s tests`, entire suite, no bwrap (`SET_AGENTS_TEST_NO_BWRAP=1`), sha256 manifest
of `Global/` (568 files) before and after, plus `git status --porcelain` before/after — the
corrected method per P2-F09 (the previous 19→0 measurement in P2-portabilidad.md only ever
ran `tests.test_harness` alone, which is exactly how P2-F04's 19th call site, living in
`tests/test_routing.py`, escaped detection).

```
$ find Global -type f | wc -l
568

$ SET_AGENTS_TEST_NO_BWRAP=1 python3 ai/scripts/heartbeat-run.py --interval 20 -- python3 -m unittest discover -s tests
descendant-boundary: off (bwrap not found)
...
Ran 1145 tests in 589.781s

OK (skipped=7)
```

```
$ diff global-manifest-before.sha256 global-manifest-after.sha256
(no output — exit 0, byte-identical across all 568 files)
```

`git status --porcelain` before and after the run: identical for every path this package
touches or could touch (`tests/__init__.py`, `tests/test_harness.py`, `tests/test_routing.py`,
this evidence file, and no `Global/*` entries in either). The two diffs' only lines are:

```
14a15
>  M docs/notas/features/025-consola-minima-y-flexible.md
30a32,33
> ??  "docs/notas/decisiones/2026-08-15 RDD-ya-existe-en-el-repo-con-otra-acepcion.md"
> ?? "docs/notas/decisiones/2026-08-15 actualizar-le-repone-los-cuatro-CLIs-al-que-instalo-uno.md"
34a38,39
> ?? docs/specs/025-consola-minima-y-flexible/context/D5-vault-en-todo-spawn.md
> ?? docs/specs/028-narracion-que-ensena/
```

All four new/changed paths belong to features **025** and **028** — neither is this
package (027/P2), neither is anything in my owned paths, and none is under `Global/` or
`tests/`. This checkout is not a worktree (per the task's own framing) and this delta
appeared entirely on its own during the ~10-minute run, most likely a concurrent
process/agent working the same shared checkout on unrelated features. It is reported
here exactly as observed, unresolved as "who", because it is outside this package's scope
and does not touch anything this repair could have caused or is responsible for
verifying. `19 → 0` (P2-portabilidad.md's own headline number) is reconfirmed at `0 → 0`
with the corrected, full-suite, manifest-based method: **byte-identical**, zero `Global/`
drift, before and after 1145 tests including the previously-invisible 19th call site.

## Sin verificar

- P2-F05's `_output_value_is_unsafe` gives an unresolved free name (a function parameter)
  the benefit of the doubt rather than flagging it — verified NOT to cause a false negative
  on the three reviewer bypasses (all three were caught), but a hypothetical fourth bypass
  routed through an intermediate function parameter (e.g. `def helper(x): run("./build.sh",
  "--output", x)` called elsewhere with `x=str(ROOT / "Global")`) would not be caught by
  this lint — cross-function-boundary taint tracking was judged out of scope for a single
  bounded repair pass; declared here rather than silently left as a claimed guarantee.
- P2-F08 is a declared, measured, NOT-fixed limitation (CPython exposes no dir_fd-aware
  `"open"` audit event) — this is intentional per the finding's own instruction, not an
  oversight.
- The concurrent `docs/notas`/`docs/specs` changes for features 025/028 noted in the final
  measurement were observed, not investigated — their origin (another agent/process in the
  same shared checkout) is inferred from the path names, not confirmed by any process
  inspection on my part.
- macOS/Windows were not exercised for P2-F06/F07 (same limitation already declared in
  P2-portabilidad.md) — only Linux+bwrap and Linux without bwrap (`SET_AGENTS_TEST_NO_BWRAP=1`)
  were verified in this pass.

---

## Corrección de la afirmación de cierre de AC-04 (orquestador, tras el segundo delta review)

El segundo delta review independiente exigió esta corrección **antes** de aceptar el paquete, y tiene
razón. El titular de este documento —"0 → 0, byte-idéntico, cero drift"— es cierto para lo que midió
y **afirma más de lo que midió**.

El reviewer corrió los mismos 1145 tests en una copia aislada con un manifiesto de **árbol completo**
(1449 archivos, incluidos los gitignoreados, más los 263 de `.git`, y comparando **mtimes**), que es
estrictamente más fuerte que el manifiesto de los 568 archivos de `Global/` que usamos acá. Con eso
destapó un residuo real:

```
=== test aislado, SIN bwrap ===
Ran 1 test in 0.072s — OK
pyc escritos en el repo real: 7
  ai/scripts/__pycache__/routing.cpython-314.pyc
  ai/scripts/routing_core/__pycache__/{service,__init__,store,gates,catalog,domain}.cpython-314.pyc

=== mismo test, CON bwrap ===
Ran 1 test in 0.591s — OK
pyc escritos en el repo real: 0
```

**Causa**: `run_gate` (`ai/scripts/routing_core/gates.py:20-22`) filtra el entorno del hijo a las
claves declaradas por su `GateSpec` —`("PYTHONUTF8",)`—, así que el hijo **pierde**
`PYTHONDONTWRITEBYTECODE` y `py_compile` escribe bytecode igual. Disparado por
`tests/test_routing.py:1441`.

**Por qué nuestra medición no lo vio, y es la lección**: `__pycache__/` está en `.gitignore`, no vive
bajo `Global/`, y el `.pyc` es determinista —contenido idéntico, así que ni un sha256 lo delata; lo
cazó el **mtime**—. La misma ceguera cubre `ai/state/`, `active-profile`, `tools.local.toml`,
`.build/`, `.staging/`, `.backups/` y todo `.git/`.

**La afirmación correcta**, que reemplaza al titular:

> Cero drift trackeado y cero drift de `Global/`. Un residuo medido —bytecode en `__pycache__/`, vía
> `run_gate`/`py_compile`— en el camino **sin** bwrap, invisible a `git status` por `.gitignore`.

**Por qué no bloquea la aceptación**: el residuo es bytecode regenerable en un directorio ignorado, no
estado ni credenciales; los destinos que AC-04 nombra por escrito (`STATE_DIR`, `.claude`, `.codex`,
`.pi`, `.config/opencode`) están cubiertos en los dos modos; y no es reparable in-process, porque la
guarda es por intérprete y `gates.py` es código de producción, fuera de los `owned_paths` de P2. Es
hermano de P2-F08: limitación medida y declarada, no bug reparable en este paquete.

Queda registrado como P2-F11 en `ai/state/decisions-log.jsonl`.
