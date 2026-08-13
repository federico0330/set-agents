"""UI refresh — main menu personalized to the harness.

New tests only: the shared width-aware panel renderer (`table_lines`), the
'Estado general' panel content, and the Instalar/Reparar harness selector
(gentle-ai-style onboarding). The immutable suite keeps pinning Vault-before-
Salir, the Esc contract, and the tools_menu row format — nothing here may
contradict those.
"""

import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import set_agents_app as app  # noqa: E402


class TableLinesTests(unittest.TestCase):
    def test_columns_align_to_the_widest_cell(self):
        with mock.patch.object(app.shutil, "get_terminal_size", return_value=__import__("os").terminal_size((120, 24))):
            lines = app.table_lines([("gh", "instalado"), ("supabase", "falta")])
        self.assertEqual(lines, ["  gh        instalado", "  supabase  falta"])

    def test_lines_clip_to_the_live_terminal_width(self):
        with mock.patch.object(app.shutil, "get_terminal_size", return_value=__import__("os").terminal_size((46, 24))):
            lines = app.table_lines([("x" * 60,)])
        self.assertEqual(len(lines[0]), 46)
        self.assertTrue(lines[0].endswith("…"))

    def test_empty_rows_render_nothing(self):
        self.assertEqual(app.table_lines([]), [])


class EstadoGeneralTests(unittest.TestCase):
    def test_panel_carries_harnesses_scope_tools_and_providers(self):
        data = {"rows": [("claude", "1.0", "ok")], "drift": "ok"}
        with mock.patch.object(app, "_pi_lane_state", return_value="via-pnpm-dlx"), \
             mock.patch.object(app, "_install_scope", return_value=["claude-code", "pi"]), \
             mock.patch.object(app, "_tools_data", return_value=[("gh", True)]), \
             mock.patch.object(app.models_config, "load_config", side_effect=OSError("hermetic")):
            lines = app._estado_general_lines(data)
        text = "\n".join(lines)
        self.assertIn("Harnesses", text)
        self.assertIn("vía pnpm dlx", text)
        self.assertIn("claude-code, pi", text)
        self.assertIn("gh", text)
        self.assertIn("probe no disponible", text)
        self.assertNotIn("drift:", text)

    def test_ac19_panel_labels_listado_and_usable_separately_when_they_differ(self):
        # AC-19: the 'vidriera' surface (first menu item) -- proven with a listed/
        # usable pair that genuinely DIFFERS, so a regression that reused one count
        # for both labels (or dropped the split entirely, back to a bare `models=<N>`)
        # fails this test, not just "some numbers printed".
        data = {"rows": [], "drift": "ok"}
        fake_listed = {("opencode", "opencode-zen"): {"a", "b", "c"}}
        fake_usable = {("opencode", "opencode-zen"): {"a"}}
        with mock.patch.object(app, "_pi_lane_state", return_value="no"), \
             mock.patch.object(app, "_install_scope", return_value=None), \
             mock.patch.object(app, "_tools_data", return_value=[]), \
             mock.patch.object(app.models_config, "load_config", return_value={}), \
             mock.patch("routing_core.catalog.prune_legacy_probe_cache", return_value=False), \
             mock.patch("routing_core.catalog.probe_listed_and_usable", return_value=(fake_listed, fake_usable)):
            text = "\n".join(app._estado_general_lines(data))
        self.assertIn("listado=3", text)
        self.assertIn("usable=1", text)

    def test_stale_drift_adds_the_repair_hint(self):
        data = {"rows": [], "drift": "stale"}
        with mock.patch.object(app, "_pi_lane_state", return_value="no"), \
             mock.patch.object(app, "_install_scope", return_value=None), \
             mock.patch.object(app, "_tools_data", return_value=[]), \
             mock.patch.object(app.models_config, "load_config", side_effect=OSError("hermetic")):
            text = "\n".join(app._estado_general_lines(data))
        self.assertIn("Instalar / Reparar", text)


class MenuDispatchTests(unittest.TestCase):
    def _menu(self, picks):
        with mock.patch.object(app, "first_run", return_value=False), \
             mock.patch.object(app, "launch_update_check", return_value="al día"), \
             mock.patch.object(app, "drift_state", return_value="ok"), \
             mock.patch.object(app, "banner"), \
             mock.patch.object(app, "short_sha", return_value="abc"), \
             mock.patch.object(app, "auto_update_enabled", return_value=True), \
             mock.patch.object(app.tui, "run_picker", side_effect=picks) as picker, \
             mock.patch.object(app, "run_tty", return_value=0) as tty, \
             mock.patch("sys.stdout", io.StringIO()):
            rc = app.menu()
        return rc, picker, tty

    def test_estado_general_is_first_and_renders_inside_the_picker_frame(self):
        with mock.patch.object(app, "_status_data", return_value={"rows": [], "drift": "ok",
                                                                  "sha": "abc", "behind": 0,
                                                                  "auto_update": True}), \
             mock.patch.object(app, "_estado_general_lines", return_value=["Harnesses"]):
            rc, picker, _ = self._menu([app.tui.Selected(0), None, None])
        self.assertEqual(rc, 0)
        estado_call = picker.call_args_list[1]
        self.assertIn("Harnesses", estado_call.kwargs["header"])

    def test_instalar_picks_a_harness_and_passes_it_to_install_sh(self):
        rc, _, tty = self._menu([app.tui.Selected(1), app.tui.Selected(2), None])
        self.assertEqual(rc, 0)
        command = tty.call_args.args[0]
        self.assertTrue(command[0].endswith("install.sh"))
        self.assertEqual(command[1:], ["--harness", "opencode"])

    def test_cancelling_the_harness_picker_runs_nothing(self):
        rc, _, tty = self._menu([app.tui.Selected(1), None, None])
        self.assertEqual(rc, 0)
        tty.assert_not_called()

    def test_menu_items_start_with_estado_general(self):
        self.assertIn("Estado general", app.MENU_ITEMS[0])


if __name__ == "__main__":
    unittest.main()


class ToolsHeaderTests(unittest.TestCase):
    def test_header_lists_method_and_note_per_tool(self):
        catalog = {"cli": {"vercel": {"detect": "vercel", "note": "cli de vercel",
                                      "install": {"npm": "npm install -g vercel"}}}}
        with mock.patch.object(app, "load_catalog", return_value=catalog), \
             mock.patch.object(app.shutil, "which", return_value=None), \
             mock.patch.object(app, "pick_method", return_value="npm"):
            header = app._tools_header()
        self.assertIn("vercel", header)
        self.assertIn("npm", header)
        self.assertIn("cli de vercel", header)

    def test_tools_menu_still_installs_on_enter_with_the_pinned_rows(self):
        # The immutable suite pins this too; asserted here so THIS package's header
        # addition can't have changed the picker items or the install dispatch.
        with mock.patch.object(app, "_tools_data", return_value=[("jq", True), ("vercel", False)]), \
             mock.patch.object(app, "_tools_header", return_value="x"), \
             mock.patch.object(app.tui, "run_picker", return_value=app.tui.Selected(1)) as picker, \
             mock.patch.object(app, "cmd_tools_install") as install:
            app.tools_menu()
        install.assert_called_once_with("vercel")
        self.assertEqual(picker.call_args.kwargs["header"], "x")
