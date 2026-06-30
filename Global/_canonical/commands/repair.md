---
description: Fix concrete audit findings minimally
agent: implementer
---
Repair ONLY the concrete findings in ai/state/audit-findings.md (or: $ARGUMENTS).
Sort blocker>major>minor, make the minimal fix per finding, do not change acceptance criteria or weaken
tests, run focused verification then ai/scripts/verify.sh, and hand back to the auditor for re-audit.
