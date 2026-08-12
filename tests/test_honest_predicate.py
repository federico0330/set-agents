"""020-honest-dashboard PKG-1 (ADR-0040) — direct unit coverage for the shared
"is this feature still live" predicate in `feature_state_lib/model.py`.

`tests/test_digest.py` and `tests/test_harness.py` already exercise this predicate
end-to-end through `cmd_digest`, `_hub_body`, and `cmd_status` (where the observable
behavior actually matters); this file pins the smaller building blocks in isolation --
edge cases a rendering-level test would be an awkward way to reach (an empty blockers
list, a malformed blocker entry, a naive-vs-aware timestamp, the exact 7-day boundary).
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai/scripts"))

from feature_state_lib import model  # noqa: E402


def _ago(days: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()


class FeatureIsLiveTests(unittest.TestCase):
    def test_no_final_state_is_live(self):
        self.assertTrue(model.feature_is_live({}))

    def test_blocked_is_live(self):
        self.assertTrue(model.feature_is_live({"final_state": "BLOCKED"}))

    def test_done_is_not_live(self):
        self.assertFalse(model.feature_is_live({"final_state": "DONE"}))

    def test_comparison_is_exact_not_truthy(self):
        # AC-02: closed vocabulary, case-sensitive -- a value real code never writes
        # must not accidentally get treated as the terminal one.
        self.assertTrue(model.feature_is_live({"final_state": "done"}))
        self.assertTrue(model.feature_is_live({"final_state": "Done"}))


class OpenBlockerTests(unittest.TestCase):
    def test_no_blockers_is_none(self):
        self.assertIsNone(model.open_blocker({"blockers": []}))
        self.assertIsNone(model.open_blocker({}))

    def test_all_resolved_is_none(self):
        data = {"blockers": [{"reason": "x", "at": "2026-01-01T00:00:00+00:00", "resolved_at": "2026-01-02T00:00:00+00:00"}]}
        self.assertIsNone(model.open_blocker(data))

    def test_skips_a_resolved_entry_that_precedes_the_live_one(self):
        # 002-adaptive-pi-orchestration's real shape: one resolved entry, then a live one.
        data = {"blockers": [
            {"reason": "ya resuelta", "at": "2026-07-24T15:57:02+00:00", "resolved_at": "2026-07-24T15:59:02+00:00"},
            {"reason": "vigente", "at": "2026-07-24T16:16:04+00:00"},
        ]}
        blocker = model.open_blocker(data)
        self.assertEqual(blocker["reason"], "vigente")

    def test_returns_the_last_unresolved_not_the_first_when_two_are_open(self):
        # Two genuinely unresolved entries (a feature blocked twice with neither resolved
        # in between, or a malformed record) -- must pick the most recent one, not the
        # first one in list order.
        data = {"blockers": [
            {"reason": "primer bloqueo", "at": "2026-07-01T00:00:00+00:00"},
            {"reason": "segundo bloqueo", "at": "2026-07-24T16:16:04+00:00"},
        ]}
        blocker = model.open_blocker(data)
        self.assertEqual(blocker["reason"], "segundo bloqueo")

    def test_ignores_non_dict_entries(self):
        data = {"blockers": ["not-a-dict", {"reason": "real", "at": "2026-01-01T00:00:00+00:00"}]}
        self.assertEqual(model.open_blocker(data)["reason"], "real")


class DaysSinceTests(unittest.TestCase):
    def test_none_for_missing_timestamp(self):
        self.assertIsNone(model.days_since(None))
        self.assertIsNone(model.days_since(""))

    def test_none_for_unparsable_timestamp(self):
        self.assertIsNone(model.days_since("not-a-date"))

    def test_counts_whole_days(self):
        self.assertEqual(model.days_since(_ago(5)), 5)

    def test_naive_timestamp_is_treated_as_utc(self):
        naive = (datetime.now(timezone.utc) - timedelta(days=3)).replace(microsecond=0, tzinfo=None).isoformat()
        self.assertEqual(model.days_since(naive), 3)

    def test_never_negative(self):
        # A clock skew or a future-dated fixture must not read as "negative days ago".
        self.assertEqual(model.days_since(_ago(-1)), 0)


class BlockedDaysAndStaleDaysTests(unittest.TestCase):
    def test_blocked_days_none_when_not_blocked(self):
        self.assertIsNone(model.blocked_days({"blockers": []}))

    def test_blocked_days_from_the_open_blocker(self):
        data = {"blockers": [{"reason": "x", "at": _ago(4)}]}
        self.assertEqual(model.blocked_days(data), 4)

    def test_stale_days_none_when_done(self):
        data = {"final_state": "DONE", "updated_at": _ago(30), "blockers": []}
        self.assertIsNone(model.stale_days(data))

    def test_stale_days_none_when_blocked(self):
        # AC-03: exempt -- AC-01's headline already covers it in more detail.
        data = {"final_state": "BLOCKED", "updated_at": _ago(30), "blockers": [{"reason": "x", "at": _ago(30)}]}
        self.assertIsNone(model.stale_days(data))

    def test_stale_days_for_a_live_unblocked_feature(self):
        data = {"updated_at": _ago(9), "blockers": []}
        self.assertEqual(model.stale_days(data), 9)

    def test_feature_is_stale_boundary_at_the_threshold(self):
        self.assertEqual(model.STALE_THRESHOLD_DAYS, 7)
        just_under = {"updated_at": _ago(6), "blockers": []}
        exactly_at = {"updated_at": _ago(7), "blockers": []}
        self.assertFalse(model.feature_is_stale(just_under))
        self.assertTrue(model.feature_is_stale(exactly_at))

    def test_feature_is_stale_false_for_a_blocked_feature_no_matter_how_old(self):
        data = {"final_state": "BLOCKED", "updated_at": _ago(90), "blockers": [{"reason": "x", "at": _ago(90)}]}
        self.assertFalse(model.feature_is_stale(data))


if __name__ == "__main__":
    unittest.main()
