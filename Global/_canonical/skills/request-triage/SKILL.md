---
name: request-triage
description: Intake + mode selection for the orchestrator — classify an incoming request into an execution mode (consult/analysis, feature/SDD, scoped-feature, quick-fix, or incident/break-glass), ask scoping questions BEFORE starting, and know which normally-dormant agents (security-auditor, brainstormer, ux-ui-designer) to pull in and when. Load at the START of every user request, before delegating anything.
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
2. **Resolvé antes de preguntar (ADR-0037)** applies here too, before any scoping question: check the
   original request, `docs/notas/`, `ai/state/decisions-log.jsonl`, and the approved spec/ADRs — a
   scoping doubt one of those already answers is resolved with `log-decision`, not asked.
3. **Close architecture conventions before code** when the request opens them: audience, data shape
   (including vector vs relational), hosting now vs at scale, API boundary, auth, real-time behavior,
   mobile surface, cost posture, and legal/ToS constraints. This is not a questionnaire ritual: each
   open axis must land as either (a) a resolved convention with source, or (b) an explicit unknown that
   blocks implementation.
4. For category-matching requests, load `solution-baselines` in intake and bring a default + threshold
   before asking. Ask for the user's **bit** (which side of the threshold they are on), not for a raw
   tool choice. Example: "default Postgres, vector only if semantic-search trigger appears."
5. Never invent thresholds or defaults: if no source-backed baseline exists, say "sin default verificado",
   ask the minimum needed question, and record the resolution.
6. If the request is still ambiguous on scope, risk, or intent after that check, ask **1–2 scoping
   questions** — do NOT start. Terse in execution, but interrogate up front. This is where you "stop the
   cart".
7. Only then delegate the first action of the chosen mode.

## The five modes

### 0. Consult / analysis — thinking together, no pipeline (check this FIRST)
Triggers: "qué opinás", "cómo encararías", "analizame esta idea", comparisons, design questions — any request
where the user wants analysis or a recommendation, not a code change. This is a first-class mode, not a
misclassified feature.
Flow: NO `init`, NO state file, NO pipeline. Delegate in parallel (these spawns are allowed and cheap):
- `brainstormer` — 3-6 genuinely different options with tradeoffs,
- `architect` — read-only pass over the three axes (relational vs non-relational vs vector store, API Gateway,
  deploy platform) plus design patterns / clean-architecture shape; NO ADR unless the user asks,
- `security-auditor` — design-level threat sketch, only when the idea touches auth/money/PII/external input.
Then SYNTHESIZE yourself into ONE multi-lens analysis: data model, architecture/patterns, security,
algorithms/complexity — ending with a recommendation plus runner-up. Close by asking: "¿Lo convierto en spec
(feature) o en scoped?". A consult NEVER starts the pipeline on its own; if durable learning surfaced,
delegate a `memory-scribe` note to the domain knowledge.

### 1. Feature / build — full SDD (opt-in; only when the work truly demands it)
Triggers — full SDD is chosen ONLY when at least one of these holds; otherwise drop to scoped-feature (if a
concrete risk signal is present) or quick-fix (the default lane):
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

### 2. Scoped-feature — for bounded work that shows a concrete risk signal
Triggers: a **well-bounded** change on established infrastructure where at least ONE concrete risk signal is
present: money/billing (`money-billing`), data migrations (`data-migration`), auth/permissions/PII
(`auth-pii`), a public contract or shared API (`public-contract`), genuinely multi-module work
(`multi-module`), or the user explicitly asking for the full treatment (`user-asked-full-pipeline`,
"hacelo con el pipeline completo").
The canonical case: "a login view + password recovery on Supabase". Without one of these signals, a bounded
change is a quick-fix, not a scoped-feature — running spec + planner + panel + judge on an ordinary bugfix is
the same waste as running the full panel after every task (that is what turned a login into a 4-5h grind).
Flow: SDD-lite (spec + acceptance Given-When-Then; an ADR only if there is a genuinely new architectural
decision) → BDD connection point with the user → one or more coherent packages → package gates → **ONE
consolidated package review over the complete package diff** → `security-auditor` when the package
touches that surface → regression tests → `adversarial-judge` → release → memory.
What is cut: deep review does NOT run after each task or each trivial repair. Security guarantee is preserved by
reviewing the complete relevant package/diff once, then delta-reviewing repairs. Escalate to feature mode only
when one of feature mode's explicit triggers appears (net-new system, multi-package, uncovered architecture
axis) — "this feels big" is a reason to scope the package better, not to escalate.

### 3. Quick-fix — the DEFAULT for small and medium bounded work
Triggers: any small-or-medium, well-understood change with a clear blast radius — a bugfix, a bounded behavior
tweak, a change across 1-3 files, copy/config, one function or one component. This is the write-side half of
the same 1-3 number `orchestrator.md`'s "Direct-read vs. delegated-explore threshold" (ADR-0020) uses for the
read side — the two are kept as one cross-referenced constant, not two independent numbers. This is the default lane: most
day-to-day requests land here unless a concrete scoped/feature trigger is present. Flow: implement →
`gate-runner` verify → done. Skip spec/design/ADR and the full audit panel — UNLESS the diff itself turns out
to touch a concrete risk signal (auth/money/PII/migration/public contract), then **escalate to scoped-feature
or feature mode**, naming the signal. MANDATORY at close: record the minimal durable trace with
`python3 ai/scripts/feature-state.py log-quickfix --summary "<what/why>" --result done --file <path> --gate "<gate evidence>"`
— quick-fixes with no trace are how the development thread gets lost. Gate red in quick-fix (no package):
retry locally or escalate to scoped/feature with a named `--risk-signal`; salvage does not apply, and the
context pack required of packages (033 AC-6.1) does not apply either — a quick-fix never creates a package.

### 4. Incident / break-glass — production is broken NOW
Triggers: production down or a user blocked with no in-app path, and speed matters more than ceremony (e.g. a
prod user needs a password reset and there is no forgot-password flow → a one-shot `psql` script, done).
Flow: fastest correct + ingenious fix, minimal ceremony, delegate the actual change to `debugger`/`implementer`
(you still never implement yourself). MANDATORY afterward — never skip: (a) write down exactly what was done,
(b) open a follow-up task to do it properly, (c) delegate a memory note. Break-glass is a conscious, logged
exception to the rigor default — not a licence to abandon it.

Ambiguous which mode? Ask. Otherwise pick the LIGHTEST mode that covers the risk actually observed in the
request and the code — not the hypothetical risk. Escalate only when you find a concrete signal from the
lists above, and name that signal in the narration. Downgrading is equally legitimate: if mid-scoped the
planner or implementer establishes the change is smaller than assumed (no signal actually present), degrade
to quick-fix and record why with `log-decision` — escalation is not a one-way ratchet.

## Physical budgets per mode (enforced by the state CLI, not by prose)

The mode you choose is not just a flow — it sets hard budgets in the feature state. Pass it to
`feature-state.py init` via `--mode`. Operational default for a 1-3 file change with no risk signal is
**quick-fix without `init`** (`implement → gate → log-quickfix`). `init --mode scoped` / `feature`
without `--risk-signal TOKEN` dies `RISK_SIGNAL_REQUIRED` and leaves no valid state (unknown token →
`RISK_SIGNAL_INVALID`). The CLI `--mode` default stays `scoped` on purpose: a bare `init` fails closed
instead of silently opening ceremony. Do not treat `scoped` as the default lane for 1-3 files.

| Mode | `--mode` | Spawns/package | Deep review cycles | Gate failures |
|---|---|---|---|---|
| Feature / SDD | `feature` (opt-in) | 12 | 2 | 3 |
| Scoped-feature | `scoped` | 8 | 2 | 3 |
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
(including vector vs relational)**, **API Gateway**, and **deploy platform (Vercel/PaaS vs VPS/IaaS)**. The
check fires on EVIDENCE, not plausibility: the request or the files it names concretely require one of these
axes (a new kind of persistence, a new external entry point, a deploy change) AND no existing ADR covers it.
When it fires, do not implement directly — escalate to at least `scoped-feature` with an architecture
checkpoint (`architect` loads `system-design-decisions`, proposes options, and the orchestrator asks the user
per its Question policy) before any code is written. This applies even to a request that looks like a
quick-fix on its surface ("add semantic search to the docs page" is a one-line ask, but it is a data-store
decision). What it does NOT mean: "could hypothetically touch persistence someday" is not a red flag — an
ordinary bugfix inside existing tables/routes/deploy stays a quick-fix. A safe default is NOT an escape
hatch for these three axes specifically — see `orchestrator.md`'s Question policy.
**Named-platform carve-out (ADR-0025)**: when the request itself names the platform ("deploy this to
Vercel", "store it in Supabase"), that axis is DECIDED — record it with `log-decision` and proceed without
asking; `architect` writes the formal ADR afterwards. The red-flag question is only for an axis the user
left genuinely open.

## Waking the dormant agents (concrete triggers, not "by risk")
These agents are permitted but easy to forget — pull them in on these triggers. The trigger is evidence in
the plan or the diff (the concrete files/paths the package owns: auth/, payments/, migrations/, ui
components, .env-adjacent config), not the topic of the request in the abstract; `package-planner` justifies
each entry in `required_reviewers` with the paths that demand it:
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

The first delegation is announced with the dual-register narration block from `orchestrator.md`
(`Cliente:` / `Ingeniería:`), and so is every delegation after it — in every mode. In consult mode the
parallel fan-out is narrated as ONE logical instance and persisted with `feature-state.py log-narrative`,
since a consult has no feature state file.
