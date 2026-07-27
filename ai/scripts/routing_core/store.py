from __future__ import annotations

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

SCHEMA = 5
_RUN = re.compile(r"^run1_[0-9a-f]{32}$")
_PROJECT_KEY = re.compile(r"^proj1_[0-9a-f]{32}$")
NIL_PROJECT_KEY = "proj1_00000000000000000000000000000000"
_TEST_PROJECT_KEY = "proj1_11111111111111111111111111111111"
PROJECT_KEY_COLUMN = "project_key TEXT NOT NULL DEFAULT 'proj1_00000000000000000000000000000000' CHECK(project_key GLOB 'proj1_[0-9a-f]*' AND length(project_key)=38)"
_IDENTITY = ("route_id", "runtime", "provider", "model", "family", "effort")
_EVENT_TYPES = {"authorized", "dispatched", "partial", "fallback", "terminal", "rejected", "abandoned"}
_OUTCOMES = {"success", "failure", "none"}


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
     authorized_at INTEGER NOT NULL, dispatched_at INTEGER, partial_write_at INTEGER, fallback_consumed_at INTEGER, terminal_at INTEGER, updated_at INTEGER NOT NULL, """ + PROJECT_KEY_COLUMN + """,
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
 CREATE INDEX events_retention ON events(occurred_at,event_id); CREATE INDEX events_route_retention ON events(route_id,occurred_at,event_id); CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at);
""")
        c.execute("INSERT INTO meta VALUES('schema_version',?)", (str(SCHEMA),)); c.execute("INSERT INTO meta VALUES('installation_hmac_salt',?)", (secrets.token_hex(32),))

    def _validate_schema(self, c):
        quick=c.execute("PRAGMA integrity_check").fetchone()
        tables={row[0] for row in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        meta=dict(c.execute("SELECT key,value FROM meta")) if "meta" in tables else {}
        if quick != ("ok",) or tables != {"meta","dispatches","events","metric_rollups"} or meta.keys() != {"schema_version","installation_hmac_salt"} or meta["schema_version"] != str(SCHEMA) or len(meta["installation_hmac_salt"]) != 64:
            raise RoutingError("ROUTING_UNAVAILABLE")

    _canonical_ddl = None

    @classmethod
    def _canonical_schema_sql(cls):
        """Normalized DDL of a pristine schema; the single source of truth for validation."""
        if cls._canonical_ddl is None:
            c = sqlite3.connect(":memory:", isolation_level=None)
            try:
                cls._create_schema(c); c.execute("COMMIT")
                cls._canonical_ddl = {name: " ".join(text.split()).lower() for name, text in
                                      c.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL")}
            finally:
                c.close()
        return cls._canonical_ddl

    def _validate_existing_readonly(self):
        """Existing state is checked without journal/pragma writes before any RW open."""
        before = self._file_fingerprint(self.db_path, True)
        try:
            c = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, isolation_level=None, timeout=0)
            self._validate_schema(c)
            # Exact structural equality with the canonical DDL: columns, types,
            # NOT NULL, CHECK constraints, primary keys, and index definitions
            # must all match byte-for-byte after whitespace normalization.
            sql = {name: text for name, text in c.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL")}
            if any(not isinstance(text, str) for text in sql.values()): raise RoutingError("ROUTING_UNAVAILABLE")
            normalized = {name: " ".join(text.split()).lower() for name, text in sql.items()}
            if normalized != self._canonical_schema_sql():
                raise RoutingError("ROUTING_UNAVAILABLE")
            c.close()
        except (sqlite3.Error, RoutingError) as exc:
            try: c.close()
            except Exception: pass
            raise RoutingError("ROUTING_UNAVAILABLE") from exc
        if self._file_fingerprint(self.db_path, True) != before: raise RoutingError("ROUTING_UNAVAILABLE")

    def migration_required(self) -> bool:
        """True only for a securely opened legacy schema-4 database.

        This is deliberately informational: normal routing still refuses the old
        schema and never writes or attempts an automatic migration.
        """
        try:
            self._safe_dir(create=False)
            self._file_fingerprint(self.db_path, True)
            c = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True,
                                isolation_level=None, timeout=0)
            try:
                return dict(c.execute("SELECT key,value FROM meta")).get("schema_version") == "4"
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

    def migrate_from_v4(self, harness_project_key: str) -> tuple[int, Path]:
        """Explicit, backup-first schema 4 -> 5 migration; never called by normal routing."""
        if not _PROJECT_KEY.fullmatch(harness_project_key) or harness_project_key == NIL_PROJECT_KEY:
            raise RoutingError("ROUTING_UNAVAILABLE")
        self._safe_dir(create=False)
        self._file_fingerprint(self.db_path, True)
        try:
            source = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, isolation_level=None, timeout=0)
            schema = dict(source.execute("SELECT key,value FROM meta"))
            if schema.get("schema_version") != "4":
                raise RoutingError("ROUTING_UNAVAILABLE")
            rows = int(source.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0])
            backup_dir = self.root / "backups"
            old = os.umask(0o077)
            try:
                backup_dir.mkdir(mode=0o700, exist_ok=True)
            finally:
                os.umask(old)
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            backup = backup_dir / f"routing-v4-{stamp}.db"
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
                if dict(check.execute("SELECT key,value FROM meta")).get("schema_version") != "4":
                    raise RoutingError("ROUTING_UNAVAILABLE")
                if int(check.execute("SELECT COUNT(*) FROM dispatches").fetchone()[0]) != rows:
                    raise RoutingError("ROUTING_UNAVAILABLE")
            finally:
                check.close(); source.close()
            c = sqlite3.connect(f"file:{self.db_path}?mode=rw", uri=True, isolation_level=None, timeout=0)
            try:
                self._configure(c)
                c.execute("BEGIN EXCLUSIVE")
                if dict(c.execute("SELECT key,value FROM meta")).get("schema_version") != "4":
                    raise RoutingError("ROUTING_UNAVAILABLE")
                c.execute("ALTER TABLE dispatches ADD COLUMN " + PROJECT_KEY_COLUMN)
                c.execute("UPDATE dispatches SET project_key = ?", (harness_project_key,))
                c.execute("DROP INDEX dispatches_review")
                c.execute("CREATE INDEX dispatches_review ON dispatches(project_key,role,state,terminal_at)")
                c.execute("UPDATE meta SET value='5' WHERE key='schema_version'")
                sql = {name: " ".join(text.split()).lower() for name, text in
                       c.execute("SELECT name,sql FROM sqlite_master WHERE type IN ('table','index') AND sql IS NOT NULL")}
                if sql != self._canonical_schema_sql():
                    raise RoutingError("ROUTING_UNAVAILABLE")
                c.execute("COMMIT")
            except Exception:
                try: c.execute("ROLLBACK")
                except sqlite3.Error: pass
                raise
            finally:
                c.close()
            return rows, backup
        except RoutingError:
            raise
        except (OSError, sqlite3.Error) as exc:
            raise RoutingError("ROUTING_UNAVAILABLE") from exc

    @staticmethod
    def _now(): return int(time.time() * 1000)
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
            values=(run_id,role,role_class,*identity,*(fallback or (None,)*6),*(None,)*6,"authorized",0,1,0,now,None,None,None,None,now,self.project_key)
            c.execute("INSERT INTO dispatches VALUES(" + ",".join("?" for _ in values) + ")", values)
            self._event(c,"authorized",identity,fallback=fallback is not None); c.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            c.execute("ROLLBACK"); self._rejection_event(identity,"AUTHORIZATION_REPLAY"); raise RoutingError("AUTHORIZATION_REPLAY") from exc
        except sqlite3.Error as exc:
            try:c.execute("ROLLBACK")
            except sqlite3.Error:pass
            self._rejection_event(identity,"ROUTING_UNAVAILABLE"); raise RoutingError("ROUTING_UNAVAILABLE") from exc
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

    def close_run(self, run_id, outcome, latency_ms=None):
        """Close ANY run_id in one transaction (F02): reads the current state ONCE and
        transitions to exactly the right destination — `dispatched` -> `terminal_<outcome>`,
        `authorized`+failure -> `abandoned` (contract 004 AC-03), anything else -> a single
        `rejected`/STATE_CONFLICT event. This replaces the CLI's former
        `try terminal() except STATE_CONFLICT: abandon()` two-transaction pattern, which left
        a spurious rejected row behind a SUCCESSFUL abandon (terminal() already audited its
        own STATE_CONFLICT before abandon() ever ran) and wrote TWO rejected rows for a
        nonexistent/already-terminal run_id. Returns the resulting state string.
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
                changed=c.execute("UPDATE dispatches SET state=?,fallback_window_open=0,terminal_at=?,updated_at=? "
                                  "WHERE run_id=? AND project_key=? AND state='dispatched'",(f"terminal_{outcome}",now,now,run_id,self.project_key))
                if changed.rowcount != 1:
                    c.execute("ROLLBACK"); self._rejection_event(tuple(row[7:13]),"STATE_CONFLICT"); raise RoutingError("STATE_CONFLICT")
                identity = tuple(row[1:7]) if all(row[1:7]) else tuple(row[7:13])
                self._event(c,"terminal",identity,outcome,latency=latency_ms,via_fallback=bool(row[13])); c.execute("COMMIT")
                return f"terminal_{outcome}"
            if state == "authorized" and outcome == "failure":
                changed=c.execute("UPDATE dispatches SET state='abandoned',fallback_window_open=0,updated_at=? "
                                  "WHERE run_id=? AND project_key=? AND state='authorized'",(now,run_id,self.project_key))
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
            return {"retained_events":c.execute("SELECT COUNT(*) FROM events").fetchone()[0],"p50_ms":p50,"p90_ms":p90,"per_route":per_route,"lifetime_events":c.execute("SELECT COALESCE(SUM(lifetime_count),0) FROM metric_rollups").fetchone()[0]}
        finally:c.close()
