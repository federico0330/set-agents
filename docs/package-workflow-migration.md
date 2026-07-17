# Package Workflow Migration

## Diagnosis
The previous harness preserved quality but used the wrong unit of control after spec approval: ordinary small
tasks triggered deep audit, repair, re-audit, security/performance/stability checks, and user questions too often.
That created a task x review-cycle multiplier and made routine failures look like human decisions.

## Preserved
- Requirements conversation.
- Feature Contract / spec draft.
- Spec challenge before approval.
- Human approval before implementation.
- Separation of duties: implementers do not approve; reviewers are read-only.
- Deterministic gates and final adversarial judgment.

## Changed
After USER_APPROVAL, work now advances by coherent packages:

`PACKAGE_PLANNING -> PACKAGE_IMPLEMENTATION -> PACKAGE_GATES -> PACKAGE_REVIEW -> PACKAGE_REPAIR ->
DELTA_REVIEW -> PACKAGE_ACCEPTED -> INTEGRATION`.

Tasks inside a package still run local validation, but deep review runs on the integrated package. Findings are
reported together, repaired together, and re-reviewed as a delta. Each package has a maximum of two deep review
cycles before `BLOCKED`.

`BLOCKED` has no automatic exit and `transition` cannot leave it — it is a deliberate sink. The only formal way
out is `feature-state.py reopen --reason ... --authorized-by ...`, which requires both fields, only applies from
`BLOCKED`, and moves the feature back to `PACKAGE_PLANNING` so the remaining real work can be split into a new
package (e.g. after a budget-exhaustion block where scope genuinely still needs finishing). It requires the human
to have explicitly authorized the reopen; it is not a generic unblock.

## State
Package features use compact state under `ai/state/features/<feature_id>.json` with approved spec version/hash,
acceptance criteria, packages, tasks, ownership paths, gates, attempts, findings, repairs, and final state.

## Commands
- `/feature-batch` starts the package workflow.
- `/resume-feature` resumes from feature state.
- `/audit-package` runs the package reviewer.
- `/feature-status` reports state without mutation.

## Validation
Use `./build.sh --check`, `python3 -m unittest discover -s tests -v`, and
`PROYECTO/ai/scripts/feature-state.py dry-run <feature_id>` for a safe smoke simulation.
