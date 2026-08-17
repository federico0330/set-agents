---
name: solution-baselines
description: Pre-decided starting points per solution category (management webapp/dashboard, scraping+data/ML, B2B API/integrations, e-commerce/landing) — golden-path stack, the architecture conventions already taken with explicit YAGNI thresholds (three first-class axes + transversal defaults), typical package shapes, and recurring risks. Load at the START of any architecture/design for a new system or module — design as a DEVIATION from the matching baseline, not from zero.
license: MIT
metadata:
  enabled_for: orchestrator, architect, project-bootstrapper, package-planner
---

# Solution Baselines

## Why this exists
Deriving every architecture from first principles costs tokens and produces inconsistent systems across
client projects. A freelance practice repeats categories of solutions; each category has a baseline whose
decisions were already reasoned once. The architect's job on a new project is to (1) pick the matching
baseline, (2) design only the DEVIATIONS the client's case actually requires, and (3) record each deviation
as an ADR. Conformance with the baseline needs no ADR — deviation does.

## How to use
1. Classify the request into one category (or declare "no baseline fits" — that itself goes in `design.md`
   with one line of why, and you design from `system-design-decisions` as usual).
2. Read the matching reference file in `references/`:
   - `references/gestion-dashboard.md` — management webapp: CRUD + auth + roles + reports
   - `references/scraping-datos-ml.md` — scraping pipelines, normalization, storage, ML features
   - `references/api-b2b-integraciones.md` — third-party integrations, webhooks, queues, idempotency
   - `references/ecommerce-landing.md` — conversion-oriented store/landing, brand-grade UI, payments
3. In `design.md`, state: chosen baseline, deviations (each → ADR), and confirmations (one line each, no ADR).
4. The three architecture axes (data store / API Gateway / deploy platform) come PRE-DECIDED in each
   baseline with explicit YAGNI thresholds ("no X until Y"). If the client's case crosses a stated
   threshold, that is a deviation → ADR + the orchestrator's Question policy still applies.

## Hard rules
- A baseline is a starting posture, not a straitjacket: crossing a YAGNI threshold with evidence is
  expected and healthy. Ignoring a threshold silently is not.
- Never copy a baseline's stack into `design.md` when the project already has an established stack —
  existing conventions win; the baseline then only contributes its risk checklist and package shapes.
- Baselines are maintained here (harness repo), not per project. If a real project teaches a better
  default, update the reference file in the same change that records the lesson (memory-scribe trigger).
