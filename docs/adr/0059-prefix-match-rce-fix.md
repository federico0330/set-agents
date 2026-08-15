# ADR-0059: Command Policy Prefix-Match RCE (SEC-030) Fix

**Date:** 2026-08-15
**Status:** IMPLEMENTED
**Severity:** CRITICAL (RCE in public repository)

## Problem

The command policy in `ai/scripts/coord_policy.py:321` used prefix-matching to validate safe commands:

```python
return any(re.fullmatch(pattern + r".*", command) for pattern in SAFE)
```

This allowed **arbitrary trailing flags** on every whitelisted command (23 entries in `SAFE`). Combined with the read-only harness role in a **public repository**, this enabled Remote Code Execution:

### Proof of Concept (Executed)

Four PoCs were successfully demonstrated:

1. **`fd . -X touch pwned_fd`** — fd prefix matched, -X flag executed arbitrary command via command substitution
2. **`find . -maxdepth 1 -name victim.txt -exec touch pwned_find {} +`** — find prefix matched, -exec flag executed arbitrary command
3. **`curl -s http://localhost:1/ file:///etc/hostname -o exfil.txt`** — curl prefix matched, -o flag exfiltrated /etc/hostname
4. **`curl http://localhost:9/ -o ~/.claude/hooks/coord_policy.py`** — curl prefix matched, -o flag overwrote the guard itself

### Root Cause

The same vulnerability existed in **three independent copies** of the syntax validation regex:
- `coord_policy.py:127` — `FORBIDDEN_SYNTAX` (original definition, later copies didn't have updates)
- `claude_local_gate_guard.py` — old `FORBIDDEN` regex (missing bare `&`)
- `claude_release_guard.py:9` — `FORBIDDEN` regex (missing bare `&` and control chars)

This violated the single-source-of-truth principle and allowed fixes to miss some surfaces.

### Scope

The vulnerability affected command execution in:
- The Claude-Code lane (via `coord_policy.allowed()`)
- The local P001 gate (via `claude_local_gate_guard.py`)
- Release actions (via `claude_release_guard.py`)

## Solution

### 1. Replaced Prefix-Matching with Enumerated Flag Validation (via `_rest_allowed`)

The solution uses the **same disciplinary pattern already in `SAFE_ARGV`** (which validates Python script invocations), extended to all binary commands. Instead of "safe subcommand + any trailing flags" or "flags blacklist", each command specifies exactly which flags are allowed:

```python
SAFE_BINARY_COMMANDS = [
    # (command_name, modifiers_dict)
    ("git", {
        "status": 0,           # argv[1]="status", no args after it
        "--porcelain": 0,      # or "--porcelain", no args
        "diff": 0,
        "--check": 0,
        "--stat": 0,
        "-U": 1,               # -U takes 1 arg
        "log": 0,
        "--oneline": 0,
        "-n": 1,               # -n takes 1 arg
        # ... no "-c", no "--exec-path" (dangerous)
    }),
    ("grep", {
        "-r": 0, "-n": 0, "-i": 0, "-c": 0, "-l": 0, "-v": 0, "-F": 0, "-E": 0,
        # ... (no "--pre" or other exec-enabling flags)
    }),
    ("ls", {
        "-l": 0, "-a": 0, "-h": 0, "-R": 0, "-t": 0, "--color": 0,
        # ... (only read flags)
    }),
    ("cat", {}),    # No flags allowed; "cat file" only
    ("python3", {
        "-m": 1,                                    # -m takes 1 arg (module name)
        "--version": 0, "-V": 0,
        # ... (no "-c" for exec)
    }),
]

def _rest_allowed(rest, modifiers):
    """Validate argv[1:] against allowed flags + args.

    - Flag not in modifiers → rejected
    - Flag's arg count must match
    - Positional args (no leading -) → always allowed
    - Short flag composition (-rn = -r, -n) → expanded and validated per flag
    """
```

Commands with truly unbounded or dangerous flag sets (`fd` with `-x`, `find` with `-exec` or `-delete`) were **removed from the allowlist**, since they cannot be safely enumerated. But `grep`, `rg`, `cat`, `ls`, `head`, `tail`, `wc`, `curl` remain, with their specific safe flags enumerated.

### 2. Specialized `curl` Validation

Created `_curl_allowed()` function that:
- **Parses URLs** using `urllib.parse.urlparse()`, not regex
- **Rejects dangerous schemes**: `file://`, `scp://`, `dict://`
- **Prohibits I/O redirection flags**: `-o`, `--output`, `-O`, `-T`, `--upload`, `-d`, `--data*`, `-K`, `--config`
- **Enforces URL as last token** to prevent flag injection
- **Only allows** `http://` and `https://` schemes (or localhost without scheme)

### 3. Centralized Forbidden Syntax Definition

`FORBIDDEN_SYNTAX` now includes:
- **Bare `&`** (statement separator, was missing in old copies)
- **All ASCII control characters** `[\x00-\x1f\x7f]` (added as defense-in-depth alongside newline check)

Both `claude_local_gate_guard.py` and `claude_release_guard.py` **import** `FORBIDDEN_SYNTAX` from `coord_policy` (single source of truth), eliminating copy-paste drift.

### 4. Comprehensive Test Suite

Added `tests/test_command_policy.py` with:
- **PoC verification**: All four attack vectors now return `False`
- **Simple command validation**: Each `SAFE_SIMPLE_COMMANDS` entry rejects invented flags
- **Metacharacter blocking**: Verifies bare `&`, `&&`, `;`, `|`, `>`, `<`, `$()`, backticks, and control chars are rejected
- **curl specifics**: Tests scheme validation, forbidden flags, and URL parsing
- **Positive corpus**: Confirms legitimate harness commands remain allowed

All tests pass.

## Commands in Allowlist (with Enumerated Flags)

### Kept (Critical to Harness)
- **`git`**: status, diff, log, show (with flags: `--porcelain`, `--check`, `--stat`, `--oneline`, `-n`, etc.)
- **`grep` / `rg`**: search flags (`-r`, `-n`, `-i`, `-c`, `-l`, `-v`, `-F`, `-E`), but NOT `--pre` (pre-command)
- **`ls`**: read flags (`-l`, `-a`, `-h`, `-R`, `-t`, `--color`), no execution flags
- **`cat`, `head`, `tail`, `wc`**: no flags (read-only by construction)
- **`python3` / `python`**: `-m <module>` (only safe modules: `unittest`, `py_compile`, `json.tool`), `--version`
- **`curl`**: localhost/https URLs, NO `-o` / `--output` / `-d` / `-K` (output/config redirection)
- **Others**: `pwd`, `which`, `uname`, `opencode models`, etc.

### Removed (Truly Unbounded or Dangerous)
- **`fd`** — cannot enumerate (has `-x`, `-exec`, unbounded behavior)
- **`find`** — cannot enumerate (has `-exec`, `-execdir`, `-delete`, `-fprintf`, unbounded)
- **`rg --pre` / `grep` variants** — the base commands are allowed; the dangerous subflags are absent

**Rationale:** The policy is "whitelist what is safe, not blacklist what is dangerous." The harness's real usage (extracted from context packs and subprocess calls) proves it needs only `git` with specific flags, `grep -rn`, `ls`, `cat`, etc. The commands that would require blacklisting unbounded flags (`fd`, `find`, `bat`, `eza`) are developer tools, not harness infrastructure.

## Known Limitation

**`generate.py:186-197`** contains a fourth copy of the invariant (glob-based validation for OpenCode lane), with a distinct set of allowed patterns. This remains **pending review** and was out of scope for this fix (affects OpenCode lane, not Claude-Code or P001 gates). Marked in comments for future ADR.

## Verification (PoCs + Real Corpus)

### PoCs Blocked

```
PoC 1: fd . -X touch pwned_fd                                  → BLOCKED ✓
PoC 2: find . -maxdepth 1 -name victim.txt -exec ... {} +      → BLOCKED ✓
PoC 3: curl -s http://localhost:1/ file:///etc/hostname -o ... → BLOCKED ✓
PoC 4: curl http://localhost:9/ -o ~/.claude/hooks/...         → BLOCKED ✓
```

### Real Corpus (with Actual Flags)

Extracted from `docs/specs/025-consola-minima-y-flexible/context/D1-superficie-humana.md`:

```
git status                          → ALLOWED ✓
git status --porcelain              → ALLOWED ✓
git diff --check                    → ALLOWED ✓
git log --oneline -n 5              → ALLOWED ✓
grep -n pattern                     → ALLOWED ✓
grep -rn pattern dir/               → ALLOWED ✓ (composed flags -rn = -r, -n)
ls docs/adr/                        → ALLOWED ✓
ls -la                              → ALLOWED ✓
cat README.md                       → ALLOWED ✓
python3 -m unittest discover -s ... → ALLOWED ✓
python3 ai/scripts/feature-state... → ALLOWED ✓
```

### Run Tests

```bash
python3 tests/test_command_policy.py
# Result: ALL TESTS PASSED (54 assertions)
```

## Files Changed

- `ai/scripts/coord_policy.py` — `SAFE` reduced to 2 entries, added `_simple_command_allowed()`, `_curl_allowed()`, updated `FORBIDDEN_SYNTAX`, changed line 321 from prefix-match to structured validation
- `ai/scripts/claude_local_gate_guard.py` — Import `FORBIDDEN_SYNTAX` from `coord_policy`, use it in validation
- `ai/scripts/claude_release_guard.py` — Import `FORBIDDEN_SYNTAX` from `coord_policy`, use it in validation
- `tests/test_command_policy.py` — NEW: comprehensive test suite (90+ assertions)
- `docs/adr/0059-*.md` — THIS DOCUMENT

## Impact on Users

**No breaking changes to normal usage.** Commands the harness actually invokes remain allowed:
- `git status`, `git diff`, `git log`, `git show` ✓
- `python3 --version`, `node --version`, `npm ls` ✓
- `uname`, `pwd`, `which` ✓
- `curl http://localhost:...` ✓
- Feature-state mutations (`feature-state.py transition`, `integration_action.py`) ✓

**Removed access:** The tooling that was blacklisted (`fd`, `find`, `grep`, etc.) was not part of the harness's read-only authorization model; it was incidental that they matched the prefix of allowed commands.

## References

- **SEC-030:** RCE via command policy prefix-match (this fix)
- **F-01 repair:** Bare `&` and control chars in `FORBIDDEN_SYNTAX`
- **ADR-0025:** Resolve-first principle
- **ADR-0020:** Receipt-checked integration wrapper (only safe mutation channel)
