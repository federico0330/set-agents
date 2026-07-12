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
python3 ai/scripts/feature-state.py start-review-panel <PKG> --role package-reviewer --role security-auditor --role db-auditor
python3 ai/scripts/feature-state.py record-subreview <PKG> security-auditor <pass|repair_required|blocked> --finding '<json>' ...
python3 ai/scripts/feature-state.py finalize-review-panel <PKG> <pass|repair_required|blocked>
```

That full panel counts as one deep package review cycle.
