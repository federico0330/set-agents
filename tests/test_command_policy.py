#!/usr/bin/env python3
"""Test suite for command policy security (SEC-030: prefix-match RCE fix).

This module tests that:
1. PoCs are blocked
2. Real corpus (extracted from repo usage with actual flags) is allowed
3. Dangerous flags are blocked
4. Shell composition is blocked

Run without pytest: python3 tests/test_command_policy.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "ai" / "scripts"))

from coord_policy import allowed, FORBIDDEN_SYNTAX


def test_pocs_blocked():
    """The four documented PoCs must all be blocked."""
    print("\nTesting: Four PoCs blocked...")
    pocs = [
        ("fd . -X touch pwned_fd", "fd -X"),
        ("find . -maxdepth 1 -name victim.txt -exec touch pwned_find {} +", "find -exec"),
        ("curl -s http://localhost:1/ file:///etc/hostname -o exfil.txt", "curl exfil"),
        ("curl http://localhost:9/ -o ~/.claude/hooks/coord_policy.py", "curl rewrite"),
    ]
    for cmd, desc in pocs:
        assert allowed(cmd) is False, f"PoC '{desc}' should be blocked"
        print(f"  ✓ {desc}")


def test_corpus_positive_real():
    """Corpus extracted from actual repo usage (with real flags)."""
    print("\nTesting: Real corpus from repo usage...")
    corpus = [
        ("git status", "git status"),
        ("git status --porcelain", "git status --porcelain"),
        ("git diff --check", "git diff --check"),
        ("git log --oneline -n 5", "git log --oneline -n 5"),
        ("grep -n ADR", "grep -n"),
        ("grep -rn ls docs/adr/", "grep -rn (composed flags)"),
        ("ls docs/adr/", "ls path"),
        ("ls -la", "ls -la"),
        ("cat README.md", "cat file"),
        ("python3 -m unittest discover -s tests", "python3 -m unittest"),
        ("python3 ai/scripts/feature-state.py status", "feature-state.py"),
    ]
    for cmd, desc in corpus:
        result = allowed(cmd)
        assert result is True, f"Corpus '{desc}' should be allowed, got {result} for '{cmd}'"
        print(f"  ✓ {desc}")


def test_dangerous_flags_blocked():
    """Dangerous flags and compositions must be blocked."""
    print("\nTesting: Dangerous flags blocked...")
    dangerous = [
        ("git status -c user.name=evil", "git -c (config execution)"),
        ("git --exec-path", "git --exec-path"),
        ("python3 -c 'import os; os.system(\"touch /tmp/pwn\")'", "python3 -c (exec code)"),
        ("grep --pre 'touch /tmp/pwn' file", "grep --pre (not in allowlist)"),
        ("curl file:///etc/passwd", "curl file:// scheme"),
        ("curl scp://example.com/file", "curl scp:// scheme"),
        ("ls -X touch pwned", "ls -X (invalid flag)"),
    ]
    for cmd, desc in dangerous:
        assert allowed(cmd) is False, f"'{desc}' should be blocked"
        print(f"  ✓ {desc}")


def test_shell_composition_blocked():
    """Shell metacharacters must be blocked."""
    print("\nTesting: Shell composition blocked...")
    compositions = [
        ("git status; touch /tmp/pwn", "semicolon"),
        ("git status && touch /tmp/pwn", "&&"),
        ("git status & touch /tmp/pwn", "bare &"),
        ("git status | cat", "pipe"),
        ("git status || cat", "||"),
        ("git status > /tmp/out", "> redirection"),
        ("git status $(echo pwn)", "$() substitution"),
        ("git status `echo pwn`", "backtick substitution"),
        ("git status \x00", "null byte"),
        ("git status \x7f", "DEL char"),
    ]
    for cmd, desc in compositions:
        assert allowed(cmd) is False, f"'{desc}' should be blocked"
        print(f"  ✓ {desc}")


def test_curl_validation():
    """curl validation: schemes, output flags."""
    print("\nTesting: curl validation...")
    test_cases = [
        ("curl http://localhost/", True, "localhost http"),
        ("curl http://localhost:8080/api", True, "localhost with port"),
        ("curl https://example.com/", True, "https public"),
        ("curl file:///etc/passwd", False, "file:// blocked"),
        ("curl scp://example.com/file", False, "scp:// blocked"),
        ("curl dict://dict.org/word", False, "dict:// blocked"),
        ("curl http://localhost/ -o /tmp/file", False, "-o blocked"),
        ("curl http://localhost/ --output /tmp/file", False, "--output blocked"),
        ("curl http://localhost/ -d 'data'", False, "-d blocked"),
        ("curl http://localhost/ -K /tmp/config", False, "-K blocked"),
    ]
    for cmd, expected, desc in test_cases:
        result = allowed(cmd)
        assert result == expected, f"curl '{desc}': expected {expected}, got {result}"
        print(f"  ✓ {desc}")


def main():
    print("=" * 70)
    print("Command Policy Security Tests (SEC-030 fix - Real Corpus)")
    print("=" * 70)
    try:
        test_pocs_blocked()
        test_corpus_positive_real()
        test_dangerous_flags_blocked()
        test_shell_composition_blocked()
        test_curl_validation()
        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
