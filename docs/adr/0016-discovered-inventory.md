# ADR-0016 — Discovered inventory: two providers, two maps, four gates, one collision rule

- Estado: Accepted (2026-07-31). Feature `012-discovered-inventory`, contract 1.0.0 (three
  spec-challenge rounds, `ready_for_user_approval`; originally drafted as `008-dynamic-selection`'s
  `## P2` section, split out per `ai/state/decisions-log.jsonl` slug
  `p2-discovered-inventory-pasa-a-ser-su-propia-feature-012`).
- Context: `ai/scripts/routing_core/catalog.py`, `models.toml` (`[catalog]`/`[routing]`),
  `ai/scripts/models_config.py` (`ROUTING_PROVIDERS`).

## Contexto

`routing_core`'s probed universe (`_PAIR_COMMANDS`) audited two OpenCode-lane providers,
`openai-codex` and `anthropic`, while the OpenCode CLI already authenticates and lists models for two
more: `opencode-zen` (60 model ids) and `opencode-go` (16 model ids), verified live in this
environment (`opencode auth list --pure`, `opencode models {opencode,opencode-go} --pure`, no shell
pipe). `models.toml`'s own hand-typed `zen` lane already uses Zen names; the `go-zen` lane has never
used a real `opencode-go/…` id. Nothing in `routing_core` could audit, revalidate, or offer either
lane before this feature — not because the providers are unavailable, but because the probed universe
stopped one provider short of what is actually authenticated where the harness runs. This is
availability-only work: no route becomes selectable by this feature alone.

## Decisión

1. **Extend, never replace, the closed pair table.** `_PAIR_COMMANDS` gains exactly two entries,
   `("opencode", "opencode-zen")` and `("opencode", "opencode-go")`. No other runtime gains a pair for
   either provider; `codex`, `claude-code`, and `pi` have no client for them.

2. **Two independently addressable maps for OpenCode's credential/model translation, not one.**
   `_probe_pairs` needs two different strings per provider: the credential display text
   `_parse_opencode_auth` reports (used only at the credential-set membership check) and the CLI
   argument/model-id-prefix `opencode models <id>` actually accepts (used to build the probe argv and
   as the prefix `_parse_opencode_models` strips). For the two pre-existing providers these values
   happen to coincide (`"openai"` serves both roles). They do not for the two new ones: the credential
   display text is the two-token `"opencode zen"` / `"opencode go"`, while the CLI id is the
   single-token `"opencode"` / `"opencode-go"`. `_OPENCODE_PROVIDER_KEYS` (extended, not replaced) holds
   the credential-display side; a new map, `_OPENCODE_CLI_IDS`, holds the CLI-id side. Using the
   CLI-id value at the credential-membership check would search the two-token display-name set for a
   single-token string and report the pair permanently absent, authenticated or not — a stronger defect
   than "fails closed on drift": it would never work on any machine.

3. **A declared allowlist ceiling that must move in lockstep across five sites.** (Corrected post-review,
   panel RP-01, F-04: the original decision undercounted the site total by two — this package's own
   `models_config.py` changes added two more that the same lockstep discipline already required.) Model
   membership for OpenCode-lane pairs is always the intersection with a curated `models.toml` list, never
   the CLI's own report, so a runtime can never widen the audited model set. This is enforced by five
   independent sites that must be extended together: (a) `models.toml`'s `[catalog]` table gains
   `opencode_zen`/`opencode_go`, each the full live-verified roster (60/16 bare model ids, no provider
   prefix, same convention as `claude`/`codex`); (b) `_configured_models`'s provider-to-TOML-key map; (c)
   `build_snapshot`'s own `configured_models` comprehension; (d) `models_config.load_config`'s
   optional-key validation loop for the same two TOML keys; (e) `models_config.emit`'s preservation loop
   for the same two keys. Extending only the TOML without (b)/(c) leaves the new allowlists unreachable
   from code — `_configured_models` would return an empty set regardless of what the TOML says, and every
   new pair would be silently skipped on every probe. Extending (a)-(c) without (d)/(e) leaves the
   allowlists reachable but silently unpersisted — `[catalog]` has no closed-schema check the way
   `[routing]`/`[permissions]` do, so an allowlist key absent from both `models_config.py` sites is read
   fine today but never survives the next `./setup-models.sh` re-emit (a latent data-loss gap this
   package closed at the same site AC-04 already required touching, not separately scoped work).

4. **Four independent selectability gates, not three — none of them opened by this feature.** A probed
   pair must clear: (1) `_PAIR_COMMANDS`; (2) the five-site `[catalog]` allowlist ceiling; (3)
   `models.toml`'s `[routing].enabled_providers`; and (4) `models_config.ROUTING_PROVIDERS`, a closed set
   enforced as a hard allowlist at config-validation time. Gate (4) is the one this feature's own
   spec-challenge found missing from an earlier draft: adding a provider to `enabled_providers` without
   first extending `ROUTING_PROVIDERS` does not merely leave it unreachable — `models.toml` fails to
   load entirely (`die("models.toml: invalid [routing] values")`), taking down every harness command,
   not just routing. This feature touches none of the four gates: `enabled_providers` and
   `ROUTING_PROVIDERS` are unchanged, and no `routes.v1.toml` row exists for either new provider. The two
   new providers become **probeable**, never **routable**, by this feature alone.

5. **`family` stays fully curated, with a cross-provider normalization rule for shared model ids.**
   `family` is set by hand, exactly like `roles`/`tools`/`tier`/`curated_priority` — never captured from
   the probe. For any model id curated under more than one provider, every curated row for that id must
   carry the identical, curator-normalized `family` value, even where the vendor's own taxonomy names it
   differently. This is enforced by a pure function, `_check_family_collisions`, run inside
   `build_snapshot` over the fully-parsed row set (`model`, `family`) before a snapshot is returned, and
   independently unit-testable with synthetic fixture rows without any probe, `--verbose`, or curated
   `routes.v1.toml` row for the new providers. It exists because `service.py`'s reviewer-independence
   checks — `REVIEW_FAMILY_CONFLICT` and `REVIEW_PROVIDER_CONFLICT`, checked together as the pair they
   are — read `family` as a security-relevant signal: the same underlying model, offered under two
   provider names with two different curated families, would let a reviewer clear both checks while
   reviewing itself. 11 model ids are offered by both `opencode` and `opencode-go`; the vendor's own
   `family` string agrees for 9 of them and diverges for 2 (`minimax-m2.7`: `"minimax"` under `opencode`
   vs `"minimax-m2.7"` under `opencode-go`; `minimax-m3` diverges the same way) — measured live with
   `opencode models <id> --verbose --pure`. This is why the rule normalizes rather than requires a
   literal vendor match.

   **Repair (panel RP-01, security-auditor, SEC-001, critical, closed post-review, still `Proposed`).**
   The rule above keyed collisions on the raw curated `model` string, which only catches the SAME id
   curated twice — it is blind to the SAME underlying model curated under two DIFFERENT ids across
   providers (e.g. `anthropic`/`opus` and a future `opencode-zen`/`claude-opus-4-8` row: proven identical
   in-repo by `PI_MODEL_MAP`, which already translates `opus` to that exact id for Pi). Two layers close
   this: (a) `_check_family_collisions` now keys on `canonical_model(provider, model)`, a curated
   `(provider, model) -> canonical id` map seeded from `PI_MODEL_MAP`, so both spellings collide; (b)
   `service.py`'s route-decide review branch gains a third hard exclusion, `REVIEW_MODEL_CONFLICT`,
   between `REVIEW_FAMILY_CONFLICT` and `REVIEW_PROVIDER_CONFLICT`, comparing `canonical_model` of the
   candidate against the writer's — defense in depth, independent of whether the build_snapshot-time
   guard was ever bypassed. `service.py` was not in this package's owned paths; touching it is recorded
   as an approved exception on the package state, not a silent scope expansion.

6. **`subscription`/`metered` is a curated, provider-keyed map, never a row field.**
   `PROVIDER_BILLING_KIND = {"opencode-zen": "metered", "opencode-go": "subscription"}`, declared
   alongside the AC-02 credential/CLI-id maps and the AC-04 allowlist — same file, same "declared by a
   curator, never derived from the probe" discipline. OpenCode Go is a monthly subscription and OpenCode
   Zen is metered/API-key (user clarification, `ai/state/decisions-log.jsonl` slug
   `opencode-zen-go-billing-model-distinto-no-mismo-pool`) — a different axis than model-id overlap: two
   kinds of provider by billing model, not just two catalogs that share ids. `build_snapshot`'s row
   schema is closed (`required_keys`/`optional_keys`); a `billing` key on a real row would raise
   `RoutingError("CATALOG_INVALID")` and take the entire catalog down, existing providers included. This
   feature implements no weighting, selection-order, or budget logic against this map — it records the
   fact only, as the input `008-dynamic-selection`'s `## P3` section (and whatever later ADR that section
   produces) will read.

## Rejected alternatives

- **A single `_OPENCODE_PROVIDER_KEYS`-shaped map for both the credential check and the CLI argument**
  (the previous draft's design). Backwards for the new pairs: the CLI-id value does not appear in the
  credential-name set `_parse_opencode_auth` produces, so every OpenCode-Zen/Go pair would report absent
  on every machine, never just on drift.
- **Reusing `PI_MODEL_MAP`'s shape for the credential/CLI-id translation.** `PI_MODEL_MAP` translates a
  model name within one already-matched provider — a different axis than the one that broke here, which
  is the provider identifier itself varying independently across two unrelated string spaces
  (credential display text vs. CLI argument).
- **Curated `family` MUST equal the vendor-reported value, captured live via `--verbose`.** Two ways to
  satisfy this were tried and both fail: probing `--verbose` breaks the existing parser
  (`_parse_opencode_models` raises `PROVIDER_UNAUTHENTICATED` on the JSON body lines that follow the
  first `opencode/<model>` line), and copying the vendor's literal string for the 2 of 11 shared ids
  where providers disagree would fabricate a false `REVIEW_FAMILY_CONFLICT`/`REVIEW_PROVIDER_CONFLICT`
  independence for the same underlying model. `family` reverts to fully curated with the normalization
  rule in decision 5 instead.
- **`subscription`/`metered` as a `routes.v1.toml` row column.** Crashes `build_snapshot`'s closed
  row-schema validation for every provider, not only the new ones, on the very first curated row that
  carries it.
- **Sketching P3's weighting/selection consumer of the `subscription`/`metered` map inline in this
  feature.** That shape belongs to `008-dynamic-selection`'s `## P3` section; this feature only supplies
  the map as an input.

## Accepted residual risk

AC-07's collision rule keys on `canonical_model(provider, model)` — exact equality after curated
normalization, not raw model-id equality (post-SEC-001/SEC-002; see decision 5's repair note). Two ids
that are plausibly the same underlying model split across a free/paid tier but spelled differently
across lanes, and for which no curated `CANONICAL_MODEL`/`PI_MODEL_MAP` entry links them — measured
live: `opencode-go`'s `mimo-v2.5`/`mimo-v2.5-pro` next to `opencode`'s `mimo-v2.5-free`, with vendor
`family` values `"mimo-v2.5"` vs `"mimo-v2.5-free"` — are not linked by the rule and could still be
curated with diverging `family`, reopening the same false-independence scenario the rule closes for
curated-alias matches. Closing the general case needs model-identity knowledge no probe provides. This
is the same kind of curator judgment call already made today for `gpt-5.6-luna`/`gpt-5.6-sol`/
`gpt-5.6-terra` (three `models.toml` `codex` catalog entries, one underlying Codex family,
distinguished by curated `effort` tier rather than by a probed identity link) — named here as an
accepted gap, not fixed by this feature.

**SEC-002 (delta-review round 2, medium, closed).** The curated alias set closing the gap above is
itself only as complete as whoever curates it. SEC-001's first cut seeded `CANONICAL_MODEL` solely from
`PI_MODEL_MAP` — Pi's own CLI name-translation table, a different purpose and lifecycle from a security
guarantee — which left `fable` (a fourth `[catalog].claude` id `PI_MODEL_MAP` never needed to translate,
since Pi has no fable route) without a canonical alias, reopening the exact SEC-001 hole for that one
model. `catalog.py` now curates `fable` explicitly (`_ANTHROPIC_CANONICAL_EXTRA`), and a coherence test
(`test_sec002_...` in `tests/test_routing.py`) asserts every `[catalog].claude` id resolves through
`canonical_model` to a canonical id `[catalog].opencode_zen` actually curates — so this is no longer an
open residual risk for the four Anthropic ids curated today, though it remains the same kind of
standing curator obligation the `mimo-v2.5` example above already names: a future fifth Anthropic id, or
a first cross-lane alias outside the Anthropic family, still needs a human to add the curated pair, and
the coherence test only catches an Anthropic-side omission, by construction.

`store.py`, `service.py`, and `domain.py` carried uncommitted changes from the (`BLOCKED`, not accepted)
`011-quota-failover` feature at the time this ADR was written, while `catalog.py` and `models_config.py`
were clean against `HEAD`. This ADR therefore cites `service.py`'s reviewer-independence checks by their
stable symbols — `REVIEW_FAMILY_CONFLICT` and `REVIEW_PROVIDER_CONFLICT` inside its route-decide
review branch — rather than line numbers, which can move again before `011` lands. The same discipline
applies to `store.py`'s fallback-window machinery that `011` extends: `RoutingStore.consume_fallback`
(the method that atomically switches an authorized-but-undispatched run onto its pre-minted fallback
identity) and the `dispatches` table's terminal-state `CHECK` constraint (`state NOT IN
('terminal_success','terminal_failure','abandoned') OR fallback_window_open=0`, which forces
`fallback_window_open` closed the moment a run reaches any terminal state, so a fallback can never be
consumed after the fact). Neither symbol is touched by this feature — `012` adds no route to
`routes.v1.toml`, so nothing it discovers can yet be selected as a `selected_route_id` or a
`fallback_route_id` — but both are named here because `011`'s quota-failover linked dispatch is the
first consumer that would let a probed-but-uncurated OpenCode-lane pair actually reach `consume_fallback`
once AC-05's four gates are separately opened, and the accepted residual risk above (exact-id family
collision) applies identically to whichever of `selected_route_id`/`fallback_route_id` ends up naming
such a pair.

## Consecuencias

- `routing_core`'s probed universe now reflects the real, currently-authenticated OpenCode installation
  for four providers instead of two; nothing about how a route is chosen, cached, or recorded changes —
  `_cache_key` already hashes `[catalog]`/`[routing]` wholesale, so a cache written before this feature
  lands can never silently claim a Zen/Go pair.
- Discovery and routability stay cleanly separated: a later package can curate `routes.v1.toml` rows for
  either provider, extend `enabled_providers`, and extend `ROUTING_PROVIDERS` in one coordinated change
  (per the four-gate model in decision 4) without touching the probe mechanism this feature adds.
- The two-map split (decision 2) and the five-site allowlist (decision 3) are the same discipline
  extended, not a second, competing mechanism — future providers with their own independently-varying
  credential/CLI-id strings follow the same pattern.
- `family`'s curator-normalization rule (decision 5) is a standing obligation on whoever curates the
  first shared-id row across OpenCode-lane providers, not a one-time migration; `_check_family_collisions`
  enforces it automatically on every `build_snapshot` call from that point on.
