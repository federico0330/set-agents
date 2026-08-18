"""Test package for unittest discovery."""

import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

try:  # POSIX only; Windows resolves no descriptor to a path at all.
    import fcntl
except ImportError:  # pragma: no cover - exercised only on Windows CI
    fcntl = None

# AC-02 (027/P1). Dozens of test modules do `import provider_registry` (and siblings)
# by bare name from inside ai/scripts/*.py -- that only resolves once ai/scripts/ is on
# sys.path. Every individual test_*.py used to do its own `sys.path.insert(0, ...)` at
# import time, so `python3 -m unittest discover` only ever worked because SOME module
# (alphabetically first to be imported) happened to run that side effect before the
# ones that needed it -- e.g. tests.test_harness itself never inserts the path, and
# relied entirely on that accident. Running it alone (`python3 -m unittest
# tests.test_harness`) skipped the accident and produced ~118 ModuleNotFoundError.
# tests/__init__.py is the one choke point Python guarantees runs before ANY submodule
# of this package is imported, regardless of which one unittest loads first or whether
# the rest of the suite ever runs -- so the path is set here, once, instead of auditing
# every module that happens to need it today or will need it tomorrow.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ai/scripts"))

# 027/P2 (AC-04/05): every unittest run owns one private filesystem root.  Configure
# all inherited home/temp seams before a test module can import production code, then
# reject every mutating filesystem audit event whose *resolved destination* escapes
# that root.  The guard is test infrastructure only: production modules remain
# unmodified and subprocesses inherit the relocated HOME/TMPDIR/STATE_DIR seams.
_ORIGINAL_HOME = Path.home().resolve(strict=False)
_TEST_SANDBOX_HANDLE = tempfile.TemporaryDirectory(prefix="set-agentes-unittest-")
_TEST_SANDBOX = Path(_TEST_SANDBOX_HANDLE.name).resolve(strict=False)
_TEST_HOME = _TEST_SANDBOX / "home"
_TEST_STATE_DIR = _TEST_SANDBOX / "state"
_TEST_APP_CONFIG = _TEST_STATE_DIR / "config.toml"
_TEST_TMPDIR = _TEST_SANDBOX / "tmp"
_TEST_CHILD_TMPDIR = _TEST_SANDBOX / "child-tmp"
_NON_MUTATING_DEVICE = Path(os.devnull).resolve(strict=False)
_REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
_TEST_CHECKOUT = _TEST_SANDBOX / "checkout"
_DESCENDANT_BOUNDARY_ACTIVE = os.environ.get("SET_AGENTS_TEST_SANDBOXED") == "1"
# 027/P2 portability repair: detect the Bubblewrap boundary's availability exactly
# once, by lookup rather than the hardcoded "/usr/bin/bwrap" (NixOS and Homebrew do
# not install it there). Absent bwrap (macOS, Windows, or a bwrap-less Linux), the
# descendant-confinement layer below degrades to a no-op and only the in-process
# audit hook -- which is what AC-04/AC-05 actually require -- stays enforced. A
# degraded run says so exactly once instead of silently dropping a guard.
_BWRAP = None if os.environ.get("SET_AGENTS_TEST_NO_BWRAP") == "1" else shutil.which("bwrap")
_TEST_CHECKOUT_READY = False
if _BWRAP is None and not _DESCENDANT_BOUNDARY_ACTIVE:
    print("descendant-boundary: off (bwrap not found)", file=sys.stderr)
for _directory in (_TEST_HOME, _TEST_STATE_DIR, _TEST_TMPDIR, _TEST_CHILD_TMPDIR):
    _directory.mkdir(mode=0o700)
os.environ.update({
    "HOME": str(_TEST_HOME),
    "TMPDIR": str(_TEST_TMPDIR),
    "TEMP": str(_TEST_TMPDIR),
    "TMP": str(_TEST_TMPDIR),
    "SET_AGENTS_STATE": str(_TEST_STATE_DIR),
    "PYTHONDONTWRITEBYTECODE": "1",
})
tempfile.tempdir = str(_TEST_TMPDIR)
sys.dont_write_bytecode = True
_WRITE_GUARD_ENABLED = True

# P2-F01 (027): audit hooks are per-interpreter, so a child process can otherwise call
# os.open directly and bypass this module. Give every descendant a private view instead:
# the host is read-only, only this run's sandbox is writable, and the canonical repository
# location names a copy inside that sandbox. This preserves child commands/cwds while making
# a write that appears to target ROOT harmlessly private, never a host-repository mutation.
_ORIGINAL_POPEN = subprocess.Popen


def _ensure_test_checkout():
    """Populate the private checkout the first time a bwrap-confined descendant
    actually needs it (never at import). A ~1809s-vs-~1050s suite regression traced
    to this copytree running unconditionally for every process that imports this
    package, whether or not it ever spawns a bwrap-confined child -- see
    docs/specs/027-controles-que-miran/evidence/P2-gates-retry.md. Hosts without
    bwrap, or a process only ever running already-boundary-active descendants, now
    never pay this ~31MB copy at all."""
    global _TEST_CHECKOUT_READY
    if _TEST_CHECKOUT_READY:
        return
    shutil.copytree(
        _REPOSITORY_ROOT,
        _TEST_CHECKOUT,
        symlinks=True,
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env", ".env.*", "secrets"),
    )
    _TEST_CHECKOUT_READY = True


class _SandboxPopen(_ORIGINAL_POPEN):
    """Translate Bubblewrap's conventional 128+signal exit status back to Popen's API."""
    def _handle_exitstatus(self, sts, *args, **kwargs):
        super()._handle_exitstatus(sts, *args, **kwargs)
        if self.returncode is not None and 128 <= self.returncode <= 255:
            self.returncode = -(self.returncode - 128)


def _child_environment(env):
    """Keep a fixture's HOME and implicit state directory coherent in descendants."""
    child_env = dict(os.environ if env is None else env)
    home = child_env.get("HOME")
    inherited_state = child_env.get("SET_AGENTS_STATE")
    if home and inherited_state == str(_TEST_STATE_DIR):
        resolved_home = Path(home).resolve(strict=False)
        if resolved_home != _TEST_HOME:
            child_env["SET_AGENTS_STATE"] = str(resolved_home / ".local/state/set-agentes")
    return child_env


def _sandboxed_popen(args, *popen_args, **popen_kwargs):
    """Run descendants behind the private checkout boundary, preserving Popen semantics."""
    if popen_kwargs.get("executable") or (
        _BWRAP and args and isinstance(args, (tuple, list)) and args[0] == _BWRAP
    ):
        return _ORIGINAL_POPEN(args, *popen_args, **popen_kwargs)
    if _DESCENDANT_BOUNDARY_ACTIVE:
        # Guest tests run inside their caller's already-private Bubblewrap boundary. They
        # still install this module's audit hook, but a second namespace cannot remount its
        # guest checkout reliably and adds no confinement.
        popen_kwargs["env"] = _child_environment(popen_kwargs.get("env"))
        return _ORIGINAL_POPEN(args, *popen_args, **popen_kwargs)
    if _BWRAP is None:
        # Portable degradation (Federico, 2026-08-14): no Bubblewrap on this host
        # (macOS, Windows, or a bwrap-less Linux). The OS-level descendant boundary
        # (P2-F01) is unavailable here, but AC-04/AC-05 do not require it -- the
        # in-process audit hook below still rejects this interpreter's own escaping
        # writes. Relocated HOME/TMPDIR/SET_AGENTS_STATE (P2-F03) still apply.
        popen_kwargs["env"] = _child_environment(popen_kwargs.get("env"))
        return _ORIGINAL_POPEN(args, *popen_args, **popen_kwargs)
    _ensure_test_checkout()
    requested_cwd = popen_kwargs.pop("cwd", None)
    child_cwd = Path(requested_cwd or os.getcwd()).resolve(strict=False)
    popen_kwargs["env"] = _child_environment(popen_kwargs.get("env"))
    popen_kwargs["env"]["SET_AGENTS_TEST_SANDBOXED"] = "1"
    child_path = popen_kwargs["env"].get("PATH", os.defpath)
    if popen_kwargs.pop("shell", False):
        command = ("/bin/sh", "-c", args)
    elif isinstance(args, str):
        command = (args,)
    else:
        command = tuple(os.fspath(part) for part in args)
    try:
        _REPOSITORY_ROOT.relative_to(_TEST_SANDBOX)
        checkout_mount = ()  # Guest checkout: it is already a writable private subtree.
    except ValueError:
        checkout_mount = ("--bind", str(_TEST_CHECKOUT), str(_REPOSITORY_ROOT))
    boundary = (
        _BWRAP, "--die-with-parent",
        "--ro-bind", "/", "/",
        "--dev", "/dev",
        "--bind", str(_TEST_SANDBOX), str(_TEST_SANDBOX),
        "--bind", str(_TEST_CHILD_TMPDIR), "/tmp",
        *checkout_mount,
        "--setenv", "PATH", child_path,
        "--chdir", str(child_cwd), "--",
        *command,
    )
    return _SandboxPopen(boundary, *popen_args, **popen_kwargs)


class _BoundaryPopen(_ORIGINAL_POPEN):
    """`subprocess.Popen`'s replacement, as a CLASS and not a bare function.

    P2-F10 (Windows CI, 2026-08-18): this used to be `subprocess.Popen =
    _sandboxed_popen`, a plain function. Anything that later did `class
    X(subprocess.Popen)` then blew up at import time, because a function cannot be a
    base class. On Windows the CPython standard library does exactly that:
    `unittest.mock` imports `asyncio`, which imports `asyncio.windows_utils`, whose
    line 125 is `class Popen(subprocess.Popen)`. So `from unittest import mock` --
    line 26 of tests/test_harness.py -- died with `TypeError: function() argument
    'code' must be code, not str`, and the ENTIRE module failed to load. Linux and
    macOS never import `asyncio.windows_utils`, so the landmine sat there unseen.

    `__new__` dispatches only when instantiated as this exact class; a genuine
    subclass builds itself normally. `_sandboxed_popen` returns an instance of a
    DIFFERENT class (`_ORIGINAL_POPEN` or `_SandboxPopen`, both parents rather than
    children of this one), so Python correctly skips calling `__init__` on it again.
    """

    def __new__(cls, args=(), *popen_args, **popen_kwargs):
        if cls is not _BoundaryPopen:
            return super().__new__(cls)
        return _sandboxed_popen(args, *popen_args, **popen_kwargs)


subprocess.Popen = _BoundaryPopen


def _descriptor_path(fd):
    """The filesystem path an open descriptor points at, portably.

    P2-F09 (macOS CI, 2026-08-18): both fd-resolving call sites below read
    ``/proc/self/fd/<n>``, which exists ONLY on Linux.  On macOS every read raised
    ``FileNotFoundError``, both sites swallowed it as "unresolvable", and the guard
    returned ``None`` -- so the whole write sandbox FAILED OPEN for every fd-based and
    ``dir_fd``-based write on that platform.  The one test that would have caught it
    (``test_unittest_write_guard_rejects_symlink_parent_for_remove_rename_and_dir_fd``)
    was itself the macOS failure: the real ``os.remove`` ran unguarded and reported
    ``FileNotFoundError`` instead of the ``PermissionError`` the guard owes.

    Darwin/BSD answer the same question through ``fcntl(fd, F_GETPATH, buf)``.  CPython
    only exposes ``fcntl.F_GETPATH`` from 3.13, so the Darwin constant (50) is the
    fallback.  Raises ``OSError`` when the descriptor has no path at all -- a pipe or a
    socket -- which both callers already treat as "not a filesystem destination".
    """
    try:
        return os.readlink(f"/proc/self/fd/{fd}")
    except OSError:
        if fcntl is None:
            raise
        buf = fcntl.fcntl(fd, getattr(fcntl, "F_GETPATH", 50), b"\0" * 1024)
        return buf.split(b"\0", 1)[0].decode()


def _resolved_write_target(value, *, dir_fd=None, follow_final_symlink=True):
    """Return a stable absolute destination without requiring it to exist."""
    if isinstance(value, int):
        try:
            target = Path(_descriptor_path(value))
            # Pipes/sockets are file descriptors, not filesystem destinations.  Treating
            # their kernel labels (for example ``pipe:[123]``) as relative paths would
            # falsely resolve them below the repository and block subprocess stdout.
            # Darwin's F_GETPATH answers `/dev/fd/<n>` for a descriptor with no name of
            # its own -- absolute, but self-referential, so it is the same non-answer
            # `pipe:[123]` is on Linux and must not be mistaken for a real destination.
            if target.parent == Path("/dev/fd"):
                return None
            return target.resolve(strict=False) if target.is_absolute() else None
        except OSError:
            return None
    try:
        target = Path(os.fspath(value))
    except (TypeError, ValueError):
        return None
    # Resolved HERE and never inside the block below: PermissionError is itself an
    # OSError, so a denial raised in there would be swallowed by that same handler and
    # silently downgraded to "unresolvable" -- fail open, the very bug P2-F09 fixes.
    # An absolute path ignores dir_fd (POSIX), so it is never resolved for one.
    if not target.is_absolute() and isinstance(dir_fd, int) and dir_fd >= 0:
        try:
            target = Path(_descriptor_path(dir_fd)) / target
        except OSError as exc:
            # Fail CLOSED: a write relative to a directory this process cannot name
            # cannot be proven to land inside the sandbox, so it is denied rather than
            # waved through.
            raise PermissionError(
                f"test write outside private sandbox denied: dir_fd {dir_fd} is not "
                f"resolvable on this platform, so {value!r} cannot be proven inside it"
            ) from exc
    try:
        if follow_final_symlink:
            return target.resolve(strict=False)
        # unlink/rename mutate a directory entry rather than the target of a final
        # symlink. Resolve every PARENT component (a symlinked parent can escape the
        # sandbox) but preserve the final entry lexically so deleting a sandbox symlink
        # never mistakes its external referent for the deletion destination.
        return target.parent.resolve(strict=False) / target.name
    except (OSError, TypeError, ValueError):
        return None


def _deny_if_outside_sandbox(target):
    if target is None:
        return
    if target == _NON_MUTATING_DEVICE:
        return
    try:
        target.relative_to(_TEST_SANDBOX)
    except ValueError:
        raise PermissionError(f"test write outside private sandbox denied: {target}")


def _reject_write_outside_sandbox(value, *, dir_fd=None, follow_final_symlink=True):
    target = _resolved_write_target(value, dir_fd=dir_fd, follow_final_symlink=follow_final_symlink)
    _deny_if_outside_sandbox(target)


def _resolved_sqlite_target(database):
    """P2-F07: `sqlite3.connect` never calls `open()`/`os.*` -- it talks to the
    filesystem through SQLite's own C library, so none of the events above ever fire
    for it, and it was a live, silent escape hatch for exactly the state this package
    exists to protect (`ai/scripts/routing_core/store.py`, `ai/scripts/
    provider_registry.py`, and `ai/scripts/cost-report.py` all open a `routing.db`
    below `STATE_DIR` via sqlite3). ``sqlite3.connect`` raises its own dedicated audit
    event, `"sqlite3.connect"`, with the exact `database` argument as given -- before
    the file is created/opened, so a reject here is still before-mutation.
    `:memory:`/`""` (private, never touch disk) are not destinations to classify. The
    SQLite URI form (``sqlite3.connect("file:...", uri=True)``) is also handled,
    including its own explicit ``mode=ro`` (a real read-only open never creates or
    mutates a file, so it is not a destination this guard needs to reject)."""
    if not isinstance(database, (str, bytes, os.PathLike)):
        return None
    text = database if isinstance(database, str) else os.fsdecode(database)
    if text in ("", ":memory:"):
        return None
    if text.startswith("file:"):
        parsed = urllib.parse.urlsplit(text)
        if urllib.parse.parse_qs(parsed.query).get("mode") == ["ro"]:
            return None
        text = urllib.parse.unquote(parsed.path or parsed.netloc)
        if not text:
            return None
    try:
        return Path(text).resolve(strict=False)
    except (OSError, ValueError):
        return None


def _test_write_audit(event, args):
    if not _WRITE_GUARD_ENABLED:
        return
    if event == "sqlite3.connect":
        _deny_if_outside_sandbox(_resolved_sqlite_target(args[0] if args else None))
    elif event == "open":
        # P2-F08 (027 repair pass 2, declared/measured limitation, NOT fixed): unlike
        # "os.remove"/"os.rename"/"os.mkdir"/etc. below, CPython's "open" audit event
        # carries only `(path, mode, flags)` -- it never transmits a `dir_fd`, even
        # when the caller passed one (verified: `sys.addaudithook` prints the exact
        # same `(path, None, flags)` tuple with or without `dir_fd=` on the real
        # `os.open` call). So `_reject_write_outside_sandbox` below resolves a relative
        # `path` against this process's cwd, which can be inside the sandbox, while the
        # real `openat()` syscall the kernel actually performs honors `dir_fd` and can
        # land anywhere that file descriptor points. Measured, concretely: with cwd set
        # to the private sandbox and `dir_fd` opened on an external directory,
        # `os.open("relative.txt", os.O_WRONLY | os.O_CREAT, dir_fd=<external fd>)`
        # passed this guard and created a real file outside the sandbox -- this gap is
        # not closeable from the "open" event itself; CPython exposes no dir_fd-aware
        # variant of it. `remove`/`rename`/`mkdir`/`chmod`/`chown`/`utime`/`link`/
        # `symlink` below ARE dir_fd-aware (P2-F02) because THEIR audit events do carry
        # the fd.
        path, _mode, flags = args
        write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        if flags & write_flags:
            _reject_write_outside_sandbox(path)
    elif event in {"os.remove", "os.rmdir"}:
        _reject_write_outside_sandbox(args[0], dir_fd=args[1] if len(args) > 1 else None,
                                      follow_final_symlink=False)
    elif event == "os.truncate":
        _reject_write_outside_sandbox(args[0])
    elif event in {"os.mkdir", "os.chmod"}:
        _reject_write_outside_sandbox(args[0], dir_fd=args[2] if len(args) > 2 else None)
    elif event in {"os.chown", "os.utime"}:
        _reject_write_outside_sandbox(args[0], dir_fd=args[3] if len(args) > 3 else None)
    elif event == "os.rename":
        _reject_write_outside_sandbox(args[0], dir_fd=args[2], follow_final_symlink=False)
        _reject_write_outside_sandbox(args[1], dir_fd=args[3], follow_final_symlink=False)
    elif event == "os.link":
        _reject_write_outside_sandbox(args[1], dir_fd=args[3], follow_final_symlink=False)
    elif event == "os.symlink":
        _reject_write_outside_sandbox(args[1], dir_fd=args[2], follow_final_symlink=False)


sys.addaudithook(_test_write_audit)


# ---------------------------------------------------------------------------
# The POSIX shell toolchain this harness is built on.
#
# `set-agents`, `build.sh`, `install.sh`, `verify.sh`, `mcp.sh` and friends are bash
# scripts that `exec python3`. That is not incidental: README.md:107 declares the
# Windows path as `install.ps1` -> managed WSL, i.e. the harness RUNS on Linux even
# when the machine is a Windows machine. Native Windows is a BOOTSTRAP target (parse
# install.ps1, dry-run it, compile the Python sources), never a runtime one.
#
# The CI job is even named `windows-bootstrap`. Its "Full unittest suite" step was
# added on 2026-08-01 and has failed on every single run since -- it has never once
# been green. It was asserting a claim the product does not make.
#
# So the tests that shell out to that toolchain SKIP on a machine that lacks it, with
# the reason named, rather than failing as if a defect had been found. This changes
# nothing on Linux or macOS: `_POSIX_TOOLCHAIN` is True there by construction, and
# `test_the_posix_toolchain_is_present_on_posix` fails loudly if it ever is not, so a
# broken PATH can never silently skip the suite on the platforms that do support it.
_TOOLCHAIN_REASON = (
    "requires the POSIX shell toolchain (a shebang-ed .sh that a process can exec "
    "directly); on Windows the harness runs inside WSL per README.md:107, and this "
    "job only proves the bootstrap"
)


def _detect_posix_toolchain():
    """Can a process exec a shebang-ed `.sh` file directly?

    That, and not "is there a bash binary", is what this repo's Python actually needs.
    Measured on the Windows runner, CI run 32144718950, `Diagnose the POSIX toolchain`:
    bash 5.3 and python3 3.12 are both present, `bash` computes `/d/a/set-agents` and
    native Python stats it fine -- the composition every earlier hypothesis blamed WORKS.
    What fails is one layer down:

        set_agents_app.py:1266  subprocess.run([str(script), "--quiet"], ...)
        OSError: [WinError 193] %1 is not a valid Win32 application

    `CreateProcess` has no shebang handling, so a `.sh` path handed to it as argv[0] is
    not an executable image at all. `ai/scripts/check-drift.sh` is only the first of many
    such call sites, and a probe that measured anything else (as the previous two did)
    answers True here and the tests go right back to failing.

    The probe runs ONLY off-POSIX; on Linux and macOS the answer is True with no
    subprocess at all, so nothing about the normal path changes or slows down."""
    if os.name == "posix":
        return True
    if not shutil.which("bash") or not shutil.which("python3"):
        return False
    probe = None
    try:
        directory = tempfile.mkdtemp(prefix="set-agentes-toolchain-")
        probe = os.path.join(directory, "probe.sh")
        with open(probe, "w", encoding="utf-8", newline="\n") as handle:
            handle.write("#!/usr/bin/env bash\nexit 0\n")
        os.chmod(probe, 0o755)
        return subprocess.run([probe], capture_output=True, timeout=60).returncode == 0
    except (OSError, subprocess.SubprocessError):
        return False
    finally:
        if probe is not None:
            shutil.rmtree(os.path.dirname(probe), ignore_errors=True)


_POSIX_TOOLCHAIN = _detect_posix_toolchain()


def require_posix_toolchain():
    """Skip the calling test when the POSIX shell toolchain is absent."""
    if not _POSIX_TOOLCHAIN:
        import unittest
        raise unittest.SkipTest(_TOOLCHAIN_REASON)
