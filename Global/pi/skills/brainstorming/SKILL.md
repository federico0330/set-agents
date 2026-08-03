---
name: brainstorming
description: Diverge then converge — generate 3-6 genuinely different options spanning boring to ambitious, weigh tradeoff/risk/cost on each, surface hidden assumptions and reversibility, then land one recommendation plus a runner-up with no false balance. Load when exploring approaches before committing to one.
license: MIT
compatibility: opencode
metadata:
  enabled_for: brainstormer, architect, product-analyst
---

# Brainstorming

## When to use
A decision has more than one credible path: architecture, product direction, tooling, or sequencing. Use before writing a proposal or design, not after the answer is already fixed.

## Cycle / Checklist
1. **Frame** — state the actual need and the constraints in one sentence.
2. **Diverge** — produce 3-6 options that are genuinely different in approach, not variants of one idea.
3. **Anchor the range** — include at least one boring/low-risk option and one ambitious/high-upside option.
4. **Evaluate each** — for every option note tradeoff, key risk, and cost (effort/time/complexity).
5. **Surface assumptions** — list the hidden assumptions each option depends on; flag the ones that, if wrong, kill it.
6. **Classify reversibility** — mark each decision reversible (cheap to undo) or irreversible (hard to undo).
7. **Converge** — give one clear recommendation and one runner-up, with the reason the rest were cut.

## Rules
- No false balance: do not present options as equal when they are not — take a position.
- Options must be materially distinct; drop near-duplicates.
- Prefer the smallest option that actually meets the need over the most impressive one.
- Be honest about cost and risk; do not hide the downside of your recommendation.
- For irreversible decisions, raise the bar for evidence and call out the lock-in explicitly.
- Recommend exactly one primary path; ambiguity is a non-answer.

## Inputs / Outputs
- **Inputs**: the problem/need, known constraints, and any non-negotiables.
- **Outputs**: a ranked option set (each with tradeoff/risk/cost/assumptions/reversibility), one recommendation, one runner-up, and the cut rationale.
