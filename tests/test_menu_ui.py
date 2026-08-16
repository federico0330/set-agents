"""UI refresh — main menu personalized to the harness.

New tests only: the shared width-aware panel renderer (`table_lines`), the
'Estado general' panel content, and the Instalar/Reparar harness selector
(gentle-ai-style onboarding). The immutable suite keeps pinning Vault-before-
Salir, the Esc contract, and the tools_menu row format — nothing here may
contradict those.
"""

import contextlib
import io
import os
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


class _FakeStream(io.StringIO):
    """`StringIO` with a controllable `isatty()` -- mirrors `tests/test_harness.py`'s
    `_FakeStdout`, kept local here (own-paths discipline: this file doesn't import that
    one) so `--route-doctor`/`--doctor-all`'s progress indicator can be exercised as a
    LIVE (animated) stream without a real pty."""

    def __init__(self, is_tty):
        super().__init__()
        self._is_tty = is_tty

    def isatty(self):
        return self._is_tty


class RouteDoctorProgressTests(unittest.TestCase):
    """025/D2 (AC-04/AC-05): the progress indicator wrapping `--route-doctor`'s ~20s provider
    probe (`route_doctor`, `catalog.py:1136`) never touches stdout -- the JSON envelope's
    contract (D1, AC-03) -- and never leaves the operation silent, live or degraded."""

    def _run(self, *, human, stderr_stream, env):
        fake_report = {"cache": {"used": False, "reason": "CACHE_ROOT_ABSENT"}, "providers": []}
        stdout_buf = io.StringIO()
        with mock.patch("routing_core.catalog.prune_legacy_probe_cache", return_value=False), \
             mock.patch("routing_core.catalog.route_doctor", return_value=fake_report), \
             mock.patch.object(app, "ROUTING_WARNINGS", ()), \
             mock.patch.dict(os.environ, env, clear=False), \
             mock.patch("sys.stderr", stderr_stream), \
             contextlib.redirect_stdout(stdout_buf):
            rc = app.cmd_route_doctor(human=human)
        return rc, stdout_buf.getvalue(), stderr_stream.getvalue()

    def test_json_stdout_is_byte_identical_whether_or_not_the_spinner_animates(self):
        # Mordida #1 at the command level: same `--route-doctor --json` bytes on stdout
        # whether the spinner is live (stderr is a TTY) or degraded (stderr is piped too).
        env_live = {"NO_COLOR": "", "TERM": "xterm"}
        env_degraded = {"NO_COLOR": "", "TERM": "xterm"}
        rc_live, stdout_live, stderr_live = self._run(
            human=False, stderr_stream=_FakeStream(is_tty=True), env=env_live)
        rc_degraded, stdout_degraded, stderr_degraded = self._run(
            human=False, stderr_stream=_FakeStream(is_tty=False), env=env_degraded)
        fake_report = {"cache": {"used": False, "reason": "CACHE_ROOT_ABSENT"}, "providers": []}
        expected = app.json.dumps(app.routing.cli_envelope(
            True, "route-doctor", fake_report, (), ()), sort_keys=True) + "\n"
        self.assertEqual(rc_live, 0)
        self.assertEqual(rc_degraded, 0)
        self.assertEqual(stdout_live, stdout_degraded)
        self.assertEqual(stdout_live, expected)
        # The DIFFERENCE lives entirely on stderr: live got a spinner, degraded got a
        # static line -- proving the spinner ran at all in the live case, not that both
        # cases silently skipped it.
        self.assertIn("\r", stderr_live)
        self.assertNotIn("\r", stderr_degraded)

    def test_no_color_pipe_never_leaves_route_doctor_silent(self):
        # Mordida #2 at the command level (AC-05): the exact env the harness's own spawns
        # force (opencode_spawn.py:202, codex_spawn.py:222, set_agents_spawn.py:115).
        stderr_stream = _FakeStream(is_tty=False)
        rc, stdout, stderr = self._run(
            human=False, stderr_stream=stderr_stream, env={"NO_COLOR": "1", "TERM": "dumb"})
        self.assertEqual(rc, 0)
        self.assertNotIn("\r", stderr)
        self.assertNotIn("\x1b", stderr)
        self.assertIn("consultando routing: listo", stderr)


class DoctorAllProgressTests(unittest.TestCase):
    """Same discipline as `RouteDoctorProgressTests`, for `--doctor-all`'s
    `probe_listed_and_usable` (`catalog.py:1238`) -- it has no `--json` mode, so the
    interesting assertion is stdout purity of the progress mechanism itself plus the
    persistent stderr line under degradation, not byte-for-byte stdout equality."""

    def _run(self, *, stderr_stream, env):
        with mock.patch("routing_core.catalog.prune_legacy_probe_cache", return_value=False), \
             mock.patch("routing_core.catalog.probe_listed_and_usable", return_value=({}, {})), \
             mock.patch.dict(os.environ, env, clear=False), \
             mock.patch("sys.stderr", stderr_stream):
            rc = app.cmd_doctor_all()
        return rc

    def test_no_color_pipe_never_leaves_doctor_all_silent(self):
        stderr_stream = _FakeStream(is_tty=False)
        rc = self._run(stderr_stream=stderr_stream, env={"NO_COLOR": "1", "TERM": "dumb"})
        out = stderr_stream.getvalue()
        self.assertEqual(rc, 0)
        self.assertNotIn("\r", out)
        self.assertNotIn("\x1b", out)
        self.assertIn("consultando proveedores: listo", out)
