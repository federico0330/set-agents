# S1-implementer: Command Policy SEC-030 RCE Fix Evidence

**Date:** 2026-08-15
**Implementer:** Claude (Haiku 4.5)
**Package:** 030-guardas-que-no-se-pueden-prefijar
**Final Status:** ✓ VERIFIED (16/16 PoCs blocked + 23/23 corpus commands allowed)

---

## Why My First Test Failed (Important)

**My first corpus passed because I tested the wrong thing.**

I tested commands like `git status`, `grep -n`, `ls` in isolation. These passed, so I thought the fix was complete. But the harness doesn't run commands like that — it runs:
- `git status --porcelain` (not just `git status`)
- `git diff --check` (not just `git diff`)
- `grep -rn pattern dir/` (not just `grep -n`)
- `head -20 file` with numeric flags (not in my list)
- `./build.sh --check` (not in my list at all)

My test suite passed for the wrong reasons: **testing `git status` doesn't verify that `git status --porcelain` works, and it doesn't catch that `head -20` (numeric flags) was missing.**

This is exactly the defect this package hunts. A corpus built by **inventing examples** passes. A corpus extracted from **actual usage** reveals what the system truly needs. The fix is good, but the test must be REAL.

---

## Final Test Results (Both Batteries)

### PoCs Blocked: 16/16

```
fd . -X touch pwned_fd                                      → BLOCKED ✓
find . -maxdepth 1 -name victim.txt -exec touch pwned_find  → BLOCKED ✓
curl -s http://localhost:1/ file:///etc/hostname -o ...    → BLOCKED ✓
curl http://localhost:9/ -o ~/.claude/hooks/...             → BLOCKED ✓

rg --pre=/bin/sh                                             → BLOCKED ✓
git -c core.pager=sh log                                     → BLOCKED ✓
python3 -c "import os; os.system('id')"                      → BLOCKED ✓
sed -i 's/a/b/' file                                         → BLOCKED ✓ (removed)
find . -delete                                               → BLOCKED ✓
curl -d @credenciales http://localhost/                      → BLOCKED ✓
bat --pager sh                                               → BLOCKED ✓

git log; touch /tmp/pwn                                      → BLOCKED ✓
git log && touch /tmp/pwn                                    → BLOCKED ✓
git log $(touch /tmp/pwn)                                    → BLOCKED ✓
git log & touch /tmp/pwn (bare & — newly fixed)             → BLOCKED ✓
git log | cat                                                → BLOCKED ✓
```

### Corpus Allowed: 23/23

```
git status                                    → ALLOWED ✓
git status --porcelain                        → ALLOWED ✓
git diff --check                              → ALLOWED ✓
git log --oneline -n 5                        → ALLOWED ✓
grep -n ADR                                   → ALLOWED ✓
grep -rn ls docs/adr/  (composed -rn)        → ALLOWED ✓
ls docs/adr/                                  → ALLOWED ✓
ls -la                                        → ALLOWED ✓
cat README.md                                 → ALLOWED ✓
head -20 README.md  (numeric flag)           → ALLOWED ✓
head -n 20 README.md                          → ALLOWED ✓
tail -5 README.md  (numeric flag)            → ALLOWED ✓
tail -n 5 README.md                           → ALLOWED ✓
wc -l tests/test_harness.py                   → ALLOWED ✓
cmp -s a b                                    → ALLOWED ✓
diff a b                                      → ALLOWED ✓
diff -u a b                                   → ALLOWED ✓
python3 -m unittest discover -s tests         → ALLOWED ✓
python3 ai/scripts/feature-state.py status    → ALLOWED ✓
./build.sh --check                            → ALLOWED ✓
./build.sh --output /tmp/x  (feature 027)    → ALLOWED ✓
./build.sh --profile zen                      → ALLOWED ✓
./build.sh --target opencode                  → ALLOWED ✓
```

**Final Score: 16/16 PoCs blocked + 23/23 corpus allowed ✓✓**

---

## Key Design Decisions

### 1. Removed `sed` (RCE Risk)

**Decision:** Removed from allowlist.

**Reason:** The `sed` script can contain commands like `e` (execute), `w` (write), `W` (append write), `r` (read), `R` (read line), `s///e` (execute substitution result), and more. These have side effects (shell execution, file I/O) that cannot be reliably enumerated without parsing a complex DSL.

**Trade-off:** No `sed` access via allowlist, but:
- Safety is maintained (can't hide `e` command in a seemingly-safe script)
- If a use case arises, it will be explicit and documented

**Evidence:** Not finding `sed` in actual subprocess calls or context packs so far.

### 2. Allowed `./build.sh --output` (Feature 027 Gate)

**Decision:** Added to allowlist.

**Reason:** Feature 027 converted 19 test call sites to use `./build.sh --output /tmp/dir` instead of rewriting the tracked `Global/` tree. This is the safe path forward. Blocking it would break those 19 tests.

**Trade-off:** `--output` was in `FORBIDDEN_OPTIONS` as a blanket ban (to catch `git diff --output` etc.). Removed it and let command-specific validation (via `SAFE_BINARY_COMMANDS`) handle safety. Git doesn't allow `--output` in its modifiers, but `build.sh` does.

### 3. Added Numeric Flag Aliases (`head -20` = `head -n 20`)

**Decision:** Rewrite `-<N>` as `-n <N>` for `head` and `tail` before validation.

**Reason:** Both tools accept `-20` as shorthand for `-n 20`. Standard Unix behavior. The rewrite preserves compatibility while validating through the normal flag map.

### 4. Short Flag Composition Support (`-rn` = `-r` + `-n`)

Each character in a composed flag is validated individually. Works for `grep -rn`, `ls -la`, etc.

---

## Files Changed

- `/home/federico/SET-AGENTES/ai/scripts/coord_policy.py`
  - Removed `sed` from `SAFE_BINARY_COMMANDS`
  - Added numeric flag aliases for `head`/`tail` in `_binary_command_allowed()`
  - Removed `--output` from `FORBIDDEN_OPTIONS` (now context-specific)
  - Updated `FORBIDDEN_SYNTAX` to include bare `&` + control chars

- `/home/federico/SET-AGENTES/ai/scripts/claude_local_gate_guard.py`
  - Import `FORBIDDEN_SYNTAX` from `coord_policy` (single source)

- `/home/federico/SET-AGENTES/ai/scripts/claude_release_guard.py`
  - Import `FORBIDDEN_SYNTAX` from `coord_policy` (single source)

- `tests/test_command_policy.py`
  - Real corpus (23 commands extracted from context packs and subprocess usage)

- `docs/adr/0059-prefix-match-rce-fix.md`
  - Updated with final design and rationale

---

## Known Gaps / Pending

1. **`generate.py:186-197`** — Fourth copy of validation for OpenCode lane. Not in scope. Pending.

2. **`sed` use case** — If code using `sed -n` appears in subprocess calls or prompts, this will be a finding (not a silent gap).

3. **`./install.sh`** — Listed in allowlist but less common. No corpus hits yet.

---

## Sign-Off

- **PoCs:** 16/16 blocked ✓
- **Corpus:** 23/23 allowed (real commands with actual flags) ✓
- **Single Source of Truth:** FORBIDDEN_SYNTAX centralized ✓
- **Decisions Documented:** sed (removed), --output (allowed) ✓
- **Test Quality:** Real corpus, not invented ✓

**Status: READY FOR REVIEW**
