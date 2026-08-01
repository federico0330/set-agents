from __future__ import annotations

import decimal
import os
import pwd
import re
import secrets
import sqlite3
import stat
import sys
import time
import datetime as dt
from pathlib import Path
from .domain import ImplementationIdentity, RoutingError

SCHEMA = 7
_RUN = re.compile(r"^run1_[0-9a-f]{32}$")
_PROJECT_KEY = re.compile(r"^proj1_[0-9a-f]{32}$")
NIL_PROJECT_KEY = "proj1_00000000000000000000000000000000"
_TEST_PROJECT_KEY = "proj1_11111111111111111111111111111111"
PROJECT_KEY_COLUMN = "project_key TEXT NOT NULL DEFAULT 'proj1_00000000000000000000000000000000' CHECK(project_key GLOB 'proj1_[0-9a-f]*' AND length(project_key)=38)"
# The SAME vocabulary as cost-report.py's FIELDS, mapped mechanically as "usage_" + field.
# Deliberately no translation table: a table between two vocabularies drifts silently, and
# cost-report.py cannot be imported (zero repo-local imports, and a hyphenated filename is
# not a module name), so the equality is pinned by a test instead.
USAGE_TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write", "reasoning")
USAGE_STATUSES = ("ok", "absent", "invalid")
# ONE ordered sequence with two consumers -- `_create_schema` splices it and the 5->6 step
# emits one ALTER per element, in this order.  AC-09's coupling becomes arithmetic instead
# of discipline: there is no second hand-maintained list to keep in step.
#
# WHERE THIS SITS IS LOAD-BEARING.  `ALTER TABLE ADD COLUMN` inserts after the LAST column
# definition and before the first table constraint, so these are declared immediately after
# `project_key` and a future schema 7 must extend after `usage_status` -- anywhere else and
# the post-migration DDL differs from canonical, which no test that merely creates a
# database and reopens it can see.  That is the 4->5 defect 007-P1 exists to have closed.
#
# The `>= 0` CHECKs are corruption detectors, not input validation: `_usage_row` binds only
# NULL or a validated non-negative int, so the write path cannot violate them.  That
# matters because a violated CHECK raises inside close_run's transaction and would ROLLBACK
# the close, and AC-11's invariant is that the run closes no matter what the usage says.
USAGE_COLUMNS = tuple(
    f"usage_{field} INTEGER CHECK(usage_{field} IS NULL OR usage_{field} >= 0)"
    for field in USAGE_TOKEN_FIELDS
) + (
    "cost_micros INTEGER CHECK(cost_micros IS NULL OR cost_micros >= 0)",
    "usage_status TEXT CHECK(usage_status IS NULL OR usage_status IN ('ok','absent','invalid'))",
)
USAGE_COLUMNS_SQL = ", ".join(USAGE_COLUMNS)
# Bare column names, derived rather than hand-listed a second time: `close_run` binds these
# in `_usage_row`'s order on BOTH UPDATE branches.
_USAGE_COLUMN_NAMES = tuple(definition.split()[0] for definition in USAGE_COLUMNS)
_USAGE_SET_CLAUSE = ",".join(f"{name}=?" for name in _USAGE_COLUMN_NAMES)
_IDENTITY = ("route_id", "runtime", "provider", "model", "family", "effort")
# The columns an authorization writes, in the order `_authorize_issued` binds them.  Named
# explicitly so widening `dispatches` never again silently requires widening that tuple.
_AUTHORIZED_COLUMNS = (
    "run_id", "role", "role_class",
    *(f"selected_{part}" for part in _IDENTITY),
    *(f"fallback_{part}" for part in _IDENTITY),
    *(f"actual_{part}" for part in _IDENTITY),
    "state", "partial_write", "fallback_window_open", "fallback_consumed",
    "authorized_at", "dispatched_at", "partial_write_at", "fallback_consumed_at", "terminal_at",
    "updated_at", "project_key",
)

# Exclusive: the JSON safe-integer ceiling on the STORED micro-dollar figure, not on the
# dollar amount that arrives. Read the other way this collides with AC-11: 2**53-1 *dollars*
# converts to ~9.0e21 micros, which overflows SQLite's 2**63-1 bind limit and rolls the close
# back -- measured, and the one shape of input that would keep a run from ever closing.
_COST_MICROS_BOUND = 2 ** 53


def _cost_micros(total) -> int | None:
    """AC-12: round-half-up to the nearest micro-dollar, on the provider's own decimal text.

    `total` is expected to be the `decimal.Decimal` that `parse_usage` produced with
    `parse_float=decimal.Decimal` -- never a value that went through a plain float. Half a
    micro-dollar written as `0.0000005` is `4.999...e-7` once it has been through an
    IEEE754 float, so both `round()` and `Decimal(float)+ROUND_HALF_UP` give 0 where the text
    the provider actually wrote rounds to 1; only parsing from text keeps the rule
    well-defined. `scaleb(6)` shifts the decimal point rather than multiplying, so no
    precision is lost converting to micros before rounding.

    Never raises. Returns None for anything unusable -- wrong type, negative, unconvertible,
    non-finite, out of bounds -- and `_usage_row` treats None as "discard the whole usage"
    (AC-11).

    007-P2 review finding (F-SEC-01/F-PR-01, both reviewers independently, upheld by
    finding-verifier): `json.loads` accepts the bare `NaN`/`Infinity` JSON literals through
    `parse_constant`, which `parse_float=decimal.Decimal` never intercepts -- `total` can
    arrive as a real `float('nan')`/`float('inf')`, which `str()` turns into `Decimal('NaN')`/
    `Decimal('Infinity')` without error. `Decimal('NaN') < 0` then raises
    `decimal.InvalidOperation` (an `ArithmeticError`, not caught by `close_run`'s
    `except (OverflowError, sqlite3.Error)`), and `int(Decimal('Infinity'))` raises the
    BUILTIN `OverflowError` -- a different class than `decimal.Overflow` -- which the second
    `try` below did not catch either. Either shape left the run permanently `dispatched`
    instead of closing with `usage_status='invalid'`. `is_finite()` is checked before any
    comparison or conversion touches the value, closing both paths at once.
    """
    if isinstance(total, bool) or not isinstance(total, (int, decimal.Decimal, float)):
        return None
    try:
        value = total if isinstance(total, decimal.Decimal) else decimal.Decimal(str(total))
    except (decimal.InvalidOperation, ValueError):
        return None
    if not value.is_finite() or value < 0:
        return None
    try:
        micros = int(value.scaleb(6).to_integral_value(rounding=decimal.ROUND_HALF_UP))
    except (decimal.InvalidOperation, decimal.Overflow):
        return None
    return micros if 0 <= micros < _COST_MICROS_BOUND else None


# Pi's own wire format is not internally consistent: a real spawn observed 2026-07-29
# reports `{"input":3321,"output":5,"reasoning":0,"totalTokens":3326,"cacheRead":0,
# "cacheWrite":0,"cost":{...}}` -- input/output/reasoning/totalTokens are plain, but the two
# cache fields are camelCase. Looking them up under our snake_case column names alone would
# silently leave `usage_cache_read`/`usage_cache_write` NULL even when Pi explicitly reports
# them as 0, which is indistinguishable from Pi never having sent them at all -- exactly the
# NULL-vs-0 confusion AC-08 exists to prevent, just moved one level up into the parser.
_USAGE_FIELD_ALIASES = {"cache_read": ("cache_read", "cacheRead"), "cache_write": ("cache_write", "cacheWrite")}


def _usage_field_key(usage, field):
    for key in _USAGE_FIELD_ALIASES.get(field, (field,)):
        if key in usage:
            return key
    return None


def _usage_row(usage) -> tuple:
    """AC-11: the store's half of the two-edge split -- parseable but untrustworthy usage
    never aborts `close_run`; it is discarded and the discard is recorded, never silent.

    Returns a 7-tuple in `USAGE_COLUMNS` order: the five nullable token counts, then
    `cost_micros`, then `usage_status`.

    `usage` is `None` or `{}` for the two failure closes that never spawned -- `spawn()`
    itself returns `usage or {}`, so `{}` is the ordinary "provider reported nothing" case,
    not an error -- and that is `absent`, never `invalid`.

    Any single untrustworthy value -- a non-integer or negative token count, a `totalTokens`
    that does not match the sum of the fields actually present, an unconvertible cost --
    discards the ENTIRE usage rather than storing a partially-trusted mix:
    `usage_status='invalid'` IS the record of the discard, so nothing beneath it is kept.

    A field simply absent from an otherwise-good usage stays NULL and the status stays
    `'ok'` -- NULL means "not reported", 0 means "reported as zero", and Pi reporting no
    cache/reasoning keys at all is the ordinary case this whole package exists to make
    visible rather than fabricate away.
    """
    all_null = (None,) * (len(USAGE_TOKEN_FIELDS) + 1)
    if not usage:
        return all_null + ("absent",)
    if not isinstance(usage, dict):
        return all_null + ("invalid",)
    tokens: dict = {}
    for field in USAGE_TOKEN_FIELDS:
        key = _usage_field_key(usage, field)
        if key is None:
            continue
        value = usage[key]
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return all_null + ("invalid",)
        tokens[field] = value
    total_tokens = usage.get("totalTokens")
    if total_tokens is not None:
        if isinstance(total_tokens, bool) or not isinstance(total_tokens, int) or total_tokens < 0:
            return all_null + ("invalid",)
        if total_tokens != sum(tokens.values()):
            return all_null + ("invalid",)
    cost_micros = None
    if "cost" in usage:
        cost = usage["cost"]
        if not isinstance(cost, dict) or "total" not in cost:
            return all_null + ("invalid",)
        cost_micros = _cost_micros(cost["total"])
        if cost_micros is None:
            return all_null + ("invalid",)
    return tuple(tokens.get(field) for field in USAGE_TOKEN_FIELDS) + (cost_micros, "ok")


_EVENT_TYPES = {"authorized", "dispatched", "partial", "fallback", "terminal", "rejected", "abandoned"}
_OUTCOMES = {"success", "failure", "none"}
_SCHEMA_OBJECTS = "SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL"
# `[` closes with `]` and has no escape at all; the other three double themselves.
_DDL_DELIMITERS = {"'": "'", '"': '"', "`": "`", "[": "]"}


def _normalize_ddl(text: str) -> str:
    """The one DDL normalizer (007 AC-01/AC-02).

    Comments are stripped FIRST and the pre-existing whitespace/case collapse is then
    applied verbatim, so comment-free DDL normalizes byte for byte as it always did --
    including its lossiness inside string literals, which is load-bearing: changing it
    would change which databases already on disk validate.  The order is not a style
    choice.  Collapsing whitespace first destroys the newline that terminates a `--`
    comment, and the comment then swallows the rest of the statement: `dispatches` drops
    from 2581 normalized characters to 2081, taking every following CHECK with it.

    The scan is delimiter-aware over all four SQLite quoting forms, and the reason is
    correctness, not security -- whoever can write the database file can write canonical
    DDL directly (ADR-0005 amendment).  `CHECK(run_id GLOB 'run1_[0-9a-f]*' ...)` below
    puts a `[` inside a single-quoted literal; letting it open a bracket-quoted identifier
    flips quote parity for the rest of the statement and the `-- N03:` block survives
    normalization, silently defeating AC-03 while every test that creates a database and
    reopens it stays green.

    Never raises on malformed text: an unterminated quote or `/*` is consumed to the end
    of input.  SQLite would not have stored unparseable DDL, so that branch means the file
    is corrupt or hand-written; the only obligations are to terminate and not to compare
    equal to canonical, and stripping can only remove text.
    """
    if not isinstance(text, str):
        raise RoutingError("ROUTING_UNAVAILABLE")
    out: list[str] = []
    index = 0
    size = len(text)
    while index < size:
        char = text[index]
        closer = _DDL_DELIMITERS.get(char)
        if closer is not None:
            # A quoted run is copied verbatim: nothing inside it opens a comment, and
            # nothing inside it opens another delimiter.
            out.append(char)
            index += 1
            while index < size:
                if text[index] != closer:
                    out.append(text[index])
                    index += 1
                    continue
                if closer != "]" and text.startswith(closer * 2, index):
                    out.append(closer * 2)
                    index += 2
                    continue
                out.append(closer)
                index += 1
                break
            continue
        if text.startswith("--", index):
            newline = text.find("\n", index)
            index = size if newline < 0 else newline
            out.append(" ")  # a comment separates two tokens; it is never nothing
            continue
        if text.startswith("/*", index):
            end = text.find("*/", index + 2)
            index = size if end < 0 else end + 2
            out.append(" ")
            continue
        out.append(char)
        index += 1
    return " ".join("".join(out).split()).lower()


class SchemaDivergence(RoutingError):
    """`ROUTING_UNAVAILABLE`, plus which canonical object diverged (007 AC-05).

    `str()` is still exactly the stable public reason code, so every `except RoutingError`,
    every envelope and every assertion on the message is unchanged; the detail rides in
    attributes and reaches an operator only through the migration CLI.  That is not a
    stylistic choice: AC-04 requires this same input -- a removed CHECK -- to keep being
    refused with `ROUTING_UNAVAILABLE`, so "not a bare ROUTING_UNAVAILABLE" in AC-05 can
    only mean "not unaccompanied".

    Only canonical object names are ever named, and they are compile-time constants.  A
    name that is not canonical came from the database file, which a hostile or corrupt
    writer controls -- it can carry newlines, terminal escapes and arbitrary length -- so
    it is counted and never echoed.  Canonical names are ours and get printed; anything
    else is theirs and is a number.
    """

    def __init__(self, missing=(), altered=(), unexpected=0):
        super().__init__("ROUTING_UNAVAILABLE")
        self.missing = tuple(missing)
        self.altered = tuple(altered)
        self.unexpected = int(unexpected)
        self.schema_diagnostic = (
            "SCHEMA_DIVERGED missing=" + (",".join(self.missing) or "none")
            + " altered=" + (",".join(self.altered) or "none")
            + f" unexpected={self.unexpected}"
        )


class RoutingStore:
    """Private POSIX SQLite adapter; root injection is test composition only."""
    def __init__(self, root: Path | None = None, filesystem_supported: bool = True, project_key: str | None = None):
        self._test_root = root is not None
        # The production root comes from the account database, not $HOME, so the
        # environment cannot redirect where durable authorizations live.
        home = Path(pwd.getpwuid(os.getuid()).pw_dir) if os.name == "posix" else Path.home()
        self.root = home / ".local/state/set-agentes/routing-v2" if root is None else Path(root)
        self.db_path = self.root / "routing.db"
        self.filesystem_supported = filesystem_supported
        self._issuer = None
        self.project_key = project_key or (_TEST_PROJECT_KEY if self._test_root else NIL_PROJECT_KEY)
        if not _PROJECT_KEY.fullmatch(self.project_key):
            raise RoutingError("ROUTING_UNAVAILABLE")

    @classmethod
    def _for_tests(cls, root: Path, filesystem_supported: bool = True, project_key: str | None = None):
        """Private test composition seam; production has no caller-selected root."""
        return cls(root, filesystem_supported, project_key)

    def _bind_issuer(self, issuer):
        if self._issuer is not None: raise RoutingError("AUTHORIZATION_INVALID")
        self._issuer = issuer

    @staticmethod
    def new_run_id() -> str: return "run1_" + secrets.token_hex(16)

    def _check_supported(self):
        if os.name != "posix" or sys.platform.startswith("win") or not self.filesystem_supported: raise RoutingError("ROUTING_UNAVAILABLE")

    @staticmethod
    def _private_dir(path: Path, leaf: bool = False):
        st = path.lstat()
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISDIR(st.st_mode): raise RoutingError("ROUTING_UNAVAILABLE")
        if leaf and (st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o700): raise RoutingError("ROUTING_UNAVAILABLE")
        # Some supported user namespaces expose host-root as the overflow uid (65534).
        # It is trusted only for ancestors; the managed leaf still must be this uid's 0700 directory.
        if not leaf and st.st_uid not in {0, os.getuid(), 65534}: raise RoutingError("ROUTING_UNAVAILABLE")
        if not leaf and (stat.S_IMODE(st.st_mode) & 0o022) and not (st.st_mode & stat.S_ISVTX): raise RoutingError("ROUTING_UNAVAILABLE")

    def ensure_cache_root(self) -> Path:
        """AM-2/F06: create-or-validate the private cache root, never the DB file.

        Reuses the exact same private-directory discipline as the store
        (never chmod/adopt a foreign existing directory); a caller that
        catches `RoutingError` here degrades to fresh, uncached probing.
        """
        self._safe_dir(create=True)
        return self.root

    def _safe_dir(self, create: bool):
        self._check_supported()
        parts = self.root.parts
        current = Path(parts[0]) if self.root.is_absolute() else Path(".")
        for index, piece in enumerate(parts[1:] if self.root.is_absolute() else parts):
            current /= piece; leaf = index == len(parts[1:] if self.root.is_absolute() else parts) - 1
            try: self._private_dir(current, leaf)
            except FileNotFoundError:
                if not create: raise RoutingError("ROUTING_UNAVAILABLE")
                # Parent was checked on the preceding iteration; create private, never chmod an existing object.
                old = os.umask(0o077)
                try: current.mkdir(mode=0o700)
                except FileExistsError: self._private_dir(current, leaf)
                finally: os.umask(old)
                self._private_dir(current, leaf)

    def _file_fingerprint(self, path: Path, required: bool = False):
        try: st = path.lstat()
        except FileNotFoundError:
            if required: raise RoutingError("ROUTING_UNAVAILABLE")
            return None
        if stat.S_ISLNK(st.st_mode) or not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or stat.S_IMODE(st.st_mode) != 0o600:
            raise RoutingError("ROUTING_UNAVAILABLE")
        return (st.st_dev, st.st_ino, stat.S_IFMT(st.st_mode), st.st_uid, stat.S_IMODE(st.st_mode))

    def _existing_valid(self) -> bool:
        try: self.db_path.lstat(); return True
        except FileNotFoundError: return False

    def _create_new(self):
        old=os.umask(0o077)
        try: fd=os.open(self.db_path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
        except FileExistsError: return False
        finally: os.umask(old)
        os.close(fd)
        try:
            c=sqlite3.connect(f"file:{self.db_path}?mode=rw", uri=True, isolation_level=None, timeout=0)
            self._configure(c); self._create_schema(c); c.execute("COMMIT"); c.close()
        except Exception:
            # A failed first initialization deliberately leaves an unavailable state; no retry/repair occurs.
            try: c.close()
            except Exception: pass
            raise RoutingError("ROUTING_UNAVAILABLE")
        return True

    def _configure(self, c):
        if c.execute("PRAGMA journal_mode=WAL").fetchone()[0].lower() != "wal": raise sqlite3.DatabaseError
        c.execute("PRAGMA synchronous=FULL"); c.execute("PRAGMA foreign_keys=ON"); c.execute("PRAGMA busy_timeout=0")

    @staticmethod
    def _create_schema(c):
        c.executescript("""
BEGIN EXCLUSIVE;
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE dispatches (
 run_id TEXT PRIMARY KEY CHECK(run_id GLOB 'run1_[0-9a-f]*' AND length(run_id)=37), role TEXT NOT NULL, role_class TEXT NOT NULL CHECK(role_class='writer'),
 selected_route_id TEXT NOT NULL, selected_runtime TEXT NOT NULL, selected_provider TEXT NOT NULL, selected_model TEXT NOT NULL, selected_family TEXT NOT NULL, selected_effort TEXT NOT NULL,
 fallback_route_id TEXT, fallback_runtime TEXT, fallback_provider TEXT, fallback_model TEXT, fallback_family TEXT, fallback_effort TEXT,
 actual_route_id TEXT, actual_runtime TEXT, actual_provider TEXT, actual_model TEXT, actual_family TEXT, actual_effort TEXT,
 state TEXT NOT NULL CHECK(state IN ('authorized','dispatched','terminal_success','terminal_failure','abandoned')), partial_write INTEGER NOT NULL DEFAULT 0 CHECK(partial_write IN (0,1)), fallback_window_open INTEGER NOT NULL CHECK(fallback_window_open IN (0,1)), fallback_consumed INTEGER NOT NULL DEFAULT 0 CHECK(fallback_consumed IN (0,1)),
     authorized_at INTEGER NOT NULL, dispatched_at INTEGER, partial_write_at INTEGER, fallback_consumed_at INTEGER, terminal_at INTEGER, updated_at INTEGER NOT NULL, """ + PROJECT_KEY_COLUMN + ", " + USAGE_COLUMNS_SQL + """, replacement_of_run_id TEXT REFERENCES dispatches(run_id), terminal_outcome TEXT,
 CHECK((fallback_route_id IS NULL AND fallback_runtime IS NULL AND fallback_provider IS NULL AND fallback_model IS NULL AND fallback_family IS NULL AND fallback_effort IS NULL) OR (fallback_route_id IS NOT NULL AND fallback_runtime IS NOT NULL AND fallback_provider IS NOT NULL AND fallback_model IS NOT NULL AND fallback_family IS NOT NULL AND fallback_effort IS NOT NULL)),
 CHECK((actual_route_id IS NULL AND actual_runtime IS NULL AND actual_provider IS NULL AND actual_model IS NULL AND actual_family IS NULL AND actual_effort IS NULL) OR (actual_route_id IS NOT NULL AND actual_runtime IS NOT NULL AND actual_provider IS NOT NULL AND actual_model IS NOT NULL AND actual_family IS NOT NULL AND actual_effort IS NOT NULL)),
 CHECK(state IN ('authorized','abandoned') OR actual_route_id IS NOT NULL),
 -- N03: abandoned is a never-dispatched close — it can never carry an actual (dispatched)
 -- identity. Its close timestamp is `updated_at` (documented here): `terminal_at`'s ordering
 -- CHECK below requires dispatched_at, which a never-dispatched row never has.
 CHECK(state<>'abandoned' OR (actual_route_id IS NULL AND actual_runtime IS NULL AND actual_provider IS NULL AND actual_model IS NULL AND actual_family IS NULL AND actual_effort IS NULL)),
 CHECK(state NOT IN ('terminal_success','terminal_failure','abandoned') OR fallback_window_open=0),
 CHECK(dispatched_at IS NULL OR dispatched_at>=authorized_at),
 CHECK(terminal_at IS NULL OR (dispatched_at IS NOT NULL AND terminal_at>=dispatched_at)),
 CHECK(fallback_consumed=0 OR fallback_route_id IS NOT NULL));
CREATE TABLE events (event_id INTEGER PRIMARY KEY, occurred_at INTEGER NOT NULL, event_type TEXT NOT NULL, route_id TEXT, runtime TEXT, provider TEXT, model TEXT, family TEXT, outcome TEXT NOT NULL, reason_family TEXT NOT NULL, latency_ms INTEGER, latency_bucket TEXT NOT NULL);
CREATE TABLE metric_rollups (route_key TEXT NOT NULL, runtime TEXT NOT NULL, provider TEXT NOT NULL, model TEXT NOT NULL, family TEXT NOT NULL, outcome TEXT NOT NULL, reason_family TEXT NOT NULL, latency_bucket TEXT NOT NULL, lifetime_count INTEGER NOT NULL, lifetime_latency_sum_ms INTEGER NOT NULL, compacted_count INTEGER NOT NULL, exclusion_count INTEGER NOT NULL, fallback_offered_count INTEGER NOT NULL, fallback_consumed_count INTEGER NOT NULL, fallback_success_count INTEGER NOT NULL, fallback_failure_count INTEGER NOT NULL, PRIMARY KEY(route_key,runtime,provider,model,family,outcome,reason_family,latency_bucket));
CREATE TABLE provider_exhaustions (provider TEXT PRIMARY KEY, expires_at INTEGER NOT NULL);
 CREATE INDEX events_retention ON events(occurred_at,event_id); CREATE INDEX events_route_retention ON events(route_id,occurred_at,event_id); CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at); CREATE UNIQUE INDEX dispatches_one_replacement ON dispatches(replacement_of_run_id) WHERE replacement_of_run_id IS NOT NULL;
""")
        c.execute("INSERT INTO meta VALUES('schema_version',?)", (str(SCHEMA),)); c.execute("INSERT INTO meta VALUES('installation_hmac_salt',?)", (secrets.token_hex(32),))

    def _validate_schema(self, c):
        quick=c.execute("PRAGMA integrity_check").fetchone()
        tables={row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        meta=dict(c.execute("SELECT key,value FROM meta")) if "meta" in tables else {}
        if quick != ("ok",) or tables != {"meta","dispatches","events","metric_rollups","provider_exhaustions"} or meta.keys() != {"schema_version","installation_hmac_salt"} or meta["schema_version"] != str(SCHEMA) or len(meta["installation_hmac_salt"]) != 64:
            raise RoutingError("ROUTING_UNAVAILABLE")

    _canonical_ddl = None

    @classmethod
    def _canonical_schema_sql(cls):
        """Normalized DDL of a pristine schema; the single source of truth for validation."""
        if cls._canonical_ddl is None:
            c = sqlite3.connect(":memory:", isolation_level=None)
            try:
                cls._create_schema(c); c.execute("COMMIT")
                cls._canonical_ddl = {name: _normalize_ddl(text) for name, text in c.execute(_SCHEMA_OBJECTS)}
            finally:
                c.close()
        return cls._canonical_ddl

    @classmethod
    def _ddl_divergence(cls, found):
        """(missing, altered, unexpected_count) against the canonical DDL.

        The condition is identical to the dict inequality it replaces -- neither loosened
        nor tightened -- it just says which side of it failed.  A name absent from the
        canonical set is file-controlled, so it is counted here and never carried out.
        """
        canonical = cls._canonical_schema_sql()
        normalized = {}
        unexpected = 0
        for name, text in found:
            if name not in canonical:
                unexpected += 1
                continue
            normalized[name] = _normalize_ddl(text)
        missing = tuple(sorted(set(canonical) - set(normalized)))
        altered = tuple(sorted(name for name, text in normalized.items() if text != canonical[name]))
        return missing, altered, unexpected

    def _validate_existing_readonly(self):
        """Existing state is checked without journal/pragma writes before any RW open."""
        before = self._file_fingerprint(self.db_path, True)
        try:
            c = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, isolation_level=None, timeout=0)
            self._validate_schema(c)
            # Exact structural equality with the canonical DDL: columns, types,
            # NOT NULL, CHECK constraints, primary keys, and index definitions must all
            # match after normalization.  Comments are prose, not structure, and are the
            # only thing normalization is allowed to discard (007 AC-02).
            missing, altered, unexpected = self._ddl_divergence(c.execute(_SCHEMA_OBJECTS))
            if missing or altered or unexpected:
                raise SchemaDivergence(missing, altered, unexpected)
            c.close()
        except (sqlite3.Error, RoutingError) as exc:
            try: c.close()
            except Exception: pass
            # The single narrow exit: everything else is still flattened into the bare
            # reason code, so a driver error can never leak past `except RoutingError`.
            if isinstance(exc, SchemaDivergence): raise
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        if self._file_fingerprint(self.db_path, True) != before: raise RoutingError("ROUTING_UNAVAILABLE")

    @staticmethod
    def _stored_schema_version(c) -> int | None:
        """The ONE reader of `meta.schema_version`, as an int, or None if unreadable.

        Every version comparison in this file goes through here, so there is no second
        place that parses `meta` and no literal version left to go stale: before 007-P2
        the string `"4"` appeared in three separate guards and `'5'` was written back as a
        literal, which is why raising SCHEMA used to be a three-site edit that silently
        disabled the migration warning if any one was missed.
        """
        try:
            return int(dict(c.execute("SELECT key,value FROM meta")).get("schema_version"))
        except (TypeError, ValueError, sqlite3.Error):
            return None

    def migration_required(self) -> bool:
        """True for a securely opened database whose schema is BELOW the current one.

        Deliberately informational: normal routing still refuses an old schema and never
        writes or attempts an automatic migration.

        The comparison is `< SCHEMA`, never `!= SCHEMA`.  A file written by a NEWER
        harness must answer False — offering to "migrate" it would be offering a
        downgrade, and there is no step that could perform one.  A version that does not
        parse also answers False: garbage is `ROUTING_UNAVAILABLE`, which the open path
        already refuses, not an invitation to rewrite the file.
        """
        try:
            self._safe_dir(create=False)
            self._file_fingerprint(self.db_path, True)
            c = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True,
                                isolation_level=None, timeout=0)
            try:
                stored = self._stored_schema_version(c)
                return stored is not None and stored < SCHEMA
            finally:
                c.close()
        except (OSError, sqlite3.Error, RoutingError):
            return False

    def _connect(self):
        self._safe_dir(create=True)
        existed=self._existing_valid()
        if existed:
            self._file_fingerprint(self.db_path)
            self._validate_existing_readonly()
        else: self._create_new()
        before=self._file_fingerprint(self.db_path, True)
        try:
            c=sqlite3.connect(f"file:{self.db_path}?mode=rw", uri=True, isolation_level=None, timeout=0); self._configure(c); self._validate_schema(c)
            for sidecar in (self.db_path.with_name("routing.db-wal"), self.db_path.with_name("routing.db-shm")): self._file_fingerprint(sidecar)
            if self._file_fingerprint(self.db_path, True) != before: raise RoutingError("ROUTING_UNAVAILABLE")
            return c
        except RoutingError: raise
        except (OSError, sqlite3.Error) as exc: raise RoutingError("ROUTING_UNAVAILABLE") from exc

    def _migrate_4_to_5(self, c, harness_project_key):
        """Feature 005: project scoping."""
        c.execute("ALTER TABLE dispatches ADD COLUMN " + PROJECT_KEY_COLUMN)
        c.execute("UPDATE dispatches SET project_key = ?", (harness_project_key,))
        c.execute("DROP INDEX dispatches_review")
        c.execute("CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at)")

    def _migrate_5_to_6(self, c, harness_project_key):
        """Feature 007-P2: what the spawn cost.

        One ALTER per element of USAGE_COLUMNS, in that order, so the resulting text
        matches where `_create_schema` declares them.  There is no second list.
        """
        for definition in USAGE_COLUMNS:
            c.execute("ALTER TABLE dispatches ADD COLUMN " + definition)

    def _migrate_6_to_7(self, c, harness_project_key):
        """Feature 011: linked replacement and installation-global provider cooldown."""
        c.execute("ALTER TABLE dispatches ADD COLUMN replacement_of_run_id TEXT REFERENCES dispatches(run_id)")
        c.execute("ALTER TABLE dispatches ADD COLUMN terminal_outcome TEXT")
        c.execute("CREATE TABLE provider_exhaustions (provider TEXT PRIMARY KEY, expires_at INTEGER NOT NULL)")
        c.execute("CREATE UNIQUE INDEX dispatches_one_replacement ON dispatches(replacement_of_run_id) WHERE replacement_of_run_id IS NOT NULL")

    def migrate(self, harness_project_key: str) -> tuple[int, Path, int, int]:
        """Explicit, backup-first migration to the current SCHEMA; never automatic.

        Returns `(rows, backup_path, from_version, to_version)`.

        The whole chain runs inside ONE `BEGIN EXCLUSIVE` with a single DDL comparison at
        the end, and that is a necessity rather than a preference: the comparison is against
        `_canonical_schema_sql()`, which is always the CURRENT schema, so an intermediate
        check after 4->5 would compare a schema-5 database against schema-6 canonical and
        always fail.  Verifying intermediate states would need per-version canonical DDL
        frozen in this file — which is exactly the historical artifact the test tree keeps
        instead.  Atomicity is the second reason: separate transactions leave a crash window
        where the version says 5, the running code refuses the file, and the operator's only
        backup is a v4.  One transaction gives two outcomes and no third.

        `harness_project_key` stays required whatever steps run, even though only 4->5 uses
        it.  Making it conditional would LOOSEN ADR-0008 D8's stated precondition — a 5->6
        migration would newly succeed on a harness with no persisted identity.  The cost is
        a pointless refusal in that one case, accepted as scope discipline.
        """
        if not _PROJECT_KEY.fullmatch(harness_project_key) or harness_project_key == NIL_PROJECT_KEY:
            raise RoutingError("ROUTING_UNAVAILABLE")
        self._safe_dir(create=False)
        self._file_fingerprint(self.db_path, True)
        try:
            source = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, isolation_level=None, timeout=0)
            observed = self._stored_schema_version(source)
            if observed is None or observed >= SCHEMA or observed not in _MIGRATION_STEPS:
                raise RoutingError("ROUTING_UNAVAILABLE")
            rows = int(source.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0])
            backup_dir = self.root / "backups"
            old = os.umask(0o077)
            try:
                backup_dir.mkdir(mode=0o700, exist_ok=True)
            finally:
                os.umask(old)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            # Named for what is IN the file, not for where the chain was headed: if the
            # chain aborts, the destination never happened.
            backup = backup_dir / f"routing-v{observed}-{stamp}.db"
            destination = sqlite3.connect(backup)
            try:
                source.backup(destination)
            finally:
                destination.close()
            os.chmod(backup, 0o600)
            check = sqlite3.connect(f"file:{backup}?mode=ro", uri=True)
            try:
                if check.execute("PRAGMA integrity_check").fetchone() != ("ok",):
                    raise RoutingError("ROUTING_UNAVAILABLE")
                if self._stored_schema_version(check) != observed:
                    raise RoutingError("ROUTING_UNAVAILABLE")
                if int(check.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0]) != rows:
                    raise RoutingError("ROUTING_UNAVAILABLE")
            finally:
                check.close(); source.close()
            c = sqlite3.connect(f"file:{self.db_path}?mode=rw", uri=True, isolation_level=None, timeout=0)
            try:
                self._configure(c)
                c.execute("BEGIN EXCLUSIVE")
                # Re-read under the lock: the backup was taken outside it.
                version = self._stored_schema_version(c)
                if version != observed:
                    raise RoutingError("ROUTING_UNAVAILABLE")
                while version < SCHEMA:
                    step = _MIGRATION_STEPS.get(version)
                    if step is None:
                        raise RoutingError("ROUTING_UNAVAILABLE")
                    step(self, c, harness_project_key)
                    version += 1
                # The target is always the constant, never a literal: `'5'` written here by
                # hand is what made raising SCHEMA a multi-site edit before 007-P2.
                c.execute("UPDATE meta SET value=? WHERE key='schema_version'", (str(SCHEMA),))
                missing, altered, unexpected = self._ddl_divergence(c.execute(_SCHEMA_OBJECTS))
                if missing or altered or unexpected:
                    raise SchemaDivergence(missing, altered, unexpected)
                c.execute("COMMIT")
            except Exception:
                try: c.execute("ROLLBACK")
                except sqlite3.Error: pass
                raise
            finally:
                c.close()
            return rows, backup, observed, SCHEMA
        except RoutingError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise RoutingError("ROUTING_UNAVAILABLE") from exc

    @staticmethod
    def _now(): return int(time.time() * 1000)
    @staticmethod
    def _next_utc_day_ms(now_ms):
        now = dt.datetime.fromtimestamp(now_ms / 1000, tz=dt.timezone.utc)
        tomorrow = (now.date() + dt.timedelta(days=1))
        return int(dt.datetime.combine(tomorrow, dt.time.min, tzinfo=dt.timezone.utc).timestamp() * 1000)
    @staticmethod
    def _bucket(latency): return "none" if latency is None else ("0-99" if latency < 100 else "100+")
    def _event(self, c, event_type, identity=None, outcome="none", reason="none", latency=None, fallback=False, via_fallback=False):
        if event_type not in _EVENT_TYPES or outcome not in _OUTCOMES: raise RoutingError("AUTHORIZATION_INVALID")
        now=self._now(); route,runtime,provider,model,family,_effort = identity or (None,)*6
        c.execute("INSERT INTO events(occurred_at,event_type,route_id,runtime,provider,model,family,outcome,reason_family,latency_ms,latency_bucket) VALUES(?,?,?,?,?,?,?,?,?,?,?)", (now,event_type,route,runtime,provider,model,family,outcome,reason,latency,self._bucket(latency)))
        key=(route or "none", runtime or "none", provider or "none", model or "none", family or "none", outcome, reason, self._bucket(latency))
        # Every counter is incremented exactly once, at insertion time, in the same transaction as its event.
        exclusion = 1 if event_type == "rejected" else 0
        consumed = 1 if event_type == "fallback" else 0
        fb_success = 1 if (event_type == "terminal" and outcome == "success" and via_fallback) else 0
        fb_failure = 1 if (event_type == "terminal" and outcome == "failure" and via_fallback) else 0
        c.execute("INSERT INTO metric_rollups VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(route_key,runtime,provider,model,family,outcome,reason_family,latency_bucket) DO UPDATE SET lifetime_count=lifetime_count+1,lifetime_latency_sum_ms=lifetime_latency_sum_ms+excluded.lifetime_latency_sum_ms,exclusion_count=exclusion_count+excluded.exclusion_count,fallback_offered_count=fallback_offered_count+excluded.fallback_offered_count,fallback_consumed_count=fallback_consumed_count+excluded.fallback_consumed_count,fallback_success_count=fallback_success_count+excluded.fallback_success_count,fallback_failure_count=fallback_failure_count+excluded.fallback_failure_count", (*key,1,latency or 0,0,exclusion,1 if fallback else 0,consumed,fb_success,fb_failure))
        # Compaction shares the writer's transaction: the retention bound holds
        # at COMMIT and no separate connection re-runs integrity validation.
        self._compact_in(c, now)

    def _authorize_issued(self, run_id, nonce, identity, fallback, role, role_class, snapshot):
        if (not _RUN.fullmatch(run_id) or self._issuer is None or role_class != "writer"
                or not snapshot.identity_allowed(identity) or (fallback and not snapshot.identity_allowed(fallback))
                or not self._issuer.consume(nonce, identity, fallback, role, role_class, snapshot)):
            raise RoutingError("AUTHORIZATION_INVALID")
        c=self._connect()
        try:
            now=self._now(); c.execute("BEGIN IMMEDIATE")
            if c.execute("SELECT 1 FROM provider_exhaustions WHERE provider=? AND expires_at>?",
                         (identity[2], now)).fetchone():
                c.execute("ROLLBACK"); raise RoutingError("PROVIDER_EXHAUSTED")
            # Named, not positional.  This was `INSERT INTO dispatches VALUES(?…)` with no
            # column list, so every widening of the table silently required widening this
            # tuple too -- 007-P2 had to add seven columns and would have broken every
            # authorization.  Naming what it writes lets any future column default to NULL
            # without this line being touched again, which is the whole point.
            values=(run_id,role,role_class,*identity,*(fallback or (None,)*6),*(None,)*6,"authorized",0,1,0,now,None,None,None,None,now,self.project_key)
            c.execute("INSERT INTO dispatches (" + ",".join(_AUTHORIZED_COLUMNS) + ") VALUES(" + ",".join("?" for _ in values) + ")", values)
            self._event(c,"authorized",identity,fallback=fallback is not None); c.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            c.execute("ROLLBACK"); self._rejection_event(identity,"AUTHORIZATION_REPLAY"); raise RoutingError("AUTHORIZATION_REPLAY") from exc
        except sqlite3.Error as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            self._rejection_event(identity,"ROUTING_UNAVAILABLE"); raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()

    def provider_exhausted(self, provider, now_ms=None):
        """Read-only prefilter; authorization repeats this inside its immediate transaction."""
        if not isinstance(provider, str) or not provider:
            return True
        c=self._connect()
        try:
            now=self._now() if now_ms is None else now_ms
            return c.execute("SELECT 1 FROM provider_exhaustions WHERE provider=? AND expires_at>?",
                             (provider, now)).fetchone() is not None
        finally:c.close()

    def close_exhausted_and_authorize_replacement(self, run_id, classification, usage=None, latency_ms=None):
        """Atomically close an exact quota exhaustion and dispatch its one stored fallback.

        This is intentionally not a route decision: it never receives a catalog or a new
        identity.  The only candidate is the fallback identity durably stored at the first
        authorization, preserving both its original independence decision and the closed
        fallback window of the failed run.
        """
        if not _RUN.fullmatch(run_id) or classification != "quota_exhausted":
            raise RoutingError("AUTHORIZATION_INVALID")
        c=self._connect(); row=None
        try:
            now=self._now(); c.execute("BEGIN IMMEDIATE")
            existing=c.execute("SELECT run_id FROM dispatches WHERE replacement_of_run_id=?", (run_id,)).fetchone()
            if existing:
                c.execute("COMMIT"); return {"run_id": existing[0], "existing": True}
            row=c.execute("SELECT state,replacement_of_run_id,actual_route_id,actual_runtime,actual_provider,actual_model,actual_family,actual_effort,"
                          "fallback_route_id,fallback_runtime,fallback_provider,fallback_model,fallback_family,fallback_effort,"
                          "role,role_class,project_key FROM dispatches WHERE run_id=? AND project_key=?",
                          (run_id,self.project_key)).fetchone()
            if (not row or row[0] != "dispatched" or row[1] is not None
                    or any(value is None for value in row[2:8]) or any(value is None for value in row[8:14])
                    or row[15] != "writer"):
                c.execute("ROLLBACK"); raise RoutingError("FAILOVER_DENIED")
            original_identity=tuple(row[2:8]); fallback=tuple(row[8:14])
            expires_at=self._next_utc_day_ms(now)
            c.execute("INSERT INTO provider_exhaustions(provider,expires_at) VALUES(?,?) "
                      "ON CONFLICT(provider) DO UPDATE SET expires_at=excluded.expires_at",
                      (original_identity[2], expires_at))
            changed=c.execute("UPDATE dispatches SET state='terminal_failure',terminal_outcome='quota_exhausted',terminal_at=?,updated_at=?,"
                              + _USAGE_SET_CLAUSE + " WHERE run_id=? AND project_key=? AND state='dispatched'",
                              (now,now,*_usage_row(usage),run_id,self.project_key))
            if changed.rowcount != 1:
                c.execute("ROLLBACK"); raise RoutingError("STATE_CONFLICT")
            if c.execute("SELECT 1 FROM provider_exhaustions WHERE provider=? AND expires_at>?", (fallback[2],now)).fetchone():
                # The exhausted original remains durably closed; contract 011 forbids
                # choosing a third identity when its already-stored replacement expired.
                self._event(c,"terminal",original_identity,"failure",reason="quota_exhausted",latency=latency_ms)
                c.execute("COMMIT"); return {"run_id": None, "existing": False}
            replacement_id=self.new_run_id()
            columns=("run_id","role","role_class",*(f"selected_{part}" for part in _IDENTITY),
                     *(f"actual_{part}" for part in _IDENTITY),"state","partial_write","fallback_window_open","fallback_consumed",
                     "authorized_at","dispatched_at","updated_at","project_key","replacement_of_run_id")
            values=(replacement_id,row[14],row[15],*fallback,*fallback,"dispatched",0,0,0,now,now,now,row[16],run_id)
            c.execute("INSERT INTO dispatches (" + ",".join(columns) + ") VALUES(" + ",".join("?" for _ in values) + ")", values)
            self._event(c,"terminal",original_identity,"failure",reason="quota_exhausted",latency=latency_ms)
            self._event(c,"authorized",fallback)
            self._event(c,"dispatched",fallback)
            c.execute("COMMIT"); return {"run_id": replacement_id, "existing": False,
                                            "provider": fallback[2], "model": fallback[3]}
        except RoutingError:
            raise
        except sqlite3.IntegrityError:
            try:
                c.execute("ROLLBACK")
                existing=c.execute("SELECT run_id FROM dispatches WHERE replacement_of_run_id=?", (run_id,)).fetchone()
                if existing: return {"run_id": existing[0], "existing": True}
            except sqlite3.Error:
                pass
            raise RoutingError("ROUTING_UNAVAILABLE")
        except (OverflowError, sqlite3.Error) as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()

    def _rejection_event(self, identity, reason):
        c=None
        try:
            c=self._connect(); c.execute("BEGIN IMMEDIATE"); self._event(c,"rejected",identity,"failure",reason); c.execute("COMMIT")
        except Exception: pass
        finally:
            try:
                if c is not None: c.close()
            except Exception: pass

    def _transition(self, run_id, sql, params, event, outcome="none", latency=None):
        c=self._connect(); row=None
        try:
            c.execute("BEGIN IMMEDIATE"); row=c.execute("SELECT actual_route_id,actual_runtime,actual_provider,actual_model,actual_family,actual_effort,selected_route_id,selected_runtime,selected_provider,selected_model,selected_family,selected_effort,fallback_consumed FROM dispatches WHERE run_id=? AND project_key=?",(run_id,self.project_key)).fetchone(); result=c.execute(sql,params)
            if not row or result.rowcount != 1:
                c.execute("ROLLBACK"); self._rejection_event(tuple(row[6:12]) if row else None,"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
            # The audited identity is the actual dispatched identity when one exists (post-fallback runs
            # audit the fallback identity, never the originally selected one).
            self._event(c,event,tuple(row[:6] if all(row[:6]) else row[6:12]),outcome,latency=latency,via_fallback=bool(row[12])); c.execute("COMMIT")
        except RoutingError: raise
        except (OverflowError, sqlite3.Error) as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            # SEC-A02: an out-of-range latency (OverflowError at SQLite bind time, e.g. an
            # unvalidated caller) or any other sqlite failure still leaves an independent
            # audit trail before mapping to ROUTING_UNAVAILABLE — never a silent traceback.
            self._rejection_event(tuple(row[6:12]) if row else None,"ROUTING_UNAVAILABLE")
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()

    def mark_dispatched(self, run_id):
        now=self._now(); self._transition(run_id,"UPDATE dispatches SET state='dispatched',fallback_window_open=0,actual_route_id=selected_route_id,actual_runtime=selected_runtime,actual_provider=selected_provider,actual_model=selected_model,actual_family=selected_family,actual_effort=selected_effort,dispatched_at=?,updated_at=? WHERE run_id=? AND project_key=? AND state='authorized' AND fallback_window_open=1 AND partial_write=0",(now,now,run_id,self.project_key),"dispatched")
    def mark_partial(self, run_id):
        now=self._now(); self._transition(run_id,"UPDATE dispatches SET partial_write=1,partial_write_at=?,updated_at=? WHERE run_id=? AND project_key=? AND state='dispatched' AND partial_write=0",(now,now,run_id,self.project_key),"partial")
    def terminal(self, run_id, outcome, latency_ms=None):
        if outcome not in {"success","failure"}: raise RoutingError("AUTHORIZATION_INVALID")
        now=self._now(); self._transition(run_id,"UPDATE dispatches SET state=?,fallback_window_open=0,terminal_at=?,updated_at=? WHERE run_id=? AND project_key=? AND state='dispatched'",(f"terminal_{outcome}",now,now,run_id,self.project_key),"terminal",outcome,latency_ms)
    def consume_fallback(self, run_id):
        c=self._connect()
        try:
            now=self._now(); c.execute("BEGIN IMMEDIATE"); row=c.execute("SELECT fallback_route_id,fallback_runtime,fallback_provider,fallback_model,fallback_family,fallback_effort,selected_route_id,selected_runtime,selected_provider,selected_model,selected_family,selected_effort FROM dispatches WHERE run_id=? AND project_key=? AND state='authorized' AND fallback_window_open=1 AND fallback_consumed=0 AND partial_write=0",(run_id,self.project_key)).fetchone()
            if not row or any(item is None for item in row[:6]):
                # Every rejected lifecycle operation leaves an independent post-rollback audit trail.
                c.execute("ROLLBACK"); self._rejection_event(tuple(row[6:12]) if row else None,"FALLBACK_DENIED"); raise RoutingError("FALLBACK_DENIED")
            changed=c.execute("UPDATE dispatches SET state='dispatched',fallback_window_open=0,fallback_consumed=1,actual_route_id=?,actual_runtime=?,actual_provider=?,actual_model=?,actual_family=?,actual_effort=?,fallback_consumed_at=?,dispatched_at=?,updated_at=? WHERE run_id=? AND project_key=? AND state='authorized'",(*row[:6],now,now,now,run_id,self.project_key))
            if changed.rowcount != 1: c.execute("ROLLBACK"); self._rejection_event(tuple(row[6:12]),"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
            self._event(c,"fallback",tuple(row[:6])); c.execute("COMMIT"); return tuple(row[:6])
        except RoutingError:raise
        except sqlite3.Error as exc: raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()
    def abandon(self, run_id):
        """Close a never-dispatched authorization (contract 004 AC-03): terminal, no actual identity."""
        c=self._connect()
        try:
            now=self._now(); c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT selected_route_id,selected_runtime,selected_provider,selected_model,selected_family,selected_effort FROM dispatches WHERE run_id=? AND project_key=? AND state='authorized'",(run_id,self.project_key)).fetchone()
            changed=c.execute("UPDATE dispatches SET state='abandoned',fallback_window_open=0,updated_at=? WHERE run_id=? AND project_key=? AND state='authorized'",(now,run_id,self.project_key))
            if not row or changed.rowcount != 1:
                c.execute("ROLLBACK"); self._rejection_event(tuple(row) if row else None,"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
            self._event(c,"abandoned",tuple(row),"failure"); c.execute("COMMIT")
        except RoutingError: raise
        except sqlite3.Error as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()

    def close_run(self, run_id, outcome, latency_ms=None, usage=None):
        """Close ANY run_id in one transaction (F02): reads the current state ONCE and
        transitions to exactly the right destination — `dispatched` -> `terminal_<outcome>`,
        `authorized`+failure -> `abandoned` (contract 004 AC-03), anything else -> a single
        `rejected`/STATE_CONFLICT event. This replaces the CLI's former
        `try terminal() except STATE_CONFLICT: abandon()` two-transaction pattern, which left
        a spurious rejected row behind a SUCCESSFUL abandon (terminal() already audited its
        own STATE_CONFLICT before abandon() ever ran) and wrote TWO rejected rows for a
        nonexistent/already-terminal run_id. Returns the resulting state string.

        AC-10/AC-11: `usage` never aborts the close, no matter what it contains --
        `_usage_row` never raises, it downgrades. On the `dispatched` branch it is
        interpreted (`ok`/`invalid` depending on what it holds, `absent` for `None`/`{}`).
        On the `abandoned` branch it is forced to `absent` regardless of what was passed:
        a run that never dispatched cannot semantically have consumed anything, and that
        invariant lives here rather than in caller discipline.
        """
        if outcome not in {"success", "failure"}: raise RoutingError("AUTHORIZATION_INVALID")
        c=self._connect(); row=None
        try:
            now=self._now(); c.execute("BEGIN IMMEDIATE")
            row=c.execute("SELECT state,actual_route_id,actual_runtime,actual_provider,actual_model,actual_family,actual_effort,"
                          "selected_route_id,selected_runtime,selected_provider,selected_model,selected_family,selected_effort,"
                          "fallback_consumed FROM dispatches WHERE run_id=? AND project_key=?",(run_id,self.project_key)).fetchone()
            state = row[0] if row else None
            if state == "dispatched":
                changed=c.execute("UPDATE dispatches SET state=?,fallback_window_open=0,terminal_at=?,updated_at=?,"
                                  + _USAGE_SET_CLAUSE +
                                  " WHERE run_id=? AND project_key=? AND state='dispatched'",
                                  (f"terminal_{outcome}",now,now,*_usage_row(usage),run_id,self.project_key))
                if changed.rowcount != 1:
                    c.execute("ROLLBACK"); self._rejection_event(tuple(row[7:13]),"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
                identity = tuple(row[1:7]) if all(row[1:7]) else tuple(row[7:13])
                self._event(c,"terminal",identity,outcome,latency=latency_ms,via_fallback=bool(row[13])); c.execute("COMMIT")
                return f"terminal_{outcome}"
            if state == "authorized" and outcome == "failure":
                changed=c.execute("UPDATE dispatches SET state='abandoned',fallback_window_open=0,updated_at=?,"
                                  + _USAGE_SET_CLAUSE +
                                  " WHERE run_id=? AND project_key=? AND state='authorized'",
                                  (now,*_usage_row(None),run_id,self.project_key))
                if changed.rowcount != 1:
                    c.execute("ROLLBACK"); self._rejection_event(tuple(row[7:13]),"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
                self._event(c,"abandoned",tuple(row[7:13]),"failure"); c.execute("COMMIT")
                return "abandoned"
            # Nonexistent run_id, already-terminal/abandoned row, or authorized+success (which
            # has no defined transition — success only ever follows a real dispatch): exactly
            # ONE rejected event, never two.
            c.execute("ROLLBACK"); self._rejection_event(tuple(row[7:13]) if row else None,"STATE_CONFLICT")
            raise RoutingError("STATE_CONFLICT")
        except RoutingError: raise
        except (OverflowError, sqlite3.Error) as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            self._rejection_event(tuple(row[7:13]) if row else None,"ROUTING_UNAVAILABLE")
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()

    def open_runs(self):
        """Redacted listing of non-terminal rows: (run_id, state, age_ms)."""
        c=self._connect()
        try:
            now=self._now()
            return [{"run_id":r[0],"state":r[1],"age_ms":now-r[2]} for r in
                    c.execute("SELECT run_id,state,authorized_at FROM dispatches WHERE state IN ('authorized','dispatched') ORDER BY authorized_at")]
        finally:c.close()

    def recent_writers(self, limit=20):
        """Redacted listing of recent terminal-success writer run_ids for reviewer identity sourcing."""
        c=self._connect()
        try:
            return [{"run_id":r[0],"terminal_at":r[1]} for r in
                    c.execute("SELECT run_id,terminal_at FROM dispatches WHERE project_key=? AND role_class='writer' AND state='terminal_success' ORDER BY terminal_at DESC,run_id LIMIT ?",(self.project_key,int(limit)))]
        finally:c.close()

    def implementation_identity(self, run_id):
        c=self._connect()
        try:
            row=c.execute("SELECT role_class,actual_route_id,actual_runtime,actual_provider,actual_model,actual_family,actual_effort,state FROM dispatches WHERE run_id=? AND project_key=?",(run_id,self.project_key)).fetchone()
            if not row or row[0] != "writer" or row[-1] != "terminal_success" or any(value is None for value in row[1:-1]): raise RoutingError("REVIEW_IDENTITY_INVALID")
            return ImplementationIdentity(row[3],row[5],row[1],row[2],row[4],row[6])
        finally:c.close()
    def _compact_in(self, c, now_ms):
        """Retention inside the caller's open transaction: 90 days and 10000 events."""
        cutoff=now_ms-90*86400*1000
        doomed = "occurred_at < ? OR event_id IN (SELECT event_id FROM events WHERE occurred_at >= ? ORDER BY occurred_at DESC,event_id DESC LIMIT -1 OFFSET 10000)"
        groups=c.execute(f"SELECT COALESCE(route_id,'none'),COALESCE(runtime,'none'),COALESCE(provider,'none'),COALESCE(model,'none'),COALESCE(family,'none'),outcome,reason_family,latency_bucket,COUNT(*) FROM events WHERE {doomed} GROUP BY route_id,runtime,provider,model,family,outcome,reason_family,latency_bucket", (cutoff,cutoff)).fetchall()
        if groups:
            for *key, count in groups:
                c.execute("INSERT INTO metric_rollups VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(route_key,runtime,provider,model,family,outcome,reason_family,latency_bucket) DO UPDATE SET compacted_count=compacted_count+excluded.compacted_count", (*key,0,0,count,0,0,0,0,0))
            c.execute(f"DELETE FROM events WHERE {doomed}", (cutoff,cutoff))

    def compact(self, now_ms=None):
        c=self._connect()
        try:
            c.execute("BEGIN IMMEDIATE"); self._compact_in(c, self._now() if now_ms is None else now_ms); c.execute("COMMIT")
        except sqlite3.Error as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        finally:c.close()
    def report(self):
        c=self._connect()
        try:
            def pct(where="", args=()):
                count=c.execute("SELECT COUNT(*) FROM events WHERE latency_ms IS NOT NULL " + where,args).fetchone()[0]
                if not count: return (None,None)
                def one(p):
                    offset=(count*p+99)//100-1
                    return c.execute("SELECT latency_ms FROM events WHERE latency_ms IS NOT NULL " + where + " ORDER BY latency_ms,event_id LIMIT 1 OFFSET ?",(*args,offset)).fetchone()[0]
                return one(50),one(90)
            p50,p90=pct()
            routes=c.execute("SELECT DISTINCT COALESCE(route_id,'none') FROM events WHERE latency_ms IS NOT NULL ORDER BY 1").fetchall()
            per_route={}
            for (route,) in routes:
                qroute=None if route == "none" else route
                a,b=pct("AND route_id IS ?",(qroute,)); per_route[route]={"p50_ms":a,"p90_ms":b}
            # AC-15: tokens are a SIBLING key, never merged into `per_route` above -- their
            # route-key sets are not subsets of each other (a run closed without
            # --latency-ms contributes tokens and no percentile; the events grouping above
            # is machine-global with no project_key, this one is scoped to self.project_key).
            # SUM() over an all-NULL column is NULL, never 0 -- coercing it would be exactly
            # AC-08's forbidden fabrication, generalized to the aggregate.
            sums=",".join(f"SUM(usage_{field})" for field in USAGE_TOKEN_FIELDS) + ",SUM(cost_micros)"
            overall=c.execute(f"SELECT {sums} FROM dispatches WHERE project_key=?",(self.project_key,)).fetchone()
            tokens=dict(zip(USAGE_TOKEN_FIELDS,overall[:-1]))
            tokens["cost_micros"]=overall[-1]
            tokens["per_route"]={}
            for row in c.execute(
                f"SELECT COALESCE(actual_route_id,selected_route_id,'none'),{sums} "
                "FROM dispatches WHERE project_key=? GROUP BY 1",(self.project_key,)):
                route,*route_sums=row
                entry=dict(zip(USAGE_TOKEN_FIELDS,route_sums[:-1]))
                entry["cost_micros"]=route_sums[-1]
                tokens["per_route"][route]=entry
            tokens["scope"]=("dispatches, per-project (this project_key only); unlike p50_ms/p90_ms "
                             "and per_route above, which come from events (machine-global, no "
                             "project_key). The two route-key sets are not subsets of each other.")
            # 007-P2 review finding (F-PR-03, upheld by finding-verifier): usage_status
            # records a discard, but nothing aggregated it -- a status column that only
            # the store can see is the exact blindness AC-11 exists to end, moved one
            # level up into reporting. If Pi ever reports a shape that trips the
            # totalTokens mismatch (e.g. cache tokens it doesn't today), every affected row
            # would silently become invisible: NULL tokens indistinguishable from no
            # activity at all. Counted here so a mass discard is visible instead of mute.
            tokens["status_counts"]={status:count for status,count in c.execute(
                "SELECT usage_status,COUNT(*) FROM dispatches WHERE project_key=? AND usage_status IS NOT NULL "
                "GROUP BY usage_status",(self.project_key,))}
            return {"retained_events":c.execute("SELECT COUNT(*) FROM events").fetchone()[0],"p50_ms":p50,"p90_ms":p90,"per_route":per_route,"lifetime_events":c.execute("SELECT COALESCE(SUM(lifetime_count),0) FROM metric_rollups").fetchone()[0],"tokens":tokens}
        finally:c.close()


# Keyed by the version each step migrates FROM, so a gap is a KeyError-shaped refusal
# rather than a silently skipped step.  `migrate` walks it until the stored version
# reaches SCHEMA.
_MIGRATION_STEPS = {
    4: RoutingStore._migrate_4_to_5,
    5: RoutingStore._migrate_5_to_6,
    6: RoutingStore._migrate_6_to_7,
}
