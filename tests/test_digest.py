"""Feature 017 PKG-D (ADR-0027) — the derived morning digest and the honest hub.

New tests only, against the real CLI in a synthetic project tree (the suite's
established pattern: real subprocesses, never mocks).
"""

import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE_STATE = ROOT / "PROYECTO/ai/scripts/feature-state.py"


def _write_jsonl(path, entries):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for entry in entries:
            handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def _scaffold(tmp: Path):
    state = tmp / "ai/state"
    (state / "features").mkdir(parents=True)
    _write_jsonl(state / "narrative-log.jsonl", [
        {"at": "2026-08-01T10:00:00+00:00", "feature_id": "001-vieja", "package_id": "P1",
         "role": "integrator", "result": "done", "client": "Cierre viejo fuera de ventana",
         "tech": "old", "actor": "orchestrator"},
        {"at": "2026-08-04T09:00:00+00:00", "feature_id": "002-nueva", "package_id": "P1",
         "role": "implementer", "result": "done", "client": "La pieza nueva quedó lista",
         "tech": "new", "actor": "orchestrator"},
    ])
    _write_jsonl(state / "decisions-log.jsonl", [
        {"at": "2026-08-04T09:30:00+00:00", "slug": "una-decision", "title": "Una decisión",
         "context": "c", "decision": "se decidió X", "actor": "orchestrator"},
    ])
    _write_jsonl(state / "quickfix-log.jsonl", [
        {"at": "2026-08-04T10:00:00+00:00", "summary": "arreglo chico", "result": "done",
         "actor": "orchestrator", "files": [], "gate": "-"},
    ])
    (state / "features/002-nueva.json").write_text(json.dumps({
        "feature_id": "002-nueva", "phase": "PACKAGE_PLANNING", "packages": [],
        "history": [], "blockers": [], "updated_at": "2026-08-04T10:00:00+00:00",
    }))
    (state / "features/001-vieja.json").write_text(json.dumps({
        # 020-honest-dashboard/AC-02: the shared predicate compares `final_state` exactly
        # against "DONE" (the only value real code ever writes for a finished feature --
        # `PHASES`/`TERMINAL` are closed, all-caps vocabularies). A lowercase "done" here
        # would no longer be excluded by the new predicate and is not a value any real
        # code path produces, so this fixture uses the real one.
        "feature_id": "001-vieja", "phase": "PACKAGE_ACCEPTED", "final_state": "DONE",
        "packages": [], "history": [], "blockers": [],
        "updated_at": "2026-08-01T10:00:00+00:00",
    }))
    return state


class DigestTests(unittest.TestCase):
    def _run(self, tmp, *extra):
        return subprocess.run(
            [sys.executable, str(FEATURE_STATE), "digest", *extra],
            cwd=tmp, capture_output=True, text=True,
        )

    def test_digest_renders_window_sections_and_marks_closed_features_honestly(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _scaffold(tmp)
            result = self._run(tmp, "--since", "2026-08-03")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("DIGEST_WRITTEN", result.stdout)
            text = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
            for section in ("## Qué quedó listo", "## Qué se está haciendo", "## Qué falta",
                            "## Decisiones nuevas", "## Quick-fixes"):
                self.assertIn(section, text)
            self.assertIn("La pieza nueva quedó lista", text)
            # Outside the window — the old closing must not appear.
            self.assertNotIn("Cierre viejo fuera de ventana", text)
            # ADR-0027 honest pending: the final_state feature is not "being worked on".
            self.assertNotIn("001-vieja** — fase", text)
            self.assertIn("002-nueva", text)

    def test_digest_preserves_a_preexisting_handwritten_file(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _scaffold(tmp)
            notes = tmp / "docs/notas"
            notes.mkdir(parents=True)
            (notes / "BUENOS-DIAS.md").write_text("# Mi resumen manual\n\nTexto artesanal valioso.\n")
            result = self._run(tmp, "--since", "2026-08-03")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (notes / "BUENOS-DIAS.md").read_text(encoding="utf-8")
            self.assertIn("Texto artesanal valioso.", text)
            self.assertIn("<!-- notas:auto -->", text)
            self.assertIn("## Qué quedó listo", text)

    def test_digest_is_idempotent_across_reruns(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _scaffold(tmp)
            self._run(tmp, "--since", "2026-08-03")
            first = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
            self._run(tmp, "--since", "2026-08-03")
            second = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
            # Only the "generado <ts>" line may differ between runs.
            strip = lambda text: "\n".join(
                line for line in text.splitlines() if not line.startswith("_Ventana:"))
            self.assertEqual(strip(first), strip(second))


class HonestHubTests(unittest.TestCase):
    def test_sync_notes_hub_skips_final_state_features_in_pending(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _scaffold(tmp)
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "sync-notes"],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            hub = (tmp / "docs/notas/00 - Proyecto.md").read_text(encoding="utf-8")
            pending = hub.split("## Qué falta", 1)[1].split("##", 1)[0]
            self.assertNotIn("001-vieja", pending)


def _scaffold_honesty_fixtures(tmp: Path, blocked_at: str, resolved_earlier: str, stale_updated_at: str):
    """020-honest-dashboard/PKG-1: a BLOCKED feature with TWO blocker entries (one already
    resolved, one live -- 002-adaptive-pi-orchestration's real shape) so AC-01's "days since
    the LAST unresolved blocker, never updated_at blindly" has something to get wrong; a
    genuinely DONE feature; and a live, unblocked, stale feature for AC-03's mark.

    F-02 repair (review of PKG-1): `003-blocked` also carries one package with an open
    finding -- same shape as 002-adaptive-pi-orchestration's real state (which is why the
    real digest shows "5 hallazgos abiertos" for it). With `packages: []` (the previous
    shape), `_pending_bits` can never return more than the single `⛔ bloqueo:` bit, so the
    two-mentions cap (AC-03) is structurally impossible to violate no matter what the code
    does -- this finding-bearing package is what lets the cap actually get exercised.
    """
    state = tmp / "ai/state"
    (state / "features").mkdir(parents=True)
    _write_jsonl(state / "narrative-log.jsonl", [])
    _write_jsonl(state / "decisions-log.jsonl", [])
    _write_jsonl(state / "quickfix-log.jsonl", [])
    (state / "features/003-blocked.json").write_text(json.dumps({
        "feature_id": "003-blocked", "phase": "BLOCKED", "final_state": "BLOCKED",
        "packages": [
            {
                "package_id": "P1-blocked",
                "status": "in_progress",
                "findings": [
                    {"id": "F-01", "severity": "high", "status": "open",
                     "category": "example finding kept open by the blocker"},
                ],
                "tasks": [],
            },
        ],
        "history": [],
        "blockers": [
            {"package_id": "P1", "reason": "ya resuelta hace rato", "at": resolved_earlier,
             "resolved_at": resolved_earlier},
            {"package_id": "P1", "reason": "HUMAN_DECISION_REQUIRED: necesita autorizacion",
             "at": blocked_at},
        ],
        "updated_at": blocked_at,
    }))
    (state / "features/004-done.json").write_text(json.dumps({
        "feature_id": "004-done", "phase": "DONE", "final_state": "DONE",
        "packages": [], "history": [], "blockers": [],
        "updated_at": "2026-01-01T00:00:00+00:00",
    }))
    (state / "features/005-stale.json").write_text(json.dumps({
        "feature_id": "005-stale", "phase": "PACKAGE_ACCEPTED",
        "packages": [], "history": [], "blockers": [],
        "updated_at": stale_updated_at,
    }))
    return state


class HonestPredicateTests(unittest.TestCase):
    """020-honest-dashboard AC-01/AC-02/AC-03/AC-05/AC-12: the shared `feature_is_live`
    predicate (ADR-0040) and the sections it feeds. AC-05/AC-12 must fail red against
    today's `cli_reporting.py`/`_hub_body`, which drop a BLOCKED feature from every digest
    and hub section exactly like a genuinely DONE one."""

    def setUp(self):
        now = datetime.now(timezone.utc)
        self.blocked_at = (now - timedelta(days=3)).replace(microsecond=0).isoformat()
        self.resolved_earlier = (now - timedelta(days=10)).replace(microsecond=0).isoformat()
        self.stale_updated_at = (now - timedelta(days=9)).replace(microsecond=0).isoformat()

    def _digest_text(self, tmp):
        _scaffold_honesty_fixtures(tmp, self.blocked_at, self.resolved_earlier, self.stale_updated_at)
        result = subprocess.run(
            [sys.executable, str(FEATURE_STATE), "digest", "--since", "2020-01-01"],
            cwd=tmp, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")

    def test_digest_names_a_blocked_feature_even_though_it_carries_final_state(self):
        """AC-05: a BLOCKED feature must be named in the digest, with a fixed
        '## Necesita tu decisión' section computed from the LAST unresolved blocker (3 days
        ago), never the earlier resolved one (10 days ago) and never updated_at blindly."""
        with tempfile.TemporaryDirectory() as raw:
            text = self._digest_text(Path(raw))
        self.assertIn("## Necesita tu decisión", text)
        headline = text.split("## Necesita tu decisión", 1)[1].split("##", 1)[0]
        self.assertIn("003-blocked", headline)
        self.assertIn("hace 3 días", headline)
        self.assertNotIn("hace 10 días", headline)
        self.assertNotIn("004-done** — fase", text)

    def test_digest_caps_a_blocked_feature_at_two_mentions_and_marks_the_stale_one(self):
        """AC-03: a blocked feature is exempt from 'Qué se está haciendo' entirely (a 3rd
        mention beyond AC-01's headline and 'Qué falta''s bit would be redundant, SC-06); an
        unblocked live feature past the 7-day threshold gets marked stale there instead.

        F-02 repair (review of PKG-1): the earlier version of this test never counted
        mentions, and its fixture (`packages: []`) could not have produced more than the
        cap even under the bug -- `_pending_bits` had nothing else to offer. The fixture now
        gives `003-blocked` an open finding too (002-adaptive-pi-orchestration's real
        shape), so the count below is the actual regression test for the tope: without the
        F-01 fix, the literal `⛔ bloqueo:` duplicate of the AC-01 headline would still land
        in 'Qué falta' alongside the finding bit, mentioning the feature THREE times."""
        with tempfile.TemporaryDirectory() as raw:
            text = self._digest_text(Path(raw))
        working = text.split("## Qué se está haciendo", 1)[1].split("## Qué falta", 1)[0]
        self.assertNotIn("003-blocked", working)
        self.assertIn("005-stale", working)
        self.assertIn("estancada", working)
        falta = text.split("## Qué falta", 1)[1].split("##", 1)[0]
        self.assertIn("003-blocked", falta)
        # New information survives ("Qué falta"'s own bit)...
        self.assertIn("hallazgos abiertos", falta)
        # ...but the literal duplicate of the AC-01 headline does not: that bit alone
        # carries zero information beyond what "## Necesita tu decisión" already said.
        self.assertNotIn("⛔", falta)
        total_mentions = text.count("003-blocked")
        self.assertEqual(
            total_mentions, 2,
            f"AC-03 caps mentions of a blocked feature at two (headline + one actionable "
            f"'Qué falta' bit); found {total_mentions} in:\n{text}",
        )

    def test_hub_lists_the_blocked_feature_in_que_falta(self):
        """AC-12: the hub already tags a BLOCKED feature under '## Features'; today it drops
        it from '## Qué falta' (`_hub_body`'s `if data.get('final_state'): continue`)."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            _scaffold_honesty_fixtures(tmp, self.blocked_at, self.resolved_earlier, self.stale_updated_at)
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "sync-notes"],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            hub = (tmp / "docs/notas/00 - Proyecto.md").read_text(encoding="utf-8")
        features_section = hub.split("## Features", 1)[1].split("##", 1)[0]
        self.assertIn("003-blocked", features_section)
        self.assertIn("BLOCKED", features_section)
        falta = hub.split("## Qué falta", 1)[1].split("##", 1)[0]
        self.assertIn("003-blocked", falta)


class DoctrineTests(unittest.TestCase):
    def test_milestone_narration_is_doctrine_in_all_shared_files(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md"):
            text = (ROOT / path).read_text()
            self.assertIn("by MILESTONE, not by spawn (ADR-0027)", text, path)
        orchestrator = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("by MILESTONE, not by spawn", orchestrator)
        self.assertIn("feature-state.py digest", orchestrator)

    def test_resume_feature_reads_the_living_notes(self):
        text = (ROOT / "Global/_canonical/commands/resume-feature.md").read_text()
        self.assertIn("docs/notas/features/<feature_id>.md", text)
        self.assertIn("## Qué falta", text)

    def test_session_open_reads_hub_without_vault(self):
        text = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("no vault required", text)


if __name__ == "__main__":
    unittest.main()
