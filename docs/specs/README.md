# Spec Index

> One row per feature, no exceptions. `product-analyst` updates this on draft (`Draft`), approval
> (`Approved`), integration (`Shipped`), or when a newer spec replaces this one's behavior
> (`Superseded by <id>`). Rows and spec folders are never deleted — this table is the single place to check
> what is current instead of crawling every folder.

| ID | Title | Status | Date |
|---|---|---|---|
| [001](001-harness-evolution/spec.md) | Package-based harness evolution | Shipped | 2026-07-08 |
| [002](002-adaptive-pi-orchestration/spec.md) | Adaptive orchestration and Pi runtime | Superseded by [003](003-trusted-routing-pi-runtime/spec.md) | 2026-07-24 |
| [003](003-trusted-routing-pi-runtime/spec.md) | Trusted routing and Pi runtime recovery | Approved | 2026-07-24 |
| [004](004-adaptive-dispatch/spec.md) | Adaptive dispatch (per-task model routing) | Shipped | 2026-07-27 |
| [005](005-portable-harness/spec.md) | Portable harness, mandatory vault, TUI selector | Draft | 2026-07-27 |
| [014](014-model-preference-policy/spec.md) | Model preference policy (credential-aware role-class bias) | Draft | 2026-07-31 |
| [015](015-anthropic-dispatch-parity/spec.md) | Anthropic dispatch parity v3.0.0 (cross-lane redirect to Claude Code — OpenCode-lane Anthropic auth needs a metered API key, never OAuth, so no OpenCode-lane Anthropic variants; routing-service redirect + Claude-Code CLI spawn with a live-verified CLI-level tool ceiling + review-independence fix, time-boxed ~12 days + `go-zen`/`.claude`-axis collision fixes) | Draft (round-2 correction pass, pending re-challenge) | 2026-07-31 |
| [034](034-cuota-organica-y-writer-barato/spec.md) | Cuota orgánica y escritor barato (quick-fix 1–3 enforceable, writer barato + un salvage, techo frontier, pins Cursor; supersede parcial de 032 AC-06) | Approved | 2026-08-19 |
