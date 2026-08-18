"""Feature 017 PKG-D (ADR-0027) — the derived morning digest and the honest hub.

New tests only, against the real CLI in a synthetic project tree (the suite's
established pattern: real subprocesses, never mocks).
"""

import json
import os
import re
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


def _status_cell(text: str, feature_id: str, column: str) -> str:
    """Pull one markdown-table cell out of STATUS.md by (feature_id, column header).
    Fixtures below never put a literal '|' inside the cells under test, so a plain
    split is exact -- the escaping `render_status.summarize_feature` applies for a
    hostile blocker/reason is exercised by `test_harness.py`'s injected-heading test,
    untouched by this package."""
    header_line = next(line for line in text.splitlines() if line.startswith("| Feature "))
    headers = [h.strip() for h in header_line.strip("|").split("|")]
    idx = headers.index(column)
    row_line = next(line for line in text.splitlines() if line.startswith(f"| {feature_id} "))
    cells = [c.strip() for c in row_line.strip("|").split("|")]
    return cells[idx]


def _write_feature(state_dir: Path, feature_id: str, payload: dict) -> None:
    (state_dir / "features").mkdir(parents=True, exist_ok=True)
    (state_dir / "features" / f"{feature_id}.json").write_text(
        json.dumps({"feature_id": feature_id, **payload}, ensure_ascii=False)
    )


class NextStepTranslationTests(unittest.TestCase):
    """028/N3a AC-11 x AC-17: STATUS.md's "Próximo paso" carries `next_transition`'s
    `reason`, translated -- never the bare `next` phase name it used to show
    (`next_transition(data).get("next") or "-"`, D-4a), and the four states AC-17
    names get an explicit, tested contract."""

    def _render(self, tmp, **features):
        state_dir = tmp / "ai/state"
        for feature_id, payload in features.items():
            _write_feature(state_dir, feature_id, payload)
        result = subprocess.run(
            [sys.executable, str(FEATURE_STATE), "render-status", "--state-dir", str(state_dir)],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return (state_dir / "STATUS.md").read_text(encoding="utf-8")

    def test_mordida_a_regression_to_bare_next_would_show_the_raw_phase_name_here(self):
        """The specific bite the package brief asked for: a state whose `next` and
        `reason` clearly diverge (PACKAGE_IMPLEMENTATION, all tasks done -> `next` is
        the bare phase "PACKAGE_GATES", `reason` is "all package tasks completed").
        `next_transition(data).get("next") or "-"` would print the literal string
        "PACKAGE_GATES" in the cell; `describe_next_step` prints translated prose that
        never contains it. If someone reverts render_status.py to the old one-liner,
        this test goes red on the `assertNotIn` below -- proven by neutralizing the
        fix in this very test run (see the package evidence for the red/green pair)."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._render(tmp, **{
                "700-impl-done": {
                    "phase": "PACKAGE_IMPLEMENTATION", "current_package_id": "P1",
                    "packages": [{"package_id": "P1", "status": "in_progress",
                                  "tasks": [{"id": "T-001", "status": "completed"}]}],
                    "history": [], "blockers": [], "updated_at": "2026-08-15T00:00:00+00:00",
                },
            })
        cell = _status_cell(text, "700-impl-done", "Próximo paso")
        self.assertNotEqual(cell, "PACKAGE_GATES")
        self.assertNotIn("PACKAGE_GATES", cell)
        self.assertIn("gates", cell)

    def test_ac17_terminal_done_shows_a_dash_never_the_word_terminal(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._render(tmp, **{
                "701-done": {
                    "phase": "DONE", "final_state": "DONE", "packages": [],
                    "history": [], "blockers": [], "updated_at": "2026-01-01T00:00:00+00:00",
                },
            })
        cell = _status_cell(text, "701-done", "Próximo paso")
        self.assertEqual(cell, "—")
        self.assertNotIn("terminal", cell)

    def test_ac17_blocked_names_it_as_the_humans_turn_not_a_bare_dash(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._render(tmp, **{
                "702-blocked": {
                    "phase": "BLOCKED", "final_state": "BLOCKED", "packages": [],
                    "history": [],
                    "blockers": [{"reason": "HUMAN_DECISION_REQUIRED: x", "at": "2026-08-10T00:00:00+00:00"}],
                    "updated_at": "2026-08-10T00:00:00+00:00",
                },
            })
        cell = _status_cell(text, "702-blocked", "Próximo paso")
        self.assertNotEqual(cell, "—")
        self.assertNotEqual(cell, "-")
        self.assertNotIn("terminal", cell)
        self.assertIn("decisión", cell)

    def test_ac17_no_package_branch_is_translated_never_the_raw_fallback_string(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._render(tmp, **{
                "703-no-package": {
                    "phase": "PACKAGE_GATES", "packages": [],
                    "history": [], "blockers": [], "updated_at": "2026-08-15T00:00:00+00:00",
                },
            })
        cell = _status_cell(text, "703-no-package", "Próximo paso")
        self.assertNotIn("record required event before continuing", cell)
        self.assertIn("registrar el evento pendiente", cell)

    def test_ac17_a_stale_live_feature_is_flagged_as_possibly_interrupted(self):
        old = (datetime.now(timezone.utc) - timedelta(days=9)).replace(microsecond=0).isoformat()
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._render(tmp, **{
                "704-stale": {
                    "phase": "PACKAGE_IMPLEMENTATION", "current_package_id": "P1",
                    "packages": [{"package_id": "P1", "status": "in_progress",
                                  "tasks": [{"id": "T-001", "status": "planned"}]}],
                    "history": [], "blockers": [], "updated_at": old,
                },
            })
        cell = _status_cell(text, "704-stale", "Próximo paso")
        self.assertIn("interrumpido", cell)
        self.assertIn("9 días", cell)


class DigestPlainLanguageTests(unittest.TestCase):
    """028/N3a AC-12: the digest's "Qué falta" bit stops publishing raw flags, command
    names, and English task-id dumps -- D-4b/D-4c's own cited examples, run against
    today's code."""

    def _digest(self, tmp, **features):
        state_dir = tmp / "ai/state"
        for feature_id, payload in features.items():
            _write_feature(state_dir, feature_id, payload)
        result = subprocess.run(
            [sys.executable, str(FEATURE_STATE), "digest", "--state-dir", str(state_dir),
             "--since", "2020-01-01"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")

    def test_module_impact_reason_never_leaks_the_cli_flags_d4b(self):
        """D-4b, reproduced verbatim: a `PACKAGE_ACCEPTED` feature with an accepted
        package that never recorded (or waived) a module impact used to publish
        "→ `PACKAGE_ACCEPTED` — P3-graph-view: module impact required
        (record-module-impact) or waived (--module-impact-waived --reason)" straight
        into the digest."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._digest(tmp, **{
                "705-accepted": {
                    "phase": "PACKAGE_ACCEPTED",
                    "packages": [{"package_id": "P3-graph-view", "status": "accepted"}],
                    "history": [], "blockers": [], "updated_at": "2026-08-15T00:00:00+00:00",
                },
            })
        falta = text.split("## Qué falta", 1)[1].split("##", 1)[0]
        self.assertNotIn("record-module-impact", falta)
        self.assertNotIn("--module-impact-waived", falta)
        self.assertNotIn("PACKAGE_ACCEPTED", falta)
        self.assertIn("P3-graph-view", falta)
        self.assertIn("impacto de módulo", falta)

    def test_pending_tasks_show_a_count_never_the_raw_english_titles_d4c(self):
        """D-4c: `task["id"]` has held free-form English titles in real history
        ("additive schema/migration and invariants, narrow classifier + Pi terminal
        plumbing…") -- the digest must stop dumping them raw."""
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            text = self._digest(tmp, **{
                "706-pending": {
                    "phase": "PACKAGE_IMPLEMENTATION", "current_package_id": "P1",
                    "packages": [{
                        "package_id": "P1", "status": "in_progress",
                        "tasks": [
                            {"id": "additive schema/migration and invariants", "status": "planned"},
                            {"id": "narrow classifier + Pi terminal plumbing", "status": "planned"},
                        ],
                    }],
                    "history": [], "blockers": [], "updated_at": "2026-08-15T00:00:00+00:00",
                },
            })
        falta = text.split("## Qué falta", 1)[1].split("##", 1)[0]
        self.assertNotIn("additive schema/migration", falta)
        self.assertNotIn("narrow classifier", falta)
        self.assertIn("2 tareas pendientes en P1", falta)


class DigestNoMidSentenceTruncationTests(unittest.TestCase):
    """028/N3a AC-13: the three truncation points in `cmd_digest` (blockers 120,
    closes 300, decisions 200) stop cutting mid-sentence. Criterio de cierre: cero
    `…` al final de línea en esas tres secciones."""

    LONG = (
        "Esta es una narración deliberadamente larga, sin ningún punto ni coma antes "
        "del viejo límite de caracteres, escrita así a propósito para que un corte por "
        "cantidad de caracteres caiga a mitad de una palabra o de una oración y así "
        "se pueda comprobar que el corte silencioso ya no ocurre en esta sección del "
        "digest, sin importar cuán larga sea la narración original que un agente haya "
        "escrito en su cierre."
    )

    def test_blocker_reason_in_necesita_tu_decision_is_never_cut(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state_dir = tmp / "ai/state"
            _write_feature(state_dir, "707-blocked-long", {
                "phase": "BLOCKED", "final_state": "BLOCKED", "packages": [], "history": [],
                "blockers": [{"reason": self.LONG, "at": "2026-08-10T00:00:00+00:00"}],
                "updated_at": "2026-08-10T00:00:00+00:00",
            })
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "digest", "--state-dir", str(state_dir),
                 "--since", "2020-01-01"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
        headline = text.split("## Necesita tu decisión", 1)[1].split("##", 1)[0]
        self.assertIn(self.LONG, headline)
        for line in headline.splitlines():
            self.assertFalse(line.rstrip().endswith("…"), line)

    def test_closing_narration_in_que_quedo_listo_is_never_cut(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state_dir = tmp / "ai/state"
            _write_feature(state_dir, "708-active", {
                "phase": "PACKAGE_PLANNING", "packages": [], "history": [], "blockers": [],
                "updated_at": "2026-08-15T00:00:00+00:00",
            })
            _write_jsonl(state_dir / "narrative-log.jsonl", [
                {"at": "2026-08-15T00:00:00+00:00", "feature_id": "708-active", "package_id": "-",
                 "role": "implementer", "result": "done", "client": self.LONG,
                 "tech": "x", "actor": "orchestrator"},
            ])
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "digest", "--state-dir", str(state_dir),
                 "--since", "2020-01-01"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
        section = text.split("## Qué quedó listo", 1)[1].split("##", 1)[0]
        self.assertIn(self.LONG, section)
        for line in section.splitlines():
            self.assertFalse(line.rstrip().endswith("…"), line)

    def test_decision_text_in_decisiones_nuevas_is_never_cut(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state_dir = tmp / "ai/state"
            _write_feature(state_dir, "709-any", {
                "phase": "PACKAGE_PLANNING", "packages": [], "history": [], "blockers": [],
                "updated_at": "2026-08-15T00:00:00+00:00",
            })
            _write_jsonl(state_dir / "decisions-log.jsonl", [
                {"at": "2026-08-15T00:00:00+00:00", "slug": "una-decision-larga",
                 "title": "Una decisión larga", "context": "c", "decision": self.LONG,
                 "actor": "orchestrator"},
            ])
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "digest", "--state-dir", str(state_dir),
                 "--since", "2020-01-01"],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            text = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
        section = text.split("## Decisiones nuevas", 1)[1].split("##", 1)[0]
        self.assertIn(self.LONG, section)
        for line in section.splitlines():
            self.assertFalse(line.rstrip().endswith("…"), line)


class DigestRegenerationCadenceTests(unittest.TestCase):
    """028/N3a AC-14: the digest regenerates at phase/turn close (`sync-notes`, its
    own docstring's "run it at phase close and end of turn"), never on every
    per-mutation write (`log-narrative`/`log-quickfix`)."""

    def test_sync_notes_alone_produces_a_fresh_digest_with_matching_timestamps(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state_dir = tmp / "ai/state"
            _write_feature(state_dir, "710-any", {
                "phase": "PACKAGE_PLANNING", "packages": [], "history": [], "blockers": [],
                "updated_at": "2026-08-15T00:00:00+00:00",
            })
            digest_path = tmp / "docs/notas/BUENOS-DIAS.md"
            self.assertFalse(digest_path.exists(), "no digest before sync-notes ever ran")
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "sync-notes", "--state-dir", str(state_dir)],
                capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("NOTES_SYNCED", result.stdout)
            self.assertTrue(digest_path.exists(), "sync-notes must regenerate the digest by itself")
            status_text = (state_dir / "STATUS.md").read_text(encoding="utf-8")
            digest_text = digest_path.read_text(encoding="utf-8")
            status_ts = status_text.splitlines()[4].split("Actualizado: ", 1)[1].strip()
            digest_ts = digest_text.splitlines()[3].split("generado ", 1)[1].strip("_ ")
            status_dt = datetime.fromisoformat(status_ts)
            digest_dt = datetime.fromisoformat(digest_ts)
            self.assertLessEqual(
                abs((status_dt - digest_dt).total_seconds()), 5,
                "AC-14's measurable criterion: BUENOS-DIAS.md's 'generado' must never "
                "trail STATUS.md's 'Actualizado' -- both come from the same sync-notes call",
            )

    def test_log_narrative_alone_never_writes_the_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state_dir = tmp / "ai/state"
            _write_feature(state_dir, "711-any", {
                "phase": "PACKAGE_PLANNING", "packages": [], "history": [], "blockers": [],
                "updated_at": "2026-08-15T00:00:00+00:00",
            })
            digest_path = tmp / "docs/notas/BUENOS-DIAS.md"
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "log-narrative",
                 "--client", "Se avanzó en la implementación prevista.",
                 "--tech", "Se completó la tarea técnica y quedó lista para continuar.",
                 "--feature-id", "711-any", "--result", "done",
                 "--milestone", "no",
                 "--log-file", str(state_dir / "narrative-log.jsonl")],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(
                digest_path.exists(),
                "AC-14: a single narrated close is not a phase/turn close -- the "
                "tracked BUENOS-DIAS.md must not move on every mutation (024/C1 + "
                "027's owned-paths hardening)",
            )


class StatusRenderIsLocaleIndependentTests(unittest.TestCase):
    """STATUS.md is Spanish prose; the machine's locale never gets a vote on it."""

    def _render_under(self, tmp, env_extra):
        state_dir = tmp / "ai/state"
        _write_feature(state_dir, "900-acentos", {
            "feature_id": "900-acentos", "phase": "PACKAGE_PLANNING",
            "title": "Acentuación, bitácora y días",
        })
        env = {k: v for k, v in os.environ.items() if k not in {"LANG", "LC_ALL"}}
        env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(FEATURE_STATE), "render-status", "--state-dir", str(state_dir)],
            capture_output=True, text=True, env=env,
        ), state_dir

    def test_a_non_utf8_locale_still_produces_the_dashboard_and_leaves_no_debris(self):
        """Before this repair the command exited 0 while writing NOTHING.

        Measured 2026-08-18 on Linux, `PYTHONCOERCECLOCALE=0 LC_ALL=C`: the write
        raised UnicodeEncodeError on "Bitácora", a bare `except Exception: pass`
        swallowed it, `render-status` returned 0, STATUS.md never appeared and the
        half-written temp file stayed in ai/state/ -- one more per failed render.
        The harness's own dashboard reporting success while going silently stale is
        the precise failure mode it exists to prevent. Windows CI hit the same omission
        from the other side, writing cp1252 that later reads rejected."""
        with tempfile.TemporaryDirectory() as td:
            result, state_dir = self._render_under(Path(td), {
                "PYTHONCOERCECLOCALE": "0", "LC_ALL": "C", "PYTHONUTF8": "0",
            })
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            status = state_dir / "STATUS.md"
            self.assertTrue(status.is_file(), f"STATUS.md was never written: {result.stderr}")
            self.assertIn("Bitácora", status.read_text(encoding="utf-8"))
            debris = [p.name for p in state_dir.iterdir() if p.name.startswith("tmp")]
            self.assertEqual(debris, [], f"partial renders left behind: {debris}")


class DoctrineTests(unittest.TestCase):
    def test_milestone_narration_is_doctrine_in_all_shared_files(self):
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md", "Global/_shared/AGENTS.codex.md"):
            text = (ROOT / path).read_text()
            self.assertIn("by MILESTONE, not by spawn (ADR-0027)", text, path)
            self.assertIn("feature-state.py digest", text, path)
        orchestrator = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("by MILESTONE, not by spawn", orchestrator)
        self.assertIn("feature-state.py digest", orchestrator)

    def test_write_limit_and_render_limit_are_the_same_number(self):
        """AC-15, hallazgo N3b-F01. Había dos topes en desacuerdo: escribir concedía 400
        (`narration_lint.LONG_FIELD_LIMIT`, por AC-05) y renderizar cortaba en 300, así que
        todo `tech` de entre 301 y 400 caracteres era legal al escribirlo y salía siempre
        mutilado al leerlo. AC-15 pide alinearlos, no sólo hacer ruidoso el corte. Este
        test es lo que impide que vuelvan a separarse en silencio."""
        # Se lee el literal del fuente en vez de importar: `narration_lint` vive en
        # ai/scripts/ (fuera del paquete) y cargarlo por spec_from_file_location rompe el
        # descubrimiento de unittest sobre este mismo módulo. Para un test de deriva de
        # constante, leer el literal alcanza y no tiene efectos de importación.
        source = (ROOT / "ai/scripts/narration_lint.py").read_text()
        match = re.search(r"^LONG_FIELD_LIMIT\s*=\s*(\d+)", source, re.MULTILINE)
        self.assertIsNotNone(match, "no se encontro LONG_FIELD_LIMIT en narration_lint.py")
        write_limit = int(match.group(1))
        from feature_state_lib.render_bitacora import NARRATION_FIELD_LIMIT
        self.assertEqual(
            NARRATION_FIELD_LIMIT, write_limit,
            "el tope de render y el de escritura tienen que ser el mismo numero (AC-15)")

    def test_doctrine_says_WHEN_to_run_digest_not_only_that_it_exists(self):
        """AC-18, hallazgo N2-F01 del review independiente de 028. El test anterior
        afirmaba `assertIn("feature-state.py digest", text)` — presencia del NOMBRE del
        comando, una cadena que ya existía antes del commit que decía implementar AC-18,
        así que pasaba en verde con o sin trabajo real. Es el mismo falso verde (D-3) que
        toda la feature 028 existe para erradicar, reproducido en su propio test de
        aceptación. La cadencia es el contenido: sin ella, el lector encuentra un digest
        viejo y le cree."""
        for path in ("Global/_shared/CLAUDE.md", "Global/_shared/AGENTS.opencode.md",
                     "Global/_shared/AGENTS.pi.md", "Global/_shared/AGENTS.codex.md",
                     "Global/_canonical/agents/orchestrator.md"):
            text = (ROOT / path).read_text()
            self.assertIn("PHASE CLOSE", text, f"{path}: falta la cadencia de digest (AC-18)")
            self.assertIn("TURN CLOSE", text, f"{path}: falta la cadencia de digest (AC-18)")

    def test_resume_feature_reads_the_living_notes(self):
        text = (ROOT / "Global/_canonical/commands/resume-feature.md").read_text()
        self.assertIn("docs/notas/features/<feature_id>.md", text)
        self.assertIn("## Qué falta", text)

    def test_session_open_reads_hub_without_vault(self):
        text = (ROOT / "Global/_canonical/agents/orchestrator.md").read_text()
        self.assertIn("no vault required", text)


class NarrationSurfacesTests(unittest.TestCase):
    def test_new_narration_fields_render_in_bitacora_and_digest(self):
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state = tmp / "ai/state"
            at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            (state / "features").mkdir(parents=True)
            (state / "features/901-campos.json").write_text(json.dumps({
                "feature_id": "901-campos",
                "phase": "PACKAGE_IMPLEMENTATION",
                "packages": [],
                "history": [],
                "blockers": [],
                "updated_at": at,
            }))
            _write_jsonl(state / "narrative-log.jsonl", [
                {
                    "at": at,
                    "feature_id": "901-campos",
                    "package_id": "N3b",
                    "role": "implementer",
                    "result": "done",
                    "client": "La salida de estado ahora explica por qué conviene el próximo paso.",
                    "tech": "render_status usa la razón de transición en castellano y sin flags crudos.",
                    "learned": "El problema no era falta de datos, era descarte en el render.",
                    "next": "Cerrar la ronda de pruebas de regresión de narración.",
                    "why": "Sin esa ronda no hay garantía de que no reaparezcan punteros vacíos.",
                    "alternative": "Cerrar ya y corregir luego; se descartó porque dejaría superficies inconsistentes.",
                    "actor": "orchestrator",
                }
            ])
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "sync-notes", "--state-dir", str(state)],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            bitacora = (state / "bitacora/901-campos.md").read_text(encoding="utf-8")
            digest = (tmp / "docs/notas/BUENOS-DIAS.md").read_text(encoding="utf-8")
            self.assertIn("Aprendimos:", bitacora)
            self.assertIn("Conviene ahora:", bitacora)
            self.assertIn("Por qué ahora:", bitacora)
            self.assertIn("Alternativa:", bitacora)
            self.assertIn("aprendimos:", digest)
            self.assertIn("conviene ahora:", digest)
            self.assertIn("por qué ahora:", digest)
            self.assertIn("alternativa:", digest)
            self.assertNotIn("None", bitacora)
            self.assertNotIn("None", digest)

    def test_bitacora_marks_render_truncation_explicitly(self):
        """El largo sale del tope canónico, nunca de un número copiado a mano.

        Este test usaba 340 caracteres fijos, elegidos cuando el render cortaba en 300.
        La feature 028 (hallazgo N3b-F01) subió ese corte a 400 para alinearlo con
        `narration_lint.LONG_FIELD_LIMIT`, que es lo que AC-05 concede al ESCRIBIR --
        y el test siguió verde igual, porque corre la CLI de `PROYECTO/`, cuyo espejo
        nunca recibió la reparación y seguía cortando en 300. O sea que este test
        estaba fijando el comportamiento SIN reparar, y sólo se enteró el 2026-08-18,
        cuando el espejo se sincronizó. Ahora el largo se deriva del tope real, así
        que un cambio de tope no puede volver a dejarlo afirmando lo que no pasa."""
        limit = int(re.search(
            r"^NARRATION_FIELD_LIMIT = (\d+)$",
            (ROOT / "ai/scripts/feature_state_lib/render_bitacora.py").read_text(encoding="utf-8"),
            re.M,
        ).group(1))
        overflow = limit + 40
        with tempfile.TemporaryDirectory() as raw:
            tmp = Path(raw)
            state = tmp / "ai/state"
            at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            (state / "features").mkdir(parents=True)
            (state / "features/902-historico.json").write_text(json.dumps({
                "feature_id": "902-historico",
                "phase": "PACKAGE_IMPLEMENTATION",
                "packages": [],
                "history": [],
                "blockers": [],
                "updated_at": at,
            }))
            _write_jsonl(state / "narrative-log.jsonl", [
                {
                    "at": at,
                    "feature_id": "902-historico",
                    "package_id": "N3b",
                    "role": "implementer",
                    "result": "done",
                    "client": "x" * overflow,
                    "tech": "y" * overflow,
                    "actor": "orchestrator",
                }
            ])
            result = subprocess.run(
                [sys.executable, str(FEATURE_STATE), "sync-notes", "--state-dir", str(state)],
                cwd=tmp, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            bitacora = (state / "bitacora/902-historico.md").read_text(encoding="utf-8")
            self.assertIn("truncado al render", bitacora)


if __name__ == "__main__":
    unittest.main()
