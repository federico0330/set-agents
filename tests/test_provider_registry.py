"""022 PKG-4 (proveedores-del-usuario, AC-11..15): the `providers.toml` registry
(`ai/scripts/provider_registry.py`), its `--provider-list|add|remove|verify` CLI
(`ai/scripts/set_agents_app.py`), and `install.py`'s render-from-registry + JSON-subtree
prune (AC-13/AC-14).

Every subprocess test below runs with `HOME` pointed at a `tempfile.TemporaryDirectory`
(never the real machine's `~/.config/opencode` or `~/.local/state/set-agentes` — the repo
harness rule this whole package exists under). `./build.sh --output <staging>` is run
fresh per test that needs a real staged tree, exactly like
`tests/test_harness.py::test_managed_install_preserves_unrelated_and_rolls_back` already
does for the rest of the installer.
"""

import json
import os
import subprocess
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import provider_registry as pr  # noqa: E402
import set_agents_app as app  # noqa: E402


def run(*args, env=None, check=True, cwd=ROOT):
    return subprocess.run(
        args, cwd=cwd, env={**os.environ, **(env or {})},
        text=True, capture_output=True, check=check,
    )


def build_staging(staging_dir):
    run("./build.sh", "--output", staging_dir)


def make_home(td):
    home = Path(td)
    (home / ".claude").mkdir(parents=True, exist_ok=True)
    (home / ".config/opencode").mkdir(parents=True, exist_ok=True)
    (home / ".codex").mkdir(parents=True, exist_ok=True)
    return home


def live_provider_block(home):
    doc = json.loads((home / ".config/opencode/opencode.json").read_text())
    return doc.get("provider")


# --------------------------------------------------------------- provider_registry.py


class ParseSerializeRoundTripTests(unittest.TestCase):
    def test_round_trip_preserves_origin_and_arbitrary_spec_shape(self):
        entries = {
            "ollama": pr.ProviderEntry(origin="harness", spec=dict(pr.HARNESS_PROVIDER_SEED["ollama"])),
            "weird id.with:punct": pr.ProviderEntry(
                origin="user",
                spec={"npm": "x", "name": 'quote " and \\ backslash and \n newline',
                      "options": {"baseURL": "http://x/v1"}, "models": {"m": {"name": "M"}}},
            ),
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text(pr.serialize_providers_toml(entries))
            back = pr.parse_providers_toml(path)
        self.assertEqual(back, entries)

    def test_absent_file_is_the_unbiased_empty_default(self):
        self.assertEqual(pr.parse_providers_toml(Path("/nonexistent/providers.toml")), {})

    def test_fails_closed_on_unknown_origin_not_silent_default(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text('[x]\norigin = "bogus"\nspec = "{}"\n')
            with self.assertRaises(pr.ProvidersRegistryError):
                pr.parse_providers_toml(path)

    def test_fails_closed_on_spec_not_valid_json(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text('[x]\norigin = "user"\nspec = "not json{"\n')
            with self.assertRaises(pr.ProvidersRegistryError):
                pr.parse_providers_toml(path)

    def test_fails_closed_on_malformed_toml(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text("[x\nnot valid toml")
            with self.assertRaises(pr.ProvidersRegistryError):
                pr.parse_providers_toml(path)


class SeedOrMigrateTests(unittest.TestCase):
    """AC-15: the migration comparison is against the harness's own VALUE, never an
    id/name heuristic (022 context pack, P4)."""

    def test_empty_live_block_seeds_harness_defaults(self):
        entries = pr.seed_or_migrate({})
        self.assertEqual(set(entries), set(pr.HARNESS_PROVIDER_SEED))
        self.assertTrue(all(e.origin == "harness" for e in entries.values()))
        self.assertEqual(entries["ollama"].spec, pr.HARNESS_PROVIDER_SEED["ollama"])

    def test_byte_identical_block_is_harness_legacy(self):
        live = {"ollama": dict(pr.HARNESS_PROVIDER_SEED["ollama"])}
        entries = pr.seed_or_migrate(live)
        self.assertEqual(entries["ollama"].origin, "harness-legacy")

    def test_an_id_the_harness_never_shipped_is_user(self):
        live = {"lmstudio": {"npm": "@ai-sdk/openai-compatible", "name": "LM Studio",
                              "options": {"baseURL": "http://localhost:1234/v1"},
                              "models": {"foo": {"name": "Foo"}}}}
        entries = pr.seed_or_migrate(live)
        self.assertEqual(entries["lmstudio"].origin, "user")

    def test_same_id_but_edited_value_is_user_not_harness_legacy(self):
        """The exact nuance the context pack calls out: name-matching alone would call
        this harness-legacy; it must not, because the VALUE diverged."""
        edited = dict(pr.HARNESS_PROVIDER_SEED["ollama"])
        edited["name"] = "Ollama (edited by Federico)"
        entries = pr.seed_or_migrate({"ollama": edited})
        self.assertEqual(entries["ollama"].origin, "user")
        self.assertEqual(entries["ollama"].spec, edited)  # the edit itself is preserved, never lost


class LoadOrBootstrapTests(unittest.TestCase):
    def test_existing_file_returns_none_bootstrap_text(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text(pr.serialize_providers_toml({"x": pr.ProviderEntry(origin="user", spec={"npm": "a", "name": "b", "options": {"baseURL": "http://x"}, "models": {"m": {"name": "M"}}})}))
            entries, bootstrap = pr.load_or_bootstrap(path, {})
            self.assertIsNone(bootstrap)
            self.assertEqual(set(entries), {"x"})

    def test_absent_file_returns_computed_bootstrap_text_not_yet_written(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            entries, bootstrap = pr.load_or_bootstrap(path, {})
            self.assertIsNotNone(bootstrap)
            self.assertFalse(path.exists(), "load_or_bootstrap must never write by itself")
            self.assertEqual(set(entries), set(pr.HARNESS_PROVIDER_SEED))


# --------------------------------------------------------------- set_agents_app.py CLI


class ProviderCliDirectTests(unittest.TestCase):
    """In-process calls, module globals redirected to a temp registry file -- never the
    real HOME (PROVIDERS_TOML_PATH is patched explicitly per test, independent of
    STATE_DIR/HOME)."""

    def _run_with_registry(self, func, *a, **kw):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            with mock.patch.object(app, "PROVIDERS_TOML_PATH", path):
                out = []
                with mock.patch("builtins.print", side_effect=lambda *args, **_: out.append(" ".join(map(str, args)))):
                    rc = func(*a, **kw)
                return rc, out, (pr.parse_providers_toml(path) if path.exists() else {})

    def test_list_on_empty_registry_prints_none(self):
        rc, out, _ = self._run_with_registry(app.cmd_provider_list)
        self.assertEqual(rc, 0)
        self.assertTrue(out[0].startswith("PROVIDER_NONE"))

    def test_add_builds_spec_from_structured_flags_never_raw_json(self):
        rc, out, entries = self._run_with_registry(
            app.cmd_provider_add, "lmstudio", "http://localhost:1234/v1",
            npm=None, label=None, models=["llama-3:Llama 3", "phi-4"],
        )
        self.assertEqual(rc, 0)
        self.assertIn("PROVIDER_ADDED id=lmstudio origin=user models=2", out[0])
        self.assertEqual(entries["lmstudio"].origin, "user")
        self.assertEqual(entries["lmstudio"].spec["npm"], "@ai-sdk/openai-compatible")
        self.assertEqual(entries["lmstudio"].spec["options"]["baseURL"], "http://localhost:1234/v1")
        self.assertEqual(entries["lmstudio"].spec["models"], {"llama-3": {"name": "Llama 3"}, "phi-4": {"name": "phi-4"}})

    def test_add_rejects_an_id_that_shadows_the_routing_registry(self):
        rc, out, entries = self._run_with_registry(
            app.cmd_provider_add, "anthropic", "http://x/v1", npm=None, label=None, models=["m"],
        )
        self.assertEqual(rc, 2)
        self.assertIn("PROVIDER_RESERVED", out[0])
        self.assertEqual(entries, {}, "a rejected add must never write")

    def test_add_requires_at_least_one_model(self):
        rc, out, entries = self._run_with_registry(
            app.cmd_provider_add, "lmstudio", "http://x/v1", npm=None, label=None, models=(),
        )
        self.assertEqual(rc, 2)
        self.assertEqual(entries, {})

    def test_add_rejects_a_non_http_base_url(self):
        rc, out, entries = self._run_with_registry(
            app.cmd_provider_add, "lmstudio", "not-a-url", npm=None, label=None, models=["m"],
        )
        self.assertEqual(rc, 2)
        self.assertEqual(entries, {})

    def test_remove_unknown_id_is_rejected_not_silently_ok(self):
        rc, out, _ = self._run_with_registry(app.cmd_provider_remove, "nope")
        self.assertEqual(rc, 2)
        self.assertIn("PROVIDER_UNKNOWN", out[0])

    def test_verify_reports_missing_fields_only_declared_surface_no_network(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            broken = {"broken": pr.ProviderEntry(origin="user", spec={"npm": "x", "name": "n", "options": {}, "models": {}})}
            path.write_text(pr.serialize_providers_toml(broken))
            with mock.patch.object(app, "PROVIDERS_TOML_PATH", path):
                out = []
                with mock.patch("builtins.print", side_effect=lambda *args, **_: out.append(" ".join(map(str, args)))):
                    rc = app.cmd_provider_verify(None)
        self.assertEqual(rc, 1)
        self.assertIn("shape=invalid", out[0])
        self.assertIn("options.baseURL", out[0])
        self.assertIn("models", out[0])


# --------------------------------------------------------------- AC-18 (022 PKG-5): liveness


def _entry(origin, base_url="http://x/v1", models=("m",)):
    return pr.ProviderEntry(origin=origin, spec={
        "npm": "@ai-sdk/openai-compatible", "name": origin,
        "options": {"baseURL": base_url},
        "models": {m: {"name": m} for m in models},
    })


class ProviderLivenessUnitTests(unittest.TestCase):
    """`_provider_liveness` in isolation -- every branch mocked at `urllib.request.urlopen`,
    never a real socket: fast, hermetic, and exercises the exact three-way distinction
    AC-18 requires without depending on network availability in the sandbox."""

    def test_alive_on_a_normal_http_response(self):
        cm = mock.MagicMock()
        cm.__enter__.return_value = mock.MagicMock()
        cm.__exit__.return_value = False
        with mock.patch.object(app.urllib.request, "urlopen", return_value=cm):
            self.assertEqual(app._provider_liveness("http://x/v1"), "alive")

    def test_alive_on_an_http_error_status_the_server_still_answered(self):
        err = app.urllib.error.HTTPError("http://x/v1/models", 404, "not found", {}, None)
        with mock.patch.object(app.urllib.request, "urlopen", side_effect=err):
            self.assertEqual(app._provider_liveness("http://x/v1"), "alive")

    def test_dead_on_connection_refused_the_measured_ollama_case(self):
        wrapped = app.urllib.error.URLError(ConnectionRefusedError(111, "Connection refused"))
        with mock.patch.object(app.urllib.request, "urlopen", side_effect=wrapped):
            self.assertEqual(app._provider_liveness("http://localhost:11434/v1"), "dead")

    def test_unreachable_on_timeout_never_reported_as_dead(self):
        wrapped = app.urllib.error.URLError(TimeoutError("timed out"))
        with mock.patch.object(app.urllib.request, "urlopen", side_effect=wrapped):
            self.assertEqual(app._provider_liveness("http://x/v1"), "unreachable")

    def test_unreachable_on_dns_failure_never_reported_as_dead(self):
        wrapped = app.urllib.error.URLError(OSError("Name or service not known"))
        with mock.patch.object(app.urllib.request, "urlopen", side_effect=wrapped):
            self.assertEqual(app._provider_liveness("http://no-such-host.invalid/v1"), "unreachable")

    def test_unreachable_on_a_missing_or_empty_base_url_never_a_crash(self):
        self.assertEqual(app._provider_liveness(None), "unreachable")
        self.assertEqual(app._provider_liveness(""), "unreachable")


class ProviderVerifyLivenessScopeTests(unittest.TestCase):
    """AC-18: liveness is attempted ONLY for `origin=user` by default -- `harness`,
    `harness-legacy`, and `discovered` are shape-checked but never network-probed unless
    `--include-legacy` explicitly widens the scope to also cover `harness-legacy` (the
    real post-P4 Ollama interaction, resolved explicitly per the context pack, never
    left implicit)."""

    def _verify(self, entries, include_legacy=False, prune_dead=False, provider_id=None):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "providers.toml"
            path.write_text(pr.serialize_providers_toml(entries))
            with mock.patch.object(app, "PROVIDERS_TOML_PATH", path):
                out = []
                with mock.patch("builtins.print", side_effect=lambda *a, **_: out.append(" ".join(map(str, a)))):
                    rc = app.cmd_provider_verify(provider_id, include_legacy=include_legacy, prune_dead=prune_dead)
                final = pr.parse_providers_toml(path)
            return rc, out, final

    def test_default_scope_checks_user_never_harness_or_harness_legacy_or_discovered(self):
        entries = {
            "mine": _entry("user"), "seed": _entry("harness"),
            "ollama": _entry("harness-legacy"), "found": _entry("discovered"),
        }
        with mock.patch.object(app, "_provider_liveness", return_value="alive") as liveness:
            rc, out, _ = self._verify(entries)
        self.assertEqual(rc, 0)
        liveness.assert_called_once()  # only "mine" (origin=user) ever reaches the network call
        by_id = {line.split()[1]: line for line in out}
        self.assertIn("liveness=alive", by_id["mine"])
        for pid in ("seed", "ollama", "found"):
            self.assertNotIn("liveness=", by_id[pid])

    def test_include_legacy_widens_scope_to_harness_legacy_only_not_plain_harness_or_discovered(self):
        entries = {
            "mine": _entry("user"), "seed": _entry("harness"),
            "ollama": _entry("harness-legacy"), "found": _entry("discovered"),
        }
        with mock.patch.object(app, "_provider_liveness", return_value="dead") as liveness:
            rc, out, _ = self._verify(entries, include_legacy=True)
        self.assertEqual(liveness.call_count, 2)  # "mine" (user) and "ollama" (harness-legacy)
        by_id = {line.split()[1]: line for line in out}
        self.assertIn("liveness=dead", by_id["mine"])
        self.assertIn("liveness=dead", by_id["ollama"])
        self.assertNotIn("liveness=", by_id["seed"])
        self.assertNotIn("liveness=", by_id["found"])
        self.assertEqual(rc, 1)  # not everything measured alive

    def test_liveness_line_carries_a_measurement_timestamp(self):
        entries = {"mine": _entry("user")}
        with mock.patch.object(app, "_provider_liveness", return_value="alive"):
            _, out, _ = self._verify(entries)
        self.assertRegex(out[0], r"at=\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

    def test_shape_invalid_entry_is_never_liveness_checked_even_if_origin_is_user(self):
        entries = {"broken": pr.ProviderEntry(origin="user", spec={"npm": "x", "name": "n", "options": {}, "models": {}})}
        with mock.patch.object(app, "_provider_liveness") as liveness:
            rc, out, _ = self._verify(entries)
        liveness.assert_not_called()
        self.assertIn("shape=invalid", out[0])
        self.assertEqual(rc, 1)

    def test_prune_dead_removes_only_ids_measured_dead_this_run(self):
        entries = {
            "gone": _entry("user", base_url="http://gone/v1"),
            "flaky": _entry("user", base_url="http://flaky/v1"),
            "fine": _entry("user", base_url="http://fine/v1"),
            "seed": _entry("harness", base_url="http://seed/v1"),
        }
        results_by_url = {"http://gone/v1": "dead", "http://flaky/v1": "unreachable", "http://fine/v1": "alive"}
        with mock.patch.object(app, "_provider_liveness", side_effect=lambda url, **kw: results_by_url[url]):
            rc, out, final = self._verify(entries, prune_dead=True)
        self.assertIn("PROVIDER_PRUNED ids=gone", "\n".join(out))
        self.assertNotIn("gone", final)
        # unreachable is NOT evidence of absence -- never pruned; neither is a fully
        # healthy entry, nor one outside the liveness scope entirely.
        self.assertIn("flaky", final)
        self.assertIn("fine", final)
        self.assertIn("seed", final)

    def test_prune_dead_on_a_single_provider_id_never_drops_the_rest_of_the_registry(self):
        # Regression guard: pruning after a single-`provider_id` verify must write back
        # against the FULL registry, never the narrowed one-entry view.
        entries = {"gone": _entry("user", base_url="http://gone/v1"),
                   "untouched": _entry("user", base_url="http://untouched/v1")}
        with mock.patch.object(app, "_provider_liveness", return_value="dead"):
            rc, out, final = self._verify(entries, prune_dead=True, provider_id="gone")
        self.assertNotIn("gone", final)
        self.assertIn("untouched", final, "a single-id verify+prune must never wipe unrelated entries")

    def test_prune_dead_with_nothing_dead_is_a_no_op_and_says_so(self):
        entries = {"fine": _entry("user")}
        with mock.patch.object(app, "_provider_liveness", return_value="alive"):
            rc, out, final = self._verify(entries, prune_dead=True)
        self.assertIn("PROVIDER_PRUNE_NONE", "\n".join(out))
        self.assertIn("fine", final)


class LivenessNeverInHotPathTests(unittest.TestCase):
    """AC-18: "nunca dentro de route(), nunca en la clave de caché, nunca en el spawn" --
    a source-grep tripwire, same style as the existing ADR-0043 AC-10 lockstep guards:
    the liveness/empirical-verification functions must never even be IMPORTED by the
    modules that make routing decisions or spawn a runtime."""

    def test_service_py_never_imports_liveness_or_empirical_verification(self):
        text = (ROOT / "ai/scripts/routing_core/service.py").read_text()
        for name in ("_provider_liveness", "_verify_unlistable_credential", "probe_listed_and_usable"):
            self.assertNotIn(name, text)

    def test_cache_key_source_never_calls_liveness_or_empirical_verification(self):
        text = (ROOT / "ai/scripts/routing_core/catalog.py").read_text()
        cache_key_start = text.index("def _cache_key(")
        cache_key_body = text[cache_key_start:text.index("\ndef ", cache_key_start + 1)]
        self.assertNotIn("_provider_liveness", cache_key_body)
        self.assertNotIn("_verify_unlistable_credential", cache_key_body)

    def test_no_spawn_module_imports_liveness_or_empirical_verification(self):
        for path in (ROOT / "ai/scripts").glob("*_spawn.py"):
            text = path.read_text()
            self.assertNotIn("_provider_liveness", text, path)
            self.assertNotIn("_verify_unlistable_credential", text, path)


class ProviderCliSubprocessTests(unittest.TestCase):
    """A real `set_agents_app.py` invocation, HOME sandboxed — proves the CLI is wired
    end to end through argparse, not just the underlying functions."""

    def test_add_list_remove_round_trip_via_real_argv(self):
        with tempfile.TemporaryDirectory() as td:
            home = make_home(td)
            added = run("python3", "ai/scripts/set_agents_app.py", "--provider-add", "lmstudio",
                        "--base-url", "http://localhost:1234/v1", "--model", "m1:Model One",
                        env={"HOME": str(home)})
            self.assertIn("PROVIDER_ADDED", added.stdout)
            listed = run("python3", "ai/scripts/set_agents_app.py", "--provider-list", env={"HOME": str(home)})
            self.assertIn("PROVIDER lmstudio origin=user", listed.stdout)
            removed = run("python3", "ai/scripts/set_agents_app.py", "--provider-remove", "lmstudio", env={"HOME": str(home)})
            self.assertIn("PROVIDER_REMOVED id=lmstudio origin=user", removed.stdout)
            listed_after = run("python3", "ai/scripts/set_agents_app.py", "--provider-list", env={"HOME": str(home)})
            self.assertIn("PROVIDER_NONE", listed_after.stdout)

    def test_provider_verify_prune_dead_real_network_round_trip(self):
        """AC-18, end to end, real TCP: a `user` provider pointed at a loopback port
        nothing listens on measures REAL `dead` (no mock anywhere in this test) and
        `--prune-dead` removes exactly it -- the CLI flags wired through argparse, not
        just the underlying Python functions."""
        with tempfile.TemporaryDirectory() as td:
            home = make_home(td)
            dead_port = 39217  # unassigned, nothing binds it in CI/dev sandboxes
            added = run("python3", "ai/scripts/set_agents_app.py", "--provider-add", "deadendpoint",
                        "--base-url", f"http://127.0.0.1:{dead_port}/v1", "--model", "m1",
                        env={"HOME": str(home)})
            self.assertIn("PROVIDER_ADDED", added.stdout)
            verified = run("python3", "ai/scripts/set_agents_app.py", "--provider-verify",
                           env={"HOME": str(home)}, check=False)
            self.assertIn("liveness=dead", verified.stdout)
            self.assertRegex(verified.stdout, r"at=\d{4}-\d{2}-\d{2}T")
            pruned = run("python3", "ai/scripts/set_agents_app.py", "--provider-verify", "--prune-dead",
                        env={"HOME": str(home)}, check=False)
            self.assertIn("PROVIDER_PRUNED ids=deadendpoint", pruned.stdout)
            listed_after = run("python3", "ai/scripts/set_agents_app.py", "--provider-list", env={"HOME": str(home)})
            self.assertIn("PROVIDER_NONE", listed_after.stdout)


# --------------------------------------------------------------- install.py (AC-13/14/15)


class InstallProviderRenderTests(unittest.TestCase):
    def test_global_shared_opencode_json_no_longer_hardcodes_a_provider_block(self):
        """AC-13's own premise: the render must come from the registry because the
        overlay literally doesn't carry one anymore."""
        doc = json.loads((ROOT / "Global/_shared/opencode.json").read_text())
        self.assertNotIn("provider", doc)

    def test_fresh_install_seeds_the_registry_and_renders_ollama(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            result = run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            self.assertIn("INSTALL_PASS", result.stdout)
            registry = pr.parse_providers_toml(home / ".local/state/set-agentes/providers.toml")
            self.assertEqual(registry["ollama"].origin, "harness")
            block = live_provider_block(home)
            self.assertEqual(set(block), {"ollama"})
            self.assertEqual(block["ollama"], pr.HARNESS_PROVIDER_SEED["ollama"])

    def test_preview_never_writes_the_registry(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode", "--preview")
            self.assertFalse((home / ".local/state/set-agentes/providers.toml").exists())

    def test_removed_provider_does_not_come_back_on_a_later_install(self):
        """AC-13's core claim, measured, not argued: remove via the CLI, install again,
        confirm the block is gone from the LIVE opencode.json -- exactly the failure
        `deep_merge` used to reintroduce every run before this package."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            self.assertIn("ollama", live_provider_block(home))
            removed = run("python3", "ai/scripts/set_agents_app.py", "--provider-remove", "ollama", env={"HOME": str(home)})
            self.assertIn("PROVIDER_REMOVED", removed.stdout)
            # Still present right after removal -- removal only touches providers.toml,
            # never opencode.json directly (documented CLI contract).
            self.assertIn("ollama", live_provider_block(home))
            second = run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            self.assertIn("INSTALL_PASS", second.stdout)
            self.assertNotIn("ollama", live_provider_block(home) or {})
            # A THIRD install must not resurrect it either -- the registry file, once it
            # exists (even having had an entry removed), is authoritative forever.
            third = run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            self.assertIn("INSTALL_PASS", third.stdout)
            self.assertNotIn("ollama", live_provider_block(home) or {})

    def test_a_hand_added_foreign_provider_survives_an_install_that_prunes_a_different_one(self):
        """AC-14's OBLIGATORY test. There is no real user-owned provider on any measured
        machine today (context pack, P4) -- this is a FIXTURE by construction, stated
        here rather than implied: it simulates a block the user added by editing
        opencode.json directly, outside `set-agents` entirely (never registered, never
        in the JSON-subtree manifest)."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            oc_path = home / ".config/opencode/opencode.json"
            oc_path.write_text(json.dumps({
                "$schema": "https://opencode.ai/config.json",
                "provider": {
                    "ollama": dict(pr.HARNESS_PROVIDER_SEED["ollama"]),
                    "byhand": {"npm": "@ai-sdk/openai-compatible", "name": "My hand-added LLM",
                               "options": {"baseURL": "http://localhost:9999/v1"},
                               "models": {"whatever": {"name": "Whatever"}}},
                },
            }))
            state = home / ".local/state/set-agentes"
            state.mkdir(parents=True)
            (state / "providers.toml").write_text(pr.serialize_providers_toml(
                {"ollama": pr.ProviderEntry(origin="harness", spec=dict(pr.HARNESS_PROVIDER_SEED["ollama"]))}
            ))
            (state / "managed-json-paths.json").write_text(json.dumps({"opencode.json": ["ollama"]}))
            # Prune ollama from the registry -- "byhand" was never registered at all.
            (state / "providers.toml").write_text(pr.serialize_providers_toml({}))
            before_byhand = live_provider_block(home)["byhand"]
            result = run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            self.assertIn("INSTALL_PASS", result.stdout)
            block = live_provider_block(home)
            self.assertNotIn("ollama", block, "the registered-then-removed id must be pruned")
            self.assertIn("byhand", block, "an id the harness never registered must never be touched")
            self.assertEqual(block["byhand"], before_byhand, "must survive BYTE-IDENTICAL, not just present")

    def test_migration_from_a_live_file_distinguishes_harness_legacy_from_user(self):
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            oc_path = home / ".config/opencode/opencode.json"
            oc_path.write_text(json.dumps({
                "$schema": "https://opencode.ai/config.json",
                "provider": {
                    "ollama": dict(pr.HARNESS_PROVIDER_SEED["ollama"]),  # byte-identical
                    "lmstudio": {"npm": "@ai-sdk/openai-compatible", "name": "LM Studio",
                                 "options": {"baseURL": "http://localhost:1234/v1"},
                                 "models": {"foo": {"name": "Foo"}}},
                },
            }))
            run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            registry = pr.parse_providers_toml(home / ".local/state/set-agentes/providers.toml")
            self.assertEqual(registry["ollama"].origin, "harness-legacy")
            self.assertEqual(registry["lmstudio"].origin, "user")

    def test_migration_of_an_edited_same_id_block_is_user_never_harness_legacy(self):
        """The comparison is by VALUE, never by id -- 022 context pack's explicit
        instruction, exercised through the real install.py entry point this time (the
        unit test above already covers `seed_or_migrate` directly)."""
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as staging:
            home = make_home(td)
            build_staging(staging)
            edited = dict(pr.HARNESS_PROVIDER_SEED["ollama"])
            edited["name"] = "Ollama (edited by Federico)"
            (home / ".config/opencode/opencode.json").write_text(json.dumps({
                "$schema": "https://opencode.ai/config.json", "provider": {"ollama": edited},
            }))
            run("python3", "ai/scripts/install.py", "--staging", staging, "--home", str(home), "--target", "opencode")
            registry = pr.parse_providers_toml(home / ".local/state/set-agentes/providers.toml")
            self.assertEqual(registry["ollama"].origin, "user")


if __name__ == "__main__":
    unittest.main()
