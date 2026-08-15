"""Test package for unittest discovery."""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

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
shutil.copytree(
    _REPOSITORY_ROOT,
    _TEST_CHECKOUT,
    symlinks=True,
    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".env", ".env.*", "secrets"),
)
_ORIGINAL_POPEN = subprocess.Popen


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
    if popen_kwargs.get("executable") or args and isinstance(args, (tuple, list)) and args[0] == "/usr/bin/bwrap":
        return _ORIGINAL_POPEN(args, *popen_args, **popen_kwargs)
    if _DESCENDANT_BOUNDARY_ACTIVE:
        # Guest tests run inside their caller's already-private Bubblewrap boundary. They
        # still install this module's audit hook, but a second namespace cannot remount its
        # guest checkout reliably and adds no confinement.
        popen_kwargs["env"] = _child_environment(popen_kwargs.get("env"))
        return _ORIGINAL_POPEN(args, *popen_args, **popen_kwargs)
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
        "/usr/bin/bwrap", "--die-with-parent",
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


subprocess.Popen = _sandboxed_popen


def _resolved_write_target(value, *, dir_fd=None, follow_final_symlink=True):
    """Return a stable absolute destination without requiring it to exist."""
    if isinstance(value, int):
        try:
            target = Path(os.readlink(f"/proc/self/fd/{value}"))
            # Pipes/sockets are file descriptors, not filesystem destinations.  Treating
            # their kernel labels (for example ``pipe:[123]``) as relative paths would
            # falsely resolve them below the repository and block subprocess stdout.
            return target.resolve(strict=False) if target.is_absolute() else None
        except OSError:
            return None
    try:
        target = Path(os.fspath(value))
        if not target.is_absolute() and isinstance(dir_fd, int) and dir_fd >= 0:
            target = Path(os.readlink(f"/proc/self/fd/{dir_fd}")) / target
        if follow_final_symlink:
            return target.resolve(strict=False)
        # unlink/rename mutate a directory entry rather than the target of a final
        # symlink. Resolve every PARENT component (a symlinked parent can escape the
        # sandbox) but preserve the final entry lexically so deleting a sandbox symlink
        # never mistakes its external referent for the deletion destination.
        return target.parent.resolve(strict=False) / target.name
    except (OSError, TypeError, ValueError):
        return None


def _reject_write_outside_sandbox(value, *, dir_fd=None, follow_final_symlink=True):
    target = _resolved_write_target(value, dir_fd=dir_fd, follow_final_symlink=follow_final_symlink)
    if target is None:
        return
    if target == _NON_MUTATING_DEVICE:
        return
    try:
        target.relative_to(_TEST_SANDBOX)
    except ValueError:
        raise PermissionError(f"test write outside private sandbox denied: {target}")


def _test_write_audit(event, args):
    if not _WRITE_GUARD_ENABLED:
        return
    if event == "open":
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
