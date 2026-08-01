# Context pack — 007-P1 `schema-normalize`

Delimited by structure, not by a file list: the surface is the **DDL normalization and validation family** of
`ai/scripts/routing_core/store.py` — the canonical generator, the two comparison sites, and the migration's
post-`ALTER` equality check — plus the three lines of `cmd_routing_migrate` that give the failure a voice, and
the ADR paragraph that currently overstates what the comparison is.

There is **no `PROYECTO/` twin of `routing_core/`**. `build.sh --check` compares an explicit hardcoded list of
exactly two files (`feature-state.py`, `check-owned-paths.py`), so no drift gate looks at this module at all;
`verify.sh:19` only `py_compile`s it.

## The defect, and why it is not one machine's problem

`store.py` normalizes stored DDL with `" ".join(text.split()).lower()` in three places (`:170`, `:187`,
`:278`). That collapses whitespace and lowercases, and **preserves SQL comments**. `ALTER TABLE ADD COLUMN`
keeps the original `CREATE TABLE` text in `sqlite_master`. So a comment added to the canonical DDL *after* a
database was created blocks that database's migration permanently — for **every prior installation**, not just
the one where it was diagnosed (decision `routing-db-schema4-unmigratable`, which cost a full session).

The only comments in the entire schema are the three `-- N03:` lines at `store.py:140-142`, inside
`CREATE TABLE dispatches (...)`, between the CHECK at `:139` and the CHECK at `:143` that they document.

## What the two real backups actually contain, verified

The two files under `~/.local/state/set-agentes/routing-v2/backups/routing-v4-*.db` were opened read-only
(`?immutable=1`) and their `dispatches` DDL has **neither** the `-- N03:` comments **nor** the
`CHECK(state<>'abandoned' OR …)` clause. They are an AC-05 case — genuine structural divergence — not an
AC-03 one. The user decided to discard them; P1 recovers nothing. `routing.db` itself is absent from that
directory (only an empty `-wal` and an orphan `-shm` remain), so live routing creates a clean schema-5
database and works.

## The two traps, both measured against the real canonical DDL

- **Order is not free.** Stripping comments *after* the whitespace collapse destroys the newline that
  terminates a `--` comment, so the comment swallows the rest of the statement: `dispatches` drops from 2581
  to **2081** normalized characters, taking every following CHECK with it. That number is not a coincidence —
  the original diagnosis recorded that "the divergence starts at character 2082". Comments first, then
  whitespace, then case.
- **`[` inside `'…'`.** The canonical contains `CHECK(run_id GLOB 'run1_[0-9a-f]*' …)` (`store.py:131`) and
  `PROJECT_KEY_COLUMN` (`store.py:20`) contains `'proj1_[0-9a-f]*'`. A scanner that lets `[` open a
  bracket-quoted identifier *while already inside a single-quoted literal* flips quote parity and never
  recovers: the `-- N03:` block reads as string content and **survives** (2843 characters instead of 2581).
  The failure is not visible garbage — it is the canonical DDL keeping its own comment, which breaks AC-03
  while every test that creates a database and reopens it stays green.

## Invariants the package must not break

- **Comment-free DDL must normalize byte-for-byte as it does today.** Steps 2 and 3 are the existing
  expression verbatim, including its pre-existing lossiness: `.lower()` applies to string literals and the
  whitespace collapse reaches inside them. Both are lossy and both are load-bearing — changing either changes
  which databases on disk validate.
- **`ROUTING_UNAVAILABLE` stays the public reason code on the divergence path.** `domain.py:9` calls it "a
  stable public reason code; never attach host/provider detail";
  `test_schema_drift_fails_closed_byte_identically` (`tests/test_routing.py:649-661`) pins it on a *missing
  index*, which is itself an AC-05 case; and `--routing-migrate`'s output contract is pinned by ADR-0008 D8.
  The diagnostic travels beside the code, never instead of it. This is also the only reading under which
  AC-04 and AC-05 do not contradict each other — see the 1.2.0 amendment log.
- **Canonical names are ours and get printed; anything else is theirs and is a number.**
  `sqlite_master.name` comes from a file an attacker may have written: it can carry newlines, ANSI escapes,
  arbitrary length, and need not even be `str`. `missing` and `altered` are subsets of seven compile-time
  constants by construction; unexpected objects are a count and nothing else.
- **The comparison condition does not move.** Today it is dict inequality over the normalized maps; it becomes
  "any missing, altered or unexpected". Same set, neither loosened nor tightened. An altered `CHECK` must
  still be refused, or the repair is indistinguishable from weakening the control.
- **Migration stays all-or-nothing.** Everything from the `ALTER` to the equality check lives inside one
  `BEGIN EXCLUSIVE`; the verified backup path (`store.py:243-266`: online backup, `integrity_check`, version
  re-check, row count) is untouched.
- **The frozen schema-4 fixture stays a historical artifact.** It must not be regenerated from
  `_create_schema` — deriving it makes every test that uses it tautological. That is finding F-07 of this
  contract's own challenge, which already caught the same trap once. The only production value it imports is
  `PROJECT_KEY_COLUMN`, because that shared string is exactly what makes 4→5 work.
- **Nothing patches `_normalize_ddl` or touches `RoutingStore._canonical_ddl`.** That memo (`store.py:161`) is
  a class attribute that is never invalidated: a patched normalizer either reads a warm memo and proves
  nothing, or leaves a poisoned canonical behind for every later test in the process.

## Out of scope, recorded rather than fixed

The trigger/view blindness of `_validate_schema` (`type='table'` only, DDL comparison `type IN
('table','index')`) is untouched: AC-07 corrects the prose that oversold the control, not the control
(`routing-ddl-validation-blind-to-triggers`). AC-14 — a version-generic `migration_required()` and real
`from`/`to` in the migrate CLI — belongs to P2 and is not stolen. `done_ready`'s blocker-truthiness bug is
side-stepped by this feature's re-init, not repaired. `_canonical_ddl` never being invalidated is harmless
with one `SCHEMA` per process and becomes worth revisiting when P2 raises it to 6.
