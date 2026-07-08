# Multi-harness evolution

## Problem

The repository duplicates role manifests and generated configuration, while global installation can overwrite unrelated user configuration. The coordinator also has contradictory write permissions and can execute the main loop.

## Invariants

- `roles.tsv` and `active-profile` are the only role/model selection inputs.
- Coordinators are read-only and delegate all mutating or gate work.
- A role or model family that mutates code cannot audit or judge that same change.
- Every change reaches a read-only adversarial judge after deterministic verification and domain audits.
- MCP servers remain disabled unless the user grants explicit, temporary permission.
- Global installation only mutates indexed files and explicitly managed configuration keys.
- Installation is staged, validated, diffed, backed up, atomic per file, and rolled back on smoke failure.

## In scope

Native agent generation for OpenCode, Claude Code, and Codex; coordinator policy enforcement; new lifecycle agents; safe installation; policy, golden, bootstrap, release, and timeout tests.

## Non-goals

- Automatically repairing Engram data.
- Enabling or invoking an MCP server.
- Performing a real push, PR creation, or merge during verification.
- Replacing project-specific verification commands.

