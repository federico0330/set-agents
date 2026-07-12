---
description: Start approved-spec workflow with package implementation and package review
agent: orchestrator
---
Start package-based feature delivery for:
$ARGUMENTS

Workflow:
1. Close the Feature Contract and BDD acceptance criteria.
2. Run `spec-challenger` before human approval.
3. Stop for USER_APPROVAL of the spec.
4. Create coherent packages after approval.
5. Implement related tasks with local validations; do not deep-audit ordinary tasks one by one.
6. Run deterministic package gates.
7. Run one deep `package-reviewer` pass over the integrated package.
8. Repair findings in one consolidated pass.
9. Run focused `delta-reviewer`.
10. Integrate accepted packages, write end-stage regressions, run final gates, judge, and report evidence.

Workers/reviewers must not interrupt the user for routine failures. Persist compact state in
`ai/state/features/<feature_id>.json` when possible. Report current phase, package status, gates, findings,
retry budget, and next transition.
