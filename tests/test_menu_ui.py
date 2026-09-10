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
import time
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
    def test_panel_carries_harnesses_scope_and_tools_without_probe_jargon(self):
        data = {"rows": [("claude", "1.0", "ok")], "drift": "ok"}
        with mock.patch.object(app, "_pi_lane_state", return_value="via-pnpm-dlx"), \
             mock.patch.object(app, "_install_scope", return_value=["claude-code", "pi"]), \
             mock.patch.object(app, "_tools_data", return_value=[("gh", True)]), \
             mock.patch.object(app.models_config, "load_config", side_effect=OSError("hermetic")):
            lines = app._estado_general_lines(data)
        text = "\n".join(lines)
        self.assertIn("Versiones y sesión", text)
        self.assertIn("vía pnpm dlx", text)
        self.assertIn("claude-code, pi", text)
        self.assertIn("gh", text)
        self.assertNotIn("listado=", text)
        self.assertNotIn("usable=", text)
        self.assertNotIn("probe no disponible", text)
        self.assertNotIn("drift:", text)

    def test_estado_omits_listado_usable_doctor_detail(self):
        # End-user Estado: probe detail stays in --doctor-all, not the home panel.
        data = {"rows": [], "drift": "ok"}
        with mock.patch.object(app, "_pi_lane_state", return_value="no"), \
             mock.patch.object(app, "_install_scope", return_value=None), \
             mock.patch.object(app, "_tools_data", return_value=[]), \
             mock.patch.object(app.models_config, "load_config", return_value={}):
            text = "\n".join(app._estado_general_lines(data))
        self.assertNotIn("listado=", text)
        self.assertNotIn("usable=", text)
        self.assertIn("Tus CLIs de IA", text)

    def test_stale_drift_adds_the_repair_hint(self):
        data = {"rows": [], "drift": "stale"}
        with mock.patch.object(app, "_pi_lane_state", return_value="no"), \
             mock.patch.object(app, "_install_scope", return_value=None), \
             mock.patch.object(app, "_tools_data", return_value=[]), \
             mock.patch.object(app.models_config, "load_config", side_effect=OSError("hermetic")):
            text = "\n".join(app._estado_general_lines(data))
        self.assertIn("Configurar", text)


class MenuDispatchTests(unittest.TestCase):
    """The home dispatches on a stable key (ADR-0074), so these tests name the ACTION they
    want and let the helper find its row. A pin on the integer position would have stayed
    green if the label ever moved to a different branch; naming the key cannot."""

    def _key_index(self, key, experto=False):
        keys = [action.key for action in app.visible_actions(experto=experto)]
        self.assertIn(key, keys, f"la acción {key!r} desapareció del home")
        return keys.index(key)

    def _pick(self, key, experto=False):
        return app.tui.Selected(self._key_index(key, experto=experto))

    def _menu(self, picks, experto=False):
        with mock.patch.object(app, "first_run", return_value=False), \
             mock.patch.object(app, "launch_update_check", return_value="al dia"), \
             mock.patch.object(app, "measure_hosts", return_value={}), \
             mock.patch.object(app, "experto_activo", return_value=experto), \
             mock.patch.object(app, "drift_state", return_value="ok"), \
             mock.patch.object(app, "banner"), \
             mock.patch.object(app, "short_sha", return_value="abc"), \
             mock.patch.object(app, "auto_update_enabled", return_value=True), \
             mock.patch.object(app, "_home_header", return_value="SET"), \
             mock.patch.object(app.tui, "run_picker", side_effect=picks) as picker, \
             mock.patch.object(app, "run_tty", return_value=0) as tty, \
             mock.patch("sys.stdout", io.StringIO()):
            rc = app.menu()
        return rc, picker, tty

    def test_estado_renders_inside_the_pickers_own_frame(self):
        with mock.patch.object(app, "_status_data", return_value={"rows": [], "drift": "ok",
                                                                  "sha": "abc", "behind": 0,
                                                                  "auto_update": True}) as status:
            rc, picker, _ = self._menu([self._pick("estado"), None, None])
        self.assertEqual(rc, 0)
        estado_call = picker.call_args_list[1]
        self.assertIn("Instalación", estado_call.kwargs["header"])
        self.assertIn("Actualizar estado", estado_call.kwargs["header"])
        status.assert_not_called()

    def test_actualizar_is_the_only_estado_path_that_measures(self):
        ctx = {"drift": "unknown", "update_badge": "sin revisar"}
        with mock.patch.object(app, "launch_update_check", return_value="al día") as update, \
             mock.patch.object(app, "measure_hosts_visibly") as hosts, \
             mock.patch.object(app, "drift_state", return_value="ok") as drift:
            app._run_home_action("actualizar", {}, ctx)
        update.assert_called_once()
        hosts.assert_called_once_with(refresh=True)
        drift.assert_called_once()
        self.assertEqual({"drift": "ok", "update_badge": "al día"}, ctx)

    def test_configurar_runs_the_guided_wizard_and_installs_what_it_returns(self):
        """The install path still ends in `install.sh --harness <value>`, verbatim -- the
        guided wizard replaced the two nested pickers that used to lead there, not the
        command they produced."""
        def fake_run(ops, style=None):
            ops["set_postura"]("autonoma")
            ops["set_metodologia"]("sdd")
            ops["install"]("opencode")
            return True

        with mock.patch.object(app.onboarding, "run", side_effect=fake_run), \
             mock.patch.object(app, "set_postura"), mock.patch.object(app, "set_metodologia"):
            rc, _, tty = self._menu([self._pick("configurar"), None])
        self.assertEqual(rc, 0)
        command = tty.call_args.args[0]
        self.assertTrue(command[0].endswith("install.sh"))
        self.assertEqual(command[1:], ["--harness", "opencode"])

    def test_cancelling_the_guided_wizard_runs_nothing(self):
        with mock.patch.object(app.onboarding, "run", return_value=False):
            rc, _, tty = self._menu([self._pick("configurar"), None])
        self.assertEqual(rc, 0)
        tty.assert_not_called()

    def test_salir_is_last_and_ends_the_session_in_both_modes(self):
        for experto in (False, True):
            rows = app.visible_actions(experto=experto)
            self.assertEqual(rows[-1].key, "salir")
            rc, _, _ = self._menu([self._pick("salir", experto=experto)], experto=experto)
            self.assertEqual(rc, 0)

    def test_engineering_surfaces_are_hidden_until_expert_mode_is_on(self):
        simple = {action.key for action in app.visible_actions(experto=False)}
        expert = {action.key for action in app.visible_actions(experto=True)}
        for key in ("vault", "mcps", "plugins", "herramientas", "proponer", "hosts"):
            self.assertNotIn(key, simple, f"{key} no debería estar en el modo simple")
            self.assertIn(key, expert, f"{key} debería estar en el modo experto")
        self.assertEqual(simple, expert - {"vault", "mcps", "plugins", "herramientas",
                                           "proponer", "hosts"})

    def test_modo_toggles_expert_mode_and_nothing_else(self):
        with mock.patch.object(app, "write_app_config") as writer:
            rc, _, _ = self._menu([self._pick("modo"), None])
        self.assertEqual(rc, 0)
        writer.assert_called_once_with(experto=True)

    def test_every_visible_label_is_one_cell_per_character_and_free_of_emoji(self):
        """ADR-0050's real rule (ADR-0075 restates it): a label carries text, never a
        decorative glyph, so nothing in it can have a font-dependent width. This admits
        accented Spanish -- which `isascii()` used to reject -- and still refuses U+23FB,
        the symbol that motivated the original pin."""
        import ui
        labels = [action.label for action in app.visible_actions(experto=True)]
        labels += [label for label, _ in app.HARNESS_CHOICES]
        labels += [target.label for target in app.onboarding.TARGETS]
        labels += [preset.label for preset in app.onboarding.PRESETS]
        labels += list(app.HOST_LABELS.values())
        for label in labels:
            self.assertTrue(ui.is_safe_label(label), f"etiqueta con glifo prohibido: {label!r}")
            self.assertEqual(ui.cell_width(label), len(label), f"ancho variable en: {label!r}")
            self.assertEqual(label, label.strip(), f"espacio al borde en: {label!r}")
            self.assertNotIn("  ", label, f"doble espacio en: {label!r}")


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


class InteractiveInstallerProgressTests(unittest.TestCase):
    """D2-DR01: a child that might prompt owns the terminal until it exits."""

    def test_run_tty_never_redraws_after_an_installer_prompt(self):
        stderr = _FakeStream(is_tty=True)

        def child(*_args, **_kwargs):
            stderr.write("CONFIRMAR? [s/N] ")
            time.sleep(0.35)
            stderr.write("CHILD_DONE")
            return mock.Mock(returncode=0)

        with mock.patch.object(app.subprocess, "run", side_effect=child), \
             mock.patch("sys.stderr", stderr), \
             mock.patch.dict(os.environ, {"NO_COLOR": "", "TERM": "xterm"}, clear=False):
            rc = app.run_tty(["fake-installer"])
        between = stderr.getvalue().split("CONFIRMAR? [s/N] ", 1)[1].split("CHILD_DONE", 1)[0]
        self.assertEqual(rc, 0)
        self.assertNotIn("\r", between)
        self.assertTrue(stderr.getvalue().endswith("ejecutando instalador: listo\n"))

    def test_post_update_without_yes_never_redraws_after_an_installer_prompt(self):
        stdout, stderr = io.StringIO(), _FakeStream(is_tty=True)
        commands = []

        def child(command, **_kwargs):
            commands.append(command)
            stderr.write("ACTUALIZAR? [s/N] ")
            time.sleep(0.35)
            stderr.write("CHILD_DONE")
            return mock.Mock(returncode=0)

        pull = mock.Mock(returncode=0, stdout="", stderr="")
        with mock.patch.object(app, "tree_clean", return_value=True), \
             mock.patch.object(app, "upstream_ref", return_value="origin/main"), \
             mock.patch.object(app, "rev_count", side_effect=[1, 0]), \
             mock.patch.object(app, "short_sha", side_effect=["old", "new"]), \
             mock.patch.object(app, "git", return_value=pull), \
             mock.patch.object(app, "_upstream_remote_and_branch", return_value=("origin", "main")), \
             mock.patch.object(app, "_install_scope", return_value=None), \
             mock.patch.object(app.subprocess, "run", side_effect=child), \
             mock.patch("sys.stdout", stdout), mock.patch("sys.stderr", stderr), \
             mock.patch.dict(os.environ, {"NO_COLOR": "", "TERM": "xterm"}, clear=False):
            rc = app.cmd_update(yes=False, assume_fetched=True)
        between = stderr.getvalue().split("ACTUALIZAR? [s/N] ", 1)[1].split("CHILD_DONE", 1)[0]
        self.assertEqual(rc, 0)
        self.assertNotIn("--yes", commands[0])
        self.assertNotIn("\r", between)
        self.assertTrue(stderr.getvalue().endswith("instalando actualización: listo\n"))


class RouteDoctorProgressTests(unittest.TestCase):
    """025/D2 (AC-04/AC-05): the progress indicator wrapping `--route-doctor`'s ~20s provider
    probe (`route_doctor`, `catalog.py:1136`) never touches stdout -- the JSON envelope's
    contract (D1, AC-03) -- and never leaves the operation silent, live or degraded."""

    def _run(self, *, human, stderr_stream, env):
        fake_report = {"cache": {"used": False, "reason": "CACHE_ROOT_ABSENT"}, "providers": []}
        stdout_buf = io.StringIO()
        with mock.patch("routing_core.catalog.prune_legacy_probe_cache", return_value=False), \
             mock.patch("routing_core.catalog.route_doctor", side_effect=lambda *_a, **_k: (time.sleep(0.35), fake_report)[1]), \
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


class InteractiveNavigationTests(unittest.TestCase):
    """Tests for Vim keys (hjkl/q), direct numeric keys (1-9), left/right arrows, and `ui`."""

    def test_vim_keys_navigate_and_select(self):
        import tui
        state = tui.PickerState(items=("Opcion A", "Opcion B", "Opcion C"))
        self.assertEqual(state.cursor, 0)
        # 'j' moves down
        s2 = tui.reduce(state, tui.KeyEvent("CHAR", "j"))
        self.assertEqual(s2.cursor, 1)
        # 'k' moves up
        s3 = tui.reduce(s2, tui.KeyEvent("CHAR", "k"))
        self.assertEqual(s3.cursor, 0)
        # 'l' selects
        s4 = tui.reduce(s2, tui.KeyEvent("CHAR", "l"))
        self.assertEqual(s4.result, tui.Selected(1))
        # 'h' cancels
        s5 = tui.reduce(s2, tui.KeyEvent("CHAR", "h"))
        self.assertIsNone(s5.result)
        # 'q' cancels
        s6 = tui.reduce(s2, tui.KeyEvent("CHAR", "q"))
        self.assertIsNone(s6.result)

    def test_numeric_keys_direct_selection(self):
        import tui
        state = tui.PickerState(items=("Opcion 1", "Opcion 2", "Opcion 3", "Opcion 4"))
        # Press '3' selects index 2
        s = tui.reduce(state, tui.KeyEvent("CHAR", "3"))
        self.assertEqual(s.result, tui.Selected(2))
        # Press '1' selects index 0
        s1 = tui.reduce(state, tui.KeyEvent("CHAR", "1"))
        self.assertEqual(s1.result, tui.Selected(0))

    def test_left_right_keys(self):
        import tui
        state = tui.PickerState(items=("Alpha", "Beta"))
        # RIGHT selects current
        s_right = tui.reduce(state, tui.KeyEvent("RIGHT"))
        self.assertEqual(s_right.result, tui.Selected(0))
        # LEFT cancels
        s_left = tui.reduce(state, tui.KeyEvent("LEFT"))
        self.assertIsNone(s_left.result)

    def test_decode_keys_left_right(self):
        import tui
        events, rem = tui.decode_keys(b"\x1b[C\x1b[D")
        self.assertEqual(rem, b"")
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].kind, "RIGHT")
        self.assertEqual(events[1].kind, "LEFT")

    def test_ui_rule_and_cache(self):
        import ui
        line = ui.rule("Test Title", width=60)
        self.assertIn("Test Title", line)
        self.assertIn("─", line)

        # SessionCache
        cache = ui.SessionCache(ttl_seconds=10.0)
        compute_count = 0

        def compute():
            nonlocal compute_count
            compute_count += 1
            return "computed_val"

        v1 = cache.get_or_compute("key", compute)
        v2 = cache.get_or_compute("key", compute)
        self.assertEqual(v1, "computed_val")
        self.assertEqual(v2, "computed_val")
        self.assertEqual(compute_count, 1)  # cached, not recomputed

        cache.invalidate("key")
        v3 = cache.get_or_compute("key", compute)
        self.assertEqual(compute_count, 2)  # recomputed after invalidation
