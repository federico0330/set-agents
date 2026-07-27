# ADR-0008 — Two roots: `HARNESS_HOME` vs `PROJECT_ROOT`, install-time baking, project-scoped routing

- Estado: Accepted (2026-07-27). Feature `005-portable-harness`, contract 1.1.0, package P1-portable-core,
  work item T-100 / AC-00. This ADR is a BLOCKING predecessor: no P1 code lands before it.
- Amends the *deployment* assumptions of ADR-0004 and ADR-0007 (a harness that only works from
  `~/SET-AGENTES`). Does NOT amend ADR-0005 (routing store root stays fixed and environment-immune) nor
  ADR-0006 (AM-1/AM-2 fact derivation and probe cache are untouched).
- Every file:line citation below was re-verified against the working tree on 2026-07-27; the
  "Contract vs repo discrepancies" section at the end lists the places where the spec text and the code
  disagree, and states which one this ADR follows.

## Contexto

The harness hardcodes one assumption: **"the project" and "the harness" are the same directory.** The
orchestrator prompt writes `python3 ai/scripts/set_agents_app.py --route-decide` (a HARNESS file) and
`python3 ai/scripts/feature-state.py` (a PROJECT file) with the same relative syntax; only
`~/SET-AGENTES` happens to contain both. Splitting the two roots is the whole of P1, and it touches four
security-relevant surfaces at once: the coord allowlist, the context-pack confinement anchor, the routing
DB's identity model, and the installer's write path.

Four repo facts constrain the entire design and were verified before anything was decided:

1. **Baking cannot happen at build time.** `ai/scripts/verify.sh:13-16` regenerates `Global/**` into a
   staging dir and requires `diff -ruN "Global/$harness" "$STAGING/$harness"` to be empty;
   `ai/scripts/generate.py:429` copies `coord_policy.py` VERBATIM into the tracked
   `Global/claude-code/hooks/coord_policy.py`. A path baked at generate/build time would commit the
   *builder's* absolute path into tracked files and make `verify.sh` unpassable on every other machine —
   exactly what AC-09 proves must work.
2. **`install.py`'s substitution is JSON-only today.** `install.py:61-72` substitutes
   `__SET_AGENTS_ROOT__` inside `merged_json()` only, with a JSON-specific escape
   (`json.dumps(str(REPO_ROOT))[1:-1]`, line 71). Managed files are copied verbatim as bytes
   (`install.py:317`).
3. **The allowlist matches the raw command string.** `coord_policy.py:55-63` runs
   `re.fullmatch(pattern + r".*", command)` over the unparsed command. A `HARNESS_HOME` containing a space
   forces the caller to quote the path, and the quoted form never matches. (The `sudo` clause of
   `ALWAYS_DENY`, `coord_policy.py:44`, is `(?:^|\s)sudo(?:\s|$)` — it requires a whitespace boundary, so a
   directory component named `sudo` between slashes does NOT trigger it. The real defect is the space, not
   `sudo`.)
4. **The routing DB validates its own DDL byte-for-byte.** `store.py:168-187`
   (`_validate_existing_readonly`) compares every `sqlite_master` `table`/`index` SQL text, whitespace-
   normalized and lowercased, against the DDL a pristine `_create_schema()` produces
   (`store.py:155-166`). Any migration whose resulting DDL text differs from the canonical text — even by
   column ORDER inside the `CREATE TABLE` string — makes the DB permanently `ROUTING_UNAVAILABLE`.

## Opciones consideradas

1. **One root, made relocatable by `cwd` conventions.** Keep a single root and require every invocation to
   run from the harness. Rejected: it is the status quo, and it makes "route from the user's own repo"
   impossible without moving project state into the harness.
2. **Two roots, both discovered at runtime.** Discover `HARNESS_HOME` too (e.g. from `__file__` at every
   entry point). Rejected for the *allowlist* surface specifically: the coord permission entries are static
   text inside generated agent prompts and hook files; a permission pattern cannot be "discovered", it must
   be a literal. A literal that is correct per machine can only be produced by the installer.
3. **Two roots: `HARNESS_HOME` baked at install time into installed artifacts only, `PROJECT_ROOT`
   discovered per invocation.** Chosen. It keeps the tracked tree machine-independent (constraint 1),
   makes the sanctioned command surface an exact literal (auditable, no globbed prefix), and leaves the
   project side dynamic where it must be.
4. **Make the routing DB per-project (one DB under each `PROJECT_ROOT`).** Rejected: it contradicts
   ADR-0005's fixed, environment-immune root, multiplies the private-state surface, and destroys the global
   telemetry (`metric_rollups`) whose whole value is cross-project model quality. A `project_key` COLUMN
   inside the existing single DB gives scoping without moving storage.

## Decisión

### D1 — Two roots, named and resolved differently

| | `HARNESS_HOME` | `PROJECT_ROOT` |
|---|---|---|
| What | the clone of SET-AGENTES | the repo the user is working in |
| Resolved | ONCE, at install time (`install.py`, `REPO_ROOT = Path(__file__).resolve().parents[2]`, line 58) | per invocation, from `cwd` |
| Lives in | installed artifacts under `$HOME` only | nothing is baked; it is discovered |
| Trust | the operator's own tree (trusted) | third-party content (UNTRUSTED, see D6) |
| Owns | `set_agents_app.py`, `coord_policy.py`, `models.toml`, `roles.tsv`, the agent prompts | `ai/state/`, `docs/`, `ai/scripts/feature-state.py`, `ai/scripts/check-owned-paths.py` |

Doctrine, stated once and applied everywhere: **a reference to a HARNESS-side artifact is baked absolute
(via the placeholder); a reference to a PROJECT-side artifact stays relative to the invocation `cwd`.**
Applied to `Global/_canonical/agents/orchestrator.md` (verified occurrences): lines 146, 169, 193, 198
(`set_agents_app.py`) become `__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py`; lines 54
(`feature-state.py`) and 209 (`check-owned-paths.py`) stay relative. Same split in `coord_policy.py`'s
allowlist (D4) and in `generate.py:210-212`'s emitted permission lines.

`ROOT` in `set_agents_app.py:31` keeps its current meaning and name (`HARNESS_HOME`); a new module-level
`PROJECT_ROOT` resolution (D5) is added beside it. `STATE_DIR` (`:32`) is harness/machine state and is
NOT re-anchored.

### D2 — Path baking happens exclusively in `install.py`'s write path

**Mechanism.** One function, used by every write and by the preview:

```python
PLACEHOLDER = b"__SET_AGENTS_ROOT__"

def substitute_root(data: bytes, *, json_escaped: bool) -> bytes:
    """Bake this machine's HARNESS_HOME into an installed artifact. `json_escaped=True`
    keeps the historical JSON rendering (install.py:71); False writes the raw value,
    which is unambiguous in Python/Markdown/TOML/YAML precisely because D3 refuses to
    install from a root containing quote, backslash, or glob bytes."""
```

- Operates on **bytes**, never on decoded text: `install.py:317` already writes
  `source.read_bytes()` with `source.stat().st_mode & 0o777`; substitution must not change either the
  encoding or the mode.
- Applies to **every managed file whose bytes contain the placeholder**, not to a hardcoded four-file list.
  Rationale: the placeholder is an explicit opt-in marker; an allowlist would silently miss a new consumer.
  The set that contains it today (verified in `Global/*/managed-files.txt`) is
  `claude-code/hooks/coord_policy.py`, `opencode/agents/orchestrator.md`,
  `claude-code/agents/orchestrator.md`, `codex/agents/orchestrator.toml`, plus the two JSON specials
  already handled.
- **The two JSON specials keep the existing JSON escape** (`json_escaped=True`), byte-identical to today,
  because `tests/test_harness.py:1637` regression-locks that path and the escape is defense in depth for a
  writer that also merges pre-existing user config. Managed files use `json_escaped=False`. The two
  renderings differ only for non-ASCII roots (`json.dumps` emits `\uXXXX`); both are correct in their own
  syntax, which is exactly why the flag exists rather than a single global escape.
- **The preview path MUST use the same function.** `install.py:253-281` compares staging bytes against the
  installed file, and `build.sh:78` runs `--preview` before every real install while
  `ai/scripts/check-drift.sh:22-27` derives its post-commit `DRIFT_DETECTED` badge from
  `MANAGED_DIFF_FILES`. If the preview compared the *unsubstituted* staging bytes against the *substituted*
  installed file, those files would report as changed forever: a permanent phantom diff on every install
  prompt and a permanent `DRIFT_DETECTED` on every commit. This is a hard requirement, not a nicety.

**Manifest coherence.** `MANIFEST` (`install.py:45`, written at `:368-369`) records only *target relative
paths* (`str(t.relative_to(home))`), never contents or hashes. Byte substitution therefore cannot
desynchronize it, and no manifest change is required. This is recorded so the implementer does not "fix"
a non-problem.

**Post-install verification (rollback-able).** Inside `install.py`'s existing `try:` block, alongside the
other smoke checks (`:332-354`) and BEFORE the manifest write: assert that no installed managed file and no
installed special still contains `PLACEHOLDER`. A failure raises, which triggers `rollback()` (`:305-313`)
and prints `INSTALL_ROLLED_BACK` — an unsubstituted placeholder is a failed install, never a silent one.

**The `Global/**` assertion in `verify.sh` (T-101), in its implementable form.** AC-01's literal wording
("`Global/**` … contains ZERO absolute filesystem paths") is FALSE against the current tree and cannot be
implemented as written — verified: `Global/_canonical/opencode-agents/package-gate-runner.md` and its
compiled copy `Global/opencode/agents/package-gate-runner.md` carry hardcoded
`/home/federico/iey/iey-ai/...` literals, and every script under `Global/**` starts with the absolute
shebang `/usr/bin/env`. The gate is therefore three precise rules:

- **R1 (placeholder present).** Every occurrence of `ai/scripts/set_agents_app.py` under `Global/**` is
  immediately preceded by `__SET_AGENTS_ROOT__/`. Zero bare occurrences.
- **R2 (no builder path).** `Global/**` contains zero occurrences of the building machine's own
  `HARNESS_HOME` string (`$ROOT` in `verify.sh`). True today (verified: `SET-AGENTES` appears in
  `Global/**` only as prose in `commands/feature-batch.md:45`), and it is the property that actually makes
  `verify.sh` pass on a guest machine.
- **R3 (absolute-path ratchet).** The set of files under `Global/**` containing a `/home/`- or `/Users/`-
  anchored path is exactly the frozen legacy pair named above; any new file joining that set fails the
  gate. The pair is a PRE-EXISTING defect (a project-specific allowlist committed into the canonical
  roster), out of P1's ownership, and is recorded in "Contract vs repo discrepancies" — the ratchet stops
  it from growing without pretending P1 fixed it.

### D3 — `install.py` refuses a hostile `HARNESS_HOME`

Validation runs at the TOP of `install.py`, immediately after `REPO_ROOT` is computed (`:58`) and before
any backup directory is created (`:283-302`), so a rejected root writes nothing at all — and because
`build.sh --install` runs `--preview` first (`build.sh:78`), the refusal surfaces before the confirmation
prompt.

Rejected byte classes in `str(REPO_ROOT)` — a superset of `FORBIDDEN_SYNTAX` (`coord_policy.py:37`), with
each addition justified by a real downstream syntax:

| Bytes | Why |
|---|---|
| `;` `\|` `<` `>` `` ` `` `&` `$` | `FORBIDDEN_SYNTAX` hard-blocks any command containing them, so the allowlist could never match (`&`/`$` are rejected as whole bytes, not only as `&&`/`$(`, because a single one still breaks a shell token) |
| `"` `'` `\` | the value is baked into a Python string literal, a TOML multi-line basic string (`Global/codex/agents/orchestrator.toml:6`, `developer_instructions = """…"""`) and JSON-quoted permission keys |
| `*` `?` `[` `]` | the OpenCode/Claude permission entries are GLOB patterns (`Global/opencode/agents/orchestrator.md:111`); a glob metacharacter inside the baked path would make the sanctioned pattern match MORE than the intended command — a permission widening, not just a mismatch |
| `\n` `\r`, any C0/C1 control byte | `allowed()` rejects any command containing a newline (`coord_policy.py:57`) |

**A SPACE is explicitly ACCEPTED.** It is the ordinary macOS/Windows case and is handled by D4, not by
refusal.

Output and exit code:

```
INSTALL_ABORTED_UNSAFE_ROOT root=/Users/Jane;Doe/SET-AGENTES offending=';'@offset=11
  The harness path must not contain shell, quoting, or glob metacharacters.
  Move or rename the clone (a SPACE is fine) and re-run ./build.sh --install.
```

on stderr, `raise SystemExit(2)` — exit 2 = refused input/configuration, deliberately distinct from the
install-failure path, which rolls back and re-raises. Every offending byte is named with its offset; the
message never truncates the root, and the root is a local filesystem path (no secret content).

### D4 — The allowlist gains an argv mode; the routing entry migrates to it

The installed `coord_policy.py` gets one baked constant and one new rule list:

```python
HARNESS_HOME = "__SET_AGENTS_ROOT__"                       # baked by install.py (D2)
APP_CLI = HARNESS_HOME + "/ai/scripts/set_agents_app.py"

SAFE_ARGV = [                                              # (interpreters, script, first-flag)
    ({"python3", "python"}, APP_CLI, re.compile(r"--rout(e|ing)-\S+")),
]
```

`allowed()` keeps its existing pre-filters in the same order — empty/newline, `FORBIDDEN_SYNTAX`,
`FORBIDDEN_OPTIONS`, then `shlex.split` — and inserts the argv rule between the split and the legacy
regex pass:

```python
try:
    argv = shlex.split(command)
except ValueError:
    return False                    # unbalanced quotes: unchanged, still a deny
if _argv_allowed(argv):
    return True
return any(re.fullmatch(pattern + r".*", command) for pattern in SAFE)
```

`_argv_allowed` requires `len(argv) >= 3`, `argv[0] in interpreters`, `argv[1] == script` by **exact string
equality**, and `flag.fullmatch(argv[2])`. Trailing arguments stay unconstrained, exactly as
`re.fullmatch(pattern + r".*")` leaves them today, and `FORBIDDEN_SYNTAX`/`FORBIDDEN_OPTIONS` still ran over
the raw string first. Decisions inside this shape:

- **Which patterns migrate: exactly one today** — `r"python3 ai/scripts/set_agents_app\.py --rout(e|ing)-\S+"`
  (`coord_policy.py:34`) is REMOVED from `SAFE` and re-expressed in `SAFE_ARGV`. Removal is mandatory, not
  cosmetic: after the split, the relative string `ai/scripts/set_agents_app.py` denotes a PROJECT-side path,
  and leaving it allowlisted would sanction a path the harness no longer controls. P2's `--context*`
  (ORQ-1) joins `SAFE_ARGV` as a second tuple with a read-only comment; nothing else moves.
- **What stays a raw-string regex:** the other 15 `SAFE` entries (`git status`, `rg`, `cat`, …) and
  `r"python3 ai/scripts/feature-state\.py \S+"` (`:27`). The `feature-state.py` entry stays RELATIVE on
  purpose — it is the PROJECT-side channel, resolved against the orchestrator's `cwd` (D1). These entries
  embed no harness path, so quoting is not a practical concern for them.
- **`shlex.split` raising** (unbalanced quotes) keeps its current meaning: deny, no exception escapes. It is
  already the first thing `allowed()` does after the syntax filters (`:59-62`); the argv mode reuses the
  same parse rather than parsing twice.
- **No normalization of `argv[1]`.** `./ai/scripts/…`, a symlinked equivalent, or a `$HOME`-expanded variant
  all DENY. This is not a regression (today only one exact literal matches) and it keeps the sanctioned
  surface a single auditable string.
- **The tracked copy is fail-closed by construction:** in `Global/claude-code/hooks/coord_policy.py`,
  `APP_CLI` is literally `"__SET_AGENTS_ROOT__/ai/scripts/set_agents_app.py"`, which matches no real
  invocation. A regression test asserts that the TRACKED copy allows nothing on that channel and that the
  INSTALLED copy allows the quoted-with-space form.
- **Honest scope limit.** This fixes SET-AGENTES's own hook (`claude_bash_guard.py:9` imports
  `coord_policy.allowed`). The OpenCode/Claude *permission-glob* layer is matched by those runtimes, not by
  us; with a space in `HARNESS_HOME`, a quoted invocation may fall through their glob to `ask` (a prompt)
  rather than `allow`. That degrade is safe (never a silent allow) and is stated here rather than
  over-promised: `generate.py` emits the baked absolute pattern, and the space case is regression-locked
  only where we own the matcher.

### D5 — `find_project_root(start)`

```
candidates = [start] + list(start.resolve().parents)        # self-inclusive (AC-03)
for candidate in candidates:
    if candidate == candidate.parent:      # filesystem root
        break                              # '/' is never a PROJECT_ROOT, marker or not
    if (candidate / "ai/state/features").is_dir():  return candidate
    if (candidate / ".git").exists():               return candidate   # file OR dir (worktrees)
return None
```

- **Both markers are evaluated at EACH level before ascending** (nearest-ancestor-wins). Never
  marker-by-marker across all levels: a stray `~/ai/state/features/` would otherwise outrank the real
  repo's own nearer `.git` and widen the confinement anchor (D6) to the whole home directory.
- **`/` is never a valid `PROJECT_ROOT`**, even if it carries a marker. An anchor of `/` is no confinement
  at all. The walk stops there and returns unresolved.
- **`.git` may be a file** (submodule/worktree gitlink), hence `.exists()`, not `.is_dir()`.
- **Precedence, most to least specific: `--project DIR` > `SET_AGENTS_PROJECT` > walk-up.**
- **An explicit override that does not resolve is an ERROR, never a degrade.** If `--project` (or
  `SET_AGENTS_PROJECT`) names a path that does not exist, is not a directory, is `/`, or carries NEITHER
  marker: `ROUTING_INPUT_INVALID`, exit 2, no fallback to the walk-up. Two reasons: (a) "explicit always
  wins" is meaningless if an invalid explicit value silently hands control back to discovery; (b) the
  allowlisted routing channel ends in `--rout(e|ing)-\S+` plus unconstrained trailing arguments, so an agent
  *can* append `--project /` — requiring a marker and banning `/` bounds the anchor to real project roots
  and makes the widening attempt a hard, audited failure. (`find_vault`'s explicit branch,
  `set_agents_app.py:1019-1021`, degrades to `None` instead; that precedent is deliberately NOT followed
  here, because a vault is optional context whereas `PROJECT_ROOT` is a security anchor.)
- **Resolution is memoized once per process** and never re-resolved mid-run.
- **Unresolved ⇒ degrade, never a fallback to `HARNESS_HOME`-as-project** (AC-08): the envelope is 004's
  existing `ROUTING_UNAVAILABLE` shape, exit 1, plus the free-form warning string
  `PROJECT_ROOT_UNRESOLVED` in the envelope's `warnings` list. **No new reason code is introduced in P1** —
  `cli_envelope`'s `reason_codes` set stays closed (`routing.py:42-43`); `warnings` is already an open list
  (`legacy_warnings`, `routing.py:45-56`) and is the right place for a diagnosis that is not a decision.
- **A scaffolded directory with `ai/state/features/` and NO `.git` resolves normally** — the state marker
  alone suffices; this is explicitly NOT a degrade case (AC-08, AC-09 case 4).
- **Harness-internal propagation.** A child process cannot mutate its parent's environment, so exporting
  `SET_AGENTS_PROJECT` from `set_agents_app.py` cannot propagate a discovered root back to the Pi spawner.
  `set_agents_spawn.py` therefore receives the narrow approved exception: `_run_app_cli(..., cwd=...)`
  accepts an optional cwd (defaulting to `ROOT` for existing callers), and `route_and_spawn` resolves one
  `routing_cwd` from `spawn_cwd` or its process cwd. It passes that same value to `--route-decide`,
  `--route-dispatched`, and every normal or best-effort `--route-terminal` close. `APP_CLI` remains an
  absolute harness path; Pi itself still executes with the original `spawn_cwd`. This is the minimal change
  that makes the lifecycle's persisted `dispatches.project_key` belong to the user project.

### D6 — SEC-A02 re-anchored, with a trust-level change

`_validate_context_pack_path` (`set_agents_app.py:140-155`) and `_resolve_context_pack` (`:185-205`,
`state_dir = ROOT / "ai/state/features"` at `:191`) re-anchor from `ROOT` to `PROJECT_ROOT`. The
`os.path.commonpath` confinement and the "traversal outside ⇒ no pack, never a bare `ROOT / pack` join"
guarantee are preserved verbatim. What CHANGES is the trust level: `ROOT` is the harness's own audited
tree; `PROJECT_ROOT` is a repo a user merely `cd`-ed into.

**The discovered root is a CONFINEMENT BOUNDARY, never a GRANT OF TRUST.** Finding `.git` two levels up
says "reads stay inside this directory". It says nothing about the directory's contents being safe to act
on.

**Exhaustive list of paths P1 may read under `PROJECT_ROOT`** (anything not listed is out of bounds):

1. `<PROJECT_ROOT>/ai/state/features/<id>.json`, opened directly when `<id>` matches `_SAFE_STATE_ID`
   (`^[A-Za-z0-9._-]+$`, `:124`) — never a glob (N10, preserved).
2. `<PROJECT_ROOT>/ai/state/features/*.json`, non-recursive, sorted, **at most 256 entries**; a directory
   with more entries resolves to `CONTEXT_UNRESOLVED` instead of an unbounded scan.
3. `<PROJECT_ROOT>/ai/state/project.json` — the project identity file (D7).
4. The context-pack path itself: **`lstat` only, never opened.** Verified: `_package_context_ok`
   (`:158-183`) stats for `S_ISREG`/`S_ISLNK` and compares `st_mtime`; P1 never reads pack CONTENT. P2's
   `--context` is a different surface with its own caps (AC-18).

**Numeric caps (measurable, not aspirational):**

| Limit | Value | Basis |
|---|---|---|
| Max bytes read per feature-state JSON | 1 MiB (1 048 576) | largest real state file in this repo is 96 180 bytes (`ai/state/features/004-adaptive-dispatch.json`); ~10x headroom |
| Max `*.json` entries scanned per resolution | 256 | this repo has 4 |
| Max length of any value echoed to an agent (`feature_id`, `package_id`) | 64 chars | longest real id is 22 (`005-portable-harness`) |
| Charset of any echoed value | `^[A-Za-z0-9._-]{1,64}$` (`_SAFE_STATE_ID`) | already the harness's own id grammar |

A file exceeding the byte cap is treated exactly like a malformed one: `_load_feature_doc` returns `None`
(existing degrade), no partial parse, no exception.

**The injection path this closes, traced end to end.** `cmd_route_decide` writes
`data["feature_id"] = resolved_feature; data["package_id"] = resolved_package` into the printed JSON
envelope (`set_agents_app.py:288`). In the default-resolution branch `resolved_feature` is
`doc.get("feature_id")` and `resolved_package` is `doc.get("current_package_id")`
(`:203`, `:222-225`) — values read from the JSON file and **never validated against `_SAFE_STATE_ID`**
(only the CALLER-supplied ids are, at `:196` and `:202`). Today that content comes from the harness's own
tree; after the re-anchor it comes from a third-party repo, and it lands verbatim in text an agent reads.
**Decision: both values are validated against the charset+length rule above at the moment they leave the
doc; a value that fails is emitted as `null`, never as raw bytes.** The envelope's key set is unchanged
(`null` is already the shape used for an unresolved package, `:268`).

**Symlink treatment (paths that leave the project):**

- `<PROJECT_ROOT>/ai`, `ai/state`, `ai/state/features` must each be a REAL directory (`lstat`, not a
  symlink). A symlinked state directory degrades to "no pack"/"no identity" — it is the one hop that would
  move the whole read set outside the confinement boundary in a single step.
- Every read under `PROJECT_ROOT` uses `os.open(path, os.O_RDONLY | os.O_NOFOLLOW)`. Today
  `_load_feature_doc` (`:132-137`) uses `Path.read_text()`, which FOLLOWS symlinks: after the re-anchor,
  `ai/state/features/x.json -> ~/.pi/agent/auth.json` would read a credential surface and could surface
  bytes from it into the envelope. `O_NOFOLLOW` closes that; a symlink there degrades to `None`.
- The already-`lstat`-based `S_ISLNK` rejection of the pack path (`:171-172`) is preserved unchanged.

**Framing, stated for the security-auditor's re-derivation:** everything read under `PROJECT_ROOT` is
**DATA to be reasoned about, never instructions to follow**. No content read from `PROJECT_ROOT` may be
concatenated into an agent's directives, and the only values that cross into the envelope are the two
constrained identifiers above. A `feature-state.json` that contains prose telling the orchestrator to do
something is a string in a JSON field, nothing more.

### D7 — Project identity and `project_key`

**Primary: a persisted id file.** `<PROJECT_ROOT>/ai/state/project.json`, written once by the P1 scaffold
(D10), mode 0644, content:

```json
{"schema": 1, "project_key": "proj1_<32 lowercase hex>", "created_at": "<ISO-8601 UTC>"}
```

- **Format `proj1_` + 32 hex (38 chars total)** mirrors the existing `run1_` convention
  (`store.py:15`, `_RUN = ^run1_[0-9a-f]{32}$`) so the DB CHECK reads the same way as the one beside it.
- **JSON, not a bare line**, because every other artifact under `ai/state/` is JSON and a bare file invites
  whitespace mutations; `schema` allows a future field without a format guess.
- **Generated with `secrets.token_hex(16)`** — random, not derived. It carries NO path, NO username, NO
  machine identity: a value that may appear in envelopes and logs must not fingerprint the user's
  directory layout (a path hash is dictionary-guessable).
- **It is meant to be COMMITTED** with the project. Two clones of the same repo therefore share one
  `project_key` — correct, because they are the same project, and it is precisely what makes the key
  survive a move, a rename, or a re-clone (ORQ-2's stated purpose).
- **Missing ⇒ path-hash fallback** (below), documented as a fallback.
- **Present but CORRUPT (unparseable, wrong schema, key failing `^proj1_[0-9a-f]{32}$`) ⇒ NOT the same as
  missing.** No silent fallback: routing degrades with `ROUTING_UNAVAILABLE` + warning
  `PROJECT_IDENTITY_INVALID`. Falling back to a path hash here would silently split one project's history
  into two identities and hand the reviewer-independence check a key that matches nothing — a fail-open
  disguised as resilience.

**Fallback: hash of the normalized resolved path.**
`"proj1_" + sha256(b"set-agents-project-v1\x00" + normalized.encode("utf-8", "surrogateescape")).hexdigest()[:32]`,
where `normalized` is:

1. `os.path.realpath(PROJECT_ROOT)` — symlinks and `..` resolved;
2. `unicodedata.normalize("NFC", …)` — macOS filesystems return NFD, so the same directory typed in NFC
   would otherwise hash differently;
3. lowercased **only when the filesystem is case-insensitive**, detected concretely: `lstat` the final
   component and `lstat` the same component with `str.swapcase()` applied, in the same parent, and compare
   `(st_dev, st_ino)`. Equal inode ⇒ case-insensitive. If the component has no cased character or the probe
   raises, fall back to the platform default (`sys.platform in {"darwin", "win32"}` ⇒ case-insensitive) —
   a last resort, because APFS can be case-sensitive.

The domain-separation prefix keeps this hash from colliding with any other sha256 the harness computes.

**Reserved NIL key: `proj1_` + 32 zeros** (`proj1_00000000000000000000000000000000`). Never issued
(generation rejects it), used as the column DEFAULT (D8) and treated by every scoped read as matching
nothing.

**Fail-CLOSED independence.** `RoutingStore` binds `project_key` at construction (mirroring `_bind_issuer`,
`store.py:38-40`) so no call path can forget it:

- every write (`_authorize_issued`, `store.py:224-241`) stores it;
- `implementation_identity(run_id)` (`:373-379`) additionally requires the row's `project_key` to equal the
  bound key and raises `RoutingError("REVIEW_IDENTITY_INVALID")` otherwise. This is the exact fail-closed
  point: `service.py:124-125` already maps ANY `RoutingError` from that call to a
  `REVIEW_IDENTITY_INVALID` exclusion, so a cross-project reviewer request DENIES with no new branch;
- `recent_writers()` (`:365-371`) filters `WHERE project_key = ?`;
- **"no prior runs in this project" is NOT a mismatch and NOT a special case.** There is simply no writer
  run to match against, so independence is trivially unsatisfiable and the SAME denial fires
  (`REVIEW_IDENTITY_INVALID`), identical in shape to a mismatch. No "first run in a project" exemption
  exists — that exemption would be the fail-open.
- `open_runs()` (`:356-363`) stays GLOBAL and keeps its exact dict shape `{run_id, state, age_ms}`. It is an
  operator hygiene surface for the router as a whole; scoping it would hide a stuck run in project A from
  the operator standing in project B, and it returns no cross-project content beyond an opaque run id under
  a same-UID threat model (ADR-0005). `metric_rollups` and `events` likewise stay global and gain NO
  `project_key`: model quality is a property of the provider/model pair, and adding a key to `events` would
  create a cross-project join surface with no consumer.

### D8 — SCHEMA 4 → 5 migration

**Column.** Exact text, defined ONCE as a module constant and used verbatim by BOTH `_create_schema` and
the migration's `ALTER` (single source of truth — the two texts MUST be identical for D8's core invariant to
hold):

```
project_key TEXT NOT NULL DEFAULT 'proj1_00000000000000000000000000000000' CHECK(project_key GLOB 'proj1_[0-9a-f]*' AND length(project_key)=38)
```

Its position in `_create_schema` is fixed: **immediately after `updated_at INTEGER NOT NULL,`
(`store.py:128`) and before the first table-level `CHECK` (`:129`).** That position is not cosmetic. It is
what `ALTER TABLE … ADD COLUMN` produces, verified empirically against sqlite 3.53.3: SQLite rewrites the
stored `CREATE TABLE` text by inserting the new column definition at the end of the LAST COLUMN
DEFINITION, keeping the trailing table-level constraints after it. Since `_validate_existing_readonly`
(`store.py:168-187`) compares the whitespace-normalized, lowercased `sqlite_master` text against a pristine
`_create_schema`, any other position makes every migrated DB permanently `ROUTING_UNAVAILABLE`.

**Why a NIL sentinel DEFAULT instead of `''`.** Also verified empirically: `ALTER TABLE … ADD COLUMN` with
a CHECK constraint FAILS (`CHECK constraint failed`) when the column's DEFAULT does not satisfy the CHECK
and the table is non-empty. `DEFAULT ''` with a format CHECK is therefore impossible on a live DB. The NIL
sentinel satisfies the CHECK, is never issued as a real key, and makes any row that somehow keeps it
fail-closed for every scoped read.

**Index.** `DROP INDEX dispatches_review;` then
`CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at);` — the exact canonical
text, name unchanged. Column order and its reasoning:

- `project_key` LEADS because every project-scoped query has an EQUALITY predicate on it; an equality
  column first is what lets the index prune to one project's rows.
- `(role,state,terminal_at)` is preserved verbatim as the suffix — a minimal delta that removes no existing
  access path.
- Rejected: appending `project_key` LAST — the index could not prune by project, so the reviewer-identity
  query would scan every project's rows, which is the exact cost this feature exists to remove.
- Rejected: a second index, or swapping `role` for `role_class`. Recorded honestly: `recent_writers`
  filters `role_class`, not `role` (`store.py:370`), and no current query filters `role` at all, so the
  suffix is currently non-selective — a PRE-EXISTING condition, not one introduced here. YAGNI threshold to
  revisit: >5 000 `dispatches` rows for a single `project_key`, or a measured p90 of
  `--routing-recent-writers` above 50 ms.

**Trigger: explicit operator command, never automatic.** `_validate_schema`'s `schema_version != SCHEMA`
check (`store.py:150`) stays fail-closed and is NOT taught to auto-migrate. Instead:

- routing commands add the free-form warning `ROUTING_SCHEMA_MIGRATION_REQUIRED` when a read-only,
  no-follow probe sees `schema_version == 4`;
- a new operator command performs the migration and prints
  `ROUTING_MIGRATE_OK from=4 to=5 rows=<n> backup=<path>`.

Rationale: ADR-0005's doctrine is that state-changing recovery is operator-driven; an auto-migration would
make every ordinary `--route-decide` a potential schema writer, and a crash mid-migration during a routine
spawn is strictly worse than an explicit degrade with printed instructions.

**Preconditions (checked before anything is written).** `<HARNESS_HOME>/ai/state/project.json` must exist
and be valid — the backfill value is the harness's OWN persisted key, never a path hash, so the harness's
historical rows survive a future move of the clone. Missing ⇒ exit 2 telling the operator to scaffold the
harness first. Consequence for sequencing: **T-108/T-109 (scaffold) must land before T-107's migration is
runnable.**

**Backup, before any `ALTER`.** A SQLite-CONSISTENT copy via `sqlite3.Connection.backup()` from a
read-only connection — never a raw file copy, which without the WAL sidecar is not a consistent snapshot
(ADR-0005 already declares WAL sidecars part of the backup procedure). Destination:
`<routing root>/backups/routing-v4-<UTC YYYYmmddTHHMMSSZ>.db`, directory created `0700` under `umask 0077`,
file `0600`, inside the existing private root. The backup is then verified — `PRAGMA integrity_check` ==
`ok`, `schema_version` == `4`, `COUNT(*) FROM dispatches` equal to the source — before the transaction
opens. Backups are never auto-pruned (one small file, irreplaceable).

**One transaction, self-verifying.**

```
BEGIN EXCLUSIVE;
  -- re-read schema_version inside the transaction; abort unless it is exactly '4'
  ALTER TABLE dispatches ADD COLUMN <the exact coldef above>;
  UPDATE dispatches SET project_key = :harness_key;            -- ALL rows, no WHERE
  DROP INDEX dispatches_review;
  CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at);
  UPDATE meta SET value='5' WHERE key='schema_version';
  -- compare the normalized sqlite_master text against the canonical SCHEMA-5 DDL,
  -- INSIDE the transaction; ROLLBACK on any difference
COMMIT;
```

- `BEGIN EXCLUSIVE` matches `_create_schema`'s own pattern (`store.py:120`); with `busy_timeout=0`
  (`:115`) a concurrent writer fails immediately rather than interleaving. DDL is transactional in SQLite,
  so the equality check sees the uncommitted schema and a mismatch rolls the whole thing back with the DB
  untouched. Nothing is verified only AFTER `COMMIT`.
- **The backfill has no `WHERE`: every pre-existing row, including rows still in `authorized` or
  `dispatched` (non-terminal) state, gets the harness's key.** Every row in this DB predates project scoping
  and was, by the definition of the bug this feature fixes, produced by invocations running inside the
  harness repo. Leaving non-terminal rows at the NIL sentinel would strand in-flight runs as
  permanently un-closable.
- Post-`COMMIT` failure of any kind is reported to the operator with the backup path. There is no automatic
  restore — consistent with ADR-0005's "recovery requires an integrity-checked backup, never automatic
  recreation".

**Required regression (the linchpin proof, not an assertion of intent):** a schema-4 DB built from a frozen
copy of the v4 DDL, migrated by this procedure, must produce a `sqlite_master` DDL dict byte-identical
(after the same normalization) to a pristine schema-5 `_create_schema()`. If that test does not exist and
PASS, the migration is not done.

**Backward incompatibility, documented and correct.** A pre-005 checkout (SCHEMA=4) opening a schema-5 DB
fails closed at `store.py:150` (`meta["schema_version"] != str(SCHEMA)`) and degrades to
`ROUTING_UNAVAILABLE`. This is CORRECT and is not a new failure mode: it is the same fail-closed
schema-mismatch doctrine 004 already applies to schema-2/3 databases. The alternative — a version-tolerant
reader — would mean an old binary writing rows without a `project_key`, i.e. rows that silently defeat the
scoping this ADR exists to create. Downgrading the harness therefore requires restoring the migration
backup; that is the stated cost.

### D9 — `build.sh --check`'s internal drift check (the THIRD kind of drift)

`build.sh:57-59`'s `check)` branch is empty today (verified: `--check` regenerates into staging at
`:53-55` and compares nothing). It gains exactly one comparison:

- `PROYECTO/ai/scripts/feature-state.py` vs `ai/scripts/feature-state.py`
- `PROYECTO/ai/scripts/check-owned-paths.py` vs `ai/scripts/check-owned-paths.py`

byte-for-byte (`cmp -s`). Output: `SELF_SCAFFOLD_SYNC_OK files=2` on success; on failure one line per file,
`SELF_SCAFFOLD_DRIFT file=ai/scripts/<name> template=PROYECTO/ai/scripts/<name> reason=<differs|missing>`,
exit 1.

The three drift checks are DIFFERENT and must never be conflated:

| Check | Compares | Direction | Where |
|---|---|---|---|
| `check-drift.sh` | the live install under `$HOME` vs what the repo would install (`install.py --preview`'s `MANAGED_DIFF_FILES`) | installed vs repo | post-commit git hook |
| `verify.sh:13-16` | tracked `Global/**` vs `build.sh --output` regeneration | tracked vs regenerated | `verify.sh` |
| **this one (new)** | `PROYECTO/ai/scripts/{feature-state,check-owned-paths}.py` vs the harness's own copies | template vs harness self-scaffold | `build.sh --check` |

Cross-package obligation (ORQ-6), restated because this check is what will enforce it: P2 edits the
`PROYECTO/` template for ORQ-3/AC-13 and MUST re-sync the harness's copy before P2's gates, or this check
starts failing mid-P2.

### D10 — P1 scaffold scope and idempotency for a STATE directory

`set-agents --scaffold [DIR]`, P1 portion, creates exactly three things:

1. `<DIR>/ai/state/features/` (`mkdir(parents=True, exist_ok=True)`);
2. `<DIR>/ai/scripts/feature-state.py` and `<DIR>/ai/scripts/check-owned-paths.py`, copied from
   `PROYECTO/ai/scripts/`, create-if-missing;
3. `<DIR>/ai/state/project.json` (D7).

**No vault, no Obsidian, no link — that is P2** (ORQ-6). P1 must be acceptable on its own.

**Why exactly those two scripts** (and not `sync-project.sh`'s seven-name `GENERIC` array): verified,
`bootstrap_project.py:20` already copies `run.sh, verify.sh, loop.sh, e2e.sh, mcp.sh, audit-readonly.sh`
from the same templates, so five of the seven already have an owner. The two Python state scripts are the
exact gap that NEITHER existing script fills, and `brave-cdp-mcp.sh` is only needed by projects using that
MCP (`sync-project.sh` remains its path). Copying the five again here would create a second source of truth
for the same files.

**Idempotency semantics for a state directory** (no precedent existed — `bootstrap_project.py`'s `FILES`
dict is for docs, `:23-61`, `:94-103`):

- an existing `ai/state/features/` is left ALONE: never emptied, never re-permissioned, never touched
  beyond `exist_ok=True`. It holds live feature state; "re-scaffold" is not a reset;
- an existing generic script with IDENTICAL bytes ⇒ skip; with DIFFERENT bytes ⇒ **conflict, never
  overwritten** (mirrors `bootstrap_project.py`'s `conflicts` list). Upgrading a diverged copy is
  `sync-project.sh`'s job — it does backups and validates in-flight feature state first
  (`sync-project.sh:23-30`);
- an existing VALID `project.json` ⇒ skip (this is what makes re-running safe). An existing INVALID one ⇒
  conflict, never regenerated: regenerating would re-key the project and orphan every routing row it owns.

Reported observables, one line per item, mirroring the existing `VAULT_INIT_OK`/`VAULT_INIT_SKIP` style:
`SCAFFOLD_CREATED path=…`, `SCAFFOLD_SKIP path=…`, `SCAFFOLD_CONFLICT path=… reason=…`, and a final
`SCAFFOLD_OK project=<dir> project_key=<key>` (exit 0) or `SCAFFOLD_CONFLICTS n=<count>` (exit 1). The
final line prints the `project_key`, which is what AC-09 asserts against.

### Scale / Data / Security decisions

- **Data store:** unchanged — local relational SQLite at the fixed private root of ADR-0005. This feature
  adds ONE column and re-derives ONE index inside that database. No second store, no per-project database,
  no vector/document/KV store: there is no similarity-search or schemaless requirement anywhere in P1.
  Threshold to revisit: a measured need to query across machines (would require a remote store, a
  separately approved decision), or single-file contention proven by real `SQLITE_BUSY` rates (`busy_timeout=0`
  makes them immediately visible today).
- **API Gateway:** not yet — YAGNI, and reaffirmed. There is no remotely exposed service; the "API" is a
  local CLI. It would be warranted only by multiple remotely exposed backends needing centralized authn,
  rate limiting, and observability.
- **Deploy platform:** none — this is a locally installed runtime. Vercel/PaaS, VPS/IaaS, and managed
  hosting all remain out of scope. Portability here means "any path on any developer machine", not
  "deployed anywhere". Reconsider only with an approved remote control plane.
- **Queue / cache / CDN / replica / shard:** not yet — YAGNI. `PROJECT_ROOT` resolution is memoized per
  process (the only caching introduced, bounded to one value). A queue would require measured asynchronous
  backpressure; a cache, a profiled hot read with safe invalidation; replicas, primary read saturation;
  sharding, proven single-database capacity exhaustion. None is observed.
- **Security (decided day one, never deferred):**
  - *Least privilege / isolation:* `PROJECT_ROOT` is a confinement boundary, not a trust grant (D6). The
    read set under it is an exhaustive four-item list with numeric caps, `O_NOFOLLOW` on every read, and a
    real-directory requirement on `ai/`, `ai/state/`, `ai/state/features/`. `/` is never a valid anchor and
    an explicit `--project` must carry a marker, which closes the agent-supplied `--project /` widening.
  - *Sanctioned surface:* the allowlist stays an exact interpreter+script pair; the literal `set-agents`
    wrapper is still NOT allowlisted; `install.py` refuses a root whose bytes could widen a permission glob
    (D3).
  - *Fail-closed everywhere:* corrupt project identity, cross-project reviewer identity, schema mismatch,
    unresolved `PROJECT_ROOT`, and an unsubstituted placeholder each DENY/degrade; none falls back to a
    broader scope.
  - *Recovery:* the SCHEMA 4→5 migration is operator-triggered, backed by a verified SQLite-consistent
    snapshot, self-verifying inside its own transaction, and never auto-restores.
  - *Secrets:* nothing added here reads or logs a credential surface; `O_NOFOLLOW` specifically prevents a
    planted symlink under `ai/state/features/` from turning a state read into a credential read.

## Alternativas descartadas

- **Bake at generate/build time** (contract 1.0.0's implied mechanism). Rejected with evidence: it commits
  the builder's absolute path into tracked `Global/**` and makes `verify.sh:13-16` unpassable on every
  other machine. This is the finding that nearly sank the feature; it is a first-order constraint here.
- **Reuse the JSON escape for non-JSON targets.** Rejected: `json.dumps(str(REPO_ROOT))[1:-1]` escapes
  non-ASCII to `\uXXXX`, which is correct inside a JSON string and wrong inside a Markdown prompt body or a
  permission glob. Hence the explicit `json_escaped` flag rather than one global escape.
- **Substitute only in the write path, leaving `--preview` unsubstituted.** Rejected: it produces a
  permanent phantom `MANAGED_DIFF_FILES > 0`, i.e. a permanent `DRIFT_DETECTED` badge from
  `check-drift.sh:22-27` on every commit.
- **Regex-escape the baked path into the existing `SAFE` regex.** Rejected: the value would need three
  simultaneous escapings (Python literal + regex + the surrounding permission syntax). Moving the rule to
  an argv comparison removes the path from the regex domain entirely.
- **Normalize/realpath `argv[1]` before comparing.** Rejected: it widens the sanctioned surface to an
  open-ended family of equivalent spellings for no operational gain.
- **Keep the relative `python3 ai/scripts/set_agents_app.py --rout…` entry in `SAFE` "for compatibility".**
  Rejected: post-split, that relative path denotes a PROJECT-side file the harness does not control.
- **Refuse to install on a `HARNESS_HOME` containing a space.** Rejected: it is the ordinary macOS/Windows
  case and refusing it would make the portability promise hollow. The argv matcher handles it.
- **`--project` that fails to resolve degrades to the walk-up** (the `find_vault` precedent,
  `set_agents_app.py:1019-1021`). Rejected: an explicit value that silently returns control to discovery
  is not "explicit wins", and it re-opens the anchor-widening path.
- **`project_key` derived only from the path** (contract 1.0.0). Rejected: it breaks on move/rename and
  fingerprints the user's directory layout. Path hash survives as an explicit fallback only.
- **Regenerate a corrupt `project.json`.** Rejected: it silently re-keys a project and orphans its routing
  history — a fail-open dressed as self-healing.
- **`ALTER TABLE … ADD COLUMN project_key TEXT NOT NULL DEFAULT ''` with a format CHECK.** Rejected with
  empirical evidence: SQLite refuses the ALTER when the default violates the CHECK on a non-empty table.
- **Table rebuild (`CREATE TABLE dispatches_new …; INSERT … SELECT; DROP; ALTER … RENAME`).** Rejected with
  empirical evidence: `ALTER TABLE … RENAME TO` rewrites the stored DDL with the table name QUOTED
  (`CREATE TABLE "dispatches" (…)`), which no longer equals the canonical `_create_schema` text and would
  make `_validate_existing_readonly` reject the migrated DB forever.
- **`PRAGMA writable_schema=ON` to hand-edit `sqlite_master`.** Rejected: hazardous by construction, and it
  bypasses the very integrity checks this store is built on.
- **Rebuild the whole DB file and `os.replace` it.** Rejected: it discards the WAL/SHM identity checks the
  store performs before and after connecting (`store.py:196-200`) and races any concurrent reader holding
  the old file, for no benefit over the in-place ALTER once the column position is fixed.
- **Auto-migrate on first connect.** Rejected: it turns every routine `--route-decide` into a potential
  schema writer.
- **Add `project_key` to `events`/`metric_rollups`.** Rejected: rollups are deliberately global (model
  quality is a provider/model property) and an `events` key would create a cross-project join surface with
  no consumer.
- **Scope `open_runs()` per project.** Rejected: it would hide a stuck run in project A from the operator
  standing in project B, and it would change a 004 envelope's meaning for no security gain under the
  same-UID threat model.
- **Copy all seven `sync-project.sh` `GENERIC` scripts in `--scaffold`.** Rejected: five already belong to
  `bootstrap_project.py:20`; duplicating them creates a second source of truth for the same files.

## Implementer contract

MUST hold (any violation is a package-review blocker):

1. `Global/**` tracked NEVER contains a machine-specific absolute path; the placeholder survives every
   `generate`/`build`. R1/R2/R3 of D2 are the executable form of that statement.
2. `verify.sh` stays green from a fresh clone at ANY path (AC-09 case 5).
3. The `--doctor --harness pi` envelope (`set_agents_app.py:359-368`) is BYTE-IDENTICAL. Zero branches
   added to `cmd_doctor`.
4. `cli_envelope`'s `reason_codes` vocabulary is UNCHANGED (`routing.py:42-43`). New diagnoses go in
   `warnings`.
5. `RoutingStore`'s root stays `~/.local/state/set-agentes/routing-v2` derived from
   `pwd.getpwuid(os.getuid()).pw_dir` (`store.py:23-29`), unchanged. ADR-0005 is not amended.
6. `metric_rollups` and `events` stay global and unkeyed; identity/independence checks read only
   `dispatches`.
7. The literal `set-agents` never enters the allowlist.
8. `tests/test_harness.py:1637` and the JSON substitution path keep passing unchanged.
9. `install.py`'s manifest semantics, backup/rollback flow, and pruning fence (`:195-211`) are untouched.
10. `set_agents_spawn.py` changes only by D5's explicit routing-cwd propagation; no store, allowlist,
    metric-rollup, doctor-envelope, or read-only guard behavior changes.
11. Sequencing: T-108/T-109 (scaffold + harness self-scaffold) land BEFORE T-107's migration is runnable;
    the migration refuses to run without `<HARNESS_HOME>/ai/state/project.json`.
12. No opportunistic refactors; no public API/data-contract change beyond the ones enumerated in D1–D10.

Review gates this change must pass: `python3 -m unittest discover -s tests -v` (net assertion count never
shrinks) · `./build.sh --check` (now including D9) · `py_compile` of `ai/scripts/*.py` and
`routing_core/*.py` · `./ai/scripts/verify.sh` → `VERIFY_PASS` (now including D2's R1/R2/R3) ·
`git diff --check` · ownership vs the package baseline · the migration DDL-equality regression named in D8 ·
`security-auditor` on the P1 panel for D6 (mandatory) · AC-09 executed by `gate-runner`/`package-reviewer`,
never self-attested by the implementer.

## Consecuencias

- The harness becomes usable from any repo at any path, and the tracked tree stays machine-independent —
  but correctness now depends on an install step that MUST have run: an artifact copied by hand instead of
  installed keeps the placeholder and is fail-closed (allows nothing), by design.
- The coord allowlist has two matching modes. Any future entry that embeds a harness path MUST use the argv
  mode; adding one to `SAFE` would silently reintroduce the quoting defect.
- `PROJECT_ROOT` becomes a security anchor, so its resolution rules (both markers per level, `/` excluded,
  explicit-but-invalid is an error) are security-relevant code, not convenience code, and belong under
  regression test.
- The routing DB gains a per-project dimension while remaining a single global file: telemetry stays global,
  identity is scoped, and downgrading the harness below 005 requires restoring the migration backup.
- Reviewer independence now denies in one more situation (cross-project). This is intended and is the only
  direction the change moves — never toward granting.
- Three distinct drift checks now exist. Their scopes are documented in D9 precisely so a future failure is
  read against the right one.
- P2 inherits two obligations: re-sync the harness's `feature-state.py` copy after editing the template
  (D9), and add `--context*` to `SAFE_ARGV` (never to `SAFE`) when it lands ORQ-1.

## Contract vs repo discrepancies (found while verifying, resolved above)

1. **AC-01's "ZERO absolute filesystem paths in `Global/**`" is false today.**
   `Global/_canonical/opencode-agents/package-gate-runner.md` (+ its compiled copy) carry
   `/home/federico/iey/iey-ai/...` literals, and every shipped script has a `/usr/bin/env` shebang.
   Resolved by D2's R1/R2/R3 (ratchet + placeholder + no-builder-path) instead of the unimplementable
   literal. The gate-runner literals are a PRE-EXISTING portability defect outside P1's ownership and are
   flagged for a follow-up.
2. **`sync-project.sh:14`'s `GENERIC` list is at line 17 and has SEVEN entries**, not the two AC-06 names;
   five of them are already copied by `bootstrap_project.py:20`. Resolved by D10 (copy exactly the two
   Python scripts that no existing script copies).
3. **`install.py:69-72`** — the substitution is at lines 71-72 (69-70 are the comment); `REPO_ROOT` is at
   line 58.
4. **`set_agents_spawn.py:285-291` runs the app CLI with `cwd=ROOT` (the harness)** and is a real
   `--route-decide` caller (`:343`). The context pack does not mention that this silently mis-scopes
   `PROJECT_ROOT`. Resolved by D5's `SET_AGENTS_PROJECT` export, which needs no edit to that non-owned file.
5. **`_validate_existing_readonly` (`store.py:168-187`) enforces byte-exact DDL equality.** Neither the spec
   nor the context pack mentions it, and it invalidates the two obvious migration strategies (see
   "Alternativas descartadas"). It is the single hardest constraint in T-107.
6. **`_load_feature_doc` follows symlinks and reads unbounded** (`set_agents_app.py:132-137`), and
   `feature_id`/`current_package_id` read FROM the doc are echoed into the envelope WITHOUT the
   `_SAFE_STATE_ID` validation applied to caller-supplied ids (`:203`, `:222-225`, `:288`). Harmless while
   anchored at the harness; a real injection/credential-read path once anchored at a third-party
   `PROJECT_ROOT`. Resolved by D6.
7. **`set_agents_app.py:28-30`'s comment credits ADR-0006 for the fixed routing root**; the actual decision
   is ADR-0005 (`0006` is AM-1/AM-2). Cosmetic, not corrected here (comment-only, outside this ADR's
   deliverable).
8. **`docs/adr/README.md` was missing rows for ADR-0006 and ADR-0007**, contrary to its own
   "one row per ADR, no exceptions" rule. Backfilled together with this ADR's row.
