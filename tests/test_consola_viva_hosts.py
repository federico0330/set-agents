"""045/046/047 — live console, instance overlay, hosts, effort_request."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import host_adapters  # noqa: E402
import models_config  # noqa: E402
import provider_registry  # noqa: E402
import setup_models  # noqa: E402
import set_agents_app as app  # noqa: E402


class ModelsOverlayTests(unittest.TestCase):
    def test_absent_overlay_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.local.toml"
            self.assertEqual(models_config.load_models_overlay(path), {})

    def test_write_and_effective_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.local.toml"
            models_config.write_models_overlay_field(
                ("areas", "implement"), "codex_effort", "xhigh", path=path)
            overlay = models_config.load_models_overlay(path)
            self.assertEqual(overlay["areas"]["implement"]["codex_effort"], "xhigh")
            factory = {
                "areas": {"implement": {"claude": "haiku", "codex": "gpt", "codex_effort": "low",
                                        "opencode": "openai/x", "cursor": "inherit"}},
                "roles": {},
            }
            effective = models_config.effective_models_config(factory, overlay)
            self.assertEqual(effective["areas"]["implement"]["codex_effort"], "xhigh")
            self.assertEqual(effective["areas"]["implement"]["claude"], "haiku")
            self.assertNotIn("_models_overlay", factory)

    def test_malformed_overlay_degrades(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "models.local.toml"
            path.write_text("not = [toml\n", encoding="utf-8")
            self.assertEqual(models_config.load_models_overlay(path), {})


class HostRegistryTests(unittest.TestCase):
    def test_seven_candidates_always_listed(self):
        rows = provider_registry.list_host_rows(which=lambda _: None)
        self.assertEqual([r[0] for r in rows], list(provider_registry.HOSTS))
        self.assertTrue(all(state == "ausente" for _, state in rows))

    def test_agy_present_without_models_is_unlistable(self):
        which = lambda name: "/bin/agy" if name == "agy" else None
        state = provider_registry.resolve_host_state("agy", which=which, model_count=0)
        self.assertEqual(state, "unlistable")

    def test_fx_present_is_sin_lane(self):
        which = lambda name: "/bin/fx" if name == "fx" else None
        state = provider_registry.resolve_host_state("fx", which=which)
        self.assertEqual(state, "sin lane")

    def test_providers_order_untouched(self):
        self.assertEqual(
            list(provider_registry.PROVIDERS),
            ["openai-codex", "anthropic", "opencode-zen", "opencode-go"],
        )

    def test_adapter_contract_complete(self):
        for host_id in ("agy", "fx", "copilot"):
            adapter = host_adapters.get_adapter(host_id)
            self.assertIsNotNone(adapter)
            for op in ("detect", "probe_models", "materialize", "install_harness"):
                self.assertTrue(callable(getattr(adapter, op)))

    def test_fx_deferred_reason_written(self):
        adapter = host_adapters.get_adapter("fx")
        self.assertIn("SPAWN_DEFERRED", adapter.spawn_deferred_reason or "")

    def test_agy_materialize_carries_effort(self):
        argv = host_adapters.get_adapter("agy").materialize("gemini-2.5-pro", "high")
        self.assertEqual(argv[:4], ["agy", "--print", "--model", "gemini-2.5-pro"])
        self.assertIn("--effort", argv)
        self.assertIn("high", argv)


class MenuAndPanelTests(unittest.TestCase):
    def test_home_surfaces_how_it_works_and_keeps_vault_out_of_simple_mode(self):
        """045 AC-C.1 still holds -- postura/metodología are one keystroke from the home, no
        --avanzado needed -- now stated over the stable keys instead of over label text."""
        simple = [action.key for action in app.visible_actions(experto=False)]
        expert = [action.key for action in app.visible_actions(experto=True)]
        self.assertIn("trabajo", simple)
        self.assertEqual(simple[-1], "salir")
        self.assertEqual(expert[-1], "salir")
        self.assertNotIn("vault", simple)
        self.assertIn("vault", expert)

    def test_panel_header_is_human_compact(self):
        config = models_config.load_config(ROOT / "models.toml")
        roster = models_config.load_roster(ROOT / "roles.tsv")
        with mock.patch.object(setup_models, "_load_pins", return_value={}), \
             mock.patch.object(models_config, "load_models_overlay", return_value={}):
            lines = setup_models._panel_lines(config, roster, detected=None)
        text = "\n".join(lines)
        self.assertLessEqual(len(lines), 3)
        self.assertNotIn("DEFAULTS CURADOS", text)
        self.assertNotIn(f"{'AREA':<10}", text)
        self.assertNotIn("ADR-", text)
        self.assertIn("Elige solo", text)

    def test_overrides_matrix_has_area_rows(self):
        config = models_config.load_config(ROOT / "models.toml")
        text = "\n".join(setup_models._overrides_matrix_lines(config))
        self.assertIn("Preferencias por area", text)
        self.assertIn("implement", text)

    def test_estado_lists_hosts(self):
        data = {"rows": [("claude", "1.0", "ok")], "drift": "ok"}
        with mock.patch.object(app, "_pi_lane_state", return_value="yes"), \
             mock.patch.object(app, "_install_scope", return_value=["claude-code"]), \
             mock.patch.object(app, "_tools_data", return_value=[]), \
             mock.patch.object(app.models_config, "load_config", side_effect=OSError("hermetic")), \
             mock.patch.object(host_adapters, "probe_host_model_counts", return_value={}):
            lines = app._estado_general_lines(data)
        text = "\n".join(lines)
        self.assertIn("Tus CLIs de IA", text)
        # 046 AC-01: all seven candidates are listed, absent ones included. The panel shows
        # each host's display name, so that is what is asserted -- `ui.HOST_TITLES` is the one
        # map from host id to the word a person reads.
        import ui
        for host_id in provider_registry.HOSTS:
            self.assertIn(ui.HOST_TITLES[host_id], text, f"falta el host {host_id}")
        self.assertNotIn("listado=", text)


class EffortRequestTests(unittest.TestCase):
    def test_invalid_effort_request_is_parse_failure(self):
        descriptor = json.dumps({
            "role": "implementer", "task_class": "scoped", "risk": "low",
            "selected_runtime": "opencode", "effort_request": "ludicrous",
        })
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            handle.write(descriptor)
            path = handle.name
        try:
            with mock.patch.object(app.sys, "stdout"), mock.patch.object(app.sys, "stderr"):
                # _routing_output writes; capture return code only
                rc = app.cmd_route_decide(path, human=False)
            self.assertEqual(rc, 2)
        finally:
            os.unlink(path)

    def test_efforts_constant_matches_catalog(self):
        config = models_config.load_config(ROOT / "models.toml")
        self.assertTrue(set(config["catalog"]["codex_effort"]) <= set(models_config.EFFORTS))


if __name__ == "__main__":
    unittest.main()
