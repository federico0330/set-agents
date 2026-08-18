---
name: web-frontend-fundamentals
description: Runtime fundamentals a frontend build/review must respect — the browser pipeline, DOM-as-API, the single-threaded event loop (micro- vs macro-tasks), Virtual DOM/reconciliation cost, state & UI race conditions, CSR/SSR/SSG rendering strategies, and Core Web Vitals. Load when building interactive UI, managing client state/async, or reviewing render/perf.
license: MIT
compatibility: opencode
metadata:
  enabled_for: frontend-engineer, ux-ui-designer, implementer, package-reviewer
---

# Web Frontend Fundamentals

## When to use
Before (or while) building anything interactive — components that fetch, hold client state, animate, or paginate —
and when reviewing render cost or perceived performance. This is the RUNTIME companion to the visual-design skills
(`frontend-design`, `aesthetic-frontend`, `frontend-error-ux`): those decide how the UI looks; this one decides how
it behaves under async work, how it renders, and why it stays (or stops being) responsive. Complements
`performance-scalability` (server/query cost) on the client side.

## The 7 fundamentals
1. **Browser pipeline** — a page is not "just shown": DNS resolves the host → the browser downloads and parses
   HTML+CSS → builds the **render tree** → then reacts to user events. Everything you ship lands somewhere on this
   path; know which stage your change taxes (parse, layout, paint, or interaction).
2. **HTML / CSS / JS = structure / presentation / logic** — kept decoupled on purpose. Structure is semantic
   markup, presentation is styling, logic is behavior. Leaking one into another (inline styles, DOM strings built
   in logic) is the first smell.
3. **The DOM is an in-memory API, not the HTML file** — it is the live tree the browser exposes to script, not the
   bytes you authored. Reading/mutating the DOM IS the core of interaction, and each real mutation can force layout
   and paint — so it is the expensive part.
4. **The event loop is single-threaded** — JS runs on one thread. Concurrency is managed by queues: **microtasks**
   (Promises, `queueMicrotask`, `await` continuations) drain **completely** before the next **macrotask**
   (`setTimeout`, UI rendering, I/O). Two consequences you must design around: (a) never block the thread with
   long synchronous work — the UI freezes; (b) ordering is not intuitive — an `await` continuation runs *before* a
   `setTimeout(0)` queued earlier, because microtasks jump the macrotask queue.
5. **Virtual DOM / reconciliation** — mutating the real DOM is costly, so modern frameworks compute changes on a
   lightweight in-memory tree and apply only the diff (reconciliation). You get this for free only if you help it:
   stable keys, no needless re-renders, memoization on hot subtrees.
6. **State is a snapshot of UI + data — beware race conditions** — state is the current "photo" of what the user
   sees and what you know. The classic bug is a **race condition**: a slower earlier request resolves *after* a
   newer one and overwrites fresh state with stale data. Defend it: cancel in-flight requests (AbortController),
   discard responses that don't match the latest request version, or make the action idempotent.
7. **Rendering strategy: CSR vs SSR vs SSG** — a per-need choice, not a religion:
   - **CSR** (client-side): fast initial shell, but Time-to-Interactive depends on JS executing on the client;
     weaker SEO.
   - **SSR** (server-side): server ships ready HTML → better perceived load and SEO; costs server render time.
   - **SSG** (static generation): HTML baked at build time → ideal for static content (blogs, landings).
   Modern frameworks (e.g. Astro) combine these **per component**. Pick per the component's need and name the trade.

## Target metrics
Time-to-Load (visual), FPS / smoothness, Time-to-Interactive (when the user can actually act) — map these to the
**Core Web Vitals** (LCP, INP, CLS). Improve them with lazy-loading, asset reduction, and efficient algorithms on
the hot path, not by guessing.

## Rules
- Pick the rendering strategy (CSR/SSR/SSG) per component and state the tradeoff (TTI vs SEO vs simplicity) in the
  task note when it is non-obvious — so the auditor can check it.
- Never block the event loop on the main thread; break long work up (chunking, `requestIdleCallback`, workers).
- Every async response that can arrive out of order must be cancelled or version-discarded — stale must never
  overwrite fresh.
- Budget render: no mass re-render without stable keys / memoization; a re-render storm on a hot path is a finding.
- Keep structure, presentation, and logic separated; do not build DOM strings inside business logic.

## Verification ideas
- Does the UI stay responsive while async work runs (no main-thread freeze under load)?
- Fire two overlapping requests where the first resolves last — does stale data overwrite fresh? (must not)
- Is the CSR/SSR/SSG choice justified for this component, or defaulted by habit?
- Are LCP / INP / CLS within target on the happy path, and are heavy assets lazy-loaded?
