---
name: integration-validation
description: Validate accepted packages together against the approved feature contract, cross-package dependencies, global gates, and final evidence bundle.
license: MIT
compatibility: opencode
metadata:
  enabled_for: integrator, orchestrator, adversarial-judge
---

# Integration Validation

## Checks
- Accepted packages compose without contract drift.
- Shared state, migrations, routes, UI flows, and APIs agree.
- Global gates pass.
- Final evidence maps each acceptance criterion to package, validation, review, and regression coverage.

## Rule
Do not re-open accepted packages for cosmetic issues. Re-open only when integration creates a real contradiction,
regression, or uncovered acceptance criterion.
