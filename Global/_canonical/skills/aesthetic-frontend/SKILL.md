---
name: aesthetic-frontend
description: Brand-grade, non-generic UI — start from a real company's design brief and build with animated component kits (getdesign.md, Skiper UI, Motion Primitives, motion galleries) so even an MVP looks intentional. Load whenever building or reshaping any user-facing surface.
license: MIT
compatibility: opencode
metadata:
  enabled_for: frontend-engineer, ux-ui-designer, implementer
---

# Aesthetic Frontend

The first thing a user sees is the aesthetic. An MVP is not an excuse for a templated, default-theme look.
Pick a deliberate visual direction FIRST, then build it with these kits instead of hand-rolling generic markup.
Pair this with `frontend-design` (tokens/typography/a11y) and `clean-architecture` (component structure).

## Workflow (aesthetics first, then structure)
1. **Direction from a real brief** — before laying anything out, pull a design brief from **getdesign.md**
   (`https://getdesign.md`): 300+ analyzed DESIGN.md files from real brands (Apple, Figma, Stripe, Ferrari,
   Tesla, Coinbase, Revolut…). Adopt one brand's palette/type/spacing/component language as the north star, or
   match a reference site the user names. This is the antidote to "generic AI layout".
2. **Structure with shadcn/ui** — base primitives (accessible via Radix). Keep tokens in one place.
3. **Elevate with animated component kits** (copy-paste, own the code — no lock-in):
   - **Skiper UI** (`https://skiper-ui.com`) — 73+ animated components on top of shadcn (card swipers, marquees,
     scroll effects, theme toggles) via the shadcn CLI. **24+ are free; ~54 are premium/paid** — prefer the free
     set and only reach for premium if the user opts in. WAI-ARIA via Radix.
   - **Motion Primitives** (`https://motion-primitives.com`) — open-source animated primitives for text effects,
     cards, transitions, and scroll/micro-interactions. Install: `npm i motion lucide-react`, then
     `npx motion-primitives@latest add <component>` (e.g. `text-effect`). Same copy-paste philosophy as shadcn.
   - **MotionSites** (`https://motionsites.ai`) — a **premium/paid** library of 100+ AI hero-section prompts and
     animated-background/gradient templates by use case (SaaS, agency, portfolio, DeFi, travel…). Paste a prompt to
     generate production-ready animated React, then refactor it to tokens + SOLID and strip any bloat. Use only when
     the user has access — flag it before use; otherwise prefer the free kits above.
   - **Inspiration galleries** — for direction/taste only (e.g. Awwwards "Motion", motion.page); never copy proprietary work.
4. **Motion with restraint** — animation serves hierarchy and feedback, not decoration. Respect
   `prefers-reduced-motion`; keep durations/easings as tokens; never block interaction on an animation.

## Non-negotiables
- Use design tokens (spacing/type/color/radius/shadow) — never one-off magic numbers. See `frontend-design`.
- Accessibility is not optional: semantic HTML, focus order, keyboard operability, WCAG AA contrast.
- Error UX per `frontend-error-ux`: no native `alert()`; app's own toast; centralized status→message mapping.
- Prefer free/open kits; flag any premium/paid component before using it.
- Components stay small, single-responsibility, and reusable (SOLID) — see `clean-architecture`.

## Definition of done (aesthetic)
The screen reads as intentional (clear point of view, consistent tokens, deliberate type/color), animates with
purpose and reduced-motion support, and is accessible — not a default-theme MVP.
