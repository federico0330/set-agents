---
description: Deep read-only review of one integrated package
agent: package-reviewer
---
Review the integrated package specified by:
$ARGUMENTS

Inputs must include approved spec/version, package id, covered acceptance criteria, package diff, ownership paths,
gate results, assumptions, and risks. Return one consolidated package review with `pass`, `repair_required`, or
`blocked`. Do not edit files and do not ask the user.

Before review, the orchestrator must prove readiness:

```bash
python3 ai/scripts/feature-state.py next <feature_id>
```

Invoke this command only when `next` returns `PACKAGE_REVIEW`. If it does not, stop and report the missing
precondition instead of reviewing. After the review, the orchestrator must record the result:

```bash
python3 ai/scripts/feature-state.py record-review <PKG> <pass|repair_required|blocked> --finding '<json>' ...
```

When the package surface warrants specialist review, the orchestrator should run a bounded panel instead:

```bash
python3 ai/scripts/feature-state.py start-review-panel <PKG> --role package-reviewer --role security-auditor
python3 ai/scripts/feature-state.py record-subreview <PKG> security-auditor <pass|repair_required|blocked> --finding '<json>' ...
python3 ai/scripts/feature-state.py finalize-review-panel <PKG> <pass|repair_required|blocked>
```

That full panel counts as one deep package review cycle.

**`--role` is required and the panel is closed to everyone else.** `record-subreview` refuses a role the panel
never named, and it refuses it *after* the spawn is already paid for — so the membership list has to be the
one you are actually about to spawn. If a specialist becomes necessary once the panel is already open, grow
the panel rather than opening a second one:

```bash
python3 ai/scripts/feature-state.py extend-review-panel <PKG> --role architect --reason "<why this member became necessary mid-panel>"
```

A grown panel is still **one** cycle, and `--reason` is required so the record can tell it apart from a panel
that named all its members up front. Opening a second panel against a `panel_id` that already exists is an
error, not a correction — the one exception is a genuine retry, which passes the original `--event-id` and is
then an idempotent no-op.

When an independent review returns **after** its panel has closed, it still lands on the package record:

```bash
python3 ai/scripts/feature-state.py record-late-review <PKG> <role> --finding '<json>' ... --evidence "<what was examined and found>"
```

This consumes **no** review cycle — the panel is one cycle by rule, and counting a straggler as a second one
would misrepresent the process in the other direction. It takes no verdict, because it drives no phase: its
findings enter `package.findings`, and the acceptance gate refuses while any of them is open above `low`. It
is refused while a panel is still open (use `record-subreview`, or `extend-review-panel` first) and once the
package is `accepted`, because from there nothing could act on the finding. Do not write a late finding to
`decisions-log.jsonl`: a reader looking at the package would never find it.
