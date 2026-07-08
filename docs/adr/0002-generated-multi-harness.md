# ADR 0002: Generate three harnesses from one roster

## Status

Accepted

## Decision

Keep prompts and portable skills canonical in `Global/_canonical`, keep role metadata in `roles.tsv`, and generate harness-native artifacts into `Global/{opencode,claude-code,codex}`. Installation uses a managed-file index plus narrow JSON overlays for shared settings.

Codex uses standalone agent TOML files. Claude uses tool allowlists and a `PreToolUse` Bash guard. OpenCode uses ordered permission patterns. MCP definitions remain disabled.

## Consequences

Generated output is reviewable and golden-tested. Adding a role requires one roster row and one canonical prompt. Installation cannot silently replace unrelated plugins or custom files, but managed settings require explicit merge logic.

