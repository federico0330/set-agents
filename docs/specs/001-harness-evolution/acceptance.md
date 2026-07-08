# Acceptance criteria

## AC-001 — Single roster

Given both quota profiles, when generation runs, then every role is read from one unique row in `roles.tsv` and `active-profile` selects the OpenCode model column without rewriting the roster.

## AC-002 — Separation graph

Given a role combining mutation and audit or an auditor sharing an implementation model family, when validation runs, then it fails with a concrete policy error.

## AC-003 — Read-only coordinator

Given coordinator policy fixtures, when safe diagnostics and version queries are checked, then they are allowed; when writes, redirection, installs, Git mutation, `mcp.sh`, or `loop.sh` are checked, then they are denied.

## AC-004 — Native formats

Given a valid roster, when generation runs, then OpenCode and Claude frontmatter parse, OpenCode MCP entries are disabled, Claude includes a Bash guard, and every Codex role is a parseable TOML agent with an explicit sandbox.

## AC-005 — Managed installation

Given unrelated user plugins and files, when installation runs, then only indexed paths and managed configuration keys change.

## AC-006 — Rollback

Given a forced smoke-test failure, when installation runs, then all managed live files return to their pre-install state.

## AC-007 — Required lifecycle

Given the orchestrator prompt, when inspected, then it routes bootstrap, factory, gates, audits, repair, judge, release, and memory without asking the user to run commands manually.

## AC-008 — Human gates

Given release state, when verify/audits/judge are not green, then local commit and publication are blocked; when green, local commit is permitted but push/PR and merge require distinct confirmation flags.

## AC-009 — Resilience and idempotence

Given empty/existing/conflicting project fixtures and a hanging Engram command, when helper tests run, then existing content is preserved, conflicts are reported, repeated bootstrap is idempotent, and local memory succeeds without waiting more than 60 seconds.

