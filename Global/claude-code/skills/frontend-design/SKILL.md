---
name: frontend-design
description: Distinctive, intentional visual design built on design tokens, deliberate typography, reusable components, responsive layout, and WCAG AA accessibility — not templated framework defaults. Load when building or reshaping any UI surface.
license: MIT
compatibility: opencode
metadata:
  enabled_for: ux-ui-designer, implementer
---

# Frontend Design

## When to use
Creating a new screen, component, or design system, or reworking UI that reads as generic. Use whenever choices about spacing, type, color, or states are being made.

## Checklist
- **Intentional direction** — pick a point of view (mood, reference, contrast) before laying out; avoid default theme out-of-the-box look.
- **Design tokens** — define spacing, type, color, radius, and shadow as named scales; never hardcode one-off values.
- **Spacing scale** — one rhythm (e.g. 4/8px steps); align everything to it.
- **Typography** — pair at most two families with clear roles (display vs body); set a modular type scale and line-height.
- **Color** — a small palette with semantic roles (bg, surface, text, accent, danger); derive shades, don't pick ad hoc.
- **Component reuse** — compose from shared primitives; one source of truth per pattern.
- **Responsive** — design mobile-first; verify at narrow, mid, and wide breakpoints.
- **States** — design empty, loading, success, and error for every data view; no dead ends.

## Rules
- Every visual value comes from a token; raw magic numbers are a defect.
- Semantic HTML first (button, nav, label, headings in order); ARIA only to fill gaps.
- Meet WCAG AA: text contrast >= 4.5:1 (>= 3:1 large), visible focus rings, hit targets >= 44px.
- Keyboard reachable and operable; never trap focus or remove outlines without a replacement.
- Don't ship a happy-path-only screen — empty/loading/error must exist.

## Verification ideas
- Tab through the screen: is order logical and focus always visible?
- Run a contrast check on text and interactive elements.
- Resize to 320px and to wide desktop — does anything break or overflow?
- Force each state (empty, loading, error) — is each designed, not blank?
- Diff against framework defaults: does it look intentional or templated?
