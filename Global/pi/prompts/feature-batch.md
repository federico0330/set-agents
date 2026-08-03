---
description: Start approved-spec workflow with package implementation and package review
---

Before doing anything else, invoke `subagent({ agent: "orchestrator", task: "<the request/arguments below>" })` to delegate this to the `orchestrator` role — never handle it directly.

Start package-based feature delivery for:
$ARGUMENTS

Workflow:
1. Close the Feature Contract and BDD acceptance criteria; `product-analyst` also writes the executive
   `proposal.md` (business-language deliverable for the client).
2. Run `spec-challenger` before human approval.
3. Stop for USER_APPROVAL, presenting spec + acceptance + `proposal.md` together.
4. Create coherent packages after approval.
5. Implement related tasks with local validations; do not deep-audit ordinary tasks one by one.
6. Run deterministic package gates.
7. Run one deep `package-reviewer` pass over the integrated package.
8. When useful, run a bounded review panel with specialist subagents; the panel is still one package review cycle.
9. Repair findings in one consolidated pass.
10. Run focused `delta-reviewer`.
11. Write/run regression and integration tests.
12. Start the app and perform browser/runtime QA when behavior is user-visible.
13. Integrate accepted packages, run final gates, judge, and report evidence.

Workers/reviewers must not interrupt the user for routine failures. Persist compact state in
`ai/state/features/<feature_id>.json`.

Executable state requirements:
- After USER_APPROVAL, run `python3 ai/scripts/feature-state.py init <feature_id> <spec_path> <spec_hash> --approved-by <who approved it> --ac <AC>... --mode <triage mode>`.
  `<spec_hash>` is `sha256sum <spec_path>` on the exact bytes that were approved, and `init` verifies it:
  a mismatch is `SPEC_HASH_MISMATCH` and no state file is written. If the spec changed after approval it
  needs approving again — a record that attests bytes nobody read is worse than no record.
- **A commit that delivers a package names it: `Feature <n> P<k>...`** — the feature number, then the package
  token, in that order and immediately adjacent (`Feature 006 P2-finding-verification: ...`). This is not
  style: `ai/scripts/check-feature-state.py` reads it to tell a delivery from a draft, so a subject that omits
  it lets a whole feature ship outside the state machine with the gate still reporting green. A commit that is
  not a package delivery must NOT carry that shape — put the package reference later in the subject
  (`Feature 005: handoff document for continuing P1`) so the pre-approval lifecycle stays quiet.
- Register each package with `create-package`, including multiple related `--task` values when functionally
  reasonable and `--context-pack docs/specs/<feature_id>/context/<PKG>.md`.
- Record every subagent delegation with `record-spawn <PKG> <role>` BEFORE spawning it.
- Before delegating implementation, run `feature-state.py transition PACKAGE_IMPLEMENTATION --package-id <PKG>`.
- After every implemented task, record local validation with `complete-task <PKG> <TASK> --validation <gate>`.
- Before package review, `feature-state.py next <feature_id>` must report `PACKAGE_REVIEW`; otherwise do not invoke reviewers.
- For multiple reviewers, use `start-review-panel` naming every member with `--role` (it is required), one
  `record-subreview` per specialist, then `finalize-review-panel`. Do not count each specialist as a separate
  deep audit cycle. A member that becomes necessary mid-panel is added with `extend-review-panel --role <r>
  --reason <why>`; a review that returns after the panel closed is recorded with `record-late-review <PKG>
  <role> --finding '<json>' --evidence <text>`. Neither costs an extra cycle, and re-opening an existing
  `panel_id` with `start-review-panel` is an error rather than a way to add anyone.
- Record package review, repair, delta review, acceptance, integration, and blockers with the matching `record-*`,
  `accept-package`, `transition`, or `block` command.
- Record tests with `record-testing` and runtime/browser QA with `record-runtime-qa` before package acceptance.

Report current phase, package status, gates, findings, retry budget, and next transition from the state file.

After DONE, close the delivery: the evidence bundle lives at `docs/specs/<feature_id>/evidence/`, and the
consumption summary can be added with `cost-report.py --project . --md > docs/specs/<feature_id>/evidence/cost.md`
(script lives in the SET-AGENTES repo, `ai/scripts/cost-report.py`).
