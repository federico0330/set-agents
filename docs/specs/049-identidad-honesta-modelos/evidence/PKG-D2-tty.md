# PKG-D2 — TTY observation summary (sanitized)

- **OpenCode fixture:** fake 1.18.14-shaped binary on isolated `PATH`; accepts **only** exact argv:
  - `session list --format json --pure`
  - `export --sanitize --pure <session_id>`
  - rejects `auth`, `login`, `install`, and any other command
- **Isolation:** minimal sanitized env (`clear=True`); `PATH` is exactly the fake bin directory (no trailing colon, no cwd); ephemeral `HOME` + `SET_AGENTS_STATE`; overlay at `~/.local/state/set-agentes/models.local.toml`
- **No auth / install / retention:** no credentials, no package installs, cache excludes session IDs, prompts, exports

## Observation path (rc=0)

`_refresh_model_state()` with fake binary:

- `observed.status=observed`, `observed.model=opaque/luna`
- `desired.model=opaque/terra` (SET default unchanged)
- `model-state.json` written without private fields (`root-private-id`, `messages`, `parts`)

## Degradation path (rc=0)

Absent OpenCode on isolated `PATH`:

- `observed.status=unobserved`, reason ∈ `{opencode_absent, child_failed}`
- overlay bytes unchanged

## Wizard path (rc=0)

`setup_models.wizard` → **Actualizar datos** → **Listo**:

- cache reflects `opaque/luna` observed, `opaque/terra` desired
- no session identifiers in persisted JSON
