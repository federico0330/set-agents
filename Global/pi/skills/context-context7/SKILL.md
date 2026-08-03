---
name: context-context7
description: Pull current, version-specific library/framework/SDK/ORM docs via the Context7 MCP when an API may have changed or correctness depends on up-to-date references, instead of guessing from stale model memory. Load when you need authoritative current docs for an external dependency.
license: MIT
compatibility: opencode
metadata:
  enabled_for: implementer, architect, debugger, test-writer
---

# Context Context7

## When to use
Fetch current, version-specific documentation for an external library/framework/SDK/ORM before relying on its API.

## Server
- Context7 MCP, remote at `https://mcp.context7.com/mcp`.
- Invoke by adding `use context7` to the request, or call the MCP's resolve + docs tools directly.

## USE when
- The API may have changed since the model's training cutoff.
- The specific framework/SDK/ORM VERSION matters for correctness.
- Security or behavior depends on current, authoritative docs.
- The model is unsure of the exact signature, option, or current best practice.

## DO NOT USE when
- The answer is already in the repository (read the code/config first).
- The task is pure local domain/business logic with no external API.
- It would only add tokens without reducing risk or uncertainty.

## Procedure
1. Confirm the dependency and the version in use (`package.json`, lockfile, `requirements.txt`, etc.).
2. Resolve the library, then fetch docs scoped to that version and the specific topic.
3. Apply the docs to the code; cite the version you relied on.

## Rules
- Repo first, Context7 second — never fetch docs for something the codebase already answers.
- Scope queries to the installed version; do not apply newer-version APIs to an older pinned dep.
- Use it to reduce risk, not to pad context — skip when local knowledge is sufficient.
