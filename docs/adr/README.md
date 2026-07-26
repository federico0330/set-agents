# ADR Index

> One row per ADR, no exceptions. `architect` updates this on every new ADR. An ADR is never deleted or
> edited retroactively — a superseded decision gets a new ADR (`Accepted`) and the old one is marked
> `Superseded by ADR-XXXX` here and in the file itself.

| ADR | Title | Status | Date | Supersedes | Superseded by |
|---|---|---|---|---|---|
| [0002](0002-generated-multi-harness.md) | Generate three harnesses from one roster | Accepted | 2026-07-08 | — | — |
| [0003](0003-models-toml-source-of-truth.md) | Use `models.toml` as the model source of truth | Accepted | 2026-07-24 | — | — |
| [0004](0004-adaptive-routing-pi-runtime.md) | Deterministic adaptive routing with opt-in Pi runtime | Superseded in part by 0005 | 2026-07-24 | — | 0005 (routing journal only) |
| [0005](0005-trusted-routing-sqlite-lifecycle.md) | Trusted routing lifecycle in local SQLite | Accepted | 2026-07-24 | 0004 (routing journal only) | — |
