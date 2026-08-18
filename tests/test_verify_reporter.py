"""PKG-5 presenter for verify.sh: live progress, immediate failures, summary, same set."""

from __future__ import annotations

import io
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

import verify_reporter


class FakeClock:
    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def _load_tests(clock, specs):
    """Build a TestCase class inside this function so discover does not collect it."""

    class LoadTests(unittest.TestCase):
        pass

    for index, (kind, duration, extra) in enumerate(specs):
        def body(self, kind=kind, duration=duration, extra=extra):
            clock.advance(duration)
            if kind == "fail":
                self.fail(extra or "synthetic-fail")
            elif kind == "skip":
                self.skipTest(extra or "synthetic-skip")
            elif kind == "error":
                raise RuntimeError(extra or "synthetic-error")

        setattr(LoadTests, f"test_{index:02d}_{kind}", body)
    return unittest.TestLoader().loadTestsFromTestCase(LoadTests)


def _run(specs, *, verbose=False, clock=None):
    clock = FakeClock() if clock is None else clock
    stream = io.StringIO()
    suite = _load_tests(clock, specs)
    result = verify_reporter.run_suite(suite, stream=stream, clock=clock, verbose=verbose)
    return result, stream.getvalue(), clock


class VerifyReporterTests(unittest.TestCase):
    def test_progress_line_rewrites_and_eta_uses_measured_pace(self):
        # Three tests, 2s each on the injected clock. After the first, remaining=2
        # and measured pace is 2s/test → ETA 4s, not a 1s-per-test constant (that
        # would print ETA 2s).
        result, output, _ = _run([("ok", 2.0, None)] * 3)
        self.assertTrue(result.wasSuccessful())
        self.assertIn("\r", output)
        self.assertIn("1/3 · 2s · ETA 4s · ✗0", output)
        self.assertIn("2/3 · 4s · ETA 2s · ✗0", output)
        self.assertIn("3/3 · 6s · ETA 0s · ✗0", output)
        elapsed, done, total, remaining = 2.0, 1, 3, 2
        measured = elapsed * remaining / done
        self.assertEqual(measured, 4.0)

    def test_failure_block_prints_immediately_not_only_at_end(self):
        _, output, _ = _run([
            ("ok", 1.0, None),
            ("fail", 1.0, "boom-now"),
            ("ok", 1.0, None),
        ])
        fail_at = output.index("FAIL: ")
        self.assertIn("boom-now", output)
        self.assertLess(fail_at, output.index("2/3 ·"))
        self.assertLess(fail_at, output.index("3/3 ·"))
        self.assertLess(fail_at, output.index("verify summary"))
        self.assertIn(verify_reporter.SEPARATOR1, output[fail_at - 80:fail_at])

    def test_final_summary_groups_skips_and_lists_ten_slowest(self):
        specs = [("ok", 0.1 * (n + 1), None) for n in range(12)]
        specs[3] = ("fail", 0.4, "summary-boom")
        specs[5] = ("skip", 0.05, "windows-only")
        specs[6] = ("skip", 0.05, "windows-only")
        specs[8] = ("skip", 0.05, "missing-tool")
        result, output, _ = _run(specs)
        self.assertFalse(result.wasSuccessful())
        self.assertIn("verify summary", output)
        self.assertIn("ran 12 tests", output)
        self.assertIn("fail=1", output)
        self.assertIn("skip=3", output)
        fail_ids = [tid for tid, _ in result.durations if "test_03_fail" in tid]
        self.assertEqual(len(fail_ids), 1)
        self.assertIn(f"FAIL {fail_ids[0]}", output)
        self.assertIn("windows-only (2):", output)
        self.assertIn("missing-tool (1):", output)
        slowest_block = output.split("slowest:\n", 1)[1].split(verify_reporter.SUMMARY_BAR, 1)[0]
        slow_lines = [line for line in slowest_block.splitlines() if line.startswith("  ")]
        self.assertEqual(len(slow_lines), 10)
        times = [float(line.split()[0].removesuffix("s")) for line in slow_lines]
        self.assertEqual(times, sorted(times, reverse=True))
        self.assertGreaterEqual(times[0], 1.2 - 1e-9)

    def test_verbose_follows_set_agents_verify_verbose(self):
        specs = [("ok", 0.2, None), ("fail", 0.2, "verbose-boom")]
        _, quiet, _ = _run(specs, verbose=False)
        _, noisy, _ = _run(specs, verbose=True)
        self.assertFalse(verify_reporter.verbose_enabled({}))
        self.assertFalse(verify_reporter.verbose_enabled({"SET_AGENTS_VERIFY_VERBOSE": "0"}))
        self.assertTrue(verify_reporter.verbose_enabled({"SET_AGENTS_VERIFY_VERBOSE": "1"}))
        self.assertEqual(verify_reporter.VERBOSE_ENV, "SET_AGENTS_VERIFY_VERBOSE")
        self.assertNotIn(" ... ok", quiet)
        self.assertIn(" ... ok", noisy)
        self.assertIn(" ... FAIL", noisy)
        self.assertIn("verbose-boom", quiet)
        self.assertIn("verbose-boom", noisy)

    def test_executed_set_matches_unittest_discover(self):
        vanilla = unittest.TestLoader().discover("tests", pattern="test*.py")
        reported = verify_reporter.discover_suite()
        vanilla_ids = set(verify_reporter.collect_ids(vanilla))
        reported_ids = set(verify_reporter.collect_ids(reported))
        self.assertEqual(vanilla_ids, reported_ids)
        self.assertGreater(len(reported_ids), 100)
        clock = FakeClock()
        suite = _load_tests(clock, [("ok", 0.01, None)] * 4 + [("skip", 0.01, "n")])
        expected = set(verify_reporter.collect_ids(suite))
        result = verify_reporter.run_suite(
            suite, stream=io.StringIO(), clock=clock, verbose=False
        )
        executed = {tid for tid, _ in result.durations}
        self.assertEqual(expected, executed)

    def test_verify_sh_calls_reporter_and_keeps_guest_path(self):
        text = (ROOT / "ai/scripts/verify.sh").read_text()
        self.assertIn('python3 "$ROOT/ai/scripts/verify_reporter.py"', text)
        live = [
            line for line in text.splitlines()
            if line.lstrip().startswith("python3 -m unittest discover")
        ]
        self.assertEqual(live, [])
        guest = text.split("SET_AGENTS_GUEST_VERIFY", 1)[1]
        self.assertIn("tests.test_harness.HarnessTests.test_check_and_native_codex_agents", guest)
        self.assertIn("tests.test_harness.HarnessTests.test_shell_scripts_parse", guest)
        self.assertIn("python3 -m unittest -v", guest.split("else", 1)[0])
        # Historical discover string stays as a comment on the reporter line so
        # test_build_check_runs_before_the_suite... can still pin --check order.
        self.assertIn("python3 -m unittest discover -s tests -v", text)

    def test_discover_suite_imports_tests_when_invoked_as_script(self):
        # verify.sh runs `python3 ai/scripts/verify_reporter.py`. That leaves
        # sys.path[0] = ai/scripts; os.chdir in main does not change it.
        # In-process discover_suite() from this unittest is the wrong probe:
        # `tests` is already importable, which is how the crash slipped through.
        reporter = ROOT / "ai/scripts/verify_reporter.py"
        with tempfile.TemporaryDirectory(prefix="pkg5-discover-") as td:
            fixture = Path(td)
            scripts = fixture / "ai" / "scripts"
            tests_dir = fixture / "tests"
            scripts.mkdir(parents=True)
            tests_dir.mkdir()
            shutil.copy(reporter, scripts / "verify_reporter.py")
            (tests_dir / "test_tiny.py").write_text(
                "import unittest\n"
                "class TinyTests(unittest.TestCase):\n"
                "    def test_ok(self):\n"
                "        pass\n",
                encoding="utf-8",
            )
            proc = subprocess.run(
                [sys.executable, str(scripts / "verify_reporter.py")],
                cwd=fixture,
                capture_output=True,
                text=True,
            )
        self.assertNotIn("Start directory is not importable", proc.stderr)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("ran 1 tests", proc.stderr)
        self.assertIn("test_tiny.TinyTests.test_ok", proc.stderr)

    def test_wall_clock_loadtests_still_emit_progress_and_summary(self):
        # AC-5.1–5.3 with real sleeps (tiny), not the 1290-test gate.
        class LoadTests(unittest.TestCase):
            def test_fast_ok(self):
                time.sleep(0.01)

            def test_slow_ok(self):
                time.sleep(0.03)

            def test_fails(self):
                self.fail("loadtests-boom")

            def test_skip_reason(self):
                self.skipTest("loadtests-skip")

        stream = io.StringIO()
        suite = unittest.TestLoader().loadTestsFromTestCase(LoadTests)
        result = verify_reporter.run_suite(suite, stream=stream)
        output = stream.getvalue()
        self.assertFalse(result.wasSuccessful())
        self.assertIn("\r", output)
        self.assertIn("ETA", output)
        self.assertIn("✗", output)
        self.assertLess(output.index("FAIL: "), output.index("verify summary"))
        self.assertIn("loadtests-boom", output)
        self.assertIn("loadtests-skip (1):", output)
        self.assertIn("slowest:", output)
