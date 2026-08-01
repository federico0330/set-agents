# P1-discovered-inventory — repair evidence (panel RP-01)

Package: `P1-discovered-inventory` (feature `012-discovered-inventory`). Consolidated repair of the
14 findings from review panel RP-01 (`package-reviewer` + `security-auditor`, both read-only, clean
context). `PACKAGE_REPAIR` instance. Acceptance criteria AC-01..AC-12 are unchanged; no design was
reopened — every finding below is an implementation fix, a test fix, or a documentation correction.

## SEC-001 (critical) — repaired

**Finding**: `_check_family_collisions` (`catalog.py`) indexed `seen` by the raw `model` string, so
the SAME underlying model curated under two DIFFERENT ids across providers (e.g. `anthropic`/`opus`
and a future `opencode-zen`/`claude-opus-4-8` row — proven identical in-repo by `PI_MODEL_MAP`) would
never collide, letting a reviewer clear both `REVIEW_FAMILY_CONFLICT` and `REVIEW_PROVIDER_CONFLICT`
while reviewing itself under a different provider name.

**Fix, two layers as requested**:
1. `catalog.py`: added `CANONICAL_MODEL` (curated `(provider, model) -> canonical id` map, seeded from
   `PI_MODEL_MAP`) and `canonical_model(provider, model)`. `_check_family_collisions` now keys `seen` on
   `canonical_model(row["provider"], model)` when a `provider` key is present (falls back to the raw
   model id when absent, so the pre-existing pure-function unit assertions in
   `test_ac07_family_collision_rule_is_pure_and_wired_into_build_snapshot` — lines that were explicitly
   marked "do not touch" — keep passing unmodified). `build_snapshot`'s call site now passes `provider`
   alongside `model`/`family`.
2. `service.py`: added a third hard exclusion, `REVIEW_MODEL_CONFLICT`, between `REVIEW_FAMILY_CONFLICT`
   and `REVIEW_PROVIDER_CONFLICT`, comparing `canonical_model(route.provider, route.model)` against
   `canonical_model(writer.provider, writer.model)`. This is the layer that actually closes the hole if
   the catalog-time guard is ever bypassed (stale snapshot, a future code path that skips
   `build_snapshot`, or a curator mistake layer 1 does not anticipate).

**`service.py` was not in this package's `owned_paths`.** Touching it was necessary to implement the
requested defense-in-depth layer; this is flagged as an **exception requiring orchestrator approval**
(`update-package --exception`), not self-approved. The change is minimal and additive: one new `import`
name (`canonical_model`) and one new `elif` branch plus its comment; no existing line was rewritten.

**Verification**: new test `test_sec001_cross_provider_alias_cannot_satisfy_reviewer_independence`
(`tests/test_routing.py`) — exact fixture the panel specified (writer=`anthropic`/`opus`,
reviewer=`opencode-zen`/`claude-opus-4-8`):
- Layer 1: `build_snapshot` over the two-row alias catalog (with `enabled_providers` extended in an
  **in-memory copy** of config only, never written to disk, never touching `ROUTING_PROVIDERS`, to
  isolate the family check from the separate, correctly-closed AC-05 gate) raises
  `RoutingError("CATALOG_FAMILY_COLLISION")`.
- Layer 2: a hand-built `CatalogSnapshot` containing both routes (bypassing `build_snapshot` entirely,
  to prove layer 2 works independently of layer 1) is fed to `RoutingService._for_tests`; a real writer
  authorization + `close_run("success")` + reviewer `route(..., review_of_run_id=...)` call asserts
  `execution_enabled is False`, `reason_codes == ("REVIEWER_INDEPENDENCE_UNAVAILABLE",)`,
  `independence_verified is False`, and `{"route_id": reviewer_route.route_id, "reason":
  "REVIEW_MODEL_CONFLICT"}` present in `exclusions` — the exact assertions the panel specified.
- The pre-existing test at `tests/test_routing.py` (the `minimax-m2.7` exact-id pure-function
  assertions, ~2666-2681) was **not modified**, per the panel's explicit instruction.

## F-01 (high) — repaired

**Finding**: the AC-07 colliding fixture (`roles=["implementer"]`) let `build_snapshot`'s
roster-coverage check raise `CATALOG_INVALID` on its own, masking whether
`_check_family_collisions` itself still worked.

**Fix**: both rows in the colliding fixture now use full roster coverage
(`sorted({row["role"] for row in self.roster})`), and the assertion is
`assertRaisesRegex(routing.RoutingError, "CATALOG_FAMILY_COLLISION")` (tied to the SEC-001 reason-code
differentiation, F-12).

**Verification**: manually monkeypatched `cat._check_family_collisions = lambda rows: None` and reran
`test_ac07_family_collision_rule_is_pure_and_wired_into_build_snapshot` in isolation — the fixture now
correctly **fails** (`RoutingError not raised`), proving the neutering is caught. Restored before the
real run; the test passes unmodified against the real, wired-in check.

## F-02 (high) — repaired

**Finding**: `assertTrue(probed_models <= ceiling)` in the P2 local live-parity gate passes trivially
with an empty `probed_models`, exactly the failure mode the gate exists to catch.

**Fix**: `assertTrue(ceiling, ...)` (non-empty) + `assertEqual(probed_models, ceiling, ...)` for both
providers in `test_ac10_p2_local_live_parity_gate`.

**Verification**: ran the test live on this machine (credentials present) — still `ok`, confirming
`probed == ceiling` holds in practice as the finding predicted (60/16).

## F-03 (medium) — repaired

**Finding**: the "lockstep across the three sites" test exercised sites 1/2 only; site 3
(`build_snapshot`'s own `configured_models` comprehension) is load-bearing but untested.

**Fix**: new test `test_ac04_site3_configured_models_comprehension_is_load_bearing`. `enabled_providers`
is extended in an **in-memory copy** of config (never written to disk, `ROUTING_PROVIDERS` untouched) so
a single fully-roster-covered `opencode-zen` row reaches `build_snapshot` far enough to prove site 3
alone determines whether it's accepted.

**Verification (mutation, exactly as the finding's own reproduction steps)**: temporarily reverted site
3's provider tuple to `("openai-codex", "anthropic")` via `sed`, reran the new test in isolation — it
correctly **errors** (`RoutingError: CATALOG_INVALID`), then reverted the mutation and reran — `ok`.

## F-04 (medium) — repaired

**Finding**: comments (`catalog.py:108-113,417-423`) and the ADR say "three sites"; this package added
two more in `models_config.py` (`load_config`'s optional-key validation, `emit`'s preservation loop),
making five.

**Fix**:
- `catalog.py`: both comments (`_configured_models`'s docstring-comment and `build_snapshot`'s inline
  comment) rewritten to enumerate all five sites by symbol: (1) `models.toml`'s `[catalog]` table, (2)
  `_configured_models`'s key map, (3) `build_snapshot`'s `configured_models` comprehension, (4)
  `models_config.load_config`'s optional-key validation loop, (5) `models_config.emit`'s preservation
  loop.
- `docs/adr/0016-discovered-inventory.md`, decision 3: rewritten from "three independent sites" to
  "five independent sites", with the same by-symbol enumeration and a note flagging the correction.
- New coherence test `test_ac04_opencode_lane_providers_are_coherent_across_every_hardcoded_map`: a
  single declared `{"opencode-zen", "opencode-go"}` set is checked for presence in
  `_OPENCODE_PROVIDER_KEYS`, `_OPENCODE_CLI_IDS`, `PROVIDER_BILLING_KIND`, `_PAIR_COMMANDS`, and (via a
  real `load_config(emit(...))` round trip) `models_config.py`'s sites 4/5.

## F-05 (medium) — repaired (preferred fix: derive, not test-only)

**Finding**: `_PAIR_COMMANDS` hardcoded the opencode-lane CLI id in its argv instead of deriving it from
`_OPENCODE_CLI_IDS`.

**Fix**: `_OPENCODE_CLI_IDS` is now defined *before* `_PAIR_COMMANDS`, and the opencode entries of
`_PAIR_COMMANDS` are built with a dict comprehension over `_OPENCODE_CLI_IDS.items()` — the argv is
derived, never a second hand-typed copy. The same coherence test added for F-04 also asserts the
registered argv for each opencode-lane provider equals what deriving it from `_OPENCODE_CLI_IDS` would
produce, so a future regression back to a hardcoded literal is caught even if someone reverts the
derivation.

**Verification**: `test_ac01_new_pairs_are_registered_in_the_closed_pair_table_only` (pre-existing,
unmodified) still asserts the exact same argv tuples and passes — the derivation is behavior-preserving.

## F-06 (medium) — repaired (mitigation b, as preferred by the orchestrator)

**Finding**: `_probe_pairs` always ran both opencode-lane commands (`auth list` then `models <id>`)
before checking credentials, paying the second command's latency even when the credential was absent
(measured +69%/+10.5s for the two new pairs on a machine without those credentials).

**Fix**: `_probe_pairs` now special-cases `runtime == "opencode"`: it runs `auth list` (memoized via the
new `_run_cached` helper), parses credentials, and `continue`s immediately if the provider's credential
key is absent — the `models <id>` command is **never invoked** for that pair. `models.toml` was not
touched (mitigation (a), not versioning the allowlists, was explicitly not preferred).

**Verification**: new test `test_ac06_f06_credential_check_precedes_the_expensive_models_call` — a
credential set missing `"OpenCode Zen"` but including `"OpenCode Go"`; asserts
`("opencode", "models", "opencode", "--pure")` is never in the recorded call list while
`("opencode", "models", "opencode-go", "--pure")` is. Full suite reruns confirm no other test depended
on the old "always run both commands" ordering.

## F-07 (medium) — repaired

**Finding**: `models.toml:18-19` and `catalog.py:417` cite "AC-11 non-goal" — AC-11 is the cache/trace
AC, not the (unnumbered) non-goals paragraph that actually says "no curated `routes.v1.toml` rows for
the new models." AC-11's real content (cache key covers the new allowlists; negatives not persisted for
the two new pairs) was unverified by any test.

**Fix**:
- Citations corrected in `models.toml` (comment above `opencode_zen`/`opencode_go`), `catalog.py`
  (`build_snapshot`'s site-3 comment), and `docs/specs/012-discovered-inventory/evidence/
  P1-implementation.md` (the "Not touched" line) — all now point to "contract 012's non-goals
  paragraph", explicitly not AC-11.
- New test `test_ac11_cache_key_covers_the_new_allowlists_and_negatives_stay_unpersisted`: asserts
  `_cache_key` changes when the two new `[catalog]` keys are removed or narrowed, and that a probe run
  where the zen credential is absent and the go models-call fails leaves **neither**
  `"opencode|opencode-zen"` nor `"opencode|opencode-go"` in the persisted `probe-cache.json`.

## F-08 (low) — repaired

**Finding**: `docs/adr/0016-discovered-inventory.md:3` said `Estado: Accepted` before the package was
accepted.

**Fix**: changed to `Estado: Proposed`, matching `0015-quota-failover.md`'s convention for a
not-yet-accepted feature. `docs/adr/README.md`'s row for 0016 updated to `Proposed` too.

## F-09 (low) — investigated, **not applied as literally requested** (see below)

**Finding**: the diff to `docs/adr/README.md` filled rows 0009-0016; AC-12 only asks for the 0016 row.

**What I found**: reverting rows 0009-0015 (leaving only 0016) makes
`tests/test_harness.py::HarnessTests::test_every_adr_on_disk_has_a_row_in_the_index` **fail** — that
test (pre-existing, unrelated to this package, already in the suite) asserts every `NNNN-*.md` file
under `docs/adr/` has a row in the index, and ADR files 0009-0015 already exist on disk (some committed
at `HEAD`, e.g. `0009-finding-verification.md`; others uncommitted work from other in-flight features,
e.g. `0010`-`0015`). This is exactly the case the orchestrator's own instruction anticipated: "si alguna
de esas 7 correcciones es genuinamente necesaria y no solo cosmética, dejala pero decilo explícito."

**What I did**: restored rows 0009-0015 exactly as the implementer left them (verified against
`git diff HEAD -- docs/adr/README.md` before my edit) and only changed the 0016 row's `Status` cell
(`Accepted` → `Proposed`, same as F-08). The 7-row addition is a genuine regression-test requirement,
not cosmetic scope creep — flagging this explicitly as requested rather than silently leaving it either
way.

## F-10 (low) — repaired

**Finding**: the AC-09 test never exercised `service.py`'s revalidation comparison
(`recomputed != selected.route_id or not fresh.identity_allowed(identity)`), which AC-09 names
explicitly as its second half.

**Fix**: added an assertion to the existing coverage via a new dedicated test,
`test_ac09_service_revalidation_recomputes_the_identical_identifier` — a real writer authorization
(which runs `service.py`'s exact recompute line on every call, not a re-implementation) is compared
against an independently-computed `StaticRoute.identifier(...)` using the SAME inputs, proving the
mechanism this AC's synthetic assertions cover in isolation is also the live mechanism a real
authorization exercises.

## F-11 (low) — repaired

**Finding**: `evidence/P1-implementation.md:62,81-82` claimed `emit(load_config(...))` round-trips
"byte-for-byte" — false; `emit` is a normalizing emitter (drops standalone comments, re-sorts lists).

**Fix**: both passages rewritten. Measured directly:
`emit(load_config("models.toml")) == Path("models.toml").read_text()` is `False`. The corrected claim:
the two new `[catalog]` keys and their full member sets survive a load→emit→load cycle unchanged (which
is what AC-04 actually requires and is what was actually verified), and this pre-existing
non-byte-identical emitter behavior is unrelated to this package.

## F-12 (low) — repaired (folded into the SEC-001 fix, as suggested)

**Finding**: `_check_family_collisions` raised a generic `RoutingError("CATALOG_INVALID")`,
indistinguishable from any other `build_snapshot` failure.

**Fix**: now raises `RoutingError("CATALOG_FAMILY_COLLISION")` — following the SAME differentiation
pattern the file already uses (`CATALOG_INVALID` vs `CATALOG_COLLISION` for the id-collision case,
`catalog.py`'s per-row loop), not a new, unrelated vocabulary. No RoutingService-level `reason_codes`
vocabulary is touched — this is a `build_snapshot`-internal `RoutingError` message, the same kind of
string `CATALOG_COLLISION` already is.

## F-13 (low) — repaired

**Finding**: the ADR didn't name `consume_fallback`, the terminal-state `CHECK`, or the relationship
with `011`, which AC-12 asks for by symbol.

**Fix**: added a paragraph to the ADR's "Accepted residual risk" section naming
`RoutingStore.consume_fallback` (by symbol, per the spec's own instruction to cite symbols rather than
line numbers for files with uncommitted `011` changes), the `dispatches` table's terminal-state `CHECK`
constraint (quoted verbatim), and the relationship: neither symbol is touched by this feature, but
`011`'s quota-failover linked dispatch is the first consumer that would let a probed-but-uncurated
OpenCode-lane pair reach `consume_fallback` once AC-05's gates are separately opened, and the accepted
residual risk applies identically there.

## Tests run

- Targeted: all 7 new/modified test methods run in isolation — all `ok`.
- Mutation verification for F-01 and F-03: performed and reverted (see above), confirming both fixtures
  now discriminate the exact regression they exist to catch.
- `PYTHONPATH=ai/scripts python3 -m unittest tests.test_routing.RoutingTests` (134 tests) — `OK`.
- `PYTHONPATH=ai/scripts python3 -m unittest discover -s tests` — **488 tests, OK** (482 baseline + 6 net
  new test methods: `test_sec001_...`, `test_ac04_site3_...`, `test_ac04_opencode_lane_providers_...`,
  `test_ac06_f06_...`, `test_ac09_service_revalidation_...`, `test_ac11_cache_key_...`; F-01/F-02 modified
  existing tests in place, no new method). No test was skipped beyond the one pre-existing named
  exemption (AC-10's live-parity gate, which ran live here). No existing test weakened or deleted.
- `./ai/scripts/verify.sh` → `VERIFY_PASS` (full log ends `GLOBAL_PORTABILITY_OK` /
  `CANONICAL_PATHS_OK` / `FEATURE_STATE_OK` / `VERIFY_PASS`).
- `git diff --check` on every touched file → exit 0, no whitespace errors.

## Ownership exception (requires orchestrator approval)

`ai/scripts/routing_core/service.py` was **not** in `P1-discovered-inventory`'s `owned_paths`. It was
touched to implement SEC-001's requested defense-in-depth layer (`REVIEW_MODEL_CONFLICT`), which cannot
be done anywhere else — it is the module that actually makes the review/writer selection decision. This
is flagged here explicitly, per the orchestrator's own instruction, for approval via
`feature-state.py update-package --exception`; it was not self-approved. `python3
ai/scripts/check-owned-paths.py` confirms this is the **only** out-of-scope file in this repair's diff
(`"out_of_scope": ["ai/scripts/routing_core/service.py"]`, `"read_only_violations": []`).

## Changed files

- `ai/scripts/routing_core/catalog.py` (owned) — SEC-001 layer 1, F-04, F-05, F-06, F-07, F-12
- `ai/scripts/routing_core/service.py` (exception, see above) — SEC-001 layer 2
- `models.toml` (owned, approved exception on record from the implementation phase) — F-07
- `docs/adr/0016-discovered-inventory.md` (owned) — F-04, F-08, F-13, SEC-001 note
- `docs/adr/README.md` (owned) — F-08, F-09 (investigated, not applied as literally requested — see above)
- `tests/test_routing.py` (shared) — SEC-001, F-01, F-02, F-03, F-04, F-05 (coherence assertion), F-06,
  F-10, F-11 (none — evidence file only)
- `docs/specs/012-discovered-inventory/evidence/P1-implementation.md` (owned) — F-07, F-11
- `docs/specs/012-discovered-inventory/evidence/P1-repair.md` (owned, this file) — new

## Not touched

`ai/scripts/models_config.py` — no finding required a code change there (F-04's fix was comments +
tests only; sites 4/5 were already correctly implemented by the implementer, only undercounted in
comments). `ai/catalogs/routes.v1.toml`, `models_config.ROUTING_PROVIDERS`,
`[routing].enabled_providers` — unchanged, consistent with AC-05's non-goal (still verified by
`test_ac05_new_providers_are_probeable_not_routable_today`, unmodified).

## Remaining findings

None open. All 14 findings (1 critical, 2 high, 4 medium, 7 low) addressed above: repaired (12),
investigated with the requested transparency and a documented reason for the deviation (F-09).

## Blockers

None outstanding for this repair pass. One item needs orchestrator action before `PACKAGE_ACCEPTED`:
approve or reject the `service.py` ownership exception above.

---

# Ronda 2 (delta-review, 3 findings)

A clean-context `delta-reviewer` re-reviewed round 1's repair and confirmed all 14 original findings
closed by mutation, but opened 3 new/reopened findings scoped to round 1's own changes. This section is
that second bounded repair pass. No file outside the round-1 scope (`ai/scripts/routing_core/catalog.py`,
`ai/scripts/routing_core/service.py` — already an approved exception, `docs/adr/0016-discovered-inventory.md`,
`tests/test_routing.py`) was touched. `models.toml`, `models_config.py`, `docs/adr/README.md`, and
`docs/specs/012-discovered-inventory/spec.md` were not touched, as instructed.

## SEC-002 (medium) — repaired

**Finding**: SEC-001's `CANONICAL_MODEL` was seeded ONLY from `PI_MODEL_MAP["anthropic"]`
(`{opus, sonnet, haiku}`), which does not include `fable` — the fourth id `models.toml`'s
`[catalog].claude` allowlist curates. `[catalog].opencode_zen` curates the same underlying model under
the alias `claude-fable-5`. Before the fix: `canonical_model("anthropic","fable")` returned `"fable"`
(unchanged, identity fallback) while `canonical_model("opencode-zen","claude-fable-5")` returned
`"claude-fable-5"` — different keys, so `build_snapshot` accepted the alias pair as a real catalog and
`service.py`'s route-decide gave `independence_verified=True`, `reason_codes=()` for a reviewer/writer
pair that are actually the same underlying model. Exact re-run of the SEC-001 PoC with `fable`
substituted for `opus` reproduced this live (`/var/tmp/.../scratchpad/dr_fable.py`, run before the fix:
`LAYER 1: build_snapshot ACCEPTED the fable alias catalog`; `LAYER 2 ... independence_verified = True |
reason_codes = ()`).

**Fix**: `catalog.py` — added `_ANTHROPIC_CANONICAL_EXTRA = {"fable": "claude-fable-5"}`, an explicit,
hand-curated pair completing what `PI_MODEL_MAP` (a CLI name-translation table for Pi's own invocation,
never itself a security curation) does not cover. `CANONICAL_MODEL` is now seeded from
`_ANTHROPIC_CANONICAL = {**PI_MODEL_MAP["anthropic"], **_ANTHROPIC_CANONICAL_EXTRA}` instead of
`PI_MODEL_MAP["anthropic"]` directly, so `PI_MODEL_MAP` is no longer the sole source of this security
guarantee — future Anthropic ids needing a curated alias but no Pi translation go in
`_ANTHROPIC_CANONICAL_EXTRA` directly.

**Verification**:
- `/var/tmp/.../scratchpad/dr_fable.py` re-run after the fix: Layer 1 now raises
  `CATALOG_FAMILY_COLLISION`; Layer 2 now gives `independence_verified = False`,
  `reason_codes = ('REVIEWER_INDEPENDENCE_UNAVAILABLE',)`, with `REVIEW_MODEL_CONFLICT` present in
  `exclusions` alongside `REVIEW_FAMILY_CONFLICT` — matching SEC-001's own closure shape exactly.
- New test `test_sec002_every_curated_anthropic_id_resolves_to_a_zen_curated_canonical_id`
  (`tests/test_routing.py`): the requested generalized coherence check — asserts every id in
  `[catalog].claude` resolves through `canonical_model` to a canonical id actually present in
  `[catalog].opencode_zen`, plus a direct by-name assertion for `fable` (the exact id the panel's PoC
  exploited), so a future fifth uncurated Anthropic id fails this test instead of needing a fourth
  auditor to find it.
- `test_sec001_cross_provider_alias_cannot_satisfy_reviewer_independence` (round 1's test, unmodified)
  still passes — the `opus`/`claude-opus-4-8` pair is unaffected.

## F-10 (low, reopened) — repaired

**Finding**: round 1's `test_ac09_service_revalidation_recomputes_the_identical_identifier` only proves
`StaticRoute.identifier` is deterministic (recomputing it twice with the same inputs and comparing) — it
never exercises `service.py`'s actual comparison branch (`if recomputed != selected.route_id or not
fresh.identity_allowed(identity) ...`, `service.py:193`). Confirmed by mutation
(`/var/tmp/.../scratchpad/dr_f10.py`, and independently reproduced here): replacing the guard's left
operand with the constant `False` (`if False or not fresh.identity_allowed(identity) ...`) leaves the
entire `RoutingTests` class green, the F-10 test included, because a normally-selected route's
`route_id` always already matches its own canonical fields whether or not the comparison actually ran.

**Fix**: added `test_f10_service_revalidation_rejects_a_route_id_that_does_not_match_its_own_fields` —
builds a hand-crafted `CatalogSnapshot` with a single `StaticRoute` whose `route_id` is a deliberately
wrong constant (`"deadbeef"*4`, never `StaticRoute.identifier(...)` of the row's own fields), with that
same wrong id present in `identities` (so `identity_allowed` alone would pass and isolate the recompute
comparison specifically). A real, non-simulate, writer-role authorization against this snapshot must be
rejected with exactly `("AUTHORIZATION_INVALID",)`, `run_id is None`, and no open run recorded. The
pre-existing `test_ac09_...` test is kept (still a valid, if weaker, positive-path assertion), not
replaced or weakened.

**Verification (mutation, live)**: temporarily replaced `service.py:193`'s
`recomputed != selected.route_id` with `False` — new test **fails**
(`AssertionError: True is not false`, `decision.execution_enabled` was `True`) while the old
`test_ac09_...` test still passes `ok` unchanged, exactly confirming the delta-reviewer's diagnosis.
Reverted the mutation (`git diff` on `service.py` afterward showed byte-identical to the pre-mutation
state, only the pre-existing round-1 SEC-001 diff against `HEAD` remains); reran both tests — both `ok`.

## N-02 (low) — repaired

**Finding**: the ADR (`docs/adr/0016-discovered-inventory.md`) was left self-contradictory after round
1's partial F-04/SEC-001 fixes: decision 4 (line ~60) and Consecuencias (line ~176) still said
"three-site"/"three sites" after decision 3 was corrected to "five sites"; the "Accepted residual risk"
section (line ~139) still claimed AC-07's collision rule "keys on **exact** model-id equality", false
after SEC-001 (it keys on `canonical_model(provider, model)`).

**Fix**:
- Decision 4: "the three-site `[catalog]` allowlist ceiling" → "the five-site `[catalog]` allowlist
  ceiling".
- Consecuencias: "the three-site allowlist (decision 3)" → "the five-site allowlist (decision 3)".
- Decision 3's own historical note (line 42) reworded from `undercounted "three sites"` to
  `undercounted the site total by two` — the literal string `"three sites"` inside quotation marks was
  itself still a hit for the requested `grep`, even though it was accurately describing the historical
  mistake being corrected; reworded to preserve the same meaning without the literal string.
- "Accepted residual risk": first sentence rewritten to `AC-07's collision rule keys on
  \`canonical_model(provider, model)\` — exact equality after curated normalization, not raw model-id
  equality (post-SEC-001/SEC-002; see decision 5's repair note).` A new paragraph, **"SEC-002
  (delta-review round 2, medium, closed)"**, was added to the same section: explains the `fable` gap
  round 1 left, that it is now closed by explicit curation plus the coherence test, and that it remains
  the same kind of standing curator obligation the pre-existing `mimo-v2.5` residual-risk example
  already names (a future Anthropic id or a first non-Anthropic cross-lane alias still needs a human to
  curate the pair).

**Verification**: `grep -n "three-site\|three sites" docs/adr/0016-discovered-inventory.md` → **empty**
(exit 1, no matches). `grep -n "five sites\|five-site"` confirms the three corrected sites are present.
`docs/specs/012-discovered-inventory/spec.md` was not touched (confirmed via `git status --porcelain`
before and after this pass — the file is untracked/unmodified by this repair either way).

## Tests run (Ronda 2)

- `PYTHONPATH=ai/scripts python3 -m unittest tests.test_routing -v` — **136 tests, OK** (134 baseline +
  2 new: `test_sec002_every_curated_anthropic_id_resolves_to_a_zen_curated_canonical_id`,
  `test_f10_service_revalidation_rejects_a_route_id_that_does_not_match_its_own_fields`).
- Mutation verification, both new tests, performed live and reverted (see SEC-002 and F-10 sections
  above).
- `./ai/scripts/verify.sh` → **VERIFY_PASS**, full suite **490 tests, OK** (488 round-1 baseline + 2 net
  new methods this round). No test skipped, weakened, or deleted.
- Both delta-reviewer PoC scripts (`/var/tmp/claude/claude-1000/-home-federico/
  43dc2166-f747-499d-bb44-b977839e26f7/scratchpad/dr_fable.py`,
  `.../scratchpad/dr_f10.py`) re-run after the fixes, output included above per finding.

## Changed files (Ronda 2)

- `ai/scripts/routing_core/catalog.py` (owned) — SEC-002 (`_ANTHROPIC_CANONICAL_EXTRA`,
  `_ANTHROPIC_CANONICAL`, `CANONICAL_MODEL` reseeded).
- `ai/scripts/routing_core/service.py` — **not touched this round** (SEC-002 is fully closed by the
  layer-1 `canonical_model` fix in `catalog.py`; layer 2's `REVIEW_MODEL_CONFLICT` comparison, added in
  round 1, automatically covers the new alias once `canonical_model` resolves it — no new code needed
  there).
- `docs/adr/0016-discovered-inventory.md` (owned) — N-02 (three corrected passages + new SEC-002
  residual-risk paragraph).
- `tests/test_routing.py` (shared) — SEC-002 (new coherence test), F-10 (new discriminating test).

## Remaining findings

None open from this round's 3 findings. All 17 total findings across both repair rounds (1 critical, 2
high, 5 medium, 9 low) are now closed by mutation-verified fixes or documented, transparent deviation
(F-09, round 1).

## Blockers

None. The `service.py` ownership exception from round 1 still stands unchanged (not touched this round)
and still needs orchestrator approval before `PACKAGE_ACCEPTED`, per round 1's note above.
