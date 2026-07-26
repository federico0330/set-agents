import os
import dataclasses
import json
import signal
import sqlite3
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"ai/scripts"))
import models_config
import routing
from routing_core import catalog as routing_catalog

class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.config=models_config.load_config(ROOT/"models.toml")
        self.roster=models_config.load_roster(ROOT/"roles.tsv")
        self.inventory={("codex","openai-codex"):{"gpt-5.6-sol"},("claude-code","anthropic"):{"opus"},
                        ("opencode","openai-codex"):{"gpt-5.6-sol"},("opencode","anthropic"):{"opus"}}

    def facts(self, role="product-analyst", runtime="claude-code", **changes):
        data=dict(role=role,operation="change",task_class="documentation",read_write="write",write_started=False,
                  risk="low",criticality="",affected_surfaces=(),required_tools=("read",),context_required=True,
                  context_present=True,critical_coverage=True,selected_runtime=runtime)
        data.update(changes); return data

    def service(self, root=None, inventory=None, simulate=False):
        return routing._compose_for_tests(self.config,self.roster,inventory or self.inventory,root,simulate=simulate)

    def observed(self, service, role="product-analyst", runtime="claude-code", **changes):
        return service._observe_for_invocation(**self.facts(role, runtime, **changes))

    def authorize(self, svc, role="implementer", runtime="codex"):
        decision=svc.route(routing.TaskRequest(role,"change","documentation",selected_runtime=runtime),
                           self.observed(svc,role,runtime))
        self.assertTrue(decision.execution_enabled, decision.reason_codes)
        return decision

    def test_static_ids_exclude_runtime_and_catalog_is_immutable(self):
        service=self.service(); routes=service.snapshot.routes
        self.assertTrue(all(r.route_id.startswith("rt1_") and len(r.route_id)==20 for r in routes))
        openai=next(r for r in routes if r.provider=="openai-codex")
        self.assertIn((openai.route_id,"codex",openai.provider,openai.model,openai.family,openai.effort),service.snapshot.identities)
        self.assertIn((openai.route_id,"opencode",openai.provider,openai.model,openai.family,openai.effort),service.snapshot.identities)

    def test_facts_are_internal_single_use_and_conflicts_disable_execution(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); request=routing.TaskRequest("implementer","change","documentation",selected_runtime="codex")
            stale=dataclasses.replace(self.observed(svc,role="implementer",runtime="codex"),observed_at=time.time()-301)
            decision=svc.route(request,stale)
            self.assertFalse(decision.execution_enabled); self.assertEqual(decision.reason_codes,("FACTS_INCOMPLETE",))
            facts=self.observed(svc,role="implementer",runtime="codex")
            self.assertFalse(svc.route(request,dataclasses.replace(facts)).execution_enabled)
            self.assertTrue(svc.route(request,facts).execution_enabled)
            self.assertFalse(svc.route(request,facts).execution_enabled)  # exact facts are single-use
            decision=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="codex"),self.observed(svc,role="implementer",runtime="codex"))
            self.assertFalse(decision.execution_enabled); self.assertEqual(decision.reason_codes,("FACTS_INCOMPLETE",))

    def test_observed_risk_is_never_downgraded_and_enums_are_closed(self):
        svc=self.service(simulate=True)
        # A low-risk request cannot downgrade an observed high risk: the combined
        # risk stays high, so missing critical coverage excludes every route.
        request=routing.TaskRequest("product-analyst","change","documentation",risk="low",selected_runtime="claude-code")
        facts=self.observed(svc,risk="high",context_required=False,context_present=False,critical_coverage=False)
        decision=svc.route(request,facts)
        self.assertFalse(decision.execution_enabled)
        self.assertIn("NO_ELIGIBLE_ROUTE",decision.reason_codes)
        # The anthropic route (the only claude-code-compatible one) is excluded for context, not risk passthrough.
        self.assertEqual({item["reason"] for item in decision.exclusions},{"RUNTIME_UNAVAILABLE","CONTEXT_MISSING"})
        # The same observation with low risk routes normally.
        ok=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="low",selected_runtime="claude-code"),
                     self.observed(svc,risk="low",context_required=False,context_present=False,critical_coverage=False))
        self.assertIsNotNone(ok.route_id)
        # Values outside the closed vocabularies are FACTS_INCOMPLETE, request and facts alike.
        bad=svc.route(routing.TaskRequest("product-analyst","change","documentation",risk="extreme",selected_runtime="claude-code"),self.observed(svc))
        self.assertEqual(bad.reason_codes,("FACTS_INCOMPLETE",))
        bad=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="claude-code"),self.observed(svc,risk="extreme"))
        self.assertEqual(bad.reason_codes,("FACTS_INCOMPLETE",))

    def test_pi_is_simulation_only_and_runtime_auth_is_pair_scoped(self):
        svc=self.service(); d=svc.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="pi"),self.observed(svc,runtime="pi"))
        self.assertFalse(d.execution_enabled); self.assertIn("NO_ELIGIBLE_ROUTE",d.reason_codes)
        unavailable=self.service(inventory={("codex","openai-codex"):{"gpt-5.6-sol"}})
        d=unavailable.route(routing.TaskRequest("product-analyst","change","documentation",selected_runtime="opencode"),self.observed(unavailable,runtime="opencode"))
        self.assertFalse(d.execution_enabled)

    def test_probe_parsers_are_pair_specific_and_fail_closed(self):
        # Parsers are validated hermetically against recorded shapes; live CLI
        # output is deliberately not asserted (it changes across versions).
        self.assertTrue(routing_catalog._parse_codex_login("Logged in using ChatGPT\n"))
        self.assertFalse(routing_catalog._parse_codex_login("Not logged in\n"))
        self.assertTrue(routing_catalog._parse_claude_auth('{"loggedIn": true, "authMethod": "claude.ai"}'))
        self.assertFalse(routing_catalog._parse_claude_auth('{"loggedIn": false}'))
        with self.assertRaises(ValueError): routing_catalog._parse_claude_auth("Logged in")
        auth="\x1b[90m│\n●  OpenAI \x1b[90moauth\x1b[0m\n●  OpenCode Zen api\n└  2 credentials\n"
        self.assertEqual(routing_catalog._parse_opencode_auth(auth),{"openai","opencode zen"})
        models="\x1b[0mopenai/gpt-5.6-sol\nopenai/gpt-5.4\n"
        self.assertEqual(routing_catalog._parse_opencode_models(models,"openai"),{"gpt-5.6-sol","gpt-5.4"})
        # opencode exits 0 on unknown providers; the error text must fail the pair.
        with self.assertRaises(routing.RoutingError):
            routing_catalog._parse_opencode_models("Error: Provider not found: anthropic\n","anthropic")
        with self.assertRaises(routing.RoutingError):
            routing_catalog._parse_opencode_models("anthropic/opus\nunexpected junk\n","anthropic")

    def test_sqlite_authorization_closes_fallback_before_dispatch(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc)
            svc.store.mark_dispatched(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"FALLBACK_DENIED"): svc.store.consume_fallback(d.run_id)
            self.assertEqual(os.stat(Path(td)/"state").st_mode & 0o777,0o700)
            self.assertEqual(os.stat(Path(td)/"state/routing.db").st_mode & 0o777,0o600)

    def test_review_identity_only_comes_from_terminal_writer(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc)
            run=d.run_id; svc.store.mark_dispatched(run); svc.store.terminal(run,"success")
            review=svc.route(routing.TaskRequest("package-reviewer","change","documentation",selected_runtime="claude-code"),self.observed(svc,"package-reviewer","claude-code"),run)
            self.assertFalse(review.execution_enabled); self.assertNotEqual(review.family,"gpt-5.6")

    def test_rejected_lifecycle_operations_are_audited(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            d=self.authorize(svc); store.mark_dispatched(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"FALLBACK_DENIED"): store.consume_fallback(d.run_id)
            with self.assertRaisesRegex(routing.RoutingError,"STATE_CONFLICT"): store.mark_dispatched(d.run_id)
            c=store._connect()
            try:
                reasons={row[0] for row in c.execute("SELECT reason_family FROM events WHERE event_type='rejected'")}
                self.assertEqual(reasons,{"FALLBACK_DENIED","STATE_CONFLICT"})
                exclusions=c.execute("SELECT COALESCE(SUM(exclusion_count),0) FROM metric_rollups").fetchone()[0]
                self.assertEqual(exclusions,2)
            finally: c.close()

    def test_fallback_counters_record_actual_identity_outcomes(self):
        with tempfile.TemporaryDirectory() as td:
            inventory=dict(self.inventory)
            svc=self.service(Path(td)/"state",inventory=inventory)
            d=self.authorize(svc,role="implementer",runtime="opencode")
            self.assertIsNotNone(d.fallback_identity)
            consumed=svc.store.consume_fallback(d.run_id)
            self.assertEqual(consumed,d.fallback_identity)
            svc.store.terminal(d.run_id,"success",latency_ms=42)
            c=svc.store._connect()
            try:
                consumed_count,success_count=c.execute("SELECT COALESCE(SUM(fallback_consumed_count),0),COALESCE(SUM(fallback_success_count),0) FROM metric_rollups").fetchone()
                self.assertEqual((consumed_count,success_count),(1,1))
                # The terminal event audits the actually dispatched (fallback) identity, not the selected one.
                terminal_route=c.execute("SELECT route_id FROM events WHERE event_type='terminal'").fetchone()[0]
                self.assertEqual(terminal_route,d.fallback_identity[0])
            finally: c.close()

    def test_explain_cli_is_schema_two_and_creates_no_state(self):
        state=Path.home()/".local/state/set-agentes/routing-v2"
        before=sorted(state.glob("*")) if state.exists() else []
        result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-explain","documentation","--json"],cwd=ROOT,text=True,capture_output=True)
        self.assertIn(result.returncode,(0,1),result.stderr); self.assertEqual(result.stdout.count("\n"),1)
        data=json.loads(result.stdout); self.assertEqual(set(data),{"schema_version","ok","command","data","warnings","reason_codes"}); self.assertEqual(data["schema_version"],2)
        self.assertEqual(before,sorted(state.glob("*")) if state.exists() else [])

    def test_cli_mode_exclusion_covers_every_non_routing_argument(self):
        # Any argument other than --json combined with an observability mode is a
        # total conflict (exit 2), including plain modifiers such as --yes.
        for extra in (["--yes"],["--no-install"],["--harness","claude"]):
            result=subprocess.run([sys.executable,"ai/scripts/set_agents_app.py","--route-explain","documentation","--json",*extra],
                                  cwd=ROOT,text=True,capture_output=True)
            self.assertEqual(result.returncode,2,(extra,result.stdout,result.stderr))
            self.assertIn("ROUTING_INPUT_INVALID",result.stdout)

    def test_gate_and_telemetry_negative_cases(self):
        gates=routing.gate_specs(ROOT); gate=gates["v2:python-compile"]
        self.assertIn("v2:routing-unit",gates)
        self.assertEqual(routing.run_gate(gate,ROOT,{"PYTHONUTF8":"1"}),0)
        self.assertTrue(Path(gate.argv[0]).is_absolute())
        with self.assertRaises(ValueError): routing.run_gate(dataclasses.replace(gate,argv=("python3","-c","pass")),ROOT)
        with self.assertRaises(ValueError): routing.run_gate(gate,ROOT,{"PATH":"/tmp"})

    def test_existing_invalid_sqlite_is_byte_preserving_and_legacy_is_nofollow(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"; root.mkdir(mode=0o700)
            db=root/"routing.db"; db.write_bytes(b"not sqlite"); db.chmod(0o600)
            before=db.read_bytes()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()
            self.assertEqual(before,db.read_bytes())
            legacy=Path(td)/"legacy/routing"; legacy.mkdir(parents=True)
            candidate=legacy/"routing-events-2026-7.jsonl"; candidate.write_text("keep")
            self.assertEqual(routing.legacy_warnings(legacy.parent),("LEGACY_ROUTING_STATE_PRESENT",))
            link=legacy/"routing.lock"; link.symlink_to(candidate)
            self.assertEqual(routing.legacy_warnings(legacy.parent),("LEGACY_ROUTING_STATE_PRESENT","LEGACY_ROUTING_STATE_UNSAFE"))

    def test_schema_drift_fails_closed_byte_identically(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"
            store=routing.RoutingStore._for_tests(root); store.report()  # creates a pristine database
            c=sqlite3.connect(root/"routing.db"); c.execute("DROP INDEX dispatches_review"); c.execute("VACUUM"); c.close()
            before=(root/"routing.db").read_bytes()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()
            self.assertEqual(before,(root/"routing.db").read_bytes())
            # A downlevel schema version is rejected the same way.
            c=sqlite3.connect(root/"routing.db"); c.execute("UPDATE meta SET value='2' WHERE key='schema_version'"); c.commit(); c.close()
            with self.assertRaisesRegex(routing.RoutingError,"ROUTING_UNAVAILABLE"):
                routing.RoutingStore._for_tests(root).report()

    def test_concurrent_writer_lock_fails_closed_without_corruption(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            first=self.authorize(svc)
            holder=store._connect()
            try:
                holder.execute("BEGIN IMMEDIATE")
                # busy_timeout=0: a concurrent writer loses immediately and fail-closed.
                request=routing.TaskRequest("implementer","change","documentation",selected_runtime="codex")
                decision=svc.route(request,self.observed(svc,"implementer","codex"))
                self.assertFalse(decision.execution_enabled)
                self.assertEqual(decision.reason_codes,("ROUTING_UNAVAILABLE",))
                holder.execute("ROLLBACK")
            finally: holder.close()
            second=self.authorize(svc)  # the lock loser left a consistent database behind
            c=store._connect()
            try:
                runs={row[0] for row in c.execute("SELECT run_id FROM dispatches")}
                self.assertEqual(runs,{first.run_id,second.run_id})
            finally: c.close()

    def test_crash_between_begin_and_commit_preserves_consistency(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"
            svc=self.service(root); d=self.authorize(svc)
            script=textwrap.dedent(f"""
                import os, signal, sys
                from pathlib import Path
                sys.path.insert(0, {str(ROOT/'ai/scripts')!r})
                from routing_core.store import RoutingStore
                store=RoutingStore._for_tests(Path({str(root)!r}))
                c=store._connect(); c.execute("BEGIN IMMEDIATE")
                store._event(c,"terminal",("rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","medium"),"success","none",10)
                os.kill(os.getpid(), signal.SIGKILL)
            """)
            result=subprocess.run([sys.executable,"-c",script],cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(result.returncode,-signal.SIGKILL,result.stderr)
            report=routing.RoutingStore._for_tests(root).report()
            # The killed transaction never becomes visible and the database stays fully usable.
            self.assertEqual(report["retained_events"],1)  # only the original authorization event
            svc2=self.service(root); self.authorize(svc2)

    def test_retention_bound_holds_within_the_writing_transaction(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state"); store=svc.store
            conn=store._connect()
            try:
                now=store._now(); conn.execute("BEGIN IMMEDIATE")
                rows=[(now-120*86400*1000 if n==0 else now,"terminal","rt","codex","openai-codex","gpt-5.6-sol","gpt-5.6","success","none",n,"100+") for n in range(10005)]
                conn.executemany("INSERT INTO events(occurred_at,event_type,route_id,runtime,provider,model,family,outcome,reason_family,latency_ms,latency_bucket) VALUES(?,?,?,?,?,?,?,?,?,?,?)",rows)
                conn.execute("COMMIT")
            finally: conn.close()
            # The next write path compacts in its own transaction: bound holds at COMMIT.
            self.authorize(svc)
            c=store._connect()
            try:
                self.assertLessEqual(c.execute("SELECT COUNT(*) FROM events").fetchone()[0],10000)
                compacted=c.execute("SELECT COALESCE(SUM(compacted_count),0) FROM metric_rollups").fetchone()[0]
                self.assertGreater(compacted,0)
            finally: c.close()

    def test_database_bytes_never_contain_private_task_or_account_data(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            d=self.authorize(svc); svc.store.mark_dispatched(d.run_id); svc.store.terminal(d.run_id,"success",latency_ms=10)
            blob=b"".join((Path(td)/"state"/name).read_bytes() for name in os.listdir(Path(td)/"state"))
            for secret in (b"documentation",b"change",os.environ.get("USER","@@none@@").encode(),str(Path.home()).encode(),b"@gmail",b"password",b"token"):
                self.assertNotIn(secret,blob)

    def test_compaction_keeps_bounded_events_and_percentiles(self):
        with tempfile.TemporaryDirectory() as td:
            svc=self.service(Path(td)/"state")
            store=svc.store; conn=store._connect()
            try:
                now=store._now(); conn.execute("BEGIN IMMEDIATE")
                conn.executemany("INSERT INTO events(occurred_at,event_type,route_id,runtime,provider,model,family,outcome,reason_family,latency_ms,latency_bucket) VALUES(?,?,?,?,?,?,?,?,?,?,?)",[(now,"terminal","rt", "codex","openai-codex","gpt-5.6-sol","gpt-5.6","success","none",n,"100+") for n in (10,20,30)])
                conn.execute("COMMIT")
            finally: conn.close()
            report=store.report(); self.assertEqual((report["p50_ms"],report["p90_ms"]),(20,30))

if __name__ == "__main__": unittest.main()
