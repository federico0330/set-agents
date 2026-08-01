# Feature 012 — discovered-inventory, contract 1.0.0

Status: `SPEC_CHALLENGE` corrió tres veces en total, las tres sobre este mismo contenido (heredado del
intento como `008-P2`, ver "Origen" abajo): primera — `revision_required`, 19 hallazgos (3 bloqueantes, 4
altos, 6 medios, 6 bajos), todos aplicados; segunda — `revision_required`, acotado a 1 bloqueante + 2 altos +
3 bajos (más 2 bajos heredados sin resolver de la primera), todos aplicados; tercera — verificación,
`ready_for_user_approval`, 4 bajos resueltos como correcciones de texto puntuales, sin bloqueantes ni altos
ni medios.

## Origen

Este contrato se redactó, desafió y corrigió como la sección `## P2 — discovered-inventory` de
`008-dynamic-selection`, a través de tres rondas completas de spec-challenge (detalle abajo). No pudo quedarse
ahí: `ai/state/features/008-dynamic-selection.json` tiene `acceptance_criteria: [AC-01..AC-10]`, acuñada una
sola vez por `cmd_init` cuando el P1 de 008 fue aceptado — con historial real detrás (spawns, un panel de
revisión, un registro de aceptación). `cmd_init` es el único comando que escribe `acceptance_criteria`, y la
única forma de extender esa lista es `--force`, que reconstruye el archivo de estado de la feature desde cero
y destruiría el historial real de P1, no solo planning descartable. Es exactamente la misma pared que
`006-execution-graph` encontró con su propio intento de P3.1 antes en esta sesión, razón por la cual ese
trabajo hoy vive como la feature `010-spawn-provenance` en vez de dentro de `006`. Decisión registrada en
`ai/state/decisions-log.jsonl`, slug `p2-discovered-inventory-pasa-a-ser-su-propia-feature-012`, 2026-07-30.
La propia sección `## P2` de `docs/specs/008-dynamic-selection/spec.md` vuelve a su párrafo original, sin
contrato, con un puntero de una línea hacia este archivo — el resto de 008 (P1, aceptado con historial; P1b,
diferido; P3, alcanzado pero no contratado) queda intacto por esta separación.

Los números de AC de abajo son las mismas AC-11..AC-22 del intento como 008-P2, renumeradas AC-01..AC-12 (la
convención de toda feature nueva) con cada referencia cruzada interna actualizada — incluidos los puntos que
apuntaban a las secciones `P1b`/`P1`/`P3` de 008 por encabezado desnudo, ahora nombrados explícitamente porque
cruzan un límite de archivo. Ningún contenido técnico se reescribió para la mudanza; solo cambiaron números y
punteros de sección.

Depends on: ninguna dependencia de código dura de otra feature — el contrato toca únicamente
`ai/scripts/routing_core/catalog.py`, `models.toml` (tablas `[catalog]`/`[routing]`) y
`ai/scripts/models_config.py` (`ROUTING_PROVIDERS`). Nace del mismo problema que motivó `008-dynamic-selection`
(ver el "Contexto" y la "tension paragraph" de ese archivo) y comparte terreno con `004-adaptive-dispatch`
(las lanes `zen`/`go-zen` de `models.toml`) y con `011-quota-failover` (`provider_exhaustions`, hoy `BLOCKED`,
no aceptada) — ninguna de las dos se edita ni se requiere aceptada para que este contrato sea correcto; ambas
relaciones están nombradas explícitamente en las ACs de abajo, no asumidas.

## Historial de challenge (heredado del intento como 008-P2)

**Primera pasada** — `revision_required`, 19 hallazgos (3 bloqueantes, 4 altos, 6 medios, 6 bajos).
Bloqueantes reales: **F-01** (el mapa credencial→id-CLI corría al revés y habría dejado los dos pares nuevos
inalcanzables en toda máquina, no solo en drift); **F-02** (la asimetría de exit code entre proveedores
inválidos estaba mal medida — contaminada por un `| head` de shell); **F-03** (la AC original de "effort
capability record" partía de una premisa refutada al correr el comando real con `--verbose`). Altos: **F-05**
(`family` estaba mal archivada como "política no descubierta" cuando es un campo de seguridad real, leído por
`REVIEW_FAMILY_CONFLICT`); **F-06** (Zen y Go no son solo catálogos que se solapan, son dos tipos de proveedor
distintos por modelo de facturación); **F-07** (existe un cuarto gate de selectabilidad, `ROUTING_PROVIDERS`,
no encontrado en la redacción original). El resto — medios y bajos — fueron correcciones mecánicas de cita y
alcance, todas aplicadas sin volver a preguntar.

**Segunda pasada** — `revision_required`, acotado a 1 bloqueante + 2 altos + 3 bajos, más 2 bajos heredados
sin resolver de la primera (F-16, F-18) — los seis nuevos originados enteramente por los propios fixes de la
primera pasada a lo que hoy son AC-07 y AC-08. **N-01** (bloqueante) + **N-02** (alto): el mandato "el valor
curado de `family` DEBE igualar el vendor-reportado" era autocontradictorio — sondearlo en vivo con
`--verbose` rompe el parser existente (`_parse_opencode_models` levanta `PROVIDER_UNAUTHENTICATED`), y
copiarlo literal habría fabricado una independencia de revisor falsa para 2 de los 11 model ids compartidos
entre Zen y Go (`minimax-m2.7`, `minimax-m3`). Resuelto revirtiendo `family` a curación manual con una regla
de normalización cruzada nueva — decisión registrada en `ai/state/decisions-log.jsonl`, slug
`family-se-normaliza-no-se-captura-del-vendor-para-ids-compartidos`. **N-03** (alto): el campo
`subscription`/`metered` no puede ser una columna de fila de `routes.v1.toml` — el esquema de fila es cerrado
(`required_keys`/`optional_keys`, `catalog.py:359-360,366`) y cualquier clave extra tumba el catálogo entero;
se movió a un mapa curado a nivel de proveedor, mismo patrón que el mapa credencial→id-CLI de AC-02. **N-04**
(bajo): el bosquejo de dos capas de P3 estaba mal ubicado dentro de lo que hoy es AC-08 — movido a la sección
`## P3` de `008-dynamic-selection`, que sigue viviendo ahí, no repetido en este archivo. **N-05** (bajo): una
palabra ("invent") describía un riesgo que la propia regla de intersección de AC-04 hace imposible por
construcción. **N-06** (bajo): una cita contaba "cuatro call sites" cuando en realidad eran cuatro funciones
con cinco referencias de línea.

**Tercera pasada** — verificación, `ready_for_user_approval`, 0 bloqueantes/altos/medios, 4 bajos resueltos
como ediciones de texto puntuales por el coordinador: **L-01** confirmó que el bosquejo de dos capas de P3
quedó en su lugar correcto (la sección `## P3` de `008-dynamic-selection`); **L-02** corrigió una cita de
línea ajena a este contrato (`service.py:163→164`, dentro de la sección P1b de 008, no de este archivo);
**L-03** agregó, a lo que hoy es AC-12, un párrafo de riesgo residual aceptado sobre `mimo-v2.5`/
`mimo-v2.5-pro` (ids plausiblemente relacionados pero no exactamente iguales, fuera del alcance de la regla
de colisión exacta de AC-07); **L-04**, también en AC-12, instruye que el ADR cite símbolos de
`store.py`/`service.py`/`domain.py` en vez de números de línea, porque esos archivos tienen cambios sin
aceptar de la feature `011` (`BLOCKED`) que pueden mover las líneas antes de que el ADR se escriba.

## AC-01..AC-12

**Amended 2026-07-30, revised 2026-07-30 (second pass).** This section was originally a scoping paragraph
with no acceptance criteria; it was first rewritten into AC-01..AC-10, then sent to a clean-context
spec-challenger who returned `revision_required` with 19 findings (3 blocking, 4 high, 6 medium, 6 low). This
revision addresses all 19 inline, re-measuring everything the first pass cited as "verified live" with the
corrected method (`subprocess.run(cmd, capture_output=True, text=True)`, no shell pipe, `.returncode`/
`.stdout`/`.stderr` read separately) rather than reusing the first pass's readings, several of which were
mismeasured. What changed **of substance**, not just citation: the credential-to-CLI-id translation was
backwards and would have left the new pairs permanently unreachable (F-01); the claimed exit-code asymmetry
for invalid providers does not exist and the real closing mechanism is a different line (F-02); the "effort
capability record" AC is retracted, its premise refuted live (F-03) — the field promoted in its place is
`family`, wrongly filed as undiscoverable policy when it is actually vendor-reported and security-relevant
(F-05); Zen and Go are not just overlapping catalogs but two different kinds of provider by billing model
(F-06); a fourth selectability gate exists that the previous pass did not find (F-07). Numbering now runs
AC-01..AC-12 to hold the added scope.

**Revised again 2026-07-30 (third pass, second spec-challenge round).** 16 of the 19 first-round findings were
independently reverified and closed by that second challenger, including F-01/F-02 tested end-to-end against
the real CLI; the return was `revision_required`, scoped to 1 blocker + 2 high + 3 low, all originating from
this section's own fixes to AC-07 and AC-08 (N-01..N-06 below), plus two carried-over low findings from the
first round (F-16, F-18). AC-07's "the curated value MUST match the vendor-reported one" mandate is retracted:
it required either an `--verbose` probe that breaks the existing parser (reproducing F-03's structural
failure) or a literal vendor-string copy that, for 2 of the 11 shared model ids, would fabricate a false
`REVIEW_FAMILY_CONFLICT`/`REVIEW_PROVIDER_CONFLICT` independence (N-01 blocking, N-02 high) — `family` reverts
to fully curated, with a new curator-normalization rule for cross-provider collisions instead. AC-08's
`subscription`/`metered` field moves from a proposed `routes.v1.toml` row column — which would have crashed
`build_snapshot`'s closed row-schema validation on the very first curated row, `catalog.py:359-360,366`
(N-03 high) — to a provider-keyed map alongside AC-02's credential-key map. Decision authority for both fixes:
the coordinator, relaying a technical correction to an already-approved security guarantee, not a product
trade-off; logged at `ai/state/decisions-log.jsonl`, slug
`family-se-normaliza-no-se-captura-del-vendor-para-ids-compartidos`, 2026-07-30. AC-01 and the non-goals
paragraph also drop an "invent" claim about allowlist copying that AC-04's own intersection rule makes
impossible by construction (N-05), correct a citation to name four functions rather than an undercounted
"four call sites" (N-06), and P2's non-goals now name the sondeable-but-unused `cost`/`limit.context` fields
(F-18) alongside a corrected P1/P1b citation drift (F-16, `store.py`/`service.py` line numbers, unrelated to
P2's own scope but fixed in passing since it was already flagged). AC-01..AC-06 and AC-09..AC-12 are
unchanged from the second pass — the second challenger verified them individually and this revision does not
reopen them.

**What is actually missing (verified, not assumed).** `ai/catalogs/routes.v1.toml` has exactly six rows,
`provider ∈ {openai-codex, anthropic}` (verified by reading the file). `probe_inventory`
(`ai/scripts/routing_core/catalog.py:305`) only ever probes the `(runtime, provider)` pairs in the closed
table `_PAIR_COMMANDS` (`catalog.py:60-67`) — the comment above the table states "a pair absent here can
never authenticate, list models, or appear in identities" (`catalog.py:58-59`; the enforcement is the four
sites that consult `_PAIR_COMMANDS` directly, `catalog.py:212,258,326,328,362` — see AC-01 for why the
`allowed_probe` helper is not the citable mechanism). OpenCode's own models are real and live today, and are
simply outside that table. Re-verified live in this environment (2026-07-30, read-only, credential values
never printed, no shell pipe): `opencode auth list --pure` reports four credentials — `OpenCode Go`, `OpenAI`,
`GitHub Copilot`, `OpenCode Zen` — and `opencode models opencode --pure` returns **60** model ids (not
"100+", corrected — see AC-01) including `opencode/kimi-k2.7-code`, `opencode/glm-5.2`,
`opencode/deepseek-v4-pro`, `opencode/deepseek-v4-flash-free` and `opencode/nemotron-3-ultra-free`;
`opencode models opencode-go --pure` returns a separate, smaller **16**-id `opencode-go/…` roster
(`opencode-go/kimi-k2.7-code`, `opencode-go/glm-5.2`, …). The Zen names are exactly what `models.toml`
already uses for its `zen` OpenCode lane (`models.toml:18,66,72,78,96,102,115,125,182,198,203,224`) to pick a
**fixed, hand-typed** model per role/area — that file already proves the Zen names are real. The Go names are
**not** independently corroborated by `models.toml`: `grep -c "opencode-go/" models.toml` returns **0** — the
file's `go-zen` lane column is populated with `openai/…` or `opencode/…` values today, never
`opencode-go/…` (verified; see AC-01's non-goal note). Nothing in `routing_core` can audit, revalidate, or
offer either lane through `--route-decide` today, because neither was ever probed. This is the gap P2 closes:
not the `models.toml` lanes (out of scope, unchanged by this contract), but the fact that `routing_core`'s
probed universe stops one provider short of what is actually authenticated where the harness runs.

**What P2 does not touch (verified during exploration, not assumed absent).** `service.py`'s exhaustion check
(`elif self.store is not None and self.store.provider_exhausted(route.provider): reason="PROVIDER_EXHAUSTED"`,
`service.py:143`) is a separate hard exclusion that runs on the candidate list built from the probed
inventory — it never feeds the probe itself. `provider_exhaustions` (`store.py:410,698`) was implemented
under the separately tracked `011-quota-failover`, but per `docs/adr/0015-quota-failover.md`
(`Estado: Proposed`, 2026-07-30) and the coordinator's confirmation it is **BLOCKED, not accepted** — see
`008-dynamic-selection`'s P1b section; nothing here should be read as "011 shipped." Nothing this section adds reads
`provider_exhaustions`. P2 is availability-right-now only; it neither reads nor writes exhaustion memory,
spend, or quota state. No dependency on `011` or `007-P2` was found by reading the code; if one is found
later it must be stated here, not silently absorbed.

- **AC-01** — the probeable universe is the closed pair table, extended, never replaced, and its real numbers
  are corrected. `_PAIR_COMMANDS` (`catalog.py:60-67`) is the single source of runtime/provider compatibility
  (comment at `catalog.py:58-59`); the real enforcement is four functions that reference the table directly —
  `_read_probe_cache` (`catalog.py:212`), `_probe_pairs` (`catalog.py:258`), `probe_inventory`
  (`catalog.py:326,328` — two references inside the same function), and `build_snapshot` (`catalog.py:362`) —
  five line references across those four functions (clarified 2026-07-30, second spec-challenge pass, N-06:
  "four call sites" undercounted the two references inside `probe_inventory`) — not the `allowed_probe`
  helper (`catalog.py:73-75`), which `grep -rn "allowed_probe" --include=*.py .` outside its own definition
  returns zero callers for: it is dead code and must not be cited as the mechanism. `_PAIR_COMMANDS` gains
  exactly two new pairs: `("opencode", "opencode-zen")` and `("opencode", "opencode-go")`. Re-measured live
  2026-07-30 with `subprocess.run(..., capture_output=True)` (no shell pipe, correcting the previous pass's
  `| head`-tainted count): `opencode models opencode --pure` returns **60** model ids; `opencode models
  opencode-go --pure` returns **16**. Six of the 60 `opencode/…` ids end in `-free` (`deepseek-v4-flash-free`,
  `laguna-s-2.1-free`, `ling-3.0-flash-free`, `mimo-v2.5-free`, `nemotron-3-ultra-free`,
  `north-mini-code-free`); zero of the 16 `opencode-go/…` ids do — the free tier is Zen-only, and an
  allowlist copied verbatim from one pair's roster to the other's would silently drop members (corrected
  2026-07-30, N-05: "or silently invent members" is retracted — AC-04's intersection rule, `allowed &
  _parse_opencode_models(...)`, `catalog.py:297`, makes inventing a model impossible by construction; the
  real, empirically confirmed risk is drop-only). `models.toml` corroborates the Zen names (citations above)
  but has zero `opencode-go/` occurrences (`grep -c` verified) — the Go pair's names are proven only by this
  session's direct CLI probe, not by any existing file, and that must not be overstated as independently
  corroborated. No provider the harness has never audited an invocation for is ever added implicitly, and no
  runtime other than `opencode` gains a pair — these are OpenCode-lane models only; `codex`, `claude-code`
  and `pi` have no client for them and none is implied here.
- **AC-02** — the credential check needs two separate maps, not one, and the previous revision's translation
  ran backwards. `_probe_pairs` (`catalog.py:242-302`) never starts from a credential's display text: it
  starts from the catalog provider string (e.g. `"openai-codex"`), looks it up in `_OPENCODE_PROVIDER_KEYS`
  (`catalog.py:69`) to get one `provider_key`, and reuses that single value for two different jobs — the
  credential-set membership test (`if provider_key not in credentials: continue`, `catalog.py:295`) *and* the
  models-listing CLI argument/line-prefix passed into `_parse_opencode_models(completed[1].stdout,
  provider_key)` (`catalog.py:297`). For the two existing providers this single value coincidentally serves
  both jobs (`"openai"` is both the credential name and the CLI argument). It cannot for the two new pairs.
  Re-measured live: `_parse_opencode_auth` (`catalog.py:102-114`) run on the real `opencode auth list --pure`
  output yields the credential-name set `{"opencode go", "openai", "github copilot", "opencode zen"}` (two
  tokens each for the new ones, literal display text with the method stripped) — while the CLI argument that
  actually returns a model roster is the single token `opencode` and the hyphenated token `opencode-go`
  (verified: `opencode models opencode --pure` → `returncode=0`, 60 ids; `opencode models "opencode zen"
  --pure` → `returncode=1`, `Error: Provider not found: opencode zen` on **stderr**, empty stdout). One map
  keyed the way `_OPENCODE_PROVIDER_KEYS` is today cannot hold both values for the same provider, and using
  the CLI-id value at the AC-02(old)/`catalog.py:295` membership check — as the previous revision of this AC
  specified — would search for `"opencode"`/`"opencode-go"` inside a credential set that only ever contains
  the two-token display names, so the pair would be reported absent **on every machine**, authenticated or
  not. Two maps are required: (1) `_OPENCODE_PROVIDER_KEYS` extended with `"opencode-zen": "opencode zen"`,
  `"opencode-go": "opencode go"` (the credential-name side, used at the `catalog.py:295` check); (2) a second,
  new map providing the CLI argument/prefix — `"opencode-zen": "opencode"`, `"opencode-go": "opencode-go"` —
  used to build the `_PAIR_COMMANDS` argv and passed into `_parse_opencode_models`. [UNVERIFIED for
  architecture: exact symbol name/location for map (2); the requirement is that the two lookups are
  independently addressable for the same provider, not a specific Python identifier. `PI_MODEL_MAP`
  (`catalog.py:56`) is explicitly the WRONG precedent here — it translates a model name within one
  already-matched provider, a different axis than the one that broke — `_OPENCODE_PROVIDER_KEYS` is the real
  precedent, extended, not replaced.]
- **AC-03** — with the two-map split in AC-02, the fail-closed guarantee is real and demonstrated, not merely
  asserted. Success path, verified live: `_OPENCODE_PROVIDER_KEYS["opencode-zen"]` (map 1) would be
  `"opencode zen"`, present in the live-parsed credential set `{"opencode go", "openai", "github copilot",
  "opencode zen"}`, so `catalog.py:295`'s `continue` does not fire, and probing proceeds to map 2's
  `"opencode"` CLI argument, which does return the 60-id roster. Failure path: if a future OpenCode release
  renames the credential's display text (e.g. to `"OpenCode Zen v2"`), `_parse_opencode_auth` would yield
  `"opencode zen v2"`, map 1's stale `"opencode zen"` value is absent from that set, `catalog.py:295` fires,
  and the pair is silently excluded — never silently assumed authenticated. This is the concrete instance of
  "falla cerrada, nunca inventa" for this section, and it only holds now because AC-02 fixed which direction
  the lookup runs: under the previous revision's single, backwards map, this branch could not succeed on ANY
  machine, which is a stronger defect than "fails closed on drift" — it never worked at all. AC-02 is what
  turns "always absent" into "absent only on a real credential mismatch."
- **AC-04** — model membership stays intersection-only, and that ceiling is enforced at three sites that must
  move together, not one. Today's rule for the two existing providers ("Model names are always the
  intersection with the canonical models.toml catalog for the provider, so a runtime can never widen the
  audited model set", `catalog.py:308-311`) is implemented by three places that each currently hardcode
  exactly two providers: (1) `models.toml`'s `[catalog]` table (today only `catalog.codex`/`catalog.claude`,
  `models.toml:13-14`); (2) `_configured_models`'s own hardcoded key map (`key = {"openai-codex": "codex",
  "anthropic": "claude"}.get(provider)`, `catalog.py:79`); (3) `build_snapshot`'s independent second hardcode
  (`configured_models = {provider: _configured_models(config, provider) for provider in ("openai-codex",
  "anthropic")}`, `catalog.py:356`). Extending only the TOML without (2) and (3) leaves the new providers'
  allowlists unreachable from code — `_configured_models` would return an empty set for them regardless of
  what the TOML says, and `probe_inventory`'s `if not allowed: continue` (`catalog.py:260`) would silently
  skip both new pairs on every run. [UNVERIFIED for architecture: exact `[catalog]` key spellings for the two
  new allowlists; the invariant is "declared ceiling, probed floor, enforced at all three sites in lockstep,"
  not the TOML key spelling.]
- **AC-05** — there are FOUR independent gates a probed pair must clear before it is ever selectable, not
  three (corrected from the previous revision, which found only the first three): (1) `_PAIR_COMMANDS`
  (AC-01); (2) the three-site `[catalog]` allowlist ceiling (AC-04); (3) `models.toml`'s
  `routing.enabled_providers` (`models.toml:32`, read at `catalog.py:351`); and (4) — found by re-reading
  `models_config.py`, not assumed absent — `ROUTING_PROVIDERS` (`models_config.py:35`, the closed set
  `{"openai-codex", "anthropic"}`), enforced as a hard allowlist at config-validation time
  (`models_config.py:187`: `not all(isinstance(x, str) and x in ROUTING_PROVIDERS for x in
  routing["enabled_providers"])`). Adding `"opencode-zen"` to `enabled_providers` WITHOUT first extending
  `ROUTING_PROVIDERS` does not leave the new provider merely unreachable — it makes `models.toml` fail to
  load at all (`die("models.toml: invalid [routing] values")`), which is every subsequent harness command.
  Gate (3) alone was undersold in the previous revision as "flip a switch in curated TOML"; it is that AND a
  matching edit to gate (4), in the same change, or the harness stops starting. P2 makes no change to any of
  the four gates itself; it names all four so the package that eventually opens them does not discover the
  crash live. Discovery answers "is it reachable right now"; it never answers "should the router consider
  offering it" — that stays a human decision behind all four gates, and P2 authorizes no route by itself.
- **AC-06** — row-level policy — `roles`, `tools`, `tier`, `curated_priority` — stays undiscovered, by design.
  Probing a CLI proves a model answers; it never proves which agent role should be trusted with it, at what
  tool surface, or at what tier. `build_snapshot` (`catalog.py:345-392`) keeps requiring all four on every row
  and validates them against the roster and `TIER_ORDER` exactly as today (`catalog.py:364-372`) — P2 changes
  what CAN be discovered as an available `(runtime, provider, model)` triple, never what a curated row is
  allowed to do with it. (`family` is still not folded into this list. Not, as an earlier revision of this
  contract claimed, because it must be vendor-captured — that claim is retracted in AC-07, second
  spec-challenge pass, N-01/N-02 — but because, unlike the fields above, it carries one extra
  cross-provider collision constraint that deserves its own AC; see AC-07.) This is the line that keeps "the
  inventory becomes discovered" from silently becoming "the router auto-curates roles" — the latter is
  explicitly out of scope.
- **AC-07** — `family` stays fully curated — set by a human, exactly like `roles`/`tools`/`tier`/
  `curated_priority` in AC-06 — with one added constraint for any model id that appears under more than one
  provider. (This AC fully replaces the previous two versions of AC-07: the first, an "effort capability
  record," whose premise was refuted live on the first spec-challenge pass and is not carried forward in any
  form — no per-model effort/reasoning axis distinguishes these providers the way `codex_effort` distinguishes
  `openai-codex`, and `probe_inventory` returns exactly `dict[(runtime,provider) -> set[str]]`, no richer
  "capability record" shape exists to populate. The second, which mandated the curated `family` value MUST
  equal the vendor-reported one, is retracted here — corrected 2026-07-30, second spec-challenge pass, N-01
  blocking + N-02 high: that mandate was self-contradictory and, followed literally, would have fabricated a
  false reviewer independence. Neither of those two premises survives into this version.)

  **Why "capture the vendor value" is wrong, measured on the second pass, not assumed.** Two ways to satisfy
  it were considered and both fail. (a) Probing it live requires `--verbose`
  (`opencode models <id> --verbose --pure`); re-run directly against the real parser in this pass —
  `_parse_opencode_models(<live --verbose stdout>, "opencode")` — it raises `RoutingError
  ("PROVIDER_UNAUTHENTICATED")` (`catalog.py:117-129`), not a parsed model set, because every line after the
  first `opencode/<model>` id is a JSON body line that does not start with the required `opencode/` prefix.
  Using `--verbose` therefore breaks the existing probe mechanism outright, contradicts AC-10/AC-11's "no
  probe mechanism change," and reproduces the exact structural failure that killed the original effort-based
  AC-07. (b) Copying the vendor's *reported* string literally for a shared model id does not preserve the
  safety property `REVIEW_FAMILY_CONFLICT` exists for: re-measured live, `minimax-m2.7` reports
  `family="minimax"` under `opencode` and `family="minimax-m2.7"` under `opencode-go` — same model, same id,
  two providers, two different vendor strings. Written literally into two curated rows, those two strings
  would make both `REVIEW_FAMILY_CONFLICT` (`service.py:149`) and `REVIEW_PROVIDER_CONFLICT`
  (`service.py:155`) fail to fire for a writer and a reviewer running the literal same model through
  different providers — independence that looks real in the record and is not.

  **The actual rule.** `family` is set by hand, never probed, exactly like `roles`/`tools`/`tier`/
  `curated_priority`. For any model id that appears under more than one curated provider — visible directly
  from the two rosters `probe_inventory` already returns for the new pairs, needing no new probing — the
  curator MUST set the identical `family` value on every curated row for that id across providers, normalized
  so the values collide even where the vendor's own taxonomy names them differently (both `opencode`'s and
  `opencode-go`'s `minimax-m2.7` rows get the same curated `family`, regardless of what each provider's own
  output says). The vendor's reported string remains informative context a curator may consult; it is never a
  binding source of truth. This preserves the guarantee `REVIEW_FAMILY_CONFLICT` exists for — the same
  underlying model is never allowed to review itself under a different provider name — instead of faithfully
  transcribing a vendor taxonomy that actively defeats that guarantee for at least 2 of the 11 shared ids
  measured. Decision recorded at `ai/state/decisions-log.jsonl`, slug
  `family-se-normaliza-no-se-captura-del-vendor-para-ids-compartidos`, 2026-07-30.

  **Correction of the first spec-challenge pass's own F-06 finding, verified live, not assumed.** 11 model
  ids are offered by both `opencode` and `opencode-go` (`kimi-k2.7-code`, `glm-5.2`, `deepseek-v4-flash`,
  `deepseek-v4-pro`, `glm-5.1`, `grok-4.5`, `kimi-k2.6`, `kimi-k3`, `minimax-m2.7`, `minimax-m3`,
  `qwen3.6-plus`) — but they are **not** all family-identical in the VENDOR's own reporting, as that finding
  stated ("byte-idénticos, misma family"). 9 of the 11 report the same `family` string under both providers;
  2 do not (`minimax-m2.7`, `minimax-m3`, both above). This is exactly why a "copy the vendor value" rule
  cannot work and a curator-normalized rule is required instead — the correction is what motivates this AC's
  mechanism, not an incidental footnote.

  **Verifiable today, without the probe, `--verbose`, or AC-05/AC-08's curation.** The rule is a pure function
  over any candidate row set: for every model id appearing in more than one row, all such rows must share one
  `family` value. This is unit-testable today with synthetic fixture rows — e.g. two fabricated rows,
  `provider="opencode-zen"` and `provider="opencode-go"`, both `model="minimax-m2.7"`, deliberately different
  `family` values — asserting the collision is rejected; the test exercises the validation rule itself, not a
  live curated catalog for the new providers, so it depends on nothing AC-05/AC-08 have not yet opened. The
  same rule is trivially satisfied by today's real six rows (`routes.v1.toml`), which share no model id
  across `openai-codex`/`anthropic` — the check is exercised meaningfully only once shared-id rows exist, but
  the rule and its test both exist and pass now. [UNVERIFIED for architecture: whether this check is added
  inside `build_snapshot` (`catalog.py:345-392`) as a new validation pass or as a separate lint step over
  `routes.v1.toml`; the requirement is that it exists and runs before any shared-id row is accepted, not its
  exact location.]
- **AC-08** — the `subscription`/`metered` distinction is a curated, provider-level map — same mechanism
  class as AC-02/AC-03's credential-key map — never a new column on a `routes.v1.toml` row. (Corrected
  2026-07-30, second spec-challenge pass, N-03, high: the previous revision proposed this as a per-row field.
  `build_snapshot` validates each row's key set as CLOSED — `required_keys = {"provider", "model", "family",
  "effort", "tier", "roles", "tools", "curated_priority"}`, `optional_keys = {"runtimes"}`
  (`catalog.py:359-360`) — and rejects any row carrying an extra key (`if not required_keys <= set(row) or
  set(row) - required_keys - optional_keys: raise ValueError`, `catalog.py:366`, re-verified against the real
  code). Adding a `billing`/`subscription` key to a real row would not merely leave the field unreachable, it
  would raise `RoutingError("CATALOG_INVALID")` on the very next `build_snapshot` call and take down the
  entire catalog for every provider, existing two included. And under this contract's own non-goals — no
  curated `routes.v1.toml` rows for the new models — no row exists yet for either new provider to carry a
  field on regardless.) A small, human-curated Python mapping keyed by provider string — e.g.
  `{"opencode-zen": "metered", "opencode-go": "subscription"}` — living alongside the AC-02 credential-key
  map and the AC-04 `[catalog]` allowlist (same file, same discipline, same "declared by a curator, never
  derived from the probe" rule), records the distinction without touching the closed row schema at all: it
  keys off `provider`, a value every row and every probed pair already carries, so it needs no schema change
  and no new row key. [UNVERIFIED for architecture: exact symbol name/location for this map; the requirement
  is that it exists as a provider-keyed, out-of-row structure, not a specific Python identifier.]

  Per the user's own clarification, relayed by the coordinator and logged at `ai/state/decisions-log.jsonl`
  (slug `opencode-zen-go-billing-model-distinto-no-mismo-pool`, 2026-07-30): "Opencode go es una suscripcion
  mensual (por ende tiene que usarse con mayor ponderancia que opencode zen que es una API KEY)." This is a
  different axis than AC-07's model-id overlap — it is two different KINDS of provider, not just two catalogs
  that share some model ids. Independent corroboration found while exploring, not assumed:
  `COMO-CAMBIAR-MODELO.md:56` already refers in prose to "the OpenCode Go five-hour quota," and
  `models_config.py:45-51`'s `SUBSCRIPTION_BY_PREFIX` maps BOTH the `"opencode"` and `"opencode-go"` prefixes
  to the same `"zen"` subscription key today — a latent inconsistency with the user's own billing
  description, pre-existing, living in `models_config.py`'s `models.toml`-driven static-agent lane (not
  `routing_core`), and explicitly **not fixed by this contract**, only named so it is not silently assumed
  already correct.

  **No weighting, no selection-order logic, no daily-USD ceiling is implemented or sketched here** (corrected
  2026-07-30, N-04: the previous revision sketched P3's two-layer model inline in this AC and then claimed
  "not sketched further," which was itself a sketch, in the wrong section. That shape belongs to, and stays
  fully in `008-dynamic-selection`'s `## P3` section and whatever `docs/adr/0016-discovered-inventory.md` records for it — this AC
  states only that the `subscription`/`metered` map is the input those later sections will read, not what
  they will do with it). `provider_exhaustions` (`store.py:410`, feature `011`, BLOCKED not accepted — `008-dynamic-selection`'s P1b
  section) remains the right shape for `opencode-go`'s real quota once `011` lands; it is the wrong
  shape for `opencode-zen`'s metered ceiling, which has no quota to exhaust in the same sense. P2 records the
  distinction so P3 does not have to re-derive it, and implements no part of what P3 will do with it.
- **AC-09** — `route_id` stability for a probed row is real, but is provable today only as a unit-level
  property, and this AC is scoped to say exactly that (the previous revision implied an end-to-end path
  already existed; AC-05/AC-08 establish that no route row, `enabled_providers` entry, or `ROUTING_PROVIDERS`
  entry exists for either new provider yet, so no live authorization can reach one). `StaticRoute.identifier`
  (`domain.py:147-149`) and `canonical_static_binding` (`domain.py:80-97`) hash only a row's own declared
  fields (provider, model, family, effort, tier, roles, tools, priority) as opaque UTF-8 strings — the
  function performs no provider allowlist check and has no knowledge of `_PAIR_COMMANDS`,
  `enabled_providers`, or `ROUTING_PROVIDERS`. The provable claim, and the exact fixture that proves it: a
  unit test constructs a synthetic `StaticRoute`-shaped row with `provider="opencode-zen"` (bypassing
  `build_snapshot`'s TOML/config path, which would correctly reject it today per AC-04/AC-05/AC-06 — this is a pure
  identity-function test, not a routed one) and asserts `StaticRoute.identifier(...)` returns a stable
  `rt1_`-prefixed hash indistinguishable in shape from one computed for `provider="openai-codex"`, and that
  `service.py`'s revalidation comparison (`recomputed != selected.route_id or not fresh.identity_allowed
  (identity)`, `service.py:181`) treats both as pure functions of their inputs with no special-casing by
  provider string. This is a property proof of the identity mechanism's provider-agnosticism, not an
  end-to-end route-decide path — the end-to-end path stays out of scope until AC-05 and AC-08's curation are
  separately done, and this AC must not be read as claiming otherwise.
- **AC-10** — the probe stays fail-closed on ambiguity or plugin drift, and the mechanism that enforces this
  is corrected from the previous revision's mismeasurement. `opencode models <id> --pure` (verified via
  `--help`: `--pure` "run without external plugins") must be passed for the two new pairs exactly as it
  already is for `("opencode","openai-codex")` and `("opencode","anthropic")` (`catalog.py:63-64`).
  Re-measured live 2026-07-30 with `subprocess.run(cmd, capture_output=True, text=True)` and no shell pipe
  (the previous pass's exit-code claim was measured through a trailing `| head`, which reports `head`'s exit
  code, not the probed command's — that reading is retracted): three distinct invalid-provider probes
  (`bogus-xyz`, the literal two-token credential strings `"opencode zen"` and `"opencode go"`, and even the
  existing catalog provider name `"anthropic"` run bare against this OpenCode installation) **all** return
  `returncode=1`, empty stdout, and the `Error: Provider not found: …` text on **stderr** — there is no
  exit-code asymmetry between a bogus provider and a real-but-misnamed one; all three fail the same way. The
  mechanism that actually closes this branch is `_probe_pairs`'s `if any(item.returncode != 0 for item in
  completed): continue` (`catalog.py:278`), never the stdout-`"Error"`-line branch inside
  `_parse_opencode_models` (`catalog.py:121-122`), which is unreachable here because `_parse_opencode_models`
  is only called after that nonzero-exit check already passed (`catalog.py:297`, inside the `try` starting at
  `catalog.py:280`). No new failure-handling code path is introduced for the two new pairs; the existing
  nonzero-exit check is exercised by two more pairs. The previous revision's claim of a stdout-based, exit-0
  error shape for invalid providers is retracted for the three cases re-measured here; it is not generalized
  to every possible malformed-provider shape, only asserted for what was actually run.
- **AC-11** — the probe cache and the decision/audit trail are unchanged by this contract. `_cache_key`
  (`catalog.py:167-170`) hashes `config["catalog"]` and `config["routing"]`, so adding AC-04's allowlists
  changes the hash automatically — a cache written before this contract lands can never silently claim a
  zen/go-zen pair (`_read_probe_cache`'s key match, `catalog.py:204`), and the "negatives are never persisted"
  rule (`catalog.py:190-191`) applies unchanged to the two new pairs, so one transient probe failure costs one
  retry, never the whole TTL window. Nothing about *how* a route is chosen or recorded changes:
  `route_decide`'s authorization (`service.py:198-201`) and the orchestrator's narration discipline
  (`record-spawn`/`log-narrative`) apply identically whether the winning row's provider is `openai-codex`,
  `anthropic`, or — once AC-05/AC-08 are separately curated — `opencode-zen`/`opencode-go`. This closes the
  original paragraph's last sentence: "selection stays a recorded decision with a stated rationale" is not a
  new promise P2 makes, it is the existing mechanism proven to need zero changes to keep holding.
- **AC-12** — `docs/adr/0016-discovered-inventory.md` records this design, mirroring `008-dynamic-selection`'s P1 AC-10 pattern.
  Confirmed as the next free ADR number by listing `docs/adr/` directly: the highest existing file is
  `0015-quota-failover.md` (`Estado: Proposed`). It must record, at minimum: the two-map credential/CLI-id
  split and why one `_OPENCODE_PROVIDER_KEYS`-shaped map cannot serve both roles (AC-02); the three-site
  catalog-membership allowlist that must move together (AC-04); the four-gate selectability model, including
  the `ROUTING_PROVIDERS` hard-crash risk (AC-05); `family`'s cross-provider normalization rule — stays fully
  curated, never vendor-captured, but must collide across providers for any shared model id, including the
  two-model vendor-taxonomy exception found live and the rejected vendor-must-match alternative (AC-07,
  corrected second spec-challenge pass, N-01/N-02 — this clause updated in that pass; nothing else in AC-12
  reopened); the `subscription`/`metered` provider-keyed map, not a row field, and its explicit
  non-implementation of any weighting logic (AC-08, corrected same pass, N-03); and the rejected alternative
  of reusing `PI_MODEL_MAP`'s single-map shape for the credential/CLI-id translation, rejected because it
  conflates two independently-varying strings (AC-02). It must also record, as an accepted residual risk
  (third spec-challenge pass, L-03): AC-07's collision rule keys on exact model-id equality, so two ids that
  are plausibly the same underlying model under a free/paid tier split but are spelled differently across
  lanes (measured live: `opencode-go`'s `mimo-v2.5`/`mimo-v2.5-pro` next to `opencode`'s
  `mimo-v2.5-free`, vendor `family` values `"mimo-v2.5"` vs `"mimo-v2.5-free"`) are not linked by the rule and
  could still be curated with diverging `family`, reopening the false-independence scenario AC-07 closes for
  exact-id matches. Closing the general case needs model-identity knowledge no probe provides; this is named
  as a curator judgment call already made today for `gpt-5.6-luna/sol/terra`, not fixed by this contract.
  Because `store.py`, `service.py`, and `domain.py` carry uncommitted changes from the (`BLOCKED`, not
  accepted) `011` feature at spec-writing time (third spec-challenge pass, L-04), while `catalog.py` and
  `models_config.py` are clean against `HEAD`, the ADR must cite the `store.py`/`service.py`/`domain.py`
  symbols this contract references (`consume_fallback`, the terminal-state `CHECK`, the review/run
  persistence branch) rather than their current line numbers, which can move again before `011` is accepted.

**Non-goals of P2 (explicit, so a later package does not assume them included).** No `enabled_providers` or
`ROUTING_PROVIDERS` change (AC-05 — all four gates named, none of them opened). No curated `routes.v1.toml`
rows for the new models — this contract makes them *probeable*, not *routable*; a route row still needs a
human to pick its roles/tools/tier/priority/family (the last with AC-07's cross-provider normalization rule).
The `subscription`/`metered` distinction (AC-08, corrected 2026-07-30 to a provider-keyed map, not a row
field) lives outside any row entirely, so it does not add to that per-row list. No change to `pi` or
`claude-code` lanes. No budget, spend, selection-weighting, or quality signal (`007-P2`'s and `008-dynamic-selection`'s P3's territory,
untouched — AC-08 records a field, never a decision, and its two-layer consumer sketch lives only in
`008-dynamic-selection`'s `## P3` section, not repeated here). No fix to `models.toml`'s existing `zen`/`go-zen` static lanes or to
`models_config.py`'s `SUBSCRIPTION_BY_PREFIX` zen/go conflation (named, not resolved, in AC-08) — they keep
working exactly as they do today, independent of whether `routing_core` can also see the same models. Also
out of scope, named so it is not silently assumed unavailable rather than deliberately unused (F-18, first
spec-challenge pass, low): `opencode models <id> --verbose --pure` additionally exposes `cost.input/output/
cache` and `limit.context` per model (verified live, same JSON objects `family` and `capabilities.reasoning`
were read from) — P2 does not capture either, and does not need `--verbose` at all for anything it actually
ships (AC-07 explicitly rejects using `--verbose` in the probe path); both fields are real, sondeable, and
deliberately left for whichever later package needs a true numeric cost signal.

### Audit (self-review)

- **Universe named:** yes — the closed `_PAIR_COMMANDS` extension (AC-01), the three-site `[catalog]`
  allowlist ceiling (AC-04), `enabled_providers` (AC-05), and `ROUTING_PROVIDERS` (AC-05) — **four**
  independent gates, corrected from the first pass's "three," each named, each fail-closed on its own.
- **Absence behavior defined:** yes for every failure mode found, including two the first pass measured
  wrong and this pass corrects: an untranslatable/stale credential-map entry (AC-03, now actually reachable
  because AC-02 fixed the lookup direction — the first pass's version could never succeed at all), a
  nonzero-exit CLI probe with stderr text (AC-10, corrected from a false stdout/exit-0 claim), and a
  stale/mismatched cache (AC-11) — each resolves to "pair/model absent," never to an assumed-available
  default.
- **Data source proven to carry the signal:** yes, re-measured live in this session (2026-07-30) with
  `subprocess.run(..., capture_output=True, text=True)` and no shell pipe, per the coordinator's explicit
  process correction — `opencode auth list --pure`, `opencode models {opencode,opencode-go} --pure`, and
  `opencode models {opencode,opencode-go} --verbose --pure` were all actually re-run in this pass, not reused
  from the first, mis-measured pass.
- **Pairwise conflict pass:** AC-01..AC-12 extend existing mechanisms (pair table, cache key, identity hash,
  exhaustion exclusion, family/provider-based review-independence check) rather than adding a second,
  competing one. Three external interactions were specifically checked, one added on the second
  spec-challenge pass: `PROVIDER_EXHAUSTED` (`service.py:143`, confirmed downstream and independent of the
  probe); `REVIEW_FAMILY_CONFLICT` (`service.py:149`) together with `REVIEW_PROVIDER_CONFLICT`
  (`service.py:155`) — checked as a PAIR, not singly, after the second pass showed AC-07's original
  vendor-must-match mandate would have let a shared model id satisfy both checks independently and produce a
  fabricated reviewer independence; AC-07's normalization rule is what keeps the pair from being satisfied
  independently for the same underlying model.
- **UNVERIFIED-for-architecture tags:** the credential/CLI-id map's exact symbol/location (AC-02), the three
  `[catalog]` key spellings (AC-04), the exact location of the family-collision validation pass (AC-07,
  added second pass), and the exact symbol/location for the provider-keyed `subscription`/`metered` map
  (AC-08, corrected second pass from a row-level TOML field to a provider-level Python mapping). All are
  HOW-level naming choices; the WHAT — that they must exist, stay separate where the evidence shows they vary
  independently, and fail closed — is asserted as the contract.
- **What I could not verify:** whether `OpenCode Go`/`OpenCode Zen`'s display text is stable across OpenCode
  CLI versions (only `1.18.5` was probed) — AC-03 is written so a future rename degrades to "absent," not to a
  silent false positive. Also not verified: whether every OpenCode CLI version returns `Error:` text on
  stderr with exit 1 for every malformed-provider shape, versus some other shape this session's three probes
  did not exercise — AC-10 is scoped to exactly the three cases measured, not generalized further.

## Verificación

`./ai/scripts/verify.sh` → `VERIFY_PASS` · `./build.sh --check` → `SELF_SCAFFOLD_SYNC_OK files=2` ·
`python3 -m unittest discover -s tests -v` · `git diff --check` · ownership vs baseline. Test count rises
from **473** (medido en vivo esta misma sesión, estática y dinámicamente — `grep -rhoE "^\s*def test_"
tests/*.py | wc -l` y `python3 -m unittest discover -s tests` → `Ran 473 tests`, un flake preexistente de
limpieza de `tempfile` ajeno a `routing_core`/`catalog` y no tocado por este contrato), never falls, and no
test is skipped.

**P2's** proof is that the probed inventory reflects the real, currently-authenticated environment, not a
mock — and specifically exercises the AC-02/AC-03 translation gap, not a fixture that has already been
translated for it. A fixture that stubs `opencode auth list --pure` to print the CLI provider id directly
(e.g. a synthetic `opencode` bullet instead of the real `OpenCode Zen` display line) would go green while the
real translation table sat broken or absent — that is the exact fixture this section's live check must
survive. The proof has two parts, of different kinds, corrected 2026-07-30 (F-04, F-14 from the P2
spec-challenge):

1. A hermetic unit test, part of the standard suite, never skipped: it drives the exact credential display
   text the parser actually consumes — `"OpenCode Go"`, `"OpenAI"`, `"GitHub Copilot"`, `"OpenCode Zen"`
   (these are the plain-text tokens `_parse_opencode_auth` reads once ANSI decoration is stripped by its own
   `_ANSI` regex, `catalog.py:70`; this document does not additionally claim to reproduce the raw ANSI/
   box-drawing bytes `opencode auth list` prints, only the text the parser is contractually given — a
   narrower and honest claim than "verbatim bytes," which the previous revision overstated) through
   `_parse_opencode_auth` and the two-map translation from AC-02, and asserts the correct CLI ids come out for
   both the success and the drifted-display-text failure path from AC-03.
2. **`P2 local live-parity gate`** — a named, explicitly credential-gated gate, opt-in and required only when
   the `OpenCode Zen`/`OpenCode Go` credentials are actually present on the machine running it, following the
   same pattern `011-quota-failover`'s own credential-gated E2E check already uses (`docs/specs/
   011-quota-failover/spec.md`: "an explicit, credential-gated E2E test... When its controlled precondition is
   absent, it records `BLOCKED`/`HUMAN_DECISION_REQUIRED`"). When the precondition is met, it runs a live
   (uncached, `fresh=True`) `probe_inventory` call and compares it against an independent, directly-run
   `opencode models {opencode,opencode-go} --pure` in the same process invocation — the probed model set must
   be a subset of the live CLI output intersected with the AC-04 allowlist, and must never contain a model
   absent from either. When the precondition is absent (CI, or any machine without those two subscriptions),
   this gate records `BLOCKED`/`HUMAN_DECISION_REQUIRED`, never a silent skip and never a false pass — it is
   named here specifically so it is never confused with, or counted against, the "no test is skipped" rule
   that governs the standard suite in part (1). Both parts are required; a passing unit test alone does not
   discharge the "reflects the real environment" obligation for this AC set, and a `BLOCKED` gate (2) does not
   excuse a failing or absent gate (1).

Standard test count rises from **473** (see the generic gate line above), same requirement as every other
gate in this feature; the credential-gated gate in part (2) is exempt from that count by name, not by
omission.
