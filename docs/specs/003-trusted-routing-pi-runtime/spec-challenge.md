# Spec challenge — trusted routing-v2

Contract: [spec.md](spec.md) version `2.0.0`.

## Original verdict

**REVISION_REQUIRED.** This was the original verdict. The correction passes below resolved the findings while
preserving the approved intent.

| Finding | Challenge | Contract resolution |
|---|---|---|
| F-01 | Observed facts lacked a complete field/source/absence definition and could be downgraded by caller data. | `spec.md` freezes the authoritative field/source matrix, including `selected_runtime` from same-invocation harness composition, freshness, incomplete/conflict outcome, and additive-only caller constraints. `AC-01a` independently tests every field downgrade. |
| F-02 | Provider/model inventory and authentication evidence were not sufficiently canonical or safe. | Evidence is keyed by `(runtime,provider)` with the four exact P1R adapter pairs, redacted status/exit only, no credential-file reads, and unavailable treatment for nonzero/missing/timeout/ambiguous/absent-model probes and every other pair. Pi simulation has no P1R execution auth adapter. Immutable provider-model-runtime compatibility and authorization identity `(route_id,runtime,provider,model,family,effort)` fail closed on mismatch; `AC-02a` covers negative pairs. |
| F-03 | The static ID could accidentally bind dynamic eligibility or accept a truncation collision. | IDs bind exactly static rows using only `catalog_version`, provider, model, family, effort, sorted tiers/roles/tools, and curated priority. Runtime and dynamic eligibility are excluded; a compatible-runtime change keeps the ID. Any distinct-tuple truncated-ID collision invalidates the entire snapshot. `AC-02a` requires a hash-injection collision fixture. |
| F-04 | Role class, completed-writer semantics, run identity, and authorization boundary were underdefined. | `roles.tsv` duty/capability mapping, terminal selected/fallback writer success, CSPRNG-only `run1_` IDs with no event persistence, and route-then-`authorize` boundary are contractual in `AC-03a`. |
| F-05 | No independent additional finding was supplied. | No new behavior is invented; the original review-identity and family-exclusion concerns remain covered by AC-03/AC-03a and require re-challenge confirmation. |
| F-06 | Fallback could remain eligible after primary external dispatch or crash. | Fallback closes durably at `mark_dispatched`. A pre-dispatch restart may consume it only while durable state is authorized with `fallback_window_open=1`, `partial=false`, and `terminal=false`; any restart after dispatch/start or failed terminal persistence cannot. AC-07/AC-07a test both sides. |
| F-07 | Retention metrics did not define population, rank calculation, clocks, or counters exactly. | The contract requires one transaction UTC clock, exact 90-day deletion, nearest-rank p50/p90 overall/per-route, null empties, insertion-time lifetime counters, and compaction-only `compacted_count`. |
| F-08 | CLI envelope, legacy-state handling, and explain immutability were insufficiently exact. | Schema-2 one-document JSON, stdout/stderr/exit rules, the six named legacy entries plus strict `routing-events-[0-9]+-[0-9]+\.jsonl` children, `lstat` no-follow/no-open/no-read, safe/unsafe warning codes, byte-for-byte explain proof, and a never-emitted one-time `meta.installation_hmac_salt` are now contractual. |
| F-09 | Two existing hermetic test repairs were missing from the delivery work. | T-005 and the plan explicitly require isolated-PATH `test_install_sh_dry_run_plans_missing_tools` and schema-1-compatible/deterministic-schema-2 `test_models_config_emit_roundtrip`, followed by full verification. |

## Platform decision

Persistent routing-v2 is a POSIX-local-filesystem feature requiring Python `sqlite3`, reliable local locking, and Unix
ownership/mode semantics. Windows and unreliable network filesystems return `ROUTING_UNAVAILABLE` without mutation.
Existing non-routing Windows surfaces remain unchanged.

## Final re-challenge result

**PROCEED.** F-01 through F-09 and the second five-point re-challenge (selected runtime, per-pair authentication,
dispatch identity persistence, restart boundary, and exact legacy universe) are closed. No blocker or high-severity
issue remains in the product/BDD contract. The contract is approved on `2026-07-24` from the user's original explicit
instruction to implement the supplied P1R plan, after the corrections preserved intent.
