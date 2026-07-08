---
name: request-triage
description: Intake + mode selection for the orchestrator — classify an incoming request into an execution mode (feature/SDD, scoped-feature, quick-fix, or incident/break-glass), ask scoping questions BEFORE starting, and know which normally-dormant agents (red-team, blue-team, security-auditor, brainstormer, ux-ui-designer) to pull in and when. Load at the START of every user request, before delegating anything.
license: MIT
compatibility: opencode
metadata:
  enabled_for: orchestrator
---

# Request Triage

## When to use
At the very start of EVERY user request, before any delegation. Classify the request, decide the mode, ask
what you must, then run the matching flow. Do not dive into the SDD pipeline reflexively — that is exactly the
failure this skill exists to prevent (applying the heavy flow to a problem that needed a fast, clever fix).

## Step 0 — intake (always, before delegating)
1. Restate the request in one line and name the **mode** you are choosing + why.
2. If the request is ambiguous on scope, risk, or intent, ask **1–2 scoping questions first** — do NOT start.
   Terse in execution, but interrogate up front. This is where you "stop the cart".
3. Only then delegate the first action of the chosen mode.

## The four modes

### 1. Feature / build — full SDD (default; ~90% of requests)
Triggers: "build an app", "add a feature", anything net-new or non-trivial touching architecture/data/security.
Before code, **run the scoping interrogation** (load `system-design-decisions`): what future/scale do you
expect? what data model? where centralized vs decentralized? what must be secure day one? Then the rigorous
**SDD → BDD → implement⇄audit loop → regression tests** flow: spec → design+ADR (SDD) → acceptance
Given-When-Then (BDD) → **implement → read-only audit against the spec/design → repair → audit → … until no
findings** → regression tests (written now) → verify → audit panel → judge → release → memory. Tests do NOT gate
implementation; the auditor does. This order is mandatory in feature mode; the three lanes below are the only
exceptions (scoped-feature / quick-fix / incident).

### 2. Scoped-feature — bounded but security-sensitive (the middle lane)
Triggers: a net-new but **well-bounded** feature with a clear blast radius that DOES touch a sensitive surface
(auth / PII / external API) on established infrastructure — the canonical case is "a login view + password
recovery on Supabase". It is too sensitive for quick-fix, but running the full panel after every task and every
repair is waste (that is what turned a login into a 4-5h grind).
Flow: SDD-lite (spec + acceptance Given-When-Then; an ADR only if there is a genuinely new architectural
decision) → BDD connection point with the user → implement⇄audit loop → **ONE consolidated `auditor` pass over
the complete diff** → `security-auditor` + `red-team` **once at the end** (not per cycle) → regression tests →
`adversarial-judge` → release → memory.
What is cut: the heavy panel does NOT re-run after each task or each trivial repair — it runs once on the full
diff before the judge. The security guarantee is preserved (auth ALWAYS passes security + red-team once), but the
task×cycle multiplier is eliminated. Ambiguous between scoped and full feature → **go up to feature mode**.

### 3. Quick-fix — bounded and low-risk
Triggers: a small, well-understood change with an obvious blast radius (copy tweak, one-function bug, config
value). Flow: implement → `gate-runner` verify → done. Skip spec/design/ADR and the full audit panel — UNLESS
real risk surfaces mid-way (touches auth/money/PII/migration), then **escalate to scoped-feature or feature
mode**.

### 4. Incident / break-glass — production is broken NOW
Triggers: production down or a user blocked with no in-app path, and speed matters more than ceremony (e.g. a
prod user needs a password reset and there is no forgot-password flow → a one-shot `psql` script, done).
Flow: fastest correct + ingenious fix, minimal ceremony, delegate the actual change to `debugger`/`implementer`
(you still never implement yourself). MANDATORY afterward — never skip: (a) write down exactly what was done,
(b) open a follow-up task to do it properly, (c) delegate a memory note. Break-glass is a conscious, logged
exception to the rigor default — not a licence to abandon it.

Ambiguous which mode? Ask. When risk is unclear, bias toward the more rigorous mode.

## Waking the dormant agents (concrete triggers, not "by risk")
These agents are permitted but easy to forget — pull them in on these triggers:
- **auth / money / PII / any external input** → `security-auditor` AND `red-team` are MANDATORY before the judge.
- **after red-team finds something** → `blue-team` to design the hardening + detection.
- **any user-facing surface / new UI** → `ux-ui-designer` (brand-grade, accessible; not generic defaults).
- **the approach is genuinely open / multiple viable designs** → `brainstormer` before committing.
- **queries / lists / transactions / migrations** → `db-auditor` + `performance-auditor` (already mandatory).

**Cadence by mode:** in **feature** mode these run per the orchestrator's cadence (heavy panel on first touch of
the surface and again only when a repair changes that surface, plus one full panel pass before the judge). In
**scoped-feature** mode they run **once at the end** on the complete diff, not per task or per repair. Either
way, a full panel pass before `adversarial-judge` is mandatory — never skip the pre-judge panel.

## Hard logic → hosted implementer (never the local leaf)
Concurrency, atomic transactions, money/financial rules, and security-critical logic must NOT be implemented by
the local leaf model (the cheap 8B) — a weak first draft on exactly this logic triggers more strong-auditor
rework than it saves. When a task touches these, pin implementation to a **hosted** model (e.g. `openai/gpt-5.4`)
rather than the local `implementer`. The autonomous `loop.sh` does this automatically when the spec flags a
sensitive/data surface; in the interactive path, route such implementation to a hosted model deliberately. The
local leaf stays for boilerplate/CRUD/UI churn, which the audit panel then reviews.

## Output of triage
State: chosen mode + one-line why, the scoping questions asked (if any), and the first delegation. In
incident mode, also name the follow-up task you will open once the fire is out.
