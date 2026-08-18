#!/usr/bin/env python3
"""Presenter for verify.sh's unittest suite (033 PKG-5, AC-5.1–AC-5.5).

Replaces `python3 -m unittest discover -s tests -v` with the same discovered
set (AC-5.5) and a readable live presentation: one rewritten progress line with
ETA from measured pace (AC-5.1), the full failure block as soon as a test
fails (AC-5.2), and a copiable final summary (AC-5.3).

Streams: progress, failure blocks, and the summary go to stderr (or an injected
stream) so they do not mix with test stdout. The progress line uses ``\\r``.
Clock: injectable for tests; default ``time.monotonic``.

Verbose: SET_AGENTS_VERIFY_VERBOSE=1 prints per-test status lines. Default is
the summary presenter; nothing is discarded, it moves behind the env var.

AC-5.6 (parallel shards) is intentionally absent: there is no isolation proof
for N interpreters against the tests/__init__.py sandbox.
"""

from __future__ import annotations

import os
import sys
import time
import unittest
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERBOSE_ENV = "SET_AGENTS_VERIFY_VERBOSE"
SLOWEST_LIMIT = 10
SEPARATOR1 = "=" * 70
SEPARATOR2 = "-" * 70
SUMMARY_BAR = "-" * 40


def verbose_enabled(environ=None) -> bool:
    env = os.environ if environ is None else environ
    return env.get(VERBOSE_ENV) == "1"


def format_duration(seconds: float) -> str:
    """Compact whole-second duration for the live line and summary totals."""
    total = max(0, int(round(seconds)))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def format_precise(seconds: float) -> str:
    return f"{seconds:.3f}s"


def progress_line(done: int, total: int, elapsed_s: float, fail_count: int) -> str:
    """ETA is remaining tests times the measured seconds-per-test so far."""
    if done <= 0:
        eta = "—"
    else:
        eta = format_duration(elapsed_s * (total - done) / done)
    return f"{done}/{total} · {format_duration(elapsed_s)} · ETA {eta} · ✗{fail_count}"


def iter_tests(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from iter_tests(item)
        else:
            yield item


def collect_ids(suite) -> list[str]:
    return [test.id() for test in iter_tests(suite)]


def discover_suite(start_dir="tests", pattern="test*.py", top_level_dir=None):
    """Same discovery as `python3 -m unittest discover -s tests`.

    Invoking this file as a script (`python3 ai/scripts/verify_reporter.py`)
    leaves ``sys.path[0]`` as ``ai/scripts``. ``os.chdir(ROOT)`` in ``main``
    does not change that, so unittest treats ``tests`` as a dotted name and
    raises ``ImportError: Start directory is not importable``. Put the repo
    root on ``sys.path`` before discover so the same invocation as verify.sh
    can import ``tests``.
    """
    root = str(ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    return unittest.TestLoader().discover(
        start_dir, pattern=pattern, top_level_dir=top_level_dir
    )


class VerifyTestResult(unittest.TestResult):
    def __init__(self, stream, clock, total, verbose=False):
        super().__init__()
        self.stream = stream
        self.clock = clock
        self.total = total
        self.verbose = verbose
        self.durations: list[tuple[str, float]] = []
        self.completed = 0
        self._run_start = 0.0
        self._test_start = 0.0
        self._progress_len = 0

    def startTestRun(self):
        super().startTestRun()
        self._run_start = self.clock()

    def startTest(self, test):
        super().startTest(test)
        self._test_start = self.clock()

    def stopTest(self, test):
        self.durations.append((test.id(), self.clock() - self._test_start))
        self.completed += 1
        self._write_progress()
        super().stopTest(test)

    def addSuccess(self, test):
        super().addSuccess(test)
        self._verbose_status(test, "ok")

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._verbose_status(test, f"skipped {reason!r}")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._verbose_status(test, "FAIL")
        self._emit_problem("FAIL", test, self.failures[-1][1])

    def addError(self, test, err):
        super().addError(test, err)
        self._verbose_status(test, "ERROR")
        self._emit_problem("ERROR", test, self.errors[-1][1])

    def addSubTest(self, test, subtest, err):
        super().addSubTest(test, subtest, err)
        if err is None:
            return
        kind = "FAIL" if issubclass(err[0], test.failureException) else "ERROR"
        detail = self.failures[-1][1] if kind == "FAIL" else self.errors[-1][1]
        self._emit_problem(kind, subtest, detail)

    def fail_count(self) -> int:
        return len(self.failures) + len(self.errors)

    def _verbose_status(self, test, status: str) -> None:
        if not self.verbose:
            return
        self._end_progress_line()
        self.stream.write(f"{test.id()} ... {status}\n")
        self.stream.flush()

    def _emit_problem(self, kind: str, test, detail: str) -> None:
        self._end_progress_line()
        self.stream.write(f"{SEPARATOR1}\n")
        self.stream.write(f"{kind}: {test.id()}\n")
        self.stream.write(f"{SEPARATOR2}\n")
        self.stream.write(detail if detail.endswith("\n") else detail + "\n")
        self.stream.flush()

    def _write_progress(self) -> None:
        elapsed = self.clock() - self._run_start
        line = progress_line(self.completed, self.total, elapsed, self.fail_count())
        pad = max(0, self._progress_len - len(line))
        self.stream.write("\r" + line + (" " * pad))
        self.stream.flush()
        self._progress_len = len(line)

    def _end_progress_line(self) -> None:
        if self._progress_len:
            self.stream.write("\n")
            self._progress_len = 0

    def print_summary(self) -> None:
        self._end_progress_line()
        elapsed = self.clock() - self._run_start
        self.stream.write(f"{SUMMARY_BAR}\n")
        self.stream.write("verify summary\n")
        self.stream.write(
            f"ran {self.completed} tests in {format_duration(elapsed)}  "
            f"fail={len(self.failures)}  error={len(self.errors)}  "
            f"skip={len(self.skipped)}\n"
        )
        self.stream.write(f"failures ({len(self.failures) + len(self.errors)}):\n")
        for test, _ in self.failures:
            self.stream.write(f"  FAIL {test.id()}\n")
        for test, _ in self.errors:
            self.stream.write(f"  ERROR {test.id()}\n")
        grouped: dict[str, list[str]] = defaultdict(list)
        for test, reason in self.skipped:
            grouped[reason].append(test.id())
        self.stream.write(f"skips ({len(self.skipped)}):\n")
        for reason in sorted(grouped):
            ids = sorted(grouped[reason])
            self.stream.write(f"  {reason} ({len(ids)}):\n")
            for tid in ids:
                self.stream.write(f"    {tid}\n")
        self.stream.write("slowest:\n")
        ranked = sorted(self.durations, key=lambda item: item[1], reverse=True)
        for tid, duration in ranked[:SLOWEST_LIMIT]:
            self.stream.write(f"  {format_precise(duration)}  {tid}\n")
        self.stream.write(f"{SUMMARY_BAR}\n")
        self.stream.flush()


def run_suite(suite, *, stream=None, clock=None, verbose=False) -> VerifyTestResult:
    stream = sys.stderr if stream is None else stream
    clock = time.monotonic if clock is None else clock
    result = VerifyTestResult(
        stream=stream,
        clock=clock,
        total=suite.countTestCases(),
        verbose=verbose,
    )
    result.startTestRun()
    try:
        suite.run(result)
    finally:
        result.stopTestRun()
        result.print_summary()
    return result


def main(argv=None) -> int:
    del argv
    os.chdir(ROOT)
    suite = discover_suite()
    result = run_suite(suite, stream=sys.stderr, verbose=verbose_enabled())
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(main())
