# ADR-0020 — Direct-read vs. delegated-explore threshold: a file-count rule for the orchestrator's own reading, not a new delegation mechanism

- Estado: Accepted (2026-08-03). **Amended in part by ADR-0064** (Accepted 2026-08-19): write-side
  mode selection is an `init --risk-signal` CLI gate; the number 3 as a
  cross-referenced constant does not change; the read-side table is untouched.
  Adopted after studying `gentle-ai`'s (Gentleman Programming) RDD/SDD
  orchestrator delegation-rules table, contrasted against SET-AGENTES's existing mode-selection doctrine.
  First of five ADRs (0020-0024) tracking the RDD-inspired integration; the other four (integration receipt,
  evidence-based risk escalation, bounded repair ceiling, strict-TDD opt-in) are separate, larger packages not
  yet drafted.

## Contexto

gentle-ai's orchestrator (`internal/assets/claude/sdd-orchestrator.md`) codifies a delegation-rules table:
reading 1-3 known files to decide/verify is done directly; exploring/understanding 4+ files is delegated to a
narrow subagent; writing one mechanical already-understood file is direct; writing 2+ non-trivial files is
delegated. SET-AGENTES's orchestrator already forbids itself from ever writing/editing any file at all (`Hard
boundary`: "Never edit files... Use only read/search, safe Git inspection..."), so gentle-ai's write-side rule
does not transplant literally — SET-AGENTES already has a *stronger* version of it (never, not "only if
small"). What SET-AGENTES lacks is the read-side half: no codified number distinguishes "read this myself to
decide" from "delegate this exploration", leaving it a judgment call not tied to the same number
`request-triage`'s quick-fix trigger already uses on the write side ("a change across 1-3 files"). Codifying
the read side closes that asymmetry without inventing a new mechanism — it restates `Spawn economy`'s existing
"minimal-context" and "agents are for judgement, plumbing is free" rules as a concrete number, in the one
place (reading, before any delegation decision is even made) that rule was previously judgment-only.

## Decisión

1. The orchestrator reads 1-3 already-named files directly, itself, when doing so answers a decide/verify/
   triage question — no subagent spawn for that.
2. Understanding 4 or more files, or files that must first be located/searched for, is delegated to one
   narrowly-briefed exploration subagent (`Explore` or an equivalent single mapper spawn) — never read
   directly by the orchestrator itself, since inflating its own context with raw file content it only needed
   synthesized is exactly the waste `Spawn economy` already names.
3. This governs reading only. Writing of any size remains governed exclusively by the pre-existing `Hard
   boundary` (orchestrator never writes/edits, full stop) and by `request-triage`'s mode selection (quick-fix
   for a well-understood 1-3-file write, scoped-feature/feature for larger or riskier write scope) — this ADR
   adds no new write-side rule, since SET-AGENTES's write-side rule already covers what gentle-ai's table
   describes, at the mode-selection layer instead of a raw file count.
4. `request-triage.md`'s quick-fix trigger and `orchestrator.md`'s new threshold both use the number 3 as one
   deliberate, cross-referenced constant — a future change to one must revisit the other explicitly, rather
   than the two silently drifting apart.

## Rejected alternatives

- **Import gentle-ai's write-side rule as written (orchestrator writes 1 mechanical file directly).** Rejected
  outright: SET-AGENTES's separation-of-duties model never lets the orchestrator write any file, mechanical or
  not — adopting this literally would weaken an existing, stronger invariant for no benefit the user asked
  for.
- **A single unified read+write threshold table, copied verbatim from gentle-ai.** Rejected because it would
  either restate the write-side rule redundantly (already covered by mode selection) or, worse, imply the
  orchestrator could write small files directly, contradicting `Hard boundary`.

## Consecuencias

- Closes a real, previously judgment-only gap (the orchestrator inflating its own context reading files it
  should have delegated) with a concrete number, reusing the same "3" the write side already committed to.
- No schema change, no new CLI verb, no new agent role — pure doctrine text in
  `Global/_canonical/agents/orchestrator.md` and a cross-reference in
  `Global/_canonical/skills/request-triage/SKILL.md`, propagated via `./build.sh --install`.
- Nothing about `PACKAGE_ACCEPTED→INTEGRATION`, receipts, review lenses, repair ceilings, or TDD (the other
  four decisions from the same gentle-ai study) is affected — this ADR covers exactly the routing/delegation
  read-side axis, on its own.
