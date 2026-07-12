---
name: test-gap-analysis
description: Identify meaningful package-level and feature-level test gaps after implementation/review convergence without using tests as the implementation guardrail.
license: MIT
compatibility: opencode
metadata:
  enabled_for: package-reviewer, delta-reviewer, test-writer, adversarial-judge
---

# Test Gap Analysis

## Use
After implementation exists and package review is evaluating whether accepted behavior has durable regression
coverage.

## Checks
- Each acceptance criterion has at least one verification path.
- Important failure modes are covered.
- Tests assert real expected values, not implementation accidents.
- No skipped/weakened assertions.

## Output
Report gaps as findings only when they create real regression risk for accepted behavior.
