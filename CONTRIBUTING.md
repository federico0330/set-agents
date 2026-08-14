# Contributing

## Access model

The maintainer (Federico) is the only account with write access to `main`. There is no
accepted-contributor list beyond that today. If you want to propose a change: fork the repo,
branch, and open a pull request against `main`. Issues are enabled on this repository (verified
via `gh repo view --json hasIssuesEnabled` -> `true`), so bug reports and feature requests belong
there too — except vulnerabilities, see `SECURITY.md`.

By opening a pull request you agree your contribution is licensed under the terms in `LICENSE`
(MIT).

## CI

`.github/workflows/ci.yml` runs on every `push` and `pull_request` against `main`, no extra setup
required on your side:

- `verify-linux` / `verify-macos`: `./ai/scripts/verify.sh` (full gate) on real Ubuntu and macOS
  runners.
- `windows-bootstrap`: parses `install.ps1`, runs it with `-DryRun`, `py_compile`s every
  `ai/scripts/*.py`, and runs the full `unittest` suite under Windows Python.

## Before opening a pull request

Run these locally first — they are the same commands CI runs, and they need to pass before review
makes sense:

```bash
python3 -m unittest discover -s tests   # pytest is NOT installed in this repo's dev environment
./ai/scripts/verify.sh                  # expect VERIFY_PASS
./build.sh --check                      # expect GLOBAL_TREE_SYNC_OK + BUILD_CHECK_PASS
git diff --check                        # no trailing-whitespace / conflict-marker errors
```

The full unit test suite takes a while (order of minutes); for long-running commands, use
`ai/scripts/heartbeat-run.py --interval 20 -- <command>` so the process doesn't look hung to
whatever is watching it (see `docs/adr/0041-build-check-verifies-global.md`).

## Scope of a pull request

- Keep diffs bounded to the change you're proposing — no opportunistic reformatting of unrelated
  files.
- Preserve existing public entry points (`set-agents`, `ai/scripts/set_agents_app.py --*` flags,
  `models.toml`/`tools.toml` schemas) unless the PR's own description says otherwise and updates
  the tests that pin them.
- Add or update the focused test that covers your change under `tests/` — the suite is what a
  reviewer actually checks against, not the description.

## What this repo is

`SET-AGENTS` installs and configures OpenCode, Claude Code, Codex, and Pi with a shared
model-routing, permissions, and workflow layer (see `README.md` and `TIPS-USO.md`). It has no
separate staging/production deploy of its own — the test suite and the two gate scripts above are
the validation surface.
