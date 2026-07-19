---
name: request-triage
description: Intake + mode selection for the orchestrator — classify an incoming request into an execution mode (feature/SDD, scoped-feature, quick-fix, or incident/break-glass), ask scoping questions BEFORE starting, and know which normally-dormant agents (security-auditor, brainstormer, ux-ui-designer) to pull in and when. Load at the START of every user request, before delegating anything.
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

### 1. Feature / build — full SDD (opt-in; only when the work truly demands it)
Triggers — full SDD is chosen ONLY when at least one of these holds, otherwise default to scoped-feature:
- a net-new system or module (not an addition to established infrastructure),
- genuinely multi-package work (several coherent packages with dependencies),
- the request touches one of the three architecture axes (data store type, API Gateway, deploy platform)
  with no ADR covering it.
Before code, **run the scoping interrogation** (load `system-design-decisions`): what future/scale do you
expect? where centralized vs decentralized? what must be secure day one? and name these three axes
explicitly, not generically — **does persistence need vector/semantic search or does relational cover it?
does this need an API Gateway or is it a monolith with one client? where does it deploy and why (Vercel/PaaS
vs VPS/IaaS vs managed)?** Then the rigorous
**SDD → BDD → package workflow → regression tests** flow: spec → design+ADR (SDD) → acceptance
Given-When-Then (BDD) → spec challenge → user approval → package planning → package implementation with local
validations → package gates → one deep package review → consolidated repair → delta review → regression tests →
integration → judge → release → memory. Tests do NOT approve implementation; the independent package reviewer
does. This order is mandatory in feature mode; the three lanes below are the only
exceptions (scoped-feature / quick-fix / incident).

### 2. Scoped-feature — the DEFAULT for bounded work on existing code
Triggers: any **well-bounded** change with a clear blast radius on established infrastructure that is too big
or too sensitive for quick-fix — from "a new endpoint + view" up to the canonical sensitive case, "a login view
+ password recovery on Supabase". This is the default lane: most day-to-day requests land here, and the full
SDD ceremony is reserved for the explicit feature-mode triggers above. Running the full panel after every task
and every repair is waste (that is what turned a login into a 4-5h grind).
Flow: SDD-lite (spec + acceptance Given-When-Then; an ADR only if there is a genuinely new architectural
decision) → BDD connection point with the user → one or more coherent packages → package gates → **ONE
consolidated package review over the complete package diff** → `security-auditor` when the package
touches that surface → regression tests → `adversarial-judge` → release → memory.
What is cut: deep review does NOT run after each task or each trivial repair. Security guarantee is preserved by
reviewing the complete relevant package/diff once, then delta-reviewing repairs. Escalate to feature mode only
when one of feature mode's explicit triggers appears (net-new system, multi-package, uncovered architecture
axis) — "this feels big" is a reason to scope the package better, not to escalate.

### 3. Quick-fix — bounded and low-risk
Triggers: a small, well-understood change with an obvious blast radius (copy tweak, one-function bug, config
value). Flow: implement → `gate-runner` verify → done. Skip spec/design/ADR and the full audit panel — UNLESS
real risk surfaces mid-way (touches auth/money/PII/migration), then **escalate to scoped-feature or feature
mode**. MANDATORY at close: record the minimal durable trace with
`python3 ai/scripts/feature-state.py log-quickfix --summary "<what/why>" --result done --file <path> --gate "<gate evidence>"`
— quick-fixes with no trace are how the development thread gets lost.

### 4. Incident / break-glass — production is broken NOW
Triggers: production down or a user blocked with no in-app path, and speed matters more than ceremony (e.g. a
prod user needs a password reset and there is no forgot-password flow → a one-shot `psql` script, done).
Flow: fastest correct + ingenious fix, minimal ceremony, delegate the actual change to `debugger`/`implementer`
(you still never implement yourself). MANDATORY afterward — never skip: (a) write down exactly what was done,
(b) open a follow-up task to do it properly, (c) delegate a memory note. Break-glass is a conscious, logged
exception to the rigor default — not a licence to abandon it.

Ambiguous which mode? Ask. When risk is unclear, bias toward the more rigorous mode.

## Physical budgets per mode (enforced by the state CLI, not by prose)

The mode you choose is not just a flow — it sets hard budgets in the feature state. Pass it to
`feature-state.py init` via `--mode`:

| Mode | `--mode` | Spawns/package | Deep review cycles | Gate failures |
|---|---|---|---|---|
| Feature / SDD | `feature` (opt-in) | 12 | 2 | 3 |
| Scoped-feature | `scoped` (default) | 8 | 2 | 3 |
| Quick-fix | `quick-fix` | 4 | 1 | 2 |
| Incident | `incident` | 6 | 1 | 2 |

Two physical waivers keep light modes light without prose exceptions:
- `record-repair --skip-delta` skips the delta review ONLY when every repaired finding is ≤ medium severity
  and the repair touched ≤ 3 files (the CLI rejects it otherwise, and the waiver is recorded in the event).
- `create-package --runtime-surface false` (planner declaration) lets a package with no observable runtime
  surface become accept-ready after testing, without spawning `app-runner`/`runtime-verifier`. Default is
  `true` — fail-safe.

`record-spawn` blocks the feature when the spawn budget is exhausted. If a quick-fix genuinely needs more
than 4 spawns, that is the signal it was misclassified — re-triage to `scoped`/`feature` (a conscious,
logged decision), do not fight the budget.

## Architecture red-flags (transversal — check in EVERY mode, including quick-fix)
Before delegating in ANY mode, check the request against the three named axes above: **data store type
(including vector vs relational)**, **API Gateway**, and **deploy platform (Vercel/PaaS vs VPS/IaaS)**. If
the request plausibly touches one of these AND no existing ADR already covers it for this project, do not
implement directly — escalate to at least `scoped-feature` with an architecture checkpoint (`architect`
loads `system-design-decisions`, proposes options, and the orchestrator asks the user per its Question
policy) before any code is written. This applies even to a request that looks like a quick-fix on its
surface ("add semantic search to the docs page" is a one-line ask, but it is a data-store decision). A safe
default is NOT an escape hatch for these three axes specifically — see `orchestrator.md`'s Question policy.

## Waking the dormant agents (concrete triggers, not "by risk")
These agents are permitted but easy to forget — pull them in on these triggers:
- **auth / money / PII / any external input** → `security-auditor` is MANDATORY before the judge (its report
  covers the attack path AND the hardening/detection plan in one pass — no separate hand-off agent).
- **any user-facing surface / new UI** → `ux-ui-designer` (brand-grade, accessible; not generic defaults).
- **the approach is genuinely open / multiple viable designs** → `brainstormer` before committing.
- **queries / lists / transactions / migrations** → covered by `package-reviewer`'s own data-integrity/
  scalability checklist (already mandatory, no separate agent).

**Cadence by mode:** in package workflow, specialized reviewers run when the package touches their surface, or
when a repair changes that surface. They do not run after every ordinary task. A final evidence pass before
`adversarial-judge` is mandatory.

## Hard logic → hosted implementer (never the local leaf)
Concurrency, atomic transactions, money/financial rules, and security-critical logic must NOT be implemented by
the local leaf model (the cheap 8B) — a weak first draft on exactly this logic triggers more strong-auditor
rework than it saves. When a task touches these, pin implementation to a **hosted** model (e.g. `openai/gpt-5.4`)
rather than the local `implementer`. Route such implementation deliberately from the package plan. The
local leaf stays for boilerplate/CRUD/UI churn, which the audit panel then reviews.

## Output of triage
State: chosen mode + one-line why, the scoping questions asked (if any), and the first delegation. In
incident mode, also name the follow-up task you will open once the fire is out.
