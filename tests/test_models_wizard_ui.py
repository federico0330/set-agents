"""UI refresh — the Modelos wizard stops dumping and learns ADR-0029.

New tests only. The immutable suite pins WIZARD_ITEMS indexes 0-4 and the
dropped-cells hint; here we cover the compact panel (`_panel_lines`), the
end of the double status dump, the tri-state subscriptions branch, and the
discovered-providers toggle.
"""

import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import setup_models  # noqa: E402


def _config():
    return {
        "areas": {"audit": {"claude": "opus", "codex": "gpt-5.5", "codex_effort": "high",
                            "opencode": {"go-zen": "openai/gpt-5.5"}}},
        "roles": {"debugger": {"claude": "opus"}, "implementer": {"codex": "gpt-5.4"}},
        "subscriptions": {"anthropic": True, "ollama": False},
        "routing": {"discovered_providers": []},
    }


class PanelLinesTests(unittest.TestCase):
    def test_panel_is_compact_overrides_collapse_to_a_count(self):
        lines = setup_models._panel_lines(_config(), [], "go-zen", detected=None)
        text = "\n".join(lines)
        self.assertIn("audit", text)
        self.assertIn("overrides de rol: 2", text)
        self.assertNotIn("debugger:", text)  # the old per-role dump is gone

    def test_tri_state_origins_pin_off_and_auto(self):
        lines = setup_models._panel_lines(_config(), [], "go-zen", detected={"openai", "anthropic"})
        subs_line = lines[0]
        self.assertIn("anthropic=✓pin", subs_line)
        self.assertIn("ollama=✗off", subs_line)
        self.assertIn("openai=auto✓", subs_line)  # absent key, probe-alive

    def test_discovered_providers_surface_when_configured(self):
        config = _config()
        config["routing"]["discovered_providers"] = ["opencode-zen"]
        text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("opencode-zen", text)

    def test_auto_resolves_the_live_inventory_never_iterates_the_string(self):
        # ADR-0035 (AC-16): the exact defect this replaces -- `list("auto")` printing
        # "a, u, t, o" -- reproduced live before this fix and registered as the package's
        # first task. `"auto"` is a policy, resolved via `_resolve_live_discovered`,
        # never iterated as a string.
        config = _config()
        config["routing"]["discovered_providers"] = "auto"
        with mock.patch.object(setup_models, "_resolve_live_discovered",
                               return_value=("opencode-zen", "opencode-go")):
            text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("proveedores descubiertos rutables: auto → opencode-zen (metered), "
                      "opencode-go (suscripción)", text)
        self.assertNotIn("a, u, t, o", text)

    def test_auto_with_nothing_live_says_so_instead_of_iterating(self):
        config = _config()
        config["routing"]["discovered_providers"] = "auto"
        with mock.patch.object(setup_models, "_resolve_live_discovered", return_value=()):
            text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("auto → ninguno vivo ahora", text)

    def test_auto_probe_failure_degrades_to_an_explicit_message(self):
        config = _config()
        config["routing"]["discovered_providers"] = "auto"
        with mock.patch.object(setup_models, "_resolve_live_discovered", return_value=None):
            text = "\n".join(setup_models._panel_lines(config, [], "go-zen"))
        self.assertIn("auto → no verificable ahora", text)


class PanelAgeAndDegradeTests(unittest.TestCase):
    def test_panel_shows_subscription_age(self):
        lines = setup_models._panel_lines(
            _config(), [], "go-zen", detected={"openai"},
            subscription_age_s=4 * 60 + 20,
        )
        self.assertIn("suscripciones: hace 4 min", lines[0])
        self.assertIn("openai=auto✓", lines[0])

    def test_panel_degrades_named_when_probe_failed(self):
        lines = setup_models._panel_lines(
            _config(), [], "go-zen", detected=None, subscription_error=True,
        )
        self.assertIn(setup_models.SUBSCRIPTION_PROBE_FAILED, lines[0])
        self.assertIn("anthropic=✓pin", lines[0])

    def test_wizard_passes_explicit_live_discovered_so_first_paint_does_not_probe(self):
        config = _config()
        config["routing"]["discovered_providers"] = "auto"
        with mock.patch.object(setup_models, "_resolve_live_discovered") as probe:
            text = "\n".join(setup_models._panel_lines(
                config, [], "go-zen", live_discovered=None))
        probe.assert_not_called()
        self.assertIn("auto → no verificable ahora", text)


class WizardBehaviorTests(unittest.TestCase):
    def _run(self, picks, config=None):
        config = config or _config()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions", return_value=None), \
             mock.patch.object(setup_models.tui, "with_progress",
                               side_effect=lambda msg, fn, **kwargs: fn()), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=picks) as picker:
            buf = io.StringIO()
            with mock.patch("sys.stdout", buf):
                setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                    Path("roles.tsv"), Path("models.toml"))
        return config, buf.getvalue(), picker

    def test_the_status_avalanche_is_gone_from_stdout(self):
        _, out, picker = self._run([None])  # Esc right away
        self.assertNotIn("AREA", out)
        self.assertIn("AREA", picker.call_args.kwargs["header"])  # lives in the picker frame

    def test_subscription_auto_writes_the_overlay_never_the_tracked_config(self):
        # ADR-0048 (024 C2, AC-05): the wizard's Suscripciones no longer touches
        # `config["subscriptions"]` (the tracked models.toml) at all -- it writes the
        # per-machine overlay, immediately, which is what stops a subscription toggle
        # from dirtying the tree and blocking --update forever (tree_clean()).
        with mock.patch.object(setup_models.models_config, "write_subscription_overlay",
                               return_value={"anthropic": True}) as write:
            config, out, _ = self._run([
                setup_models.tui.Selected(2),   # Suscripciones
                setup_models.tui.Selected(1),   # choose(): "ollama" -- candidate universe is
                                                 # now the audited 4 names, sorted: anthropic,
                                                 # ollama, openai, zen (index 1 == ollama)
                setup_models.tui.Selected(2),   # tri-state: Auto (el probe decide)
                setup_models.tui.Selected(4),   # Salir sin guardar
            ])
        write.assert_called_once_with("ollama", None)
        self.assertEqual(config["subscriptions"], {"anthropic": True, "ollama": False})
        self.assertEqual(config["_subscriptions_overlay"], {"anthropic": True})
        self.assertIn("auto en este equipo", out)
        self.assertIn("efectivo ya", out)

    def test_discovered_provider_toggle_round_trips(self):
        # ADR-0035 (AC-16): option 7 is now a three-way policy picker (auto/manual/none);
        # "Lista manual" (index 1) still offers the per-provider toggle, but its
        # candidates come from `models_config.DISCOVERABLE_PROVIDERS` (sorted:
        # anthropic, openai-codex, opencode-go, opencode-zen), not a literal tuple --
        # index 3 in that sorted list is `opencode-zen`.
        config, out, _ = self._run([
            setup_models.tui.Selected(6),   # Proveedores descubiertos
            setup_models.tui.Selected(1),   # Lista manual
            setup_models.tui.Selected(3),   # opencode-zen (sorted DISCOVERABLE_PROVIDERS)
            setup_models.tui.Selected(4),   # Salir sin guardar
        ])
        self.assertEqual(config["routing"]["discovered_providers"], ["opencode-zen"])
        self.assertIn("MODEL_METADATA_INFERRED", out)

    def test_discovered_provider_auto_and_none_policies(self):
        config, out, _ = self._run([
            setup_models.tui.Selected(6),   # Proveedores descubiertos
            setup_models.tui.Selected(0),   # auto (recomendado)
            setup_models.tui.Selected(4),   # Salir sin guardar
        ])
        self.assertEqual(config["routing"]["discovered_providers"], "auto")
        self.assertIn("discovered_providers = auto", out)

        config, out, _ = self._run([
            setup_models.tui.Selected(6),   # Proveedores descubiertos
            setup_models.tui.Selected(2),   # Ninguno
            setup_models.tui.Selected(4),   # Salir sin guardar
        ])
        self.assertEqual(config["routing"]["discovered_providers"], [])

    def test_refresh_is_appended_indexes_0_4_stay_pinned(self):
        _, _, picker = self._run([None])
        items = picker.call_args.args[0]
        self.assertEqual(
            items[:5],
            ("Cambiar un área", "Cambiar un rol", "Suscripciones", "Guardar", "Salir sin guardar"),
        )
        self.assertEqual(items[-1], setup_models.REFRESH_ITEM)

    def test_first_paint_does_not_call_detect_subscriptions(self):
        config = _config()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions") as probe, \
             mock.patch.object(setup_models.tui, "run_picker",
                               return_value=setup_models.tui.Selected(4)):
            setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                Path("roles.tsv"), Path("models.toml"))
        probe.assert_not_called()

    def test_refresh_key_probes_via_with_progress_and_redraws(self):
        config = _config()
        progress_messages = []

        def fake_progress(message, fn, **kwargs):
            progress_messages.append(message)
            return fn()

        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions",
                               return_value={"openai"}), \
             mock.patch.object(setup_models.tui, "with_progress", side_effect=fake_progress), \
             mock.patch.object(setup_models, "_fetch_opencode_models",
                               return_value=["openai/gpt-5.5"]), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=[
                 setup_models.tui.Selected(8),  # refresh (last item)
                 setup_models.tui.Selected(4),  # salir
             ]) as picker:
            setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                Path("roles.tsv"), Path("models.toml"))
        self.assertIn("midiendo suscripciones", progress_messages)
        self.assertIn("listando modelos", progress_messages)
        second_header = picker.call_args_list[1].kwargs["header"]
        self.assertIn("openai=auto✓", second_header)
        self.assertIn("suscripciones: hace 0 min", second_header)

    def test_refresh_degrades_named_when_probe_raises_and_stays_usable(self):
        config = _config()

        def boom(*_args, **_kwargs):
            raise RuntimeError("probe down")

        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions", side_effect=boom), \
             mock.patch.object(setup_models.tui, "with_progress",
                               side_effect=lambda msg, fn, **kwargs: fn()), \
             mock.patch.object(setup_models, "_fetch_opencode_models", return_value=[]), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=[
                 setup_models.tui.Selected(8),
                 setup_models.tui.Selected(4),
             ]) as picker:
            rc = setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                     Path("roles.tsv"), Path("models.toml"))
        self.assertEqual(rc, 0)
        second_header = picker.call_args_list[1].kwargs["header"]
        self.assertIn(setup_models.SUBSCRIPTION_PROBE_FAILED, second_header)
        self.assertIn("anthropic=✓pin", second_header)

    def test_disk_cache_age_is_on_the_first_frame(self):
        config = _config()
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}):
            setup_models.models_config.write_wizard_live_cache(
                "subscriptions",
                {"at": setup_models.time.time() - 4 * 60, "names": ["openai"], "error": False},
            )
            with mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
                 mock.patch.object(setup_models.models_config, "detect_subscriptions") as probe, \
                 mock.patch.object(setup_models.tui, "run_picker",
                                   return_value=setup_models.tui.Selected(4)) as picker:
                setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                    Path("roles.tsv"), Path("models.toml"))
        probe.assert_not_called()
        header = picker.call_args.kwargs["header"]
        self.assertIn("suscripciones: hace 4 min", header)
        self.assertIn("openai=auto✓", header)

    def test_stale_cache_auto_probes_after_first_paint_not_before(self):
        counts, progress = [], []

        def fake_picker(*_a, **_k):
            counts.append(probe.call_count)
            return [setup_models.tui.Selected(0), None, setup_models.tui.Selected(4)][len(counts) - 1]
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions",
                               return_value={"openai"}) as probe, \
             mock.patch.object(setup_models.tui, "with_progress",
                               side_effect=lambda msg, fn, **kw: progress.append(msg) or fn()), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=fake_picker):
            setup_models.wizard(_config(), [{"role": "audit"}], "go-zen",
                                Path("roles.tsv"), Path("models.toml"))
        self.assertEqual(counts[:2], [0, 0])
        self.assertGreaterEqual(counts[2], 1)
        self.assertIn("midiendo suscripciones", progress)

    def test_auto_live_measure_fills_live_discovered_not_probe_failed(self):
        config = _config()
        config["routing"]["discovered_providers"] = "auto"
        inventory = {("opencode", "opencode-zen"): ["opencode/x"]}

        def fake_detect(_config, inventory_holder=None, **_kw):
            if inventory_holder is not None:
                inventory_holder.append(inventory)
            return {"openai"}
        picks = [setup_models.tui.Selected(0), None, setup_models.tui.Selected(4)]
        with tempfile.TemporaryDirectory() as td, \
             mock.patch.dict(os.environ, {"SET_AGENTS_STATE": td}), \
             mock.patch.object(setup_models.sys.stdin, "isatty", return_value=True), \
             mock.patch.object(setup_models.models_config, "detect_subscriptions",
                               side_effect=fake_detect), \
             mock.patch.object(setup_models.tui, "with_progress",
                               side_effect=lambda msg, fn, **kw: fn()), \
             mock.patch.object(setup_models.tui, "run_picker", side_effect=picks) as picker:
            setup_models.wizard(config, [{"role": "audit"}], "go-zen",
                                Path("roles.tsv"), Path("models.toml"))
        first, second = picker.call_args_list[0].kwargs["header"], picker.call_args_list[2].kwargs["header"]
        self.assertNotIn("probe falló", first)
        self.assertNotIn("probe falló", second)
        self.assertIn("opencode-zen", second)


class GroupedModelPickerTests(unittest.TestCase):
    def test_choose_groups_by_provider_and_maps_selected_index_to_the_model_id(self):
        models = ["opencode-go/a", "opencode-go/b-free", "openai/x"]
        captured = {}

        def fake_picker(items, **kwargs):
            captured["items"] = list(items)
            captured["headers"] = list(kwargs.get("headers") or [])
            captured["suffixes"] = list(kwargs.get("suffixes") or [])
            captured["current"] = kwargs.get("current")
            return setup_models.tui.Selected(2)  # second model under opencode-go

        with mock.patch.object(setup_models.tui, "run_picker", side_effect=fake_picker):
            result = setup_models.choose(
                "Modelo", models, current="opencode-go/b-free",
                group_by_provider=True,
                used_by={"opencode-go/a": ["implementer"]},
            )
        self.assertEqual(result, "opencode-go/b-free")
        self.assertEqual(captured["items"][0], "opencode-go (2)")
        self.assertEqual(captured["items"][3], "openai (1)")
        self.assertEqual(captured["headers"], [0, 3])
        self.assertEqual(captured["current"], "opencode-go/b-free")
        self.assertIn("free", captured["suffixes"][2])
        self.assertIn("← implementer", captured["suffixes"][1])
        self.assertNotIn(captured["items"][0], models)  # a header is never a model id

    def test_choose_without_grouping_keeps_a_flat_index_into_options(self):
        options = ["claude", "codex", "effort"]
        with mock.patch.object(
            setup_models.tui, "run_picker", return_value=setup_models.tui.Selected(1),
        ) as picker:
            result = setup_models.choose("Campo", options)
        self.assertEqual(result, "codex")
        self.assertEqual(list(picker.call_args.args[0]), options)
        self.assertEqual(list(picker.call_args.kwargs.get("headers") or []), [])


if __name__ == "__main__":
    unittest.main()
