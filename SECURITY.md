# Security Policy

## Supported versions

This project does not publish tagged releases yet (`git tag --list` returns nothing as of this
writing) — `main` is the only supported line, and security fixes land there.

## Reporting a vulnerability

Please do **not** open a public GitHub issue for a security vulnerability. Use GitHub's private
reporting channel instead:

- On the repo: **Security** tab -> **Report a vulnerability**, or directly
  <https://github.com/federico0330/set-agents/security/advisories/new>.

Private vulnerability reporting is enabled on this repository (verified live:
`gh api repos/federico0330/set-agents/private-vulnerability-reporting` -> `{"enabled": true}`).

This is a single-maintainer project, so there is no measured response-time SLA to promise here —
expect an acknowledgement from the maintainer, not a guaranteed turnaround.

## Scope

This repository installs and auto-updates third-party AI CLIs (OpenCode, Claude Code, Codex, Pi)
on the user's machine, and runs a routing/dispatch layer on top of them. Reports of particular
interest:

- Anything that lets install/auto-update (`install.sh`, `install.ps1`, `ai/scripts/install.py`)
  execute untrusted code or write outside the paths it documents.
- Credential or secret exposure — `.env` contents, `models.toml`, vault/Obsidian data, or
  provider tokens — in logs, generated notes, or committed files.
- A way to bypass the guarded/yolo permission profile documented in `README.md` (e.g. an
  irreversible operation — `sudo`, `rm -rf`, `git push --force` — running without the
  confirmation the harness promises).

## Out of scope

Vulnerabilities in the third-party CLIs this repo configures (OpenCode, Claude Code, Codex, Pi,
`gh`, `gcloud`, etc.) belong to their own upstream repositories, not this one.
