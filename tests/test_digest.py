"""Feature 017 PKG-D (ADR-0027) — the derived morning digest and the honest hub.

New tests only, against the real CLI in a synthetic project tree (the suite's
established pattern: real subprocesses, never mocks).
"""

import json
import subprocess
import sys
import tempfile
import unittest
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
        "feature_id": "001-vieja", "phase": "PACKAGE_ACCEPTED", "final_state": "done",
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
