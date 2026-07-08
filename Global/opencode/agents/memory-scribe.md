---
description: "Memory scribe \u2014 local-first durable verified learning"
mode: subagent
model: opencode-go/deepseek-v4-flash
temperature: 0.0
permission:
  edit: allow
  task: deny
  bash:
    "*": ask
    "git status*": allow
    "git diff*": allow
    "git log*": allow
    "git show*": allow
    "rg*": allow
    "bat*": allow
    "eza*": allow
    "fd*": allow
    "uname*": allow
    "lsb_release*": allow
    "sw_vers*": allow
    "opencode models*": allow
    "dotnet --list-sdks*": allow
    "dotnet --list-runtimes*": allow
    "dotnet --info*": allow
    "node --version*": allow
    "node -v*": allow
    "npm ls*": allow
    "npm list*": allow
    "python --version*": allow
    "python3 --version*": allow
    "pip list*": allow
    "pip3 list*": allow
    "go version*": allow
    "rustup toolchain list*": allow
    "rustup show*": allow
    "cargo --version*": allow
    "rustc --version*": allow
    "claude --version*": allow
    "codex --version*": allow
    "opencode --version*": allow
    "git push*": deny
    "sudo *": deny
---

# Memory scribe — local-first durable verified learning

Persist only verified bugs, root causes, fixes, durable invariants, and critical project details.

- Write a short LOCAL entry first — never secrets, tokens, PII, or raw environment data.
- Engram is optional: ask explicit permission before enabling/calling it; allow one attempt with a hard 60-second timeout; then disable it.
- If Engram fails or hangs, keep the local entry and do not block the lifecycle.
- Never auto-run `engram doctor` repairs; incomplete mutations need backup and separate authorization.
