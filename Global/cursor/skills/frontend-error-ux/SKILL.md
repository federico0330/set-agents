---
name: frontend-error-ux
description: Frontend error-UX checklist — no native alert(), use the app's own notification component, centralize status→message mapping, and refresh stale state after a conflict. Load when touching client-side error handling or user feedback.
license: MIT
compatibility: opencode
metadata:
  enabled_for: ux-ui-designer, package-reviewer, implementer
---

# Frontend Error UX

## When to use
Any client-side change handling API errors, conflicts, or user feedback after an action.

## Inputs
`git diff` of client code, the API status contract, the app's notification/component system.

## Outputs
`PASS` or findings (`id, severity, file:line, evidence, impact, minimal_fix, verification`).

## Checklist
1. **No native `alert()`** — use the app's own toast/notification component (non-blocking, on-brand).
2. **Refresh stale state after conflict** — when another user wins (e.g. 409), show a friendly message AND
   reload the affected view automatically; never leave outdated data (a lost seat still shown as free).
3. **Centralized status→message mapping** — one module maps HTTP status/codes to user-facing messages, so
   tone stays consistent and strings are translatable. No ad-hoc messages scattered per call site.
4. **All states handled** — loading, empty, success, partial, error; disable controls during in-flight actions.
5. **Accessible feedback** — messages reach assistive tech (aria-live), focus is managed, contrast meets AA.

## Verification ideas
Trigger a 409 from two clients: the loser sees an in-app toast ("Ese asiento ya no está disponible") and the
map refreshes to show it taken — no `alert()`, no manual reload. All messages come from the central mapper.
