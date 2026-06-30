---
name: secrets-hygiene
description: Repo hygiene checklist — no committed secrets/connection strings, gitignore build artifacts (bin/obj/*.user), no dead/commented code, no real credentials in appsettings. Load before commit/PR and when touching config or VCS.
license: MIT
compatibility: opencode
metadata:
  enabled_for: security-auditor, auditor, implementer
---

# Secrets & Repo Hygiene

## When to use
Before commit/PR, and whenever the diff touches config files, connection strings, or repository structure.

## Inputs
`git diff`, `.gitignore`, config files (`appsettings*.json`, `.env*`), tracked files list.

## Outputs
`PASS` or findings (`id, severity, file:line, evidence, impact, minimal_fix, verification`).

## Checklist
1. **No committed secrets** — no real passwords/connection strings/tokens/keys in tracked files
   (`appsettings.json`, `.env`, source). Use env vars / secret store; commit only `.env.example` / typed config schema.
2. **Ignore build artifacts** — `.gitignore` covers `bin/`, `obj/`, `*.user`, `appsettings.Development.json`,
   `node_modules/`, `dist/`, coverage. If already tracked: `git rm -r --cached` then commit.
3. **No dead code** — delete commented-out blocks and abandoned scaffolding (`Class1.cs`, `WeatherForecast.cs`,
   unused template projects); that is what version control is for.
4. **No PII / secrets in logs** — diff doesn't log tokens, passwords, or personal data.

## Verification ideas
`git grep -nE '(Password|ConnectionString|ApiKey|secret)\s*=\s*["'\''][^"'\'' ]+' -- tracked files` finds
nothing real. `git ls-files | rg '^(bin|obj)/'` is empty. No `// old code` blocks remain in the diff.
