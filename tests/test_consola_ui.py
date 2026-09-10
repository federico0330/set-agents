"""Regression tests for the rebuilt console: the visual system (`ui.py`), the multi-selection
mode added to the picker (`tui.py`), and the guided first run (`onboarding.py`).

Each test here names the defect it exists to catch, because three of them are defects the
previous UI shipped with and no test noticed.
"""

import io
import os
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import onboarding  # noqa: E402
import tui  # noqa: E402
import ui  # noqa: E402


class _FakeTTY(io.StringIO):
    def isatty(self):
        return True


class CellWidthTests(unittest.TestCase):
    """`tui_views.visual_len` was `len(strip_ansi(...))`, so every panel padded with it came
    out crooked the moment a wide glyph appeared -- which is exactly what happened once emoji
    reached the more/preferencias headers."""

    def test_wide_glyphs_count_two_cells(self):
        self.assertEqual(ui.cell_width("🧰"), 2)
        self.assertEqual(ui.cell_width("漢字"), 4)

    def test_combining_marks_count_zero(self):
        # "e" + COMBINING ACUTE renders as one cell, not two.
        self.assertEqual(ui.cell_width("é"), 1)

    def test_latin_text_with_accents_counts_one_cell_per_character(self):
        for text in ("Cómo está", "Más", "autonomía", "¿Qué CLI?"):
            self.assertEqual(ui.cell_width(text), len(text), text)

    def test_ansi_sequences_are_not_measured(self):
        self.assertEqual(ui.cell_width("\033[1;36mhola\033[0m"), 4)

    def test_pad_and_clip_use_cells_not_codepoints(self):
        self.assertEqual(ui.cell_width(ui.pad("🧰", 6)), 6)
        self.assertEqual(ui.cell_width(ui.pad("Cómo", 6)), 6)
        clipped = ui.clip("abcdefghij", 5)
        self.assertEqual(ui.cell_width(clipped), 5)
        self.assertTrue(clipped.endswith("…"))


class LabelRuleTests(unittest.TestCase):
    def test_accented_spanish_is_allowed_and_symbols_are_not(self):
        self.assertTrue(ui.is_safe_label("Cómo está"))
        self.assertTrue(ui.is_safe_label("Proponer herramienta"))
        self.assertFalse(ui.is_safe_label("⏻ Salir"))
        self.assertFalse(ui.is_safe_label("🧰 Herramientas"))
        self.assertFalse(ui.is_safe_label("⚙️ Ajustes"))

    def test_every_glyph_the_renderer_uses_is_exactly_one_cell(self):
        """A two-cell glyph in the cursor or the state dot re-creates the alignment defect
        ADR-0050 was written about, one layer down."""
        glyphs = (ui.CURSOR, ui.DOT_ON, ui.DOT_OFF, ui.DOT_WARN,
                  ui.CHECK, ui.CROSS, ui.BAR_FULL, ui.BAR_EMPTY, *ui.SPINNER)
        for glyph in glyphs:
            self.assertEqual(ui.cell_width(glyph), 1, repr(glyph))


class PaletteTests(unittest.TestCase):
    """`tui_views` decided its palette at import time (`if use_color():` at module level), so
    a process that imported it without a TTY had empty colour codes forever after."""

    def test_colour_capability_is_recomputed_on_every_call(self):
        with mock.patch.dict(os.environ, {"NO_COLOR": "1"}, clear=False):
            self.assertEqual(ui.caps(_FakeTTY()), "none")
            self.assertEqual(ui.paint("hola", "ok", stream=_FakeTTY()), "hola")
        env = {k: v for k, v in os.environ.items() if k != "NO_COLOR"}
        env.update({"COLORTERM": "truecolor", "TERM": "xterm-256color"})
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(ui.caps(_FakeTTY()), "truecolor")
            self.assertIn("\033[38;2;", ui.paint("hola", "ok", stream=_FakeTTY()))

    def test_capability_ladder_degrades_by_terminal(self):
        base = {k: v for k, v in os.environ.items() if k not in ("NO_COLOR", "COLORTERM")}
        with mock.patch.dict(os.environ, {**base, "TERM": "xterm-256color"}, clear=True):
            self.assertEqual(ui.caps(_FakeTTY()), "256")
            self.assertIn("\033[38;5;", ui.paint("x", "ok", stream=_FakeTTY()))
        with mock.patch.dict(os.environ, {**base, "TERM": "xterm"}, clear=True):
            self.assertEqual(ui.caps(_FakeTTY()), "16")
        with mock.patch.dict(os.environ, {**base, "TERM": "dumb"}, clear=True):
            self.assertEqual(ui.caps(_FakeTTY()), "none")

    def test_a_non_tty_stream_never_receives_ansi(self):
        plain = io.StringIO()  # isatty() is False
        for painter in (ui.title, ui.heading, ui.muted, ui.ok, ui.warn, ui.err, ui.body):
            self.assertEqual(painter("hola", stream=plain), "hola")
        self.assertEqual(ui.wordmark("x"), ["SET-AGENTS — x"])

    def test_every_role_resolves_at_every_colour_depth(self):
        for role in ui._ROLES:
            for level in ("truecolor", "256", "16"):
                self.assertTrue(ui._sgr(role, level).startswith("\033["))


class MultiSelectTests(unittest.TestCase):
    """`multi=True` is additive: with it off, the reducer must behave exactly as it did."""

    def test_space_toggles_and_enter_returns_the_marked_rows(self):
        state = tui.PickerState(items=("a", "b", "c"), multi=True)
        for key in (tui.KeyEvent("CHAR", " "), tui.KeyEvent("DOWN"), tui.KeyEvent("DOWN"),
                    tui.KeyEvent("CHAR", " "), tui.KeyEvent("ENTER")):
            state = tui.reduce(state, key)
        self.assertEqual(state.result, tui.Marked((0, 2)))

    def test_space_toggles_off_again(self):
        state = tui.PickerState(items=("a", "b"), multi=True)
        for key in (tui.KeyEvent("CHAR", " "), tui.KeyEvent("CHAR", " "), tui.KeyEvent("ENTER")):
            state = tui.reduce(state, key)
        self.assertEqual(state.result, tui.Marked(()))

    def test_a_section_header_can_never_be_marked(self):
        state = tui.PickerState(items=("grupo", "a"), headers=frozenset({0}), multi=True)
        state = tui.reduce(state, tui.KeyEvent("CHAR", " "))
        self.assertEqual(state.marked, frozenset())

    def test_escape_cancels_without_returning_marks(self):
        state = tui.PickerState(items=("a", "b"), multi=True)
        state = tui.reduce(state, tui.KeyEvent("CHAR", " "))
        state = tui.reduce(state, tui.KeyEvent("ESCAPE"))
        self.assertIsNone(state.result)

    def test_single_selection_is_untouched_by_the_new_field(self):
        state = tui.PickerState(items=("a", "b", "c"))
        self.assertEqual(tui.reduce(state, tui.KeyEvent("ENTER")).result, tui.Selected(0))
        self.assertEqual(tui.reduce(state, tui.KeyEvent("CHAR", "3")).result, tui.Selected(2))
        # A space in single mode still opens typeahead, exactly as before.
        self.assertEqual(tui.reduce(state, tui.KeyEvent("CHAR", " ")).mode, "search")


class ProbeDisciplineTests(unittest.TestCase):
    """`probe_host_model_counts` shells out once per CLI, each with its own timeout. It used
    to be reachable from `_home_header`, so the menu could re-probe on a repaint; and the
    wizard called it from inside the alternate screen, where the progress line is invisible
    and the user faces a blank terminal."""

    SOURCE = (ROOT / "ai/scripts/set_agents_app.py").read_text(encoding="utf-8")

    def test_exactly_one_function_reaches_the_probe(self):
        callers = [line for line in self.SOURCE.splitlines()
                   if "host_adapters.probe_host_model_counts" in line
                   and not line.strip().startswith("#")]
        self.assertEqual(len(callers), 1, callers)
        # ...and that one call sits inside `measure_hosts`, the caching entry point.
        before = self.SOURCE.split(callers[0])[0]
        enclosing = [line for line in before.splitlines() if line.startswith("def ")][-1]
        self.assertTrue(enclosing.startswith("def measure_hosts("), enclosing)

    def test_the_visible_measurement_leaves_the_alternate_screen(self):
        body = self.SOURCE.split("def measure_hosts_visibly(")[1].split("\ndef ")[0]
        self.assertIn("tui.suspend_terminal()", body)
        self.assertIn("tui.with_progress", body)

    def test_the_probe_measures_every_present_host_concurrently(self):
        import concurrent.futures
        import host_adapters
        adapters = [
            host_adapters.HostAdapter(
                host_id=f"h{i}", detect=lambda: True,
                probe_models=lambda i=i: {f"m{i}"} , materialize=lambda m, e=None: ["x"],
                install_harness=lambda: None)
            for i in range(3)
        ]
        registry = {adapter.host_id: adapter for adapter in adapters}
        with mock.patch.object(host_adapters, "_REGISTRY", registry), \
             mock.patch.object(concurrent.futures, "ThreadPoolExecutor",
                               wraps=concurrent.futures.ThreadPoolExecutor) as pool:
            counts = host_adapters.probe_host_model_counts()
        self.assertEqual(counts, {"h0": 1, "h1": 1, "h2": 1})
        pool.assert_called_once()

    def test_a_failing_probe_counts_as_zero_never_as_a_crash(self):
        import host_adapters
        boom = host_adapters.HostAdapter(
            host_id="boom", detect=lambda: True,
            probe_models=mock.Mock(side_effect=OSError("sin binario")),
            materialize=lambda m, e=None: ["x"], install_harness=lambda: None)
        good = host_adapters.HostAdapter(
            host_id="good", detect=lambda: True, probe_models=lambda: {"a", "b"},
            materialize=lambda m, e=None: ["x"], install_harness=lambda: None)
        with mock.patch.object(host_adapters, "_REGISTRY", {"boom": boom, "good": good}):
            self.assertEqual(host_adapters.probe_host_model_counts(), {"boom": 0, "good": 2})

    def test_an_absent_host_gets_no_entry_at_all(self):
        import host_adapters
        absent = host_adapters.HostAdapter(
            host_id="absent", detect=lambda: False, probe_models=lambda: {"a"},
            materialize=lambda m, e=None: ["x"], install_harness=lambda: None)
        with mock.patch.object(host_adapters, "_REGISTRY", {"absent": absent}):
            self.assertEqual(host_adapters.probe_host_model_counts(), {})


class HostCountsCacheTests(unittest.TestCase):
    """A CLI that is installed but not logged in burns its whole timeout before answering
    "nothing", so on a machine with agy and copilot present the console spent ~30 s measuring
    on EVERY launch. The counts change when you log in or install something, not minute to
    minute, so they get a disk cache with a TTL -- the same shape the models wizard already
    uses for its own probes."""

    def setUp(self):
        import tempfile
        import set_agents_app as app
        self.app = app
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "host-counts.json"
        self.addCleanup(self.tmp.cleanup)
        app.ui.GLOBAL_CACHE.invalidate()
        self.addCleanup(app.ui.GLOBAL_CACHE.invalidate)

    def test_a_fresh_cache_spares_the_probe_entirely(self):
        self.app._write_host_counts_cache({"agy": 3}, path=self.path)
        with mock.patch.object(self.app, "HOST_COUNTS_CACHE", self.path), \
             mock.patch.object(self.app.host_adapters, "probe_host_model_counts") as probe:
            self.assertEqual(self.app.measure_hosts(), {"agy": 3})
        probe.assert_not_called()

    def test_force_re_probes_even_with_a_fresh_cache(self):
        self.app._write_host_counts_cache({"agy": 3}, path=self.path)
        with mock.patch.object(self.app, "HOST_COUNTS_CACHE", self.path), \
             mock.patch.object(self.app.host_adapters, "probe_host_model_counts",
                               return_value={"agy": 9}) as probe:
            self.assertEqual(self.app.measure_hosts(force=True), {"agy": 9})
        probe.assert_called_once()
        self.assertEqual(self.app._load_host_counts_cache(path=self.path), {"agy": 9})

    def test_an_expired_cache_is_ignored(self):
        old = time.time() - self.app.HOST_COUNTS_TTL_SECONDS - 1
        self.app._write_host_counts_cache({"agy": 3}, now=old, path=self.path)
        self.assertIsNone(self.app._load_host_counts_cache(path=self.path))

    def test_a_cache_stamped_in_the_future_is_ignored(self):
        self.app._write_host_counts_cache({"agy": 3}, now=time.time() + 600, path=self.path)
        self.assertIsNone(self.app._load_host_counts_cache(path=self.path))

    def test_a_tampered_cache_never_injects_a_host_or_a_bogus_count(self):
        for payload in ('{"at": %f, "counts": {"noexiste": 1}}' % time.time(),
                        '{"at": %f, "counts": {"agy": -1}}' % time.time(),
                        '{"at": %f, "counts": {"agy": "muchos"}}' % time.time(),
                        '{"at": %f, "counts": {"agy": true}}' % time.time(),
                        '{"at": "ayer", "counts": {}}',
                        'no soy json'):
            self.path.write_text(payload, encoding="utf-8")
            self.assertIsNone(self.app._load_host_counts_cache(path=self.path), payload)

    def test_a_missing_cache_is_not_an_error(self):
        self.assertIsNone(self.app._load_host_counts_cache(path=Path("/no/existe.json")))

    def test_an_unwritable_cache_gives_a_slow_console_never_a_broken_one(self):
        counts = self.app._write_host_counts_cache({"agy": 1}, path=Path("/no/existe/x.json"))
        self.assertEqual(counts, {"agy": 1})

    def test_the_cache_file_is_private(self):
        self.app._write_host_counts_cache({"agy": 1}, path=self.path)
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o600)


class HostPinTests(unittest.TestCase):
    """045 AC-B.*: a machine's taste never dirties the tracked models.toml."""

    def setUp(self):
        import tempfile
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "models.local.toml"
        self.addCleanup(self.tmp.cleanup)

    def test_absent_overlay_reads_as_no_pin(self):
        import models_config
        self.assertEqual(models_config.host_pin("agy", self.path), {})

    def test_a_pin_round_trips_and_can_be_cleared(self):
        import models_config
        models_config.write_host_pin("agy", "model", "composer-2.5", self.path)
        models_config.write_host_pin("agy", "effort", "high", self.path)
        self.assertEqual(models_config.host_pin("agy", self.path),
                         {"model": "composer-2.5", "effort": "high"})
        models_config.write_host_pin("agy", "effort", None, self.path)
        self.assertEqual(models_config.host_pin("agy", self.path), {"model": "composer-2.5"})

    def test_an_effort_outside_the_closed_set_is_refused_at_the_writer(self):
        import models_config
        with self.assertRaises(models_config.ModelsError):
            models_config.write_host_pin("agy", "effort", "ludicrous", self.path)
        self.assertEqual(models_config.host_pin("agy", self.path), {})

    def test_a_malformed_overlay_degrades_to_no_pin_instead_of_raising(self):
        import models_config
        self.path.write_text("esto no es toml [[[", encoding="utf-8")
        self.assertEqual(models_config.host_pin("agy", self.path), {})

    def test_host_pins_never_leak_into_the_area_matrix(self):
        import models_config
        models_config.write_host_pin("agy", "model", "composer-2.5", self.path)
        overlay = models_config.load_models_overlay(self.path)
        merged = models_config.effective_models_config({"areas": {}, "roles": {}}, overlay)
        self.assertEqual(merged.get("areas"), {})
        self.assertEqual(merged.get("roles"), {})


class OnboardingScreenTests(unittest.TestCase):
    """The five steps are pure functions on data, so their copy is testable with no terminal."""

    ROWS = [("agy", "ausente"), ("claude", "vivo"), ("codex", "unlistable"),
            ("opencode", "ausente"), ("pi", "vivo")]

    def test_detection_lists_every_candidate_including_the_absent_ones(self):
        text = "\n".join(onboarding.detection_lines(self.ROWS, {"claude": 12}))
        for host_id, _ in self.ROWS:
            self.assertIn(ui.HOST_TITLES[host_id], text)
        self.assertIn("no está", text)

    def test_detection_never_invents_a_model_count(self):
        """045 AC-A.2: a number reaches the screen only when a probe returned it."""
        text = "\n".join(onboarding.detection_lines(self.ROWS, {}))
        self.assertNotIn("modelos", text)
        with_count = "\n".join(onboarding.detection_lines(self.ROWS, {"claude": 12}))
        self.assertIn("12 modelos", with_count)

    def test_install_options_flag_what_is_not_installed_yet(self):
        options = dict((target.host_id, note) for target, note in onboarding.install_options(self.ROWS))
        self.assertEqual(options["claude"], "")
        self.assertTrue(options["opencode"])

    def test_review_names_every_action_before_anything_runs(self):
        chosen = (onboarding.TARGETS[0],)
        text = "\n".join(onboarding.review_lines(chosen, onboarding.PRESETS[0]))
        self.assertIn("Claude Code", text)
        self.assertIn("Nada se toca", text)

    def test_summary_reports_a_failed_install_instead_of_claiming_success(self):
        text = "\n".join(onboarding.summary_lines(
            [("Claude Code", True), ("Codex", False)], onboarding.PRESETS[0]))
        self.assertIn(ui.CHECK, text)
        self.assertIn(ui.CROSS, text)
        self.assertIn("falló", text)

    def test_every_target_is_a_harness_install_sh_actually_accepts(self):
        """`install.sh` validates --harness against a closed set and exits 2 on anything else.
        A target added here that is not in that set would fail at install time, after the user
        already confirmed the review."""
        import re
        script = (ROOT / "install.sh").read_text(encoding="utf-8")
        accepted = set(re.search(r"^\s*(\S+(?:\|\S+)*)\) HARNESS=", script, re.M).group(1).split("|"))
        for target in onboarding.TARGETS:
            self.assertIn(target.harness, accepted, target)

    def test_presets_only_reference_real_posturas_and_metodologias(self):
        import set_agents_app as app
        for preset in onboarding.PRESETS:
            self.assertIn(preset.postura, app.POSTURA_KEYS)
            self.assertIn(preset.metodologia, ("sdd", "rdd", "off"))


class OnboardingRunTests(unittest.TestCase):
    def _ops(self):
        calls = {"install": [], "postura": [], "metodologia": []}
        ops = {
            "host_rows": lambda: ([("claude", "vivo"), ("codex", "ausente"),
                                   ("opencode", "ausente"), ("pi", "ausente")], {"claude": 3}),
            "install": lambda harness: (calls["install"].append(harness), 0)[1],
            "set_postura": calls["postura"].append,
            "set_metodologia": calls["metodologia"].append,
            "postura_actual": lambda: "autonoma",
            "metodologia_preferida": lambda: "sdd",
        }
        return ops, calls

    def test_cancelling_before_the_review_writes_nothing(self):
        for stop_after in range(4):
            ops, calls = self._ops()
            picks = [tui.Selected(0), tui.Marked((0,)), tui.Selected(0), tui.Selected(0)]
            picks[stop_after] = None
            with mock.patch.object(tui, "run_picker", side_effect=picks[:stop_after + 1]):
                applied = onboarding.run(ops)
            self.assertFalse(applied, f"paso {stop_after + 1}")
            self.assertEqual(calls["install"], [])
            self.assertEqual(calls["postura"], [])

    def test_choosing_cancel_on_the_review_writes_nothing(self):
        ops, calls = self._ops()
        picks = [tui.Selected(0), tui.Marked((0,)), tui.Selected(0), tui.Selected(1)]
        with mock.patch.object(tui, "run_picker", side_effect=picks):
            self.assertFalse(onboarding.run(ops))
        self.assertEqual(calls["install"], [])
        self.assertEqual(calls["postura"], [])

    def test_applying_installs_exactly_the_marked_targets_and_stores_the_preset(self):
        ops, calls = self._ops()
        picks = [tui.Selected(0), tui.Marked((0, 2)), tui.Selected(1), tui.Selected(0), None]
        with mock.patch.object(tui, "run_picker", side_effect=picks), \
             mock.patch("sys.stdout", io.StringIO()):
            self.assertTrue(onboarding.run(ops))
        self.assertEqual(calls["install"], ["claude", "opencode"])
        self.assertEqual(calls["postura"], [onboarding.PRESETS[1].postura])
        self.assertEqual(calls["metodologia"], [onboarding.PRESETS[1].metodologia])

    def test_a_failed_probe_still_reaches_the_first_screen(self):
        ops, _ = self._ops()
        ops["host_rows"] = mock.Mock(side_effect=OSError("sin PATH"))
        with mock.patch.object(tui, "run_picker", return_value=None) as picker:
            self.assertFalse(onboarding.run(ops))
        self.assertIn("Paso 1 de 5", picker.call_args.kwargs["header"])


class StaleSandboxSweepTests(unittest.TestCase):
    """A killed run leaves its sandbox behind (`TemporaryDirectory` cleans up through a
    finalizer, and no finalizer runs on SIGKILL). Measured 2026-08-31: 35 orphans from up to
    17 days earlier, 5.9 GB, on a disk at 99%. Each run now sweeps its dead predecessors."""

    def setUp(self):
        import tempfile as _tempfile
        import tests as _tests
        self.sweep = _tests._sweep_stale_sandboxes
        self.prefix = _tests._SANDBOX_PREFIX
        self.tmp = _tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.addCleanup(self.tmp.cleanup)
        self.now = time.time()

    def _make(self, name, age_days, *, directory=True):
        target = self.root / name
        if directory:
            target.mkdir()
            (target / "peso").write_text("x" * 64, encoding="utf-8")
        else:
            target.write_text("", encoding="utf-8")
        stamp = self.now - age_days * 24 * 3600
        os.utime(target, (stamp, stamp))
        return target

    def test_an_old_orphan_is_removed(self):
        old = self._make(self.prefix + "viejo", 3)
        removed = self.sweep(self.root, now=self.now)
        self.assertEqual(removed, [old])
        self.assertFalse(old.exists())

    def test_a_recent_sandbox_survives(self):
        """The concurrency guarantee: a run happening RIGHT NOW must never be swept."""
        fresh = self._make(self.prefix + "de-otra-corrida", 0)
        self.assertEqual(self.sweep(self.root, now=self.now), [])
        self.assertTrue(fresh.exists())

    def test_the_live_sandbox_is_never_swept_even_when_old(self):
        mine = self._make(self.prefix + "el-mio", 10)
        self.assertEqual(self.sweep(self.root, now=self.now, keep=mine), [])
        self.assertTrue(mine.exists())

    def test_nothing_outside_the_prefix_is_touched(self):
        victims = [self._make(name, 30) for name in
                   ("Documentos", "set-agentes-verify.abc123", ".config", "importante")]
        self._make(self.prefix + "viejo", 30)
        self.sweep(self.root, now=self.now)
        for victim in victims:
            self.assertTrue(victim.exists(), victim.name)

    def test_a_symlink_is_never_handed_to_rmtree(self):
        """A symlink named like a sandbox must not even be ATTEMPTED.

        The first version of this test only asserted that the link's target survived -- and it
        passed with the symlink guard deleted, because `shutil.rmtree` refuses a symlink on its
        own. A test that cannot fail is worse than no test, so this pins the guard itself: the
        sweep never hands a symlink to `rmtree`. Bitten red with the guard removed."""
        target = self.root / "datos-reales"
        target.mkdir()
        (target / "importante.txt").write_text("no me borres", encoding="utf-8")
        link = self.root / (self.prefix + "trampa")
        link.symlink_to(target)
        stamp = self.now - 30 * 24 * 3600
        for path in (link, target):
            os.utime(path, (stamp, stamp), follow_symlinks=False)

        with mock.patch("tests.shutil.rmtree") as rmtree:
            self.sweep(self.root, now=self.now)
        for call in rmtree.call_args_list:
            self.assertFalse(Path(call.args[0]).is_symlink(), call.args[0])
        self.assertTrue(target.exists())
        self.assertTrue((target / "importante.txt").exists())

    def test_a_missing_parent_is_not_an_error(self):
        self.assertEqual(self.sweep(self.root / "no-existe", now=self.now), [])

    def test_an_unremovable_entry_is_skipped_without_raising(self):
        """Tidying up must never be what breaks a run."""
        old = self._make(self.prefix + "viejo", 5)
        with mock.patch("tests.shutil.rmtree", side_effect=OSError("montado")):
            self.assertEqual(self.sweep(self.root, now=self.now), [])
        self.assertTrue(old.exists())

    def test_verify_sh_sweeps_its_own_stagings_with_a_bounded_pattern(self):
        script = (ROOT / "ai/scripts/verify.sh").read_text(encoding="utf-8")
        sweep = [line for line in script.splitlines() if "set-agentes-verify" in line and "find" in line]
        self.assertEqual(len(sweep), 1, sweep)
        line = sweep[0]
        self.assertIn("-maxdepth 1", line)   # nunca recursivo
        self.assertIn("-type d", line)       # nunca un archivo suelto
        self.assertIn("-mtime +0", line)     # nunca el staging de una corrida viva


if __name__ == "__main__":
    unittest.main()
